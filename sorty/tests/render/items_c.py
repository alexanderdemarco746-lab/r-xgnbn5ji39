"""Batch C (extended set): pizza leftovers, opaque bottle, tied bag, shipping box, cutlery,
glass bottle, spray can, smartphone, two items, empty scene."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise
import sortylib as L
import items_a as A
import items_b as B

WHITE = (1, 1, 1, 1)
BLACK = (0.012, 0.012, 0.012, 1)


# =============================================================== pizza leftovers
def torus_segment(name, R, r, a0, a1, mat, nseg=26, nr=12, zscale=0.85, seed=0.0):
    bm = bmesh.new()
    rings = []
    for i in range(nseg + 1):
        a = a0 + (a1 - a0) * i / nseg
        radial = Vector((math.sin(a), math.cos(a), 0))
        c = radial * R
        end = min(i, nseg - i) / 3.0
        k_end = 0.55 + 0.45 * min(1.0, end)
        ring = []
        for k in range(nr):
            t = 2 * math.pi * k / nr
            lump = 1.0 + 0.14 * noise.noise(Vector((a * 9 + seed, t * 1.3, seed)))
            rr = r * k_end * lump
            ring.append(bm.verts.new(c + radial * (rr * math.cos(t)) + Vector((0, 0, rr * zscale * (math.sin(t) + 1.0)))))
        rings.append(ring)
    for i in range(nseg):
        for k in range(nr):
            k2 = (k + 1) % nr
            f = bm.faces.new((rings[i][k], rings[i + 1][k], rings[i + 1][k2], rings[i][k2]))
            f.smooth = True
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return L.obj_from_bm(name, bm, smooth=True, sharp_deg=70, mats=[mat])


def pizza_mats(R):
    cm, nt, bsdf, out = L.new_mat('cheese')
    co = L.tex_coord(nt, 'Object')
    n = L.noise_tex(nt, co, scale=95, detail=4, rough=0.6)
    c = L.ramp(nt, n, [(0.28, L.srgb(0.55, 0.25, 0.06)), (0.46, L.srgb(0.93, 0.62, 0.16)), (0.72, L.srgb(0.99, 0.84, 0.42))])
    ln = nt.nodes.new('ShaderNodeVectorMath')
    ln.operation = 'LENGTH'
    nt.links.new(co, ln.inputs[0])
    sauce = L.ramp(nt, ln.outputs['Value'], [((R - 0.030) / 0.2, 0), ((R - 0.022) / 0.2, 1)])
    # ramp positions are 0..1, so scale the distance by 1/0.2 first
    sc = L.math_n(nt, 'MULTIPLY', ln.outputs['Value'], 1 / 0.2)
    sauce = L.ramp(nt, sc, [((R - 0.030) / 0.2, 0), ((R - 0.022) / 0.2, 1)])
    c = L.mix_col(nt, L.math_n(nt, 'MULTIPLY', sauce, 0.9), c, L.srgb(0.62, 0.10, 0.04))
    L.setp(nt, bsdf, base=c, rough=0.33, normal=L.bump(nt, n, strength=0.5, distance=0.002))
    br, nt, bsdf, out = L.new_mat('crust')
    co = L.tex_coord(nt, 'Object')
    n = L.noise_tex(nt, co, scale=70, detail=4, rough=0.65)
    c = L.ramp(nt, n, [(0.30, L.srgb(0.42, 0.22, 0.07)), (0.52, L.srgb(0.78, 0.52, 0.22)), (0.78, L.srgb(0.92, 0.72, 0.40))])
    L.setp(nt, bsdf, base=c, rough=0.78, normal=L.bump(nt, n, strength=0.6, distance=0.002))
    pm, nt, bsdf, out = L.new_mat('pepperoni')
    co = L.tex_coord(nt, 'Object')
    n = L.noise_tex(nt, co, scale=260, detail=3)
    c = L.mix_col(nt, n, L.srgb(0.42, 0.06, 0.04), L.srgb(0.66, 0.14, 0.07))
    L.setp(nt, bsdf, base=c, rough=0.3)
    return cm, br, pm


def pizza_slice(name, R=0.135, ang=math.radians(38), eaten=0.0, seed=0.0, crust_only=False, mats=None):
    cm, br, pm = mats
    bm = bmesh.new()
    nr, na = 16, 12
    r_in = R - 0.014
    grid = []
    for i in range(nr + 1):
        row = []
        for j in range(na + 1):
            a = -ang / 2 + ang * j / na
            start = (R - 0.034) if crust_only else eaten * R
            rho0 = start * (1 + 0.10 * math.sin(a * 46 + seed)) + 0.004 * abs(math.sin(a * 23 + seed))
            rho = rho0 + (r_in - rho0) * i / nr
            z = 0.0068 + 0.0012 * noise.noise(Vector((rho * 60 + seed, a * 30, seed)))
            row.append(bm.verts.new((rho * math.sin(a), rho * math.cos(a), z)))
        grid.append(row)
    for i in range(nr):
        for j in range(na):
            f = bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
            f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    top = L.obj_from_bm(name, bm, smooth=True, mats=[cm])
    L.add_solidify(top, 0.0066, offset=-1.0)
    crust = torus_segment(name + '_crust', R - 0.006, 0.0088, -ang / 2 - 0.02, ang / 2 + 0.02, br, seed=seed)
    L.parent(crust, top)
    if not crust_only:
        rnd = random.Random(int(seed * 10) + 3)
        for k in range(3):
            rho = R * (0.45 + 0.17 * k) + rnd.uniform(-0.006, 0.006)
            a = rnd.uniform(-ang / 2 + 0.10, ang / 2 - 0.10) * (0.5 + 0.25 * k)
            if rho < eaten * R + 0.02:
                continue
            p = L.lathe(name + f'_pep{k}', [(0.0006, 0.0018), (0.0125, 0.0018), (0.0148, 0.0012), (0.0150, 0.0)], segments=28, mats=[pm], cap_top=True)
            p.location = (rho * math.sin(a), rho * math.cos(a), 0.0070)
            L.parent(p, top)
    return top


@L.frame('pizza_box_open_leftovers')
def f_pizza_leftovers(scene):
    tray, lid = A.make_pizza_box(open_deg=104, greasy=True, seed=6.0)
    A.add_crumbs(tray, seed=9, heavy=False)
    mats = pizza_mats(0.148)
    s1 = pizza_slice('slice_a', R=0.148, eaten=0.26, seed=1.0, mats=mats)
    s1.location = (-0.105, -0.092, 0.0032)
    s1.rotation_euler.z = math.radians(-34)
    L.parent(s1, tray)
    s2 = pizza_slice('slice_b', R=0.148, eaten=0.0, seed=4.0, crust_only=True, mats=mats)
    s2.location = (0.030, 0.098, 0.0032)
    s2.rotation_euler.z = math.radians(200)
    L.parent(s2, tray)
    tray.rotation_euler.z = math.radians(-6)
    return dict(objs=[tray], lens=30, shot=dict(elev=41, azim=20, fill=0.80, fstop=7, shift=(0.0, 0.06)))


# =============================================================== opaque HDPE bottle
def make_opaque_bottle():
    k_oval = 0.62
    a_, b_ = 0.035, 0.035 * k_oval
    W, H = 2 * math.pi * math.sqrt((a_ * a_ + b_ * b_) / 2), 0.100
    TEAL = L.srgb(0.02, 0.50, 0.55)
    body_col = L.srgb(0.95, 0.95, 0.94)
    lb = L.Label('shampoo', W, H, px=2048, bg=body_col)
    lw = W * 0.40
    lb.rect(0, 0, lw, H * 0.82, TEAL)
    lb.rect(0, H * 0.20, lw, 0.0012, WHITE)
    lb.text('SHAMPOO', 0, H * 0.06, 0.0125, WHITE, 'ariblk.ttf', fit_w=lw * 0.86)
    lb.text('Fresh & Clean', 0, -H * 0.07, 0.0068, WHITE, 'segoepr.ttf', fit_w=lw * 0.8)
    lb.text('DAILY CARE', 0, H * 0.29, 0.0052, WHITE, 'arialbd.ttf', spacing=1.4)
    lb.text('400 mL (13.5 FL OZ)', 0, -H * 0.31, 0.0038, WHITE, 'arial.ttf')
    lb.ellipse(0, -H * 0.19, 0.006, 0.008, L.srgb(0.55, 0.85, 0.88))
    img = lb.render()
    body = L.image_mat('hdpe_label', img, rough=0.42)
    plain = L.plastic('hdpe', body_col, rough=0.42, sss=0.08)
    capm = L.plastic('cap_teal', TEAL, rough=0.35)

    def oval(u, z, r):
        k = k_oval if z < 0.125 else min(1.0, k_oval + (1 - k_oval) * (z - 0.125) / 0.025)
        a = 2 * math.pi * (u - 0.5)
        return r / math.sqrt(math.sin(a) ** 2 + (math.cos(a) / k) ** 2)

    P, I = 1, 0
    prof = [(0.0006, 0.004, P), (0.026, 0.003, P), (0.031, 0.0, P), (0.0335, 0.004, P), (0.0348, 0.012, P), (0.0350, 0.020, I),
            (0.0350, 0.070, I), (0.0350, 0.120, P), (0.0335, 0.132, P), (0.0270, 0.146, P), (0.0170, 0.156, P), (0.0135, 0.160, P), (0.0135, 0.166, P)]
    bottle = L.lathe('opaque_bottle', prof, segments=96, mats=[body, plain], cap_bottom=True, radial_fn=oval, sharp_deg=45)
    cap = L.lathe('flip_cap', [(0.0170, 0.1615), (0.0176, 0.1625), (0.0176, 0.1870), (0.0166, 0.1895), (0.0006, 0.1900)],
                  segments=64, mats=[capm], cap_top=True, sharp_deg=40)
    L.parent(cap, bottle)
    seam = L.lathe('cap_seam', [(0.0178, 0.1800), (0.0178, 0.1806)], segments=64, mats=[L.simple_mat('seam', (0.01, 0.12, 0.14, 1), rough=0.5)])
    L.parent(seam, bottle)
    return bottle


@L.frame('opaque_bottle')
def f_opaque(scene):
    b = make_opaque_bottle()
    b.rotation_euler.z = math.radians(6)
    return dict(objs=[b], lens=40, shot=dict(elev=15, azim=10, fill=0.70, fstop=11))


# =============================================================== tied plastic bag
def make_tied_bag(seed=3.0):
    m, nt, bsdf, out = L.new_mat('bag_film')
    co = L.tex_coord(nt, 'Object')
    wr = L.noise_tex(nt, L.mapping(nt, co, scale=(1, 1, 0.28)), scale=75, detail=3, rough=0.6, distortion=0.6)
    fine = L.noise_tex(nt, co, scale=320, detail=2)
    h = L.math_n(nt, 'ADD', wr, L.math_n(nt, 'MULTIPLY', fine, 0.3))
    L.setp(nt, bsdf, base=L.srgb(0.92, 0.92, 0.94), rough=L.mix_val(nt, wr, 0.16, 0.30), sss=0.10, sss_radius=(0.01, 0.01, 0.01),
           spec=0.6, coat=0.25, coat_rough=0.15, normal=L.bump(nt, h, strength=0.65, distance=0.003))
    R = 0.098
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=6, radius=1.0)
    off = Vector((seed * 2.1, seed * 1.3, seed))
    z_floor = -0.60
    for v in bm.verts:
        p = v.co.normalized()
        th = math.atan2(p.y, p.x)
        lump = 0.20 * noise.noise(p * 1.3 + off) + 0.07 * noise.noise(p * 2.6 + off)
        up = max(0.0, p.z)
        pleat = 0.065 * math.sin(13 * th + 3 * noise.noise(p * 2 + off)) * smooth01((p.z + 0.1) / 1.0) ** 1.5
        wrinkle = 0.030 * noise.ridged_multi_fractal(Vector((p.x * 7, p.y * 7, p.z * 1.4)) + off, 1.0, 2.0, 3, 1.0, 2.0)
        r = 1.0 + lump + pleat + wrinkle - 0.03
        q = Vector((p.x * r, p.y * r, p.z * r * 0.86))
        # gather into a neck near the top
        t = smooth01((p.z - 0.55) / 0.45)
        neck = 0.115 + 0.03 * math.sin(9 * th)
        q.x = q.x * (1 - t) + p.x * neck * t / max(math.hypot(p.x, p.y), 0.05) * (1.0 if t < 1 else 1.0)
        q.y = q.y * (1 - t) + p.y * neck * t / max(math.hypot(p.x, p.y), 0.05)
        q.z = q.z + 0.30 * t
        if q.z < z_floor:
            q.z = z_floor
        v.co = Vector((q.x * R, q.y * R, (q.z - z_floor) * R))
    bag = L.obj_from_bm('tied_bag', bm, smooth=True, sharp_deg=60, mats=[m])
    ztop = (0.86 + 0.30 - z_floor) * R
    knot = L.blob('knot', 0.019, subdiv=4, amp=0.35, freq=2.2, seed=seed, squash=(1.25, 1.0, 0.72), mat=m, ridged=True)
    knot.location = (0, 0, ztop - 0.004)
    L.parent(knot, bag)

    def ear(name, yaw, tilt, length=0.075, width=0.050, sd=1.0):
        bm = bmesh.new()
        nu, nv = 14, 22
        grid = []
        for j in range(nv + 1):
            t = j / nv
            w = width * (0.22 + 0.78 * math.sin(math.pi * min(t * 1.15, 1.0)) ** 0.7) * (1 - 0.35 * t)
            row = []
            for i in range(nu + 1):
                s = i / nu - 0.5
                y = 0.010 * noise.fractal(Vector((s * 6 + sd, t * 5, sd)), 1.0, 2.0, 3) + 0.012 * math.sin(s * 9 + sd) * t
                row.append(bm.verts.new((s * w, y, t * length)))
            grid.append(row)
        for j in range(nv):
            for i in range(nu):
                f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
                f.smooth = True
        e = L.obj_from_bm(name, bm, smooth=True, sharp_deg=40, mats=[m])
        L.add_solidify(e, 0.0005, offset=0.0)
        e.matrix_world = Matrix.Translation((0, 0, ztop + 0.002)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'Y')
        L.parent_keep(e, bag)
        return e

    ear('ear_a', math.radians(20), math.radians(48), sd=1.0)
    ear('ear_b', math.radians(200), math.radians(40), length=0.068, sd=2.0)
    return bag


def smooth01(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


@L.frame('tied_bag')
def f_tied_bag(scene):
    bag = make_tied_bag()
    bag.rotation_euler.z = math.radians(15)
    return dict(objs=[bag], lens=35, shot=dict(elev=22, azim=10, fill=0.72, fstop=9))


# =============================================================== shipping box
def make_shipping_box():
    W, D, H, t = 0.26, 0.20, 0.14, 0.004
    col = L.srgb(0.71, 0.55, 0.37)
    cb = L.cardboard('ship_cb', color=col, seed=3.0)
    edge = L.cardboard_edge('ship_edge', color=col)
    bm = bmesh.new()
    L.add_box(bm, (W, D, t), (0, 0, t / 2))
    L.add_box(bm, (W, t, H), (0, -D / 2 + t / 2, H / 2))
    L.add_box(bm, (W, t, H), (0, D / 2 - t / 2, H / 2))
    L.add_box(bm, (t, D - 2 * t, H), (-W / 2 + t / 2, 0, H / 2))
    L.add_box(bm, (t, D - 2 * t, H), (W / 2 - t / 2, 0, H / 2))
    box = L.obj_from_bm('ship_box', bm, mats=[cb, edge])
    L.add_bevel(box, 0.0008)
    fl = D / 2 - 0.002

    def flap(name, length, hinge, yaw_deg, open_deg):
        bm = bmesh.new()
        L.add_box(bm, (length, t, fl), (0, 0, fl / 2))
        for f in bm.faces:
            if abs(f.normal.y) < 0.5:
                f.material_index = 1
        fo = L.obj_from_bm(name, bm, mats=[cb, edge])
        L.add_bevel(fo, 0.0008)
        fo.matrix_world = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(yaw_deg), 4, 'Z') @ Matrix.Rotation(math.radians(open_deg), 4, 'X')
        L.parent_keep(fo, box)
        return fo

    flap('flap_front', W - 0.002, (0, -D / 2, H + 0.0005), 0, 156)
    flap('flap_back', W - 0.002, (0, D / 2, H + 0.0005), 180, 118)
    flap('flap_right', D - 0.002, (W / 2, 0, H + 0.0005), 90, 38)
    flap('flap_left', D - 0.002, (-W / 2, 0, H + 0.0005), -90, 128)
    # packing tape tails on the short walls, shipping label on the right wall
    tape = L.simple_mat('tape', L.srgb(0.80, 0.66, 0.42), rough=0.12, coat=0.5)
    for sx in (-1, 1):
        tp = L.box_obj('tape_tail', (0.0005, 0.048, 0.062), loc=(sx * (W / 2 + 0.0003), 0, H - 0.031), mat=tape)
        L.parent(tp, box)
    lw, lh = 0.105, 0.075
    lb = L.Label('ship_label', lw, lh, px=1536, bg=WHITE)
    lb.rect(0, lh / 2 - 0.0075, lw, 0.015, BLACK)
    lb.text('PRIORITY  SHIPPING', 0, lh / 2 - 0.0075, 0.0068, WHITE, 'arialbd.ttf', spacing=1.2)
    lb.text('SHIP TO:', -lw / 2 + 0.014, 0.014, 0.0046, BLACK, 'arialbd.ttf')
    for k in range(3):
        lb.rect(-0.006, 0.006 - k * 0.0068, 0.062, 0.0024, L.srgb(0.35, 0.35, 0.35))
    lb.rect(0, -0.0145, lw, 0.0010, BLACK)
    lb.barcode(-0.010, -0.0265, 0.070, 0.015, n=46, seed=8)
    lb.text('1Z 999 AA1 01 2345 6784', -0.010, -0.0325, 0.0030, BLACK, 'consolab.ttf')
    lb.text('2 LBS', lw / 2 - 0.012, 0.012, 0.0050, BLACK, 'arialbd.ttf')
    lmat = L.image_mat('ship_label', lb.render(), rough=0.55)
    lab = L.plane_uv('ship_label', lw, lh, mat=lmat)
    lab.matrix_world = Matrix.Translation((W / 2 + 0.0004, -0.020, 0.060)) @ Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Rotation(math.radians(90), 4, 'X')
    L.parent_keep(lab, box)
    ink = L.simple_mat('box_ink', L.srgb(0.10, 0.08, 0.06), rough=0.9)
    arrows = L.text_obj('box_print', '↑↑  THIS SIDE UP', 0.017, ink, 'arialbd.ttf')
    arrows.matrix_world = Matrix.Translation((0.0, -D / 2 - 0.0004, 0.060)) @ Matrix.Rotation(math.radians(90), 4, 'X')
    L.parent_keep(arrows, box)
    return box


@L.frame('cardboard_box_clean')
def f_ship_box(scene):
    box = make_shipping_box()
    box.rotation_euler.z = math.radians(-33)
    return dict(objs=[box], lens=30, shot=dict(elev=40, azim=6, fill=0.80, fstop=7))


# =============================================================== plastic fork & knife
def strip(bm, sections, zfun, cols=5):
    """sections: [(y, x_left, x_right)]; builds a quad strip (cols columns) in the XY plane."""
    rows = []
    for (y, xl, xr) in sections:
        rows.append([bm.verts.new((xl + (xr - xl) * i / (cols - 1), y, zfun(y, xl + (xr - xl) * i / (cols - 1)))) for i in range(cols)])
    for a, b in zip(rows[:-1], rows[1:]):
        for i in range(cols - 1):
            f = bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
            f.smooth = True


def make_cutlery():
    pl = L.plastic('ps_white', L.srgb(0.96, 0.96, 0.95), rough=0.22, sss=0.12)
    LEN = 0.165
    y0 = -LEN / 2

    def hw(y):
        u = (y - y0) / LEN
        if u < 0.04:
            return 0.0034 + 0.0030 * (u / 0.04) ** 0.5
        if u < 0.47:
            return 0.0064 - 0.0024 * (u - 0.04) / 0.43
        if u < 0.72:
            return 0.0040 + 0.0084 * smooth01((u - 0.47) / 0.25)
        return 0.0124

    def zf(y, x=0.0):
        u = (y - y0) / LEN
        return 0.0018 + 0.0040 * math.sin(math.pi * min(u / 0.55, 1.0)) + 0.011 * max(0.0, (u - 0.55) / 0.45) ** 2 + 9.0 * x * x

    bm = bmesh.new()
    ys = [y0 + LEN * k / 60 for k in range(0, 48)]
    strip(bm, [(y, -hw(y), hw(y)) for y in ys], zf)
    y_root = ys[-1]
    for c in (-0.0093, -0.0031, 0.0031, 0.0093):
        secs = []
        for k in range(11):
            y = y_root - 0.002 + (LEN / 2 - y_root + 0.002) * k / 10
            w = 0.0023 - 0.0012 * (k / 10) ** 2
            secs.append((y, c - w, c + w))
        strip(bm, secs, zf, cols=3)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    fork = L.obj_from_bm('fork', bm, smooth=True, mats=[pl])
    L.add_solidify(fork, 0.0018, offset=-1.0)
    L.add_subsurf(fork, 1)

    def zk(y, x=0.0):
        u = (y - y0) / LEN
        return 0.0018 + 0.0036 * math.sin(math.pi * min(u / 0.55, 1.0)) + 0.0025 * max(0.0, (u - 0.5) / 0.5)

    bm = bmesh.new()
    secs = []
    for k in range(0, 61):
        y = y0 + LEN * k / 60
        u = k / 60
        if u < 0.47:
            secs.append((y, -hw(y), hw(y)))
        else:
            ub = (u - 0.47) / 0.53
            xr = 0.0046 * (1 - ub ** 6)
            xl = -(0.0040 + 0.0062 * math.sin(math.pi * ub ** 0.8) * (1 - ub ** 4))
            if 0.2 < ub < 0.92:
                xl -= 0.0007 * abs(((k * 1.7) % 2) - 1)
            if ub > 0.97:
                xl = min(xl, xr - 0.0005)
            secs.append((y, min(xl, xr - 0.0006), xr))
    strip(bm, secs, zk)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    knife = L.obj_from_bm('knife', bm, smooth=True, mats=[pl])
    L.add_solidify(knife, 0.0017, offset=-1.0)
    L.add_subsurf(knife, 1)
    return fork, knife


@L.frame('plastic_fork')
def f_cutlery(scene):
    fork, knife = make_cutlery()
    fork.location = (-0.022, 0.0, 0.0)
    fork.rotation_euler.z = math.radians(-58)
    knife.location = (0.020, -0.012, 0.0)
    knife.rotation_euler.z = math.radians(-72)
    return dict(objs=[fork, knife], lens=40, shot=dict(elev=46, azim=6, fill=0.74, fstop=11))


# =============================================================== glass bottle (empty, no cap)
def make_glass_bottle():
    glass = L.clear_mat('green_glass', tint=(0.36, 0.66, 0.30, 1), rough=0.015, ior=1.52, shadow=0.55)
    prof = [(0.0006, 0.0065), (0.018, 0.0050), (0.0255, 0.0012), (0.0285, 0.0), (0.0305, 0.0030), (0.0310, 0.0100), (0.0310, 0.1250),
            (0.0296, 0.1400), (0.0242, 0.1580), (0.0168, 0.1780), (0.0139, 0.1950), (0.0132, 0.2250), (0.0149, 0.2272),
            (0.0152, 0.2312), (0.0140, 0.2330), (0.0133, 0.2365)]
    bottle = L.lathe('glass_bottle', prof, segments=96, mats=[glass], cap_bottom=True, sharp_deg=60)
    L.add_solidify(bottle, 0.0030, offset=-1.0)
    W, H = 2 * math.pi * 0.0312, 0.064
    cream, dg = L.srgb(0.94, 0.90, 0.78), L.srgb(0.05, 0.28, 0.12)
    lb = L.Label('glass_label', W, H, px=2048, bg=cream)
    lb.rect(0, H / 2 - 0.004, W, 0.0025, dg)
    lb.rect(0, -H / 2 + 0.004, W, 0.0025, dg)
    lb.ellipse(0, 0.004, 0.036, 0.022, dg)
    lb.ellipse(0, 0.004, 0.0345, 0.0205, cream)
    lb.text('SPARKLING', 0, 0.010, 0.0092, dg, 'georgiab.ttf', fit_w=0.056)
    lb.text('MINERAL WATER', 0, -0.002, 0.0050, dg, 'arialbd.ttf', spacing=1.2)
    lb.text('330 mL', 0, -0.021, 0.0042, dg, 'arialbd.ttf')
    lb.barcode(W * 0.38, 0.0, 0.026, 0.016, seed=5)
    lmat = L.image_mat('paper_label', lb.render(), rough=0.7, back_color=(0.75, 0.72, 0.62, 1), bump_noise=0.1)
    band = L.lathe('glass_label', [(0.03125, 0.046), (0.03125, 0.110)], segments=96, mats=[lmat])
    L.parent(band, bottle)
    return bottle


@L.frame('glass_bottle_empty')
def f_glass(scene):
    b = make_glass_bottle()
    b.rotation_euler.z = math.radians(8)
    return dict(objs=[b], lens=40, shot=dict(elev=15, azim=10, fill=0.74, fstop=11))


# =============================================================== aerosol spray can
def make_spray_can():
    Rb = 0.0325
    W, H = 2 * math.pi * Rb, 0.144
    ORANGE, DARK, REDH = L.srgb(0.96, 0.45, 0.05), L.srgb(0.035, 0.035, 0.04), L.srgb(0.85, 0.05, 0.05)
    lb = L.Label('spray_label', W, H, px=2048, bg=DARK)
    lb.rect(0, H / 2 - 0.009, W, 0.018, ORANGE)
    lb.rect(0, -H / 2 + 0.006, W, 0.012, ORANGE)
    lb.text('SPRAY', 0, 0.044, 0.021, WHITE, 'impact.ttf', fit_w=0.070, spacing=1.05)
    lb.text('PAINT', 0, 0.022, 0.021, ORANGE, 'impact.ttf', fit_w=0.070, spacing=1.05)
    lb.text('GLOSS BLACK', 0, 0.0045, 0.0070, WHITE, 'arialbd.ttf', spacing=1.2)
    lb.text('FAST DRY  •  INDOOR / OUTDOOR', 0, -0.006, 0.0034, WHITE, 'arial.ttf')
    # GHS flame diamond
    dx, dy, sz = -0.019, -0.034, 0.0155
    lb.poly([(dx, dy - sz), (dx + sz, dy), (dx, dy + sz), (dx - sz, dy)], REDH)
    s2 = sz * 0.80
    lb.poly([(dx, dy - s2), (dx + s2, dy), (dx, dy + s2), (dx - s2, dy)], WHITE)
    fl = [(0, -0.0080), (0.0042, -0.0062), (0.0058, -0.0022), (0.0046, 0.0022), (0.0030, 0.0002), (0.0027, 0.0050), (0.0004, 0.0088),
          (-0.0006, 0.0046), (-0.0026, 0.0020), (-0.0031, 0.0046), (-0.0054, 0.0002), (-0.0054, -0.0034), (-0.0034, -0.0066)]
    lb.poly([(dx + x * 0.92, dy + y * 0.92 - 0.0004) for x, y in fl], BLACK)
    lb.text('DANGER', 0.019, -0.026, 0.0082, REDH, 'ariblk.ttf', fit_w=0.042)
    lb.text('EXTREMELY FLAMMABLE', 0.019, -0.0345, 0.0036, WHITE, 'arialbd.ttf', fit_w=0.044)
    lb.text('CONTENTS UNDER PRESSURE', 0.019, -0.0405, 0.0030, WHITE, 'arialbd.ttf', fit_w=0.044)
    lb.text('NET WT 12 OZ (340 g)', 0, -H / 2 + 0.006, 0.0040, DARK, 'arialbd.ttf')
    lb.barcode(W * 0.40, -0.02, 0.028, 0.017, seed=11)
    lb.text('Directions: shake well.', -W * 0.40, 0.030, 0.0030, WHITE, 'arial.ttf')
    for k in range(7):
        lb.rect(-W * 0.40, 0.022 - k * 0.0046, 0.034, 0.0008, L.srgb(0.6, 0.6, 0.6))
    body = L.image_mat('spray_paint', lb.render(), rough=0.28, metallic=0.45, coat=0.3)
    alu = L.metal('tin', rough=0.24)
    Bm, A_ = 0, 1
    prof = [(0.0006, 0.0060, A_), (0.020, 0.0042, A_), (0.0292, 0.0, A_), (0.0316, 0.0018, A_), (0.0325, 0.0060, Bm), (0.0325, 0.1500, A_),
            (0.0331, 0.1508, A_), (0.0331, 0.1526, A_), (0.0322, 0.1540, A_), (0.0285, 0.1630, A_), (0.0210, 0.1708, A_), (0.0142, 0.1745, A_),
            (0.0142, 0.1770, A_), (0.0130, 0.1776, A_), (0.0128, 0.1750, A_), (0.0050, 0.1748, A_), (0.0040, 0.1752, A_), (0.0040, 0.1800, A_)]
    can = L.lathe('spray_can', prof, segments=96, mats=[body, alu], cap_bottom=True, cap_top=True, sharp_deg=55)
    wp = L.plastic('actuator', L.srgb(0.95, 0.95, 0.94), rough=0.3)
    act = L.lathe('actuator', [(0.0072, 0.1772), (0.0084, 0.1786), (0.0084, 0.1915), (0.0074, 0.1942), (0.0006, 0.1946)], segments=48, mats=[wp], cap_top=True, sharp_deg=40)
    L.parent(act, can)
    hole = L.disc('orifice', 0.0015, mat=L.simple_mat('hole', (0.005, 0.005, 0.005, 1), rough=0.6), segments=24)
    hole.rotation_euler = (math.radians(90), 0, 0)
    hole.location = (0, -0.00845, 0.1880)
    L.parent(hole, can)
    return can


@L.frame('spray_can')
def f_spray(scene):
    can = make_spray_can()
    can.rotation_euler.z = math.radians(10)
    return dict(objs=[can], lens=40, shot=dict(elev=15, azim=12, fill=0.72, fstop=11))


# =============================================================== smartphone
def make_phone():
    w, h, t, r = 0.0715, 0.1475, 0.0080, 0.0105
    frame = L.simple_mat('phone_frame', (0.045, 0.047, 0.052, 1), rough=0.32, metallic=0.9)
    gm, nt, bsdf, out = L.new_mat('phone_glass')
    co = L.tex_coord(nt, 'Object')
    smudge = L.noise_tex(nt, co, scale=45, detail=4, rough=0.7, distortion=0.8)
    L.setp(nt, bsdf, base=(0.006, 0.006, 0.008, 1), rough=L.mix_val(nt, L.ramp(nt, smudge, [(0.45, 0), (0.7, 1)]), 0.035, 0.16), coat=0.6, coat_rough=0.03)
    rings = [(w - 0.0024, h - 0.0024, r - 0.0012, 0.0), (w, h, r, 0.0014), (w, h, r, t - 0.0014), (w - 0.0020, h - 0.0020, r - 0.0010, t)]
    bm = bmesh.new()
    vr = [[bm.verts.new((x, y, z)) for x, y in B.rr_ring(rw, rh, rr, n=10)] for (rw, rh, rr, z) in rings]
    n = len(vr[0])
    for i in range(len(vr) - 1):
        for j in range(n):
            j2 = (j + 1) % n
            f = bm.faces.new((vr[i][j], vr[i][j2], vr[i + 1][j2], vr[i + 1][j]))
            f.smooth = True
    bm.faces.new(list(reversed(vr[0])))
    top = bm.faces.new(vr[-1])
    top.material_index = 1
    phone = L.obj_from_bm('phone', bm, smooth=True, sharp_deg=50, mats=[frame, gm])
    disp = L.simple_mat('display_off', (0.011, 0.012, 0.015, 1), rough=0.05, coat=0.8)
    bm = bmesh.new()
    bm.faces.new([bm.verts.new((x, y, 0)) for x, y in B.rr_ring(w - 0.0062, h - 0.0062, r - 0.0030, n=10)])
    d = L.obj_from_bm('display', bm, mats=[disp])
    d.location = (0, 0, t + 0.00004)
    L.parent(d, phone)
    cam = L.disc('front_cam', 0.0019, mat=L.simple_mat('lens', (0.002, 0.003, 0.010, 1), rough=0.02, coat=1.0), segments=24)
    cam.location = (0, h / 2 - 0.0088, t + 0.00009)
    L.parent(cam, phone)
    ringm = L.disc('cam_ring', 0.0026, mat=L.simple_mat('lens_ring', (0.03, 0.03, 0.035, 1), rough=0.2), segments=24)
    ringm.location = (0, h / 2 - 0.0088, t + 0.00006)
    L.parent(ringm, phone)
    for (y, ln) in ((0.022, 0.016), (0.050, 0.010), (0.064, 0.010)):
        b_ = L.box_obj('button', (0.0016, ln, 0.0030), loc=(w / 2 + 0.0002, y, t / 2), mat=frame, bevel=0.0005)
        L.parent(b_, phone)
    sp = L.box_obj('earpiece', (0.012, 0.0009, 0.0002), loc=(0, h / 2 - 0.0022, t + 0.00008), mat=L.simple_mat('slit', (0.002, 0.002, 0.002, 1), rough=0.8))
    L.parent(sp, phone)
    return phone


@L.frame('smartphone')
def f_phone(scene):
    ph = make_phone()
    ph.rotation_euler.z = math.radians(24)
    return dict(objs=[ph], lens=40, shot=dict(elev=40, azim=8, fill=0.70, fstop=11))


# =============================================================== combos / empty
@L.frame('two_items_peel_bottle')
def f_two(scene):
    b = A.make_bottle('water')
    b.location = (-0.105, 0.03, 0)
    b.rotation_euler.z = math.radians(15)
    root, objs = B.make_banana_peel()
    root.location = (0.075, -0.01, 0)
    root.rotation_euler.z = math.radians(40)
    return dict(objs=[b] + objs, lens=35, shot=dict(elev=30, azim=6, fill=0.84, fstop=11))


@L.frame('empty_scene')
def f_empty(scene):
    e = bpy.data.objects.new('nothing', None)
    L.link(e)
    return dict(objs=[e], lens=35, shot=dict(elev=24, azim=8, dist=0.48, target=(0, 0, 0.05), fstop=8))
