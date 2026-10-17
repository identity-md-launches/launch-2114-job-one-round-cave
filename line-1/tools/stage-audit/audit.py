#!/usr/bin/env python3
"""Read-only comparison of a staged UTF-8 tree with a pinned export receipt."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import sys

SOURCE = Path(__file__).resolve().parents[1] / 'review-recheck' / 'recheck.py'
SPEC = importlib.util.spec_from_file_location('audit_recheck', SOURCE)
r = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r)
MAX_RECEIPT_BYTES = 1024 * 1024


def digest(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('SHA-256 must be 64 lowercase hexadecimal digits')
    return value


def safe_name(name):
    if not isinstance(name, str) or not name or '\\' in name or '\x00' in name:
        raise ValueError('invalid relative receipt path')
    path = PurePosixPath(name)
    if (path.is_absolute() or '..' in path.parts or
            path.as_posix() != name or name == '.' or len(path.parts) > 17):
        raise ValueError('receipt paths must be canonical relative paths')
    return path


def expected_tree(receipt):
    if not isinstance(receipt, dict) or receipt.get('schema') not in (
            'candidate-export/v1', 'conflict-finish-receipt/v1'):
        raise ValueError('unsupported export receipt schema')
    if receipt.get('review_matches') is not True:
        raise ValueError('receipt must assert a reproduced review')
    digest(receipt.get('packet_sha256'))
    if receipt['schema'] == 'candidate-export/v1':
        if receipt.get('clean') is not True:
            raise ValueError('clean export receipt must assert clean')
    else:
        digest(receipt.get('decisions_sha256'))
    files = receipt.get('files')
    if not isinstance(files, dict) or len(files) > r.tree.MAX_FILES:
        raise ValueError('receipt needs a bounded file map')
    entries, directories, total = {}, set(), 0
    for name, info in files.items():
        path = safe_name(name)
        if (not isinstance(info, dict) or set(info) != {'bytes', 'sha256'} or
                type(info['bytes']) is not int or
                not 0 <= info['bytes'] <= r.tree.review.engine.MAX_BYTES):
            raise ValueError('invalid file fingerprint')
        digest(info['sha256'])
        entries[name] = {'kind': 'file', **info}
        total += info['bytes']
        directories.update(parent.as_posix() for parent in path.parents
                           if parent.as_posix() != '.')
    if (directories & files.keys() or len(directories) > r.tree.MAX_DIRS or
            total > r.tree.MAX_TOTAL_BYTES):
        raise ValueError('receipt tree collision or size limit')
    entries.update({name: {'kind': 'directory'} for name in directories})
    manifest = {
        'sha256': hashlib.sha256(r.canonical(entries).encode()).hexdigest(),
        'files': len(files), 'directories': len(directories), 'bytes': total}
    if r.canonical(receipt.get('manifest')) != r.canonical(manifest):
        raise ValueError('receipt manifest disagrees with its file map')
    return files, directories, manifest


def load_receipt(path, expected_sha256):
    digest(expected_sha256)
    source = Path(path)
    if '..' in source.parts:
        raise ValueError('receipt path must not contain parent traversal')
    parent = r.tree.workspace_directory(source.parent)
    source = parent / source.name
    if source.is_symlink() or not source.is_file():
        raise ValueError('receipt must be a regular non-symlink file')
    with source.open('rb') as handle:
        raw = handle.read(MAX_RECEIPT_BYTES + 1)
    if len(raw) > MAX_RECEIPT_BYTES:
        raise ValueError('receipt exceeds 1 MiB')
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise ValueError('receipt differs from independently retained SHA-256')
    receipt = json.loads(raw.decode('utf-8'), object_pairs_hook=r.unique_object,
                         parse_constant=r.reject_constant)
    expected_tree(receipt)
    return receipt, actual


def compare(receipt, staged):
    files, directories, expected = expected_tree(receipt)
    current = {name: {'bytes': len(text.encode('utf-8')),
                      'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}
               for name, text in staged['files'].items()}
    actual = r.tree.manifest(staged)
    return {
        'schema': 'stage-audit/v1', 'matches': expected == actual,
        'added': sorted(current.keys() - files.keys()),
        'missing': sorted(files.keys() - current.keys()),
        'changed': sorted(name for name in files.keys() & current.keys()
                          if files[name] != current[name]),
        'added_directories': sorted(staged['directories'] - directories),
        'missing_directories': sorted(directories - staged['directories']),
        'expected_manifest': expected, 'actual_manifest': actual,
        'limits': [
            'Byte equality with a pinned receipt is not approval or semantic correctness.',
            'Receipt hash must be retained independently; no author authentication.',
            'Does not recheck source trees, merge decisions, permissions or executable bits.',
            'Stable trusted workspace required; no atomic snapshot or race protection.',
            'Bounded UTF-8 files only; no writes, network or transaction operations.']}


def audit(receipt_path, tree_path, expected_sha256):
    receipt, receipt_hash = load_receipt(receipt_path, expected_sha256)
    # The caller chooses the directory. Never follow any path inside the receipt.
    staged = r.tree.snapshot(tree_path, [0])
    result = compare(receipt, staged)
    result['receipt_sha256'] = receipt_hash
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt')
    parser.add_argument('staged_tree')
    parser.add_argument('--expected-sha256', required=True)
    args = parser.parse_args(argv)
    try:
        result = audit(args.receipt, args.staged_tree, args.expected_sha256)
    except (OSError, ValueError, UnicodeError, RecursionError) as error:
        print('stage-audit: ' + ascii(str(error)), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result['matches'] else 1


if __name__ == '__main__':
    sys.exit(main())
