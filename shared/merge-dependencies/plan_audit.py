#!/usr/bin/env python3
"""Independently enumerate small catalogs to audit a minimum-edit claim."""
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

import exhaustive as edges
fmt = edges.fmt


def normalize_baseline(raw):
    if not isinstance(raw, dict) or len(raw) > 1000:
        raise fmt.Invalid('baseline must contain at most 1000 package versions')
    result = {}
    for key, value in raw.items():
        name = fmt.name(key)
        fmt.version(value)
        if name in result:
            raise fmt.Invalid('duplicate canonical baseline package ' + name)
        result[name] = value
    return dict(sorted(result.items()))


def distance(before, after):
    # Own implementation: do not import Lock Plan or its changes() function.
    return sum(p not in before or p not in after or
               fmt.version(before[p]) != fmt.version(after[p])
               for p in before.keys() | after.keys())


def audit(data, baseline, report, max_assignments=10000):
    if type(max_assignments) is not int or not 1 <= max_assignments <= 1000000:
        raise fmt.Invalid('max_assignments must be an integer from 1 to 1000000')
    packages, roots = fmt.validate(data)
    baseline = normalize_baseline(baseline)
    if not isinstance(report, dict) or report.get('status') != 'optimal':
        raise fmt.Invalid('report must claim optimal')
    selected = report.get('selected')
    claimed = report.get('minimum_change_count')
    if type(claimed) is not int or claimed < 0:
        raise fmt.Invalid('minimum_change_count must be a nonnegative integer')
    if (not isinstance(selected, dict) or
            any(not isinstance(k, str) or not isinstance(v, str) for k, v in selected.items())):
        raise fmt.Invalid('selected must map canonical names to catalog version strings')
    if edges.assignment(packages, roots, selected) != selected:
        raise fmt.Invalid('selected violates an edge or includes unreachable packages')
    actual = distance(baseline, selected)
    binding = {'catalog': {'packages': packages, 'roots': roots}, 'baseline': baseline}
    digest = hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    base = {'method': 'cartesian-minimum-edit-audit-v1', 'input_sha256': digest,
            'claimed_minimum': claimed, 'witness_change_count': actual,
            'max_assignments': max_assignments}
    if actual != claimed:
        return dict(base, status='rejected', reason='witness cost differs from claim', checked_assignments=0)
    # Union of every release's transitive dependencies covers all possible
    # solutions, including abandoned branches. Nonroots also have an absent option.
    possible, todo = set(), list(roots)
    while todo:
        p = todo.pop()
        if p not in possible:
            possible.add(p)
            for requirements in packages.get(p, {}).values():
                todo.extend(requirements)
    names = sorted(possible)
    domains = []
    total = 1
    for p in names:
        releases = sorted(packages.get(p, {}), key=fmt.version)
        domain = ([v for v in releases if edges.matches(v, roots[p])]
                  if p in roots else [None] + releases)
        domains.append(domain)
        total *= len(domain)
    base.update(candidate_assignments=total, possible_packages=names)
    checked = 0
    for values in itertools.product(*domains):
        if checked == max_assignments:
            return dict(base, status='inconclusive', checked_assignments=checked,
                        reason='assignment budget exhausted; minimum not established')
        checked += 1
        candidate = edges.assignment(packages, roots, dict(zip(names, values)))
        if candidate is not None:
            cost = distance(baseline, candidate)
            if cost < claimed:
                return dict(base, status='rejected', checked_assignments=checked,
                            reason='compatible selection with fewer package edits',
                            counterexample={'selected': candidate, 'change_count': cost})
    return dict(base, status='verified', checked_assignments=checked,
                minimum_change_count=claimed, selected=selected,
                reason='all Cartesian assignments exhausted')


