"""Render Sorty test images.

Usage (from this folder):
  blender -b --factory-startup -P render_all.py -- [--frames a,b,c|all] [--samples 96] [--preview] [--labels] [--res 1024x768]

--preview writes to render/preview/ instead of tests/images/.
--labels  re-renders cached label textures.
"""
import sys, os, time, subprocess, importlib, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
import sortylib as L

for mod in ('items_a', 'items_b', 'items_c', 'items_d', 'items_e'):
    if os.path.exists(os.path.join(HERE, mod + '.py')):
        importlib.import_module(mod)

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def opt(flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        return argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith('--') else True
    return default


frames = opt('--frames', 'all')
frames = list(L.FRAMES) if frames in ('all', True) else [f.strip() for f in frames.split(',') if f.strip()]
samples = int(opt('--samples', 96))
preview = bool(opt('--preview', False))
L.FORCE_LABELS = bool(opt('--labels', False))
res = tuple(int(v) for v in str(opt('--res', '1024x768')).split('x'))


def post_blurdark(path):
    tmp = path[:-4] + '_tmp.jpg'
    vf = 'avgblur=sizeX=46:sizeY=3,eq=brightness=-0.10:contrast=0.85:gamma=0.75,noise=alls=14:allf=t'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path, '-vf', vf, '-q:v', '4', tmp], check=True)
    os.replace(tmp, path)


t_all = time.time()
done, failed = [], []
for name in frames:
    if name not in L.FRAMES:
        print('UNKNOWN FRAME', name)
        failed.append(name)
        continue
    t0 = time.time()
    try:
        scene = L.reset()
        L._font_cache.clear()
        L.setup_render(scene, samples=samples, res=res)
        spec = None
        # builders may ask for a different light level, so build the item first, then the room
        spec = L.FRAMES[name](scene)
        L.build_room(scene, light=spec.get('light', 1.0))
        cam = L.add_camera(scene, lens=spec.get('lens', 35.0))
        L.frame_shot(scene, cam, spec['objs'], **spec.get('shot', {}))
        if 'exposure' in spec:
            scene.view_settings.exposure = spec['exposure']
        out = L.render(scene, name, preview=preview)
        if spec.get('post') == 'blurdark':
            post_blurdark(out)
        done.append(name)
        print(f'FRAME {name} ok in {time.time() - t0:.1f}s')
    except Exception:
        traceback.print_exc()
        failed.append(name)
print(f'DONE {len(done)} frames in {time.time() - t_all:.1f}s; failed: {failed}')
