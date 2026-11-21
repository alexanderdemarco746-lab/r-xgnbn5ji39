"""
Sorty showcase layers - stage plates, person sprites and anchor points for the animated web showcase.

Reuses build_station.py (runs it with "--views none --no-save", so nothing of the design renders or the
saved .blend is touched), then renders everything from ONE fixed "showcase camera" at 2560x1440 into
    ../showcase/assets/stage/
        stage_idle.jpg                      station + room, all bin lights dim, screen off
        stage_lit_{recycle,compost,landfill}.jpg   identical to idle except that one bin is lit
        person_{idle,present,walk}.png      RGBA sprites (full frame) with a soft floor shadow
        stage.json                          anchor points in pixels (origin top-left)
        _check_composite.jpg                lit plate + present sprite + a dot on every anchor

Run:   blender.exe -b --factory-startup -P render_showcase.py
Options after "--":
    --steps a,b,c    any of: frame, plates, sprites, json, check   (default: plates,sprites,json,check)
                     "frame" = quick low-res framing checks written to the temp folder only
    --tmp DIR        where intermediates and framing checks go (default: system temp)
    --scale 0.5      debug: run the chosen steps at reduced size with few samples, output to the temp folder
"""
import bpy, sys, os, json, runpy, tempfile, time
from math import radians, sin, cos, atan2, degrees
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "showcase", "assets", "stage"))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default=None):
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            return argv[i + 1]
        return True
    return default


STEPS = set(str(opt("--steps", "plates,sprites,json,check")).split(","))
TMP = str(opt("--tmp", os.path.join(tempfile.gettempdir(), "sorty_showcase_tmp")))
K = float(opt("--scale", 1.0))                       # 1.0 = final 2560x1440
DEST = OUT if K == 1.0 else os.path.join(TMP, "scaled")
os.makedirs(DEST, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

# ----------------------------------------------------------------------------- build the station scene
_argv = sys.argv
sys.argv = [sys.argv[0], "--", "--views", "none", "--no-save"]
B = runpy.run_path(os.path.join(HERE, "build_station.py"), run_name="sorty_station_build")
sys.argv = _argv
scene = B["scene"]
M, new_obj, new_coll, limb = B["M"], B["new_obj"], B["new_coll"], B["limb"]
m_sphere, m_capsule, two_bone_ik = B["m_sphere"], B["m_capsule"], B["two_bone_ik"]

W, H = 2560, 1440
# --- showcase camera: front-right of the station, elevated, 40 degrees off the front ------------------
CAM_AZIMUTH, CAM_DIST, CAM_HEIGHT, CAM_LENS = 40.0, 5.0, 1.95, 50.0
CAM_TARGET = Vector((0.091, -0.541, 0.82))
CAM_POS = Vector((CAM_TARGET.x + CAM_DIST * sin(radians(CAM_AZIMUTH)),
                  CAM_TARGET.y - CAM_DIST * cos(radians(CAM_AZIMUTH)), CAM_HEIGHT))
# --- where the person stands: the floor zone moves there and turns toward the Sorty head --------------
ZONE = Vector((-0.75, -1.0, 0.0))
YAW = atan2(0.0 - ZONE.x, 0.17 - ZONE.y)            # clockwise from +Y, toward the head at (0, 0.17)
FWD = Vector((sin(YAW), cos(YAW), 0.0))
PERSON_ROOT = ZONE - FWD * 0.10                      # feet land on the footprints of the marking

cam = B["add_camera"]("Cam_Showcase", CAM_POS, CAM_TARGET, CAM_LENS, B["C_CAMS"])
scene.camera = cam

# move + turn the floor marking as one rigid group
pivot = new_obj("ShowZone_Pivot", None, B["C_ENV"], loc=(0.0, -0.88, 0.0))
bpy.context.view_layer.update()
DECAL = [bpy.data.objects[n] for n in ("ShowZone_Outline", "ShowZone_Footprints", "ShowZone_Caption")]
for ob in DECAL:
    ob.parent = pivot
    ob.matrix_parent_inverse = pivot.matrix_world.inverted()
pivot.location = (ZONE.x, ZONE.y, 0.0)
pivot.rotation_euler = (0.0, 0.0, -YAW)

# the planter moves a little closer to the station so it stays inside this tighter frame
for ob in bpy.data.objects:
    if ob.name.startswith("Planter_"):
        ob.location.x -= 0.2

# softer lens ring for the plates (the web page animates the "looking" state itself)
M["lens_ring"].node_tree.nodes["Emission"].inputs["Strength"].default_value = 2.4

# ----------------------------------------------------------------------------- person poses
SHOULDER = lambda sx: Vector((sx * 0.212, 0.0, 1.40))
HANDS_PRESENT = {sx: Vector((sx * 0.14, 0.41, 1.21)) for sx in (-1, 1)}      # 28 cm apart, chest height


def build_pose(pose):
    coll = new_coll("Person_" + pose)
    root = new_obj("Person_%s_Root" % pose, None, coll, loc=PERSON_ROOT, rot=(0.0, 0.0, -YAW))
    mat = M["person"]

    def part(name, mesh, loc, scale=(1, 1, 1)):
        return new_obj("Person_%s_%s" % (pose, name), mesh, coll, parent=root, loc=loc, scale=scale, mat=mat)

    def seg(name, a, b, r):
        return limb("Person_%s_%s" % (pose, name), a, b, r, coll, mat, parent=root)

    part("Head", m_sphere("PHead", 0.105), (0, 0.01, 1.615), (0.95, 1.0, 1.08))
    seg("Neck", (0, 0, 1.43), (0, 0.005, 1.53), 0.045)
    part("Torso", m_capsule("PTorso", 0.15, 0.29), (0, 0, 1.19), (1.24, 0.72, 1.0))
    part("Pelvis", m_sphere("PPelvis", 0.15), (0, 0, 0.93), (1.12, 0.74, 0.72))

    for sx, nm in ((-1, "L"), (1, "R")):
        hip = (sx * 0.085, 0, 0.9)
        if pose == "walk" and sx == 1:         # near leg forward, heel strike
            knee, ankle = (0.09, 0.17, 0.515), (0.095, 0.27, 0.09)
            heel, toe = (0.095, 0.245, 0.05), (0.10, 0.42, 0.07)
        elif pose == "walk":                   # far leg back, heel lifting
            knee, ankle = (-0.09, -0.10, 0.50), (-0.095, -0.30, 0.13)
            heel, toe = (-0.095, -0.33, 0.14), (-0.10, -0.17, 0.045)
        else:
            knee, ankle = (sx * 0.09, 0.012, 0.5), (sx * 0.095, -0.005, 0.085)
            heel, toe = (sx * 0.095, -0.03, 0.045), (sx * 0.10, 0.15, 0.04)
        seg("Thigh" + nm, hip, knee, 0.074)
        seg("Calf" + nm, knee, ankle, 0.056)
        seg("Foot" + nm, heel, toe, 0.044)

    for sx, nm in ((-1, "L"), (1, "R")):
        sh = SHOULDER(sx)
        if pose == "present":                  # both hands raised in front, holding an invisible item
            elbow, wrist = two_bone_ik(sh, HANDS_PRESENT[sx], 0.29, 0.265, (sx * 0.6, -0.35, -1.0))
            hand_scale = (0.5, 1.1, 0.95)
        elif pose == "walk" and sx == -1:      # far arm swings forward (opposite to the near leg)
            elbow, wrist = Vector((-0.235, 0.11, 1.135)), Vector((-0.235, 0.27, 0.94))
            hand_scale = (0.5, 0.9, 1.1)
        elif pose == "walk":                   # near arm swings back
            elbow, wrist = Vector((0.24, -0.09, 1.13)), Vector((0.245, -0.2, 0.905))
            hand_scale = (0.5, 0.9, 1.1)
        else:                                  # relaxed at the sides
            elbow, wrist = Vector((sx * 0.245, -0.01, 1.125)), Vector((sx * 0.25, 0.035, 0.865))
            hand_scale = (0.5, 0.85, 1.15)
        seg("UpperArm" + nm, sh, elbow, 0.047)
        seg("Forearm" + nm, elbow, wrist, 0.04)
        part("Hand" + nm, m_sphere("PHand", 0.046), wrist, hand_scale)
    return coll, root


POSES = {p: build_pose(p) for p in ("idle", "present", "walk")}
bpy.context.view_layer.update()
ROOT_MW = POSES["present"][1].matrix_world.copy()


def person_world(local):
    return ROOT_MW @ Vector(local)


# ----------------------------------------------------------------------------- states
def show_pose(pose):
    for name, (coll, _root) in POSES.items():
        coll.hide_render = (name != pose)
        coll.hide_viewport = (name != pose)


def stage_state(lit, pose=None):
    """Station + room only: screen off, one bin (or none) lit, optional person pose."""
    B["set_state"]("IDLE", lit, person=False, box_open=0, fx=False)
    for c in B["SCREENS"].values():            # screen OFF: plain dark glass, the web page draws the content
        c.hide_render = True
        c.hide_viewport = True
    show_pose(pose)


FLOOR = bpy.data.objects["Env_Floor"]
PERSON_OBJS = set(ob for coll, _r in POSES.values() for ob in coll.objects)


def sprite_mode(on):
    """Sprites: transparent film, only the person plus the floor as a shadow catcher. Everything else is
    hidden, otherwise the catcher would also record the station's own shadows a second time."""
    scene.render.film_transparent = on
    scene.render.use_compositing = not on
    FLOOR.is_shadow_catcher = on
    for ob in scene.objects:
        if ob in PERSON_OBJS or ob is FLOOR or ob.type in {"CAMERA", "LIGHT", "EMPTY"}:
            continue
        if on:
            ob["_was_hidden"] = bool(ob.hide_render)
            ob.hide_render = True
        elif "_was_hidden" in ob:
            ob.hide_render = bool(ob["_was_hidden"])
            del ob["_was_hidden"]


def clean_sprite(arr, feet_px, px_per_m):
    """Keep the person untouched; keep the shadow only as a soft contact shadow around the feet."""
    h, w = arr.shape[:2]
    rgb_max = arr[..., :3].max(axis=2)
    alpha = arr[..., 3]
    shadow = rgb_max < 0.08                                   # the catcher writes pure black + alpha
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    fy = (h - 1) - feet_px[1]                                 # rows are bottom-up
    d = np.sqrt((xx - feet_px[0]) ** 2 + ((yy - fy) / 0.5) ** 2) / px_per_m      # ~metres on the floor
    fade = np.clip((2.0 - d) / (2.0 - 1.0), 0.0, 1.0)
    fade = fade * fade * (3.0 - 2.0 * fade)
    a2 = np.where(shadow, alpha * fade, alpha)
    a2 = np.where(shadow & (a2 < 2.5 / 255.0), 0.0, a2)        # drop render noise in the empty area
    out = arr.copy()
    out[..., 3] = a2
    out[..., :3] = np.where((a2 > 0)[..., None], arr[..., :3], 0.0)
    return out


# ----------------------------------------------------------------------------- render + image helpers
def render_png(path, res_scale=1.0, rgba=False, samples=None, threshold=None):
    scene.render.resolution_x, scene.render.resolution_y = int(W * res_scale), int(H * res_scale)
    scene.render.resolution_percentage = 100
    ims = scene.render.image_settings
    ims.file_format = "PNG"
    ims.color_mode = "RGBA" if rgba else "RGB"
    scene.cycles.seed = 0
    scene.cycles.use_animated_seed = False
    if samples:
        scene.cycles.samples = samples
    if threshold:
        scene.cycles.adaptive_threshold = threshold
    bpy.ops.render.render(write_still=False)
    img = bpy.data.images["Render Result"]
    for attempt in range(6):
        try:
            img.save_render(path, scene=scene)
            break
        except Exception as e:
            print("SHOWCASE: save retry", attempt + 1, str(e)[:120])
            time.sleep(1.5)
    print("SHOWCASE: rendered", path)
    return path


def load_img(path):
    """8-bit image as float array [rows bottom-up, cols, 4] in display (sRGB) values."""
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    arr = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    bpy.data.images.remove(img)
    return arr.reshape(h, w, 4)


def save_img(arr, path, fmt, quality=92):
    h, w = arr.shape[:2]
    img = bpy.data.images.new("showcase_out", w, h, alpha=(fmt == "PNG"))
    img.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel())
    img.filepath_raw = path
    img.file_format = fmt
    for attempt in range(6):
        try:
            img.save(quality=quality)
            break
        except Exception as e:
            print("SHOWCASE: save retry", attempt + 1, str(e)[:120])
            time.sleep(1.5)
    bpy.data.images.remove(img)
    print("SHOWCASE: wrote", path)


def box_blur(a, r):
    for axis in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (r + 1, r)
        c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
        n = a.shape[axis]
        if axis == 0:
            a = (c[2 * r + 1:2 * r + 1 + n, :] - c[:n, :]) / (2 * r + 1)
        else:
            a = (c[:, 2 * r + 1:2 * r + 1 + n] - c[:, :n]) / (2 * r + 1)
        a = a.astype(np.float32)
    return a


def key_merge(idle, lit):
    """Keep the idle plate bit-for-bit wherever the bin light changes nothing; blend to the lit render only
    where it really differs, so a cross-fade between plates cannot flicker anywhere else."""
    d = np.abs(lit[..., :3] - idle[..., :3]).max(axis=2)
    d = box_blur(box_blur(d, 4), 4)
    m = np.clip((d - 1.0 / 255.0) / (3.5 / 255.0), 0.0, 1.0)
    m = (m * m * (3.0 - 2.0 * m))[..., None]
    out = idle.copy()
    out[..., :3] = idle[..., :3] * (1.0 - m) + lit[..., :3] * m
    return out, float((m > 0).mean())


def alpha_over(bg, fg):
    a = fg[..., 3:4]
    out = bg.copy()
    out[..., :3] = fg[..., :3] * a + bg[..., :3] * (1.0 - a)
    out[..., 3] = 1.0
    return out


def draw_dot(arr, x, y, color, r=9):
    h, w = arr.shape[:2]
    row, col = h - 1 - int(round(y)), int(round(x))
    for rad, colr in ((r + 3, (0.0, 0.0, 0.0)), (r, color)):
        yy, xx = np.ogrid[-rad:rad + 1, -rad:rad + 1]
        mask = xx * xx + yy * yy <= rad * rad
        r0, r1, c0, c1 = max(row - rad, 0), min(row + rad + 1, h), max(col - rad, 0), min(col + rad + 1, w)
        if r0 >= r1 or c0 >= c1:
            continue
        sub = mask[r0 - (row - rad):r1 - (row - rad), c0 - (col - rad):c1 - (col - rad)]
        arr[r0:r1, c0:c1, :3][sub] = colr


# ----------------------------------------------------------------------------- anchors
def project(p, res_scale=1.0):
    scene.render.resolution_x, scene.render.resolution_y = int(W * res_scale), int(H * res_scale)
    v = world_to_camera_view(scene, cam, Vector(p))
    return [round(v.x * W * res_scale, 1), round((1.0 - v.y) * H * res_scale, 1)], v.z


def anchors(res_scale=1.0):
    head, screen = B["head"], B["screen"]
    sw, sh = B["SCREEN_W"] / 2.0, B["SCREEN_H"] / 2.0
    smw = screen.matrix_world
    quad = [project(smw @ Vector(c), res_scale)[0] for c in ((-sw, sh, 0), (sw, sh, 0), (sw, -sh, 0), (-sw, -sh, 0))]
    data = {"size": [int(W * res_scale), int(H * res_scale)], "screen": {"quad": quad},
            "lens": project(head.matrix_world @ Vector((0, -0.094, 0.006)), res_scale)[0],
            "head": project(head.matrix_world @ Vector((0, 0.151, -0.026)), res_scale)[0], "bins": {}}
    for key in ("recycle", "compost", "landfill"):
        face = bpy.data.objects["Bin_%s_FaceFrame" % key.capitalize()]
        pts = [project(face.matrix_world @ Vector((x, y, 0.0)), res_scale)[0] for x, y in B["opening_outline"](key)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        data["bins"][key] = {
            "opening": [round((max(xs) + min(xs)) / 2, 1), round((max(ys) + min(ys)) / 2, 1)],
            "opening_rx": round((max(xs) - min(xs)) / 2, 1), "opening_ry": round((max(ys) - min(ys)) / 2, 1),
            "front": project((B["BIN_X"][key], -0.225, 0.40), res_scale)[0]}
    hands_mid = person_world((HANDS_PRESENT[-1] + HANDS_PRESENT[1]) / 2.0)
    hands_px, hands_depth = project(hands_mid, res_scale)
    focal_px = cam.data.lens / cam.data.sensor_width * W * res_scale
    data["person"] = {"feet": project(person_world((0, 0.06, 0.0)), res_scale)[0],
                      "head_top": project(person_world((0, 0.01, 1.615 + 0.105 * 1.08)), res_scale)[0],
                      "hands": hands_px, "px_per_m_at_hands": round(focal_px / hands_depth, 1)}
    data["zone"] = project(ZONE, res_scale)[0]
    return data


def draw_anchors(arr, data):
    red, yellow, cyan, mag, green, white = (1, 0.1, 0.1), (1, 0.9, 0.1), (0.1, 0.9, 1), (1, 0.2, 0.9), (0.2, 1, 0.3), (1, 1, 1)
    for p in data["screen"]["quad"]:
        draw_dot(arr, p[0], p[1], yellow, 6)
    draw_dot(arr, *data["lens"], cyan, 6)
    draw_dot(arr, *data["head"], mag, 6)
    for b in data["bins"].values():
        cx, cy = b["opening"]
        draw_dot(arr, cx, cy, red)
        for dx, dy in ((b["opening_rx"], 0), (-b["opening_rx"], 0), (0, b["opening_ry"]), (0, -b["opening_ry"])):
            draw_dot(arr, cx + dx, cy + dy, white, 4)
        draw_dot(arr, *b["front"], green)
    draw_dot(arr, *data["person"]["feet"], cyan)
    draw_dot(arr, *data["person"]["head_top"], mag)
    draw_dot(arr, *data["person"]["hands"], yellow)
    draw_dot(arr, *data["zone"], red, 6)


print("SHOWCASE: camera pos (%.3f, %.3f, %.3f) target (%.2f, %.2f, %.2f) lens %.0f mm, azimuth %.0f deg; "
      "zone (%.2f, %.2f) yaw %.1f deg" % (CAM_POS.x, CAM_POS.y, CAM_POS.z, CAM_TARGET.x, CAM_TARGET.y, CAM_TARGET.z,
                                         CAM_LENS, CAM_AZIMUTH, ZONE.x, ZONE.y, degrees(YAW)))

# ============================================================================= steps
if "frame" in STEPS:                 # quick framing / occlusion checks (station + person together)
    k = 0.5
    data = anchors(k)
    for pose in ("present", "idle", "walk"):
        stage_state("compost", pose)
        path = render_png(os.path.join(TMP, "frame_%s.png" % pose), k, samples=40, threshold=0.08)
        if pose == "present":
            arr = load_img(path)
            draw_anchors(arr, data)
            save_img(arr, os.path.join(TMP, "frame_present_dots.png"), "PNG")
    print("SHOWCASE: anchors (half res)", json.dumps(data))

if "plates" in STEPS:
    names = {None: "idle", "recycle": "lit_recycle", "compost": "lit_compost", "landfill": "lit_landfill"}
    raw = {}
    for lit, nm in names.items():
        stage_state(lit, None)
        raw[lit] = load_img(render_png(os.path.join(TMP, "plate_%s.png" % nm), K, samples=384 if K == 1.0 else 64,
                                       threshold=0.012 if K == 1.0 else 0.05))
    save_img(raw[None], os.path.join(DEST, "stage_idle.jpg"), "JPEG", 92)
    for lit in ("recycle", "compost", "landfill"):
        merged, frac = key_merge(raw[None], raw[lit])
        print("SHOWCASE: %s differs from idle on %.1f%% of the picture" % (names[lit], frac * 100))
        save_img(merged, os.path.join(DEST, "stage_%s.jpg" % names[lit]), "JPEG", 92)

if "sprites" in STEPS:
    stage_state(None, None)
    sprite_mode(True)
    for pose in ("idle", "present", "walk"):
        show_pose(pose)
        raw_path = render_png(os.path.join(TMP, "sprite_%s_raw.png" % pose), K, rgba=True,
                              samples=256 if K == 1.0 else 64, threshold=0.015 if K == 1.0 else 0.05)
        a = anchors(K)["person"]
        save_img(clean_sprite(load_img(raw_path), a["feet"], a["px_per_m_at_hands"]),
                 os.path.join(DEST, "person_%s.png" % pose), "PNG")
    sprite_mode(False)

if "json" in STEPS or "check" in STEPS:
    data = anchors(K)
    with open(os.path.join(DEST, "stage.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    print("SHOWCASE: stage.json", json.dumps(data))

if "check" in STEPS:
    bg = load_img(os.path.join(DEST, "stage_lit_compost.jpg"))
    fg = load_img(os.path.join(DEST, "person_present.png"))
    comp = alpha_over(bg, fg)
    draw_anchors(comp, data)
    save_img(comp, os.path.join(DEST, "_check_composite.jpg"), "JPEG", 90)

print("SHOWCASE: done")
