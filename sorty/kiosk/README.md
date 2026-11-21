# Sorty kiosk (screen + voice)

The page a small screen on the bin shows. Plain HTML/CSS/JS: no build step, no downloads, works offline.

## Run it

- With the Sorty server: open `http://localhost:8787/` (the server serves this folder and the `/api/*` brain).
- Without any server: serve this folder with any static server, or open `index.html` directly. If `/api/config`
  does not answer, the page switches by itself to a built-in practice brain (scripted answers) so every screen can
  still be shown. A `PRACTICE` badge appears next to the name whenever answers are scripted.

For a real kiosk, start Chrome or Edge like this so sound, camera and microphone work without a first tap:

```
chrome --kiosk --autoplay-policy=no-user-gesture-required --use-fake-ui-for-media-stream http://localhost:8787/
```

Edge has the most natural built-in voices on Windows.

## Keys (for staff and demos)

| Key | What it does |
| --- | --- |
| Space | Scan now / "Done" on a show-me-again screen / close a verdict early |
| M | Demo items (pick an item instead of using the camera; "Auto-play answers" and "Play all" live here) |
| 1-9 | Start demo item 1-9 |
| D | "How Sorty decided": the brain's steps with timings |
| Y / N / U | Answer Yes / No / Not sure |
| L | Switch language (English / Spanish) |
| S | Sound on / off (captions stay on) |
| F | Full screen |
| Esc | Close a panel, or cancel the current conversation |

## Address options

| Add to the address | Effect |
| --- | --- |
| `?mock=1` | Force the built-in practice brain |
| `?mock=1&bins=2` | Practice brain with a two-bin station |
| `?mock=1&slow=1` | Practice brain answering slowly (shows the "One moment..." waiting screen) |
| `?P_ON=0.12&STILL_MS=800` | Tune the automatic trigger (see below) |

## Automatic trigger (camera)

Sorty looks by itself when something is brought into view and then held still for about 0.65 s. If it triggers too
easily or not easily enough in your room, open "How Sorty decided" (D): the bottom line shows live motion and presence
numbers. Then adjust from the address bar:

- `P_ON` (default 0.09): how much of the picture must differ from the empty scene. Raise it if people walking far
  behind trigger scans.
- `M_OFF` (default 0.018): how still "still" is. Raise it in a busy place.
- `STILL_MS` (default 650): how long the item must be held still.

The Scan button and the Space key always work, whatever the trigger does.

## Files

- `index.html`, `css/styles.css`
- `js/app.js` screen logic, `js/api.js` server calls, `js/mock.js` practice brain, `js/camera.js` camera and motion,
  `js/voice.js` speech, listening and sounds, `js/i18n.js` texts (EN/ES), `js/icons.js` icons and pictograms
