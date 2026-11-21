p = 'build_station.py'
s = open(p, encoding='utf-8').read()


def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, ("COUNT", s.count(a), a[:80])
    s = s.replace(a, b)


# pocket material: no specular sheen, so the openings stay evenly dark
rep('''def mat_pbr(name, hexc, rough=0.5, metallic=0.0, coat=0.0, emis_hex=None, emis=0.0):
    m = bpy.data.materials.new(name)
    b = _principled(_nodes(m))''', '''def mat_pbr(name, hexc, rough=0.5, metallic=0.0, coat=0.0, emis_hex=None, emis=0.0, spec=None):
    m = bpy.data.materials.new(name)
    b = _principled(_nodes(m))
    if spec is not None:
        b.inputs["Specular IOR Level"].default_value = spec''')
rep('''    M["pocket"] = mat_pbr("Bin_Opening_Dark", "#07080A", rough=0.9)''',
    '''    M["pocket"] = mat_pbr("Bin_Opening_Dark", "#050607", rough=1.0, spec=0.0)''')
rep('''    M["deck_text"] = mat_pbr("Bin_DeckText_Gray", "#4B535C", rough=0.6)''',
    '''    M["deck_text"] = mat_pbr("Bin_DeckText_Gray", "#2A3037", rough=0.6)''')

# body is one material; the light-gray deck becomes its own thin plate with a reveal line around it
rep('''    side[1].material_index = 1      # sloped deposit face
    side[2].material_index = 1      # flat top
''', '')
rep('''    # frame on the sloped face: local Z = face normal, local Y = up the slope
    face = new_obj("Bin_" + key.capitalize() + "_FaceFrame", None, coll, loc=(x, -0.1125, 0.87),
                   rot=(SLOPE_ANGLE, 0, 0))
''', '''    # light-gray deck plate laid over the sloped face and the flat top (inset, so the body shows as a reveal)
    ins, th = 0.02, 0.003
    sdy, sdz = cos(SLOPE_ANGLE), sin(SLOPE_ANGLE)          # slope direction in (y, z)
    nsy, nsz = -sdz, sdy                                   # slope normal in (y, z)
    a0 = (PROFILE[1][0] + sdy * ins, PROFILE[1][1] + sdz * ins)
    a1 = PROFILE[2]
    a2 = (PROFILE[3][0] - ins, PROFILE[3][1])
    kk = 1.0 / (1.0 + nsz)                                 # miter at the bend
    outline = [a0, a1, a2, (a2[0], a2[1] + th), (a1[0] + th * nsy * kk, a1[1] + th), (a0[0] + th * nsy, a0[1] + th * nsz)]
    hx = w / 2 - ins
    bm = bmesh.new()
    lo = [bm.verts.new((-hx, y, z)) for y, z in outline]
    hi = [bm.verts.new((hx, y, z)) for y, z in outline]
    m6 = len(outline)
    for i in range(m6):
        j = (i + 1) % m6
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.faces.new(lo[::-1])
    bm.faces.new(hi)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    deck_me = mesh_from_bm("Deck_" + key, bm)
    for mm in (M["cap"], M["cap"], M["pocket"]):
        deck_me.materials.append(mm)
    deck = new_obj("Bin_" + key.capitalize() + "_Deck", deck_me, coll, loc=(x, 0, 0))
    db = deck.modifiers.new("EdgeBevel", "BEVEL")
    db.width, db.segments, db.limit_method, db.angle_limit = 0.0012, 2, "ANGLE", radians(30)

    # frame on the sloped face (on top of the deck plate): local Z = face normal, local Y = up the slope
    face = new_obj("Bin_" + key.capitalize() + "_FaceFrame", None, coll,
                   loc=(x, -0.1125 + nsy * th, 0.87 + nsz * th), rot=(SLOPE_ANGLE, 0, 0))
''')
rep('''    bo = body.modifiers.new("Opening", "BOOLEAN")
    bo.operation, bo.object, bo.solver = "DIFFERENCE", cutter, "EXACT"
''', '''    for target in (body, deck):
        bo = target.modifiers.new("Opening", "BOOLEAN")
        bo.operation, bo.object, bo.solver = "DIFFERENCE", cutter, "EXACT"
''')
rep('''    text_obj("Bin_" + key.capitalize() + "_DeckHint", BIN_HINT[key], 0.0105, coll, M["deck_text"], fontfile=FONT_SEMI,
             parent=face, loc=(0, -0.1435, 0.0008))''',
    '''    text_obj("Bin_" + key.capitalize() + "_DeckHint", BIN_HINT[key], 0.0112, coll, M["deck_text"], fontfile=FONT_SEMI,
             parent=face, loc=(0, -0.1365, 0.0008))''')

# the clamp and the plain bin lid follow the 3 mm deck plate
rep('''    jaw = new_obj("Mount_ClampJaw", m_box("ClampJaw", 0.16, 0.09, 0.012), mount_coll, loc=(0, 0.2, 1.0065),''',
    '''    jaw = new_obj("Mount_ClampJaw", m_box("ClampJaw", 0.16, 0.09, 0.012), mount_coll, loc=(0, 0.2, 1.0095),''')
rep('''                loc=(sx * 0.052, 0.19, 1.0195), mat=M["metal_knob"])''',
    '''                loc=(sx * 0.052, 0.19, 1.0225), mat=M["metal_knob"])''')
rep('''    lid = new_obj("PlainBin_Lid", m_cyl("PlainBinLid", 0.229, 0.04, seg=72), coll, loc=(0, 0, 0.98))''',
    '''    lid = new_obj("PlainBin_Lid", m_cyl("PlainBinLid", 0.229, 0.043, seg=72), coll, loc=(0, 0, 0.9815))''')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print("patched OK", len(s.splitlines()))

s = open(p, encoding='utf-8').read()
rep('az = radians(-56 + 112 * i / (n - 1))            # sweep across the front of the station',
    'az = radians(26 + 40 * i / (n - 1))              # gentle arc around the hero angle (the head stays visible)')
rep('n = 16 if PREVIEW else 96', 'n = 12 if PREVIEW else 72')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print("turntable patched")
