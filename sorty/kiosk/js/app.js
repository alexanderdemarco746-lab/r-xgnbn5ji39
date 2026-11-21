/* Sorty kiosk - the screen's state machine.
   idle -> (capture) -> looking -> ask | show | verdict | no_item | error -> ... -> thanks -> idle
   The brain decides what happens next; this file only senses (camera, voice, taps) and presents. */
(function () {
  'use strict';
  var S = window.Sorty, i18n = S.i18n, icons = S.icons, voice = S.voice, cam = S.camera, api = S.api;
  function $(id) { return document.getElementById(id); }
  function t(key, lang) { return i18n.t(key, lang); }

  var st = {
    state: 'boot', cfg: null, useMock: false,
    lang: 'en', sessionLang: 'en',
    token: 0,                 // bumps on every screen change; late async results compare against it
    sessionId: null, turn: null, manual: false,
    demo: null, demoFrame: null, scenarios: null, autoplay: false, tour: null,
    armed: false, overlay: null,
    lastFrame: null, showWatch: null, arrows: null, answerLock: false,
    trace: [], turnLog: [], sentAt: 0,
    listener: null, timers: {}, captionId: 0, verdictEnd: null
  };

  /* ---------- tiny helpers ---------- */
  function later(name, fn, ms) {
    clearTimeout(st.timers[name]);
    st.timers[name] = setTimeout(function () { delete st.timers[name]; fn(); }, ms);
  }
  function clearTimers() { Object.keys(st.timers).forEach(function (k) { clearTimeout(st.timers[k]); }); st.timers = {}; }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function ico(name, cls) { var s = el('span', cls || ''); s.innerHTML = icons[name] || ''; return s; }
  function store(k, v) { try { if (v === undefined) return window.localStorage.getItem(k); window.localStorage.setItem(k, v); } catch (e) { /* private mode */ } return null; }

  /* ---------- colour: keep white text at 7:1 (WCAG AAA) on every bin colour ---------- */
  function rgb(hex) {
    var h = String(hex || '#444').replace('#', '');
    if (h.length === 3) h = h.split('').map(function (c) { return c + c; }).join('');
    var n = parseInt(h, 16);
    if (!isFinite(n)) n = 0x444B53;
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function lum(c) {
    function f(v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
  }
  function contrast(a, b) { var la = lum(a), lb = lum(b); return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05); }
  function shadeFor(hex) {
    var c = rgb(hex), i = 0;
    while (contrast(c, [255, 255, 255]) < 7.05 && i++ < 80) c = c.map(function (v) { return Math.round(v * 0.965); });
    return 'rgb(' + c.join(',') + ')';
  }

  /* ---------- screen state ---------- */
  function setState(name) {
    st.state = name;
    document.body.dataset.state = name;
    var els = document.querySelectorAll('[data-show]');
    for (var i = 0; i < els.length; i++) els[i].hidden = els[i].dataset.show.split(' ').indexOf(name) < 0;
  }
  /* Enter a new screen: everything scheduled for the previous one is dropped. */
  function enter(name) {
    st.token++;
    clearTimers();
    stopListening();
    st.showWatch = null;
    st.verdictEnd = null;
    setState(name);
    return st.token;
  }

  function setHeadline(text) {
    var h = $('headline'), n = (text || '').length;
    h.textContent = text || '';
    h.classList.toggle('long', n > 22 && n <= 34);
    h.classList.toggle('xlong', n > 34);
  }
  function setSub(text) { $('sub').textContent = text || ''; }
  function setChip(label) {
    var c = $('itemChip');
    c.innerHTML = '';
    if (!label) { c.hidden = true; return; }
    c.appendChild(ico('eye'));
    var s = el('span');
    s.appendChild(el('small', '', t('i_see', st.sessionLang) + ': '));
    s.appendChild(document.createTextNode(label));
    c.appendChild(s);
    c.hidden = false;
  }

  /* ---------- bins ---------- */
  function binById(id) {
    var bins = st.cfg.station.bins;
    for (var i = 0; i < bins.length; i++) if (bins[i].id === id) return bins[i];
    return null;
  }
  function shapeClass(b) { return 'shape-' + (/^(recycle|compost|landfill)$/.test(b.icon) ? b.icon : 'other'); }
  function binIcon(b) { return icons[b.icon] ? b.icon : 'landfill'; }
  function renderBins() {
    var strip = $('binStrip');
    strip.innerHTML = '';
    st.cfg.station.bins.forEach(function (b) {
      var e = el('div', 'bin');
      e.dataset.bin = b.id;
      e.style.setProperty('--c', b.color);
      e.style.setProperty('--shade', b._shade);
      e.appendChild(ico(binIcon(b), 'ico ' + shapeClass(b)));
      e.appendChild(el('span', 'lbl', i18n.pick(b.label, st.lang)));
      strip.appendChild(e);
    });
  }
  function markTargets(bins) {
    var tiles = document.querySelectorAll('.bin');
    for (var i = 0; i < tiles.length; i++) {
      var on = false;
      for (var j = 0; j < bins.length; j++) if (bins[j].id === tiles[i].dataset.bin) on = true;
      tiles[i].classList.toggle('target', on);
    }
  }

  /* ---------- face ---------- */
  function gaze(x, y) { var f = $('face'); f.style.setProperty('--gx', x); f.style.setProperty('--gy', y); }
  function gazeAtCamera() {
    var f = $('face').getBoundingClientRect(), c = $('camFrame').getBoundingClientRect();
    if (!f.width || !c.width) { gaze(0.9, 0.1); return; }
    var dx = (c.left + c.width / 2) - (f.left + f.width / 2), dy = (c.top + c.height / 2) - (f.top + f.height / 2);
    var d = Math.sqrt(dx * dx + dy * dy) || 1;
    gaze((dx / d).toFixed(2), (dy / d).toFixed(2));
  }
  function setSeen(seen) {
    var frame = $('camFrame');
    if (frame.classList.contains('seen') === seen) return;
    frame.classList.toggle('seen', seen);
    $('face').classList.toggle('seen', seen);
    if (seen) gazeAtCamera(); else gaze(0, 0);
  }
  function scheduleGlance() {
    later('glance', function () {
      if (st.state !== 'idle') return;
      if ($('camFrame').classList.contains('seen')) { scheduleGlance(); return; }
      gazeAtCamera();
      later('glanceBack', function () {
        if (st.state !== 'idle') return;
        if (!$('camFrame').classList.contains('seen')) gaze(0, 0);
        scheduleGlance();
      }, 950);
    }, 3200 + Math.random() * 2800);
  }

  /* ---------- camera area ---------- */
  function camMode(m) { $('camFrame').dataset.mode = m; }
  function drawStill(source, mirror) {
    var c = $('still'), sw = source.width, sh = source.height;
    c.width = sw; c.height = sh;
    var x = c.getContext('2d');
    x.save();
    if (mirror) { x.translate(sw, 0); x.scale(-1, 1); }   // match the mirrored preview the person was looking at
    x.drawImage(source, 0, 0, sw, sh);
    x.restore();
    camMode('still');
  }
  function swapStill(source) {
    var c = $('still');
    c.classList.add('swap');
    setTimeout(function () { drawStill(source, false); c.classList.remove('swap'); }, 200);
  }
  function liveView() {
    var live = cam.isLive();
    camMode(live ? 'live' : 'off');
    $('demoBadge').hidden = true;
    $('demoNote').hidden = true;
    $('onAir').hidden = !live;
  }
  function flash() {
    var f = document.querySelector('#camFrame .flash');
    f.classList.remove('go'); void f.offsetWidth; f.classList.add('go');
  }
  function stillRing(p) {
    var r = $('stillRing');
    r.classList.toggle('on', p > 0.03);
    r.querySelector('.fg').style.strokeDashoffset = (113.1 * (1 - Math.max(0, Math.min(1, p)))).toFixed(1);
  }
  function updateIdleButton() {
    var live = cam.isLive(), b = $('btnScan');
    b.innerHTML = '';
    b.appendChild(ico(live ? 'camera' : 'grid'));
    b.appendChild(el('span', '', live ? t('scan') : t('demo_items')));
    if (st.state === 'idle' || st.state === 'boot') $('camHint').textContent = live ? t('privacy') : '';
  }

  /* ---------- speech + captions ---------- */
  function say(text, delayMs) {
    var tk = st.token, lang = st.sessionLang;
    return new Promise(function (resolve) {
      setTimeout(function () {
        if (tk !== st.token) { resolve('stale'); return; }
        voice.speak(text, lang).then(resolve);
      }, delayMs || 0);
    });
  }
  voice.on('start', function (d) {
    st.captionId = d.id;
    $('captionText').textContent = d.text;
    $('caption').hidden = false;
  });
  voice.on('end', function (d) {
    if (!d.all && d.id !== st.captionId) return;
    var id = st.captionId;
    setTimeout(function () { if (st.captionId === id) $('caption').hidden = true; }, d.all ? 0 : 900);
  });

  /* ---------- idle ---------- */
  function goIdle(opts) {
    opts = opts || {};
    enter('idle');
    st.sessionId = null; st.turn = null; st.demo = null; st.demoFrame = null; st.answerLock = false; st.arrows = null;
    document.body.removeAttribute('data-vkind'); document.body.removeAttribute('data-alert');
    markTargets([]);
    liveView();
    stillRing(0);
    $('camFrame').classList.remove('seen', 'is-demo');
    $('face').classList.remove('seen');
    hideBubble();
    setChip('');
    var idleSub = cam.isLive() ? t('idle_sub') : t('idle_sub_demo');
    if (opts.hint) {
      setHeadline(opts.hint); setSub(opts.hintSub || '');
      later('hint', function () { if (st.state === 'idle') { setHeadline(t('idle_headline')); setSub(cam.isLive() ? t('idle_sub') : t('idle_sub_demo')); } }, 6000);
    } else {
      setHeadline(t('idle_headline')); setSub(idleSub);
    }
    updateIdleButton();
    gaze(0, 0);
    scheduleGlance();
    // Re-arm the automatic trigger after a pause, starting from the scene as it is then,
    // so an item that is still being held does not start a second conversation.
    st.armed = false;
    later('arm', function () { cam.snapshotLast(); cam.setLearning(true); st.armed = true; }, opts.cooldown != null ? opts.cooldown : 2500);
    if (st.tour) later('tour', nextTour, 1100);
    renderCounter();
  }

  /* ---------- capture -> looking ---------- */
  function lookingUI(kind) {
    stillRing(0);
    hideBubble();
    setChip('');
    setHeadline(kind === 'think' ? t('okay', st.sessionLang) : t('looking', st.sessionLang));
    setSub('');
    $('face').classList.add('seen');
    gazeAtCamera();
    // Waiting should never feel broken: a calm line after 2.5 s, another after 9 s.
    later('wait1', function () { setSub(t('one_moment', st.sessionLang)); }, 2500);
    later('wait2', function () { setSub(t('still_thinking', st.sessionLang)); }, 9000);
  }

  function startFromCamera(manual) {
    if (st.state !== 'idle') return;
    var f = cam.grab(1280, 0.85);
    if (!f) { openDrawer('demo'); return; }
    st.manual = !!manual;
    st.demo = null;
    voice.earcon.capture();
    drawStill(f.canvas, true);
    flash();
    beginSession(f.b64, null);
  }

  function startDemo(sc) {
    if (!sc || !sc.frames || !sc.frames.initial) return;
    closeDrawers();
    abandon();
    var tk = enter('idle');
    st.armed = false; st.manual = true; st.demo = sc; st.sessionId = null; st.answerLock = false;
    document.body.removeAttribute('data-vkind'); document.body.removeAttribute('data-alert');
    markTargets([]);
    hideBubble(); setChip(''); stillRing(0);
    setHeadline(t('idle_headline')); setSub('');
    updateIdleButton();
    $('camHint').textContent = '';
    $('onAir').hidden = true;
    $('demoNote').hidden = true;
    $('demoBadge').textContent = t('demo_badge');
    $('demoBadge').hidden = false;
    $('camFrame').classList.add('is-demo');
    cam.imageToFrame(sc.frames.initial, 1280, 0.85).then(function (f) {
      if (tk !== st.token) return;
      st.demoFrame = f;
      drawStill(f.canvas, false);                 // "as if the camera saw it"
      setSeen(true);
      later('pre', function () { voice.earcon.capture(); flash(); beginSession(f.b64, sc.id); }, 750);
    }).catch(function (err) {
      if (tk !== st.token) return;
      console.warn('[sorty] demo image failed', err);
      showError();
    });
  }

  function beginSession(b64, demoId) {
    var tk = enter('looking');
    cam.setLearning(false);
    st.sessionLang = st.lang;
    st.lastFrame = b64; st.sessionId = null; st.turn = null; st.answerLock = false;
    st.trace = []; st.turnLog = [];
    renderTrace();
    lookingUI('look');
    st.sentAt = performance.now();
    api.startSession({ image: b64, lang: st.lang, demo_scenario: demoId || null }).then(function (turn) {
      if (tk !== st.token) { if (turn && turn.session_id) api.end(turn.session_id); return; }
      handleTurn(turn);
    }).catch(function (err) {
      if (tk !== st.token) return;
      console.warn('[sorty] session failed:', err && err.message || err);
      showError();
    });
  }

  function sendReply(payload, kind) {
    var sid = st.sessionId;
    var tk = enter('looking');
    lookingUI(kind);
    if (!sid) { showError(); return; }
    st.sentAt = performance.now();
    api.reply(sid, payload).then(function (turn) {
      if (tk !== st.token) return;
      handleTurn(turn);
    }).catch(function (err) {
      if (tk !== st.token) return;
      console.warn('[sorty] reply failed:', err && err.message || err);
      showError();
    });
  }

  function handleTurn(turn) {
    if (!turn || typeof turn !== 'object' || !turn.type) { showError(); return; }
    if (turn.session_id) st.sessionId = turn.session_id;
    st.turn = turn;
    logTurn(turn);
    if (turn.type === 'ask') showAsk(turn);
    else if (turn.type === 'show') showShow(turn);
    else if (turn.type === 'verdict') showVerdict(turn);
    else if (turn.type === 'no_item') noItem(turn);
    else showError();
  }

  /* ---------- ask: a question only the person can answer ---------- */
  function showAsk(turn) {
    var tk = enter('ask');
    var d = turn.display || {};
    st.answerLock = false;
    setHeadline(d.headline || turn.say || '');
    setSub(d.sub || '');
    setChip(d.item_label);
    hideBubble();
    renderAnswers(turn.ask);
    var bar = document.querySelector('#answerTimer i');
    bar.classList.remove('run');
    setListen('tap');
    voice.earcon.question();
    say(turn.say, 300).then(function () {
      if (tk !== st.token || st.answerLock) return;
      if (st.demo && st.autoplay) { autoAnswer(turn, tk); return; }
      // listen and count down only after Sorty has stopped talking
      var secs = st.cfg.timeouts.answer_s;
      bar.style.setProperty('--dur', secs + 's');
      void bar.offsetWidth; bar.classList.add('run');
      later('answerTimeout', function () {
        if (tk !== st.token || st.answerLock) return;
        st.answerLock = true;
        sendReply({ type: 'timeout' }, 'think');
      }, secs * 1000);
      startListening(tk);
    });
  }

  function renderAnswers(ask) {
    var box = $('answers');
    box.innerHTML = '';
    var kind = (ask && ask.kind) || 'yes_no';
    var opts = (ask && Array.isArray(ask.options) && ask.options.length) ? ask.options : [
      { id: 'yes', label: t('yes', st.sessionLang) }, { id: 'no', label: t('no', st.sessionLang) }, { id: 'unsure', label: t('unsure', st.sessionLang) }];
    opts.slice(0, 5).forEach(function (o) {
      var id = String(o.id != null ? o.id : o.label);
      var b = el('button', 'ans');
      b.type = 'button';
      b.dataset.id = id;
      if (id === 'unsure') b.classList.add('secondary');
      if (kind !== 'yes_no') b.classList.add('choice');
      var name = id === 'yes' ? 'check' : id === 'no' ? 'x' : id === 'unsure' ? 'question' : null;
      if (name) b.appendChild(ico(name));
      b.appendChild(el('span', '', o.label != null ? String(o.label) : id));
      b.addEventListener('click', function () { answer(id, 'tap', b); });
      box.appendChild(b);
    });
  }

  function answer(text, via, btn) {
    if (st.state !== 'ask' || st.answerLock) return;
    st.answerLock = true;
    voice.cancel();
    stopListening();
    clearTimeout(st.timers.answerTimeout); delete st.timers.answerTimeout;
    document.querySelector('#answerTimer i').classList.remove('run');
    if (btn) btn.classList.add('picked');
    if (via !== 'tap') { showBubble(text, via); pickMatching(text); }
    var tk = st.token;
    later('answerSend', function () {
      if (tk !== st.token) return;
      sendReply({ type: 'answer', text: text }, 'think');
    }, via === 'tap' ? 200 : via === 'auto' ? 1600 : 700);
  }

  /* Purely visual: light up the button that matches what was heard. The brain still gets the raw words. */
  function pickMatching(text) {
    var p = String(text || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    var id = /(not sure|unsure|no se|don'?t know)/.test(p) ? 'unsure'
      : /\b(yes|yeah|yep|si|claro)\b/.test(p) ? 'yes'
      : /\b(no|nope)\b/.test(p) ? 'no' : null;
    var btns = document.querySelectorAll('#answers .ans');
    for (var i = 0; i < btns.length; i++) {
      var lab = btns[i].textContent.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      if ((id && btns[i].dataset.id === id) || (lab && p.indexOf(lab) >= 0)) { btns[i].classList.add('picked'); return; }
    }
  }

  function autoAnswer(turn, tk) {
    setListen('auto');
    later('auto', function () {
      if (tk !== st.token || !st.demo) return;
      var question = turn.say || (turn.display && turn.display.headline) || '';
      api.demoAnswer({ scenario_id: st.demo.id, question: question }).then(function (r) {
        if (tk !== st.token) return;
        answer(r && r.text ? String(r.text) : 'unsure', 'auto');
      }).catch(function () {
        if (tk !== st.token) return;
        answer('unsure', 'auto');
      });
    }, 700);
  }

  function startListening(tk) {
    if (!voice.canListen()) { setListen('tap'); return; }
    st.listener = voice.listen({
      lang: st.sessionLang,
      onState: function (s) { if (tk === st.token) setListen(s === 'listening' ? 'on' : 'tap'); },
      onInterim: function (txt) { if (tk === st.token && !st.answerLock) showBubble(txt, 'voice', true); },
      onFinal: function (txt) { if (tk === st.token) answer(txt, 'voice'); }
    });
  }
  function stopListening() { if (st.listener) { st.listener.stop(); st.listener = null; } $('listen').classList.remove('on'); }
  function setListen(mode) {
    $('listen').classList.toggle('on', mode === 'on');
    $('listen').classList.toggle('auto', mode === 'auto');
    $('listenText').textContent = mode === 'on' ? t('listening', st.sessionLang) : mode === 'auto' ? '' : t('tap_answer', st.sessionLang);
  }
  function showBubble(text, via, interim) {
    var b = $('bubble');
    b.innerHTML = '';
    b.appendChild(ico(via === 'auto' ? 'person' : 'mic'));
    var s = el('span');
    s.appendChild(el('small', '', (via === 'auto' ? t('person', st.sessionLang) : t('you_said', st.sessionLang)) + ': '));
    s.appendChild(document.createTextNode('“' + text + '”'));
    b.appendChild(s);
    b.style.opacity = interim ? '0.7' : '1';
    b.hidden = false;
  }
  function hideBubble() { $('bubble').hidden = true; }

  /* ---------- show: "do this and let me look again" ---------- */
  function showShow(turn) {
    var tk = enter('show');
    var d = turn.display || {}, sh = turn.show || {};
    setHeadline(d.headline || sh.hint || turn.say || '');
    setSub(d.sub || '');
    setChip(d.item_label);
    var key = S.pictograms[sh.action] ? sh.action : S.hintToPictogram[d.icon];
    $('pictogram').innerHTML = key ? S.pictograms[key] : '';
    $('pictogram').hidden = !key;
    var done = $('btnDone');
    done.innerHTML = '<svg class="ring" viewBox="0 0 44 44" aria-hidden="true"><circle class="bg" cx="22" cy="22" r="18"/><circle class="fg fx-keep" cx="22" cy="22" r="18"/></svg>';
    done.appendChild(el('span', '', t('done', st.sessionLang)));
    stillRing(0);
    if (st.demo) {
      $('camHint').textContent = '';
      $('demoBadge').hidden = false;
    } else {
      liveView();
      $('camHint').textContent = cam.isLive() ? t('hold_still_hint', st.sessionLang) : '';
      if (cam.isLive()) {
        st.showWatch = { ref: null, sawChange: false, t0: performance.now() };
        later('ref', function () { if (st.showWatch) st.showWatch.ref = cam.reference(); }, 300);
      }
    }
    voice.earcon.question();
    say(turn.say, 300).then(function () {
      if (tk !== st.token) return;
      // visible countdown: after show_s seconds Sorty looks anyway
      var secs = st.cfg.timeouts.show_s, fg = done.querySelector('.fg');
      fg.style.setProperty('--dur', secs + 's');
      fg.classList.add('run');
      later('showTimeout', function () { captureShow(); }, secs * 1000);
      if (st.demo) demoPerform(turn, tk);
    });
  }

  /* Demo mode: play the person's part by swapping in the picture for the requested action. */
  function demoPerform(turn, tk) {
    var action = turn.show && turn.show.action;
    var src = st.demo.frames && action ? st.demo.frames[action] : null;
    $('demoNote').textContent = t('person_doing', st.sessionLang);
    $('demoNote').hidden = false;
    later('demo1', function () {
      if (!src) { later('demo2', captureShow, 900); return; }      // no picture for this action: show the same view again
      cam.imageToFrame(src, 1280, 0.85).then(function (f) {
        if (tk !== st.token) return;
        st.demoFrame = f;
        swapStill(f.canvas);
        later('demo2', captureShow, 1200);
      }).catch(function () { if (tk === st.token) captureShow(); });
    }, 900);
  }

  function captureShow() {
    if (st.state !== 'show') return;
    var b64 = null;
    if (st.demo) {
      b64 = st.demoFrame ? st.demoFrame.b64 : st.lastFrame;
    } else {
      var f = cam.grab(1280, 0.85);
      if (f) { drawStill(f.canvas, true); b64 = f.b64; } else b64 = st.lastFrame;
    }
    st.lastFrame = b64;
    $('demoNote').hidden = true;
    voice.cancel();
    voice.earcon.capture();
    flash();
    sendReply({ type: 'frame', image: b64 }, 'look');
  }

  /* ---------- verdict ---------- */
  function showVerdict(turn) {
    var tk = enter('verdict');
    var v = turn.verdict || {}, d = turn.display || {}, lang = st.sessionLang;
    var steps = (Array.isArray(v.steps) ? v.steps : []).filter(function (s) { return s && s.kind; });
    function of(kind) { return steps.filter(function (s) { return s.kind === kind; }); }
    var preps = of('prep').slice(0, 2), specials = of('special'), keeps = of('keep');
    var binSteps = of('bin').filter(function (s) { return binById(s.bin); });
    if (!binSteps.length && binById(v.primary_bin)) binSteps = [{ kind: 'bin', bin: v.primary_bin, item: d.item_label || '', text: d.headline || '' }];
    var targets = st.cfg.station.bins.filter(function (b) { return binSteps.some(function (s) { return s.bin === b.id; }); });

    var layout = (v.primary_bin === 'special' || (specials.length && !targets.length)) ? 'special'
      : (v.primary_bin === 'not_trash' || (keeps.length && !targets.length)) ? 'keep'
      : targets.length >= 2 ? 'split' : targets.length === 1 ? 'single' : 'keep';
    document.body.dataset.vkind = layout;
    // The instant alert: the fast check spotted something that wrecks a whole load (battery, vape, plastic bag...).
    var alertInfo = turn.alert || null;
    if (alertInfo) document.body.dataset.alert = alertInfo.harm || 'stop'; else document.body.removeAttribute('data-alert');
    markTargets(layout === 'single' || layout === 'split' ? targets : []);

    var root = $('verdict'), body = $('vBody');
    body.innerHTML = '';
    body.className = 'v-body';
    st.arrows = [];

    var chip = $('vChip'), label = d.item_label || (binSteps[0] && binSteps[0].item) || (specials[0] && specials[0].item) || '';
    chip.innerHTML = '';
    chip.hidden = !label;
    if (label) {
      chip.appendChild(ico('eye'));
      var cs = el('span'); cs.appendChild(el('small', '', t('i_see', lang) + ': ')); cs.appendChild(document.createTextNode(label)); chip.appendChild(cs);
    }
    $('vGuess').hidden = v.confidence !== 'low';
    $('vGuess').textContent = t('best_guess', lang);

    function prepRows(into) {
      preps.forEach(function (p, i) {
        var row = el('div', 'v-prep');
        row.appendChild(el('span', 'num', String(i + 1)));
        row.appendChild(el('span', '', p.text || ''));
        into.appendChild(row);
      });
    }
    function arrowIn(row, bin) {
      var a = el('div', 'v-arrow');
      a.innerHTML = icons.arrow;
      row.appendChild(a);
      st.arrows.push({ arrow: a, row: row, bin: bin.id });
    }

    if (layout === 'single') {
      var b = targets[0];
      root.style.setProperty('--vbg', b._shade); root.style.setProperty('--vink', '#fff');
      var text = el('div', 'v-text' + (preps.length ? ' has-prep' : ''));
      prepRows(text);
      var main = el('div', 'v-main');
      if (preps.length) main.appendChild(el('span', 'num', String(preps.length + 1)));
      main.appendChild(ico(binIcon(b), 'v-badge ' + shapeClass(b)));
      main.appendChild(el('div', 'v-word', i18n.pick(b.label, lang)));
      text.appendChild(main);
      var whereText = binSteps[0].text || '';
      if (whereText) text.appendChild(el('div', 'v-where', whereText));
      if (v.reason) text.appendChild(el('div', 'v-reason', v.reason));
      specials.forEach(function (s) { text.appendChild(el('div', 'v-also', [s.item, s.text, s.dest].filter(Boolean).join(' → '))); });
      body.appendChild(text);
      var arow = el('div', 'v-arrowrow');
      body.appendChild(arow);
      arrowIn(arow, b);
    } else if (layout === 'split') {
      root.style.setProperty('--vbg', '#12161C'); root.style.setProperty('--vink', '#fff');
      body.classList.add('split');
      var pre = el('div', 'v-text');
      prepRows(pre);
      body.appendChild(pre);
      var split = el('div', 'v-split');
      targets.forEach(function (bn) {
        var mine = binSteps.filter(function (s) { return s.bin === bn.id; });
        var panel = el('div', 'v-panel');
        panel.style.setProperty('--pshade', bn._shade);
        panel.appendChild(el('div', 'p-item', mine.map(function (s) { return s.item; }).filter(Boolean).join(' + ')));
        var w = el('div', 'p-word');
        w.appendChild(ico(binIcon(bn), 'v-badge ' + shapeClass(bn)));
        w.appendChild(el('span', '', i18n.pick(bn.label, lang)));
        panel.appendChild(w);
        panel.appendChild(el('div', 'p-where', mine[0].text || ''));
        var prow = el('div', 'p-arrowrow');
        panel.appendChild(prow);
        arrowIn(prow, bn);
        split.appendChild(panel);
      });
      body.appendChild(split);
      body.appendChild(el('div', 'v-reason', v.reason || ''));
    } else if (layout === 'special') {
      root.style.setProperty('--vbg', '#F5A20B'); root.style.setProperty('--vink', '#15110A');
      var sp = specials[0] || {};
      var box = el('div', 'v-special');
      box.appendChild(ico('warning', 'sp-icon'));
      box.appendChild(el('div', 'sp-head', sp.text || d.headline || t('not_in_bins', lang)));
      var dest = sp.dest || v.special_dest;
      if (dest) {
        var dd = el('div', 'sp-dest');
        dd.appendChild(ico('pin'));
        var ds = el('span'); ds.appendChild(el('small', '', t('take_it_to', lang) + ': ')); ds.appendChild(document.createTextNode(dest)); dd.appendChild(ds);
        box.appendChild(dd);
      }
      if (v.reason) box.appendChild(el('div', 'v-reason', v.reason));
      binSteps.forEach(function (s) { box.appendChild(el('div', 'v-also', [s.item, s.text].filter(Boolean).join(': '))); });
      body.appendChild(box);
    } else {
      root.style.setProperty('--vbg', '#F4F1EA'); root.style.setProperty('--vink', '#11161C');
      var kp = el('div', 'v-keep');
      kp.appendChild(ico('heart', 'sp-icon'));
      kp.appendChild(el('div', 'sp-head', (keeps[0] && keeps[0].text) || d.headline || ''));
      if (v.reason) kp.appendChild(el('div', 'v-reason', v.reason));
      body.appendChild(kp);
    }

    chip.classList.toggle('alert', !!alertInfo);
    if (alertInfo) {
      // red screen, STOP first, and how fast it was caught
      root.style.setProperty('--vbg', '#B3261E'); root.style.setProperty('--vink', '#fff');
      chip.insertBefore(el('b', 'stop', alertInfo.label || 'Stop'), chip.firstChild);
      if (alertInfo.ms) chip.appendChild(el('em', 'fast', (alertInfo.ms / 1000).toFixed(1) + ' s'));
      chip.hidden = false;
    }

    fitWords();
    placeArrows();
    requestAnimationFrame(placeArrows);
    later('arrows', placeArrows, 380);

    // the screen holds for verdict_hold_s, and never cuts Sorty off mid-sentence
    var hold = st.cfg.timeouts.verdict_hold_s * 1000;
    var bar = $('vBar');
    bar.classList.remove('run');
    bar.style.setProperty('--dur', (hold / 1000) + 's');
    void bar.offsetWidth; bar.classList.add('run');

    if (alertInfo && voice.earcon.alarm) voice.earcon.alarm();
    else if (layout === 'special') voice.earcon.warning();
    else if (layout === 'keep') voice.earcon.thanks();
    else voice.earcon.verdict();

    var spoken = false, held = false;
    function maybeEnd() { if (tk === st.token && spoken && held) showThanks(turn, layout); }
    st.verdictEnd = function () { spoken = true; held = true; voice.cancel(); maybeEnd(); };
    say(turn.say, 350).then(function () { spoken = true; maybeEnd(); });
    later('hold', function () { held = true; maybeEnd(); }, hold);
    later('holdMax', function () { spoken = true; held = true; maybeEnd(); }, hold + 7000);
  }

  /* Long bin names (or narrow screens) must never run off the screen: shrink the big word until it fits. */
  function fitWords() {
    if (st.state !== 'verdict') return;
    function shrink(word, measure, limit) {
      if (!word || !measure || !limit) return;
      word.style.fontSize = '';
      var size = parseFloat(window.getComputedStyle(word).fontSize) || 40, n = 0;
      while (measure.scrollWidth > limit.clientWidth + 1 && n++ < 16) { size *= 0.93; word.style.fontSize = size.toFixed(1) + 'px'; }
    }
    var body = $('vBody');
    shrink(body.querySelector('.v-word'), body.querySelector('.v-main'), body.querySelector('.v-text'));
    var panels = body.querySelectorAll('.v-panel');
    for (var i = 0; i < panels.length; i++) {
      var pad = parseFloat(window.getComputedStyle(panels[i]).paddingLeft) || 0;
      var w = panels[i].querySelector('.p-word');
      shrink(w, w, { clientWidth: panels[i].clientWidth - 2 * pad });
    }
  }

  /* Point every arrow from where it sits to the middle of its bin tile. */
  function placeArrows() {
    if (st.state !== 'verdict' || !st.arrows) return;
    st.arrows.forEach(function (a) {
      var tile = document.querySelector('.bin[data-bin="' + a.bin + '"]');
      if (!tile) return;
      var tr = tile.getBoundingClientRect(), rr = a.row.getBoundingClientRect();
      if (!rr.width || !rr.height) return;
      var size = Math.max(36, Math.min(rr.height * 0.98, window.innerHeight * 0.27, window.innerWidth * 0.2));
      a.arrow.style.width = size + 'px';
      a.arrow.style.height = size + 'px';
      var cx = rr.left + rr.width / 2, tx = tr.left + tr.width / 2;
      var ax = cx + (tx - cx) * 0.55;
      ax = Math.max(rr.left + size / 2, Math.min(rr.right - size / 2, ax));
      a.arrow.style.left = (ax - rr.left) + 'px';
      var ay = rr.top + rr.height / 2, ty = tr.top + tr.height * 0.25;
      var ang = Math.atan2(-(tx - ax), Math.max(1, ty - ay)) * 180 / Math.PI;   // 0 = straight down, + = toward the left
      ang = Math.max(-52, Math.min(52, ang));
      a.arrow.style.setProperty('--angle', ang.toFixed(1) + 'deg');
    });
  }

  /* ---------- the pleasant ending ---------- */
  function showThanks(turn, layout) {
    var lang = st.sessionLang;
    enter('thanks');
    $('thanksHead').textContent = t('thanks', lang);
    var sub = $('thanksSub');
    sub.innerHTML = '';
    if (layout === 'single' || layout === 'split') {
      var n = bumpCounter();
      sub.appendChild(document.createTextNode(t('sorted_today', lang) + ': '));
      sub.appendChild(el('b', '', String(n)));
    } else {
      sub.textContent = t('thanks_sub', lang);
    }
    voice.earcon.thanks();
    if (!/(thank|gracias)/i.test(turn.say || '')) voice.speak(t('thanks', lang), lang);
    later('thanksEnd', function () { goIdle({ cooldown: 2500 }); }, 1900);
  }

  function noItem(turn) {
    var d = turn.display || {}, manual = st.manual, words = turn.say, lang = st.sessionLang;
    goIdle({ hint: d.headline || t('no_item_default', lang), hintSub: d.sub || '', cooldown: 3000 });
    // quiet for an automatic false alarm (someone walking by); spoken when a person asked for the scan
    if (manual && words) voice.speak(words, lang);
  }

  function showError() {
    var sid = st.sessionId;
    enter('error');
    if (sid) api.end(sid);
    st.sessionId = null;
    document.body.removeAttribute('data-vkind'); document.body.removeAttribute('data-alert');
    markTargets([]);
    hideBubble(); setChip('');
    $('errIcon').innerHTML = icons.eyeoff;
    setHeadline(t('error_headline'));
    setSub(t('error_sub'));
    voice.speak(t('error_headline') + ' ' + t('error_sub'), st.lang);
    later('errorEnd', function () { goIdle({ cooldown: 3000 }); }, 6500);
  }

  /* Leave a conversation that is still open (Escape, or a new demo started on top of it). */
  function abandon() {
    var open = st.sessionId && (st.state === 'ask' || st.state === 'show' || st.state === 'looking');
    if (open) api.end(st.sessionId);
    st.sessionId = null;
    voice.cancel();
  }
  function cancelAll() {
    st.tour = null; updatePlayAll();
    abandon();
    goIdle({ cooldown: 1500 });
  }

  /* ---------- counter: a small positive nudge ---------- */
  function countKey() { var d = new Date(); return 'sorty.count.' + d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); }
  function getCount() { var n = parseInt(store(countKey()), 10); return isFinite(n) ? n : 0; }
  function bumpCounter() { var n = getCount() + 1; store(countKey(), String(n)); renderCounter(); return n; }
  function renderCounter() {
    var c = $('counter'), n = getCount();
    c.innerHTML = '';
    c.hidden = n < 1;
    if (n < 1) return;
    c.appendChild(ico('compost'));
    c.appendChild(document.createTextNode(t('sorted_today') + ' '));
    c.appendChild(el('b', '', String(n)));
  }

  /* ---------- "How Sorty decided" ---------- */
  function logTurn(turn) {
    var rt = Math.round(performance.now() - st.sentAt);
    var tr = Array.isArray(turn.trace) ? turn.trace.filter(function (e) { return e && typeof e === 'object'; }) : [];
    if (!st.trace.length) st.trace = tr.slice();
    else {
      // The server may send the whole session trace each turn, or only the new entries. Handle both.
      var a = st.trace[0], b = tr[0];
      var whole = tr.length >= st.trace.length && b && a.kind === b.kind && a.text === b.text;
      st.trace = whole ? tr.slice() : st.trace.concat(tr);
    }
    st.turnLog.push({ turn: turn.turn, type: turn.type, server: turn.timing_ms, rt: rt });
    renderTrace();
  }
  function secs(ms) { return (Math.round(ms / 100) / 10).toFixed(1) + ' s'; }
  function renderTrace() {
    var list = $('traceList'), turns = $('traceTurns');
    list.innerHTML = ''; turns.innerHTML = '';
    var brain = st.useMock ? 'mock (in the browser)' : (st.cfg && st.cfg.mode === 'mock' ? 'mock (server)' : 'live' + (st.cfg && st.cfg.model ? ' · ' + st.cfg.model : ''));
    $('traceMeta').textContent = t('brain') + ': ' + brain + (st.sessionId ? ' · ' + t('session') + ' ' + st.sessionId : '');
    if (!st.trace.length) { list.appendChild(el('p', 'trace-empty', t('trace_empty'))); return; }
    st.trace.forEach(function (e) {
      var row = el('div', 'trow');
      row.appendChild(el('time', '', (typeof e.t_ms === 'number') ? '+' + secs(e.t_ms) : ''));
      var cell = el('div');
      var kind = String(e.kind || '').split(':')[0];
      cell.appendChild(el('span', 'k ' + kind, t('k_' + kind) === 'k_' + kind ? String(e.kind || '') : t('k_' + kind)));
      cell.appendChild(el('p', '', e.text != null ? String(e.text) : ''));
      row.appendChild(cell);
      list.appendChild(row);
    });
    st.turnLog.forEach(function (x) {
      var parts = [t('turn') + ' ' + (x.turn != null ? x.turn : '?') + ' · ' + x.type];
      if (typeof x.server === 'number') parts.push(t('ai_time') + ' ' + secs(x.server));
      parts.push(t('round_trip') + ' ' + secs(x.rt));
      turns.appendChild(el('div', '', parts.join(' · ')));
    });
    list.scrollTop = list.scrollHeight;
  }

  /* ---------- drawers ---------- */
  function openDrawer(which) {
    closeDrawers();
    st.overlay = which;
    var d = $(which === 'demo' ? 'demoDrawer' : 'tracePanel');
    d.classList.add('open');
    d.setAttribute('aria-hidden', 'false');
    $(which === 'demo' ? 'btnDemo' : 'btnTrace').setAttribute('aria-pressed', 'true');
    if (which === 'demo') { $('backdrop').hidden = false; loadScenarios(); }
    else renderTrace();
  }
  function closeDrawers() {
    ['demoDrawer', 'tracePanel'].forEach(function (id) { $(id).classList.remove('open'); $(id).setAttribute('aria-hidden', 'true'); });
    $('btnDemo').setAttribute('aria-pressed', 'false');
    $('btnTrace').setAttribute('aria-pressed', 'false');
    $('backdrop').hidden = true;
    st.overlay = null;
  }
  function toggleDrawer(which) { if (st.overlay === which) closeDrawers(); else openDrawer(which); }

  function loadScenarios() {
    api.scenarios().then(function (list) {
      st.scenarios = Array.isArray(list) ? list.filter(function (s) { return s && s.id && s.frames && s.frames.initial; }) : [];
      renderScenarios();
    }).catch(function (err) {
      console.warn('[sorty] could not load demo items', err && err.message || err);
      st.scenarios = [];
      renderScenarios();
    });
  }
  function renderScenarios() {
    var box = $('demoList');
    box.innerHTML = '';
    var groups = [], byGroup = {};
    (st.scenarios || []).forEach(function (s, i) {
      var g = s.group || '';
      if (!byGroup[g]) { byGroup[g] = []; groups.push(g); }
      byGroup[g].push({ s: s, n: i + 1 });
    });
    groups.forEach(function (g) {
      if (g) box.appendChild(el('h3', 'group-title', g));
      var cards = el('div', 'cards');
      byGroup[g].forEach(function (x) {
        var c = el('button', 'card');
        c.type = 'button';
        var img = document.createElement('img');
        img.alt = ''; img.loading = 'lazy'; img.src = x.s.frames.initial;
        c.appendChild(img);
        if (x.n <= 9) c.appendChild(el('kbd', '', String(x.n)));
        c.appendChild(el('span', '', x.s.title || x.s.id));
        c.addEventListener('click', function () { st.tour = null; updatePlayAll(); startDemo(x.s); });
        cards.appendChild(c);
      });
      box.appendChild(cards);
    });
    if (!groups.length) box.appendChild(el('p', 'trace-empty', '—'));
  }
  function updatePlayAll() {
    var b = $('playAll');
    b.innerHTML = '';
    b.appendChild(ico(st.tour ? 'stop' : 'play'));
    b.appendChild(el('span', '', st.tour ? t('stop') : t('play_all')));
  }
  function startTour() {
    if (!st.scenarios || !st.scenarios.length) return;
    st.tour = st.scenarios.slice();
    setAutoplay(true);
    updatePlayAll();
    closeDrawers();
    nextTour();
  }
  function nextTour() {
    if (!st.tour) return;
    var sc = st.tour.shift();
    if (!sc) { st.tour = null; updatePlayAll(); return; }
    startDemo(sc);
  }
  function setAutoplay(on) { st.autoplay = !!on; $('autoPlay').checked = st.autoplay; store('sorty.autoplay', st.autoplay ? '1' : '0'); }

  /* ---------- language, sound, full screen ---------- */
  function applyTexts() {
    document.title = (st.cfg ? st.cfg.assistant_name : 'Sorty') + ' - ' + t('brand_tag');
    $('camTag').textContent = t('show_here');
    $('onAirText').textContent = t('cam_on');
    $('camOffText').textContent = t('cam_off');
    document.querySelector('.camoff-ico').innerHTML = icons.eyeoff;
    document.querySelector('#listen .mic').innerHTML = icons.mic;
    document.querySelector('#caption .cap-ico').innerHTML = icons.sound;
    $('demoBadge').textContent = t('demo_badge');
    var sh = $('soundHint'); sh.innerHTML = ''; sh.appendChild(ico('sound')); sh.appendChild(el('span', '', t('sound_hint')));
    var pairs = [['btnDemo', 'grid', 'demo'], ['btnTrace', 'list', 'trace'], ['btnFull', 'full', 'fullscreen'], ['demoClose', 'x', 'close'], ['traceClose', 'x', 'close']];
    pairs.forEach(function (p) { var b = $(p[0]); b.innerHTML = icons[p[1]]; b.title = t(p[2]); b.setAttribute('aria-label', t(p[2])); });
    var m = $('btnMute'); m.innerHTML = voice.isMuted() ? icons.mute : icons.sound;
    m.title = voice.isMuted() ? t('sound_off') : t('sound_on'); m.setAttribute('aria-label', m.title);
    m.setAttribute('aria-pressed', voice.isMuted() ? 'true' : 'false');
    $('langSeg').setAttribute('aria-label', t('language'));
    $('demoTitle').textContent = t('demo_title'); $('demoSub').textContent = t('demo_sub');
    $('autoPlayLabel').textContent = t('autoplay'); $('autoPlaySub').textContent = t('autoplay_sub');
    $('demoFoot').textContent = t('shortcuts');
    $('traceTitle').textContent = t('trace_title');
    updatePlayAll();
    updateIdleButton();
    var badge = $('modeBadge'), practice = st.useMock || (st.cfg && st.cfg.mode === 'mock');
    badge.hidden = !practice; badge.textContent = t('mode_mock');
  }
  function renderLangs() {
    var seg = $('langSeg');
    seg.innerHTML = '';
    var langs = (st.cfg.languages || ['en']).filter(function (l) { return i18n.has(l); });
    seg.hidden = langs.length < 2;
    langs.forEach(function (l) {
      var b = el('button', '', l.toUpperCase());
      b.type = 'button';
      b.setAttribute('aria-pressed', l === st.lang ? 'true' : 'false');
      b.addEventListener('click', function () { setLang(l); b.blur(); });
      seg.appendChild(b);
    });
  }
  function setLang(l) {
    st.lang = i18n.setLang(l);
    store('sorty.lang', st.lang);
    renderLangs(); renderBins(); applyTexts(); renderCounter(); renderTrace();
    if (st.overlay === 'demo') loadScenarios();
    if (st.state === 'idle') { setHeadline(t('idle_headline')); setSub(cam.isLive() ? t('idle_sub') : t('idle_sub_demo')); }
    if (st.state === 'verdict' && st.turn) markTargets(st.cfg.station.bins.filter(function (b) {
      return (st.turn.verdict && st.turn.verdict.steps || []).some(function (s) { return s.kind === 'bin' && s.bin === b.id; });
    }));
  }
  function nextLang() {
    var langs = (st.cfg.languages || ['en']).filter(function (l) { return i18n.has(l); });
    if (langs.length < 2) return;
    setLang(langs[(langs.indexOf(st.lang) + 1) % langs.length]);
  }
  function toggleMute() {
    voice.setMuted(!voice.isMuted());
    store('sorty.muted', voice.isMuted() ? '1' : '0');
    if (voice.isMuted()) $('caption').hidden = true;
    applyTexts();
  }
  function toggleFull() {
    try {
      if (document.fullscreenElement) document.exitFullscreen();
      else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
    } catch (e) { /* not allowed here */ }
  }

  var gestured = false, wake = null;
  function firstGesture() {
    voice.unlock();
    if (gestured) return;
    gestured = true;
    $('soundHint').hidden = true;
    try {
      if (navigator.wakeLock && navigator.wakeLock.request) {
        navigator.wakeLock.request('screen').then(function (w) { wake = w; }).catch(function () {});
      }
    } catch (e) { /* ignore */ }
  }

  /* ---------- camera sensing ---------- */
  cam.onTick(function (m) {
    var T = cam.tune;
    if (st.overlay === 'trace') {
      $('traceCam').textContent = t('camera') + ': ' + t('motion') + ' ' + Math.round(m.motion * 100) + '% · ' + t('presence') + ' ' +
        Math.round(m.presEmpty * 100) + '% / ' + Math.round(m.presLast * 100) + '% · ' + t('still') + ' ' + secs(m.stillMs) + (st.armed ? ' · armed' : '');
    }
    if (st.state === 'idle' && !st.demo) {
      // something was brought into view (recent movement) and it is not the empty scene
      var seen = m.sinceBurst < T.BURST_MS && m.presEmpty >= T.P_ON && m.presLast >= T.P_LAST;
      setSeen(seen);
      stillRing(seen && st.armed ? Math.min(1, m.stillMs / T.STILL_MS) : 0);
      if (seen && st.armed && m.stillMs >= T.STILL_MS && st.overlay !== 'demo') { st.armed = false; startFromCamera(false); }
    } else if (st.state === 'show' && st.showWatch && st.showWatch.ref) {
      var w = st.showWatch;
      if (m.motion >= T.M_ON) w.sawChange = true;
      var changed = cam.diffFrom(w.ref) >= 0.04;
      var ready = w.sawChange && changed;
      stillRing(ready ? Math.min(1, m.stillMs / T.STILL_MS) : 0);
      // the view changed and is now held still: look again
      if (ready && m.stillMs >= T.STILL_MS && performance.now() - w.t0 >= 1200) captureShow();
    }
  });
  cam.onState(function (live) {
    if (st.state === 'idle' && !st.demo) {
      liveView(); updateIdleButton();
      setSub(live ? t('idle_sub') : t('idle_sub_demo'));
    }
  });

  /* ---------- input ---------- */
  function primaryAction() {
    if (st.state === 'idle') { if (st.demo) return; if (cam.isLive()) startFromCamera(true); else openDrawer('demo'); }
    else if (st.state === 'show') captureShow();
    else if (st.state === 'verdict' && st.verdictEnd) st.verdictEnd();
  }

  document.addEventListener('pointerdown', firstGesture, true);
  document.addEventListener('keydown', function (e) {
    if (e.repeat || e.ctrlKey || e.metaKey || e.altKey) return;
    firstGesture();
    var k = (e.key || '').toLowerCase();
    var inDrawer = document.activeElement && document.activeElement.closest && document.activeElement.closest('.drawer');
    if (k === ' ' || e.code === 'Space') {
      if (inDrawer) return;                    // let Space press the focused control inside a drawer
      e.preventDefault(); primaryAction(); return;
    }
    if (k === 'escape') { if (st.overlay) closeDrawers(); else cancelAll(); return; }
    if (k === 'm') toggleDrawer('demo');
    else if (k === 'd') toggleDrawer('trace');
    else if (k === 'l') nextLang();
    else if (k === 's') toggleMute();
    else if (k === 'f') toggleFull();
    else if (st.state === 'ask' && (k === 'y' || k === 'n' || k === 'u')) {
      var b = document.querySelector('#answers .ans[data-id="' + (k === 'y' ? 'yes' : k === 'n' ? 'no' : 'unsure') + '"]');
      if (b) b.click();
    } else if (/^[1-9]$/.test(k) && st.scenarios && st.scenarios[+k - 1]) {
      st.tour = null; updatePlayAll(); startDemo(st.scenarios[+k - 1]);
    }
  });

  $('btnScan').addEventListener('click', function () { this.blur(); primaryAction(); });
  $('camFrame').addEventListener('click', function () { if (st.state === 'idle' || st.state === 'show') primaryAction(); });
  $('btnDone').addEventListener('click', function () { this.blur(); captureShow(); });
  $('verdict').addEventListener('click', function () { if (st.verdictEnd) st.verdictEnd(); });
  $('btnDemo').addEventListener('click', function () { this.blur(); toggleDrawer('demo'); });
  $('btnTrace').addEventListener('click', function () { this.blur(); toggleDrawer('trace'); });
  $('btnMute').addEventListener('click', function () { this.blur(); toggleMute(); });
  $('btnFull').addEventListener('click', function () { this.blur(); toggleFull(); });
  $('demoClose').addEventListener('click', closeDrawers);
  $('traceClose').addEventListener('click', closeDrawers);
  $('backdrop').addEventListener('click', closeDrawers);
  $('soundHint').addEventListener('click', firstGesture);
  $('autoPlay').addEventListener('change', function () { setAutoplay(this.checked); });
  $('playAll').addEventListener('click', function () { if (st.tour) { st.tour = null; updatePlayAll(); } else startTour(); });
  window.addEventListener('resize', function () { fitWords(); placeArrows(); });
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden && gestured && !wake) { try { navigator.wakeLock.request('screen').then(function (w) { wake = w; }).catch(function () {}); } catch (e) { /* ignore */ } }
    if (document.hidden) wake = null;
  });

  /* ---------- boot ---------- */
  function boot() {
    setState('boot');
    setHeadline(t('boot'));
    voice.setMuted(store('sorty.muted') === '1');
    api.init().then(function (r) {
      st.cfg = r.config; st.useMock = r.useMock;
      st.cfg.station.bins.forEach(function (b) { b._shade = shadeFor(b.color); });
      var saved = store('sorty.lang');
      st.lang = i18n.setLang(saved && st.cfg.languages.indexOf(saved) >= 0 ? saved : st.cfg.lang_default);
      st.sessionLang = st.lang;
      st.autoplay = store('sorty.autoplay') === '1';
      $('autoPlay').checked = st.autoplay;
      $('brandName').textContent = st.cfg.assistant_name;
      renderLangs(); renderBins(); applyTexts(); renderTrace();
      if (voice.soundBlocked()) $('soundHint').hidden = false;

      // Embedded in the virtual prototype page: that page turns the camera on when the visitor asks for it.
      if (/[?&]embed=/.test(window.location.search)) { goIdle({ cooldown: 800 }); return; }

      // Ask for the camera, but never let a permission prompt hold the screen hostage.
      var settled = false;
      cam.start($('video')).then(function (ok) {
        settled = true;
        if (st.state === 'boot') goIdle({ cooldown: 2000 });
        if (!ok && st.state === 'idle' && !st.overlay && !st.demo) openDrawer('demo');   // no camera: straight to demo mode
      });
      setTimeout(function () { if (!settled && st.state === 'boot') goIdle({ cooldown: 2000 }); }, 1800);
    });
  }

  /* For testing from the console: SortyDebug.render(turnObject) shows any Turn; SortyDebug.state() reports. */
  window.SortyDebug = {
    render: function (turn) { st.sessionLang = st.lang; st.sentAt = performance.now(); handleTurn(turn); },
    startDemo: function (id) { var s = (st.scenarios || []).filter(function (x) { return x.id === id; })[0]; if (s) startDemo(s); return !!s; },
    load: function () { return api.scenarios().then(function (l) { st.scenarios = l; return l.map(function (x) { return x.id; }); }); },
    state: function () {
      return { state: st.state, lang: st.lang, mock: st.useMock, session: st.sessionId, demo: st.demo && st.demo.id, camera: cam.isLive(),
        armed: st.armed, autoplay: st.autoplay, tour: st.tour ? st.tour.length : 0, canListen: voice.canListen(), canSpeak: voice.canSpeak(),
        voice: voice.voiceName(st.lang), trace: st.trace.length, vkind: document.body.dataset.vkind || null };
    },
    idle: function () { cancelAll(); }
  };

  boot();
})();
