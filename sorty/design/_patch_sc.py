p = 'render_showcase.py'
s = open(p, encoding='utf-8').read()
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, ("COUNT", s.count(a), a[:80])
    s = s.replace(a, b)
a0 = s.index('def sprite_mode(on):')
a1 = s.index('# ----------------------------------------------------------------------------- render + image helpers')
s = s[:a0] + '''def sprite_mode(on):
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


''' + s[a1:]
rep('''        render_png(os.path.join(DEST, "person_%s.png" % pose), K, rgba=True, samples=256 if K == 1.0 else 64,
                   threshold=0.015 if K == 1.0 else 0.05)
    sprite_mode(False)''', '''        raw_path = render_png(os.path.join(TMP, "sprite_%s_raw.png" % pose), K, rgba=True,
                              samples=256 if K == 1.0 else 64, threshold=0.015 if K == 1.0 else 0.05)
        a = anchors(K)["person"]
        save_img(clean_sprite(load_img(raw_path), a["feet"], a["px_per_m_at_hands"]),
                 os.path.join(DEST, "person_%s.png" % pose), "PNG")
    sprite_mode(False)''')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print("patched OK")
