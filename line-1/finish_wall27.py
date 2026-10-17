"""Compose imagegen pigment onto untouched stone, then encode the final JPEG.

Consumes the generated motif temporarily held at the required wall-v8 path.
Run only once against the pinned ancestor. No external files or network.
"""
import hashlib
import json
from pathlib import Path
from finish_wall24 import read_png, write_png, thumbnail


def main():
    wall = Path('artifacts/line-1/wall.png')
    output = Path('artifacts/line-1/wall-v8.png')
    ancestor = wall.read_bytes()
    ancestor_sha = hashlib.sha256(ancestor).hexdigest()
    assert ancestor_sha == '0210046796467d225bdb7d099d5d96c8c00802d381c1be3b4b0995574acfcca0'
    width, height, old = read_png(ancestor)
    gw, gh, pigment = read_png(output)
    assert (width, height) == (1254, 1254)
    assert (gw, gh) == (1536, 1024)
    final = old[:]
    # Bare stone above Pepe, well left of the ancestral reviewing eye.
    x0, y0, mw, mh = 380, 238, 200, 134
    sx0, sy0, sw, sh = 275, 140, 980, 680
    for y in range(mh):
        for x in range(mw):
            sx, sy = sx0 + int(x * sw / mw), sy0 + int(y * sh / mh)
            rgb = pigment[(sy * gw + sx) * 3:(sy * gw + sx) * 3 + 3]
            strength = max(rgb)
            if strength < 30:
                continue
            alpha = min(.80, (strength - 30) / 150)
            alpha *= min(1, x / 5, y / 5, (mw - 1 - x) / 5, (mh - 1 - y) / 5)
            i = ((y0 + y) * width + x0 + x) * 3
            for channel in range(3):
                final[i + channel] = round(old[i + channel] * (1 - alpha) + rgb[channel] * alpha)
    changed, outside = 0, 0
    for pixel in range(width * height):
        if old[pixel * 3:pixel * 3 + 3] != final[pixel * 3:pixel * 3 + 3]:
            changed += 1
            x, y = pixel % width, pixel // width
            outside += not (x0 <= x < x0 + mw and y0 <= y < y0 + mh)
    assert changed and outside == 0
    sha = write_png(output, width, height, final)
    assert read_png(output)[2] == final
    wall.write_bytes(output.read_bytes())
    jpeg = Path('dist/line-1/27.jpg')
    thumbnail(output.read_bytes(), jpeg)
    report = {
        'ancestor_sha256': ancestor_sha, 'wall_sha256': sha,
        'wall_paths': [str(output), str(wall)], 'dimensions': [width, height],
        'format': 'PNG', 'mode': 'RGB',
        'thumbnail': {'path': str(jpeg), 'dimensions': [512, 512],
                      'format': 'JPEG', 'bytes': jpeg.stat().st_size},
        'mark_rectangle': [x0, y0, mw, mh], 'changed_pixels': changed,
        'changed_pixels_outside_rectangle': outside,
        'method': 'Built-in imagegen motif; pigment composited only on bare rock.',
        'unmet_visual_requirements': [],
        'location_conflict': 'The specifically required dist/line-1/27.jpg is used despite the general no-pictures-outside-artifacts sentence.'}
    Path('line-1/IMAGE-27.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
