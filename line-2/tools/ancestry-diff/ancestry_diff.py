#!/usr/bin/env python3
"""Compare two proven Ethereum states connected to one trusted tip hash."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def sibling(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE.parent / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


chain_tool = sibling('header_chain_for_ancestry_diff', 'header-chain/header_chain.py')
diff_tool = sibling('state_diff_for_ancestry_diff', 'state-diff/state_diff.py')
w = chain_tool.w
# The sibling modules each import State Witness under a private module name.
# Their Invalid classes are distinct even though they implement the same check.
INVALID = (w.Invalid, diff_tool.w.Invalid)


def compare(chain, first_witness, tip_witness, trusted_tip_hash, address, slots):
    """Prove both endpoint states and their parent-linked ancestry atomically.

    The only caller trust anchor is the last header's hash. No bundle labels or
    embedded hash can supply or override it. Failed inputs never yield a diff.
    """
    ancestry = chain_tool.verify_chain(chain, trusted_tip_hash)
    headers = chain['headers']
    first_hash = ancestry['target']['blockHash']
    tip_hash = ancestry['checkpoint']['blockHash']
    # State Diff checks both complete proofs again against the roots in the
    # linked headers. For a single-header chain, this is a zero-distance check.
    difference = diff_tool.compare(headers[0], first_witness, headers[-1], tip_witness,
                                   first_hash, tip_hash, address, slots)
    w.require(difference['before']['blockHash'] == first_hash and
              difference['after']['blockHash'] == tip_hash,
              'comparison endpoints do not match the linked headers')
    difference['trust'] = ('Both endpoint hashes were reconstructed from the '
                           'parent-linked headers under the caller-supplied tip '
                           'hash. Authenticate that tip independently; the '
                           'linked headers alone do not establish consensus, '
                           'canonicality, finality or execution validity.')
    return {
        'format': 'ancestry-diff/1', 'verified': True,
        'ancestry': ancestry, 'difference': difference,
        'trust': ('The caller must authenticate the tip hash, chain, canonicality, '
                  'execution validity and finality independently. Parent links '
                  'prove that the first header is an ancestor of the tip, not '
                  'that either header is canonical. Differences describe only '
                  'requested state at two endpoints, not intermediate events, '
                  'transfers, token balances or a current quote.'),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo', help='verify linked real ZTO/IMD pool states offline')
    check = sub.add_parser('compare', help='compare two proofs under one trusted tip hash')
    check.add_argument('chain', help='header-chain/1 JSON, oldest first')
    check.add_argument('first_witness', help='state-witness/1 JSON at oldest header')
    check.add_argument('tip_witness', help='state-witness/1 JSON at latest header')
    check.add_argument('--tip-hash', required=True)
    check.add_argument('--address', required=True)
    check.add_argument('--slot', action='append', default=[])
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            chain = chain_tool.load_chain(HERE.parent / 'header-chain/examples/zto-header-chain.json')
            first = w.load_bundle(HERE.parent / 'state-witness/examples/zto-pool-mainnet.json')
            tip = w.load_bundle(HERE / 'examples/pool-tip.json')
            output = compare(chain, first, tip, chain_tool.DEMO_TIP,
                             w.POOL_MANAGER, [chain_tool.a.POOL_SLOT])
            output['demo'] = ('Real historical mainnet observations; the bundled tip '
                              'hash is an RPC observation, not an independently '
                              'authenticated consensus checkpoint.')
        else:
            output = compare(chain_tool.load_chain(args.chain),
                             w.load_bundle(args.first_witness), w.load_bundle(args.tip_witness),
                             args.tip_hash, args.address, args.slot)
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except INVALID as error:
        print(json.dumps({'verified': False, 'error': str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        print(json.dumps({'verified': False,
                          'error': 'Unreadable or malformed chain or witness.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
