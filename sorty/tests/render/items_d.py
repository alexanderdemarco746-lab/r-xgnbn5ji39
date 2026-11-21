"""Batch D: spoiled leftovers - open pizza box with moldy slices."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise
import sortylib as L
import items_a as A
import items_c as C


def old_pizza_mats(R):
    """Dried-out week-old pizza: duller, darker, matte."""
    cm, nt, bsdf, out = L.new_mat('old_cheese')
    co = L.tex_coord(nt, 'Object')
    n = L.noise_tex(nt, co, scale=95, detail=4, rough=0.6)
    c = L.ramp(nt, n, [(0.28, L.srgb(0.36, 0.20, 0.07)), (0.46, L.srgb(0.68, 0.46, 0.16)), (0.72, L.srgb(0.80, 0.65, 0.34))])
    ln = nt.nodes.new('ShaderNodeVectorMath')
    ln.operation = 'LENGTH'
    nt.links.new(co, ln.inputs[0])
    sc = L.math_n(nt, 'MULTIPLY', ln.outputs['Value'], 1 / 0.2)
    sauce = L.ramp(nt, sc, [((R - 0.030) / 0.2, 0), ((R - 0.022) / 0.2, 1)])
    c = L.mix_col(nt, L.math_n(nt, 'MULTIPLY', sauce, 0.9), c, L.srgb(0.40, 0.08, 0.04))
    L.setp(nt, bsdf, base=c, rough=0.62, normal=L.bump(nt, n, strength=0.6, distance=0.002))
    br, nt, bsdf, out = L.new_mat('old_crust')
    co = L.tex_coord(nt, 'Object')
    n = L.noise_tex(nt, co, scale=70, detail=4, rough=0.65)
    c = L.ramp(nt, n, [(0.30, L.srgb(0.36, 0.20, 0.08)), (0.52, L.srgb(0.66, 0.46, 0.22)), (0.78, L.srgb(0.80, 0.63, 0.38))])
    L.setp(nt, bsdf, base=c, rough=0.85, normal=L.bump(nt, n, strength=0.6, distance=0.002))
    pm, nt, bsdf, out = L.new_mat('old_pepperoni')
    co = L.tex_coord(nt, 'Object')
    n = L.noise_tex(nt, co, scale=260, detail=3)
    c = L.mix_col(nt, n, L.srgb(0.30, 0.05, 0.04), L.srgb(0.48, 0.11, 0.07))
    L.setp(nt, bsdf, base=c, rough=0.5)
    return cm, br, pm


MOLD_KINDS = {
    #            centre                     mid                        rim
    'bluegreen': (L.srgb(0.12, 0.33, 0.35), L.srgb(0.32, 0.56, 0.55), L.srgb(0.88, 0.91, 0.88)),
    'greygreen': (L.srgb(0.25, 0.37, 0.28), L.srgb(0.50, 0.60, 0.50), L.srgb(0.87, 0.89, 0.85)),
    'white':     (L.srgb(0.78, 0.81, 0.77), L.srgb(0.90, 0.92, 0.89), L.srgb(0.97, 0.97, 0.96)),
    'dark':      (L.srgb(0.04, 0.06, 0.05), L.srgb(0.15, 0.20, 0.17), L.srgb(0.62, 0.65, 0.62)),
}


def mold_mats():
    """Matte, velvety colony materials: coloured centre, pale fuzzy rim (zones follow the colony's own bounding box)."""
    mats = {}
    for kind, (centre, mid, rim) in MOLD_KINDS.items():
        m, nt, bsdf, out = L.new_mat('mold_' + kind)
        gen = L.tex_coord(nt, 'Generated')
        co = L.tex_coord(nt, 'Object')
        g = L.gradient_tex(nt, L.mapping(nt, gen, loc=(-1, -1, 0), scale=(2, 2, 0)))
        wob = L.noise_tex(nt, co, scale=420, detail=3, rough=0.6)
        t = L.math_n(nt, 'ADD', g, L.math_n(nt, 'MULTIPLY', L.math_n(nt, 'SUBTRACT', wob, 0.5), 0.30), clamp=True)
        c = L.ramp(nt, t, [(0.0, rim), (0.11, rim), (0.28, mid), (0.56, centre), (1.0, L.scale_col(centre, 0.7))])
        powder = L.noise_tex(nt, co, scale=2600, detail=2)
        c = L.mix_col(nt, L.math_n(nt, 'MULTIPLY', L.ramp(nt, powder, [(0.5, 0), (0.75, 1)]), 0.35), c, rim)
        L.setp(nt, bsdf, base=c, rough=1.0, spec=0.05, sheen=1.0, sheen_rough=0.55, sss=0.12, sss_radius=(0.002, 0.002, 0.002),
               normal=L.bump(nt, L.noise_tex(nt, co, scale=1700, detail=3), strength=0.9, distance=0.0007))
        fz_rim = L.simple_mat('fuzz_rim_' + kind, rim, rough=1.0, spec=0.05, sheen=1.0, sss=0.25)
        fz_mid = L.simple_mat('fuzz_mid_' + kind, mid, rough=1.0, spec=0.05, sheen=1.0)
        fz_c = L.simple_mat('fuzz_c_' + kind, centre, rough=1.0, spec=0.05, sheen=1.0)
        mats[kind] = (m, fz_rim, fz_mid, fz_c)
    mats['spot'] = L.simple_mat('mold_spot', L.srgb(0.03, 0.05, 0.04), rough=1.0, spec=0.05)
    return mats


def mold_colony(name, r, kind, mats, parent, loc, seed=0, height=0.36, spots=True):
    """One fuzzy raised colony: lobed dome + thousands of sub-millimetre fuzz beads + a few dark spore dots."""
    m, fz_rim, fz_mid, fz_c = mats[kind]
    rnd = random.Random(seed * 7 + 1)
    dome = L.blob(name, r, subdiv=4, amp=0.26, freq=2.3, seed=seed, squash=(1.0, rnd.uniform(0.82, 1.0), height), mat=m)
    dome.location = loc
    dome.rotation_euler.z = rnd.uniform(0, 6.283)
    L.parent(dome, parent)
    bm_r, bm_m, bm_c, bm_s = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    n = int(1500 * (r / 0.012) ** 2)
    for k in range(n):
        a = rnd.uniform(0, 6.283)
        q = rnd.random() ** 0.5 * 1.12
        x, y = r * q * math.cos(a), r * q * math.sin(a) * 0.92
        z = r * height * math.sqrt(max(0.0, 1 - min(q, 1.0) ** 2))
        s = rnd.uniform(0.00022, 0.00060)
        M = Matrix.Translation((x, y, z + s * 0.6))
        bmesh.ops.create_icosphere(bm_r if q > 0.84 else (bm_m if q > 0.50 else bm_c), subdivisions=1, radius=s, matrix=M)
    if spots and kind != 'white':
        for k in range(int(26 * (r / 0.012) ** 2)):
            a = rnd.uniform(0, 6.283)
            q = rnd.random() * 0.55
            x, y = r * q * math.cos(a), r * q * math.sin(a)
            z = r * height * math.sqrt(1 - q * q)
            bmesh.ops.create_icosphere(bm_s, subdivisions=1, radius=rnd.uniform(0.0005, 0.0011), matrix=Matrix.Translation((x, y, z + 0.0005)))
    for nm, bm_, mt in (('fr', bm_r, fz_rim), ('fm', bm_m, fz_mid), ('fc', bm_c, fz_c), ('sp', bm_s, mats['spot'])):
        if len(bm_.verts):
            o = L.obj_from_bm(f'{name}_{nm}', bm_, smooth=True, mats=[mt])
            L.parent(o, dome)
        else:
            bm_.free()
    return dome


@L.frame('pizza_box_open_moldy')
def f_pizza_moldy(scene):
    R = 0.148
    tray, lid = A.make_pizza_box(open_deg=104, greasy=True, seed=6.0)
    A.add_crumbs(tray, seed=9, heavy=False)
    pm = old_pizza_mats(R)
    s1 = C.pizza_slice('slice_a', R=R, eaten=0.26, seed=1.0, mats=pm)
    s1.location = (-0.105, -0.092, 0.0032)
    s1.rotation_euler.z = math.radians(-34)
    L.parent(s1, tray)
    s2 = C.pizza_slice('slice_b', R=R, eaten=0.0, seed=4.0, crust_only=True, mats=pm)
    s2.location = (0.030, 0.098, 0.0032)
    s2.rotation_euler.z = math.radians(200)
    L.parent(s2, tray)
    mm = mold_mats()

    def pol(rho, deg, z):
        a = math.radians(deg)
        return (rho * math.sin(a), rho * math.cos(a), z)

    # on the slice (local polar coords: rho from the tip, angle from the slice axis)
    for i, (rho, deg, r, kind) in enumerate(((0.058, 1, 0.0145, 'bluegreen'), (0.084, 9, 0.0190, 'greygreen'), (0.087, -10, 0.0145, 'white'),
                                             (0.110, 3, 0.0175, 'bluegreen'), (0.112, -13, 0.0120, 'greygreen'), (0.127, 12, 0.0130, 'white'),
                                             (0.070, -8, 0.0070, 'dark'), (0.098, 15, 0.0060, 'dark'), (0.124, -6, 0.0070, 'bluegreen'),
                                             (0.046, 8, 0.0065, 'white'), (0.100, -4, 0.0050, 'dark'), (0.072, 5, 0.0110, 'bluegreen'),
                                             (0.098, -9, 0.0100, 'greygreen'))):
        mold_colony(f'mold_a{i}', r, kind, mm, s1, pol(rho, deg, 0.0070), seed=10 + i)
    # on the bitten crust piece
    for i, (rho, deg, r, kind, z) in enumerate(((0.141, -12, 0.0130, 'bluegreen', 0.0120), (0.142, 0, 0.0150, 'white', 0.0125),
                                                (0.141, 11, 0.0120, 'greygreen', 0.0120), (0.126, -5, 0.0090, 'greygreen', 0.0070),
                                                (0.126, 7, 0.0075, 'dark', 0.0070), (0.142, 6, 0.0100, 'bluegreen', 0.0125))):
        mold_colony(f'mold_b{i}', r, kind, mm, s2, pol(rho, deg, z), seed=40 + i)
    # spreading onto the cardboard near the leftovers (tray coordinates)
    for i, (x, y, r, kind) in enumerate(((-0.004, -0.052, 0.0160, 'white'), (0.012, -0.040, 0.0110, 'greygreen'), (0.004, -0.064, 0.0100, 'bluegreen'),
                                         (-0.118, -0.004, 0.0135, 'bluegreen'), (-0.106, 0.008, 0.0090, 'greygreen'), (-0.022, 0.032, 0.0110, 'greygreen'),
                                         (0.046, -0.078, 0.0150, 'greygreen'), (0.058, -0.066, 0.0100, 'bluegreen'), (0.126, -0.062, 0.0120, 'white'),
                                         (0.060, -0.092, 0.0070, 'dark'), (-0.096, 0.012, 0.0060, 'dark'), (0.020, -0.066, 0.0050, 'dark'),
                                         (0.110, -0.082, 0.0060, 'bluegreen'), (-0.036, -0.062, 0.0060, 'bluegreen'))):
        mold_colony(f'mold_c{i}', r, kind, mm, tray, (x, y, 0.0030), seed=70 + i, height=0.28)
    tray.rotation_euler.z = math.radians(-6)
    return dict(objs=[tray], lens=30, shot=dict(elev=41, azim=20, fill=0.80, fstop=7, shift=(0.0, 0.06)))
