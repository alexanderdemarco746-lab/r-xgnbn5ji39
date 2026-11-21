"""Batch E: commonly mis-binned items - disposable vape, loose plastic grocery bag, juice carton."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise
import sortylib as L
import items_b as B

WHITE = (1, 1, 1, 1)
BLACK = (0.012, 0.012, 0.012, 1)


def fit_text(ob, max_w):
    bpy.context.view_layer.update()
    if ob.dimensions.x > max_w > 0:
        k = max_w / ob.dimensions.x
        ob.scale = (k, k, 1)
    return ob


# =============================================================== disposable vape bar
def make_vape():
    w, d, Lb, r = 0.041, 0.019, 0.079, 0.0085
    y0, y1 = -Lb / 2, Lb / 2
    rings = [(w - 0.0050, d - 0.0050, r - 0.0025, y0), (w - 0.0012, d - 0.0012, r - 0.0006, y0 + 0.0012), (w, d, r, y0 + 0.0035),
             (w, d, r, y1 - 0.0045), (w - 0.0030, d - 0.0020, r - 0.0010, y1 - 0.0012), (w - 0.0100, d - 0.0045, r - 0.0030, y1),
             (0.0265, 0.0125, 0.0058, y1 + 0.0030), (0.0215, 0.0098, 0.0046, y1 + 0.0090), (0.0185, 0.0082, 0.0038, y1 + 0.0150),
             (0.0165, 0.0068, 0.0030, y1 + 0.0162), (0.0120, 0.0036, 0.0016, y1 + 0.0162), (0.0115, 0.0032, 0.0014, y1 + 0.0120)]
    bm = bmesh.new()
    vr = [[bm.verts.new((a, yk, b)) for a, b in B.rr_ring(rw, rd, rr, n=8)] for (rw, rd, rr, yk) in rings]
    n = len(vr[0])
    for i in range(len(vr) - 1):
        mi = 0 if i < 5 else (1 if i < 9 else 2)
        for j in range(n):
            j2 = (j + 1) % n
            f = bm.faces.new((vr[i][j], vr[i + 1][j], vr[i + 1][j2], vr[i][j2]))
            f.material_index = mi
            f.smooth = True
    bm.faces.new(vr[0]).material_index = 0
    bm.faces.new(list(reversed(vr[-1]))).material_index = 2
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bodym, nt, bsdf, out = L.new_mat('vape_body')
    co = L.tex_coord(nt, 'Object')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(co, sep.inputs[0])
    t = L.math_n(nt, 'MULTIPLY', L.math_n(nt, 'ADD', sep.outputs['Y'], Lb / 2), 1 / Lb, clamp=True)
    c = L.ramp(nt, t, [(0.0, L.srgb(0.00, 0.55, 1.00)), (0.5, L.srgb(0.50, 0.22, 0.98)), (1.0, L.srgb(1.00, 0.12, 0.55))])
    L.setp(nt, bsdf, base=c, rough=0.17, coat=0.6, coat_rough=0.05)
    tipm = L.plastic('vape_mouthpiece', (0.012, 0.012, 0.016, 1), rough=0.16)
    holem = L.simple_mat('vape_hole', (0.002, 0.002, 0.002, 1), rough=0.8)
    body = L.obj_from_bm('vape', bm, smooth=True, sharp_deg=42, mats=[bodym, tipm, holem])
    zt = d / 2 + 0.00016
    wh = L.simple_mat('vape_print_white', (0.95, 0.95, 0.95, 1), rough=0.35)
    bk = L.simple_mat('vape_print_black', BLACK, rough=0.5)

    def put(txt, y, size, mat, fname='ariblk.ttf', x=0.0, max_w=0.025, spacing=1.0, dz=0.0):
        t_ = L.text_obj('vape_txt', txt, size, mat, fname, spacing=spacing)
        t_.location = (x, y, zt + dz)
        L.parent(t_, body)
        return fit_text(t_, max_w)

    put('VAPOR BAR', 0.0285, 0.0036, wh, 'ariblk.ttf', spacing=1.1)
    put('5000', 0.0150, 0.0125, wh, 'impact.ttf', max_w=0.024)
    put('PUFFS', 0.0040, 0.0058, wh, 'ariblk.ttf', max_w=0.022, spacing=1.2)
    put('BLUE RAZZ ICE', -0.0040, 0.0026, wh, 'arialbd.ttf', max_w=0.022, spacing=1.1)
    box = L.plane_uv('vape_warn_box', 0.0262, 0.0092, mat=wh)
    box.location = (0, -0.0138, zt - 0.00006)
    L.parent(box, body)
    put('WARNING: This product', -0.0119, 0.0027, bk, 'arialbd.ttf', max_w=0.0240, dz=0.00004)
    put('contains NICOTINE', -0.0159, 0.0027, bk, 'ariblk.ttf', max_w=0.0225, dz=0.00004)
    # battery icon + strength
    bmi = bmesh.new()
    bx, by, bw, bh, tk = -0.0078, -0.0245, 0.0076, 0.0038, 0.00045
    for (cx, cy, sx, sy) in ((bx, by + bh / 2, bw, tk), (bx, by - bh / 2, bw, tk), (bx - bw / 2, by, tk, bh + tk), (bx + bw / 2, by, tk, bh + tk),
                             (bx + bw / 2 + 0.0006, by, 0.0008, bh * 0.45), (bx - 0.0020, by, 0.0016, bh * 0.62), (bx + 0.0002, by, 0.0016, bh * 0.62)):
        L.add_box(bmi, (sx, sy, 0.00004), (cx, cy, zt))
    L.parent(L.obj_from_bm('vape_batt_icon', bmi, mats=[wh]), body)
    put('5% NIC', -0.0245, 0.0027, wh, 'arialbd.ttf', x=0.0052, max_w=0.0120)
    put('650mAh', -0.0300, 0.0019, wh, 'arial.ttf', x=0.0, max_w=0.0120)
    # LED indicator on the front near the bottom end
    ledm, nt, bsdf, out = L.new_mat('vape_led')
    L.setp(nt, bsdf, base=(0.6, 0.95, 1.0, 1), emit=(0.35, 0.9, 1.0, 1), emit_strength=6.0, rough=0.2)
    led = L.disc('vape_led', 0.0011, mat=ledm, segments=20)
    led.location = (0, y0 + 0.0052, zt)
    L.parent(led, body)
    # USB-C port and two air holes on the bottom end face
    bmp = bmesh.new()
    bmp.faces.new([bmp.verts.new((a, y0 - 0.00012, b)) for a, b in B.rr_ring(0.0092, 0.0034, 0.0016, n=6)])
    L.parent(L.obj_from_bm('vape_usbc', bmp, mats=[holem]), body)
    bmp = bmesh.new()
    bmp.faces.new([bmp.verts.new((a, y0 - 0.00016, b)) for a, b in B.rr_ring(0.0068, 0.0014, 0.0006, n=4)])
    L.parent(L.obj_from_bm('vape_usbc_tongue', bmp, mats=[L.simple_mat('usb_tongue', (0.25, 0.25, 0.27, 1), rough=0.3, metallic=0.8)]), body)
    for sx in (-1, 1):
        bmp = bmesh.new()
        bmp.faces.new([bmp.verts.new((sx * 0.0115 + 0.0008 * math.cos(k * math.pi / 6), y0 - 0.00012, 0.0008 * math.sin(k * math.pi / 6))) for k in range(12)])
        L.parent(L.obj_from_bm('vape_airhole', bmp, mats=[holem]), body)
    body.location = (0, 0, d / 2)
    return body


@L.frame('vape')
def f_vape(scene):
    v = make_vape()
    v.rotation_euler.z = math.radians(-16)
    return dict(objs=[v], lens=50, shot=dict(elev=41, azim=12, fill=0.66, fstop=16))


# =============================================================== loose plastic grocery bag
def make_plastic_bag(seed=4.0):
    w, h, ybot = 0.30, 0.44, -0.20
    RED = L.srgb(0.80, 0.06, 0.08)
    film_white = L.srgb(0.96, 0.96, 0.97)
    lb = L.Label('thankyou_bag2', w, h, px=2048, bg=film_white)
    # label y = bag y - (ybot + h/2) = bag y - 0.02
    for k in range(4):
        lb.text('THANK YOU', 0, -0.018 - k * 0.039, 0.030, RED, 'ariblk.ttf', fit_w=0.21)
    lb.text('HAVE A NICE DAY!', 0, -0.182, 0.014, RED, 'arialbd.ttf', spacing=1.1)
    lb.rect(0, -0.160, 0.21, 0.0022, RED)
    img = lb.render()
    m, nt, bsdf, out = L.new_mat('bag_film_thin')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    co = L.tex_coord(nt, 'Object')
    wr = L.noise_tex(nt, co, scale=55, detail=4, rough=0.65, distortion=0.8)
    fine = L.noise_tex(nt, co, scale=260, detail=2)
    L.setp(nt, bsdf, base=tex.outputs['Color'], rough=L.mix_val(nt, wr, 0.18, 0.34), trans=0.50, ior=1.25, spec=0.6,
           normal=L.bump(nt, L.math_n(nt, 'ADD', wr, L.math_n(nt, 'MULTIPLY', fine, 0.3)), strength=0.55, distance=0.0025))
    try:
        bsdf.inputs['Thin Wall'].default_value = True
    except Exception:
        try:
            bsdf.inputs['Thin Wall'].default_value = 1.0
        except Exception:
            pass

    def inside(x, y, front=True):
        ax = abs(x)
        if ax > 0.15 or y < ybot:
            return False
        if y < -0.185 and ax > 0.135 and math.hypot(ax - 0.135, y + 0.185) > 0.015:
            return False
        if y <= 0.10:
            if ax < 0.07:
                return y < 0.10 - (0.088 if front else 0.030) * math.sqrt(max(0.0, 1 - (ax / 0.07) ** 2))
            return True
        if ax < 0.07:
            return False
        return y < 0.236 - 0.022 * ((ax - 0.11) / 0.04) ** 2

    def fr(x, y, f, s=0.0):
        return noise.fractal(Vector((x * f + s, y * f - s, seed)), 1.0, 2.0, 4)

    def ridge(x, y, f, s=0.0):
        return noise.ridged_multi_fractal(Vector((x * f + s, y * f + s * 0.7, seed * 1.3)), 1.0, 2.0, 3, 1.0, 2.0)

    nx, ny = 76, 110

    def build(front):
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new('UVMap')
        grid = []
        for j in range(ny + 1):
            row = []
            for i in range(nx + 1):
                x0, y0_ = -w / 2 + w * i / nx, ybot + h * j / ny
                x = x0 + 0.005 * fr(x0, y0_, 7, 1.0) + 0.012 * (y0_ / 0.2) * (x0 / 0.15) * 0.25
                y = y0_ + 0.005 * fr(x0, y0_, 6, 5.0)
                if front:
                    lift = 0.040 * math.exp(-((y0_ - 0.030) / 0.060) ** 2) * max(0.0, 1 - (x0 / 0.105) ** 2)
                    puff = 0.010 * max(0.0, 1 - (x0 / 0.15) ** 2) ** 0.5 * max(0.0, 1 - ((y0_ + 0.04) / 0.17) ** 2) ** 0.5
                    z = 0.0030 + puff * (0.6 + 0.4 * fr(x0, y0_, 5, 2.0)) + lift + 0.0085 * max(ridge(x0, y0_, 9) - 0.85, 0) \
                        + 0.0022 * fr(x0, y0_, 38, 8.0)
                    if y0_ > 0.10:            # handle straps: a little lifted and twisted
                        z += 0.006 + 0.010 * (y0_ - 0.10) / 0.13 * (0.5 + 0.5 * math.sin(x0 * 40 + 1))
                    z = max(z, 0.0026)
                else:
                    z = 0.0007 + 0.0016 * max(ridge(x0, y0_, 8, 4.0) - 0.8, 0)
                row.append(bm.verts.new((x, y, z)))
            grid.append(row)
        for j in range(ny):
            for i in range(nx):
                xc, yc = -w / 2 + w * (i + 0.5) / nx, ybot + h * (j + 0.5) / ny
                if not inside(xc, yc, front):
                    continue
                f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
                f.smooth = True
                for loop, (a_, b_) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                    loop[uvl].uv = (a_ / nx, b_ / ny)
        for v in list(bm.verts):
            if not v.link_faces:
                bm.verts.remove(v)
        return bm

    front = L.obj_from_bm('bag_front', build(True), smooth=True, sharp_deg=38, mats=[m])
    back = L.obj_from_bm('bag_back', build(False), smooth=True, sharp_deg=38, mats=[m])
    L.add_subsurf(front, 1)
    L.parent(back, front)
    return front, back


@L.frame('plastic_bag')
def f_plastic_bag(scene):
    front, back = make_plastic_bag()
    front.rotation_euler.z = math.radians(-20)
    return dict(objs=[front, back], lens=32, shot=dict(elev=50, azim=6, fill=0.84, fstop=9))


# =============================================================== juice carton (gable top, screw cap)
def make_carton():
    s, hb, rise, fin = 0.070, 0.195, 0.033, 0.012
    W, H = 4 * s, hb
    ORANGE, DEEP = L.srgb(0.98, 0.56, 0.05), L.srgb(0.94, 0.40, 0.02)
    GREEN = L.srgb(0.10, 0.50, 0.15)
    lb = L.Label('oj_carton', W, H, px=2048, bg=ORANGE)
    lb.rect(0, -H / 2 + 0.026, W, 0.052, WHITE)
    lb.wave_band(-H / 2 + 0.054, 0.0035, 0.0080, WHITE, periods=4)

    def front_panel(x0):
        lb.rect(x0, 0.079, 0.050, 0.0125, GREEN)
        lb.text('100% PURE', x0, 0.079, 0.0066, WHITE, 'arialbd.ttf', fit_w=0.044, spacing=1.1)
        lb.text('ORANGE', x0, 0.054, 0.0190, WHITE, 'COOPBL.TTF', fit_w=0.061)
        lb.text('JUICE', x0, 0.032, 0.0190, WHITE, 'COOPBL.TTF', fit_w=0.050)
        lb.text('NOT FROM CONCENTRATE', x0, 0.0165, 0.0030, WHITE, 'arialbd.ttf', fit_w=0.058)
        lb.ellipse(x0, -0.016, 0.0255, 0.0255, WHITE)
        lb.ellipse(x0, -0.016, 0.0235, 0.0235, DEEP)
        lb.ellipse(x0 - 0.007, -0.008, 0.0075, 0.0050, L.srgb(1.0, 0.72, 0.32), rot=0.5)
        lb.ellipse(x0 + 0.010, 0.008, 0.0110, 0.0048, GREEN, rot=0.6)
        lb.rect(x0 + 0.001, 0.0085, 0.0018, 0.0060, L.srgb(0.35, 0.22, 0.08), rot=-0.3)
        lb.text('1 QT (946 mL)', x0, -H / 2 + 0.030, 0.0056, DEEP, 'ariblk.ttf', fit_w=0.056)
        lb.text('KEEP REFRIGERATED', x0, -H / 2 + 0.014, 0.0034, GREEN, 'arialbd.ttf', fit_w=0.056)

    front_panel(0.0)
    front_panel(2 * s)          # back face = same design (wraps at the image edge, drawn on both halves)
    front_panel(-2 * s)
    xr = s                       # right face: nutrition facts
    lb.rect(xr, 0.012, 0.056, 0.128, WHITE)
    lb.rect(xr, 0.012, 0.0535, 0.1255, BLACK)
    lb.rect(xr, 0.012, 0.0520, 0.1240, WHITE)
    lb.text('Nutrition Facts', xr, 0.064, 0.0064, BLACK, 'ariblk.ttf', fit_w=0.048)
    for k, row in enumerate(('Serving size 8 fl oz', 'Calories 110', 'Total Fat 0g', 'Sodium 0mg', 'Total Carb. 26g', 'Sugars 22g',
                             'Protein 2g', 'Vitamin C 100%', 'Potassium 450mg', 'Calcium 2%')):
        yy = 0.052 - k * 0.0105
        lb.rect(xr, yy + 0.0048, 0.049, 0.0007 if k else 0.0022, BLACK)
        lb.text(row, xr, yy, 0.0036, BLACK, 'arialbd.ttf' if k < 2 else 'arial.ttf', fit_w=0.046)
    xl = -s                      # left face: ingredients, barcode, recycle note
    lb.text('ORANGE JUICE', xl, 0.070, 0.0074, WHITE, 'ariblk.ttf', fit_w=0.058)
    lb.text('Ingredients: 100% orange juice.', xl, 0.052, 0.0030, WHITE, 'arial.ttf', fit_w=0.058)
    lb.text('Pasteurized. Shake well.', xl, 0.044, 0.0030, WHITE, 'arial.ttf', fit_w=0.058)
    lb.barcode(xl, 0.005, 0.040, 0.022, n=40, seed=6)
    lb.text('PLEASE RECYCLE', xl, -H / 2 + 0.032, 0.0046, GREEN, 'ariblk.ttf', fit_w=0.054)
    lb.text('CARTON', xl, -H / 2 + 0.020, 0.0040, GREEN, 'arialbd.ttf', spacing=1.4)
    img = lb.render()
    board = L.image_mat('carton_board', img, rough=0.36, coat=0.25, bump_noise=0.04)
    roofm, nt, bsdf, out = L.new_mat('carton_roof')
    co = L.tex_coord(nt, 'Object')
    L.setp(nt, bsdf, base=ORANGE, rough=0.38, coat=0.25, normal=L.bump(nt, L.noise_tex(nt, co, scale=300, detail=2), strength=0.04, distance=0.0003))
    h2 = s / 2
    FL, FR, BR, BL = (-h2, -h2), (h2, -h2), (h2, h2), (-h2, h2)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    for (a, b, u0) in ((FL, FR, 0.375), (FR, BR, 0.625), (BR, BL, 0.875), (BL, FL, 0.125)):
        vs = [bm.verts.new((a[0], a[1], 0)), bm.verts.new((b[0], b[1], 0)), bm.verts.new((b[0], b[1], hb)), bm.verts.new((a[0], a[1], hb))]
        f = bm.faces.new(vs)
        for loop, uv in zip(f.loops, ((u0, 0), (u0 + 0.25, 0), (u0 + 0.25, 1), (u0, 1))):
            loop[uvl].uv = uv
    f = bm.faces.new([bm.verts.new((p[0], p[1], 0)) for p in (FL, BL, BR, FR)])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    carton = L.obj_from_bm('carton', bm, mats=[board])
    L.add_bevel(carton, 0.0014, segments=2)
    zr = hb + rise
    bm = bmesh.new()
    P = {k: bm.verts.new(v) for k, v in dict(FL=(-h2, -h2, hb), FR=(h2, -h2, hb), BR=(h2, h2, hb), BL=(-h2, h2, hb),
                                              RL=(-h2, 0, zr), RR=(h2, 0, zr)).items()}
    bm.faces.new((P['FL'], P['FR'], P['RR'], P['RL']))
    bm.faces.new((P['BR'], P['BL'], P['RL'], P['RR']))
    bm.faces.new((P['FR'], P['BR'], P['RR']))
    bm.faces.new((P['BL'], P['FL'], P['RL']))
    L.add_box(bm, (s, 0.0018, fin), (0, 0, zr + fin / 2 - 0.0012))
    roof = L.obj_from_bm('carton_roof', bm, mats=[roofm])
    L.add_bevel(roof, 0.0008, segments=2)
    L.parent(roof, carton)
    capm = L.plastic('carton_cap', L.srgb(0.97, 0.97, 0.96), rough=0.32, sss=0.05)

    def knurl(u, z, r_):
        return r_ + (0.00035 * (0.5 + 0.5 * math.sin(2 * math.pi * u * 44)) if 0.0045 < z < 0.0135 else 0.0)

    cap = L.lathe('carton_cap', [(0.0185, 0.0), (0.0190, 0.0012), (0.0170, 0.0022), (0.0160, 0.0030), (0.0160, 0.0045), (0.0160, 0.0135),
                                 (0.0152, 0.0150), (0.0006, 0.0152)], segments=176, mats=[capm], cap_top=True, radial_fn=knurl, sharp_deg=40)
    th = math.atan2(rise, h2)
    n_ = Vector((0, -math.sin(th), math.cos(th)))
    cap.location = Vector((0.0, -h2 / 2, hb + rise / 2)) + n_ * 0.0004
    cap.rotation_euler.x = th
    L.parent(cap, carton)
    return carton


@L.frame('carton_empty')
def f_carton(scene):
    c = make_carton()
    c.rotation_euler.z = math.radians(-4)
    return dict(objs=[c] + list(c.children), lens=40, shot=dict(elev=15, azim=27, fill=0.80, fstop=11))
