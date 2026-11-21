/* Sorty kiosk - voice out (speech synthesis), voice in (speech recognition), earcons (WebAudio).
   Nothing here needs a network asset: voices come from the browser/OS, sounds are generated. */
(function () {
  'use strict';
  var i18n = window.Sorty.i18n;
  var synth = window.speechSynthesis || null;
  var voices = [];
  var muted = false;
  var seq = 0;                 // id of the latest utterance; older ones are ignored
  var keepAlive = null;        // reference so Chrome does not garbage-collect a speaking utterance
  var speechUnlocked = false;
  var handlers = { start: [], end: [] };

  function emit(evt, data) {
    handlers[evt].forEach(function (fn) { try { fn(data); } catch (e) { console.error(e); } });
  }
  function on(evt, fn) { if (handlers[evt]) handlers[evt].push(fn); }

  function refreshVoices() {
    try { voices = synth ? synth.getVoices() : []; } catch (e) { voices = []; }
  }
  if (synth) {
    refreshVoices();
    if (synth.addEventListener) synth.addEventListener('voiceschanged', refreshVoices);
    else synth.onvoiceschanged = refreshVoices;
  }

  /* Choose the most natural voice the device offers for a language. */
  function pickVoice(lang) {
    if (!voices.length) refreshVoices();
    var want = i18n.speechLang(lang).toLowerCase();
    var base = want.slice(0, 2);
    var best = null, bestScore = -1e9;
    for (var i = 0; i < voices.length; i++) {
      var v = voices[i];
      var vl = String(v.lang || '').toLowerCase().replace('_', '-');
      if (vl.slice(0, 2) !== base) continue;
      var n = String(v.name || '');
      var s = 0;
      if (vl === want) s += 12;
      if (/natural/i.test(n)) s += 50;
      if (/neural/i.test(n)) s += 30;
      if (/google/i.test(n)) s += 25;
      if (/online/i.test(n)) s += 20;
      if (/(aria|jenny|ava|emma|samantha|michelle|sonia|libby|dalia|paulina|elvira|sabina|m[oó]nica|paloma)/i.test(n)) s += 15;
      if (/(david|zira|mark|desktop)/i.test(n)) s -= 5;         // older, more robotic voices
      if (navigator.onLine === false && v.localService === false) s -= 200;
      if (v.default) s += 1;
      if (s > bestScore) { bestScore = s; best = v; }
    }
    return best;
  }

  /* Speak text. Resolves when the words are finished (or would have been, when muted),
     so callers can start listening only after Sorty stops talking. Captions get the
     same start/end events whether or not sound is on. */
  function speak(text, lang) {
    var id = ++seq;
    text = String(text || '').replace(/\s+/g, ' ').trim();
    return new Promise(function (resolve) {
      var done = false, guard = null;
      function finish(why) {
        if (done) return;
        done = true;
        if (guard) clearTimeout(guard);
        if (keepAlive && keepAlive._id === id) keepAlive = null;
        emit('end', { id: id, text: text, why: why });
        resolve(why);
      }
      if (!text) { resolve('empty'); return; }
      emit('start', { id: id, text: text });
      var words = text.split(' ').length;
      if (muted || !synth || typeof window.SpeechSynthesisUtterance === 'undefined') {
        // Silent mode: leave the caption up for a comfortable reading time.
        guard = setTimeout(function () { finish('silent'); }, Math.min(4500, 700 + words * 230));
        return;
      }
      try { synth.cancel(); } catch (e) { /* ignore */ }
      var u = new window.SpeechSynthesisUtterance(text);
      u._id = id;
      var v = pickVoice(lang);
      if (v) { u.voice = v; u.lang = v.lang; } else { u.lang = i18n.speechLang(lang); }
      u.rate = 0.97; u.pitch = 1.0; u.volume = 1.0;
      u.onend = function () { finish('end'); };
      u.onerror = function (ev) { finish('error:' + (ev && ev.error ? ev.error : '')); };
      keepAlive = u;
      // Some browsers never fire onend; never let the flow hang on that.
      guard = setTimeout(function () { finish('guard'); }, 3000 + words * 520);
      // A short gap after cancel() avoids Chrome dropping the new utterance.
      setTimeout(function () {
        if (done) return;
        if (id !== seq) { finish('superseded'); return; }
        try { synth.speak(u); } catch (e) { finish('throw'); }
      }, 70);
    });
  }

  function cancel() {
    seq++;
    try { if (synth) synth.cancel(); } catch (e) { /* ignore */ }
    emit('end', { id: -1, text: '', why: 'cancel', all: true });
  }

  /* ---------- Earcons ---------- */
  var actx = null, master = null;
  function audio() {
    if (!actx) {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      try {
        actx = new AC();
        master = actx.createGain();
        master.gain.value = 0.9;
        master.connect(actx.destination);
      } catch (e) { actx = null; return null; }
    }
    if (actx.state === 'suspended') { try { actx.resume(); } catch (e) { /* ignore */ } }
    return actx;
  }

  function tone(o) {
    var c = audio();
    if (!c || muted) return;
    var t0 = c.currentTime + (o.at || 0);
    var osc = c.createOscillator();
    var g = c.createGain();
    osc.type = o.type || 'sine';
    osc.frequency.setValueAtTime(o.f, t0);
    if (o.to) osc.frequency.exponentialRampToValueAtTime(o.to, t0 + o.dur);
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(o.peak || 0.14, t0 + (o.attack || 0.012));
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + o.dur);
    osc.connect(g); g.connect(master);
    osc.start(t0); osc.stop(t0 + o.dur + 0.05);
  }

  var earcon = {
    /* soft blip: "got it, I'm looking" */
    capture: function () { tone({ f: 660, to: 990, dur: 0.09, peak: 0.11 }); },
    /* gentle rising two-tone: "I have a question" */
    question: function () {
      tone({ f: 523.25, dur: 0.16, peak: 0.13, type: 'triangle' });
      tone({ f: 659.25, dur: 0.22, peak: 0.13, type: 'triangle', at: 0.13 });
    },
    /* pleasant chime: "here is your answer" */
    verdict: function () {
      [523.25, 659.25, 783.99].forEach(function (f, i) {
        tone({ f: f, dur: 0.55, peak: 0.15, at: i * 0.09 });
        tone({ f: f * 2, dur: 0.3, peak: 0.035, at: i * 0.09 });
      });
    },
    /* soft low double tone: "careful, special item" (never alarming) */
    warning: function () {
      tone({ f: 392, dur: 0.2, peak: 0.13 });
      tone({ f: 329.63, dur: 0.26, peak: 0.13, at: 0.2 });
    },
    /* tiny sparkle for the thank-you */
    thanks: function () {
      tone({ f: 783.99, dur: 0.12, peak: 0.07 });
      tone({ f: 1046.5, dur: 0.2, peak: 0.07, at: 0.09 });
    }
  };

  /* Browsers block sound until the first tap/key press unless launched in kiosk mode. */
  function unlock() {
    audio();
    if (synth && !speechUnlocked && typeof window.SpeechSynthesisUtterance !== 'undefined') {
      try {
        var u = new window.SpeechSynthesisUtterance(' ');
        u.volume = 0;
        synth.speak(u);
        speechUnlocked = true;
      } catch (e) { /* ignore */ }
    }
  }
  function soundBlocked() {
    var ua = navigator.userActivation;
    if (ua && ua.hasBeenActive) return false;
    var c = audio();
    if (c && c.state === 'running') return false;
    return true;
  }

  /* ---------- Listening (speech recognition) ---------- */
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition || null;
  var sttBlocked = false;

  function listen(opts) {
    opts = opts || {};
    var state = function (s) { if (opts.onState) opts.onState(s); };
    if (!SR || sttBlocked) { state('unavailable'); return { available: false, stop: function () {} }; }
    var stopped = false, rec = null, restarts = 0;

    function start() {
      if (stopped) return;
      try {
        rec = new SR();
        rec.lang = i18n.speechLang(opts.lang);
        rec.interimResults = true;
        rec.maxAlternatives = 1;
        rec.continuous = false;
      } catch (e) { stopped = true; state('unavailable'); return; }
      rec.onstart = function () { state('listening'); };
      rec.onresult = function (ev) {
        var interim = '', fin = '';
        for (var i = ev.resultIndex; i < ev.results.length; i++) {
          var r = ev.results[i];
          if (r.isFinal) fin += r[0].transcript; else interim += r[0].transcript;
        }
        if (interim && opts.onInterim) opts.onInterim(interim.trim());
        fin = fin.trim();
        if (fin && !stopped) {
          stopped = true;
          try { rec.stop(); } catch (e) { /* ignore */ }
          if (opts.onFinal) opts.onFinal(fin);
        }
      };
      rec.onerror = function (ev) {
        var e = ev && ev.error;
        if (e === 'not-allowed' || e === 'service-not-allowed' || e === 'audio-capture' || e === 'language-not-supported') {
          sttBlocked = true; stopped = true; state('unavailable');
        } else if (e === 'network') {
          stopped = true; state('unavailable');      // offline right now; try again on the next question
        }
        // 'no-speech' and 'aborted' fall through to onend, which restarts while the question is open
      };
      rec.onend = function () {
        if (!stopped && restarts < 14) { restarts++; setTimeout(start, 160); }
      };
      try { rec.start(); } catch (e) { stopped = true; state('unavailable'); }
    }
    start();
    return {
      available: true,
      stop: function () {
        if (stopped) return;
        stopped = true;
        try { if (rec) rec.abort(); } catch (e) { /* ignore */ }
      }
    };
  }

  window.Sorty = window.Sorty || {};
  window.Sorty.voice = {
    speak: speak,
    cancel: cancel,
    on: on,
    earcon: earcon,
    unlock: unlock,
    soundBlocked: soundBlocked,
    listen: listen,
    canListen: function () { return !!SR && !sttBlocked; },
    canSpeak: function () { return !!synth; },
    setMuted: function (m) { muted = !!m; if (muted) { try { if (synth) synth.cancel(); } catch (e) { /* ignore */ } } },
    isMuted: function () { return muted; },
    voiceName: function (lang) { var v = pickVoice(lang); return v ? v.name : ''; }
  };
})();
