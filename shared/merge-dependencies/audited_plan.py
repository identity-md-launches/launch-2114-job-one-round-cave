#!/usr/bin/env python3
"""Check a merged catalog's minimum-edit proposal with separate enumeration."""
import argparse
import json
import sys

import plan_merge
import plan_audit


def check(base, ours, theirs, baseline, max_steps=10000,
          max_assignments=10000, max_plan_steps=10000,
          max_audit_assignments=10000):
    if (type(max_audit_assignments) is not int or
            not 1 <= max_audit_assignments <= 1000000):
        raise ValueError('audit budget must be an integer from 1 to 1000000')
    proposal = plan_merge.check(base, ours, theirs, baseline, max_steps,
                                max_assignments, max_plan_steps)
    result = {'format': 'audited-merge-plan/v1', 'status': proposal['status'],
              'proposal': proposal, 'minimum_audit': None,
              'limits': [
                  'Read-only proposal; no files, packages or roots are changed.',
                  'Enumeration checks selected versions and minimum edit count only.',
                  'Both checks share the finite numeric catalog parser and edge checker.',
                  'No installability, security, artifact or publisher trust claim.']}
    if proposal['status'] != 'planned':
        return result
    # Reconstruct the catalog from the actual merged text. Do not audit an
    # intermediate branch or trust the planner's embedded digest/baseline.
    catalog = plan_merge.first.parse(
        proposal['checked_merge']['review']['merge']['merged'])
    try:
        audit = plan_audit.audit(catalog, baseline, proposal['plan'],
                                max_audit_assignments)
    except ValueError:
        audit = {'status': 'rejected', 'reason': 'invalid planner witness or claim'}
    result['minimum_audit'] = audit
    result['status'] = {'verified': 'audited', 'rejected': 'disagreement',
                        'inconclusive': 'inconclusive'}[audit['status']]
    return result


def demo(**budgets):
    folder = plan_merge.first.HERE / 'examples'
    texts = [plan_merge.first.review.engine.read_text(folder / f'plan-{n}.json')
             for n in ('base', 'ours', 'theirs')]
    baseline = plan_audit.fmt.load(folder / 'baseline.json')
    return check(*texts, baseline, **budgets)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('demo', 'check'):
        item = sub.add_parser(name)
        if name == 'check':
            for branch in ('base', 'ours', 'theirs'):
                item.add_argument(branch)
            item.add_argument('--baseline', required=True)
        for budget in ('steps', 'assignments', 'plan-steps', 'audit-assignments'):
            item.add_argument('--max-' + budget, type=int, default=10000)
    args = parser.parse_args(argv)
    budgets = {key: getattr(args, key) for key in (
        'max_steps', 'max_assignments', 'max_plan_steps', 'max_audit_assignments')}
    try:
        if args.command == 'demo':
            result = demo(**budgets)
        else:
            texts = [plan_merge.first.review.engine.read_text(p)
                     for p in (args.base, args.ours, args.theirs)]
            baseline = plan_audit.fmt.load(args.baseline)
            result = check(*texts, baseline, **budgets)
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return {'audited': 0, 'incompatible': 1, 'text_conflict': 1,
                'invalid_catalog': 2, 'inconclusive': 3,
                'disagreement': 4}[result['status']]
    except (ValueError, OSError, TypeError, RecursionError):
        print(json.dumps({'status': 'invalid',
                          'error': 'Invalid workspace inputs or budgets.'}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
