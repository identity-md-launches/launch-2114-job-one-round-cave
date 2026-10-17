"""Filesystem integration tests; all transient writes stay in test/scratch."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


a = load('stage_audit', HERE / 'audit.py')
f = load('audit_finish', HERE.parent / 'conflict-finish' / 'finish.py')
e = f.export


class AuditTests(unittest.TestCase):
    def setUp(self):
        scratch = Path.cwd() / 'test' / 'scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = [self.root / name for name in ('base', 'ours', 'theirs')]
        for folder in self.inputs:
            folder.mkdir()
            (folder / 'guide.txt').write_bytes(b'first\r\nsecond\r\n')
            (folder / 'old.txt').write_bytes(b'old\n')
        (self.inputs[1] / 'guide.txt').write_bytes(b'ours\r\nsecond\r\n')
        (self.inputs[2] / 'guide.txt').write_bytes(b'first\r\ntheirs\r\n')
        (self.inputs[2] / 'old.txt').unlink()
        (self.inputs[1] / 'nested').mkdir()
        (self.inputs[1] / 'nested/new.txt').write_bytes('café\n'.encode())
        (self.inputs[1] / 'empty.txt').write_bytes(b'')
        self.packet = self.root / 'packet.json'
        self.staged = self.root / 'staged'
        self.receipt_path = self.root / 'receipt.json'
        self.make_packet()
        self.receipt = e.export(self.packet, self.inputs, self.staged, self.packet_hash)
        self.pin()

    def make_packet(self):
        self.packet.write_text(json.dumps(e.r.tree.from_directories(self.inputs)), encoding='utf-8')
        self.packet_hash = hashlib.sha256(self.packet.read_bytes()).hexdigest()

    def pin(self):
        self.receipt_path.write_text(json.dumps(self.receipt), encoding='utf-8')
        self.pin_hash = hashlib.sha256(self.receipt_path.read_bytes()).hexdigest()

    def audit(self, path=None):
        return a.audit(self.receipt_path, path or self.staged, self.pin_hash)

    def cli(self, pin=None):
        return subprocess.run([sys.executable, '-B', str(HERE / 'audit.py'),
                               str(self.receipt_path), str(self.staged),
                               '--expected-sha256', pin or self.pin_hash],
                              capture_output=True, text=True)

    def test_clean_export_exact_crlf_unicode_empty_and_read_only(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = self.audit()
        self.assertTrue(result['matches'])
        self.assertEqual((self.staged / 'guide.txt').read_bytes(), b'ours\r\ntheirs\r\n')
        self.assertEqual(result['changed'], [])
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_detects_added_missing_changed_and_directory_changes(self):
        (self.staged / 'guide.txt').write_bytes(b'ours\ntheirs\n')
        (self.staged / 'nested/new.txt').unlink()
        (self.staged / 'nested').rmdir()
        (self.staged / 'old.txt').write_bytes(b'restored deletion\n')
        (self.staged / 'extra-empty-dir').mkdir()
        result = self.audit()
        self.assertFalse(result['matches'])
        self.assertEqual(result['added'], ['old.txt'])
        self.assertEqual(result['missing'], ['nested/new.txt'])
        self.assertEqual(result['changed'], ['guide.txt'])
        self.assertEqual(result['added_directories'], ['extra-empty-dir'])
        self.assertEqual(result['missing_directories'], ['nested'])

    def test_same_length_change_is_detected(self):
        (self.staged / 'guide.txt').write_bytes(b'OURS\r\ntheirs\r\n')
        self.assertEqual(self.audit()['changed'], ['guide.txt'])

    def test_moved_tree_and_untrusted_output_metadata(self):
        moved = self.root / 'moved'
        self.staged.rename(moved)
        self.receipt['output'] = '../../not-an-input'
        self.pin()
        self.assertTrue(self.audit(moved)['matches'])

    def test_pin_is_exact_bytes_and_required(self):
        self.receipt_path.write_bytes(self.receipt_path.read_bytes() + b'\n')
        with self.assertRaises(ValueError):
            self.audit()
        for pin in (None, 'bad', self.pin_hash.upper()):
            with self.assertRaises(ValueError):
                a.audit(self.receipt_path, self.staged, pin)

    def test_rehashed_inconsistent_manifest_rejected(self):
        self.receipt['files']['guide.txt']['sha256'] = hashlib.sha256(b'altered').hexdigest()
        self.pin()
        with self.assertRaises(ValueError):
            self.audit()

    def test_invalid_receipt_types_schemas_paths_and_counts(self):
        original = copy.deepcopy(self.receipt)
        variants = []
        for key, value in [('schema', 'unknown'), ('review_matches', 1), ('clean', 1),
                           ('packet_sha256', 'bad')]:
            variant = copy.deepcopy(original)
            variant[key] = value
            variants.append(variant)
        for name in ('../escape', '/absolute', 'a//b', './x', 'a/../x', 'a\\b', '.'):
            variant = copy.deepcopy(original)
            variant['files'] = {name: original['files']['guide.txt']}
            variants.append(variant)
        for value in (True, -1, 1.0, a.r.tree.review.engine.MAX_BYTES + 1):
            variant = copy.deepcopy(original)
            variant['files']['guide.txt']['bytes'] = value
            variants.append(variant)
        variant = copy.deepcopy(original)
        variant['manifest']['files'] = True
        variants.append(variant)
        for variant in variants:
            with self.subTest(variant=variant):
                self.receipt = variant
                self.pin()
                with self.assertRaises(ValueError):
                    self.audit()

    def test_duplicate_nonfinite_invalid_utf8_and_oversize(self):
        for raw in (b'{"schema":1,"schema":2}', b'{"x":NaN}', b'\xff',
                    b' ' * (a.MAX_RECEIPT_BYTES + 1)):
            self.receipt_path.write_bytes(raw)
            pin = hashlib.sha256(raw).hexdigest()
            with self.assertRaises(ValueError):
                a.audit(self.receipt_path, self.staged, pin)

    def test_workspace_symlinks_and_traversal_rejected(self):
        link = self.root / 'linked'
        link.symlink_to(self.staged, target_is_directory=True)
        receipt_link = self.root / 'receipt-link'
        receipt_link.symlink_to(self.receipt_path)
        for receipt, tree in ((receipt_link, self.staged), (self.receipt_path, link),
                              (self.receipt_path, self.staged / '..' / 'staged'),
                              (self.receipt_path, Path('/'))):
            with self.assertRaises(ValueError):
                a.audit(receipt, tree, self.pin_hash)
        (self.staged / 'link').symlink_to(self.staged / 'guide.txt')
        with self.assertRaises(ValueError):
            self.audit()

    def test_binary_and_oversized_candidate_refused(self):
        for raw in (b'\xff', b'\x00', b'x' * (a.r.tree.review.engine.MAX_BYTES + 1)):
            (self.staged / 'guide.txt').write_bytes(raw)
            with self.assertRaises(ValueError):
                self.audit()

    def test_empty_export(self):
        for folder in self.inputs:
            shutil.rmtree(folder)
            folder.mkdir()
        self.make_packet()
        other = self.root / 'empty-staged'
        self.receipt = e.export(self.packet, self.inputs, other, self.packet_hash)
        self.pin()
        self.assertTrue(self.audit(other)['matches'])
        (other / 'empty-directory').mkdir()
        self.assertFalse(self.audit(other)['matches'])

    def test_conflict_finish_receipt(self):
        (self.inputs[2] / 'guide.txt').write_bytes(b'theirs\r\nsecond\r\n')
        self.make_packet()
        decisions = self.root / 'decisions.json'
        decisions.write_text(json.dumps({
            'schema': 'conflict-finish/v1', 'packet_sha256': self.packet_hash,
            'decisions': {'guide.txt': {'candidate': 'ours and theirs\r\nsecond\r\n',
                                       'reason': 'Keep both contributions.'}}}), encoding='utf-8')
        output = self.root / 'resolved'
        self.receipt = f.finish(self.packet, self.inputs, decisions, output, self.packet_hash)
        self.pin()
        self.assertTrue(self.audit(output)['matches'])
        (output / 'guide.txt').write_text('ours only\n')
        self.assertEqual(self.audit(output)['changed'], ['guide.txt'])

    def test_cli_success_drift_and_error_codes(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['matches'])
        (self.staged / 'guide.txt').unlink()
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)['missing'], ['guide.txt'])
        result = self.cli(hashlib.sha256(b'wrong retained pin').hexdigest())
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
