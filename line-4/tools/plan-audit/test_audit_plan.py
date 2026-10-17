"""Offline behavioral checks; imports/read paths stay in this workspace."""
import copy
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('audit_plan', HERE / 'audit_plan.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
spec = importlib.util.spec_from_file_location('planner_for_comparison', HERE.parent / 'lock-plan/plan.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def claim(selected, cost):
    return {'status': 'optimal', 'selected': selected, 'minimum_change_count': cost}


def catalog(packages, roots=None):
    return {'packages': packages, 'roots': {'a': '*'} if roots is None else roots}


class AuditTests(unittest.TestCase):
    def test_real_demo(self):
        run = subprocess.run([sys.executable, '-B', str(HERE/'audit_plan.py'), 'demo'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        out = json.loads(run.stdout)
        self.assertEqual((out['status'], out['checked_assignments'], out['minimum_change_count']), ('verified', 27, 1))

    def test_nonoptimal_counterexample(self):
        data = catalog({'a': {'1': {}, '2': {}}})
        out = a.audit(data, {'a': '1'}, claim({'a': '2'}, 1))
        self.assertEqual(out['status'], 'rejected')
        self.assertEqual(out['counterexample'], {'selected': {'a': '1'}, 'change_count': 0})

    def test_exact_budget(self):
        data = catalog({'a': {'1': {}, '2': {}}})
        report = claim({'a': '1'}, 1)
        self.assertEqual(a.audit(data, {}, report, 1)['status'], 'inconclusive')
        self.assertEqual(a.audit(data, {}, report, 2)['status'], 'verified')
        self.assertNotIn('minimum_change_count', a.audit(data, {}, report, 1))

    def test_miscount(self):
        data = catalog({'a': {'1': {}}})
        self.assertEqual(a.audit(data, {}, claim({'a': '1'}, 0))['status'], 'rejected')

    def test_cycles_and_all_incoming_edges(self):
        data = catalog({'a': {'1': {'b': '==1'}}, 'b': {'1': {'a': '==1'}}})
        self.assertEqual(a.audit(data, {}, claim({'a': '1', 'b': '1'}, 2))['status'], 'verified')
        data['packages']['b']['1']['a'] = '==2'
        with self.assertRaises(a.fmt.Invalid):
            a.audit(data, {}, claim({'a': '1', 'b': '1'}, 2))

    def test_abandoned_dependencies_and_removal(self):
        data = catalog({'a': {'1': {'b': '*'}, '2': {}}, 'b': {'1': {}}})
        out = a.audit(data, {'a': '2', 'obsolete': '9'}, claim({'a': '2'}, 1))
        self.assertEqual(out['status'], 'verified')
        self.assertEqual(out['candidate_assignments'], 4)

    def test_invalid_witnesses(self):
        data = catalog({'a': {'1': {}}})
        for selected in ({}, {'a': '2'}, {'a': '1', 'extra': '1'}, {'a': None}, {'A': '1'}, []):
            with self.subTest(selected=selected), self.assertRaises(a.fmt.Invalid):
                a.audit(data, {}, claim(selected, 1))

    def test_empty_roots_and_aliases(self):
        with self.assertRaises(a.fmt.Invalid):
            a.audit(catalog({}, {}), {'gone': '1'}, claim({}, 1), 1)
        data = catalog({'a': {'1.0': {}}})
        self.assertEqual(a.audit(data, {'A': '1'}, claim({'a': '1.0'}, 0))['status'], 'verified')

    def test_invalid_inputs(self):
        data = catalog({'a': {'1': {}}})
        for baseline in ([], {'A': '1', 'a': '1'}, {'a': 'banana'}):
            with self.assertRaises(a.fmt.Invalid):
                a.audit(data, baseline, claim({'a': '1'}, 1))
        for cost in (True, -1, 1.5, '1'):
            with self.assertRaises(a.fmt.Invalid):
                a.audit(data, {}, claim({'a': '1'}, cost))
        for budget in (True, 0, -1, 1000001):
            with self.assertRaises(a.fmt.Invalid):
                a.audit(data, {}, claim({'a': '1'}, 1), budget)
        with self.assertRaises(a.fmt.Invalid):
            a.audit(data, {}, {'status': 'inconclusive'})

    def test_does_not_call_search_or_planner(self):
        data = catalog({'a': {'1': {}, '2': {}}})
        with patch.object(p, 'plan', side_effect=AssertionError), patch.object(p, 'changes', side_effect=AssertionError), patch.object(a.fmt, 'solve', side_effect=AssertionError), patch.object(a.fmt, 'accepts', side_effect=AssertionError):
            self.assertEqual(a.audit(data, {}, claim({'a': '1'}, 1))['status'], 'verified')

    def test_immutable_and_binding(self):
        data = catalog({'a': {'1': {}}})
        baseline, report = {'a': '1'}, claim({'a': '1'}, 0)
        snapshot = copy.deepcopy((data, baseline, report))
        first = a.audit(data, baseline, report)
        self.assertEqual((data, baseline, report), snapshot)
        self.assertEqual(first, a.audit(data, baseline, report))
        changed = a.audit(data, {}, claim({'a': '1'}, 1))
        self.assertNotEqual(first['input_sha256'], changed['input_sha256'])
        # Extraneous report metadata deliberately is not a claim being checked.
        report['input_sha256'] = 'untrusted'
        self.assertEqual(first, a.audit(data, baseline, report))

    def test_seeded_planner_comparison(self):
        rng = random.Random(26004)
        checked = 0
        for _ in range(500):
            packages = {}
            for name in ('a', 'b', 'c'):
                packages[name] = {v: {q: rng.choice(('*', '==1', '==2', '!=1'))
                                     for q in ('a', 'b', 'c') if rng.random() < .22}
                                  for v in ('1', '2') if rng.random() < .85}
            data = catalog(packages)
            baseline = {n: rng.choice(('1', '2', '3')) for n in ('a', 'b', 'c', 'old') if rng.random() < .6}
            planned = p.plan(data, baseline)
            if planned['status'] == 'optimal':
                out = a.audit(data, baseline, planned)
                self.assertEqual(out['status'], 'verified', (data, baseline, planned, out))
                checked += 1
        self.assertGreater(checked, 200)

    def test_cli_statuses_and_loader(self):
        scratch = Path('test/scratch/plan-audit')
        scratch.mkdir(parents=True, exist_ok=True)
        paths = [scratch / n for n in ('catalog.json', 'baseline.json', 'report.json')]
        for path, value in zip(paths, (catalog({'a': {'1': {}, '2': {}}}), {}, claim({'a': '1'}, 1))):
            path.write_text(json.dumps(value))
        command = [sys.executable, '-B', str(HERE/'audit_plan.py'), str(paths[0]), '--baseline', str(paths[1]), '--report', str(paths[2])]
        for extra, code in (([], 0), (['--max-assignments', '1'], 3)):
            run = subprocess.run(command+extra, capture_output=True, text=True)
            self.assertEqual(run.returncode, code, run.stdout+run.stderr)
        paths[1].write_text('{"a":"1"}')
        paths[2].write_text(json.dumps(claim({'a': '2'}, 1)))
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
        paths[2].write_text('{"status":"optimal","status":"optimal"}')
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)


if __name__ == '__main__':
    unittest.main()
