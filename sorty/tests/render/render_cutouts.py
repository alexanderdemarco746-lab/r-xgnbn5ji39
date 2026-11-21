"""Render transparent cut-outs of the Sorty test items for the web showcase.

Usage (from this folder):
  blender -b --factory-startup -P render_cutouts.py -- [--frames a,b|all] [--samples 128] [--sheet-only]

Writes  sorty/showcase/assets/items/<name>.png  (RGBA, cropped, longest side about 640 px)
        sorty/showcase/assets/items/items.json  (file, w, h, height_m, label per item)
and contact sheets over the cream page colour in  render/preview/cutout_sheet*.png .
It reuses the item builders of the test frames (items_a/b/c) and never touches tests/images.

Clear items (bottles, cups, glass) are rendered twice: once with opaque glass (colour) and once
with Cycles "transparent glass" (see-through mask). The final alpha keeps a faint tint in the
clear areas and stays opaque on edges and highlights, so they remain readable on a light page.
"""
import sys, os, json, math, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import sortylib as L
import items_a, items_b, items_c, items_d, items_e  # noqa: F401  (register the frame builders)

OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'showcase', 'assets', 'items'))
TMP = os.path.join(HERE, 'preview', 'cut_tmp')
RES, TARGET, PAD = 768, 640, 6
CREAM = (0xF3 / 255, 0xEE / 255, 0xE4 / 255)
FLOOR, GAIN = 0.40, 3.2          # tint opacity kept in clear areas; colour-difference gain for edges/highlights

LABELS = {
    'pizza_box_closed': 'Pizza box', 'pizza_box_open_greasy': 'Greasy pizza box', 'pizza_box_open_clean': 'Clean pizza box',
    'pizza_box_open_leftovers': 'Pizza box with leftovers', 'soda_can': 'Soda can', 'clear_bottle_empty': 'Empty water bottle',
    'clear_bottle_half_cola': 'Half-full cola bottle', 'banana_peel': 'Banana peel', 'battery_aa': 'AA batteries',
    'coffee_cup_lid': 'Coffee cup', 'cold_cup_side': 'Clear plastic cup', 'cold_cup_bottom_compostable': 'Compostable cup (bottom)',
    'cold_cup_bottom_pet': 'Plastic cup (bottom, #1 PETE)', 'clamshell_closed': 'Foam takeout box',
    'clamshell_open_food': 'Takeout box with food', 'chip_bag': 'Chip bag', 'greasy_napkin': 'Greasy napkins',
    'opaque_bottle': 'Shampoo bottle', 'tied_bag': 'Tied plastic bag', 'cardboard_box_clean': 'Cardboard box',
    'plastic_fork': 'Plastic fork and knife', 'glass_bottle_empty': 'Glass bottle', 'spray_can': 'Spray paint can',
    'two_items_peel_bottle': 'Banana peel and bottle', 'smartphone': 'Smartphone',
    'pizza_box_open_moldy': 'Moldy pizza box', 'vape': 'Disposable vape', 'plastic_bag': 'Plastic grocery bag',
    'carton_empty': 'Juice carton',
}
ORDER = list(LABELS)
FLOORS = {'cold_cup_bottom_compostable': 0.62, 'cold_cup_bottom_pet': 0.62}   # keep the base markings legible over dark things
LOWKEY = {'plastic_bag', 'plastic_fork', 'clamshell_closed', 'clamshell_open_food', 'greasy_napkin', 'tied_bag', 'coffee_cup_lid', 'opaque_bottle'}
CLEAR = {'clear_bottle_empty', 'clear_bottle_half_cola', 'cold_cup_side', 'cold_cup_bottom_compostable', 'cold_cup_bottom_pet',
         'glass_bottle_empty', 'two_items_peel_bottle'}

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def opt(flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        return argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith('--') else True
    return default


# ----------------------------------------------------------------- image io (numpy, row 0 = top)
def load_rgba(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    arr = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    bpy.data.images.remove(img)
    return arr.reshape(h, w, 4)[::-1].copy()


def save_rgba(arr, path):
    h, w = arr.shape[:2]
    img = bpy.data.images.new('cutout_out', width=w, height=h, alpha=True)
    img.alpha_mode = 'STRAIGHT'
    img.pixels.foreach_set(np.clip(np.ascontiguousarray(arr[::-1], dtype=np.float32), 0.0, 1.0).ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def resize_area(img, new_h, new_w):
    h, w = img.shape[:2]
    ys = (np.arange(new_h + 1) * h / new_h).astype(int)
    xs = (np.arange(new_w + 1) * w / new_w).astype(int)
    out = np.add.reduceat(img, ys[:-1], axis=0) / np.maximum(np.diff(ys), 1)[:, None, None]
    out = np.add.reduceat(out, xs[:-1], axis=1) / np.maximum(np.diff(xs), 1)[None, :, None]
    return out


def over(canvas, rgba, x, y):
    """Composite straight-alpha rgba onto the RGB canvas at (x, y)."""
    h, w = rgba.shape[:2]
    a = rgba[..., 3:4]
    canvas[y:y + h, x:x + w] = rgba[..., :3] * a + canvas[y:y + h, x:x + w] * (1 - a)


# ----------------------------------------------------------------- studio & camera
def studio(scene, clear, lowkey=False):
    k = 0.0 if not lowkey else 1.0     # white items: less ambient and top light so they keep form shading on a light page
    world = bpy.data.worlds.new('CutoutWorld')
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.84, 0.88, 0.94, 1)
    bg.inputs[1].default_value = 0.46 - 0.20 * k
    scene.world = world

    def area(name, loc, size, power, color=(1, 1, 1), aim=(0, 0, 0.05)):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.shape = 'RECTANGLE'
        ld.size, ld.size_y = size
        ld.energy = power
        ld.color = color
        ob = bpy.data.objects.new(name, ld)
        ob.location = loc
        ob.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        L.link(ob)
        ob.visible_camera = False

    area('key', (-0.55, -0.55, 0.95), (0.9, 0.9), 20 - 3 * k, (1.0, 0.97, 0.93))
    area('fill', (0.85, -0.35, 0.50), (0.7, 0.7), 7 - 4.5 * k, (0.92, 0.96, 1.0))
    area('top', (0.1, 0.25, 1.5), (1.2, 0.6), 26 - 17 * k, (1.0, 0.98, 0.95), aim=(0.1, 0.25, 0))
    area('rim', (0.35, 0.95, 0.75), (0.6, 0.4), 8 - 3 * k)
    area('under', (0.0, -0.3, -0.7), (1.2, 1.2), 9 - 6.5 * k, aim=(0, 0, 0.05))      # stands in for the counter bounce
    if clear:
        # dark side flags (outside the frame): glass edges pick them up and stay visible on a light page
        dark = L.simple_mat('flag', (0.035, 0.038, 0.045, 1), rough=0.9)
        for sx in (-1, 1):
            f = L.box_obj('flag', (0.02, 1.6, 1.2), loc=(sx * 0.72, 0.30, 0.20), mat=dark)
            f.visible_camera = False


def item_points(objs, per_obj=90):
    """World-space sample points of the item: for every object its extreme vertices along each axis plus an even
    subsample (so huge bead meshes cannot crowd out the few corner vertices of a box)."""
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for ob in objs:
        oe = ob.evaluated_get(dg)
        try:
            me = oe.to_mesh()
        except RuntimeError:
            continue
        if me is None or not len(me.vertices):
            continue
        co = np.empty(len(me.vertices) * 3, dtype=np.float32)
        me.vertices.foreach_get('co', co)
        M = np.array(oe.matrix_world, dtype=np.float32)
        co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        idx = set(np.linspace(0, len(co) - 1, min(len(co), per_obj)).astype(int).tolist())
        for ax in range(3):
            idx.add(int(co[:, ax].argmin()))
            idx.add(int(co[:, ax].argmax()))
        pts.append(co[sorted(idx)])
        oe.to_mesh_clear()
    return [Vector(p) for p in np.concatenate(pts)]


def fit_camera(scene, cam, pts, elev, azim):
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    tgt, d = (lo + hi) / 2, 0.6
    for _ in range(12):
        L.aim_camera(cam, tgt, d, elev, azim)
        bpy.context.view_layer.update()
        uv = [world_to_camera_view(scene, cam, p) for p in pts]
        xs, ys = [u.x for u in uv], [u.y for u in uv]
        ex, ey = max(xs) - min(xs), max(ys) - min(ys)
        cx, cy = (max(xs) + min(xs)) / 2 - 0.5, (max(ys) + min(ys)) / 2 - 0.5
        d *= max(ex, ey) * RES / TARGET
        Mw = cam.matrix_world.to_3x3()
        fw = 2 * d * math.tan(cam.data.angle_x / 2)
        tgt = tgt + (Mw @ Vector((1, 0, 0))) * (cx * fw) + (Mw @ Vector((0, 1, 0))) * (cy * fw)
    L.aim_camera(cam, tgt, d, elev, azim)
    cam.data.dof.use_dof = False
    return d


# ----------------------------------------------------------------- one item
def render_item(name, samples):
    scene = L.reset()
    L._font_cache.clear()
    L.setup_render(scene, samples=samples, res=(RES, RES))
    r = scene.render
    r.film_transparent = True
    r.image_settings.file_format = 'PNG'
    r.image_settings.color_mode = 'RGBA'
    r.image_settings.color_depth = '8'
    spec = L.FRAMES[name](scene)
    objs = [o for o in scene.objects if o.type in ('MESH', 'CURVE', 'FONT')]
    bpy.context.view_layer.update()
    pts = item_points(objs)
    clear = name in CLEAR
    studio(scene, clear, lowkey=name in LOWKEY)
    cam = L.add_camera(scene, lens=spec.get('lens', 35.0))
    shot = spec.get('shot', {})
    d = fit_camera(scene, cam, pts, shot.get('elev', 30), shot.get('azim', 20))
    m_per_px = 2 * d * math.tan(cam.data.angle_x / 2) / RES
    pb = os.path.join(TMP, name + '_B.png')
    scene.cycles.film_transparent_glass = False
    r.filepath = pb
    bpy.ops.render.render(write_still=True)
    B = load_rgba(pb)
    rgb, aB = B[..., :3], B[..., 3]
    alpha = aB.copy()
    if clear:
        pa = os.path.join(TMP, name + '_A.png')
        scene.cycles.film_transparent_glass = True
        scene.cycles.film_transparent_roughness = 0.3
        r.filepath = pa
        bpy.ops.render.render(write_still=True)
        aA = load_rgba(pa)[..., 3]
        glass = (aB > 0.02) & (aA < 0.97 * aB)
        sel = (aB > 0.98) & (aA < 0.25)
        if sel.sum() > 200:
            ref = np.median(rgb[sel], axis=0)
            key = np.clip(np.linalg.norm(rgb - ref, axis=2) * GAIN, 0, 1)
        else:
            key = np.zeros_like(aB)
        floor = FLOORS.get(name, FLOOR)
        see = np.maximum(np.maximum(aA, floor * aB), key * aB)
        alpha = np.where(glass, np.minimum(see, aB), aB)
    ys, xs = np.where(alpha > 0.004)
    y0, y1 = max(ys.min() - PAD, 0), min(ys.max() + PAD + 1, RES)
    x0, x1 = max(xs.min() - PAD, 0), min(xs.max() + PAD + 1, RES)
    out = np.dstack([rgb, alpha])[y0:y1, x0:x1]
    save_rgba(out, os.path.join(OUT, name + '.png'))
    h, w = out.shape[:2]
    touching = bool(ys.min() == 0 or xs.min() == 0 or ys.max() == RES - 1 or xs.max() == RES - 1)
    return {'file': name + '.png', 'w': int(w), 'h': int(h), 'height_m': round(float(h * m_per_px), 4), 'label': LABELS[name]}, touching


# ----------------------------------------------------------------- contact sheets
def contact_sheets(names):
    cuts = {n: load_rgba(os.path.join(OUT, n + '.png')) for n in names if os.path.exists(os.path.join(OUT, n + '.png'))}
    # 1) every item at 150 px tall on cream
    Hc, gap, Wmax = 150, 22, 1500
    rows, row, x = [], [], gap
    for n, im in cuts.items():
        w = max(1, int(round(im.shape[1] * Hc / im.shape[0])))
        if x + w + gap > Wmax and row:
            rows.append(row)
            row, x = [], gap
        row.append((n, w))
        x += w + gap
    if row:
        rows.append(row)
    canvas = np.empty((len(rows) * (Hc + gap) + gap, Wmax, 3), dtype=np.float32)
    canvas[:] = CREAM
    for ri, row in enumerate(rows):
        x = gap
        for n, w in row:
            im = cuts[n]
            pm = np.dstack([im[..., :3] * im[..., 3:4], im[..., 3]])
            sm = resize_area(pm, Hc, w)
            y = gap + ri * (Hc + gap)
            canvas[y:y + Hc, x:x + w] = sm[..., :3] + canvas[y:y + Hc, x:x + w] * (1 - sm[..., 3:4])
            x += w + gap
    save_rgba(np.dstack([canvas, np.ones(canvas.shape[:2], dtype=np.float32)]), os.path.join(HERE, 'preview', 'cutout_sheet.png'))
    # 2) clear items at full size on cream, plus the same on a dark grey strip (halo check)
    cl = [n for n in names if n in CLEAR and n in cuts]
    if cl:
        Wc = sum(cuts[n].shape[1] for n in cl) + gap * (len(cl) + 1)
        Hm = max(cuts[n].shape[0] for n in cl)
        canvas = np.empty((Hm + 2 * gap, Wc, 3), dtype=np.float32)
        canvas[:] = CREAM
        x = gap
        for n in cl:
            over(canvas, cuts[n], x, gap + (Hm - cuts[n].shape[0]))
            x += cuts[n].shape[1] + gap
        save_rgba(np.dstack([canvas, np.ones(canvas.shape[:2], dtype=np.float32)]), os.path.join(HERE, 'preview', 'cutout_clear.png'))


def detail_sheet(names, scale=1.0):
    """Chosen cut-outs side by side on the cream page colour (top) and on dark grey (bottom, shows light halos)."""
    cuts = [load_rgba(os.path.join(OUT, n + '.png')) for n in names]
    if scale != 1.0:
        sm = []
        for im in cuts:
            pm = np.dstack([im[..., :3] * im[..., 3:4], im[..., 3]])
            r_ = resize_area(pm, max(1, int(im.shape[0] * scale)), max(1, int(im.shape[1] * scale)))
            a = np.maximum(r_[..., 3:4], 1e-6)
            sm.append(np.dstack([r_[..., :3] / a, r_[..., 3]]))
        cuts = sm
    gap = 20
    W = sum(c.shape[1] for c in cuts) + gap * (len(cuts) + 1)
    Hm = max(c.shape[0] for c in cuts)
    canvas = np.empty((2 * (Hm + gap) + gap, W, 3), dtype=np.float32)
    canvas[:Hm + gap + gap // 2] = CREAM
    canvas[Hm + gap + gap // 2:] = (0.17, 0.17, 0.18)
    x = gap
    for c in cuts:
        over(canvas, c, x, gap + (Hm - c.shape[0]))
        over(canvas, c, x, 2 * gap + Hm + (Hm - c.shape[0]))
        x += c.shape[1] + gap
    save_rgba(np.dstack([canvas, np.ones(canvas.shape[:2], dtype=np.float32)]), os.path.join(HERE, 'preview', 'cutout_detail.png'))


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    frames = opt('--frames', 'all')
    names = ORDER if frames in ('all', True) else [f.strip() for f in frames.split(',') if f.strip()]
    samples = int(opt('--samples', 128))
    meta_path = os.path.join(OUT, 'items.json')
    meta = {}
    if os.path.exists(meta_path):
        try:
            meta = json.load(open(meta_path, encoding='utf-8'))
        except Exception:
            meta = {}
    failed = []
    if not opt('--sheet-only', False):
        for name in names:
            t0 = time.time()
            try:
                info, touching = render_item(name, samples)
                meta[name] = info
                print(f"CUTOUT {name} {info['w']}x{info['h']} height_m={info['height_m']} {'TOUCHES-FRAME' if touching else ''} {time.time() - t0:.1f}s")
            except Exception:
                traceback.print_exc()
                failed.append(name)
        ordered = {n: meta[n] for n in ORDER if n in meta}
        json.dump(ordered, open(meta_path, 'w', encoding='utf-8'), indent=2)
    contact_sheets(ORDER)
    det = opt('--detail', None)
    if det and det is not True:
        detail_sheet([f.strip() for f in det.split(',') if f.strip()], float(opt('--detail-scale', 1.0)))
    print('CUTOUTS DONE; failed:', failed)


main()
