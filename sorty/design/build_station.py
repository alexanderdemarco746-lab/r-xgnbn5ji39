"""
Sorty smart bin station - product design scene (Blender 5.2, Cycles).

Run headless (rebuilds the whole scene, renders, saves the .blend):
    blender.exe -b --factory-startup -P build_station.py
Options after "--":
    --preview            half resolution, few samples, output to renders/_preview/
    --views a,b,c        any of: hero, story, head, front, retrofit, camview   (default: all main views)
    --no-save            do not write sorty_station.blend

Everything is procedural: no downloaded assets. Fonts are the local Windows Segoe UI files
(text is converted to meshes, so the .blend has no font dependency).
Units are meters. The viewer stands at -Y looking toward +Y; viewer-left is -X.
"""
import bpy, bmesh, sys, os, random, shutil, subprocess
from math import radians, sin, cos, pi, sqrt, atan2
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default=None):
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            return argv[i + 1]
        return True
    return default


PREVIEW = bool(opt("--preview", False))
VIEWS = str(opt("--views", "hero,story,head,front,retrofit,camview")).split(",")
SAVE = not opt("--no-save", False)
OUT = os.path.join(HERE, "renders", "_preview") if PREVIEW else os.path.join(HERE, "renders")
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------------- design constants
BIN_COLOR = {"recycle": "#1F6FEB", "compost": "#2DA44E", "landfill": "#24292F"}
LED_COLOR = {"recycle": "#2F81F7", "compost": "#2EE06A", "landfill": "#F4F8FF"}
BIN_X = {"recycle": -0.51, "compost": 0.0, "landfill": 0.51}        # viewer-left = -X
BIN_WORD = {"recycle": "RECYCLE", "compost": "COMPOST", "landfill": "LANDFILL"}
BIN_ICON = {"recycle": "\u267b", "compost": "\U0001F331", "landfill": "\U0001F5D1"}   # Segoe UI Symbol glyphs
BIN_BODY_W = 0.488
PROFILE = [(-0.225, 0.06), (-0.225, 0.74), (0.0, 1.0), (0.225, 1.0), (0.225, 0.06)]   # (y, z) side profile
SLOPE_ANGLE = atan2(0.26, 0.225)
HEAD_POS = Vector((0.0, 0.17, 1.47))
HEAD_TILT = 8.0            # degrees, screen leans down toward the user
SCREEN_W, SCREEN_H, SCREEN_Y = 0.29, 0.172, 0.031
PERSON_XY = (-0.12, -0.82)
BOX_TILT = 36.0
FONT_BOLD, FONT_SEMI, FONT_SYM = "segoeuib.ttf", "seguisb.ttf", "seguisym.ttf"

# ----------------------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "SortyStation"
scene.unit_settings.system = "METRIC"


def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexcol(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (srgb_to_lin(r), srgb_to_lin(g), srgb_to_lin(b), a)


def new_coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or scene.collection).children.link(c)
    return c


def new_obj(name, data, coll, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), parent=None, mat=None):
    ob = bpy.data.objects.new(name, data)
    coll.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = scale
    if parent is not None:
        ob.parent = parent
    if mat is not None and data is not None and hasattr(data, "materials"):
        data.materials.append(mat)
    if data is None:
        ob.empty_display_size = 0.05
    return ob


# ----------------------------------------------------------------------------- mesh helpers
def mesh_from_bm(name, bm, smooth=False, sharp=None):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.shade_smooth()
        if sharp is not None:
            me.set_sharp_from_angle(angle=radians(sharp))
    return me


def m_box(name, sx, sy, sz, top_index=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    bm.normal_update()
    if top_index is not None:
        for f in bm.faces:
            if f.normal.z > 0.9:
                f.material_index = top_index[0]
            elif f.normal.z < -0.9:
                f.material_index = top_index[1]
    return mesh_from_bm(name, bm)


def m_cyl(name, r, depth, seg=48, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r,
                          radius2=(r if r2 is None else r2), depth=depth)
    return mesh_from_bm(name, bm, smooth=True, sharp=40)


def m_sphere(name, r, seg=32, rings=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    return mesh_from_bm(name, bm, smooth=True)


def m_ico(name, r, sub=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    return mesh_from_bm(name, bm, smooth=True)


def m_capsule(name, r, length, seg=24, hemi=8):
    """Capsule along local Z; `length` is the distance between the two hemisphere centers."""
    bm = bmesh.new()
    rows = []
    for i in range(1, hemi + 1):
        phi = -pi / 2 + (pi / 2) * i / hemi
        rows.append((r * cos(phi), -length / 2 + r * sin(phi)))
    for i in range(0, hemi):
        phi = (pi / 2) * i / hemi
        rows.append((r * cos(phi), length / 2 + r * sin(phi)))
    bot = bm.verts.new((0, 0, -length / 2 - r))
    top = bm.verts.new((0, 0, length / 2 + r))
    rings = [[bm.verts.new((rad * cos(2 * pi * j / seg), rad * sin(2 * pi * j / seg), z)) for j in range(seg)]
             for rad, z in rows]
    for j in range(seg):
        k = (j + 1) % seg
        bm.faces.new((bot, rings[0][k], rings[0][j]))
        bm.faces.new((top, rings[-1][j], rings[-1][k]))
    for a in range(len(rings) - 1):
        for j in range(seg):
            k = (j + 1) % seg
            bm.faces.new((rings[a][j], rings[a][k], rings[a + 1][k], rings[a + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_from_bm(name, bm, smooth=True)


def rounded_rect_pts(w, h, r, seg=8, cx=0.0, cy=0.0):
    r = min(r, w / 2 - 1e-6, h / 2 - 1e-6)
    pts = []
    for ox, oy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(seg + 1):
            a = radians(a0 + 90.0 * i / seg)
            pts.append((cx + ox + r * cos(a), cy + oy + r * sin(a)))
    return pts


def circle_pts(r, seg=48, cx=0.0, cy=0.0):
    return [(cx + r * cos(2 * pi * i / seg), cy + r * sin(2 * pi * i / seg)) for i in range(seg)]


def stadium_pts(p0, p1, width, seg=8):
    (x0, y0), (x1, y1) = p0, p1
    ang = atan2(y1 - y0, x1 - x0)
    r = width / 2
    pts = []
    for i in range(seg + 1):
        a = ang - pi / 2 + pi * i / seg
        pts.append((x1 + r * cos(a), y1 + r * sin(a)))
    for i in range(seg + 1):
        a = ang + pi / 2 + pi * i / seg
        pts.append((x0 + r * cos(a), y0 + r * sin(a)))
    return pts


def arc_band_pts(cx, cy, r, width, a0, a1, seg=24):
    outer = [(cx + (r + width / 2) * cos(radians(a0 + (a1 - a0) * i / seg)),
              cy + (r + width / 2) * sin(radians(a0 + (a1 - a0) * i / seg))) for i in range(seg + 1)]
    inner = [(cx + (r - width / 2) * cos(radians(a0 + (a1 - a0) * i / seg)),
              cy + (r - width / 2) * sin(radians(a0 + (a1 - a0) * i / seg))) for i in range(seg + 1)]
    return outer + inner[::-1]


def rot_pts(pts, deg, cx=0.0, cy=0.0):
    a = radians(deg)
    return [(cx + (x - cx) * cos(a) - (y - cy) * sin(a), cy + (x - cx) * sin(a) + (y - cy) * cos(a)) for x, y in pts]


def m_polys(name, polys, z=0.0):
    """Flat faces in the local XY plane (normal +Z). Each poly is a CCW list of (x, y)."""
    bm = bmesh.new()
    for pts in polys:
        vs = [bm.verts.new((x, y, z)) for x, y in pts]
        bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    return mesh_from_bm(name, bm)


def m_band(name, outer, inner, z=0.0):
    """Flat ring between two closed outlines with the same point count."""
    bm = bmesh.new()
    vo = [bm.verts.new((x, y, z)) for x, y in outer]
    vi = [bm.verts.new((x, y, z)) for x, y in inner]
    n = len(outer)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vo[i], vo[j], vi[j], vi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    return mesh_from_bm(name, bm)


def m_prism(name, pts, z0, z1, smooth=False, mat_index=0):
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, z0)) for x, y in pts]
    hi = [bm.verts.new((x, y, z1)) for x, y in pts]
    n = len(pts)
    bm.faces.new(lo[::-1])
    bm.faces.new(hi)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.material_index = mat_index
    return mesh_from_bm(name, bm, smooth=smooth, sharp=35 if smooth else None)


def curve_tube(name, pts3d, radius, coll, mat, closed=True, parent=None, res=5, loc=(0, 0, 0), rot=(0, 0, 0)):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts3d) - 1)
    for p, co in zip(sp.points, pts3d):
        p.co = (co[0], co[1], co[2], 1.0)
    sp.use_cyclic_u = closed
    cu.bevel_depth = radius
    cu.bevel_resolution = res
    cu.fill_mode = "FULL"
    cu.use_fill_caps = True
    return new_obj(name, cu, coll, loc=loc, rot=rot, parent=parent, mat=mat)


def add_bevel(ob, width, segments=4, angle=30.0, weighted=True):
    b = ob.modifiers.new("Bevel", "BEVEL")
    b.width = width
    b.segments = segments
    b.limit_method = "ANGLE"
    b.angle_limit = radians(angle)
    if weighted:
        w = ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
        w.keep_sharp = False
        w.weight = 50
    return b


def aim(ob, a, b):
    a, b = Vector(a), Vector(b)
    ob.location = (a + b) / 2
    ob.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()


def limb(name, a, b, r, coll, mat, parent=None):
    length = (Vector(b) - Vector(a)).length
    ob = new_obj(name, m_capsule(name, r, length), coll, mat=mat, parent=parent)
    aim(ob, a, b)
    return ob


def rod(name, a, b, r, coll, mat, parent=None, seg=12):
    length = (Vector(b) - Vector(a)).length
    ob = new_obj(name, m_cyl(name, r, length, seg=seg), coll, mat=mat, parent=parent)
    aim(ob, a, b)
    return ob


# ----------------------------------------------------------------------------- text helpers
_FONTS, _CAP = {}, {}


def font(file):
    if file not in _FONTS:
        path = os.path.join(r"C:\Windows\Fonts", file)
        _FONTS[file] = bpy.data.fonts.load(path) if os.path.exists(path) else None
    return _FONTS[file]


def _text_mesh(name, body, fontfile, size=1.0, align_x="CENTER"):
    cu = bpy.data.curves.new(name + "_cu", "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = align_x
    cu.align_y = "BOTTOM_BASELINE"
    f = font(fontfile)
    if f:
        cu.font = f
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    me.name = name
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    return me


def cap_ratio(fontfile):
    if fontfile not in _CAP:
        me = _text_mesh("capprobe", "H", fontfile, 1.0)
        ys = [v.co.y for v in me.vertices]
        _CAP[fontfile] = (max(ys) - min(ys)) if ys else 0.7
        bpy.data.meshes.remove(me)
    return _CAP[fontfile]


def text_obj(name, body, cap_h, coll, mat, fontfile=FONT_BOLD, parent=None, loc=(0, 0, 0), rot=(0, 0, 0),
             align_x="CENTER"):
    """Text as a flat mesh in local XY (facing +Z); capital letters are vertically centered on y=0."""
    me = _text_mesh(name, body, fontfile, cap_h / cap_ratio(fontfile), align_x)
    for v in me.vertices:
        v.co.y -= cap_h / 2
    return new_obj(name, me, coll, loc=loc, rot=rot, parent=parent, mat=mat)


def glyph_obj(name, ch, height, coll, mat, fontfile=FONT_SYM, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    me = _text_mesh(name, ch, fontfile, 1.0)
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    s = height / max(max(ys) - min(ys), 1e-6)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    for v in me.vertices:
        v.co.x = (v.co.x - cx) * s
        v.co.y = (v.co.y - cy) * s
    return new_obj(name, me, coll, loc=loc, rot=rot, parent=parent, mat=mat)


# ----------------------------------------------------------------------------- materials
def _nodes(m):
    try:
        m.use_nodes = True
    except Exception:
        pass
    return m.node_tree


def _principled(nt):
    return next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")


def mat_pbr(name, hexc, rough=0.5, metallic=0.0, coat=0.0, emis_hex=None, emis=0.0):
    m = bpy.data.materials.new(name)
    b = _principled(_nodes(m))
    b.inputs["Base Color"].default_value = hexcol(hexc)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Coat Weight"].default_value = coat
    if emis_hex:
        b.inputs["Emission Color"].default_value = hexcol(emis_hex)
        b.inputs["Emission Strength"].default_value = emis
    return m


def mat_emit(name, hexc, strength):
    m = bpy.data.materials.new(name)
    nt = _nodes(m)
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    e.inputs["Color"].default_value = hexcol(hexc)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    return m


def mat_beam(name, hexc, strength, opacity):
    m = bpy.data.materials.new(name)
    nt = _nodes(m)
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    t = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    e.inputs["Color"].default_value = hexcol(hexc)
    e.inputs["Strength"].default_value = strength
    mix.inputs[0].default_value = opacity
    nt.links.new(t.outputs[0], mix.inputs[1])
    nt.links.new(e.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs["Surface"])
    m.surface_render_method = "BLENDED"       # only matters for EEVEE viewport
    return m


def mat_cardboard(name, grease=0.0, base="#C9A26F", fiber="#B68D5B", dark="#6F481F", stain_scale=9.0):
    m = bpy.data.materials.new(name)
    nt = _nodes(m)
    b = _principled(nt)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 70.0
    n1.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    mix1 = nt.nodes.new("ShaderNodeMixRGB")
    mix1.inputs[1].default_value = hexcol(base)
    mix1.inputs[2].default_value = hexcol(fiber)
    nt.links.new(n1.outputs[0], mix1.inputs[0])
    b.inputs["Roughness"].default_value = 0.85
    if grease <= 0:
        nt.links.new(mix1.outputs[0], b.inputs["Base Color"])
        return m
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = stain_scale
    n2.inputs["Detail"].default_value = 2.5
    n2.inputs["Distortion"].default_value = 0.9
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.46
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.58
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(n2.outputs[0], ramp.inputs[0])
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = grease
    nt.links.new(ramp.outputs[0], mul.inputs[0])
    mix2 = nt.nodes.new("ShaderNodeMixRGB")
    mix2.inputs[2].default_value = hexcol(dark)
    nt.links.new(mul.outputs[0], mix2.inputs[0])
    nt.links.new(mix1.outputs[0], mix2.inputs[1])
    nt.links.new(mix2.outputs[0], b.inputs["Base Color"])
    r1 = nt.nodes.new("ShaderNodeMath")
    r1.operation = "MULTIPLY"
    r1.inputs[1].default_value = -0.55
    nt.links.new(mul.outputs[0], r1.inputs[0])
    r2 = nt.nodes.new("ShaderNodeMath")
    r2.operation = "ADD"
    r2.inputs[1].default_value = 0.85
    nt.links.new(r1.outputs[0], r2.inputs[0])
    nt.links.new(r2.outputs[0], b.inputs["Roughness"])
    return m


def mat_floor(name):
    m = bpy.data.materials.new(name)
    nt = _nodes(m)
    b = _principled(nt)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 0.9
    n1.inputs["Detail"].default_value = 8.0
    n1.inputs["Roughness"].default_value = 0.65
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.inputs[1].default_value = hexcol("#C9C8C4")
    mix.inputs[2].default_value = hexcol("#B4B3AF")
    nt.links.new(n1.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[0], b.inputs["Base Color"])
    r1 = nt.nodes.new("ShaderNodeMath")
    r1.operation = "MULTIPLY"
    r1.inputs[1].default_value = 0.22
    nt.links.new(n1.outputs[0], r1.inputs[0])
    r2 = nt.nodes.new("ShaderNodeMath")
    r2.operation = "ADD"
    r2.inputs[1].default_value = 0.22
    nt.links.new(r1.outputs[0], r2.inputs[0])
    nt.links.new(r2.outputs[0], b.inputs["Roughness"])
    return m


M = {}


def build_materials():
    for k, h in BIN_COLOR.items():
        M["bin_" + k] = mat_pbr("Bin_" + k.capitalize() + "_PowderCoat", h, rough=0.42)
    M["cap"] = mat_pbr("Bin_Deck_LightGray", "#E6E9ED", rough=0.5)
    M["pocket"] = mat_pbr("Bin_Opening_Dark", "#07080A", rough=0.9)
    M["plinth"] = mat_pbr("Bin_Plinth_Dark", "#16191D", rough=0.6)
    M["label"] = mat_pbr("Bin_Label_White", "#FFFFFF", rough=0.5, emis_hex="#FFFFFF", emis=0.12)
    M["shell"] = mat_pbr("Head_Shell_White", "#F3F5F7", rough=0.38)
    M["glass"] = mat_pbr("Head_Glass_Black", "#030405", rough=0.06, coat=1.0)
    M["lens"] = mat_pbr("Head_Lens_Glass", "#01020A", rough=0.02, coat=1.0)
    M["metal_dark"] = mat_pbr("Mast_Graphite", "#3A4047", rough=0.4, metallic=0.85)
    M["metal_knob"] = mat_pbr("Clamp_Knob_Black", "#111316", rough=0.5)
    M["grille"] = mat_pbr("Head_Grille_Gray", "#7D8590", rough=0.6)
    M["lens_ring"] = mat_emit("Head_LensRing_Glow", "#7FD4FF", 7.0)
    M["wordmark"] = mat_emit("Head_Wordmark", "#FFFFFF", 1.3)
    M["scr_dark"] = mat_emit("Screen_BG_Dark", "#0E131A", 1.0)
    M["scr_green"] = mat_emit("Screen_BG_Compost", BIN_COLOR["compost"], 1.9)
    M["scr_white"] = mat_emit("Screen_White", "#FFFFFF", 3.2)
    M["scr_soft"] = mat_emit("Screen_SoftText", "#C9D1D9", 1.6)
    M["scr_accent"] = mat_emit("Screen_Accent", "#7FD4FF", 2.4)
    M["person"] = mat_pbr("Person_Matte", "#C5CAD2", rough=0.65)
    M["kraft"] = mat_cardboard("Cardboard_Kraft", grease=0.0)
    M["kraft_under"] = mat_cardboard("Cardboard_GreaseThrough", grease=0.55, stain_scale=8.0)
    M["kraft_greasy"] = mat_cardboard("Cardboard_Greasy", grease=1.0, stain_scale=10.0)
    M["print_red"] = mat_pbr("Box_Print_Red", "#C62828", rough=0.7)
    M["crumb"] = mat_pbr("Food_Crumb", "#A06A32", rough=0.9)
    M["cheese"] = mat_pbr("Food_Cheese", "#F0BE4A", rough=0.5)
    M["sauce"] = mat_pbr("Food_Sauce", "#8E2A1C", rough=0.35)
    M["crust"] = mat_pbr("Food_Crust", "#C98F4E", rough=0.8)
    M["beam"] = mat_beam("FX_ViewCone", "#8FD8FF", 1.6, 0.085)
    M["beam_line"] = mat_emit("FX_ViewCone_Edges", "#9CE0FF", 3.2)
    M["decal"] = mat_pbr("Floor_ShowZone", "#F4F9FF", rough=0.6, emis_hex="#CFE6FF", emis=0.75)
    M["floor"] = mat_floor("Floor_PolishedConcrete")
    M["wall"] = mat_pbr("Wall_Warm", "#E4DFD6", rough=0.92)
    M["base"] = mat_pbr("Wall_Baseboard", "#CBC5BA", rough=0.8)
    M["pot"] = mat_pbr("Planter_White", "#ECEAE6", rough=0.6)
    M["leaf"] = mat_pbr("Planter_Foliage", "#2F6B3A", rough=0.75)
    M["plaincan"] = mat_pbr("Retrofit_PlainBin_Steel", "#9BA3AD", rough=0.38, metallic=0.9)
    M["plainlid"] = mat_pbr("Retrofit_PlainBin_Lid", "#2B3036", rough=0.5)


LED = {}


def led_material(key):
    pale = {"recycle": "#C5D6EE", "compost": "#C6E3CD", "landfill": "#D9DDE2"}[key]
    m = mat_pbr("LED_" + key.capitalize(), pale, rough=0.35, emis_hex=LED_COLOR[key], emis=0.05)
    return m


# ----------------------------------------------------------------------------- station
def opening_outline(key, grow=0.0):
    if key == "recycle":
        return circle_pts(0.088 + grow, seg=64)
    if key == "compost":
        return rounded_rect_pts(0.32 + 2 * grow, 0.10 + 2 * grow, 0.05 + grow, seg=12)
    return rounded_rect_pts(0.20 + 2 * grow, 0.20 + 2 * grow, 0.026 + grow, seg=8)


def build_bin(key, coll, helpers, lights):
    x = BIN_X[key]
    w = BIN_BODY_W
    bm = bmesh.new()
    left = [bm.verts.new((-w / 2, y, z)) for y, z in PROFILE]
    right = [bm.verts.new((w / 2, y, z)) for y, z in PROFILE]
    n = len(PROFILE)
    side = []
    for i in range(n):
        j = (i + 1) % n
        side.append(bm.faces.new((left[i], left[j], right[j], right[i])))
    bm.faces.new(left[::-1])
    bm.faces.new(right)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    side[1].material_index = 1      # sloped deposit face
    side[2].material_index = 1      # flat top
    me = mesh_from_bm("Bin_" + key, bm, smooth=True)
    for mm in (M["bin_" + key], M["cap"], M["pocket"]):
        me.materials.append(mm)
    body = new_obj("Bin_" + key.capitalize() + "_Body", me, coll, loc=(x, 0, 0))

    b1 = body.modifiers.new("EdgeBevel", "BEVEL")
    b1.width, b1.segments, b1.limit_method, b1.angle_limit = 0.016, 5, "ANGLE", radians(30)

    # frame on the sloped face: local Z = face normal, local Y = up the slope
    face = new_obj("Bin_" + key.capitalize() + "_FaceFrame", None, coll, loc=(x, -0.1125, 0.87),
                   rot=(SLOPE_ANGLE, 0, 0))
    cut_me = m_prism("Cutter_" + key, opening_outline(key), -0.24, 0.06, smooth=(key == "recycle"), mat_index=2)
    for mm in (M["pocket"], M["pocket"], M["pocket"]):
        cut_me.materials.append(mm)
    cutter = new_obj("Bin_" + key.capitalize() + "_OpeningCutter", cut_me, helpers, parent=face)
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    bo = body.modifiers.new("Opening", "BOOLEAN")
    bo.operation, bo.object, bo.solver = "DIFFERENCE", cutter, "EXACT"
    b2 = body.modifiers.new("LipBevel", "BEVEL")
    b2.width, b2.segments, b2.limit_method, b2.angle_limit = 0.004, 3, "ANGLE", radians(30)
    wn = body.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
    wn.keep_sharp, wn.weight = False, 50

    # plinth (recessed toe-kick)
    new_obj("Bin_" + key.capitalize() + "_Plinth", m_box("Plinth_" + key, w - 0.06, 0.39, 0.06), coll,
            loc=(x, 0.0, 0.03), mat=M["plinth"])

    # LEDs: ring around the opening, light bar on the front, underglow strip + real light
    led = led_material(key)
    ring_pts = [(px, py, 0.0015) for px, py in opening_outline(key, grow=0.017)]
    curve_tube("Bin_" + key.capitalize() + "_LED_Ring", ring_pts, 0.0055, coll, led, closed=True, parent=face)
    bar = new_obj("Bin_" + key.capitalize() + "_LED_Bar",
                  m_prism("LEDBar_" + key, stadium_pts((-0.17, 0), (0.17, 0), 0.016), 0.0, 0.005), coll,
                  loc=(x, -0.2252, 0.692), rot=(radians(90), 0, 0), mat=led)
    glow_mat = mat_emit("LED_" + key.capitalize() + "_Underglow", LED_COLOR[key], 0.0)
    new_obj("Bin_" + key.capitalize() + "_LED_Underglow", m_box("Underglow_" + key, 0.44, 0.012, 0.004), coll,
            loc=(x, -0.205, 0.0575), mat=glow_mat)
    li = bpy.data.lights.new("Bin_" + key.capitalize() + "_GlowLight", "AREA")
    li.shape, li.size, li.size_y = "RECTANGLE", 0.44, 0.05
    li.color = hexcol(LED_COLOR[key])[:3]
    li.energy = 16.0
    glow = new_obj("Bin_" + key.capitalize() + "_GlowLight", li, lights, loc=(x, -0.235, 0.05),
                   rot=(radians(-25), 0, 0))
    glow.visible_camera = False
    ring_li = bpy.data.lights.new("Bin_" + key.capitalize() + "_RingLight", "AREA")
    ring_li.shape, ring_li.size = "DISK", 0.26
    ring_li.color = hexcol(LED_COLOR[key])[:3]
    ring_li.energy = 5.0
    ring_glow = new_obj("Bin_" + key.capitalize() + "_RingLight", ring_li, lights, parent=face,
                        loc=(0, 0, 0.16), rot=(0, 0, 0))
    ring_glow.visible_camera = False
    LED[key] = {"bsdf": _principled(led.node_tree), "under": glow_mat.node_tree.nodes["Emission"],
                "lights": [glow, ring_glow]}

    # front graphics: icon + word (white), slightly proud of the panel
    glyph_obj("Bin_" + key.capitalize() + "_Icon", BIN_ICON[key], 0.185, coll, M["label"],
              loc=(x, -0.2263, 0.485), rot=(radians(90), 0, 0))
    text_obj("Bin_" + key.capitalize() + "_Word", BIN_WORD[key], 0.043, coll, M["label"],
             loc=(x, -0.2263, 0.285), rot=(radians(90), 0, 0))
    return body


def set_lit(target):
    """Only the target bin glows; every other bin stays dim."""
    for key, d in LED.items():
        on = (key == target)
        d["bsdf"].inputs["Emission Strength"].default_value = 3.4 if on else 0.05
        d["under"].inputs["Strength"].default_value = 9.0 if on else 0.0
        for li in d["lights"]:
            li.hide_render = not on
            li.hide_viewport = not on


# ----------------------------------------------------------------------------- Sorty head
def build_head(coll, mount_coll):
    head = new_obj("SortyHead_Frame", None, coll, loc=HEAD_POS, rot=(radians(90 + HEAD_TILT), 0, 0))
    shell = new_obj("SortyHead_Shell", m_box("HeadShell", 0.37, 0.302, 0.052), coll, parent=head,
                    loc=(0, 0, -0.026), mat=M["shell"])
    shell.data.shade_smooth()
    add_bevel(shell, 0.02, segments=6)
    new_obj("SortyHead_Glass", m_prism("HeadGlass", rounded_rect_pts(0.33, 0.262, 0.018), 0.0, 0.002), coll,
            parent=head, mat=M["glass"])
    # camera lens with the glowing "I am looking" ring
    ly = -0.094
    dome = new_obj("SortyHead_Lens", m_sphere("Lens", 0.0185), coll, parent=head, loc=(0, ly, 0.002),
                   scale=(1, 1, 0.42), mat=M["lens"])
    curve_tube("SortyHead_LensIris", [(0.0105 * cos(2 * pi * i / 40), 0.0105 * sin(2 * pi * i / 40), 0.0) for i in range(40)],
               0.0011, coll, M["grille"], parent=head, loc=(0, ly, 0.0088))
    curve_tube("SortyHead_LensRing", [(0.0245 * cos(2 * pi * i / 64), 0.0245 * sin(2 * pi * i / 64), 0.0) for i in range(64)],
               0.0029, coll, M["lens_ring"], parent=head, loc=(0, ly, 0.003))
    # speaker grille (left) and mic holes
    dots = []
    for r in range(4):
        for c in range(11):
            dots.append(circle_pts(0.0021, seg=12, cx=-0.105 + (c - 5) * 0.0072, cy=ly + (r - 1.5) * 0.0072))
    new_obj("SortyHead_SpeakerGrille", m_polys("Grille", dots), coll, parent=head, loc=(0, 0, 0.0024), mat=M["grille"])
    mics = [circle_pts(0.0016, seg=10, cx=sx * 0.046, cy=ly) for sx in (-1, 1)]
    new_obj("SortyHead_Mics", m_polys("Mics", mics), coll, parent=head, loc=(0, 0, 0.0024), mat=M["grille"])
    text_obj("SortyHead_Wordmark", "Sorty", 0.0165, coll, M["wordmark"], parent=head, loc=(0.105, ly, 0.0024))
    # screen frame: children are the per-state graphics
    screen = new_obj("SortyHead_ScreenFrame", None, coll, parent=head, loc=(0, SCREEN_Y, 0.0026))

    # mount: tilt hinge, slim mast and a clamp that grips the back edge of any bin
    hinge = new_obj("Mount_TiltHinge", m_cyl("Hinge", 0.017, 0.09), mount_coll, loc=(0, 0.246, 1.432),
                    rot=(0, radians(90), 0), mat=M["metal_dark"])
    mast = new_obj("Mount_Mast", m_box("Mast", 0.055, 0.032, 0.54), mount_coll, loc=(0, 0.262, 1.185),
                   mat=M["metal_dark"])
    mast.data.shade_smooth()
    add_bevel(mast, 0.006, segments=3)
    jaw = new_obj("Mount_ClampJaw", m_box("ClampJaw", 0.16, 0.09, 0.012), mount_coll, loc=(0, 0.2, 1.0065),
                  mat=M["metal_dark"])
    jaw.data.shade_smooth()
    add_bevel(jaw, 0.003, segments=2)
    back = new_obj("Mount_ClampBack", m_box("ClampBack", 0.16, 0.014, 0.2), mount_coll, loc=(0, 0.234, 0.905),
                   mat=M["metal_dark"])
    for sx in (-1, 1):
        new_obj("Mount_ClampKnob", m_cyl("ClampKnob", 0.013, 0.014, seg=24), mount_coll,
                loc=(sx * 0.052, 0.19, 1.0195), mat=M["metal_knob"])
    return head, screen


def build_screens(screen, parent_coll):
    """Three screen states as separate collections so a state is one visibility switch."""
    sc = {}
    bgpts = rounded_rect_pts(SCREEN_W, SCREEN_H, 0.006)
    z = 0.0007

    # IDLE: friendly face + invitation
    c = sc["IDLE"] = new_coll("Screen_IDLE", parent_coll)
    new_obj("Idle_BG", m_polys("Idle_BG", [bgpts]), c, parent=screen, mat=M["scr_dark"])
    eyes = [rounded_rect_pts(0.034, 0.06, 0.017, cx=sx * 0.05, cy=0.03) for sx in (-1, 1)]
    new_obj("Idle_Eyes", m_polys("Idle_Eyes", eyes), c, parent=screen, loc=(0, 0, z), mat=M["scr_white"])
    new_obj("Idle_Smile", m_polys("Idle_Smile", [arc_band_pts(0, 0.004, 0.027, 0.0065, 205, 335)]), c, parent=screen,
            loc=(0, 0, z), mat=M["scr_white"])
    text_obj("Idle_Text", "Show me your item", 0.0155, c, M["scr_white"], fontfile=FONT_SEMI, parent=screen,
             loc=(0, -0.058, z))

    # ASK: one short instruction + pictogram
    c = sc["ASK"] = new_coll("Screen_ASK", parent_coll)
    new_obj("Ask_BG", m_polys("Ask_BG", [bgpts]), c, parent=screen, mat=M["scr_dark"])
    ix, iy, lw = -0.092, -0.004, 0.0062
    icon = [stadium_pts((ix - 0.034, iy + 0.008), (ix - 0.034, iy - 0.034), lw),
            stadium_pts((ix - 0.034, iy - 0.034), (ix + 0.034, iy - 0.034), lw),
            stadium_pts((ix + 0.034, iy - 0.034), (ix + 0.034, iy + 0.008), lw),
            stadium_pts((ix - 0.034, iy + 0.008), (ix - 0.058, iy + 0.03), lw),
            stadium_pts((ix + 0.034, iy + 0.008), (ix + 0.058, iy + 0.03), lw)]
    new_obj("Ask_BoxIcon", m_polys("Ask_BoxIcon", icon), c, parent=screen, loc=(0, 0, z), mat=M["scr_white"])
    arrow = [stadium_pts((ix, iy - 0.014), (ix, iy + 0.05), lw),
             stadium_pts((ix, iy + 0.05), (ix - 0.016, iy + 0.034), lw),
             stadium_pts((ix, iy + 0.05), (ix + 0.016, iy + 0.034), lw)]
    new_obj("Ask_OpenArrow", m_polys("Ask_OpenArrow", arrow), c, parent=screen, loc=(0, 0, z), mat=M["scr_accent"])
    text_obj("Ask_Text", "Open the box", 0.021, c, M["scr_white"], parent=screen, loc=(0.046, 0.016, z))
    text_obj("Ask_Sub", "and show me the inside", 0.0098, c, M["scr_soft"], fontfile=FONT_SEMI, parent=screen,
             loc=(0.046, -0.024, z))

    # VERDICT: full bin color, the word, and a huge arrow pointing at the physical bin
    c = sc["VERDICT"] = new_coll("Screen_VERDICT", parent_coll)
    new_obj("Verdict_BG", m_polys("Verdict_BG", [bgpts]), c, parent=screen, mat=M["scr_green"])
    text_obj("Verdict_Item", "Greasy box", 0.0098, c, M["scr_white"], fontfile=FONT_SEMI, parent=screen,
             loc=(0, 0.0705, z))
    text_obj("Verdict_Word", "COMPOST", 0.0285, c, M["scr_white"], parent=screen, loc=(0, 0.04, z))
    ht, ws, wh, hh = 0.098, 0.046, 0.124, 0.056
    arr = [(-ws / 2, ht / 2), (-ws / 2, -ht / 2 + hh), (-wh / 2, -ht / 2 + hh), (0, -ht / 2),
           (wh / 2, -ht / 2 + hh), (ws / 2, -ht / 2 + hh), (ws / 2, ht / 2)]
    arr = [(px, py - 0.031) for px, py in arr]        # center bin -> arrow points straight down
    new_obj("Verdict_Arrow", m_polys("Verdict_Arrow", [arr]), c, parent=screen, loc=(0, 0, z), mat=M["scr_white"])
    return sc


# ----------------------------------------------------------------------------- person + pizza box
def two_bone_ik(s, w, l1, l2, pole):
    s, w, pole = Vector(s), Vector(w), Vector(pole)
    d = min((w - s).length, l1 + l2 - 1e-4)
    u = (w - s).normalized()
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = sqrt(max(l1 * l1 - a * a, 0.0))
    perp = (pole - pole.dot(u) * u).normalized()
    return s + u * a + perp * h, s + u * d


def build_pizza_box(coll, origin):
    S, H, T = 0.33, 0.045, 0.004
    frame = new_obj("PizzaBox_Frame", None, coll, loc=origin, rot=(radians(-BOX_TILT), 0, 0))
    base_me = m_box("BoxBase", S, S, T, top_index=(1, 2))
    for mm in (M["kraft"], M["kraft_greasy"], M["kraft_under"]):
        base_me.materials.append(mm)
    new_obj("PizzaBox_Base", base_me, coll, parent=frame, loc=(0, S / 2, T / 2))
    for nm, sz, lc in (("WallNear", (S, T, H), (0, T / 2, H / 2)), ("WallFar", (S, T, H), (0, S - T / 2, H / 2)),
                       ("WallL", (T, S, H), (-S / 2 + T / 2, S / 2, H / 2)),
                       ("WallR", (T, S, H), (S / 2 - T / 2, S / 2, H / 2))):
        new_obj("PizzaBox_" + nm, m_box("Box" + nm, *sz), coll, parent=frame, loc=lc, mat=M["kraft"])
    # leftovers that make the inside read as "greasy pizza box" to the camera
    rnd = random.Random(7)
    for i in range(22):
        r = rnd.uniform(0.003, 0.008)
        ob = new_obj("PizzaBox_Crumb", m_ico("Crumb", r), coll, parent=frame,
                     loc=(rnd.uniform(-0.13, 0.13), rnd.uniform(0.04, 0.29), T + r * 0.45),
                     scale=(rnd.uniform(0.7, 1.5), rnd.uniform(0.7, 1.5), rnd.uniform(0.4, 0.8)),
                     mat=M["cheese"] if i % 4 == 0 else M["crumb"])
    for i in range(4):
        new_obj("PizzaBox_SauceSmear", m_polys("Sauce", [circle_pts(rnd.uniform(0.012, 0.024), seg=20)]), coll,
                parent=frame, loc=(rnd.uniform(-0.1, 0.1), rnd.uniform(0.07, 0.26), T + 0.0004),
                scale=(1, rnd.uniform(0.5, 0.9), 1), mat=M["sauce"])
    crust = [(0.105 * cos(radians(a)), 0.105 * sin(radians(a)), 0.0) for a in range(200, 281, 8)]
    curve_tube("PizzaBox_Crust", crust, 0.012, coll, M["crust"], closed=False, parent=frame, loc=(0.02, 0.2, T + 0.011))

    lid = new_obj("PizzaBox_LidHinge", None, coll, parent=frame, loc=(0, 0, H))
    lw, ld = S + 0.008, S + 0.004
    lid_me = m_box("BoxLid", lw, ld, T, top_index=(0, 1))
    for mm in (M["kraft"], M["kraft_under"]):
        lid_me.materials.append(mm)
    new_obj("PizzaBox_Lid", lid_me, coll, parent=lid, loc=(0, ld / 2, T / 2))
    new_obj("PizzaBox_LidFlapFar", m_box("LidFlapFar", lw, T, 0.04), coll, parent=lid, loc=(0, ld - T / 2, T - 0.02),
            mat=M["kraft"])
    for sx in (-1, 1):
        new_obj("PizzaBox_LidFlapSide", m_box("LidFlapSide", T, ld, 0.04), coll, parent=lid,
                loc=(sx * (lw / 2 - T / 2), ld / 2, T - 0.02), mat=M["kraft"])
    zp = T + 0.0006
    new_obj("PizzaBox_PrintRing", m_band("PrintRing", circle_pts(0.118, 64), circle_pts(0.106, 64)), coll, parent=lid,
            loc=(0, ld / 2, zp), mat=M["print_red"])
    text_obj("PizzaBox_PrintWord", "PIZZA", 0.044, coll, M["print_red"], parent=lid, loc=(0, ld / 2 + 0.006, zp))
    text_obj("PizzaBox_PrintSub", "HOT & FRESH", 0.0105, coll, M["print_red"], fontfile=FONT_SEMI, parent=lid,
             loc=(0, ld / 2 - 0.043, zp))
    return frame, lid


def set_box_open(lid, angle_deg):
    lid.rotation_euler = (radians(angle_deg), 0, 0)


def build_person(coll, box_frame):
    px, py = PERSON_XY
    root = new_obj("Person_Root", None, coll, loc=(px, py, 0))
    mat = M["person"]

    def part(name, mesh, loc, scale=(1, 1, 1)):
        return new_obj("Person_" + name, mesh, coll, parent=root, loc=loc, scale=scale, mat=mat)

    part("Head", m_sphere("PHead", 0.105), (0, 0.01, 1.615), (0.95, 1.0, 1.08))
    limb("Person_Neck", (0, 0, 1.43), (0, 0.005, 1.53), 0.045, coll, mat, parent=root)
    part("Torso", m_capsule("PTorso", 0.15, 0.29), (0, 0, 1.19), (1.24, 0.72, 1.0))
    part("Pelvis", m_sphere("PPelvis", 0.15), (0, 0, 0.93), (1.12, 0.74, 0.72))
    for sx, nm in ((-1, "L"), (1, "R")):
        hip, knee, ankle = (sx * 0.085, 0, 0.9), (sx * 0.09, 0.012, 0.5), (sx * 0.095, -0.005, 0.085)
        limb("Person_Thigh" + nm, hip, knee, 0.074, coll, mat, parent=root)
        limb("Person_Calf" + nm, knee, ankle, 0.056, coll, mat, parent=root)
        foot = limb("Person_Foot" + nm, (sx * 0.095, -0.03, 0.045), (sx * 0.1, 0.15, 0.04), 0.044, coll, mat, parent=root)
    # arms reach to the sides of the pizza box (2-bone IK toward grip points on the box)
    bpy.context.view_layer.update()
    inv = root.matrix_world.inverted()
    for sx, nm in ((-1, "L"), (1, "R")):
        grip_world = box_frame.matrix_world @ Vector((sx * 0.178, 0.135, 0.018))
        grip = inv @ grip_world
        shoulder = Vector((sx * 0.212, 0.0, 1.4))
        elbow, wrist = two_bone_ik(shoulder, grip, 0.29, 0.265, (sx * 0.5, -0.35, -1.0))
        limb("Person_UpperArm" + nm, shoulder, elbow, 0.047, coll, mat, parent=root)
        limb("Person_Forearm" + nm, elbow, wrist, 0.04, coll, mat, parent=root)
        part("Hand" + nm, m_sphere("PHand", 0.046), wrist, (0.55, 1.0, 0.9))
    return root


# ----------------------------------------------------------------------------- FX: camera view cone
def build_fx(coll, lens, target, w=0.56, h=0.44):
    lens, target = Vector(lens), Vector(target)
    axis = (target - lens).normalized()
    right = axis.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(axis).normalized()
    cs = [target + right * (sx * w / 2) + up * (sy * h / 2) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm = bmesh.new()
    va = bm.verts.new(lens)
    vc = [bm.verts.new(c) for c in cs]
    for i in range(4):
        bm.faces.new((va, vc[i], vc[(i + 1) % 4]))
    objs = [new_obj("FX_ViewCone", mesh_from_bm("ViewCone", bm), coll, mat=M["beam"])]
    for i, c in enumerate(cs):
        objs.append(rod("FX_ViewCone_Edge", lens, c, 0.0011, coll, M["beam_line"], seg=8))
    blen, br = 0.085, 0.0042
    for (sx, sy), c in zip(((-1, -1), (1, -1), (1, 1), (-1, 1)), cs):
        objs.append(limb("FX_ScanBracket", c, c - right * (sx * blen), br, coll, M["beam_line"]))
        objs.append(limb("FX_ScanBracket", c, c - up * (sy * blen), br, coll, M["beam_line"]))
    for ob in objs:
        ob.visible_shadow = False
        ob.visible_diffuse = False
        ob.visible_glossy = False
        ob.visible_transmission = False
    return objs


# ----------------------------------------------------------------------------- environment
def build_environment(coll, lights):
    new_obj("Env_Floor", m_polys("Floor", [[(-9, -9), (9, -9), (9, 1), (-9, 1)]]), coll, mat=M["floor"])
    new_obj("Env_Wall", m_polys("Wall", [[(-9, 0), (9, 0), (9, 5), (-9, 5)]]), coll, loc=(0, 0.46, 0),
            rot=(radians(90), 0, 0), mat=M["wall"])
    new_obj("Env_Baseboard", m_box("Baseboard", 18, 0.018, 0.11), coll, loc=(0, 0.451, 0.055), mat=M["base"])
    # "show it here" floor zone: a softly lit outline, footprints and a caption
    cx, cy = 0.0, -0.88
    outer = rounded_rect_pts(0.86, 0.58, 0.09, seg=10, cx=cx, cy=cy)
    inner = rounded_rect_pts(0.86 - 0.036, 0.58 - 0.036, 0.072, seg=10, cx=cx, cy=cy)
    new_obj("ShowZone_Outline", m_band("ShowZoneOutline", outer, inner), coll, loc=(0, 0, 0.0015), mat=M["decal"])
    feet = [stadium_pts((cx + sx * 0.105, cy - 0.11), (cx + sx * 0.105, cy + 0.03), 0.085, seg=10) for sx in (-1, 1)]
    new_obj("ShowZone_Footprints", m_polys("ShowZoneFeet", feet), coll, loc=(0, 0, 0.0015), mat=M["decal"])
    text_obj("ShowZone_Caption", "SHOW YOUR ITEM HERE", 0.034, coll, M["decal"], loc=(cx, cy - 0.37, 0.0015))
    # a simple planter for scale and warmth
    px, py = -1.75, 0.02
    pot = new_obj("Planter_Pot", m_cyl("Pot", 0.21, 0.5, seg=48, r2=0.17), coll, loc=(px, py, 0.25),
                  rot=(radians(180), 0, 0), mat=M["pot"])
    rnd = random.Random(3)
    for i in range(9):
        r = rnd.uniform(0.13, 0.22)
        new_obj("Planter_Foliage", m_ico("Foliage", r, sub=2), coll,
                loc=(px + rnd.uniform(-0.16, 0.16), py + rnd.uniform(-0.12, 0.12), 0.62 + rnd.uniform(0.0, 0.62)),
                scale=(1, 1, rnd.uniform(0.8, 1.2)), mat=M["leaf"])

    world = bpy.data.worlds.new("World_SoftDaylight")
    try:
        world.use_nodes = True
    except Exception:
        pass
    bg = next(n for n in world.node_tree.nodes if n.bl_idname == "ShaderNodeBackground")
    bg.inputs[0].default_value = (0.93, 0.96, 1.0, 1.0)
    bg.inputs[1].default_value = 0.28
    scene.world = world

    def area(name, loc, target, size, size_y, power, color=(1, 1, 1)):
        li = bpy.data.lights.new(name, "AREA")
        li.shape, li.size, li.size_y, li.energy, li.color = "RECTANGLE", size, size_y, power, color
        ob = new_obj(name, li, lights, loc=loc)
        ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        return ob

    area("Light_Key_WindowLeft", (-3.4, -3.6, 3.5), (0.0, -0.1, 0.9), 3.6, 2.6, 260, (1.0, 0.97, 0.93))
    area("Light_Fill_Right", (3.6, -2.8, 2.4), (0.0, -0.2, 0.9), 3.0, 2.0, 80, (0.93, 0.96, 1.0))
    area("Light_Ceiling", (0.0, -1.0, 3.9), (0.0, -0.6, 0.0), 3.4, 1.6, 110)


def add_camera(name, loc, target, lens, coll):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.sensor_width = 36
    cam.clip_start, cam.clip_end = 0.05, 100
    ob = new_obj(name, cam, coll, loc=loc)
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


# ----------------------------------------------------------------------------- render setup
def setup_render():
    scene.render.engine = "CYCLES"
    engine = "Cycles CPU"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for dev_type in ("OPTIX", "CUDA"):
            prefs.compute_device_type = dev_type
            prefs.refresh_devices()
            gpus = [d for d in prefs.devices if d.type == dev_type]
            if gpus:
                for d in prefs.devices:
                    d.use = (d.type == dev_type)
                scene.cycles.device = "GPU"
                engine = "Cycles GPU (" + dev_type + ")"
                break
    except Exception as e:
        print("SORTY: GPU setup failed, using CPU:", e)
    cy = scene.cycles
    cy.samples = 40 if PREVIEW else 224
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.08 if PREVIEW else 0.02
    cy.use_denoising = True
    for dn in ("OPENIMAGEDENOISE", "OPTIX"):
        try:
            cy.denoiser = dn
            break
        except Exception:
            pass
    cy.max_bounces = 8
    cy.sample_clamp_indirect = 8.0
    scene.render.film_transparent = False
    ims = scene.render.image_settings
    try:
        ims.media_type = "IMAGE"
    except Exception:
        pass
    ims.file_format = "PNG"
    ims.color_mode = "RGB"
    vs = scene.view_settings
    for vt, look in (("Khronos PBR Neutral", None), ("AgX", "AgX - Medium High Contrast"), ("Standard", None)):
        try:
            vs.view_transform = vt
            if look:
                vs.look = look
            break
        except Exception:
            pass
    vs.exposure = 0.0
    # soft bloom so LEDs and the screen read as light sources
    try:
        tree = bpy.data.node_groups.new("SortyComp", "CompositorNodeTree")
        scene.compositing_node_group = tree
        rl = tree.nodes.new("CompositorNodeRLayers")
        gl = tree.nodes.new("CompositorNodeGlare")
        out = tree.nodes.new("NodeGroupOutput")
        tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        try:
            rl.scene = scene
        except Exception:
            pass
        gl.inputs["Type"].default_value = "Bloom"
        gl.inputs["Threshold"].default_value = 1.6
        gl.inputs["Strength"].default_value = 0.22
        gl.inputs["Size"].default_value = 0.45
        tree.links.new(rl.outputs["Image"], gl.inputs["Image"])
        tree.links.new(gl.outputs["Image"], out.inputs["Image"])
        scene.render.use_compositing = True
    except Exception as e:
        print("SORTY: compositor bloom skipped:", e)
    return engine


def render(cam, resx, resy, name):
    scene.camera = cam
    k = 0.5 if PREVIEW else 1.0
    scene.render.resolution_x = int(resx * k)
    scene.render.resolution_y = int(resy * k)
    scene.render.resolution_percentage = 100
    path = os.path.join(OUT, name)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("SORTY: rendered", path)
    return path


# ============================================================================= build
build_materials()
C_STATION = new_coll("Station")
C_BINS = new_coll("Bins", C_STATION)
C_HEAD = new_coll("SortyHead", C_STATION)
C_MOUNT = new_coll("Mount_RetrofitKit", C_STATION)
C_SCREENS = new_coll("Screens", C_HEAD)
C_PERSON = new_coll("Person")
C_BOX = new_coll("PizzaBox")
C_FX = new_coll("FX_CameraView")
C_ENV = new_coll("Environment")
C_LIGHTS = new_coll("Lights")
C_CAMS = new_coll("Cameras")
C_HELP = new_coll("Helpers_BooleanCutters")

for key in ("recycle", "compost", "landfill"):
    build_bin(key, C_BINS, C_HELP, C_LIGHTS)
head, screen = build_head(C_HEAD, C_MOUNT)
SCREENS = build_screens(screen, C_SCREENS)
px, py = PERSON_XY
box_frame, box_lid = build_pizza_box(C_BOX, (px, py + 0.24, 1.18))
set_box_open(box_lid, 120)
build_person(C_PERSON, box_frame)
build_environment(C_ENV, C_LIGHTS)
bpy.context.view_layer.update()
LENS_WORLD = head.matrix_world @ Vector((0, -0.094, 0.006))
BOX_CENTER = box_frame.matrix_world @ Vector((0, 0.165, 0.03))
FX = build_fx(C_FX, LENS_WORLD, BOX_CENTER)

CAM_HERO = add_camera("Cam_Hero", (2.55, -3.55, 1.5), (0.0, -0.3, 0.8), 38, C_CAMS)
CAM_FRONT = add_camera("Cam_Front", (0.0, -4.7, 1.25), (0.0, 0.0, 0.86), 50, C_CAMS)
CAM_HEAD = add_camera("Cam_HeadCloseup", (0.4, -0.6, 1.4), (0.0, 0.17, 1.455), 55, C_CAMS)
CAM_STORY = add_camera("Cam_Storyboard", (1.85, -2.95, 1.55), (-0.04, -0.3, 1.08), 50, C_CAMS)
CAM_SORTY = add_camera("Cam_SortyLensView", LENS_WORLD, BOX_CENTER, 22, C_CAMS)

ENGINE = setup_render()
print("SORTY: render engine =", ENGINE)


def set_state(screen_state="VERDICT", lit="compost", person=True, box_open=120, fx=True):
    for name, c in SCREENS.items():
        c.hide_render = (name != screen_state)
        c.hide_viewport = (name != screen_state)
    set_lit(lit)
    for c in (C_PERSON, C_BOX):
        c.hide_render = not person
        c.hide_viewport = not person
    C_FX.hide_render = not (fx and person)
    C_FX.hide_viewport = not (fx and person)
    set_box_open(box_lid, box_open)


if "hero" in VIEWS:
    set_state("VERDICT", "compost", True, 120, True)
    render(CAM_HERO, 1920, 1080, "01_hero.png")

if "front" in VIEWS:
    set_state("IDLE", None, False, 0, False)
    render(CAM_FRONT, 1920, 1080, "02_front_idle.png")

if "head" in VIEWS:
    set_state("ASK", None, False, 0, False)
    render(CAM_HEAD, 1920, 1080, "03_head_closeup.png")

if "story" in VIEWS:
    panels = []
    for i, (st, lit, op) in enumerate((("IDLE", None, 0), ("ASK", None, 0), ("VERDICT", "compost", 120)), 1):
        set_state(st, lit, True, op, True)
        panels.append(render(CAM_STORY, 800, 1000, "_story_%d.png" % i))
    ff = shutil.which("ffmpeg")
    if ff:
        fontf = "C\\:/Windows/Fonts/segoeuib.ttf"
        caps = ["1   Show your item", "2   Sorty asks to open the box", "3   The right bin lights up"]
        k = 0.5 if PREVIEW else 1.0
        band, gap, fs = int(96 * k), int(12 * k), int(38 * k)
        parts = []
        for i, cap in enumerate(caps):
            g = gap if i < 2 else 0
            parts.append("[%d:v]pad=iw+%d:ih+%d:0:0:color=white,drawtext=fontfile='%s':text='%s':fontcolor=0x24292F:"
                         "fontsize=%d:x=%d:y=h-%d[p%d]" % (i, g, band, fontf, cap, fs, int(22 * k), int(band * 0.72), i))
        fc = ";".join(parts) + ";[p0][p1][p2]hstack=inputs=3[out]"
        outp = os.path.join(OUT, "04_storyboard.png")
        cmd = [ff, "-y", "-loglevel", "error"]
        for p in panels:
            cmd += ["-i", p]
        cmd += ["-filter_complex", fc, "-map", "[out]", "-frames:v", "1", outp]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print("SORTY: storyboard stitched" if r.returncode == 0 else "SORTY: ffmpeg failed: " + r.stderr[:400])
    else:
        print("SORTY: ffmpeg not found; storyboard panels left as _story_N.png")

if "camview" in VIEWS:
    set_state("VERDICT", "compost", True, 120, False)
    render(CAM_SORTY, 960, 720, "06_sorty_camera_view.png")

# leave the file in the hero / verdict state
set_state("VERDICT", "compost", True, 120, True)
scene.camera = CAM_HERO
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
scene.render.filepath = "//renders/01_hero.png"
if SAVE and not PREVIEW:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "sorty_station.blend"))
    print("SORTY: saved", os.path.join(HERE, "sorty_station.blend"))
print("SORTY: done")
