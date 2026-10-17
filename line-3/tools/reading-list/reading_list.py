#!/usr/bin/env python3
"""Combine bounded offline lexical searches into a cited reading list."""
import argparse
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

_spec = importlib.util.spec_from_file_location(
    'reading_list_search', Path(__file__).absolute().parent.parent / 'evidence-search' / 'search.py')
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)


def plan(index, queries, budget=5, depth=10, require_all=False, root=None):
    """Greedy query coverage, reciprocal rank ties; sources are inert data."""
    if not isinstance(queries, list) or not 1 <= len(queries) <= 12:
        raise engine.SearchError('provide between 1 and 12 queries')
    if type(budget) is not int or not 1 <= budget <= 30:
        raise engine.SearchError('budget must be between 1 and 30')
    if type(depth) is not int or not 1 <= depth <= 50:
        raise engine.SearchError('depth must be between 1 and 50')
    if type(require_all) is not bool:
        raise engine.SearchError('require_all must be boolean')
    # Validation and query normalization are delegated to the existing engine.
    # Canonicalize document order so equal-score search ties stay reproducible.
    engine.validate_index(index)
    index = dict(index, documents=sorted(index['documents'], key=lambda d: d['path']))
    searches = [engine.search_snapshot(index, q, depth, require_all) for q in queries]
    normalized = [tuple(s['terms']) for s in searches]
    if len(set(normalized)) != len(normalized):
        raise engine.SearchError('queries must have distinct normalized term sets')
    candidates = {}
    for qi, search in enumerate(searches):
        for rank, hit in enumerate(search['hits'], 1):
            key = (hit['path'], hit['line_start'], hit['line_end'])
            if key not in candidates:
                candidates[key] = {'hit': hit, 'ranks': {}, 'rrf': Fraction(0)}
            item = candidates[key]
            item['ranks'][qi] = rank
            item['rrf'] += Fraction(1, 60 + rank)
    chosen, represented = [], set()
    remaining = dict(candidates)
    while remaining and len(chosen) < budget:
        key = min(remaining, key=lambda k: (
            -len(set(remaining[k]['ranks']) - represented), -remaining[k]['rrf'], k))
        item = remaining.pop(key)
        chosen.append(item)
        represented.update(item['ranks'])
        # Suppress all overlapping windows of an already selected source.
        remaining = {k: v for k, v in remaining.items()
                     if k[0] != key[0] or k[2] < key[1] or k[1] > key[2]}
    passages = []
    verified = set()
    if root is not None:
        root = engine.workspace_path(root)
        if not root.is_dir():
            raise engine.SearchError('corpus root must be a directory')
    for item in chosen:
        hit = item['hit']
        if root is not None and hit['path'] not in verified:
            raw = engine.read_bytes(engine.workspace_path(root / hit['path']), engine.MAX_FILE_BYTES)
            if engine.digest(raw) != hit['sha256']:
                raise engine.SearchError('stale selected source: ' + hit['path'])
            verified.add(hit['path'])
        passage = {k: hit[k] for k in (
            'path', 'line_start', 'line_end', 'citation', 'sha256', 'text')}
        passage.update(source_verified=root is not None,
                       query_ranks=[{'query': qi + 1, 'rank': rank}
                                    for qi, rank in sorted(item['ranks'].items())],
                       reciprocal_rank_score=round(float(item['rrf']), 10))
        passages.append(passage)
    queries_out = []
    for qi, search in enumerate(searches):
        refs = [p['citation'] for p in passages
                if any(r['query'] == qi + 1 for r in p['query_ranks'])]
        queries_out.append({'number': qi + 1, 'query': queries[qi], 'terms': search['terms'],
                            'candidate_count': len(search['hits']), 'selected_citations': refs,
                            'status': 'represented' if refs else (
                                'no_candidates' if not search['hits'] else 'budget_or_overlap')})
    canonical = json.dumps(index, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return {'format': 'cited-reading-list/v1', 'snapshot_sha256': hashlib.sha256(
                canonical.encode('utf-8')).hexdigest(),
            'budget': budget, 'candidate_depth_per_query': depth, 'require_all': require_all,
            'all_queries_represented': len(represented) == len(queries),
            'queries': queries_out, 'passages': passages}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    subs.add_parser('demo', help='read the inherited historical ZTO/IMD corpus; write nothing')
    for name in ('scan', 'snapshot'):
        p = subs.add_parser(name)
        p.add_argument('source', help='corpus directory' if name == 'scan' else 'saved search index')
        p.add_argument('--query', action='append', required=True)
        p.add_argument('--budget', type=int, default=5)
        p.add_argument('--depth', type=int, default=10)
        p.add_argument('--all', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            root = Path(__file__).absolute().parent.parent / 'evidence-search' / 'examples' / 'docs'
            result = plan(engine.build_index(root), ['ZTO decimals', 'pool tick spacing',
                          'consensus finality'], budget=3, require_all=True, root=root)
        else:
            root = args.source if args.command == 'scan' else None
            index = engine.build_index(root) if root is not None else engine.load_index(args.source)
            result = plan(index, args.query, args.budget, args.depth, args.all, root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if args.command == 'demo' or result['all_queries_represented'] else 1
    except (engine.SearchError, OSError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
