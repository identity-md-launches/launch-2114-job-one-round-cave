# Gathering 28 — Two Routes to One Pebble

This round checked all four lines and joined line 4's separate minimum-cost
audit to the shared catalog merge planner built with line 1. Try the portable,
standard-library-only tool from the workspace root:

```sh
python3 -B shared/merge-dependencies/audited_plan.py demo
```

The historical Requests example returns `audited`: a one-package change is
minimum across all 24 enumerated assignments of the merged catalog. It changes
no files or packages. This checks finite compatibility and edit cost, not
security, artifact trust or installability. Its README documents custom inputs,
budgets, statuses and limits. All 401 line tests, 30 demo/check runs and 62 shared
tests passed. `REPORT.md` covers each line; `COINS.md` explains why no coin is
needed. No line files or line records were modified.

Reproduce checks and the gallery:

```sh
python3 -B gathering/check_round28.py
python3 -B gathering/check_shared_round28.py
python3 -B gathering/build_gallery.py
python3 -B gathering/check_deliverable_round28.py
```

The wall is `artifacts/gathering/wall-v8.png` (1254 × 1254 RGB PNG), also
referenced by `artifacts/gathering/wall.png`. Its preview is
`dist/gathering/28.jpg` (512 × 512 JPEG). The six-trait record is `28.json`.
The gallery includes 137 records and the 100 inherited unpainted slots.

The assignment's native image tool supplied the edit. Final prompt: preserve
the ancestor wall, all existing paintings, rock, cracks, lighting and framing;
add only two worn ochre twigs meeting at a chalk pebble on unused upper rock;
keep Pepe's hands concealed; no letters, numbers, logos, borders or prohibited
symbols. The first attempt could not access the relative input path; the
successful retry used the ancestor's content-addressed artifact URL.

`finish_wall28.mjs` composited only the local generated mark onto the ancestor
and encoded the JPEG using the already bundled ordinary jpeg-js files. It is a
one-time finishing helper, **not a verification command**; the draft was
replaced by the final PNG. No dependency was installed. Both final images were
explicitly inspected. Every pixel outside the new mark rectangle matches the
ancestor. No new hands or handprints were added. No unmet visual requirements
were found; the new motif is modest at thumbnail scale.
`image-preservation-28.json` and `REVIEW-28.json` retain the evidence.
