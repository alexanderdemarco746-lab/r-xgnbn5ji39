/* Sorty virtual prototype.
   The scene is built from Blender renders: an idle plate, one plate per lit bin, person poses and item cut-outs.
   The screen beside it is the real kiosk app in an iframe. This page listens to what the kiosk sends to and
   receives from the brain, and animates the scene to match. It never decides anything itself. */
(function () {
  'use strict';

  var $ = function (id) { return document.getElementById(id); };
  var sleep = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  var S = {
    cfg: null, stage: null, base: '', W: 2560, H: 1440,
    scenarios: [], byId: {}, items: {}, bins: {},
    kiosk: null, kioskReady: false,
    run: null, seq: 0, autoplay: true, sound: true, tour: null, live: false,
    hasPoses: false, litOk: {}
  };

  var TOUR = ['pizza_box_greasy', 'soda_can_liquid', 'clear_bottle_half_full', 'cup_compostable', 'battery_aa'];
  var ORDER = ['pizza_box_greasy', 'pizza_box_clean', 'soda_can_liquid', 'soda_can_empty', 'clear_bottle_half_full',
    'clear_bottle_empty', 'cup_compostable', 'cup_pet', 'clamshell_food', 'coffee_cup_liquid', 'battery_aa',
    'spray_can_not_empty', 'spray_can_empty', 'chip_bag', 'banana_peel', 'greasy_napkin', 'two_items'];

  /* ---------------------------------------------------------------- loading */
  function getJSON(url) {
    return fetch(url, { cache: 'no-store' }).then(function (r) { if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); });
  }
  function loadImg(img, url) {
    return new Promise(function (resolve) {
      img.onload = function () { resolve(true); };
      img.onerror = function () { resolve(false); };
      img.src = url;
    });
  }
  function keyOf(url) { return String(url || '').split('/').pop().replace(/\.[a-z]+$/i, ''); }

  function init() {
    var stageP = getJSON('assets/stage/stage.json').then(function (j) { S.base = 'assets/stage/'; return j; })
      .catch(function () { return getJSON('assets/stage_dev/stage.json').then(function (j) { S.base = 'assets/stage_dev/'; return j; }); });
    Promise.all([
      getJSON('/api/config'),
      stageP,
      getJSON('assets/items/items.json').catch(function () { return {}; }),
      getJSON('/api/demo/scenarios').catch(function () { return []; })
    ]).then(function (r) {
      S.cfg = r[0]; S.stage = r[1]; S.items = r[2] || {}; S.scenarios = r[3] || [];
      S.scenarios.forEach(function (s) { S.byId[s.id] = s; });
      S.cfg.station.bins.forEach(function (b) { S.bins[b.id] = b; });
      S.W = S.stage.size[0]; S.H = S.stage.size[1];
      setBadge();
      return buildStage();
    }).then(function () {
      buildTray();
      bootKiosk();
      fit();
      $('curtain').classList.add('gone');
    }).catch(function (err) {
      $('curtain').textContent = 'Could not load the showcase: ' + (err && err.message || err) + '. Is the Sorty server running?';
    });
  }

  function setBadge() {
    var b = $('modeBadge');
    if (S.cfg.mode === 'live') { b.textContent = 'Live AI: ' + (S.cfg.model || 'Claude'); b.className = 'badge live'; }
    else { b.textContent = 'Practice mode: scripted answers, no AI key'; b.className = 'badge practice'; }
    b.hidden = false;
  }

  function buildStage() {
    var w = $('world');
    w.style.width = S.W + 'px'; w.style.height = S.H + 'px';
    var jobs = [
      loadImg($('plateIdle'), S.base + 'stage_idle.jpg'),
      loadImg($('plateRecycle'), S.base + 'stage_lit_recycle.jpg').then(function (ok) { S.litOk.recycle = ok; }),
      loadImg($('plateCompost'), S.base + 'stage_lit_compost.jpg').then(function (ok) { S.litOk.compost = ok; }),
      loadImg($('plateLandfill'), S.base + 'stage_lit_landfill.jpg').then(function (ok) { S.litOk.landfill = ok; }),
      Promise.all([
        loadImg($('poseWalk'), S.base + 'person_walk.png'),
        loadImg($('poseIdle'), S.base + 'person_idle.png'),
        loadImg($('posePresent'), S.base + 'person_present.png')
      ]).then(function (oks) { S.hasPoses = oks[1] && oks[2]; if (!oks[0]) $('poseWalk').src = $('poseIdle').src; })
    ];
    return Promise.all(jobs).then(function () {
      placeMini();
      if (!S.hasPoses) {                       // no renders yet: a plain stand-in figure
        var d = $('personDev'), f = S.stage.person.feet;
        d.hidden = false; d.style.left = f[0] + 'px'; d.style.top = (f[1] - 925) + 'px';
      }
      $('fx').setAttribute('viewBox', '0 0 ' + S.W + ' ' + S.H);
    });
  }

  /* Fit the 2560x1440 world into the viewport box, centred, never cropped. */
  function fit() {
    var v = $('viewport'), k = Math.min(v.clientWidth / S.W, v.clientHeight / S.H);
    if (!isFinite(k) || k <= 0) return;
    var ox = (v.clientWidth - S.W * k) / 2, oy = (v.clientHeight - S.H * k) / 2;
    $('world').style.transform = 'translate(' + ox + 'px,' + oy + 'px) scale(' + k + ')';
    var wrap = $('kioskWrap'), kk = wrap.clientWidth / 1280;
    $('kiosk').style.transform = 'scale(' + kk + ')';
    wrap.style.height = Math.round(800 * kk) + 'px';
  }
  window.addEventListener('resize', fit);
  if (window.ResizeObserver) new ResizeObserver(fit).observe($('viewport'));

  /* Map the 320x190 mini screen onto the display's four corners in the picture (a projective warp). */
  function placeMini() {
    var q = S.stage.screen && S.stage.screen.quad, el = $('mini');
    if (!q || q.length !== 4) { el.hidden = true; return; }
    var w = 320, h = 190;
    var src = [[0, 0], [w, 0], [w, h], [0, h]], A = [], b = [];
    for (var i = 0; i < 4; i++) {
      var x = src[i][0], y = src[i][1], u = q[i][0], v = q[i][1];
      A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.push(u);
      A.push([0, 0, 0, x, y, 1, -v * x, -v * y]); b.push(v);
    }
    var hh = solve(A, b);
    if (!hh) { el.hidden = true; return; }
    el.style.transform = 'matrix3d(' + [hh[0], hh[3], 0, hh[6], hh[1], hh[4], 0, hh[7], 0, 0, 1, 0, hh[2], hh[5], 0, 1].join(',') + ')';
  }
  function solve(A, b) {                       // Gaussian elimination, 8 unknowns
    var n = b.length, i, j, k;
    for (i = 0; i < n; i++) A[i] = A[i].concat([b[i]]);
    for (i = 0; i < n; i++) {
      var p = i;
      for (j = i + 1; j < n; j++) if (Math.abs(A[j][i]) > Math.abs(A[p][i])) p = j;
      if (Math.abs(A[p][i]) < 1e-9) return null;
      var t = A[i]; A[i] = A[p]; A[p] = t;
      for (j = i + 1; j < n; j++) { var f = A[j][i] / A[i][i]; for (k = i; k <= n; k++) A[j][k] -= f * A[i][k]; }
    }
    var x = new Array(n);
    for (i = n - 1; i >= 0; i--) { var s = A[i][n]; for (j = i + 1; j < n; j++) s -= A[i][j] * x[j]; x[i] = s / A[i][i]; }
    return x;
  }

  /* ---------------------------------------------------------------- scene pieces */
  function mini(state, binId) {
    var el = $('mini');
    el.dataset.state = state;
    if (state === 'verdict' && S.bins[binId]) {
      var b = S.bins[binId];
      el.style.setProperty('--binc', b.color);
      $('miniWord').textContent = (b.label.en || b.id).toUpperCase();
      var rot = b.position === 'left' ? 45 : b.position === 'right' ? -45 : 0;      // point at the real bin below the screen
      $('miniArrow').innerHTML = '<svg viewBox="0 0 100 100" style="transform:rotate(' + rot + 'deg)"><path fill="#fff" d="M38 6h24v48h22L50 96 16 54h22z"/></svg>';
    }
  }

  function lit(binId, alert) {
    ['Recycle', 'Compost', 'Landfill'].forEach(function (n) { $('plate' + n).classList.toggle('on', n.toLowerCase() === binId && !!S.litOk[binId]); });
    var g = $('glow');
    var needGlow = (binId && !S.litOk[binId]) || alert;
    g.hidden = !needGlow;
    g.classList.toggle('alert', !!alert);
    if (needGlow) {
      var at = alert ? S.stage.head : S.stage.bins[binId].front;
      g.style.left = at[0] + 'px'; g.style.top = at[1] + 'px';
      if (!alert) g.style.setProperty('--glow', S.bins[binId].color === '#24292F' ? '#DCE6F2' : S.bins[binId].color);
    }
  }

  function pose(name) {
    ['Walk', 'Idle', 'Present'].forEach(function (n) { $('pose' + n).classList.toggle('on', S.hasPoses && n.toLowerCase() === name); });
    $('personDev').classList.toggle('present', name === 'present');
  }

  var ENTER = 1250;
  /* Run a Web Animation, but never let the story hang on it: a browser may pause animations in a hidden tab. */
  function play(el, frames, opts) {
    var a = el.animate(frames, opts), ms = (typeof opts === 'number' ? opts : opts.duration) || 0;
    return Promise.race([a.finished.catch(function () {}), sleep(ms + 180)]);
  }
  function slide(el, base, dx, entering) {
    // a short walk: slide along the floor with a small bob, so a still figure reads as walking
    var frames = [], steps = 6;
    for (var i = 0; i <= steps; i++) {
      var p = i / steps, x = entering ? -dx * (1 - p) : -dx * p, y = (i % 2 ? -14 : 0);
      var o = entering ? Math.min(1, p * 4) : Math.min(1, (1 - p) * 4);
      frames.push({ transform: base + ' translate(' + x + 'px,' + y + 'px)', opacity: o, offset: p });
    }
    return play(el, frames, { duration: ENTER, easing: 'ease-in-out', fill: 'both' });
  }
  function walkDistance() { return S.stage.person.feet[0] + 420; }
  function personEnter() {
    var p = $('person'); p.classList.remove('off'); pose('walk');
    var jobs = [slide(p, '', walkDistance(), true)];
    if (!$('item').hidden) jobs.push(slide($('item'), 'translate(-50%,-50%)', walkDistance(), true));
    return Promise.all(jobs).then(function () { clearAnim(p); clearAnim($('item')); });
  }
  function personExit(withItem) {
    var p = $('person'); pose('walk');
    var jobs = [slide(p, '', walkDistance(), false)];
    if (withItem && !$('item').hidden) jobs.push(slide($('item'), 'translate(-50%,-50%)', walkDistance(), false));
    return Promise.all(jobs).then(function () { p.classList.add('off'); clearAnim(p); $('item').hidden = true; clearAnim($('item')); });
  }
  function clearAnim(el) { el.getAnimations().forEach(function (a) { a.cancel(); }); }

  /* What the person holds: a cut-out when one exists, otherwise a photo card of the camera frame. */
  function setItem(el, key, photoUrl) {
    var img = el.querySelector('img'), meta = S.items[key], hands = S.stage.person.hands, ppm = S.stage.person.px_per_m_at_hands || 480;
    var w, h;
    if (meta) {
      h = Math.max(110, Math.min(560, (meta.height_m || 0.25) * ppm));
      w = h * (meta.w / meta.h);
      if (w > 760) { h *= 760 / w; w = 760; }
      el.classList.remove('card'); img.src = 'assets/items/' + meta.file;
    } else {
      w = 330; h = 248; el.classList.add('card'); img.src = photoUrl || '';
    }
    el.style.width = w + 'px'; el.style.height = h + 'px';
    el.style.left = hands[0] + 'px'; el.style.top = hands[1] + 'px';
    el.style.opacity = 1; el.hidden = !(meta || photoUrl);
    el._h = h; el._w = w;
  }
  function itemLower(on) {                       // carried low while walking, raised to the camera when presenting
    var el = $('item'), hands = S.stage.person.hands, ppm = S.stage.person.px_per_m_at_hands || 480;
    el.style.transition = 'top .35s ease';
    el.style.top = (hands[1] + (on ? 0.32 * ppm : 0)) + 'px';
  }
  function itemSwap(key, photoUrl) {
    var el = $('item');
    return play(el, [{ transform: 'translate(-50%,-50%) scaleX(1)' }, { transform: 'translate(-50%,-50%) scaleX(0.04)' }], { duration: 230, easing: 'ease-in' })
      .then(function () {
        setItem(el, key, photoUrl); aimBeam();
        return play(el, [{ transform: 'translate(-50%,-50%) scaleX(0.04)' }, { transform: 'translate(-50%,-50%) scaleX(1)' }], { duration: 260, easing: 'ease-out' });
      });
  }
  function itemWiggle() {
    return play($('item'), [{ transform: 'translate(-50%,-50%) rotate(0)' }, { transform: 'translate(-50%,-50%) rotate(-9deg)' },
      { transform: 'translate(-50%,-50%) rotate(8deg)' }, { transform: 'translate(-50%,-50%) rotate(0)' }], { duration: 700 });
  }
  function itemPour() {
    return play($('item'), [{ transform: 'translate(-50%,-50%) rotate(0)' }, { transform: 'translate(-50%,-50%) rotate(115deg)', offset: .3 },
      { transform: 'translate(-50%,-50%) rotate(115deg)', offset: .75 }, { transform: 'translate(-50%,-50%) rotate(0)' }], { duration: 1500, easing: 'ease-in-out' });
  }
  function itemDrop(el, binId) {
    var to = S.stage.bins[binId].opening, x0 = parseFloat(el.style.left), y0 = parseFloat(el.style.top);
    var dx = to[0] - x0, dy = to[1] - y0, lift = Math.max(180, Math.abs(dx) * 0.28);
    var base = 'translate(-50%,-50%) ';
    var end = Math.max(0.16, Math.min(0.5, 150 / Math.max(el._w || 200, el._h || 200)));
    return play(el, [
      { transform: base + 'translate(0,0) scale(1) rotate(0)', opacity: 1, easing: 'cubic-bezier(.2,.7,.5,1)' },
      { transform: base + 'translate(' + dx * 0.5 + 'px,' + (Math.min(0, dy) * 0.5 - lift) + 'px) scale(.8) rotate(24deg)', opacity: 1, offset: .5, easing: 'cubic-bezier(.5,0,.8,.4)' },
      { transform: base + 'translate(' + dx + 'px,' + dy + 'px) scale(' + end + ') rotate(52deg)', opacity: 1, offset: .93 },
      { transform: base + 'translate(' + dx + 'px,' + (dy + 26) + 'px) scale(' + end * 0.7 + ') rotate(60deg)', opacity: 0 }
    ], { duration: 950, fill: 'forwards' }).then(function () {
      el.hidden = true; clearAnim(el);
      var r = $('ripple'), color = S.bins[binId].color === '#24292F' ? '#C9D4E3' : S.bins[binId].color;
      r.style.left = to[0] + 'px'; r.style.top = to[1] + 'px'; r.style.setProperty('--ripc', color);
      r.hidden = false; r.classList.remove('go'); void r.offsetWidth; r.classList.add('go');
    });
  }

  /* The camera's view cone: from the lens to the item, with corner brackets around what it is reading. */
  function aimBeam() {
    var el = $('item'); if (el.hidden) return;
    var cx = parseFloat(el.style.left), cy = parseFloat(el.style.top), w = (el._w || 240) / 2 + 26, h = (el._h || 240) / 2 + 26, L = S.stage.lens;
    $('beam').setAttribute('points', [L[0] + ',' + L[1], (cx - w) + ',' + (cy - h), (cx - w) + ',' + (cy + h), (cx + w) + ',' + (cy + h), (cx + w) + ',' + (cy - h)].join(' '));
    var c = 46, d = '';
    [[-1, -1], [1, -1], [1, 1], [-1, 1]].forEach(function (s) {
      var x = cx + s[0] * w, y = cy + s[1] * h;
      d += '<path d="M' + (x - s[0] * c) + ' ' + y + ' L' + x + ' ' + y + ' L' + x + ' ' + (y - s[1] * c) + '"/>';
    });
    $('brackets').innerHTML = d;
  }
  function beam(on) {
    if (on) aimBeam();
    $('beam').classList.toggle('on', !!on && !$('item').hidden);
    $('brackets').classList.toggle('on', !!on && !$('item').hidden);
  }

  var sayTimers = {};
  function say(who, text, ms) {
    var el = $(who === 'sorty' ? 'saySorty' : 'sayPerson');
    clearTimeout(sayTimers[who]);
    if (!text) { el.hidden = true; return; }
    var at = who === 'sorty' ? S.stage.head : S.stage.person.head_top;
    el.innerHTML = '';
    var tag = document.createElement('span'); tag.className = 'who'; tag.textContent = who === 'sorty' ? 'Sorty' : 'Person';
    el.appendChild(tag); el.appendChild(document.createTextNode(text));
    el.hidden = false; el.classList.remove('beside');
    var half = el.offsetWidth / 2, x = Math.max(half + 24, Math.min(S.W - half - 24, at[0]));
    var y = at[1] - 34;
    if (y - el.offsetHeight < 20) {                    // no room above: sit to the right of it, level with it
      el.classList.add('beside');
      var q = who === 'sorty' && S.stage.screen && S.stage.screen.quad;
      var right = q ? Math.max(q[1][0], q[2][0]) : at[0] + 120, mid = q ? (q[0][1] + q[3][1]) / 2 : at[1] + 120;
      x = Math.min(S.W - half - 24, right + 70 + half);
      y = Math.max(el.offsetHeight + 20, mid + el.offsetHeight / 2);
    }
    el.style.left = x + 'px'; el.style.top = y + 'px';
    if (ms) sayTimers[who] = setTimeout(function () { el.hidden = true; }, ms);
  }

  function why(tag, cls, text) {
    var t = $('whyTag'); t.textContent = tag; t.className = 'tag ' + (cls || '');
    $('whyText').textContent = text;
  }

  function showCam(b64) {
    if (!b64) return;
    $('camImg').src = b64.indexOf('data:') === 0 ? b64 : 'data:image/jpeg;base64,' + b64;
    $('camBox').classList.add('has');
  }
  function camScan(on) { $('camBox').classList.toggle('scan', !!on); }

  function renderTrace(turn) {
    var list = $('trace'), tr = (turn && turn.trace) || [];
    list.innerHTML = '';
    if (!tr.length) { var e = document.createElement('li'); e.className = 'empty'; e.textContent = 'Steps appear here as Sorty works.'; list.appendChild(e); return; }
    var names = { frame: 'camera', look: 'look', think: 'think', ask: 'asks', answer: 'person', show: 'look again', specialist: 'specialist', verdict: 'answer' };
    tr.forEach(function (s) {
      var li = document.createElement('li'), k = document.createElement('span'), v = document.createElement('span');
      k.className = 'k ' + s.kind; k.textContent = names[s.kind] || s.kind; v.textContent = s.text;
      li.appendChild(k); li.appendChild(v); list.appendChild(li);
    });
    list.scrollTop = list.scrollHeight;
    $('traceTime').textContent = turn.timing_ms != null ? 'last step took ' + (turn.timing_ms / 1000).toFixed(1) + ' s' : '';
  }

  function resetStage() {
    ['person', 'item', 'item2'].forEach(function (id) { clearAnim($(id)); });
    $('person').classList.add('off'); pose('idle');
    $('item').hidden = true; $('item2').hidden = true; $('item').style.transition = '';
    beam(false); lit(null); mini('idle'); camScan(false);
    say('sorty', ''); say('person', '');
    $('answerBar').hidden = true;
  }

  /* ---------------------------------------------------------------- the kiosk in the frame */
  function kw() { return $('kiosk').contentWindow; }
  function bootKiosk() {
    try { window.localStorage.setItem('sorty.autoplay', S.autoplay ? '1' : '0'); } catch (e) { /* private mode */ }
    var f = $('kiosk');
    f.addEventListener('load', function () {
      var tries = 0;
      (function wait() {
        var w = kw();
        var ready = w && w.SortyDebug && w.Sorty && w.Sorty.api && w.Sorty.api.config && w.Sorty.api.config();
        if (!ready) { if (++tries < 150) setTimeout(wait, 100); return; }
        patchKiosk(w);
        w.SortyDebug.load().catch(function () {}).then(function () {
          closeKioskPanels(); setKioskAutoplay(S.autoplay);
          S.kiosk = w; S.kioskReady = true;
        });
      })();
    });
    f.src = '/?embed=showcase';
  }

  /* Listen in on the kiosk's three calls to the brain. The calls themselves are untouched. */
  function patchKiosk(w) {
    var api = w.Sorty.api, o = { start: api.startSession, reply: api.reply, ans: api.demoAnswer };
    api.startSession = function (body) {
      onStart(body);
      return o.start(body).then(function (t) { onTurn(t); return t; }, function (e) { onFail(); throw e; });
    };
    api.reply = function (sid, body) {
      return Promise.resolve(beforeReply(body)).then(function () { return o.reply(sid, body); })
        .then(function (t) { onTurn(t); return t; }, function (e) { onFail(); throw e; });
    };
    api.demoAnswer = function (b) {
      return o.ans(b).then(function (r) { onPersonSays(r && r.text); return r; });
    };
  }
  function closeKioskPanels() {
    try { var d = kw().document, bd = d.getElementById('backdrop'); if (bd && !bd.hidden) bd.click(); } catch (e) { /* not ready */ }
  }
  function setKioskAutoplay(on) {
    try {
      var c = kw().document.getElementById('autoPlay');
      if (c && c.checked !== !!on) { c.checked = !!on; c.dispatchEvent(new (kw().Event)('change')); }
    } catch (e) { /* not ready */ }
  }
  function kioskAnswer(id, index) {
    try {
      var d = kw().document, b = d.querySelector('#answers .ans[data-id="' + String(id).replace(/"/g, '') + '"]') || d.querySelectorAll('#answers .ans')[index];
      if (b) b.click();
    } catch (e) { /* ignore */ }
  }

  /* ---------------------------------------------------------------- one item's story */
  function alive(run) { return run && S.run === run && !run.over; }

  function startRun(id) {
    if (!S.kioskReady) { why('Wait', '', 'The screen software is still starting. Try again in a second.'); return Promise.resolve(); }
    var sc = S.byId[id]; if (!sc) return Promise.resolve();
    cancelRun();
    var run = S.run = { id: id, sc: sc, kind: 'demo', turns: 0, over: false, key: keyOf(sc.frames.initial), photo: sc.frames.initial };
    run.done = new Promise(function (res) { run.finish = res; });
    markCard(id);
    resetStage();
    setItem($('item'), run.key, run.photo); itemLower(true);
    why('Walks up', '', sc.title + '. ' + (sc.why || ''));
    personEnter().then(function () {
      if (!alive(run)) return;
      pose('present'); itemLower(false);
      return sleep(420);
    }).then(function () {
      if (!alive(run)) return;
      beam(true);
      setKioskAutoplay(S.autoplay);
      kw().SortyDebug.startDemo(id);
    });
    return run.done;
  }

  /* A session the kiosk started by itself: the webcam saw something, or someone used the kiosk's own demo list. */
  function adoptRun(body) {
    cancelRun(true);
    var sc = body.demo_scenario ? S.byId[body.demo_scenario] : null;
    var run = S.run = { id: sc ? sc.id : null, sc: sc || { frames: {} }, kind: sc ? 'demo' : 'live', turns: 0, over: false,
      key: sc ? keyOf(sc.frames.initial) : null, photo: 'data:image/jpeg;base64,' + body.image };
    run.done = new Promise(function (res) { run.finish = res; });
    markCard(run.id);
    resetStage();
    setItem($('item'), run.key, run.photo);
    $('person').classList.remove('off'); pose('present');
    beam(true);
  }

  function cancelRun(keepKiosk) {
    var run = S.run;
    if (run && !run.over) { run.over = true; run.finish(); }
    S.run = null;
    if (!keepKiosk) { try { if (S.kiosk) S.kiosk.SortyDebug.idle(); } catch (e) { /* ignore */ } }
    resetStage();
  }

  function endRun(run) {
    if (!run || run.over) return;
    run.over = true;
    markCard(null);
    run.finish();
  }

  function onStart(body) {
    if (!S.run || S.run.over || (S.run.kind === 'demo' && body.demo_scenario !== S.run.id)) adoptRun(body);
    showCam(body.image); camScan(true); mini('looking');
    why('Looks', 'look', 'Sorty looks at the picture from its camera and works out which facts decide the bin.');
  }

  function beforeReply(body) {
    var run = S.run;
    if (!run || run.over) return null;
    if (body.type === 'frame') {
      if (run.kind === 'live') { run.photo = 'data:image/jpeg;base64,' + body.image; setItem($('item'), null, run.photo); aimBeam(); }
      showCam(body.image); camScan(true); mini('looking'); beam(true);
      return run.acting || null;                       // let the person finish moving before the new frame is sent
    }
    if (body.type === 'answer') {
      if (!run.said) say('person', pretty(body.text), 3200);
      run.said = false;
      $('answerBar').hidden = true; camScan(true); mini('looking');
      return sleep(450);
    }
    say('person', '(no answer)', 2500);
    $('answerBar').hidden = true;
    return null;
  }

  function onPersonSays(text) {                         // the simulated person answered for us
    var run = S.run; if (!run || run.over || !text) return;
    run.said = true; say('person', pretty(text), 3400);
  }
  function pretty(t) {
    var m = { yes: 'Yes', no: 'No', unsure: 'Not sure' };
    return m[String(t).toLowerCase()] || String(t);
  }

  function onFail() {
    var run = S.run; camScan(false);
    why('Problem', 'alert', 'Sorty could not reach its brain. On a real bin the screen then says: please check the labels on the bins.');
    if (run) { mini('alert'); sleep(2500).then(function () { if (alive(run)) { personExit(true).then(function () { resetStage(); endRun(run); }); } }); }
  }

  function onTurn(turn) {
    var run = S.run;
    camScan(false);
    renderTrace(turn);
    if (!run || run.over || !turn) return;
    run.turns++;
    var sub = turn.display && turn.display.sub ? ' (' + turn.display.sub.replace(/\.$/, '') + ')' : '';
    if (turn.type === 'ask') {
      mini('ask'); beam(false);
      say('sorty', turn.say);
      why('Asks', 'ask', 'No camera can see this' + sub + ', so Sorty asks the person one short question.');
      var needHuman = !(S.autoplay && run.kind === 'demo');
      if (needHuman) showAnswers(turn);
    } else if (turn.type === 'show') {
      mini('show'); beam(false);
      say('sorty', turn.say);
      why('Looks again', 'look', 'A camera could see this, just not from here' + sub + '. Sorty asks for another view.');
      var action = turn.show && turn.show.action, next = run.sc.frames ? run.sc.frames[action] : null;
      run.acting = sleep(800).then(function () {
        if (!alive(run)) return;
        if (run.kind === 'live') return itemWiggle();
        if (next) { run.key = keyOf(next); run.photo = next; return itemSwap(run.key, next); }
        say('person', '(does not move it)', 2200);
        return itemWiggle();
      });
    } else if (turn.type === 'verdict') {
      verdict(run, turn);
    } else if (turn.type === 'no_item') {
      mini('idle'); beam(false); say('sorty', turn.say, 3500);
      why('Nothing to sort', '', 'The camera saw no item, so Sorty makes no guess and simply waits.');
      sleep(2600).then(function () { if (alive(run)) personExit(true).then(function () { resetStage(); endRun(run); }); });
    } else {
      onFail();
    }
  }

  function verdict(run, turn) {
    var v = turn.verdict || {}, steps = v.steps || [];
    var binSteps = steps.filter(function (s) { return s.kind === 'bin' && S.stage.bins[s.bin]; });
    var prep = steps.filter(function (s) { return s.kind === 'prep'; });
    var special = steps.some(function (s) { return s.kind === 'special'; }), keep = steps.some(function (s) { return s.kind === 'keep'; });
    var used = (turn.trace || []).some(function (t) { return t.kind === 'specialist'; });
    beam(false); $('answerBar').hidden = true;
    say('sorty', turn.say);
    if (binSteps.length) { mini('verdict', binSteps[0].bin); lit(binSteps[0].bin); }
    else if (special) { mini('alert'); lit(null, true); }
    else mini('idle');

    var how = run.turns === 1 ? 'Everything it needed was visible, so Sorty answered at once.'
      : used ? 'A specialist check settled the detail, and Sorty gives its answer.'
        : 'Now Sorty knows enough to answer.';
    if (special) why('Safety', 'alert', 'This never goes in a bin. Sorty says where to take it instead. ' + (v.reason || ''));
    else if (keep) why('Not trash', '', 'Sorty does not bin things that are not trash. ' + (v.reason || ''));
    else why('Answers', 'done', how + ' ' + (v.reason || ''));

    sleep(1700).then(function () {
      if (!alive(run)) return;
      if (!binSteps.length) return sleep(2200);                    // nothing goes in a bin: the person keeps it
      var chain = prep.length ? (why('First', 'check', prep.map(function (p) { return p.text; }).join(', then ') + '. Then the bin.'), itemPour()) : Promise.resolve();
      return chain.then(function () {
        if (!alive(run)) return;
        var jobs = [itemDrop($('item'), binSteps[0].bin)];
        if (binSteps[1] && binSteps[1].bin !== binSteps[0].bin) {   // two parts, two bins
          setItem($('item2'), run.key, run.photo);
          lit(binSteps[1].bin);
          jobs.push(sleep(380).then(function () { return itemDrop($('item2'), binSteps[1].bin); }));
        }
        return Promise.all(jobs);
      }).then(function () { return sleep(1500); });
    }).then(function () {
      if (!alive(run)) return;
      say('sorty', '');
      return personExit(!binSteps.length);
    }).then(function () {
      if (!alive(run)) return;
      resetStage();
      why('Ready', '', 'Pick another item, or press Play tour.');
      endRun(run);
    });
  }

  function showAnswers(turn) {
    var bar = $('answerBar'), box = $('answerBtns'), opts = (turn.ask && turn.ask.options) || [];
    box.innerHTML = '';
    opts.forEach(function (o, i) {
      var b = document.createElement('button'); b.type = 'button'; b.className = 'ans'; b.textContent = o.label || o.id;
      b.addEventListener('click', function () { bar.hidden = true; kioskAnswer(o.id, i); });
      box.appendChild(b);
    });
    bar.hidden = !opts.length;
  }

  /* ---------------------------------------------------------------- tray and controls */
  function buildTray() {
    var list = $('trayList'), groups = {}, order = [];
    var sorted = S.scenarios.slice().sort(function (a, b) {
      var ia = ORDER.indexOf(a.id), ib = ORDER.indexOf(b.id);
      return (ia < 0 ? 999 : ia) - (ib < 0 ? 999 : ib);
    });
    sorted.forEach(function (sc) {
      var g = sc.group || 'Items';
      if (!groups[g]) { groups[g] = []; order.push(g); }
      groups[g].push(sc);
    });
    list.innerHTML = '';
    order.forEach(function (g) {
      var wrap = document.createElement('div'); wrap.className = 'group';
      var name = document.createElement('span'); name.textContent = g; wrap.appendChild(name);
      groups[g].forEach(function (sc) {
        var key = keyOf(sc.frames.initial), meta = S.items[key];
        var card = document.createElement('button'); card.type = 'button'; card.className = 'card'; card.dataset.id = sc.id; card.title = sc.why || sc.title;
        var th = document.createElement('span'); th.className = 'thumb';
        var img = document.createElement('img'); img.alt = ''; img.loading = 'lazy';
        if (meta) img.src = 'assets/items/' + meta.file; else { img.src = sc.frames.initial; img.className = 'photo'; }
        th.appendChild(img);
        var nm = document.createElement('span'); nm.className = 'name'; nm.textContent = sc.title;
        card.appendChild(th); card.appendChild(nm);
        card.addEventListener('click', function () { stopTour(); S.live = false; $('btnCam').classList.remove('on'); startRun(sc.id); });
        wrap.appendChild(card);
      });
      list.appendChild(wrap);
    });
    if (!S.scenarios.length) list.textContent = 'No demo items found. The test images belong in sorty/tests/images.';
  }
  function markCard(id) {
    Array.prototype.forEach.call(document.querySelectorAll('.card'), function (c) { c.classList.toggle('active', !!id && c.dataset.id === id); });
    var a = document.querySelector('.card.active'); if (a && a.scrollIntoView) a.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  }

  function stopTour() { S.tour = null; $('btnTour').textContent = 'Play tour'; $('btnTour').classList.remove('on'); }
  function playTour() {
    if (S.tour) { stopTour(); cancelRun(); return; }
    var ids = TOUR.filter(function (id) { return S.byId[id]; });
    if (!ids.length) return;
    var token = S.tour = {};
    $('btnTour').textContent = 'Stop tour'; $('btnTour').classList.add('on');
    $('optAuto').checked = true; S.autoplay = true; S.live = false; $('btnCam').classList.remove('on');
    (function next(i) {
      if (S.tour !== token) return;
      if (i >= ids.length) { stopTour(); return; }
      startRun(ids[i]).then(function () { return sleep(1300); }).then(function () { next(i + 1); });
    })(0);
  }

  function useCamera() {
    stopTour(); cancelRun();
    var st = null; try { st = S.kiosk && S.kiosk.SortyDebug.state(); } catch (e) { /* ignore */ }
    if (!st || !st.camera) {
      why('Camera', 'alert', 'No camera is available to Sorty in this browser. Allow the camera for this page (and reload), or pick an item below.');
      return;
    }
    S.live = true; $('btnCam').classList.add('on');
    why('Your camera', 'look', 'Hold a real object up to your webcam and keep it still. Sorty looks by itself, or press Scan on its screen.');
  }

  $('optAuto').addEventListener('change', function () { S.autoplay = this.checked; setKioskAutoplay(S.autoplay); });
  $('btnTour').addEventListener('click', playTour);
  $('btnCam').addEventListener('click', useCamera);
  $('btnSound').addEventListener('click', function () {
    try { kw().document.getElementById('btnMute').click(); } catch (e) { return; }
    S.sound = !S.sound;
    this.textContent = S.sound ? 'Sound on' : 'Sound off'; this.setAttribute('aria-pressed', String(S.sound));
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { stopTour(); cancelRun(); why('Ready', '', 'Pick an item below.'); }
  });

  window.SortyShowcase = { state: function () { return { ready: S.kioskReady, run: S.run && { id: S.run.id, kind: S.run.kind, turns: S.run.turns, over: S.run.over }, base: S.base, poses: S.hasPoses, lit: S.litOk, items: Object.keys(S.items).length, scenarios: S.scenarios.length }; }, start: startRun, cancel: cancelRun };

  init();
})();
