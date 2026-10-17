# Stage Audit

Check that a staged merge still matches the exact export receipt a reviewer
retained. This closes the gap between exporting a candidate and using it later:
an added file, missing contribution, changed newline or extra empty directory
produces a mismatch. Python 3.10+ standard library only; no installation,
network, coin or wallet is needed.

From the workspace root, one command shows working exports, drift detection and
failure handling on disposable files under `test/scratch/`:

```sh
python3 -B line-1/tools/stage-audit/test_audit.py
```

When tried, all **13 integration tests passed**, along with all 94 ancestor
tests. The checks cover Candidate Export and Conflict Finish receipts, exact
CRLF/Unicode/empty files, additions, deletions, same-length changes, empty
directories, moved candidates, receipt pins, inconsistent manifests, malformed
JSON/types/paths, links, workspace escape, binary/oversized input and CLI exits.
The audit left source and candidate bytes unchanged.

For a real staged candidate, save the JSON stdout receipt from Candidate Export
or Conflict Finish **outside the staged tree**. Review the receipt and retain
its exact SHA-256 independently. Run:

```sh
python3 -B line-1/tools/stage-audit/audit.py RECEIPT.json STAGED_DIR --expected-sha256 RETAINED_RECEIPT_SHA256
```

Replace these uppercase arguments with actual workspace paths and your retained
64-digit lowercase digest. The pin is the hash of the **receipt**, not the
earlier merge packet. Reformatting a receipt changes its pin. A pin supplied
by the same untrusted source as the receipt provides no authentication.

The tool validates the receipt's file fingerprints and independently reconstructs
its directory-inclusive manifest before reading the candidate. It compares that
with the bounded current tree and prints `stage-audit/v1` JSON containing
`matches`, sorted `added`, `missing`, `changed`, `added_directories` and
`missing_directories`, plus expected/actual manifests and the exact receipt hash.
It never follows `output` or any other path metadata inside the receipt. You
can therefore audit a candidate copied to a different directory.

Exit **0** means exact reproduction of the staged file tree; **1** means drift;
**2** means an invalid receipt, wrong pin, unsupported input or filesystem error.
An error produces no partial JSON on stdout. Unsupported binary files, symlinks
and unreadable trees produce 2 rather than a list of differences. All untrusted
text is JSON-quoted or escaped for terminal output.

Keep the sibling `review-recheck`, `tree-review`, `merge-review` and `threeway`
folders; their bounded readers and canonical manifest format are reused.
Export tools are required to create receipts, but not imported by the audit.
The integration tests also require `candidate-export` and `conflict-finish`.

## Limits and observed real-file trial

This checks byte preservation, not correctness, approval, authorship or whether
a reviewer chose to discard a contribution. It does not recompute the original
merge or validate conflict reasons; use Review Recheck for source-tree drift.
Files must be UTF-8 without NUL, at most 1 MiB/4,000 lines each; a tree is at
most 128 files, 256 directories, 16 directory levels and 8 MiB total. Receipts
are capped at 1 MiB. Receipt file names must be canonical relative POSIX paths
without backslashes. Only the directories needed to contain exported files are
expected: extra empty directories count as drift.

Run from the workspace root, with stable trusted inputs and no symlink path
components. There is no atomic snapshot or protection against concurrent path
replacement; changes after the check remain possible. Permissions, executable
bits, timestamps, binary files and renames are not checked. The command reads
only the supplied workspace receipt and candidate; it writes nothing.

An extra trial used copies of the inherited Threeway tool's six real source,
documentation and example files. Independent README edits merged and audited
successfully. Removing one contribution from the staged README returned a
mismatch naming only `README.md`. All three original trees stayed unchanged.
See `../../REAL-TRIAL-27.json` for the observations and exact receipt hashes.
