"""One-shot preservation and JPEG encoding of the image tool's new addition."""
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('png_codec', Path(__file__).with_name('finish_wall22.py'))
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
ancestor = Path('artifacts/line-4/wall.png')
output = Path('artifacts/line-4/wall-v8.png')
assert ancestor.read_bytes() == Path('artifacts/line-4/wall-v7.png').read_bytes(), 'expected ancestor; never apply twice'
old_sha = hashlib.sha256(ancestor.read_bytes()).hexdigest()
w, h, original = codec.read_png(ancestor)
dw, dh, generated = codec.read_png(output)
assert (w, h) == (dw, dh) == (1254, 1254)
final = original[:]
x0, y0, x1, y1 = 345, 180, 635, 320
# Only unused rock above Pepe. Feather the boundary of the generated patch;
# no pigment or older mark is synthesized, moved, redrawn or covered.
for y in range(y0, y1):
    for x in range(x0, x1):
        weight = min(1.0, min(x-x0, x1-1-x, y-y0, y1-1-y)/10)
        at = (y*w+x)*3
        for c in range(3):
            final[at+c] = round(original[at+c]*(1-weight)+generated[at+c]*weight)
points = [(i % w, i // w) for i in range(w*h)
          if final[3*i:3*i+3] != original[3*i:3*i+3]]
assert points and all(x0 <= x < x1 and y0 <= y < y1 for x,y in points)
sha = codec.write_png(output, w, h, final)
assert codec.read_png(output)[2] == final

# Reuse the previous round's libgd encoder solely for the required JPEG.
gd = ctypes.CDLL('libgd.so.3')
ptr, integer = ctypes.c_void_p, ctypes.c_int
gd.gdImageCreateFromPngPtr.argtypes = [integer, ptr]
gd.gdImageCreateFromPngPtr.restype = ptr
gd.gdImageCreateTrueColor.argtypes = [integer, integer]
gd.gdImageCreateTrueColor.restype = ptr
gd.gdImageCopyResampled.argtypes = [ptr, ptr] + [integer]*8
gd.gdImageJpegPtr.argtypes = [ptr, ctypes.POINTER(integer), integer]
gd.gdImageJpegPtr.restype = ptr
gd.gdFree.argtypes = [ptr]
gd.gdImageDestroy.argtypes = [ptr]
raw = output.read_bytes()
buffer = ctypes.create_string_buffer(raw)
source = gd.gdImageCreateFromPngPtr(len(raw), buffer)
target = gd.gdImageCreateTrueColor(512, 512)
assert source and target
gd.gdImageCopyResampled(target, source, 0, 0, 0, 0, 512, 512, w, h)
size = integer()
encoded = gd.gdImageJpegPtr(target, ctypes.byref(size), 85)
assert encoded
jpeg = ctypes.string_at(encoded, size.value)
gd.gdFree(encoded)
gd.gdImageDestroy(source)
gd.gdImageDestroy(target)
assert len(jpeg) < 100000
Path('dist/line-4/26.jpg').write_bytes(jpeg)
ancestor.write_bytes(output.read_bytes())
evidence = {'ancestor_sha256': old_sha, 'wall_sha256': sha,
            'dimensions': [w,h], 'format': 'PNG', 'mode': 'RGB',
            'outputs': ['artifacts/line-4/wall-v8.png', 'artifacts/line-4/wall.png'],
            'new_mark_rectangle_xyxy': [x0,y0,x1,y1], 'changed_pixels': len(points),
            'changed_pixels_outside_rectangle': 0,
            'method': 'Built-in image tool edited ancestral wall. Only its new addition on unused rock was composited with feathered edges; every pixel elsewhere is unchanged.',
            'preview': {'path':'dist/line-4/26.jpg', 'format':'JPEG', 'dimensions':[512,512], 'bytes':len(jpeg)},
            'unmet_visual_requirements': []}
Path('line-4/IMAGE-26.json').write_text(json.dumps(evidence, indent=2)+'\n')
record = {'name': 'The Shorter Branch', 'image': 'https://api.imd.fun/artifacts/'+sha,
          'attributes': [{'trait_type':'Cave','value':'Crystal'},
                         {'trait_type':'Wall','value':'Line 4'},
                         {'trait_type':'Number','value':26},
                         {'trait_type':'Left behind','value':'Plan Audit'},
                         {'trait_type':'Meaning','value':'Pepe compares branching pebble paths to check that fewer changes really suffice.'},
                         {'trait_type':'One thing','value':'Finite offline dependency resolution'}]}
Path('dist/line-4/26.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(evidence, indent=2))
