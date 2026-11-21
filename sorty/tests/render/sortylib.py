"""Shared helpers for rendering Sorty test images in Blender 5.2 (Cycles).

Core: scene reset, room/lighting, camera framing, node helpers, materials,
label-texture generator, lathe / box mesh helpers.
Item builders live in items_*.py and register themselves in FRAMES.
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, noise
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, '..', 'images'))
PREVIEW_DIR = os.path.join(HERE, 'preview')
LABEL_DIR = os.path.join(HERE, 'labels')
FONT_DIR = r"C:\Windows\Fonts"
FORCE_LABELS = False          # re-render label textures even if cached on disk
FRAMES = {}                   # name -> builder function


def frame(name):
    def deco(fn):
        FRAMES[name] = fn
        return fn
    return deco


# ----------------------------------------------------------------- colors
def srgb(r, g, b, a=1.0):
    """sRGB 0-1 -> linear RGBA tuple."""
    def f(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), a)


def hexc(h, a=1.0):
    h = h.lstrip('#')
    return srgb(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def scale_col(c, k):
    if isinstance(k, (int, float)):
        k = (k, k, k)
    return (c[0] * k[0], c[1] * k[1], c[2] * k[2], 1.0)


# ----------------------------------------------------------------- scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def setup_render(scene, samples=96, res=(1024, 768), gpu=True):
    scene.render.engine = 'CYCLES'
    cy = scene.cycles
    cy.device = 'CPU'
    if gpu:
        try:
            prefs = bpy.context.preferences.addons['cycles'].preferences
            prefs.compute_device_type = 'OPTIX'
            prefs.refresh_devices()
            for d in prefs.devices:
                d.use = (d.type == 'OPTIX')
            cy.device = 'GPU'
        except Exception as e:  # pragma: no cover
            print('GPU setup failed, using CPU:', e)
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.015
    cy.use_denoising = True
    try:
        cy.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    cy.max_bounces = 14
    cy.transmission_bounces = 14
    cy.glossy_bounces = 6
    cy.transparent_max_bounces = 24
    cy.volume_bounces = 2
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    r = scene.render
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    r.image_settings.file_format = 'JPEG'
    r.image_settings.quality = 90
    r.film_transparent = False
    vs = scene.view_settings
    vs.view_transform = 'AgX'
    try:
        vs.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    vs.exposure = 0.0


def link(ob, scene=None):
    (scene or bpy.context.scene).collection.objects.link(ob)
    return ob


# ----------------------------------------------------------------- node helpers
def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    out = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
    return m, nt, bsdf, out


_PNAMES = {
    'base': 'Base Color', 'metallic': 'Metallic', 'rough': 'Roughness', 'ior': 'IOR', 'alpha': 'Alpha',
    'sss': 'Subsurface Weight', 'sss_radius': 'Subsurface Radius', 'sss_scale': 'Subsurface Scale',
    'spec': 'Specular IOR Level', 'trans': 'Transmission Weight', 'coat': 'Coat Weight',
    'coat_rough': 'Coat Roughness', 'sheen': 'Sheen Weight', 'sheen_rough': 'Sheen Roughness',
    'emit': 'Emission Color', 'emit_strength': 'Emission Strength', 'normal': 'Normal',
    'aniso': 'Anisotropic', 'thin': 'Thin Wall',
}


def sset(nt, sock, val):
    """Set a socket from a constant or link it from another socket."""
    if isinstance(val, bpy.types.NodeSocket):
        nt.links.new(val, sock)
    else:
        if sock.type == 'RGBA' and len(val) == 3:
            val = (val[0], val[1], val[2], 1.0)
        sock.default_value = val


def setp(nt, bsdf, **kw):
    for k, v in kw.items():
        sset(nt, bsdf.inputs[_PNAMES[k]], v)


def tex_coord(nt, which='Object'):
    return nt.nodes.new('ShaderNodeTexCoord').outputs[which]


def mapping(nt, vec, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    n = nt.nodes.new('ShaderNodeMapping')
    nt.links.new(vec, n.inputs['Vector'])
    n.inputs['Location'].default_value = loc
    n.inputs['Rotation'].default_value = rot
    n.inputs['Scale'].default_value = scale
    return n.outputs['Vector']


def noise_tex(nt, vec, scale=5.0, detail=2.0, rough=0.5, distortion=0.0, out='Factor'):
    n = nt.nodes.new('ShaderNodeTexNoise')
    if vec is not None:
        nt.links.new(vec, n.inputs['Vector'])
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    n.inputs['Distortion'].default_value = distortion
    return n.outputs[out]


def voronoi_tex(nt, vec, scale=5.0, feature='F1', out='Distance', randomness=1.0):
    n = nt.nodes.new('ShaderNodeTexVoronoi')
    n.feature = feature
    if vec is not None:
        nt.links.new(vec, n.inputs['Vector'])
    n.inputs['Scale'].default_value = scale
    n.inputs['Randomness'].default_value = randomness
    return n.outputs[out]


def wave_tex(nt, vec, scale=5.0, distortion=0.0, direction='X', wtype='BANDS'):
    n = nt.nodes.new('ShaderNodeTexWave')
    n.wave_type = wtype
    if wtype == 'BANDS':
        n.bands_direction = direction
    if vec is not None:
        nt.links.new(vec, n.inputs['Vector'])
    n.inputs['Scale'].default_value = scale
    n.inputs['Distortion'].default_value = distortion
    return n.outputs['Factor']


def gradient_tex(nt, vec, gtype='SPHERICAL'):
    n = nt.nodes.new('ShaderNodeTexGradient')
    n.gradient_type = gtype
    nt.links.new(vec, n.inputs['Vector'])
    return n.outputs['Factor']


def ramp(nt, fac, stops, interp='LINEAR', out='Color'):
    """stops: [(pos, value_or_color), ...]; values may be floats (gray) or colors."""
    n = nt.nodes.new('ShaderNodeValToRGB')
    cr = n.color_ramp
    cr.interpolation = interp
    while len(cr.elements) < len(stops):
        cr.elements.new(0.5)
    for el, (pos, col) in zip(cr.elements, stops):
        el.position = pos
        if isinstance(col, (int, float)):
            col = (col, col, col, 1.0)
        elif len(col) == 3:
            col = (col[0], col[1], col[2], 1.0)
        el.color = col
    sset(nt, n.inputs[0], fac)
    return n.outputs[out]


def math_n(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    n.use_clamp = clamp
    sset(nt, n.inputs[0], a)
    if b is not None:
        sset(nt, n.inputs[1], b)
    return n.outputs[0]


def mix_col(nt, fac, a, b, blend='MIX'):
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type = 'RGBA'
    n.blend_type = blend
    sset(nt, n.inputs[0], fac)
    sset(nt, n.inputs[6], a)
    sset(nt, n.inputs[7], b)
    return n.outputs[2]


def mix_val(nt, fac, a, b):
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type = 'FLOAT'
    sset(nt, n.inputs[0], fac)
    sset(nt, n.inputs[2], a)
    sset(nt, n.inputs[3], b)
    return n.outputs[0]


def bump(nt, height, strength=0.3, distance=0.001, normal=None):
    n = nt.nodes.new('ShaderNodeBump')
    n.inputs['Strength'].default_value = strength
    n.inputs['Distance'].default_value = distance
    nt.links.new(height, n.inputs['Height'])
    if normal is not None:
        nt.links.new(normal, n.inputs['Normal'])
    return n.outputs['Normal']


def backfacing(nt):
    return nt.nodes.new('ShaderNodeNewGeometry').outputs['Backfacing']


# ----------------------------------------------------------------- materials
def simple_mat(name, color, rough=0.5, metallic=0.0, **kw):
    m, nt, bsdf, out = new_mat(name)
    setp(nt, bsdf, base=color, rough=rough, metallic=metallic, **kw)
    return m


def plastic(name, color, rough=0.35, sss=0.0):
    m, nt, bsdf, out = new_mat(name)
    setp(nt, bsdf, base=color, rough=rough)
    if sss:
        setp(nt, bsdf, sss=sss, sss_radius=(0.004, 0.004, 0.004), sss_scale=1.0)
    return m


def metal(name, color=(0.86, 0.87, 0.88, 1), rough=0.28):
    m, nt, bsdf, out = new_mat(name)
    co = tex_coord(nt, 'Object')
    n = noise_tex(nt, mapping(nt, co, scale=(1, 1, 40)), scale=60, detail=2)
    setp(nt, bsdf, base=color, metallic=1.0, rough=mix_val(nt, n, rough * 0.8, rough * 1.25))
    return m


def clear_mat(name, tint=(1, 1, 1, 1), rough=0.02, ior=1.45, shadow=0.85, volume=None, density=0.0, reflect=True):
    """Clear plastic / glass / liquid. Shadows are lightened (no caustics needed).
    reflect=False uses a refraction-only surface (for liquid surfaces and shell inner walls that
    touch liquid, where a separate air interface would add fake grey reflections)."""
    m, nt, bsdf, out = new_mat(name)
    if reflect:
        setp(nt, bsdf, base=tint, rough=rough, ior=ior, trans=1.0)
        surf = bsdf.outputs[0]
    else:
        rf = nt.nodes.new('ShaderNodeBsdfRefraction')
        rf.inputs['Color'].default_value = tint
        rf.inputs['Roughness'].default_value = rough
        rf.inputs['IOR'].default_value = ior
        surf = rf.outputs[0]
    lp = nt.nodes.new('ShaderNodeLightPath')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    if volume is None:
        tr.inputs['Color'].default_value = (tint[0] * 0.5 + 0.5, tint[1] * 0.5 + 0.5, tint[2] * 0.5 + 0.5, 1)
    else:
        tr.inputs['Color'].default_value = (volume[0], volume[1], volume[2], 1)
    mx = nt.nodes.new('ShaderNodeMixShader')
    sset(nt, mx.inputs[0], math_n(nt, 'MULTIPLY', lp.outputs['Is Shadow Ray'], shadow))
    nt.links.new(surf, mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    if volume is not None:
        va = nt.nodes.new('ShaderNodeVolumeAbsorption')
        va.inputs['Color'].default_value = (volume[0], volume[1], volume[2], 1)
        va.inputs['Density'].default_value = density
        nt.links.new(va.outputs[0], out.inputs['Volume'])
    return m


KRAFT = srgb(0.74, 0.60, 0.42)


def cardboard(name, color=KRAFT, stain=None, seed=0.0):
    """Corrugated cardboard. stain = dict(center=(x,y), radius=R, amount=0..1, splatter=bool)
    in OBJECT coordinates of the object using the material."""
    m, nt, bsdf, out = new_mat(name)
    co = tex_coord(nt, 'Object')
    cos = mapping(nt, co, loc=(seed * 3.1, seed * 1.7, seed))
    broad = noise_tex(nt, cos, scale=7, detail=4, rough=0.6)
    fiber = noise_tex(nt, mapping(nt, co, scale=(1, 9, 1)), scale=420, detail=2)
    speck = noise_tex(nt, co, scale=1500, detail=1)
    c = mix_col(nt, broad, scale_col(color, 0.90), scale_col(color, 1.07))
    c = mix_col(nt, math_n(nt, 'MULTIPLY', fiber, 0.30), c, scale_col(color, 0.78))
    c = mix_col(nt, math_n(nt, 'MULTIPLY', ramp(nt, speck, [(0.62, 0), (0.75, 1)]), 0.25), c, scale_col(color, 0.6))
    rough = 0.86
    flute = wave_tex(nt, co, scale=48.0, direction='X')
    h = math_n(nt, 'ADD', math_n(nt, 'MULTIPLY', fiber, 0.6), math_n(nt, 'MULTIPLY', flute, 0.22))
    if stain:
        cx, cy = stain['center']
        R = stain['radius']
        amount = stain.get('amount', 1.0)
        mp = mapping(nt, co, loc=(-cx / R, -cy / R, 0), scale=(1 / R, 1 / R, 0))
        disc = ramp(nt, gradient_tex(nt, mp), [(0.0, 0), (0.16, 1)])
        wob = noise_tex(nt, cos, scale=11, detail=3, rough=0.6)
        blobs = ramp(nt, wob, [(0.40, 0), (0.56, 1)])
        big = ramp(nt, noise_tex(nt, mapping(nt, co, loc=(4.2 + seed, 1.3, 0)), scale=4.0, detail=1), [(0.36, 0), (0.60, 1)])
        if stain.get('patchy'):
            inner = math_n(nt, 'MULTIPLY', blobs, big)
        else:
            inner = math_n(nt, 'ADD', math_n(nt, 'MULTIPLY', blobs, 0.7), math_n(nt, 'MULTIPLY', big, 0.75), clamp=True)
        mask = math_n(nt, 'MULTIPLY', disc, inner)
        if stain.get('splatter', True):
            sp = ramp(nt, noise_tex(nt, mapping(nt, co, loc=(9.0, seed, 2.0)), scale=38, detail=2), [(0.66, 0), (0.71, 1)])
            mask = math_n(nt, 'MAXIMUM', mask, math_n(nt, 'MULTIPLY', sp, 0.8))
        mask = math_n(nt, 'MULTIPLY', mask, amount, clamp=True)
        # soft, slightly darker rim: shape mask with a ramp
        maskc = ramp(nt, mask, [(0.0, 0), (0.35, 0.75), (1.0, 1.0)])
        greasy = scale_col(color, (0.30, 0.20, 0.10))
        c = mix_col(nt, math_n(nt, 'MULTIPLY', maskc, 0.96), c, greasy)
        rough = mix_val(nt, maskc, 0.86, 0.30)
    setp(nt, bsdf, base=c, rough=rough, spec=0.25)
    setp(nt, bsdf, normal=bump(nt, h, strength=0.18, distance=0.0004))
    return m


def cardboard_edge(name, color=KRAFT):
    """Cut edge of corrugated board: flute stripes."""
    m, nt, bsdf, out = new_mat(name)
    co = tex_coord(nt, 'Object')
    wx = wave_tex(nt, co, scale=62.0, direction='X')
    wy = wave_tex(nt, co, scale=62.0, direction='Y')
    w = math_n(nt, 'MULTIPLY', wx, wy)
    c = mix_col(nt, ramp(nt, w, [(0.2, 0), (0.6, 1)]), scale_col(color, 0.45), scale_col(color, 0.95))
    setp(nt, bsdf, base=c, rough=0.9)
    return m


def image_mat(name, image, rough=0.4, metallic=0.0, back_color=None, coat=0.0, bump_noise=0.0):
    """Material with an image (UV) as base color; optional different back-face color."""
    m, nt, bsdf, out = new_mat(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = image
    tex.extension = 'REPEAT'
    col = tex.outputs['Color']
    if back_color is not None:
        col = mix_col(nt, backfacing(nt), col, back_color)
    setp(nt, bsdf, base=col, rough=rough, metallic=metallic)
    if coat:
        setp(nt, bsdf, coat=coat, coat_rough=0.1)
    if bump_noise:
        co = tex_coord(nt, 'Object')
        setp(nt, bsdf, normal=bump(nt, noise_tex(nt, co, scale=300, detail=2), strength=bump_noise, distance=0.0003))
    return m


# ----------------------------------------------------------------- label textures
_font_cache = {}


def font(fname):
    if fname is None:
        return None
    key = fname.lower()
    f = _font_cache.get(key)
    try:
        if f is not None and f.name:
            return f
    except ReferenceError:
        pass
    f = bpy.data.fonts.load(os.path.join(FONT_DIR, fname))
    _font_cache[key] = f
    return f


class Label:
    """Draw a flat label with emission shapes/text and render it to an image.
    Coordinates in meters, origin at the label centre, x right, y up."""

    def __init__(self, name, w, h, px=2048, bg=(1, 1, 1, 1)):
        self.name, self.w, self.h, self.px = name, w, h, px
        self.path = os.path.join(LABEL_DIR, name + '.png')
        self.cached = os.path.exists(self.path) and not FORCE_LABELS
        self.scene = None
        self.z = 0.0
        self.mats = {}
        if not self.cached:
            self.scene = bpy.data.scenes.new('label_' + name)
            self.rect(0, 0, w, h, bg)

    def _mat(self, color):
        key = tuple(round(c, 4) for c in color[:3])
        if key not in self.mats:
            m = bpy.data.materials.new('lbl')
            m.use_nodes = True
            nt = m.node_tree
            for n in list(nt.nodes):
                if n.bl_idname != 'ShaderNodeOutputMaterial':
                    nt.nodes.remove(n)
            out = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
            em = nt.nodes.new('ShaderNodeEmission')
            em.inputs['Color'].default_value = (color[0], color[1], color[2], 1)
            em.inputs['Strength'].default_value = 1.0
            nt.links.new(em.outputs[0], out.inputs['Surface'])
            self.mats[key] = m
        return self.mats[key]

    def _add(self, ob, color):
        self.z += 0.0004
        ob.location.z = self.z
        ob.data.materials.append(self._mat(color))
        self.scene.collection.objects.link(ob)
        return ob

    def poly(self, pts, color):
        if self.cached:
            return
        me = bpy.data.meshes.new('p')
        me.from_pydata([(x, y, 0) for x, y in pts], [], [list(range(len(pts)))])
        self._add(bpy.data.objects.new('p', me), color)

    def rect(self, cx, cy, w, h, color, rot=0.0):
        c, s = math.cos(rot), math.sin(rot)
        pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
        self.poly([(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts], color)

    def ellipse(self, cx, cy, rx, ry, color, rot=0.0, n=72):
        c, s = math.cos(rot), math.sin(rot)
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            x, y = rx * math.cos(a), ry * math.sin(a)
            pts.append((cx + x * c - y * s, cy + x * s + y * c))
        self.poly(pts, color)

    def ring(self, cx, cy, r_out, r_in, color, bg):
        self.ellipse(cx, cy, r_out, r_out, color)
        self.ellipse(cx, cy, r_in, r_in, bg)

    def wave_band(self, y0, amp, thick, color, periods=2.0, phase=0.0, n=120):
        top, bot = [], []
        for i in range(n + 1):
            x = -self.w / 2 + self.w * i / n
            y = y0 + amp * math.sin(2 * math.pi * periods * i / n + phase)
            top.append((x, y + thick / 2))
            bot.append((x, y - thick / 2))
        # build as quads to keep polygons convex-ish
        if self.cached:
            return
        me = bpy.data.meshes.new('w')
        verts = [(x, y, 0) for x, y in top] + [(x, y, 0) for x, y in bot]
        faces = [(i, i + 1, n + 1 + i + 1, n + 1 + i) for i in range(n)]
        me.from_pydata(verts, [], faces)
        self._add(bpy.data.objects.new('w', me), color)

    def text(self, body, cx, cy, size, color, fname='arialbd.ttf', rot=0.0, shear=0.0, fit_w=None,
             align='CENTER', spacing=1.0):
        if self.cached:
            return
        cu = bpy.data.curves.new('t', 'FONT')
        cu.body = body
        cu.size = size
        cu.align_x = align
        cu.align_y = 'CENTER'
        cu.shear = shear
        cu.space_character = spacing
        f = font(fname)
        if f is not None:
            cu.font = f
        ob = bpy.data.objects.new('t', cu)
        ob.location = (cx, cy, 0)
        ob.rotation_euler = (0, 0, rot)
        self._add(ob, color)
        if fit_w:
            self.scene.view_layers[0].update()
            wdt = ob.dimensions.x
            if wdt > fit_w and wdt > 0:
                k = fit_w / wdt
                ob.scale = (k, k, 1)
        return ob

    def barcode(self, cx, cy, w, h, n=34, seed=3):
        rnd = random.Random(seed)
        self.rect(cx, cy, w * 1.12, h * 1.25, (1, 1, 1, 1))
        x = cx - w / 2
        step = w / n
        for i in range(n):
            if rnd.random() < 0.6:
                bw = step * rnd.choice([0.35, 0.6, 0.85])
                self.rect(x + bw / 2, cy + h * 0.06, bw, h * 0.88, (0.01, 0.01, 0.01, 1))
            x += step

    def render(self):
        if self.cached:
            return bpy.data.images.load(self.path)
        sc = self.scene
        cam_d = bpy.data.cameras.new('lc')
        cam_d.type = 'ORTHO'
        cam_d.ortho_scale = max(self.w, self.h)
        cam = bpy.data.objects.new('lc', cam_d)
        cam.location = (0, 0, 1.0)
        sc.collection.objects.link(cam)
        sc.camera = cam
        sc.render.engine = 'CYCLES'
        sc.cycles.device = 'GPU'
        sc.cycles.samples = 12
        sc.cycles.use_denoising = False
        sc.cycles.use_adaptive_sampling = False
        sc.cycles.max_bounces = 0
        px = self.px
        if self.w >= self.h:
            sc.render.resolution_x, sc.render.resolution_y = px, max(8, int(round(px * self.h / self.w)))
        else:
            sc.render.resolution_y, sc.render.resolution_x = px, max(8, int(round(px * self.w / self.h)))
        sc.render.resolution_percentage = 100
        sc.render.image_settings.file_format = 'PNG'
        sc.view_settings.view_transform = 'Standard'
        sc.view_settings.look = 'None'
        w = bpy.data.worlds.new('lw')
        w.use_nodes = True
        w.node_tree.nodes['Background'].inputs[1].default_value = 0.0
        sc.world = w
        sc.render.filepath = self.path
        bpy.ops.render.render(write_still=True, scene=sc.name)
        img = bpy.data.images.load(self.path)
        for ob in list(sc.collection.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.scenes.remove(sc)
        return img


# ----------------------------------------------------------------- mesh helpers
def obj_from_bm(name, bm, smooth=False, sharp_deg=None, mats=()):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.shade_smooth()
        if sharp_deg is not None:
            me.set_sharp_from_angle(angle=math.radians(sharp_deg))
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    link(ob)
    return ob


def add_box(bm, size, loc=(0, 0, 0), mat_index=0, rot=None):
    """Add an axis aligned (or rotated by Matrix `rot`) box to bmesh."""
    M = Matrix.Translation(loc)
    if rot is not None:
        M = M @ rot.to_4x4()
    M = M @ Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    r = bmesh.ops.create_cube(bm, size=1.0, matrix=M)
    faces = set()
    for v in r['verts']:
        for f in v.link_faces:
            faces.add(f)
    for f in faces:
        f.material_index = mat_index
    return faces


def box_obj(name, size, loc=(0, 0, 0), mat=None, bevel=0.0):
    bm = bmesh.new()
    add_box(bm, size)
    ob = obj_from_bm(name, bm, mats=[mat] if mat else [])
    ob.location = loc
    if bevel:
        add_bevel(ob, bevel)
    return ob


def add_bevel(ob, width, segments=2, angle=35):
    md = ob.modifiers.new('bevel', 'BEVEL')
    md.width = width
    md.segments = segments
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(angle)
    return md


def add_solidify(ob, thickness, offset=-1.0, mat_offset=0, rim_offset=0):
    md = ob.modifiers.new('solid', 'SOLIDIFY')
    md.thickness = thickness
    md.offset = offset
    md.material_offset = mat_offset
    md.material_offset_rim = rim_offset
    md.use_even_offset = True
    return md


def add_subsurf(ob, levels=2):
    md = ob.modifiers.new('subsurf', 'SUBSURF')
    md.levels = levels
    md.render_levels = levels
    return md


def lathe(name, profile, segments=72, mats=(), cap_bottom=False, cap_top=False, smooth=True,
          sharp_deg=50, radial_fn=None, uv_swap=False):
    """Surface of revolution around Z. profile: [(r, z) or (r, z, mat_index)] bottom->top.
    The quad strip between point i and i+1 uses the material index of point i.
    UV: u runs 0..1 around (u=0.5 faces -Y, i.e. the camera), v runs 0..1 over the z-extent
    of each material's faces. radial_fn(u, z, r) -> r lets you add ribs/knurls."""
    pts = [(p[0], p[1], p[2] if len(p) > 2 else 0) for p in profile]
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    rings = []
    for (r, z, mi) in pts:
        ring = []
        for j in range(segments):
            u = j / segments
            a = 2 * math.pi * (u - 0.5)
            rr = radial_fn(u, z, r) if radial_fn else r
            ring.append(bm.verts.new((rr * math.sin(a), -rr * math.cos(a), z)))
        rings.append(ring)
    zext = {}
    for i in range(len(pts) - 1):
        mi = pts[i][2]
        lo, hi = min(pts[i][1], pts[i + 1][1]), max(pts[i][1], pts[i + 1][1])
        a, b = zext.get(mi, (lo, hi))
        zext[mi] = (min(a, lo), max(b, hi))
    for i in range(len(pts) - 1):
        mi = pts[i][2]
        z0, z1 = zext[mi]
        span = (z1 - z0) or 1.0
        for j in range(segments):
            j2 = (j + 1) % segments
            vs = (rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j])
            try:
                f = bm.faces.new(vs)
            except ValueError:
                continue
            f.material_index = mi
            f.smooth = smooth
            uvs = ((j / segments, (pts[i][1] - z0) / span), ((j + 1) / segments, (pts[i][1] - z0) / span),
                   ((j + 1) / segments, (pts[i + 1][1] - z0) / span), (j / segments, (pts[i + 1][1] - z0) / span))
            for loop, uv in zip(f.loops, uvs):
                loop[uv_layer].uv = (uv[1], uv[0]) if uv_swap else uv
    if cap_bottom:
        f = bm.faces.new(list(reversed(rings[0])))
        f.material_index = pts[0][2]
    if cap_top:
        f = bm.faces.new(rings[-1])
        f.material_index = pts[-2][2] if len(pts) > 1 else 0
    bm.normal_update()
    ob = obj_from_bm(name, bm, smooth=False, mats=mats)
    if smooth:
        ob.data.set_sharp_from_angle(angle=math.radians(sharp_deg))
    return ob


def disc(name, radius, z=0.0, segments=72, mat=None):
    """Flat disc facing +Z with planar UVs (0..1 across the diameter, u=x, v=y)."""
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new((radius * math.cos(2 * math.pi * j / segments), radius * math.sin(2 * math.pi * j / segments), z))
          for j in range(segments)]
    f = bm.faces.new(vs)
    for loop in f.loops:
        co = loop.vert.co
        loop[uv_layer].uv = (co.x / (2 * radius) + 0.5, co.y / (2 * radius) + 0.5)
    return obj_from_bm(name, bm, mats=[mat] if mat else [])


def plane_uv(name, w, h, mat=None, nx=1, ny=1):
    """Plane in XY facing +Z, centred at origin, with 0..1 UVs; optional subdivision."""
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    grid = [[bm.verts.new((-w / 2 + w * i / nx, -h / 2 + h * j / ny, 0)) for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for loop, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uv_layer].uv = (a / nx, b / ny)
    return obj_from_bm(name, bm, mats=[mat] if mat else [])


def text_obj(name, body, size, mat, fname='arialbd.ttf', extrude=0.0, align='CENTER', shear=0.0, spacing=1.0):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = 'CENTER'
    cu.extrude = extrude
    cu.shear = shear
    cu.space_character = spacing
    f = font(fname)
    if f is not None:
        cu.font = f
    cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    link(ob)
    return ob


def parent(child, par):
    child.parent = par
    return child


def blob(name, radius, subdiv=3, amp=0.3, freq=2.0, seed=0, squash=(1, 1, 1), mat=None, smooth=True, ridged=False):
    """Noise-displaced icosphere (crumbs, food lumps, wads)."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    off = Vector((seed * 7.13, seed * 3.71, seed * 1.37))
    for v in bm.verts:
        p = v.co.normalized()
        if ridged:
            d = noise.ridged_multi_fractal(p * freq + off, 1.0, 2.0, 3, 1.0, 2.0) * 0.5
        else:
            d = noise.fractal(p * freq + off, 1.0, 2.0, 3)
        v.co = p * (1.0 + amp * d)
        v.co = Vector((v.co.x * squash[0], v.co.y * squash[1], v.co.z * squash[2])) * radius
    return obj_from_bm(name, bm, smooth=smooth, mats=[mat] if mat else [])


def scatter_blobs(name, n, area, z, r_range, mats, seed=1, squash_z=(0.4, 0.9), keep=None):
    """Many small crumbs in one mesh per material. area=(xmin,xmax,ymin,ymax)."""
    rnd = random.Random(seed)
    obs = []
    for mi, mat in enumerate(mats):
        bm = bmesh.new()
        for k in range(n // len(mats)):
            x = rnd.uniform(area[0], area[1])
            y = rnd.uniform(area[2], area[3])
            if keep is not None and not keep(x, y):
                continue
            r = rnd.uniform(*r_range)
            sz = rnd.uniform(*squash_z)
            M = Matrix.Translation((x, y, z + r * sz * 0.6)) @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, 'Z') @ \
                Matrix.Diagonal((r * rnd.uniform(0.7, 1.4), r * rnd.uniform(0.7, 1.4), r * sz, 1))
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0, matrix=M)
        obs.append(obj_from_bm(f'{name}_{mi}', bm, smooth=False, mats=[mat]))
    return obs


# ----------------------------------------------------------------- room / light / camera
def build_room(scene, counter=(0.44, 0.44, 0.435, 1), wall=(0.36, 0.345, 0.33, 1), light=1.0):
    world = bpy.data.worlds.new('World')
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.80, 0.83, 0.88, 1)
    bg.inputs[1].default_value = 0.20 * light
    scene.world = world
    # counter slab
    m, nt, bsdf, out = new_mat('counter')
    co = tex_coord(nt, 'Object')
    sp = noise_tex(nt, co, scale=900, detail=2)
    br = noise_tex(nt, co, scale=3, detail=2)
    c = mix_col(nt, sp, scale_col(counter, 0.93), scale_col(counter, 1.05))
    c = mix_col(nt, br, scale_col(counter, 0.97), c)
    setp(nt, bsdf, base=c, rough=mix_val(nt, br, 0.52, 0.62), spec=0.35)
    setp(nt, bsdf, normal=bump(nt, sp, strength=0.05, distance=0.0002))
    slab = box_obj('counter', (2.4, 1.5, 0.04), loc=(0, 0.05, -0.02), mat=m, bevel=0.004)
    wm = simple_mat('wall', wall, rough=0.92)
    box_obj('wall', (8, 0.1, 5), loc=(0, 2.6, 0.6), mat=wm)
    box_obj('floor', (8, 6, 0.1), loc=(0, 1.0, -0.95), mat=simple_mat('floor', (0.22, 0.21, 0.20, 1), rough=0.8))

    def area(name, loc, size, power, color=(1, 1, 1), aim=(0, 0, 0.03)):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.shape = 'RECTANGLE'
        ld.size, ld.size_y = size
        ld.energy = power * light
        ld.color = color
        ob = bpy.data.objects.new(name, ld)
        ob.location = loc
        d = Vector(aim) - Vector(loc)
        ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        link(ob)
        return ob

    area('key', (-0.55, -0.55, 0.95), (0.9, 0.9), 21, (1.0, 0.97, 0.93))
    area('fill', (0.85, -0.35, 0.50), (0.7, 0.7), 5.5, (0.92, 0.96, 1.0))
    area('ceiling', (0.1, 0.25, 1.5), (1.2, 0.6), 30, (1.0, 0.98, 0.95), aim=(0.1, 0.25, 0))
    area('rim', (0.35, 0.95, 0.75), (0.6, 0.4), 8, (1.0, 1.0, 1.0))
    return slab


def add_camera(scene, lens=35.0):
    cd = bpy.data.cameras.new('Cam')
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 0.01
    cd.clip_end = 50
    cam = bpy.data.objects.new('Cam', cd)
    link(cam)
    scene.camera = cam
    return cam


def aim_camera(cam, target, dist, elev, azim):
    e, a = math.radians(elev), math.radians(azim)
    t = Vector(target)
    pos = t + Vector((dist * math.cos(e) * math.sin(a), -dist * math.cos(e) * math.cos(a), dist * math.sin(e)))
    cam.location = pos
    cam.rotation_euler = (t - pos).to_track_quat('-Z', 'Y').to_euler()


def bbox_points(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for ob in objs:
        oe = ob.evaluated_get(dg)
        for c in oe.bound_box:
            pts.append(oe.matrix_world @ Vector(c))
    return pts


def frame_shot(scene, cam, objs, elev=30, azim=20, fill=0.62, fstop=8.0, shift=(0.0, 0.0), target=None, dist=None):
    """Place the camera so the items span `fill` of the frame; returns distance."""
    bpy.context.view_layer.update()
    pts = bbox_points(objs)
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    tgt = Vector(target) if target is not None else (lo + hi) / 2
    d = dist or 0.5
    if dist is None:
        for _ in range(8):
            aim_camera(cam, tgt, d, elev, azim)
            bpy.context.view_layer.update()
            uv = [world_to_camera_view(scene, cam, p) for p in pts]
            ex = max(u.x for u in uv) - min(u.x for u in uv)
            ey = max(u.y for u in uv) - min(u.y for u in uv)
            cx = (max(u.x for u in uv) + min(u.x for u in uv)) / 2 - 0.5
            cy = (max(u.y for u in uv) + min(u.y for u in uv)) / 2 - 0.5
            s = max(ex, ey) / fill
            d *= s
            # recentre: move target so the projected bbox centre goes to the frame centre
            right = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))
            up = cam.matrix_world.to_3x3() @ Vector((0, 1, 0))
            fw = 2 * d * math.tan(cam.data.angle_x / 2)
            fh = fw * scene.render.resolution_y / scene.render.resolution_x
            tgt = tgt + right * (cx * fw * 0.8) + up * (cy * fh * 0.8)
    aim_camera(cam, tgt, d, elev, azim)
    cam.data.shift_x, cam.data.shift_y = shift
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = d
    cam.data.dof.aperture_fstop = fstop
    return d


def render(scene, name, preview=False):
    out = os.path.join(PREVIEW_DIR if preview else OUT_DIR, name + '.jpg')
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print('RENDERED', out)
    return out
