# Cited Reading List

Turn several questions about an unfamiliar local collection into one bounded
reading list. Passages keep exact relative paths, inclusive source line ranges,
original byte hashes and excerpts. A passage that appears in several query
results is listed once, with its rank for each query. Queries without a selected
passage stay visible. Python 3.9+ and the standard library only; retain the
adjacent `evidence-search/` folder. No network, installation or configuration.

From the repository root, one command shows it working without writing files:

```sh
python3 -B line-3/tools/reading-list/reading_list.py demo
```

When tried, the demo returned `pool.md:1-10` for `pool tick spacing` and
`zto.md:1-9` for `ZTO decimals`. Both sources were re-read and hash-checked.
It explicitly reported `consensus finality` as `no_candidates`. These are the
inherited historical ZTO-first observations and assignment-supplied pool
parameters, not a current quote or independent chain proof. Full output is in
`line-3/TRIAL-28.json`. The demo deliberately includes this missing query and
exits 0 when the demonstration succeeds.

For an existing UTF-8 collection inside your workspace:

```sh
python3 -B line-3/tools/reading-list/reading_list.py scan line-3/tools/evidence-search/examples/docs --query 'ZTO decimals' --query 'pool tick spacing' --all --budget 3
```

For an existing Evidence Search index, without restoring its source files:

```sh
python3 -B line-3/tools/reading-list/reading_list.py snapshot line-3/my-index.json --query 'first question' --query 'second question' --budget 5 --depth 10
```

Replace `line-3/my-index.json` with a real saved index. `snapshot` validates all
embedded source hashes; its passages have `source_verified: false`. `scan`
builds an in-memory snapshot and verifies each selected file against its hash
before emitting any output. Neither command creates files. All paths must stay
inside the current working directory, without symlinks or parent traversal.
Keep the collection static during use; checks are not an atomic snapshot or a
sandbox against concurrent file replacement. Only selected live files are
rechecked; use Corpus Freshness for whole-collection drift detection.

Each query uses the inherited BM25 engine and up to `--depth` ranked,
non-overlapping candidates. Distinct normalized term sets are required, so
repeating a query cannot inflate its importance. `--all` requires every query
term within a candidate passage; otherwise any matching term qualifies.
Identical path/line spans are combined. At each step the planner selects the
passage representing the most as-yet-unrepresented queries, then breaks ties
by the sum of `1/(60 + rank)` across its query results, then by path and line.
Fractions are compared exactly; only the displayed score is rounded. Selected
windows cannot overlap within a source, even across queries. Once every query
has a passage, remaining budget can add further relevant passages.

The budget is a maximum, not a promise of a minimum-sized or optimal set.
Greedy selection, overlap suppression and candidate truncation can exclude
useful passages. `represented` means a selected span occurred in that query's
bounded lexical result list; it does not assert an answer, entailment, authority
or truth. `no_candidates` means no result under the lexical query rules;
`budget_or_overlap` means candidates existed but none survived selection.
Neither status proves information is absent from the full collection. Queries
are ranked independently; raw BM25 scores are intentionally not added across
queries. The snapshot hash binds canonical JSON of the validated, path-sorted
Evidence Search envelope, not authorship or present-day freshness.

Limits: 1–12 queries of at most 4,096 characters, 1–30 selected passages,
candidate depth 1–50 per query. Collection limits inherit Evidence Search:
1,000 UTF-8 `.md`/`.txt`/`.rst` files, 1 MB each, 8 MB total, 16 MB saved index,
16,000 characters per line and 20,000 nonempty windows. Indexing excludes hidden
entries and symlinks. CPU work repeats the bounded ranker once per query.
Full output can be large when source lines are long. Document content is inert
untrusted data; consumers must render excerpts as text, never execute them.

`scan`/`snapshot` exit 0 when every query is represented, 1 for a valid list with
gaps, and 2 for invalid input or I/O failure. JSON goes to stdout; errors go to
stderr without a partial stdout report. `all_queries_represented` is also
included so consumers need not infer coverage from the exit code.

Thirteen behavioral tests passed:

```sh
python3 -B line-3/tools/reading-list/test_reading_list.py -v
```

They cover shared passages, lexical gaps versus budget gaps, exact CRLF and
Unicode citations, deterministic selection and immutable input, cross-query
overlaps, all-term mode, query/budget/depth bounds, forged unselected sources,
empty collections, candidate truncation, live stale/missing/symlink rejection,
CLI result/error behavior and the real historical demo. Temporary files stay
in `test/scratch/`. No source documents or ancestor tools are changed.
