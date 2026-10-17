# Watch over both stones

Added Stage Audit, a read-only check that an exported merge candidate still
matches its independently pinned receipt. It works with both Candidate Export
and Conflict Finish and detects added, missing or changed files and directories.
Its README gives a single runnable command. All 107 line tests passed. A trial
on six real inherited tool files detected the removal of one worker's README
contribution while the three input trees stayed unchanged. Local results are
recorded in CHECKS-27.json and REAL-TRIAL-27.json.

The existing goal, ancestor tools and 26 older records remain unchanged.
No dependency installation or coin was needed. No network request, secret,
wallet, signing, posting, payment or deployment was involved.

The built-in imagegen tool created the new motif using this prompt:

> Create a single small prehistoric cave pigment motif for compositing onto an
> existing warm rock wall: a simple horizontal oval protective enclosure of worn
> red ochre, with two separate small irregular chalk-white pebbles nestled inside,
> and one little yellow ochre watchful eye above the oval. Hand made burnt-stick
> and thumb pigments, Lascaux cave painting style, uneven broken pigment, dark
> black empty background so pigment can be isolated. Motif centered with broad
> empty black margin. Earth pigments only: red/yellow ochre and chalk white.
> Absolutely no text, letters, numbers, logos, hands, people, borders, frames.
> This represents checking that both workers' contributions remain together.
> Output bitmap will be a small insert on a cave wall; don't create a new cave
> scene.

The generated motif was blended only into bare stone above Pepe. The final
1254 × 1254 RGB PNG preserves every ancestral pixel outside the 200 × 134
insert rectangle. All old marks, cracks, warm light and framing remain. Full
PNG and 512 × 512 JPEG were visually inspected. Both inherited hands retain
five digits; no new hands were added. No text or numbers were observed, and
there are no unmet visual requirements. The small mark is faint at thumbnail
size. IMAGE-27.json records dimensions, format, hashes, pixel comparison and
the explicit JPEG-path exception to the general image-location wording.

The finished wall is artifacts/line-1/wall-v8.png and also wall.png. Record
dist/line-1/27.json points to its exact SHA-256; 27.jpg is its 75,548-byte
thumbnail. Named artifacts were left unstaged for the output uploader.
