import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import audited_plan as tool


class AuditedPlanTests(unittest.TestCase):
    def test_historical_merge_and_exact_budget(self):
        result = tool.demo()
        self.assertEqual(result['status'], 'audited')
        audit = result['minimum_audit']
        self.assertEqual(audit['minimum_change_count'], 1)
        self.assertEqual(audit['checked_assignments'], audit['candidate_assignments'])
        self.assertEqual(tool.demo(max_audit_assignments=audit['checked_assignments'])['status'], 'audited')
        self.assertEqual(tool.demo(max_audit_assignments=audit['checked_assignments'] - 1)['status'], 'inconclusive')

    def test_false_optimum_and_bad_witness_are_disagreement(self):
        text = json.dumps({'packages': {'a': {'1': {}, '2': {}}}, 'roots': {'a': '*'}})
        false = {'status': 'optimal', 'selected': {'a': '2'}, 'minimum_change_count': 1}
        with patch.object(tool.plan_merge.lock_plan, 'plan', return_value=false):
            result = tool.check(text, text, text, {'a': '1'})
        self.assertEqual(result['status'], 'disagreement')
        self.assertEqual(result['minimum_audit']['counterexample']['change_count'], 0)
        false['selected'] = {'a': '99'}
        with patch.object(tool.plan_merge.lock_plan, 'plan', return_value=false):
            self.assertEqual(tool.check(text, text, text, {'a': '1'})['status'], 'disagreement')

    def test_audit_skipped_for_unfinished_plan(self):
        with patch.object(tool.plan_audit, 'audit', side_effect=AssertionError):
            self.assertEqual(tool.demo(max_plan_steps=1)['status'], 'inconclusive')
            self.assertEqual(tool.demo(max_assignments=1)['status'], 'inconclusive')

    def test_conflict_and_incompatibility_skip_audit(self):
        folder = tool.plan_merge.first.HERE / 'examples'
        texts = [(folder / (n + '.json')).read_text() for n in ('base', 'ours', 'theirs')]
        with patch.object(tool.plan_audit, 'audit', side_effect=AssertionError):
            self.assertEqual(tool.check(*texts, {})['status'], 'incompatible')
            self.assertEqual(tool.check('a\n', 'b\n', 'c\n', {})['status'], 'text_conflict')

    def test_inputs_unchanged_and_invalid_budgets(self):
        baseline = {'a': '1'}
        original = copy.deepcopy(baseline)
        text = json.dumps({'packages': {'a': {'1': {}}}, 'roots': {'a': '*'}})
        self.assertEqual(tool.check(text, text, text, baseline)['status'], 'audited')
        self.assertEqual(baseline, original)
        for budget in (True, 0, -1, 1000001):
            with self.assertRaises(ValueError):
                tool.check(text, text, text, baseline, max_audit_assignments=budget)

    def test_portability_cli_and_exit_codes(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            folder = Path(tmp) / 'portable'
            shutil.copytree(Path(__file__).parent, folder)
            command = [sys.executable, '-B', str(folder / 'audited_plan.py'), 'demo']
            for args, code, status in [([], 0, 'audited'),
                                      (['--max-audit-assignments', '1'], 3, 'inconclusive')]:
                proc = subprocess.run(command + args, capture_output=True, text=True)
                self.assertEqual(proc.returncode, code, proc.stderr)
                self.assertEqual(json.loads(proc.stdout)['status'], status)
            proc = subprocess.run(command + ['--max-audit-assignments', '0'], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(proc.stdout, '')


if __name__ == '__main__':
    unittest.main()
