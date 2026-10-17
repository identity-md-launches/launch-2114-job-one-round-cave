"""Keep generated pigment for round 28 while preserving all inherited pixels elsewhere."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('png_codec28', 'gathering/finish_wall.py')
png = importlib.util.module_from_spec(spec)
spec.loader.exec_module(png)

OLD = Path('artifacts/line-2/wall-v7.png')
NEW = Path('artifacts/line-2/wall-v8.png')
PREVIEW = Path('dist/line-2/28.jpg')
RECT = (270, 200, 135, 51)
EXPECTED = '2f340b47655c9dbd3a591132f3ede4c2b9a8948f0c45714093b302dd944aa947'


def main():
    ancestor_sha = hashlib.sha256(OLD.read_bytes()).hexdigest()
    assert ancestor_sha == EXPECTED, 'unexpected inherited wall'
    draft_sha = hashlib.sha256(NEW.read_bytes()).hexdigest()
    width, height, original = png.read_png(OLD)
    dw, dh, draft = png.read_png(NEW)
    assert (width, height) == (dw, dh) == (1254, 1254)
    final = original[:]
    x0, y0, rw, rh = RECT
    ellipses = ((291, 222, 18, 20), (336, 229, 18, 20), (385, 223, 21, 24))
    for y in range(y0, y0 + rh):
        for x in range(x0, x0 + rw):
            index = (y * width + x) * 3
            r, g, b = draft[index:index + 3]
            old = original[index:index + 3]
            distance = min(((x-cx)/rx)**2 + ((y-cy)/ry)**2
                           for cx, cy, rx, ry in ellipses)
            red = distance < 1.16 and 70 < r < 195 and r > 2.0*g and r > 3*b
            # The generated charcoal cord runs between the ochre pebbles.
            cord = (300 <= x <= 374 and 219 <= y <= 227 and
                    r < 100 and g < 67 and b < 50 and
                    sum(abs(draft[index+c]-old[c]) for c in range(3)) > 24)
            chalk = (380 <= x <= 392 and 216 <= y <= 233 and
                     r > 150 and g > 110 and b > 75 and
                     sum(draft[index+c]-old[c] for c in range(3)) > 80)
            if red or cord or chalk:
                fade = min(1, (x-x0)/3, (x0+rw-1-x)/3,
                           (y-y0)/3, (y0+rh-1-y)/3)
                alpha = 0.91*max(0, fade)
                for c in range(3):
                    final[index+c] = round(old[c]*(1-alpha) + draft[index+c]*alpha)
    changed = 0
    for i in range(width * height):
        if final[3*i:3*i+3] != original[3*i:3*i+3]:
            changed += 1
            x, y = i % width, i // width
            assert x0 <= x < x0+rw and y0 <= y < y0+rh
    assert changed > 1500, 'generated pigment was not retained'
    digest = png.write_png(NEW, width, height, final)
    continuation = Path('artifacts/line-2/wall.png')
    assert continuation.is_symlink() and continuation.readlink() == Path('wall-v7.png')
    continuation.unlink()
    continuation.symlink_to('wall-v8.png')
    rgba = bytearray()
    for y in range(512):
        ya, yb = y*height//512, (y+1)*height//512
        for x in range(512):
            xa, xb = x*width//512, (x+1)*width//512
            n = (yb-ya)*(xb-xa)
            for c in range(3):
                rgba.append(round(sum(final[(sy*width+sx)*3+c]
                                      for sy in range(ya, yb) for sx in range(xa, xb))/n))
            rgba.append(255)
    js = """
const fs = require('fs');
const encode = require('./line-3/tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');
const data = fs.readFileSync(0);
if (data.length !== 512*512*4) throw Error('bad input');
const result = encode({data,width:512,height:512},78);
if (result.data.length > 100000) throw Error('JPEG too large');
fs.writeFileSync('dist/line-2/28.jpg',result.data);
"""
    subprocess.run(['node', '-e', js], input=rgba, check=True)
    report = {'round': 28, 'ancestorSha256': ancestor_sha,
              'generatedDraftSha256': draft_sha, 'wallSha256': digest,
              'dimensions': [width, height], 'format': 'PNG', 'channels': 'RGB',
              'newMarkRectangle': list(RECT), 'changedPixels': changed,
              'changedPixelsOutsideRectangle': 0,
              'method': 'Built-in imagegen; retained only its new pigment on bare rock.',
              'visualReview': 'Pending final inspection', 'unmetVisualRequirements': [],
              'images': []}
    for path, kind, size in ((NEW, 'PNG', [1254, 1254]),
                             (continuation, 'PNG', [1254, 1254]),
                             (PREVIEW, 'JPEG', [512, 512])):
        data = path.read_bytes()
        report['images'].append({'path': str(path), 'format': kind,
                                 'dimensions': size, 'bytes': len(data),
                                 'sha256': hashlib.sha256(data).hexdigest()})
    Path('line-2/REVIEW-28.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
