"""Integration tests for ancestry, both endpoint proofs, and fail-closed CLI."""
import contextlib
import copy
import importlib.util
import io
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('ancestry_diff_test_target', HERE / 'ancestry_diff.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class AncestryDiffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chain = d.chain_tool.load_chain(HERE.parent / 'header-chain/examples/zto-header-chain.json')
        cls.first = d.w.load_bundle(HERE.parent / 'state-witness/examples/zto-pool-mainnet.json')
        cls.tip = d.w.load_bundle(HERE / 'examples/pool-tip.json')
        cls.address = d.w.POOL_MANAGER
        cls.slot = d.chain_tool.a.POOL_SLOT

    def check(self, chain=None, first=None, tip=None, tip_hash=None, address=None, slots=None):
        return d.compare(chain if chain is not None else self.chain,
                         first if first is not None else self.first,
                         tip if tip is not None else self.tip,
                         tip_hash if tip_hash is not None else d.chain_tool.DEMO_TIP,
                         address if address is not None else self.address,
                         slots if slots is not None else [self.slot])

    def test_real_pool_endpoints_and_three_links(self):
        result = self.check()
        self.assertTrue(result['verified'])
        self.assertEqual(result['ancestry']['parentLinks'], 3)
        self.assertEqual(result['difference']['blockDistance'], 3)
        self.assertFalse(result['difference']['summary']['requestedSlotsChanged'])
        self.assertTrue(result['difference']['summary']['storageCommitmentChanged'])

    def test_one_header_same_state(self):
        one = {'format': 'header-chain/1', 'headers': [self.chain['headers'][0]]}
        result = self.check(chain=one, tip=self.first,
                            tip_hash=d.chain_tool.a.DEMO_HASH)
        self.assertTrue(result['difference']['sameCheckpoint'])
        self.assertFalse(result['difference']['summary']['accountChanged'])

    def test_wrong_tip_is_rejected(self):
        with self.assertRaises(d.INVALID):
            self.check(tip_hash=d.chain_tool.a.DEMO_HASH)

    def test_broken_parent_link_is_rejected(self):
        altered = copy.deepcopy(self.chain)
        altered['headers'][1]['parentHash'] = '0x' + '00' * 32
        with self.assertRaises(d.INVALID):
            self.check(chain=altered)

    def test_first_proof_corruption_is_rejected(self):
        altered = copy.deepcopy(self.first)
        altered['proof']['accountProof'] = []
        with self.assertRaises(d.INVALID):
            self.check(first=altered)

    def test_tip_proof_corruption_is_rejected(self):
        altered = copy.deepcopy(self.tip)
        altered['proof']['storageProof'][0]['proof'] = []
        with self.assertRaises(d.INVALID):
            self.check(tip=altered)

    def test_wrong_address_or_slot_is_rejected(self):
        with self.assertRaises(d.INVALID):
            self.check(address=d.w.ZTO)
        with self.assertRaises(d.INVALID):
            self.check(slots=['0x0'])

    def test_bundle_metadata_is_not_a_trust_anchor(self):
        altered = copy.deepcopy(self.tip)
        altered['block']['hash'] = d.chain_tool.a.DEMO_HASH
        altered['block']['stateRoot'] = d.w.DEMO_ROOT
        self.assertTrue(self.check(tip=altered)['verified'])

    def test_cli_rejects_wrong_tip_without_success_output(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        args = ['compare', str(HERE.parent / 'header-chain/examples/zto-header-chain.json'),
                str(HERE.parent / 'state-witness/examples/zto-pool-mainnet.json'),
                str(HERE / 'examples/pool-tip.json'), '--tip-hash', d.chain_tool.a.DEMO_HASH,
                '--address', self.address, '--slot', self.slot]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = d.main(args)
        self.assertEqual(code, 1)
        self.assertEqual(stdout.getvalue(), '')
        self.assertIn('"verified": false', stderr.getvalue())

    def test_cli_rejects_bad_tip_proof_without_traceback(self):
        # The direct-function corruption test above checks the actual proof.
        # This checks that errors from State Diff's separate module instance
        # become a clean CLI rejection too.
        import json
        from tempfile import TemporaryDirectory
        Path('test/scratch').mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir='test/scratch') as temp:
            path = Path(temp) / 'bad-tip.json'
            altered = copy.deepcopy(self.tip)
            altered['proof']['storageProof'][0]['proof'] = []
            path.write_text(json.dumps(altered))
            stdout, stderr = io.StringIO(), io.StringIO()
            args = ['compare', str(HERE.parent / 'header-chain/examples/zto-header-chain.json'),
                    str(HERE.parent / 'state-witness/examples/zto-pool-mainnet.json'),
                    str(path), '--tip-hash', d.chain_tool.DEMO_TIP,
                    '--address', self.address, '--slot', self.slot]
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = d.main(args)
            self.assertEqual(code, 1)
            self.assertEqual(stdout.getvalue(), '')
            self.assertIn('"verified": false', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
