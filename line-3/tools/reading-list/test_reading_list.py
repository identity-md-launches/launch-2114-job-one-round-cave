"""Behavioral tests for bounded multi-query reading lists, using local mock text."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('reading_list', Path(__file__).with_name('reading_list.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def index(**docs):
    return {'format': r.engine.FORMAT, 'documents': [
        {'path': p, 'text': t, 'sha256': r.engine.digest(t.encode())} for p, t in docs.items()]}


class ReadingTests(unittest.TestCase):
    def test_shared_passage_covers_two_queries_before_single(self):
        value = r.plan(index(**{'a.md': 'apple', 'b.md': 'apple pear', 'c.md': 'pear'}),
                       ['apple', 'pear'], budget=1)
        self.assertEqual(value['passages'][0]['path'], 'b.md')
        self.assertTrue(value['all_queries_represented'])
        self.assertEqual(len(value['passages']), 1)
        self.assertEqual(len(value['passages'][0]['query_ranks']), 2)

    def test_gaps_distinguish_absent_and_budget(self):
        value = r.plan(index(**{'a.md': 'apple', 'b.md': 'pear'}),
                       ['apple', 'pear', 'kiwi'], budget=1)
        self.assertEqual([q['status'] for q in value['queries']],
                         ['represented', 'budget_or_overlap', 'no_candidates'])
        self.assertFalse(value['all_queries_represented'])

    def test_exact_crlf_and_unicode_citations(self):
        data = index(**{'fruit.md': '\r\nＣＡＦÉ pear\r\nnext\r\n'})
        value = r.plan(data, ['café', 'pear'])
        hit = value['passages'][0]
        self.assertEqual(hit['citation'], 'fruit.md:2-3')
        self.assertEqual(hit['text'], 'ＣＡＦÉ pear\nnext')
        self.assertFalse(hit['source_verified'])
        self.assertEqual(hit['sha256'], data['documents'][0]['sha256'])

    def test_deterministic_immutable_order_independent(self):
        data = index(**{'z.md': 'apple pear', 'a.md': 'apple pear'})
        saved = copy.deepcopy(data)
        first = r.plan(data, ['apple', 'pear'])
        self.assertEqual(data, saved)
        data['documents'].reverse()
        self.assertEqual(first, r.plan(data, ['apple', 'pear']))
        self.assertEqual(first['passages'][0]['path'], 'a.md')

    def test_global_overlaps_suppressed(self):
        text = '\n'.join(['apple'] * 9 + ['pear'] * 9 + ['plum'] * 9)
        value = r.plan(index(**{'a.md': text}), ['apple', 'pear', 'plum'], budget=30)
        hits = value['passages']
        for a in hits:
            for b in hits:
                if a is not b:
                    self.assertTrue(a['line_end'] < b['line_start'] or b['line_end'] < a['line_start'])

    def test_require_all(self):
        data = index(**{'a.md': 'apple', 'b.md': 'pear'})
        self.assertEqual(len(r.plan(data, ['apple pear'])['passages']), 2)
        self.assertEqual(r.plan(data, ['apple pear'], require_all=True)['passages'], [])

    def test_invalid_queries_and_bounds(self):
        data = index(**{'a.md': 'apple'})
        for queries in ([], ['apple'] * 13, ['Apple', 'ＡＰＰＬＥ'], ['!!!'], ['x' * 4097], [None]):
            with self.subTest(queries=str(queries)[:60]), self.assertRaises(r.engine.SearchError):
                r.plan(data, queries)
        for kwargs in ({'budget': 0}, {'budget': 31}, {'budget': True}, {'depth': 0},
                       {'depth': 51}, {'depth': '1'}, {'require_all': 1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(r.engine.SearchError):
                r.plan(data, ['apple'], **kwargs)

    def test_validates_unselected_sources(self):
        data = index(**{'a.md': 'apple', 'b.md': 'pear'})
        data['documents'][1]['text'] = 'forged'
        with self.assertRaises(r.engine.SearchError):
            r.plan(data, ['apple'])

    def test_empty_corpus(self):
        value = r.plan(index(), ['apple'])
        self.assertEqual(value['passages'], [])
        self.assertEqual(value['queries'][0]['status'], 'no_candidates')

    def test_depth_is_explicit_candidate_limit(self):
        data = index(**{'a.md': 'apple', 'b.md': 'apple', 'c.md': 'apple'})
        value = r.plan(data, ['apple'], budget=3, depth=1)
        self.assertEqual(value['candidate_depth_per_query'], 1)
        self.assertEqual(value['queries'][0]['candidate_count'], 1)
        self.assertEqual(len(value['passages']), 1)

    def test_live_verification_rejects_changed_missing_and_symlink(self):
        Path('test/scratch').mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir='test/scratch') as folder:
            root = Path(folder)
            source = root / 'a.md'
            source.write_bytes(b'apple')
            data = r.engine.build_index(root)
            self.assertTrue(r.plan(data, ['apple'], root=root)['passages'][0]['source_verified'])
            source.write_bytes(b'pear')
            with self.assertRaises(r.engine.SearchError):
                r.plan(data, ['apple'], root=root)
            source.unlink()
            with self.assertRaises(r.engine.SearchError):
                r.plan(data, ['apple'], root=root)
            (root / 'b.md').write_bytes(b'apple')
            source.symlink_to('b.md')
            with self.assertRaises(r.engine.SearchError):
                r.plan(data, ['apple'], root=root)

    def test_cli_outputs_no_partial_results_on_error(self):
        Path('test/scratch').mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir='test/scratch') as folder:
            Path(folder, 'a.md').write_bytes(b'apple')
            for queries, expected in ((['apple'], 0), (['pear'], 1), (['!!!'], 2)):
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    code = r.main(['scan', folder, '--query', queries[0]])
                self.assertEqual(code, expected)
                if code == 2:
                    self.assertEqual(out.getvalue(), '')
                    self.assertIn('error', json.loads(err.getvalue()))
                else:
                    self.assertEqual(err.getvalue(), '')
                    self.assertIn('passages', json.loads(out.getvalue()))

    def test_real_historical_demo_and_status(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(r.main(['demo']), 0)
        value = json.loads(out.getvalue())
        citations = [p['citation'] for p in value['passages']]
        self.assertIn('zto.md:1-9', citations)
        self.assertIn('pool.md:1-10', citations)
        self.assertEqual(value['queries'][2]['status'], 'no_candidates')
        self.assertTrue(all(p['source_verified'] for p in value['passages']))


if __name__ == '__main__':
    unittest.main()
