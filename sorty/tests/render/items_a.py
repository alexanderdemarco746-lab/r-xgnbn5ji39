"""Batch A: soda can, PET bottles, pizza boxes."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
import sortylib as L

WHITE = (1, 1, 1, 1)
BLACK = (0.012, 0.012, 0.012, 1)
RED = L.srgb(0.80, 0.06, 0.08)
INK_RED = L.srgb(0.63, 0.05, 0.04)


# =============================================================== soda can
def torus(name, R, r, mat, seg=32, rseg=12):
    prof = [(R + r * math.cos(2 * math.pi * k / rseg), r * math.sin(2 * math.pi * k / rseg)) for k in range(rseg + 1)]
    return L.lathe(name, prof, segments=seg, mats=[mat], sharp_deg=80)


def make_soda_can(face_deg=0.0):
    Rb, Hc = 0.0331, 0.1222
    W, H = 2 * math.pi * Rb, 0.107
    lb = L.Label('cola_can', W, H, px=2048, bg=RED)
    lb.wave_band(-0.0165, 0.0045, 0.0085, WHITE, periods=1.0, phase=0.6)
    lb.wave_band(-0.0255, 0.0045, 0.0022, L.srgb(0.85, 0.85, 0.87), periods=1.0, phase=0.6)
    lb.text('COLA', 0.0, 0.016, 0.034, WHITE, 'COOPBL.TTF', shear=0.22, fit_w=0.064)
    lb.text('CLASSIC', 0.0, -0.035, 0.0062, WHITE, 'arialbd.ttf', spacing=1.7)
    lb.text('355 mL (12 FL OZ)', 0.0, -0.0455, 0.0036, WHITE, 'arial.ttf')
    # back panel: nutrition box + barcode
    bx = W * 0.40
    lb.rect(bx, 0.004, 0.036, 0.062, WHITE)
    lb.rect(bx, 0.004, 0.0345, 0.0605, RED)
    lb.text('Nutrition Facts', bx, 0.028, 0.0042, WHITE, 'arialbd.ttf', fit_w=0.032)
    for k in range(9):
        lb.rect(bx, 0.021 - k * 0.0052, 0.031, 0.0006, WHITE)
        lb.text(['Calories 140', 'Total Fat 0g', 'Sodium 45mg', 'Total Carb 39g', 'Sugars 39g', 'Protein 0g',
                 'Caffeine 34mg', 'Not a source of', 'other nutrients'][k], bx, 0.0184 - k * 0.0052, 0.0028, WHITE, 'arial.ttf')
    lb.barcode(-W * 0.40, -0.012, 0.030, 0.017)
    lb.text('PLEASE RECYCLE', -W * 0.40, 0.012, 0.0034, WHITE, 'arialbd.ttf')
    img = lb.render()
    body = L.image_mat('can_paint', img, rough=0.30, metallic=0.60, coat=0.25)
    alu = L.metal('aluminum', rough=0.30)
    B, A = 0, 1
    prof = [(0.0006, 0.0042, A), (0.012, 0.0036, A), (0.019, 0.0022, A), (0.0235, 0.0, A), (0.0262, 0.0010, A),
            (0.0296, 0.0056, B), (0.0322, 0.0105, B), (0.0331, 0.0160, B), (0.0331, 0.1000, B), (0.0327, 0.1050, B),
            (0.0312, 0.1100, B), (0.0290, 0.1150, B), (0.0273, 0.1182, A), (0.0276, 0.1190, A), (0.0283, 0.1200, A),
            (0.0284, 0.1212, A), (0.0279, 0.1221, A), (0.0268, 0.1222, A), (0.0260, 0.1214, A), (0.0256, 0.1190, A),
            (0.0251, 0.1166, A), (0.0240, 0.1163, A), (0.0225, 0.1170, A), (0.0006, 0.1172, A)]
    can = L.lathe('soda_can', prof, segments=96, mats=[body, alu], cap_bottom=True, cap_top=True, sharp_deg=60)
    # stay-on tab
    ring = torus('tab_ring', 0.0052, 0.0011, alu)
    ring.scale = (0.85, 1.15, 0.45)
    ring.location = (0, 0.0075, 0.1184)
    L.parent(ring, can)
    bm = bmesh.new()
    L.add_box(bm, (0.0105, 0.0125, 0.0009))
    nose = L.obj_from_bm('tab_nose', bm, mats=[alu])
    L.add_bevel(nose, 0.0035, segments=4, angle=100)
    nose.location = (0, -0.0035, 0.1183)
    L.parent(nose, can)
    rivet = L.blob('rivet', 0.0021, subdiv=2, amp=0.0, squash=(1, 1, 0.45), mat=alu)
    rivet.location = (0, 0.0005, 0.1180)
    L.parent(rivet, can)
    can.rotation_euler.z = math.radians(face_deg)
    return can


@L.frame('soda_can')
def f_soda_can(scene):
    can = make_soda_can(face_deg=10)
    return dict(objs=[can], lens=42, shot=dict(elev=19, azim=14, fill=0.60, fstop=11))


@L.frame('blurry_dark')
def f_blurry_dark(scene):
    can = make_soda_can(face_deg=-40)
    can.location = (0.012, 0, 0.03)
    can.rotation_euler.y = math.radians(18)
    return dict(objs=[can], lens=42, light=0.10, post='blurdark', shot=dict(elev=14, azim=5, fill=0.55, fstop=2.0))


# =============================================================== PET bottle
def bottle_radius(z, ribs, lab):
    """Outer radius of the bottle body for 0.013 <= z <= 0.150."""
    r = 0.0325
    if ribs:
        for z0, z1, pitch in ((0.018, 0.0755, 0.0115), (0.1355, 0.147, 0.0115)):
            if z0 <= z <= z1:
                r -= 0.0012 * (0.5 - 0.5 * math.cos(2 * math.pi * (z - z0) / pitch))
    else:
        # smooth soda bottle: gentle waist
        r -= 0.0022 * math.exp(-((z - 0.062) / 0.022) ** 2)
    l0, l1 = lab
    edge = 0.0018
    if l0 - edge < z < l1 + edge:
        k = min(1.0, (z - (l0 - edge)) / edge, ((l1 + edge) - z) / edge)
        r = r * (1 - k) + 0.0318 * k
    return r


def bottle_profile(ribs, lab):
    P = [(0.0006, 0.0058), (0.010, 0.0042), (0.019, 0.0016), (0.0235, 0.0004), (0.0278, 0.0012), (0.0308, 0.0050), (0.0322, 0.0095)]
    z = 0.013
    while z <= 0.1501:
        P.append((bottle_radius(z, ribs, lab), z))
        z += 0.0015
    for k in range(1, 25):                       # shoulder
        t = k / 24
        zz = 0.150 + 0.036 * t
        rr = 0.0127 + (0.0325 - 0.0127) * (math.cos(t * math.pi / 2) ** 0.85)
        P.append((rr, zz))
    P += [(0.0127, 0.1868), (0.0164, 0.1876), (0.0166, 0.1886), (0.0131, 0.1893), (0.0134, 0.2040)]
    return P


def make_bottle(kind='water', liquid_level=None, capped=True):
    lab = (0.084, 0.130) if kind == 'water' else (0.112, 0.150)
    ribs = (kind == 'water')
    P = bottle_profile(ribs, lab)
    pet = L.clear_mat('pet', tint=(0.985, 0.995, 1.0, 1) if kind == 'water' else (1, 1, 1, 1), rough=0.025, ior=1.5, shadow=0.88)
    pet_in = L.clear_mat('pet_inner', rough=0.02, ior=1.5, shadow=0.88, reflect=False) if liquid_level else pet
    bottle = L.lathe('bottle', P, segments=96, mats=[pet, pet_in], cap_bottom=True, sharp_deg=60)
    L.add_solidify(bottle, 0.00045, offset=-1.0, mat_offset=1)
    W, H = 2 * math.pi * 0.0320, (lab[1] - lab[0]) - 0.002
    if kind == 'water':
        BLUE = L.srgb(0.05, 0.36, 0.78)
        lb = L.Label('water_label', W, H, px=2048, bg=WHITE)
        lb.rect(0, H * 0.36, W, H * 0.28, BLUE)
        lb.rect(0, -H * 0.42, W, H * 0.16, BLUE)
        lb.wave_band(H * 0.20, 0.0030, 0.0030, L.srgb(0.35, 0.70, 0.95), periods=3)
        lb.text('PURE', 0, H * 0.36, 0.0095, WHITE, 'arialbd.ttf', spacing=1.5)
        lb.text('WATER', 0, 0.001, 0.0175, BLUE, 'ariblk.ttf', fit_w=0.056)
        lb.text('NATURAL SPRING WATER', 0, -H * 0.24, 0.0034, BLUE, 'arialbd.ttf')
        lb.text('500 mL (16.9 FL OZ)', 0, -H * 0.42, 0.0036, WHITE, 'arialbd.ttf')
        lb.barcode(W * 0.38, -0.002, 0.026, 0.016)
        lb.text('PLEASE RECYCLE', -W * 0.38, 0.004, 0.0034, BLUE, 'arialbd.ttf')
        lb.text('PET 1', -W * 0.38, -0.006, 0.0034, BLUE, 'arialbd.ttf')
        cap_col = L.srgb(0.10, 0.42, 0.85)
    else:
        lb = L.Label('cola_label', W, H, px=2048, bg=RED)
        lb.wave_band(-H * 0.30, 0.0022, 0.0040, WHITE, periods=3)
        lb.text('COLA', 0, H * 0.10, 0.021, WHITE, 'COOPBL.TTF', shear=0.22, fit_w=0.058)
        lb.text('CLASSIC  500 mL', 0, -H * 0.40, 0.0034, WHITE, 'arialbd.ttf')
        lb.barcode(W * 0.38, 0.0, 0.026, 0.015)
        lb.text('Nutrition Facts', -W * 0.38, 0.008, 0.0036, WHITE, 'arialbd.ttf')
        for k in range(5):
            lb.rect(-W * 0.38, 0.003 - k * 0.0038, 0.03, 0.0005, WHITE)
        cap_col = L.srgb(0.78, 0.05, 0.06)
    img = lb.render()
    lmat = L.image_mat('label', img, rough=0.38, back_color=(0.86, 0.86, 0.88, 1))
    band = L.lathe('label_band', [(0.03205, lab[0] + 0.001), (0.03205, lab[1] - 0.001)], segments=96, mats=[lmat])
    L.parent(band, bottle)
    capm = L.plastic('cap', cap_col, rough=0.42)

    def knurl(u, z, r):
        if 0.1915 < z < 0.2045:
            return r + 0.00030 * (0.5 + 0.5 * math.sin(2 * math.pi * u * 60))
        return r

    if capped:
        cap = L.lathe('cap', [(0.0149, 0.1898), (0.0153, 0.1903), (0.0153, 0.1912), (0.0151, 0.1915), (0.0153, 0.1918),
                              (0.0153, 0.2050), (0.0147, 0.2064), (0.0006, 0.2066)],
                      segments=240, mats=[capm], cap_top=True, radial_fn=knurl, sharp_deg=40)
        L.parent(cap, bottle)
    objs = [bottle]
    if liquid_level:
        cola = L.clear_mat('cola', tint=(1, 0.96, 0.92, 1), rough=0.0, ior=1.34, shadow=0.35,
                           volume=(0.56, 0.21, 0.05), density=105.0, reflect=False)
        LP = [(max(r - 0.00022, 0.0004), z) for (r, z) in P if z < liquid_level - 0.0005]
        r_top = bottle_radius(liquid_level, ribs, lab) - 0.00022
        LP.append((r_top, liquid_level))
        liq = L.lathe('liquid', LP, segments=96, mats=[cola], cap_bottom=True, cap_top=True, sharp_deg=60)
        L.parent(liq, bottle)
        # a ring of tiny foam bubbles at the surface
        foam = L.simple_mat('foam', L.srgb(0.78, 0.62, 0.42), rough=0.5)
        bm = bmesh.new()
        rnd = random.Random(4)
        for k in range(70):
            a = rnd.uniform(0, 6.283)
            rr = r_top - rnd.uniform(0.0006, 0.0030)
            s = rnd.uniform(0.0005, 0.0012)
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=s, matrix=Matrix.Translation((rr * math.cos(a), rr * math.sin(a), liquid_level + s * 0.2)))
        fo = L.obj_from_bm('foam', bm, smooth=True, mats=[foam])
        L.parent(fo, bottle)
    return bottle


@L.frame('clear_bottle_empty')
def f_bottle_empty(scene):
    b = make_bottle('water')
    b.rotation_euler.z = math.radians(8)
    return dict(objs=[b], lens=40, shot=dict(elev=14, azim=12, fill=0.70, fstop=11))


@L.frame('clear_bottle_half_cola')
def f_bottle_cola(scene):
    b = make_bottle('cola', liquid_level=0.098)
    b.rotation_euler.z = math.radians(6)
    return dict(objs=[b], lens=40, shot=dict(elev=13, azim=10, fill=0.70, fstop=11))


# =============================================================== pizza box
def flat_ring(name, r_out, r_in, mat, seg=96):
    bm = bmesh.new()
    o = [bm.verts.new((r_out * math.cos(2 * math.pi * j / seg), r_out * math.sin(2 * math.pi * j / seg), 0)) for j in range(seg)]
    i = [bm.verts.new((r_in * math.cos(2 * math.pi * j / seg), r_in * math.sin(2 * math.pi * j / seg), 0)) for j in range(seg)]
    for j in range(seg):
        j2 = (j + 1) % seg
        bm.faces.new((o[j], o[j2], i[j2], i[j]))
    return L.obj_from_bm(name, bm, mats=[mat])


def make_pizza_box(open_deg=0.0, greasy=False, seed=1.0):
    W = D = 0.33
    H, t = 0.042, 0.003
    stain = dict(center=(0.0, 0.0), radius=0.158, amount=1.0) if greasy else None
    tray_m = L.cardboard('tray_cb', stain=stain, seed=seed)
    edge_m = L.cardboard_edge('cb_edge')
    lid_stain = dict(center=(0.01, -D / 2), radius=0.17, amount=0.42, splatter=False, patchy=True) if greasy else None
    lid_m = L.cardboard('lid_cb', stain=lid_stain, seed=seed + 2.3)
    ink = L.simple_mat('ink_red', INK_RED, rough=0.88)

    bm = bmesh.new()
    L.add_box(bm, (W, D, t), (0, 0, t / 2))
    L.add_box(bm, (W, t, H), (0, -D / 2 + t / 2, H / 2))
    L.add_box(bm, (W, t, H), (0, D / 2 - t / 2, H / 2))
    L.add_box(bm, (t, D - 2 * t, H), (-W / 2 + t / 2, 0, H / 2))
    L.add_box(bm, (t, D - 2 * t, H), (W / 2 - t / 2, 0, H / 2))
    for f in bm.faces:
        if f.normal.z > 0.9 and f.calc_center_median().z > H - 1e-4:
            f.material_index = 1
    tray = L.obj_from_bm('pizza_tray', bm, mats=[tray_m, edge_m])
    L.add_bevel(tray, 0.0006, segments=2)

    bm = bmesh.new()
    Hf = 0.036
    L.add_box(bm, (W, D, t), (0, -D / 2, t / 2))
    L.add_box(bm, (W - 2 * t - 0.003, t, Hf), (0, -D + t * 1.5 + 0.002, -Hf / 2 + 0.0002))
    for sx in (-1, 1):
        L.add_box(bm, (t, D - 0.03, Hf), (sx * (W / 2 - t * 1.5 - 0.002), -D / 2, -Hf / 2 + 0.0002))
    for f in bm.faces:
        if f.normal.z < -0.9 and f.calc_center_median().z < -Hf + 0.001:
            f.material_index = 1
    lid = L.obj_from_bm('pizza_lid', bm, mats=[lid_m, edge_m])
    L.add_bevel(lid, 0.0006, segments=2)
    lid.location = (0, D / 2, H + 0.0008)
    lid.rotation_euler.x = -math.radians(open_deg)
    L.parent(lid, tray)

    # print on the outside of the lid (local +Z face)
    zt = t + 0.00025
    cy = -D / 2
    for body, y, size, fname, sp in (('PIZZA', cy - 0.004, 0.088, 'COOPBL.TTF', 1.0),
                                     ('HOT  &  FRESH', cy + 0.078, 0.021, 'ariblk.ttf', 1.15),
                                     ('BAKED TO ORDER', cy - 0.082, 0.0165, 'arialbd.ttf', 1.4)):
        tx = L.text_obj('print', body, size, ink, fname, spacing=sp)
        tx.location = (0, y, zt)
        L.parent(tx, lid)
    rg = flat_ring('print_ring', 0.150, 0.1455, ink)
    rg.location = (0, cy, zt)
    L.parent(rg, lid)
    rg2 = flat_ring('print_ring2', 0.1425, 0.1410, ink)
    rg2.location = (0, cy, zt)
    L.parent(rg2, lid)
    for sx in (-1, 1):          # corner stars
        for sy in (-1, 1):
            st = L.text_obj('star', '★', 0.030, ink, 'seguisym.ttf')
            st.location = (sx * 0.137, cy + sy * 0.137, zt)
            L.parent(st, lid)
    ft = L.text_obj('front_print', '★  FRESH  •  HOT  •  DELICIOUS  ★', 0.0145, ink, 'arialbd.ttf', spacing=1.2)
    ft.rotation_euler.x = math.radians(90)
    ft.location = (0, -D / 2 - 0.0003, H * 0.5)
    L.parent(ft, tray)
    return tray, lid


def add_crumbs(tray, seed=3, heavy=True):
    t = 0.003
    tan = L.simple_mat('crumb_tan', L.srgb(0.80, 0.62, 0.36), rough=0.9)
    gold = L.simple_mat('crumb_gold', L.srgb(0.70, 0.47, 0.20), rough=0.85)
    dark = L.simple_mat('crumb_dark', L.srgb(0.30, 0.17, 0.08), rough=0.8)
    keep = lambda x, y: (x * x + y * y) < 0.155 ** 2
    for ob in L.scatter_blobs('crumbs', 170 if heavy else 60, (-0.15, 0.15, -0.15, 0.15), t, (0.0012, 0.0040), [tan, gold, dark], seed=seed, keep=keep):
        L.parent(ob, tray)
    # burnt cheese bits: flattened greasy blobs
    m, nt, bsdf, out = L.new_mat('burnt_cheese')
    co = L.tex_coord(nt, 'Object')
    n = L.noise_tex(nt, co, scale=160, detail=3)
    c = L.ramp(nt, n, [(0.30, L.srgb(0.16, 0.08, 0.03)), (0.50, L.srgb(0.62, 0.33, 0.08)), (0.72, L.srgb(0.93, 0.70, 0.22))])
    L.setp(nt, bsdf, base=c, rough=0.32, normal=L.bump(nt, n, strength=0.4, distance=0.001))
    rnd = random.Random(seed + 5)
    for k in range(7):
        r = rnd.uniform(0.006, 0.013)
        b = L.blob(f'cheese{k}', r, subdiv=3, amp=0.45, freq=1.6, seed=k + seed, squash=(1.0, rnd.uniform(0.6, 1.2), 0.16), mat=m)
        a, rr = rnd.uniform(0, 6.283), rnd.uniform(0.02, 0.125)
        b.location = (rr * math.cos(a), rr * math.sin(a), t + r * 0.10)
        b.rotation_euler.z = rnd.uniform(0, 6.283)
        L.parent(b, tray)


@L.frame('pizza_box_closed')
def f_pizza_closed(scene):
    tray, lid = make_pizza_box(open_deg=0.0)
    tray.rotation_euler.z = math.radians(-8)
    return dict(objs=[tray, lid], lens=30, shot=dict(elev=31, azim=28, fill=0.78, fstop=7))


@L.frame('pizza_box_open_greasy')
def f_pizza_greasy(scene):
    tray, lid = make_pizza_box(open_deg=104, greasy=True, seed=1.0)
    add_crumbs(tray, seed=3, heavy=True)
    tray.rotation_euler.z = math.radians(-6)
    return dict(objs=[tray], lens=30, shot=dict(elev=40, azim=20, fill=0.70, fstop=7, shift=(0.0, -0.10)))


@L.frame('pizza_box_open_clean')
def f_pizza_clean(scene):
    tray, lid = make_pizza_box(open_deg=104, greasy=False, seed=4.0)
    tray.rotation_euler.z = math.radians(-6)
    return dict(objs=[tray], lens=30, shot=dict(elev=40, azim=20, fill=0.70, fstop=7, shift=(0.0, -0.10)))
