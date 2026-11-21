"""Batch B: banana peel, AA batteries, coffee cup, cold cups, foam clamshell, chip bag, napkins."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise
import sortylib as L

WHITE = (1, 1, 1, 1)


def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# =============================================================== banana peel
def banana_mats():
    m, nt, bsdf, out = L.new_mat('banana_skin')
    co = L.tex_coord(nt, 'Object')
    uv = L.tex_coord(nt, 'UV')
    yellow, deep = L.srgb(0.97, 0.79, 0.13), L.srgb(0.90, 0.63, 0.08)
    c = L.mix_col(nt, L.noise_tex(nt, co, scale=14, detail=2), yellow, deep)
    vd = L.voronoi_tex(nt, co, scale=150)
    dots = L.ramp(nt, vd, [(0.16, 1), (0.27, 0)])
    patch = L.ramp(nt, L.noise_tex(nt, L.mapping(nt, co, loc=(3, 1, 2)), scale=20, detail=2), [(0.40, 0), (0.58, 1)])
    c = L.mix_col(nt, L.math_n(nt, 'MULTIPLY', L.math_n(nt, 'MULTIPLY', dots, patch), 0.92), c, L.srgb(0.26, 0.13, 0.04))
    bruise = L.ramp(nt, L.noise_tex(nt, L.mapping(nt, co, loc=(7, 5, 1)), scale=28, detail=3), [(0.62, 0), (0.74, 1)])
    c = L.mix_col(nt, L.math_n(nt, 'MULTIPLY', bruise, 0.75), c, L.srgb(0.38, 0.21, 0.07))
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(uv, sep.inputs[0])
    tip = L.ramp(nt, sep.outputs['Y'], [(0.90, 0), (0.985, 1)])
    c = L.mix_col(nt, tip, c, L.srgb(0.13, 0.08, 0.03))
    edge = L.ramp(nt, L.math_n(nt, 'ABSOLUTE', L.math_n(nt, 'SUBTRACT', sep.outputs['X'], 0.5)), [(0.44, 0), (0.50, 1)])
    c = L.mix_col(nt, L.math_n(nt, 'MULTIPLY', edge, 0.5), c, L.srgb(0.45, 0.28, 0.08))
    L.setp(nt, bsdf, base=c, rough=0.42, sss=0.05, sss_radius=(0.003, 0.002, 0.001))
    L.setp(nt, bsdf, normal=L.bump(nt, L.noise_tex(nt, co, scale=240, detail=2), strength=0.07, distance=0.0003))
    mi, nt, bsdf, out = L.new_mat('banana_inner')
    co = L.tex_coord(nt, 'Object')
    uv = L.tex_coord(nt, 'UV')
    streak = L.noise_tex(nt, L.mapping(nt, uv, scale=(70, 2.5, 1)), scale=1.0, detail=3)
    c = L.mix_col(nt, L.ramp(nt, streak, [(0.35, 0), (0.7, 1)]), L.srgb(0.97, 0.92, 0.72), L.srgb(0.87, 0.76, 0.48))
    ox = L.ramp(nt, L.noise_tex(nt, co, scale=35, detail=2), [(0.60, 0), (0.78, 1)])
    c = L.mix_col(nt, L.math_n(nt, 'MULTIPLY', ox, 0.55), c, L.srgb(0.58, 0.38, 0.15))
    L.setp(nt, bsdf, base=c, rough=0.75, normal=L.bump(nt, streak, strength=0.25, distance=0.0006))
    return m, mi


def peel_strip(name, theta, n_strips, mats, length, r_hub, h_top, seed, tip_curl=0.0, side_bend=0.0, w_max=0.034,
               thick=0.0034, twist=0.0):
    rnd = random.Random(seed)
    w0 = 2 * math.pi * r_hub / n_strips

    def width(s):
        if s < 0.28:
            return w0 + (w_max - w0) * smoothstep(s / 0.28)
        u = (s - 0.28) / 0.72
        return max(w_max * (1 - u ** 2.6), 0.0) + 0.004 * u

    def rcurv(s):
        return r_hub + (0.0195 - r_hub) * smoothstep(s / 0.2) + 0.009 * s

    def edge_drop(s):
        w, rc = width(s), rcurv(s)
        return rc * (1 - math.cos(min(0.5 * w / rc, 1.5)))

    def tw(s):
        return twist * math.pi * smoothstep((s - 0.45) / 0.33)

    reach = 0.056 + rnd.uniform(-0.004, 0.006)
    g = max(length - 0.085, 0.03)
    ctrl = [(r_hub, h_top), (r_hub, h_top - 0.008), (r_hub + 0.002, h_top - 0.015), (r_hub + 0.012, h_top - 0.024),
            (reach * 0.62, 0.024), (reach, 0.014), (reach + 0.33 * g, 0.012), (reach + 0.66 * g, 0.011), (reach + g, 0.009)]
    dense = []
    for a, b in zip(ctrl[:-1], ctrl[1:]):
        for k in range(8):
            t = k / 8
            dense.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    dense.append(ctrl[-1])
    for _ in range(6):
        dense = [dense[0]] + [((dense[i - 1][0] + 2 * dense[i][0] + dense[i + 1][0]) / 4,
                               (dense[i - 1][1] + 2 * dense[i][1] + dense[i + 1][1]) / 4) for i in range(1, len(dense) - 1)] + [dense[-1]]
    acc = [0.0]
    for a, b in zip(dense[:-1], dense[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    K = 44
    samples = []
    for k in range(K + 1):
        tgt = acc[-1] * k / K
        i = 0
        while i < len(acc) - 2 and acc[i + 1] < tgt:
            i += 1
        t = (tgt - acc[i]) / max(acc[i + 1] - acc[i], 1e-9)
        samples.append((dense[i][0] + (dense[i + 1][0] - dense[i][0]) * t, dense[i][1] + (dense[i + 1][1] - dense[i][1]) * t))
    C = []
    for k, (rho, z) in enumerate(samples):
        s = k / K
        if rho >= reach * 0.9:
            ground = thick + 0.0006 + edge_drop(s) * abs(math.cos(tw(s))) + 0.5 * width(s) * abs(math.sin(tw(s)))
            wave = 0.0055 * max(math.sin(s * 10.0 + seed), 0) * (1.0 if s < 0.85 else 0.4)
            z = ground + wave if rho >= reach else max(ground + wave, z)
            z += tip_curl * max(0.0, (s - 0.60) / 0.40) ** 2
        th = theta + side_bend * s * s + 0.10 * math.sin(s * 7.0 + seed) * s
        C.append(Vector((rho * math.cos(th), rho * math.sin(th), z)))
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    J = 10
    rows = []
    for k in range(K + 1):
        s = k / K
        T = (C[min(k + 1, K)] - C[max(k - 1, 0)]).normalized()
        hxy = Vector((T.x, T.y, 0))
        if hxy.length < 0.2:
            th = theta + side_bend * s * s
            hdir = Vector((math.cos(th), math.sin(th), 0))
        else:
            hdir = hxy.normalized()
        Tr, Tz = T.dot(hdir), T.z
        N0 = (-Tz * hdir + Tr * Vector((0, 0, 1))).normalized()
        B0 = N0.cross(T).normalized()
        a_ = tw(s)
        N = N0 * math.cos(a_) + B0 * math.sin(a_)
        B = -N0 * math.sin(a_) + B0 * math.cos(a_)
        w, rc = width(s), rcurv(s)
        row = []
        for j in range(J + 1):
            phi = (j / J - 0.5) * w / rc
            row.append(bm.verts.new(C[k] + B * (rc * math.sin(phi)) - N * (rc * (1 - math.cos(phi)))))
        rows.append(row)
    for k in range(K):
        for j in range(J):
            f = bm.faces.new((rows[k][j], rows[k + 1][j], rows[k + 1][j + 1], rows[k][j + 1]))
            f.smooth = True
            for loop, (a, b) in zip(f.loops, ((j, k), (j, k + 1), (j + 1, k + 1), (j + 1, k))):
                loop[uv_layer].uv = (a / J, b / K)
    ob = L.obj_from_bm(name, bm, smooth=True, mats=list(mats))
    L.add_solidify(ob, thick, offset=-1.0, mat_offset=1, rim_offset=1)
    L.add_subsurf(ob, 1)
    return ob


def make_banana_peel(seed=2):
    m_out, m_in = banana_mats()
    r_hub, h_top = 0.0098, 0.052
    D = math.radians
    specs = [(D(207), 0.172, 0.010, 0.28, 0.0), (D(300), 0.150, 0.016, -0.22, 1.0), (D(28), 0.162, 0.006, 0.26, 0.0), (D(118), 0.128, 0.030, -0.20, 0.0)]
    strips = []
    for i, (th, ln, curl, bend, twist) in enumerate(specs):
        strips.append(peel_strip(f'peel{i}', th, 4, (m_out, m_in), ln, r_hub, h_top, seed + i * 3, tip_curl=curl, side_bend=bend, twist=twist))
    ms, nt, bsdf, out = L.new_mat('banana_stem')
    co = L.tex_coord(nt, 'Object')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(co, sep.inputs[0])
    c = L.ramp(nt, L.math_n(nt, 'MULTIPLY', sep.outputs['Z'], 1 / 0.029),
               [(0.0, L.srgb(0.93, 0.74, 0.12)), (0.45, L.srgb(0.62, 0.55, 0.16)), (0.82, L.srgb(0.33, 0.24, 0.10)), (0.97, L.srgb(0.10, 0.07, 0.04))])
    L.setp(nt, bsdf, base=c, rough=0.6)
    stem = L.lathe('stem', [(r_hub * 1.03, -0.003), (r_hub * 0.98, 0.003), (0.0068, 0.009), (0.0054, 0.021), (0.0057, 0.0275),
                            (0.0048, 0.0295), (0.0006, 0.0299)], segments=28, mats=[ms], cap_top=True)
    stem.location = (0, 0, h_top - 0.001)
    stem.rotation_euler = (math.radians(13), math.radians(-9), 0)
    for s_ in strips[1:] + [stem]:
        L.parent(s_, strips[0])
    return strips[0], strips + [stem]


@L.frame('banana_peel')
def f_banana(scene):
    root, objs = make_banana_peel()
    root.rotation_euler.z = math.radians(12)
    return dict(objs=objs, lens=35, shot=dict(elev=40, azim=8, fill=0.74, fstop=9))


# =============================================================== AA batteries
def make_battery(name='battery'):
    Rb = 0.0070
    W, H = 2 * math.pi * Rb, 0.0464
    BLUE, YEL = L.srgb(0.04, 0.17, 0.50), L.srgb(0.98, 0.78, 0.08)
    lb = L.Label('aa_label', W, H, px=1536, bg=BLUE)
    lb.rect(0, H / 2 - 0.0042, W, 0.0084, YEL)
    lb.rect(0, H / 2 - 0.0092, W, 0.0010, WHITE)
    lb.rect(0, -H / 2 + 0.0012, W, 0.0024, L.srgb(0.75, 0.76, 0.78))
    r90 = math.pi / 2
    for xo in (0.0, W / 2 - 0.0001, -W / 2 + 0.0001):        # repeated so it reads from either side
        lb.text('AA', xo - 0.0008, -0.0125, 0.0100, WHITE, 'ariblk.ttf', rot=r90)
        lb.text('1.5V', xo - 0.0006, 0.0068, 0.0058, YEL, 'arialbd.ttf', rot=r90)
        lb.text('ALKALINE BATTERY', xo + 0.0056, -0.0040, 0.0026, WHITE, 'arialbd.ttf', rot=r90)
        lb.text('+', xo - 0.0004, H / 2 - 0.0042, 0.0085, BLUE, 'ariblk.ttf', rot=r90)
    img = lb.render()
    lab = L.image_mat('aa_wrap', img, rough=0.33, metallic=0.15, coat=0.2)
    steel = L.metal('nickel', color=(0.80, 0.80, 0.78, 1), rough=0.25)
    prof = [(0.0005, 0.0, 1), (0.0055, 0.0, 1), (0.0066, 0.0005, 1), (0.0070, 0.0014, 0), (0.0070, 0.0478, 1),
            (0.0066, 0.0487, 1), (0.0048, 0.0491, 1), (0.0029, 0.0491, 1), (0.0029, 0.0503, 1), (0.0025, 0.0507, 1), (0.0005, 0.0507, 1)]
    return L.lathe(name, prof, segments=64, mats=[lab, steel], cap_bottom=True, cap_top=True, sharp_deg=50)


def lay_cylinder(ob, loc, yaw_deg, roll_deg, radius):
    M = Matrix.Translation((loc[0], loc[1], radius)) @ Matrix.Rotation(math.radians(yaw_deg), 4, 'Z') @ \
        Matrix.Rotation(math.radians(90), 4, 'Y') @ Matrix.Rotation(math.radians(roll_deg), 4, 'Z')
    ob.matrix_world = M


@L.frame('battery_aa')
def f_battery(scene):
    a = make_battery('battery_a')
    b = make_battery('battery_b')
    lay_cylinder(a, (-0.026, -0.012, 0), -10, -42, 0.0070)
    lay_cylinder(b, (-0.012, 0.022, 0), 28, -150, 0.0070)
    return dict(objs=[a, b], lens=50, shot=dict(elev=34, azim=6, fill=0.66, fstop=16))


# =============================================================== coffee cup with lid
def make_coffee_cup():
    r0, r1, Hc = 0.0290, 0.0445, 0.110

    def rad(z):
        return r0 + (r1 - r0) * z / Hc

    paper, nt, bsdf, out = L.new_mat('cup_paper')
    co = L.tex_coord(nt, 'Object')
    n = L.noise_tex(nt, co, scale=500, detail=2)
    L.setp(nt, bsdf, base=L.srgb(0.95, 0.94, 0.91), rough=0.62, normal=L.bump(nt, n, strength=0.05, distance=0.0002))
    cup = L.lathe('coffee_cup', [(0.0006, 0.0045), (0.0272, 0.0045), (0.0276, 0.0), (r0, 0.0)] +
                  [(rad(z), z) for z in (0.004, 0.03, 0.06, 0.09, Hc)] + [(r1 + 0.0012, Hc + 0.0008), (r1 + 0.0010, Hc + 0.0022)],
                  segments=96, mats=[paper], cap_bottom=True, sharp_deg=50)
    # sleeve
    zs0, zs1 = 0.030, 0.086
    W, H = 2 * math.pi * (rad(0.058) + 0.0013), zs1 - zs0
    kraft = L.srgb(0.70, 0.53, 0.33)
    brown = L.srgb(0.24, 0.13, 0.06)
    lb = L.Label('sleeve', W, H, px=2048, bg=kraft)
    lb.text('COFFEE', 0, 0.006, 0.022, brown, 'COOPBL.TTF', fit_w=0.070)
    lb.text('FRESHLY  BREWED', 0, -0.012, 0.0052, brown, 'arialbd.ttf', spacing=1.3)
    lb.rect(0, 0.0205, 0.070, 0.0010, brown)
    lb.rect(0, -0.0185, 0.070, 0.0010, brown)
    lb.text('CAUTION: CONTENTS HOT', W * 0.36, 0.0, 0.0050, brown, 'arialbd.ttf')
    lb.text('Made with recycled paper', -W * 0.36, 0.0, 0.0044, brown, 'arial.ttf')
    img = lb.render()
    sm, nt, bsdf, out = L.new_mat('sleeve_mat')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    uv = L.tex_coord(nt, 'UV')
    ribs = L.wave_tex(nt, L.mapping(nt, uv, scale=(1, 0, 0)), scale=41.0, direction='X')
    fib = L.noise_tex(nt, L.tex_coord(nt, 'Object'), scale=600, detail=2)
    c = L.mix_col(nt, L.math_n(nt, 'MULTIPLY', fib, 0.25), tex.outputs['Color'], L.scale_col(kraft, 0.7))
    L.setp(nt, bsdf, base=c, rough=0.9, normal=L.bump(nt, L.math_n(nt, 'ADD', ribs, L.math_n(nt, 'MULTIPLY', fib, 0.3)), strength=0.35, distance=0.0008))
    sleeve = L.lathe('sleeve', [(rad(zs0) + 0.0002, zs0 - 0.0004), (rad(zs0) + 0.0014, zs0)] +
                     [(rad(z) + 0.0014, z) for z in (0.044, 0.058, 0.072)] + [(rad(zs1) + 0.0014, zs1), (rad(zs1) + 0.0002, zs1 + 0.0004)],
                     segments=96, mats=[sm, sm], sharp_deg=40)
    # make UV v span only the printed band: lathe gives v over all faces of material 0 (whole sleeve) which is fine
    L.parent(sleeve, cup)
    # lid
    lidm = L.plastic('lid_white', L.srgb(0.96, 0.96, 0.95), rough=0.32, sss=0.08)
    zl = Hc
    lp = [(r1 + 0.0024, zl - 0.0050), (r1 + 0.0030, zl - 0.0030), (r1 + 0.0031, zl + 0.0020), (r1 + 0.0024, zl + 0.0052),
          (r1 + 0.0008, zl + 0.0062), (r1 - 0.0008, zl + 0.0058), (r1 - 0.0016, zl + 0.0040), (r1 - 0.0034, zl + 0.0038),
          (r1 - 0.0046, zl + 0.0060), (r1 - 0.0058, zl + 0.0108), (r1 - 0.0075, zl + 0.0124), (r1 - 0.0110, zl + 0.0128),
          (0.0250, zl + 0.0126), (0.0200, zl + 0.0108), (0.0080, zl + 0.0104), (0.0006, zl + 0.0104)]
    lid = L.lathe('lid', lp, segments=96, mats=[lidm], cap_top=True, sharp_deg=45)
    L.parent(lid, cup)
    hole = L.disc('sip_hole', 0.0030, mat=L.simple_mat('hole', (0.004, 0.004, 0.004, 1), rough=0.6))
    hole.scale = (1.9, 0.75, 1)
    a = math.radians(-112)
    hole.location = (0.0345 * math.cos(a), 0.0345 * math.sin(a), zl + 0.01285)
    hole.rotation_euler.z = a + math.pi / 2
    L.parent(hole, cup)
    return cup


@L.frame('coffee_cup_lid')
def f_coffee(scene):
    cup = make_coffee_cup()
    cup.rotation_euler.z = math.radians(8)
    return dict(objs=[cup], lens=40, shot=dict(elev=21, azim=12, fill=0.66, fstop=11))


# =============================================================== clear cold cup
CUP_PROFILE = [(0.0006, 0.0026), (0.0240, 0.0026), (0.0270, 0.0018), (0.0292, 0.0), (0.0308, 0.0006), (0.0314, 0.0030),
               (0.0330, 0.0280), (0.0334, 0.0300), (0.0342, 0.0312), (0.0343, 0.0335), (0.0349, 0.0345), (0.0350, 0.0368),
               (0.0402, 0.0770), (0.0455, 0.1170), (0.0462, 0.1186), (0.0472, 0.1196), (0.0478, 0.1207), (0.0476, 0.1218), (0.0468, 0.1224)]


def make_cold_cup(marking=None):
    clear = L.clear_mat('cup_clear', tint=(0.99, 1.0, 0.995, 1), rough=0.03, ior=1.47, shadow=0.9)
    cup = L.lathe('cold_cup', CUP_PROFILE, segments=96, mats=[clear], cap_bottom=True, sharp_deg=50)
    L.add_solidify(cup, 0.00042, offset=-1.0)
    if marking:
        green = L.srgb(0.03, 0.36, 0.12)
        gray = L.srgb(0.10, 0.10, 0.11)
        ink = L.simple_mat('mark_ink', green if marking == 'compostable' else gray, rough=0.55)
        zt = 0.0026 - 0.00035
        flip = (math.pi, 0, 0)

        def put(body, y, size, fname='arialbd.ttf', spacing=1.0):
            t = L.text_obj('mark', body, size, ink, fname, spacing=spacing)
            t.rotation_euler = flip
            t.location = (0, y, zt)
            L.parent(t, cup)
            return t

        if marking == 'compostable':
            put('COMPOSTABLE', -0.0142, 0.0047, 'arialbd.ttf', 1.05)
            put('♹', -0.0002, 0.0300, 'seguisym.ttf')
            put('PLA', 0.0150, 0.0060, 'ariblk.ttf', 1.1)
            band = L.lathe('green_band', [(0.04335, 0.1010), (0.04435, 0.1085)], segments=96,
                           mats=[L.simple_mat('band_green', L.srgb(0.08, 0.52, 0.20), rough=0.4)])
            L.parent(band, cup)
        else:
            put('♳', -0.0035, 0.0320, 'seguisym.ttf')
            put('PETE', 0.0138, 0.0064, 'ariblk.ttf', 1.1)
    return cup


@L.frame('cold_cup_side')
def f_cup_side(scene):
    cup = make_cold_cup(None)
    return dict(objs=[cup], lens=42, shot=dict(elev=12, azim=10, fill=0.68, fstop=11))


def cup_bottom_shot(marking):
    cup = make_cold_cup(marking)
    tilt = math.degrees(math.atan((0.0478 - 0.0308) / 0.121))
    cup.rotation_euler = (math.radians(-90 + tilt), 0, math.radians(-14))
    bpy.context.view_layer.update()
    zmin = min(p.z for p in L.bbox_points([cup]))
    cup.location.z -= zmin
    bpy.context.view_layer.update()
    base = cup.matrix_world @ Vector((0, 0, 0.002))
    return dict(objs=[cup], lens=50, shot=dict(elev=10, azim=-14, fstop=16, target=tuple(base + Vector((0, 0, 0.004))), dist=0.215))


@L.frame('cold_cup_bottom_compostable')
def f_cup_comp(scene):
    return cup_bottom_shot('compostable')


@L.frame('cold_cup_bottom_pet')
def f_cup_pet(scene):
    return cup_bottom_shot('pet')


# =============================================================== foam clamshell
def rr_ring(w, d, r, n=8):
    pts = []
    for (cx, cy, a0) in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def make_tray(name, w, d, h, r, slope, flange, mat, flip=False, y_off=0.0, thick=0.0030):
    rings = [(w - 2 * slope - 0.040, d - 2 * slope - 0.040, max(r - slope - 0.012, 0.006), 0.0028),
             (w - 2 * slope - 0.032, d - 2 * slope - 0.032, max(r - slope - 0.009, 0.008), 0.0),
             (w - 2 * slope - 0.008, d - 2 * slope - 0.008, r - slope * 0.6, 0.0),
             (w - 2 * slope, d - 2 * slope, r - slope * 0.5, 0.0045),
             (w - 0.0015, d - 0.0015, r, h - 0.003), (w, d, r, h),
             (w + 2 * flange, d + 2 * flange, r + flange, h), (w + 2 * flange + 0.0008, d + 2 * flange + 0.0008, r + flange, h - 0.0026)]
    bm = bmesh.new()
    vr = []
    for (rw, rd, rr, z) in rings:
        zz = (h - z) if flip else z
        vr.append([bm.verts.new((x, y + y_off, zz)) for x, y in rr_ring(rw, rd, rr)])
    n = len(vr[0])
    for i in range(len(vr) - 1):
        for j in range(n):
            j2 = (j + 1) % n
            vs = (vr[i][j], vr[i][j2], vr[i + 1][j2], vr[i + 1][j])
            f = bm.faces.new(tuple(reversed(vs)) if flip else vs)
            f.smooth = True
    f = bm.faces.new(vr[0] if flip else list(reversed(vr[0])))
    ob = L.obj_from_bm(name, bm, smooth=True, sharp_deg=55, mats=[mat])
    L.add_solidify(ob, thick, offset=-1.0)
    return ob


def foam_mat():
    m, nt, bsdf, out = L.new_mat('foam')
    co = L.tex_coord(nt, 'Object')
    cells = L.voronoi_tex(nt, co, scale=650)
    n = L.noise_tex(nt, co, scale=90, detail=2)
    c = L.mix_col(nt, n, L.srgb(0.93, 0.93, 0.92), L.srgb(0.98, 0.98, 0.97))
    h = L.math_n(nt, 'ADD', L.math_n(nt, 'MULTIPLY', cells, 0.5), L.math_n(nt, 'MULTIPLY', n, 0.5))
    L.setp(nt, bsdf, base=c, rough=0.47, sss=0.30, sss_radius=(0.005, 0.005, 0.005), spec=0.35,
           normal=L.bump(nt, h, strength=0.22, distance=0.0006))
    return m


def make_clamshell(open_deg=0.0):
    w, d, r, fl = 0.215, 0.195, 0.032, 0.006
    h1, h2 = 0.034, 0.038
    foam = foam_mat()
    base = make_tray('clam_base', w, d, h1, r, 0.014, fl, foam)
    lid = make_tray('clam_lid', w, d, h2, r, 0.015, fl, foam, flip=True, y_off=-(d / 2 + fl))
    # flipped tray spans z 0..h2 with its flange at z=0 after flip (h - z): flange was at z=h -> 0
    lid.location = (0, d / 2 + fl, h1 + 0.0006)
    lid.rotation_euler.x = -math.radians(open_deg)
    L.parent(lid, base)
    hinge = L.box_obj('clam_hinge', (w - 0.05, 0.0075, 0.0022), loc=(0, d / 2 + fl + 0.001, h1), mat=foam)
    L.parent(hinge, base)
    bm = bmesh.new()
    L.add_box(bm, (0.034, 0.0035, 0.011), (0, -(d + 2 * fl) + 0.0005, -0.0035))
    tab = L.obj_from_bm('clam_tab', bm, mats=[foam])
    L.add_bevel(tab, 0.0012, segments=2, angle=100)
    L.parent(tab, lid)
    return base, lid


def add_food(base, seed=7):
    rnd = random.Random(seed)
    zf = 0.0062
    # fried rice mound
    rm, nt, bsdf, out = L.new_mat('rice')
    co = L.tex_coord(nt, 'Object')
    cells = L.voronoi_tex(nt, L.mapping(nt, co, scale=(1, 1.9, 1)), scale=420)
    c = L.mix_col(nt, cells, L.srgb(0.93, 0.80, 0.52), L.srgb(0.70, 0.52, 0.26))
    L.setp(nt, bsdf, base=c, rough=0.5, normal=L.bump(nt, cells, strength=0.8, distance=0.0014))
    cx, cy, a, b, ch = -0.036, 0.012, 0.056, 0.046, 0.024
    mound = L.blob('rice_mound', 0.044, subdiv=4, amp=0.22, freq=2.4, seed=seed, squash=(1.3, 1.02, 0.52), mat=rm)
    mound.location = (cx, cy, zf + 0.001)
    L.parent(mound, base)
    grains = [L.simple_mat('rice_grain_a', L.srgb(0.97, 0.88, 0.62), rough=0.45, sss=0.1),
              L.simple_mat('rice_grain_b', L.srgb(0.90, 0.74, 0.42), rough=0.45, sss=0.1)]
    bms = [bmesh.new(), bmesh.new()]
    for k in range(1500):
        x, y = cx + rnd.uniform(-0.085, 0.085), cy + rnd.uniform(-0.070, 0.070)
        q = ((x - cx) / a) ** 2 + ((y - cy) / b) ** 2
        if q < 1.0:
            z = zf + 0.0015 + ch * math.sqrt(1 - q) + rnd.uniform(-0.0004, 0.0018)
        elif q < 2.6 and rnd.random() < 0.40:
            z = zf + 0.0008
        else:
            continue
        M = Matrix.Translation((x, y, z)) @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, 'Z') @ Matrix.Rotation(rnd.uniform(-0.5, 0.5), 4, 'Y') @ \
            Matrix.Diagonal((0.0036, 0.0013, 0.0012, 1))
        bmesh.ops.create_icosphere(bms[k % 2], subdivisions=1, radius=1.0, matrix=M)
    for i_, bm_ in enumerate(bms):
        L.parent(L.obj_from_bm(f'rice_grains{i_}', bm_, smooth=True, mats=[grains[i_]]), base)
    pea = L.simple_mat('pea', L.srgb(0.33, 0.58, 0.16), rough=0.45)
    carrot = L.simple_mat('carrot', L.srgb(0.93, 0.45, 0.08), rough=0.5)
    egg = L.simple_mat('egg', L.srgb(0.98, 0.86, 0.30), rough=0.5)
    bm_p, bm_c, bm_e = bmesh.new(), bmesh.new(), bmesh.new()
    for k in range(48):
        x, y = cx + rnd.uniform(-0.048, 0.048), cy + rnd.uniform(-0.038, 0.038)
        q = ((x - cx) / a) ** 2 + ((y - cy) / b) ** 2
        if q >= 0.95:
            continue
        z = zf + 0.0030 + ch * math.sqrt(1 - q)
        if k % 3 == 0:
            bmesh.ops.create_icosphere(bm_p, subdivisions=2, radius=0.0040, matrix=Matrix.Translation((x, y, z)))
        elif k % 3 == 1:
            L.add_box(bm_c, (0.0064, 0.0062, 0.0052), (x, y, z), rot=Matrix.Rotation(rnd.uniform(0, 3), 3, 'Z') @ Matrix.Rotation(rnd.uniform(0, 1), 3, 'X'))
        else:
            L.add_box(bm_e, (0.0085, 0.0060, 0.0030), (x, y, z), rot=Matrix.Rotation(rnd.uniform(0, 3), 3, 'Z') @ Matrix.Rotation(rnd.uniform(0, 0.6), 3, 'X'))
    L.parent(L.obj_from_bm('peas', bm_p, smooth=True, mats=[pea]), base)
    for nm, bm_, mt in (('carrots', bm_c, carrot), ('egg', bm_e, egg)):
        o_ = L.obj_from_bm(nm, bm_, mats=[mt])
        L.add_bevel(o_, 0.0008)
        L.parent(o_, base)
    # fries
    fm, nt, bsdf, out = L.new_mat('fries')
    co = L.tex_coord(nt, 'Object')
    n = L.noise_tex(nt, co, scale=120, detail=3)
    c = L.ramp(nt, n, [(0.30, L.srgb(0.62, 0.36, 0.10)), (0.50, L.srgb(0.90, 0.66, 0.24)), (0.75, L.srgb(0.97, 0.80, 0.38))])
    L.setp(nt, bsdf, base=c, rough=0.55, normal=L.bump(nt, n, strength=0.3, distance=0.0006))
    bm = bmesh.new()
    for k in range(10):
        ln = rnd.uniform(0.042, 0.070)
        x, y = 0.048 + rnd.uniform(-0.020, 0.020), 0.004 + rnd.uniform(-0.040, 0.040)
        z = zf + 0.0045 + 0.0055 * (k % 3)
        R = Matrix.Rotation(rnd.uniform(0, 3.14), 3, 'Z') @ Matrix.Rotation(rnd.uniform(-0.16, 0.16), 3, 'Y')
        L.add_box(bm, (ln, 0.0082, 0.0078), (x, y, z), rot=R)
    fr = L.obj_from_bm('fries', bm, mats=[fm])
    L.add_bevel(fr, 0.0014, segments=2)
    L.parent(fr, base)
    # half-eaten breaded chicken pieces
    nm_, nt, bsdf, out = L.new_mat('nugget')
    co = L.tex_coord(nt, 'Object')
    n = L.noise_tex(nt, co, scale=220, detail=4, rough=0.7)
    c = L.ramp(nt, n, [(0.30, L.srgb(0.45, 0.24, 0.07)), (0.52, L.srgb(0.72, 0.45, 0.14)), (0.75, L.srgb(0.88, 0.62, 0.24))])
    L.setp(nt, bsdf, base=c, rough=0.7, normal=L.bump(nt, n, strength=0.8, distance=0.002))
    for k, (x, y, r_, rz) in enumerate(((0.012, -0.052, 0.019, 0.4), (-0.058, -0.048, 0.015, 1.3))):
        ng = L.blob(f'nugget{k}', r_, subdiv=4, amp=0.30, freq=1.8, seed=seed + 11 + k, squash=(1.25, 0.95, 0.55), mat=nm_)
        ng.location = (x, y, zf + r_ * 0.5)
        ng.rotation_euler.z = rz
        L.parent(ng, base)
    # ketchup smears (flat, glossy)
    sm, nt, bsdf, out = L.new_mat('sauce')
    co = L.tex_coord(nt, 'Object')
    n = L.noise_tex(nt, co, scale=70, detail=3)
    c = L.mix_col(nt, n, L.srgb(0.42, 0.03, 0.02), L.srgb(0.62, 0.08, 0.03))
    L.setp(nt, bsdf, base=c, rough=0.12, normal=L.bump(nt, n, strength=0.15, distance=0.0005))
    for k, (x, y, rr, sx, sy, rz) in enumerate(((0.070, -0.050, 0.017, 1.3, 0.8, 0.3), (0.082, 0.046, 0.011, 1.0, 1.4, 1.1), (-0.004, 0.066, 0.010, 2.0, 0.6, -0.4))):
        s_ = L.blob(f'sauce{k}', rr, subdiv=4, amp=0.55, freq=1.3, seed=seed + k, squash=(sx, sy, 0.028), mat=sm)
        s_.location = (x, y, zf + 0.0002)
        s_.rotation_euler.z = rz
        L.parent(s_, base)


@L.frame('clamshell_closed')
def f_clam_closed(scene):
    base, lid = make_clamshell(0.0)
    base.rotation_euler.z = math.radians(-10)
    return dict(objs=[base, lid], lens=32, shot=dict(elev=27, azim=28, fill=0.72, fstop=8))


@L.frame('clamshell_open_food')
def f_clam_open(scene):
    base, lid = make_clamshell(112.0)
    add_food(base)
    base.rotation_euler.z = math.radians(-8)
    return dict(objs=[base], lens=32, shot=dict(elev=42, azim=16, fill=0.76, fstop=8, shift=(0.0, 0.05)))


# =============================================================== chip bag
def make_chip_bag(seed=5.0):
    w, h = 0.170, 0.235
    YEL, REDC = L.srgb(0.99, 0.79, 0.04), L.srgb(0.80, 0.07, 0.05)
    lb = L.Label('chips_front', w, h, px=2048, bg=YEL)
    lb.rect(0, -h / 2 + 0.028, w, 0.056, REDC)
    lb.wave_band(-h / 2 + 0.058, 0.004, 0.006, WHITE, periods=2)
    lb.ellipse(0, 0.026, 0.074, 0.040, WHITE, rot=0.10)
    lb.ellipse(0, 0.026, 0.070, 0.036, REDC, rot=0.10)
    lb.text('CHIPS', 0, 0.026, 0.044, WHITE, 'COOPBL.TTF', rot=0.10, shear=0.15, fit_w=0.118)
    lb.text('CRUNCHY', 0, 0.073, 0.0125, REDC, 'ariblk.ttf', spacing=1.25)
    gold, gold_d = L.srgb(0.96, 0.74, 0.26), L.srgb(0.80, 0.52, 0.12)
    for (x, y, rot) in ((-0.040, -0.034, 0.4), (0.004, -0.040, -0.2), (0.046, -0.030, 0.9)):
        lb.ellipse(x, y, 0.0245, 0.0165, gold_d, rot=rot)
        lb.ellipse(x, y, 0.0228, 0.0150, gold, rot=rot)
        for k in (-1, 0, 1):
            lb.rect(x + k * 0.008 * math.cos(rot), y + k * 0.008 * math.sin(rot), 0.0014, 0.022, gold_d, rot=rot)
    lb.text('CLASSIC SALTED', 0, -h / 2 + 0.034, 0.0100, WHITE, 'arialbd.ttf', spacing=1.2)
    lb.text('POTATO CHIPS', 0, -h / 2 + 0.019, 0.0060, WHITE, 'arialbd.ttf', spacing=1.3)
    lb.text('NET WT 1 OZ (28g)', 0, -h / 2 + 0.008, 0.0042, WHITE, 'arial.ttf')
    img = lb.render()

    silver = (0.90, 0.90, 0.92, 1)
    fm, nt, bsdf, out = L.new_mat('chip_front')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    bf = L.backfacing(nt)
    uv = L.tex_coord(nt, 'UV')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(uv, sep.inputs[0])
    seal = L.math_n(nt, 'MAXIMUM', L.ramp(nt, sep.outputs['Y'], [(0.052, 1), (0.060, 0)]), L.ramp(nt, sep.outputs['Y'], [(0.940, 0), (0.948, 1)]))
    ribs = L.wave_tex(nt, L.mapping(nt, uv, scale=(1, 0, 0)), scale=22.0, direction='X')
    L.setp(nt, bsdf, base=L.mix_col(nt, bf, tex.outputs['Color'], silver), metallic=L.mix_val(nt, bf, 0.30, 1.0), rough=0.23,
           normal=L.bump(nt, L.math_n(nt, 'MULTIPLY', ribs, seal), strength=0.6, distance=0.0008))
    bm_, nt, bsdf, out = L.new_mat('chip_inside')
    uv = L.tex_coord(nt, 'UV')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(uv, sep.inputs[0])
    seal = L.math_n(nt, 'MAXIMUM', L.ramp(nt, sep.outputs['Y'], [(0.052, 1), (0.060, 0)]), L.ramp(nt, sep.outputs['Y'], [(0.940, 0), (0.948, 1)]))
    ribs = L.wave_tex(nt, L.mapping(nt, uv, scale=(1, 0, 0)), scale=22.0, direction='X')
    L.setp(nt, bsdf, base=silver, metallic=1.0, rough=0.24, normal=L.bump(nt, L.math_n(nt, 'MULTIPLY', ribs, seal), strength=0.6, distance=0.0008))

    nx, ny = 60, 82

    def fr(x, y, f, s=0.0):
        return noise.fractal(Vector((x * f + s, y * f - s, seed)), 1.0, 2.0, 4)

    def ridge(x, y, f, s=0.0):
        return noise.ridged_multi_fractal(Vector((x * f + s, y * f + s * 0.7, seed * 1.3)), 1.0, 2.0, 3, 1.0, 2.0)

    def pil(x, y):
        return max(0.0, 1 - (2 * x / w) ** 2) ** 0.5 * max(0.0, 1 - (2 * y / h) ** 2) ** 0.5

    def tear_y(x):
        return h / 2 - 0.038 + 0.008 * fr(x, 0, 34, 3.0) - 0.050 * math.exp(-((x - 0.040) / 0.030) ** 2)

    def build(front):
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new('UVMap')
        grid = []
        for j in range(ny + 1):
            row = []
            for i in range(nx + 1):
                x0, y0 = -w / 2 + w * i / nx, -h / 2 + h * j / ny
                p = pil(x0, y0)
                x = x0 + 0.0035 * fr(x0, y0, 9, 1.0) * abs(2 * x0 / w) + 0.010 * (y0 / h) * (2 * x0 / w) * 0.3
                y = y0 + 0.0030 * fr(x0, y0, 8, 5.0)
                if front:
                    z = 0.0016 + 0.0085 * p ** 0.75 * (0.65 + 0.35 * fr(x0, y0, 7, 2.0)) + 0.0088 * (ridge(x0, y0, 16) - 0.9) * p ** 0.35 \
                        + 0.0022 * fr(x0, y0, 55, 8.0) * p ** 0.3
                    z = max(z, 0.0030)
                    ty = tear_y(x0)
                    if y0 > ty - 0.022:
                        z += 0.007 * ((y0 - (ty - 0.022)) / 0.022) ** 2
                else:
                    z = 0.0006 + 0.0010 * max(ridge(x0, y0, 14, 4.0) - 0.8, 0) * p ** 0.4
                row.append(bm.verts.new((x, y, z)))
            grid.append(row)
        for j in range(ny):
            for i in range(nx):
                xc, yc = -w / 2 + w * (i + 0.5) / nx, -h / 2 + h * (j + 0.5) / ny
                if front and yc > tear_y(xc):
                    continue
                f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
                f.smooth = True
                for loop, (a_, b_) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                    loop[uvl].uv = (a_ / nx, b_ / ny)
        for v in list(bm.verts):
            if not v.link_faces:
                bm.verts.remove(v)
        return bm

    front = L.obj_from_bm('chip_front', build(True), smooth=True, sharp_deg=32, mats=[fm])
    back = L.obj_from_bm('chip_back', build(False), smooth=True, sharp_deg=32, mats=[bm_])
    L.add_subsurf(front, 1)
    L.parent(back, front)
    return front, back


@L.frame('chip_bag')
def f_chip_bag(scene):
    front, back = make_chip_bag()
    front.rotation_euler.z = math.radians(-18)
    return dict(objs=[front, back], lens=35, shot=dict(elev=44, azim=8, fill=0.72, fstop=9))


# =============================================================== greasy napkins
def napkin_mat(stained=True, seed=0.0, emboss=False):
    m, nt, bsdf, out = L.new_mat('napkin')
    co = L.tex_coord(nt, 'Object')
    cos = L.mapping(nt, co, loc=(seed, seed * 0.6, 1.0))
    emb = L.voronoi_tex(nt, co, scale=1300)
    c = L.srgb(0.95, 0.95, 0.93)
    rough = 0.92
    if stained:
        # translucent yellow-grey grease patches
        g = L.ramp(nt, L.noise_tex(nt, cos, scale=13, detail=3, rough=0.6), [(0.43, 0), (0.58, 1)])
        c = L.mix_col(nt, L.math_n(nt, 'MULTIPLY', g, 0.85), c, L.srgb(0.76, 0.60, 0.27))
        # orange pizza/tomato sauce smears
        s_ = L.ramp(nt, L.noise_tex(nt, L.mapping(nt, co, loc=(5 + seed, 2, 3)), scale=19, detail=3, rough=0.65), [(0.56, 0), (0.64, 1)])
        c = L.mix_col(nt, L.math_n(nt, 'MULTIPLY', s_, 0.95), c, L.srgb(0.90, 0.45, 0.03))
        # small brown spots (bbq / coffee)
        d = L.ramp(nt, L.noise_tex(nt, L.mapping(nt, co, loc=(9, 7 + seed, 3)), scale=42, detail=2), [(0.64, 0), (0.70, 1)])
        c = L.mix_col(nt, L.math_n(nt, 'MULTIPLY', d, 0.85), c, L.srgb(0.42, 0.24, 0.08))
        rough = L.mix_val(nt, L.math_n(nt, 'MAXIMUM', g, s_), 0.92, 0.50)
    hgt = L.math_n(nt, 'MULTIPLY', emb, 0.25)
    if emboss:
        uv = L.tex_coord(nt, 'UV')
        sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(uv, sep.inputs[0])
        du = L.math_n(nt, 'MINIMUM', sep.outputs['X'], L.math_n(nt, 'SUBTRACT', 1.0, sep.outputs['X']))
        dv = L.math_n(nt, 'MINIMUM', sep.outputs['Y'], L.math_n(nt, 'SUBTRACT', 1.0, sep.outputs['Y']))
        dmin = L.math_n(nt, 'MINIMUM', du, dv)
        band = L.ramp(nt, dmin, [(0.015, 0), (0.025, 1), (0.105, 1), (0.115, 0)])
        dots = L.ramp(nt, L.voronoi_tex(nt, L.mapping(nt, uv, scale=(46, 46, 1)), scale=1.0), [(0.22, 1), (0.36, 0)])
        line = L.ramp(nt, dmin, [(0.118, 0), (0.123, 1), (0.128, 1), (0.133, 0)])
        hgt = L.math_n(nt, 'ADD', hgt, L.math_n(nt, 'ADD', L.math_n(nt, 'MULTIPLY', dots, band), line))
    L.setp(nt, bsdf, base=c, rough=rough, sss=0.10, sss_radius=(0.004, 0.004, 0.004),
           normal=L.bump(nt, hgt, strength=0.5 if emboss else 0.12, distance=0.0008 if emboss else 0.0003))
    return m


def crumple_ball(name, radius, mat, seed=0.0, squash=0.78, subdiv=5, depth=0.26):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    off = Vector((seed * 5.3, seed * 2.9, seed * 1.1))
    for v in bm.verts:
        p = v.co.normalized()
        lobes = 0.15 * noise.noise(p * 1.7 + off)
        crease = 0.085 * (noise.ridged_multi_fractal(p * 2.7 + off, 1.0, 2.0, 3, 1.0, 2.0) - 1.0)
        fine = 0.030 * noise.ridged_multi_fractal(p * 7.5 + off, 1.0, 2.0, 2, 1.0, 2.0)
        rr = 1.0 + lobes + crease + fine - 0.03
        v.co = Vector((p.x * rr, p.y * rr, p.z * rr * squash)) * radius
    return L.obj_from_bm(name, bm, smooth=True, sharp_deg=27, mats=[mat])


def crumple_sheet(name, size, mat, seed=0.0, amp=0.016, n=70):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    off = Vector((seed * 3.1, seed * 1.7, seed))
    grid = []
    for j in range(n + 1):
        row = []
        for i in range(n + 1):
            x, y = -size / 2 + size * i / n, -size / 2 + size * j / n
            p = Vector((x * 22, y * 22, 0)) + off
            d, _ = noise.voronoi(p)
            facet = d[1] - d[0]
            rdist = math.hypot(x, y) / (size / 2)
            z = 0.0015 + amp * (0.9 - min(facet, 0.9)) * (0.55 + 0.45 * noise.fractal(p * 0.35, 1.0, 2.0, 2)) + 0.010 * rdist ** 2 * (0.5 + noise.noise(p * 0.2))
            sx = x * (0.86 + 0.05 * noise.noise(p * 0.3)) + 0.004 * noise.noise(p * 0.5 + Vector((7, 0, 0)))
            sy = y * (0.86 + 0.05 * noise.noise(p * 0.3 + Vector((3, 3, 0)))) + 0.004 * noise.noise(p * 0.5 + Vector((0, 7, 0)))
            row.append(bm.verts.new((sx, sy, max(z, 0.0012))))
        grid.append(row)
    for j in range(n):
        for i in range(n):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            f.smooth = True
            for loop, (a_, b_) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uvl].uv = (a_ / n, b_ / n)
    ob = L.obj_from_bm(name, bm, smooth=True, sharp_deg=22, mats=[mat])
    L.add_solidify(ob, 0.0006, offset=-1.0)
    return ob


@L.frame('greasy_napkin')
def f_napkin(scene):
    m1 = napkin_mat(True, seed=1.0)
    m2 = napkin_mat(True, seed=4.0, emboss=True)
    m3 = napkin_mat(True, seed=7.0, emboss=True)
    sheet = crumple_sheet('napkin_sheet', 0.180, m2, seed=2.0, amp=0.013)
    sheet.location = (0.026, 0.020, 0)
    sheet.rotation_euler.z = math.radians(25)
    wad = crumple_ball('napkin_wad', 0.046, m1, seed=1.0)
    wad.location = (-0.042, -0.030, 0.033)
    flap = crumple_sheet('napkin_flap', 0.085, m3, seed=5.0, amp=0.010, n=40)
    flap.location = (-0.070, -0.052, 0.030)
    flap.rotation_euler = (math.radians(38), math.radians(-22), math.radians(70))
    wad2 = crumple_ball('napkin_wad2', 0.030, m1, seed=6.0, squash=0.8)
    wad2.location = (0.064, -0.054, 0.022)
    flap2 = crumple_sheet('napkin_flap2', 0.060, m3, seed=8.0, amp=0.008, n=32)
    flap2.location = (0.088, -0.050, 0.020)
    flap2.rotation_euler = (math.radians(-30), math.radians(25), math.radians(10))
    return dict(objs=[sheet, wad, wad2, flap, flap2], lens=35, shot=dict(elev=38, azim=10, fill=0.74, fstop=9))
