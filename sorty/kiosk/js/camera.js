/* Sorty kiosk - camera, frame capture and simple motion sensing.
   The preview is mirrored (like a selfie) with CSS only; frames sent to the brain are
   NOT mirrored, so printed text and recycling codes stay readable. */
(function () {
  'use strict';

  /* Tunables. Any of them can be overridden from the URL, e.g. ?P_ON=0.12&STILL_MS=800 */
  var T = {
    interval: 150,   // ms between motion samples
    pix: 22,         // grey-level change that counts as "this pixel changed"
    M_ON: 0.05,      // share of pixels changing between samples that counts as movement
    M_OFF: 0.018,    // below this the view counts as holding still
    P_ON: 0.09,      // share of pixels that must differ from the empty scene (something is there)
    P_LAST: 0.05,    // ...and from the scene at the end of the last interaction (it is something new)
    STILL_MS: 650,   // how long the item must be held still before a capture
    BURST_MS: 4500,  // movement must have happened this recently (something was brought in)
    LEARN_MS: 9000   // a view that stays still this long becomes the new "empty scene"
  };
  try {
    var q = new URLSearchParams(window.location.search);
    Object.keys(T).forEach(function (k) {
      if (q.has(k)) { var v = parseFloat(q.get(k)); if (isFinite(v)) T[k] = v; }
    });
  } catch (e) { /* ignore */ }

  var W = 64, H = 48, N = W * H;
  var small = document.createElement('canvas');
  small.width = W; small.height = H;
  var sctx = small.getContext('2d', { willReadFrequently: true });

  var video = null, stream = null, live = false, timer = null;
  var prev = null, bgEmpty = null, bgLast = null;
  var stillSince = 0, lastBurst = -1e9, startedAt = 0;
  var listeners = [];
  var metrics = { motion: 0, presEmpty: 0, presLast: 0, stillMs: 0, sinceBurst: 1e9 };

  function sample() {
    sctx.drawImage(video, 0, 0, W, H);
    var d = sctx.getImageData(0, 0, W, H).data;
    var g = new Float32Array(N), sum = 0;
    for (var i = 0, j = 0; i < N; i++, j += 4) {
      var v = (d[j] * 77 + d[j + 1] * 150 + d[j + 2] * 29) >> 8;
      g[i] = v; sum += v;
    }
    g.mean = sum / N;
    return g;
  }

  /* Share of pixels that differ. Each frame is compared after removing its average
     brightness, so the camera's auto-exposure shifting does not look like movement. */
  function frac(a, b) {
    if (!a || !b) return 0;
    var da = a.mean || 0, db = b.mean || 0, thr = T.pix, c = 0;
    for (var i = 0; i < N; i++) {
      var x = (a[i] - da) - (b[i] - db);
      if (x > thr || x < -thr) c++;
    }
    return c / N;
  }

  function tick() {
    if (!live || !video || video.readyState < 2 || document.hidden) return;
    var now = performance.now(), cur;
    try { cur = sample(); } catch (e) { return; }
    var motion = prev ? frac(cur, prev) : 0;
    prev = cur;
    if (motion >= T.M_ON) lastBurst = now;
    if (motion > T.M_OFF) stillSince = now;
    var stillMs = now - stillSince;

    if (!bgEmpty) {
      if (now - startedAt > 1500 && stillMs > 1200) bgEmpty = copy(cur);
    } else if (stillMs > T.LEARN_MS) {
      var s = 0;
      for (var i = 0; i < N; i++) { bgEmpty[i] += (cur[i] - bgEmpty[i]) * 0.1; s += bgEmpty[i]; }
      bgEmpty.mean = s / N;
    }

    metrics.motion = motion;
    metrics.presEmpty = bgEmpty ? frac(cur, bgEmpty) : 1;
    metrics.presLast = bgLast ? frac(cur, bgLast) : 1;
    metrics.stillMs = stillMs;
    metrics.sinceBurst = now - lastBurst;
    for (var k = 0; k < listeners.length; k++) {
      try { listeners[k](metrics); } catch (e) { console.error(e); }
    }
  }

  function copy(g) { var c = new Float32Array(g); c.mean = g.mean; return c; }

  function start(videoEl) {
    video = videoEl;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return Promise.resolve(false);
    var req = navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { width: { ideal: 1280 }, height: { ideal: 720 } }   // rear or any camera: whatever the device has
    }).then(function (s) {
      stream = s;
      video.srcObject = s;
      var p = video.play();
      return (p && p.catch) ? p.catch(function () {}) : null;
    }).then(function () {
      live = true;
      startedAt = performance.now();
      stillSince = startedAt;
      if (!timer) timer = setInterval(tick, T.interval);
      var track = stream.getVideoTracks()[0];
      if (track) track.addEventListener('ended', function () { live = false; notifyState(); });
      notifyState();
      return true;
    }).catch(function () {
      live = false;
      return false;
    });
    return req;
  }

  var stateListeners = [];
  function notifyState() { stateListeners.forEach(function (fn) { try { fn(live); } catch (e) { console.error(e); } }); }

  /* Capture the current camera frame: JPEG, long edge <= maxEdge. */
  function grab(maxEdge, quality) {
    if (!live || !video || !video.videoWidth) return null;
    return toFrame(video, video.videoWidth, video.videoHeight, maxEdge || 1280, quality || 0.85);
  }

  function toFrame(src, sw, sh, maxEdge, quality) {
    var s = Math.min(1, maxEdge / Math.max(sw, sh));
    var w = Math.max(1, Math.round(sw * s)), h = Math.max(1, Math.round(sh * s));
    var c = document.createElement('canvas');
    c.width = w; c.height = h;
    c.getContext('2d').drawImage(src, 0, 0, w, h);
    var url = c.toDataURL('image/jpeg', quality);
    return { b64: url.slice(url.indexOf(',') + 1), canvas: c, w: w, h: h };
  }

  /* Turn an image URL / data URL into the same frame shape (used by demo mode). */
  function imageToFrame(src, maxEdge, quality) {
    return new Promise(function (resolve, reject) {
      var img = new Image();
      img.onload = function () {
        try { resolve(toFrame(img, img.naturalWidth, img.naturalHeight, maxEdge || 1280, quality || 0.85)); }
        catch (e) { reject(e); }
      };
      img.onerror = function () { reject(new Error('Could not load image ' + String(src).slice(0, 80))); };
      img.src = src;
    });
  }

  window.Sorty = window.Sorty || {};
  window.Sorty.camera = {
    tune: T,
    start: start,
    isLive: function () { return live; },
    grab: grab,
    imageToFrame: imageToFrame,
    onTick: function (fn) { listeners.push(fn); },
    onState: function (fn) { stateListeners.push(fn); },
    metrics: function () { return metrics; },
    /* Remember the scene as it is now; the next trigger needs something different from it. */
    snapshotLast: function () { bgLast = prev ? copy(prev) : null; },
    /* Reference + comparison used while waiting for the person to "show me again". */
    reference: function () { return prev ? copy(prev) : null; },
    diffFrom: function (ref) { return (ref && prev) ? frac(prev, ref) : 1; }
  };
})();
