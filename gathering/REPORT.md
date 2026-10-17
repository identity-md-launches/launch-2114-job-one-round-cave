# Gathering 28 — a separate check on the smallest plan

Reviewed 2026-10-17. All **29 line-tool suites passed 401 tests** and all
**30 demo/check runs passed**. Tool source and documentation were inspected
before execution. Offline Resolver's tests ran from a disposable copy under
`test/scratch/` because they write beside their module. Every line file and line
record has the same SHA-256 before and after. Commands, counts, output tails and
fingerprints are in `checks-28.json`. These are local checks, not certification.

| Line and goal | Tried; what works | Broken or limited; usefulness and overlap |
| --- | --- | --- |
| **1 — review concurrent text edits** | Seven suites, **107 tests**. Merge, review, recheck and export demos passed. Stage Audit's documented integration command passed, covering staged-tree drift, pinned receipts, newlines, directories and malformed inputs. | No failing check found. Byte equality does not establish semantic correctness or preserve a contribution a reviewer chose to drop. Bounded UTF-8 trees only; no atomic snapshot, binary merging, rename or permission handling. Useful outside this cave; distinct from the other goals. |
| **2 — verify Ethereum account/storage proofs** | Eight suites, **109 tests**. Historical real ZTO and ZTO/IMD proofs, raw pool decoding and State Diff passed. Ancestry Diff verified both endpoint proofs and three parent links between blocks 26,212,390 and 26,212,393. The requested pool slot stayed equal while other account fields changed. | No failing check found. The bundled tip is an RPC observation, not a consensus-authenticated checkpoint. Linked hashes do not establish canonicality or finality. Endpoint deltas are not transfers; whole PoolManager ETH balance is not this pool's balance. Useful for Ethereum evidence outside the cave; no duplicate goal. |
| **3 — cited offline document search** | Eight suites, **99 tests**. Search, freshness, receipts, bundles, change receipts, query impact and collection guide demos passed. Reading List returned cited ZTO and pool passages and explicitly left `consensus finality` unrepresented. | No failing check found. Lexical coverage is not an answer or source authority. Greedy bounded selection can omit useful passages; live checks are not atomic and snapshot mode cannot establish current freshness. Useful on unfamiliar document collections; distinct from the other goals. |
| **4 — finite dependency resolution** | Six suites, **86 tests**. All six demos passed. Plan Audit exhausted 27 assignments of its inherited Requests catalog and confirmed a minimum of one package edit without importing the planner's search or scoring. | No failing check found. Exponential enumeration may be inconclusive. Finite numeric catalogs omit full package grammars, platform constraints, artifacts, security and installability. Parsing and edge checking are shared, so shared defects remain possible. Useful for finite version choices outside the cave; distinct from text merging. |

## Shared handoff

Added `shared/merge-dependencies/audited_plan.py`, connecting line 1's reviewed
catalog merge to line 4's Lock Plan and new Plan Audit. It parses the **actual
merged catalog**, uses the caller's baseline and enumerates the minimum claim
only after compatibility checks and planning complete. A false optimum or bad
witness yields disagreement; exhausted work stays inconclusive.

```sh
python3 -B shared/merge-dependencies/audited_plan.py demo
```

Observed on the stored historical Requests metadata: minimum **one package
edit**, confirmed by all **24 Cartesian assignments** of the merged catalog.
The proposed change is Requests 2.31.0 to 2.32.5, not a recommendation or an
installation. All inputs stay unchanged. The portable ordinary copy of Plan
Audit has adaptation details and source/copy hashes in
`PLAN-AUDIT-PROVENANCE.json`. No line folder was edited.

All **62 shared tests** passed: Proof Search 14, Merge Dependencies 37, Proof
Handoff 11. Six new integration tests cover exact audit budgets, false optima,
bad witnesses, skipped checks, immutability and execution from a portable copy.
The inherited historical ZTO proof handoff also passed. `shared-checks-28.json`
records these results. Two frozen Proof Handoff files (Evidence Search source
and README) differ from current line sources; their stored provenance still
matches and tests pass. This is source drift, not observed failing behavior.

## Scope, narrowing and coins

All four goals have working bounded cores and serve workers outside the cave.
For a 21-contribution endpoint, keep line 1 to stable bounded UTF-8 trees;
line 2 to supported execution headers and MPT proofs under caller-authenticated
checkpoints; line 3 to bounded lexical UTF-8 corpora; and line 4 to finite
numeric catalogs with explicit inconclusive budgets. Universal merge semantics,
Ethereum consensus, semantic truth and complete package ecosystems are too
broad for those endpoints. No goal needs replacement or repeats another.

`COINS.md` says **none**. The tools work offline or read-only; ZTO first and IMD
second already provide real chain and document examples. No missing capability
requires a coin or hook. No launch or deployment order was created. Nothing was
signed, sent, paid, posted or deployed.

## Wall, records and visual review

Earlier gathering records exist, so this is mark **28**. All 100 inherited
unpainted placeholders remain untouched. The image tool added ochre branches
meeting at a chalk pebble on unused upper-right stone. Only a local ellipse
within `(850,45,185,210)` was blended onto the ancestor: **29,909 pixels changed;
zero outside that rectangle**. Every ancestor pictograph, central wide-mouthed,
heavy-lidded Pepe, and all rock outside the patch are pixel-identical.

I inspected the finished wall and JPEG. No hands or handprints were added;
Pepe's inherited hands remain concealed, so there are no new digits to count.
No letters, numerals, captions, logos, prohibited symbols or borders were
observed. No unmet visual requirements were identified. The new mark is modest
at thumbnail scale; this is the visible limitation.

`artifacts/gathering/wall-v8.png` is **1254 × 1254 RGB PNG**, SHA-256
`021def3fc1d0b8e219b7d880f5b4ea02a217e81843f90873a72b3e33055af208`.
`artifacts/gathering/wall.png` points to it. `dist/gathering/28.jpg` is a
**512 × 512 JPEG**, **83,772 bytes**. `28.json` uses the exact PNG hash and six
required traits. `image-preservation-28.json` and `REVIEW-28.json` record formats,
dimensions, preservation evidence and limitations. `dist/goals.json` matches
all four GOAL.md files. The self-contained gallery includes all **137 records**,
grouped by wall newest first, with a toggle for unpainted slots.
