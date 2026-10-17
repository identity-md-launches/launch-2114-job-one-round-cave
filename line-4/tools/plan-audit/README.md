# Plan Audit

Independently check a Lock Plan minimum-package-edit claim by enumerating a
small finite catalog. A worker receiving a proposed dependency migration can
check its selected versions and minimum cost without running the planner's
search or trusting its search count.

From the repository root, run this offline demonstration:

```sh
python3 -B line-4/tools/plan-audit/audit_plan.py demo
```

Tried here: **verified**, all **27 Cartesian assignments** exhausted, confirming
that moving Requests 2.31.0 to 2.32.5 while keeping the other four saved releases
costs a minimum of **one package edit**. The demo claim is explicitly constructed
from the inherited Requests metadata snapshot and chosen baseline; it is not an
observed installation or a recommendation. No network, package code or installer
is involved. Sources: [catalog provenance](../offline-resolver/examples/sources.json),
[baseline provenance](../lock-plan/README.md).

Python 3.9+ standard library only. Keep this folder beside `exhaustive-audit/`,
`offline-resolver/` and, for the demo, `lock-plan/`. It reads explicit workspace
JSON files and writes JSON only to stdout. Nothing is installed or applied.

For a saved planner result, catalog and baseline:

```sh
python3 -B line-4/tools/plan-audit/audit_plan.py path/to/catalog.json --baseline path/to/baseline.json --report path/to/plan.json --max-assignments 10000
```

Input formats and numeric version constraints are those of
[Offline Resolver](../offline-resolver/README.md). Baseline is a package-to-version
object of at most 1,000 entries; historical versions may be absent from the
catalog. Aliases normalize, collisions are rejected. The report must claim
`status: optimal` and provide `selected` and an integer `minimum_change_count`.
The selected map must contain exactly the reachable catalog releases. Version
changes, additions and removals each cost one; numeric version aliases cost zero.
Every current root stays mandatory. Empty root sets follow the inherited grammar
and are rejected. Unknown report metadata is ignored.

| Exit | Status | Meaning |
| --- | --- | --- |
| 0 | `verified` | Valid claimed witness; every Cartesian assignment exhausted; no lower-cost solution exists in this catalog. |
| 1 | `rejected` | Witness cost differs from claim, or a checked lower-cost counterexample exists. A counterexample does not claim the global minimum. |
| 2 | `invalid` | Bad input, unsupported claim, invalid witness, path or read error. |
| 3 | `inconclusive` | Assignment budget exhausted. No minimum is certified. |

Budget is 1–1,000,000 complete tuples (default 10,000). Completing exactly at
the limit succeeds. Enumeration is exponential. Domains include every release
of every potentially reachable dependency, plus absence for nonroots, and can
repeat equivalent reachable selections through irrelevant choices. Every valid
selection is represented. An iterative edge traversal checks all incoming
constraints and terminates on cycles. Dependencies of abandoned releases only
expand enumeration; they cannot invalidate a witness.

Plan Audit shares parsing and the separate edge checker with Exhaustive Audit;
it imports **neither Lock Plan nor its scoring/search functions**. Its cost
calculation and full Cartesian enumeration provide a different check on the
planner's branch search. Shared parser/checker defects remain possible. Budgets
bound assignments, not memory, parsing time or wall-clock time. This is a local
computational check, not formal verification or independent certification.

Only compatibility, witness cost and minimum are audited. Other report fields
(`changes`, planner digest, step count, claimed baseline) are not authenticated
or checked; the explicit baseline argument is authoritative. The output digest
binds the normalized supplied catalog and baseline, not their origin. Full PEP
440, platform markers, extras, availability, artifact hashes, security and
publisher trust remain outside scope. A verified finite-catalog optimum does
not establish installability or that a plan is safe to execute.

Checks:

```sh
python3 -B -m unittest discover -s line-4/tools/plan-audit -p 'test_*.py' -v
```

All **13 tests passed**, covering the real metadata demo, false optima, witness
miscounts, exact budget boundaries, cycles and conflicting incoming edges,
abandoned dependencies, removals, aliases, invalid inputs, immutable inputs,
digest changes, disabled inherited search functions, CLI statuses and duplicate
JSON keys. Also compared 500 seeded small catalogs with Lock Plan. Tests use
only `test/scratch/` for temporary input files; no network or external paths.
