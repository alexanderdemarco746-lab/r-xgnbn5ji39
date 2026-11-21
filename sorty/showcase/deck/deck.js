/* Sorty pitch deck: builds the slides from content.js and runs the motion.
   Keys: Right/Space/PageDown next, Left/PageUp back, Home/End, T timer, R reset timer, N notes, F full screen. */
(function () {
  'use strict';

  var D = window.DECK || { meta: {}, flags: {}, slides: [] };
  var S = (D.slides || []).filter(function (s) { return s && !s.skip; });   // skip: true leaves a slide out
  var $ = function (id) { return document.getElementById(id); };
  var reduce = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var cur = -1, jobs = [], started = null, clock = null, wheelLock = 0, ri = 0;

  /* ------------------------------------------------------------ small helpers */
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; });
  }
  function r(cls, html, tag) {                       // a piece that arrives in sequence
    tag = tag || 'div';
    return '<' + tag + ' class="r ' + (cls || '') + '" style="--i:' + (ri++) + '">' + html + '</' + tag + '>';
  }
  function head(s, small) {
    return (s.brand ? '<div class="brand">' + esc(s.brand) + '</div>' : '') +
      (s.kicker ? r('kicker', esc(s.kicker), 'p') : '') + r('headline' + (small ? ' sm' : ''), esc(s.headline), 'h1');
  }
  function list(s) {
    return s.body && s.body.length ? r('body', s.body.map(function (b) { return '<li>' + esc(b) + '</li>'; }).join(''), 'ul') : '';
  }
  function foot(s) { return s.foot ? r('foot', esc(s.foot), 'p') : ''; }
  function src(t) { return t ? '<span class="src">' + esc(t) + '</span>' : ''; }
  var CROSS = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';
  var TICK = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';
  function later(fn, ms) { var id = setTimeout(fn, ms); jobs.push(function () { clearTimeout(id); }); }
  function every(fn, ms) { var id = setInterval(fn, ms); jobs.push(function () { clearInterval(id); }); }

  /* ------------------------------------------------------------ one builder per layout */
  var build = {
    title: function (s) {
      var chips = s.chips || ['Looks', 'Asks', 'Lights the right bin'], colors = ['#1F6FEB', '#2DA44E', '#24292F'];
      /* optional evidence groups (slide "built"): a title, a big figure, short lines (a string, or { text, cite }), a source */
      var groups = (s.groups || []).length ? '<div class="groups">' + s.groups.map(function (g) {
        return r('group glass ' + (g.tone || ''), '<h3>' + esc(g.title) + '</h3>' +
          (g.big ? '<div class="bignum">' + esc(g.big) + '</div>' : '') +
          ((g.lines || []).length ? '<ul>' + g.lines.map(function (l) {
            return '<li>' + (typeof l === 'string' ? esc(l) : esc(l.text) + (l.cite ? '<small>' + esc(l.cite) + '</small>' : '')) + '</li>';
          }).join('') + '</ul>' : '') + src(g.source));
      }).join('') + '</div>' : '';
      return head(s) + list(s) +
        (s.button ? r('', '<a class="go sm" href="' + esc(D.meta.demoUrl || '#') + '" target="_blank" rel="noopener">' + esc(s.button) + '</a>') : '') +
        (s.showTeam ? r('team', esc(D.meta.team || ''), 'p') : '') + groups +
        '<div class="hero r" style="--i:2"><div class="frame float" data-depth="12"><img src="' + esc(s.image) + '" alt=""></div>' +
        chips.slice(0, 3).map(function (c, i) {
          return '<span class="chip glass c' + (i + 1) + ' float" data-depth="' + (30 + i * 12) + '"><i style="background:' + colors[i] + '"></i>' + esc(c) + '</span>';
        }).join('') + '</div>';
    },

    close: function (s) {
      return head(s) + list(s) + r('thanks', esc(s.thanks || ''), 'p') + r('team', esc(D.meta.team || ''), 'p') +
        '<div class="hero r" style="--i:2"><div class="frame float" data-depth="12"><img src="' + esc(s.image) + '" alt=""></div></div>';
    },

    statement: function (s) {
      var q = s.quote ? r('quote glass', '<q>' + esc(s.quote.text) + '</q>' + src(s.quote.source)) : '';
      var items = (s.items || []).map(function (it, i) {
        return '<div class="card glass r" style="--i:' + (3 + i) + '"><img class="float" data-depth="' + (16 + i * 10) + '" src="' + esc(it.image) + '" alt=""><span><b>?</b>' + esc(it.label) + '</span></div>';
      }).join('');
      return head(s) + list(s) + q + '<div class="mystery">' + items + '</div>';
    },

    cards: function (s) {
      var cards = (s.cards || []).map(function (c) {
        var imgs = c.images || (c.image ? [c.image] : []);
        var pic = imgs.length ? '<div class="pic' + (c.cutout ? ' cut' : '') + '">' + imgs.map(function (u) { return '<img src="' + esc(u) + '" alt="">'; }).join('') + '</div>' : '';
        return r('card glass ' + (c.tone || ''), pic + (c.big ? '<div class="bignum">' + esc(c.big) + '</div>' : '') +
          '<h3>' + esc(c.title) + '</h3><p>' + esc(c.text) + '</p>' + src(c.source));
      }).join('');
      var stats = (s.stats || []).map(function (f) {
        var num = f.text != null ? '<div class="num">' + esc(f.text) + '</div>'
          : '<div class="num" data-count="' + Number(f.value) + '" data-prefix="' + esc(f.prefix || '') + '" data-suffix="' + esc(f.suffix || '') + '">' + esc((f.prefix || '') + '0' + (f.suffix || '')) + '</div>';
        return r('stat glass', num + '<p>' + esc(f.label || '') + src(f.source) + '</p>');
      }).join('');
      /* gallery: a wall of everyday items that are hard to choose a bin for; the ones marked "wreck" light up red */
      var wn = 0;
      var gal = s.gallery ? (s.gallery.caption ? r('gcap', esc(s.gallery.caption), 'p') : '') +
        '<div class="gallery">' + (s.gallery.items || []).map(function (g, n) {
          if (g.ask) return '<div class="tile ask" style="--n:' + n + '"><b>?</b><span>' + esc(g.ask) + '</span></div>';
          var d = g.wreck ? 2600 + (wn++) * 230 : 0;
          return '<div class="tile' + (g.wreck ? ' bad' : '') + '" style="--n:' + n + (g.wreck ? ';--d:' + d + 'ms' : '') + '">' +
            '<img src="' + esc(g.image) + '" alt="' + esc(g.label || '') + '"><i class="q">?</i>' +
            (g.wreck ? '<em class="tag">' + esc(g.wreck) + '</em>' : '') + '</div>';
        }).join('') + '</div>' : '';
      return head(s, true) + gal +
        (cards ? '<div class="cards' + ((s.cards || []).length <= 3 ? ' few' : '') + '">' + cards + '</div>' : '') +
        (stats ? '<div class="stats">' + stats + '</div>' : '') +
        ((s.meters || []).length ? '<div class="meters">' + s.meters.map(function (m) {
          var share = m.total ? Math.max(0, Math.min(1, m.value / m.total)) : 0;
          return r('mrow glass ' + (m.tone || ''), '<p>' + esc(m.label) + '</p><b>' + esc(m.value + ' of ' + m.total) + '</b><div class="meter"><i data-share="' + share + '"></i></div>');
        }).join('') + '</div>' : '') + foot(s);
    },

    figures: function (s) {
      var figs = (s.figures || []).map(function (f) {
        if (f.placeholder) return r('fig glass todo', '<span class="tag">To fill in</span><div class="ph">' + esc(f.placeholder) + '</div><p>' + esc(f.label || '') + '</p>');
        var num = f.text != null
          ? '<div class="num txt">' + esc(f.text) + '</div>'
          : '<div class="num" data-count="' + Number(f.value) + '" data-prefix="' + esc(f.prefix || '') + '" data-suffix="' + esc(f.suffix || '') + '">' + esc((f.prefix || '') + '0' + (f.suffix || '')) + '</div>';
        return r('fig glass', num + '<p>' + esc(f.label || '') + '</p>' + src(f.source));
      }).join('');
      return head(s, true) + '<div class="figures' + ((s.figures || []).length > 4 ? ' many' : '') + '">' + figs + '</div>' + foot(s);
    },

    pipeline: function (s) {
      var steps = (s.steps || []).map(function (st, i) {
        return r('stepwrap', '<div class="step glass"><span class="n">' + (i + 1) + '</span><h3>' + esc(st.title) + '</h3><p>' + esc(st.text) + '</p></div>');
      }).join('');
      var extra = D.flags && D.flags.orchestratorLine && D.orchestratorLine ? r('extra', esc(D.orchestratorLine), 'p') : '';
      return head(s, true) + '<div class="pipe"><i class="rail"></i>' + steps + '</div>' + foot(s) + extra;
    },

    moves: function (s) {
      var m = s.moves || [], ys = [44, 188, 332, 476];
      var imgs = m.map(function (x) { return '<img src="' + esc(x.image) + '" alt="">'; }).join('');
      var paths = '<path class="in on" d="M0 260 L52 260"/>' + m.map(function (x, i) {
        return '<path class="out" d="M196 260 C 228 260, 216 ' + ys[i] + ', 250 ' + ys[i] + '"/>';
      }).join('');
      var cards = m.map(function (x) {
        return r('movewrap', '<div class="move glass"><h3>' + esc(x.name) + '<small>' + esc(x.when) + '</small></h3><p>' + esc(x.example) + '</p></div>');
      }).join('');
      return head(s, true) + '<div class="moves">' +
        r('cam glass', imgs) +
        r('wires', '<svg viewBox="0 0 250 520" preserveAspectRatio="none">' + paths + '</svg><span class="ai">AI</span>') +
        '<div class="movelist">' + cards + '</div></div>' + foot(s);
    },

    compare: function (s) {
      var b = s.branches || [], ys = [102, 368];
      var start = r('start', '<div class="float" data-depth="14"><img src="' + esc(s.start.image) + '" alt=""></div><span class="say glass">' + esc(s.start.say) + '</span>');
      var fork = r('fork', '<svg viewBox="0 0 190 470" preserveAspectRatio="none">' + b.map(function (x, i) {
        return '<path stroke="' + esc(x.color) + '" d="M0 235 C 100 235, 90 ' + ys[i] + ', 190 ' + ys[i] + '"/>';
      }).join('') + '</svg>');
      var rows = b.map(function (x) {
        return r('branch glass', '<img src="' + esc(x.image) + '" alt=""><p><b>' + esc(x.say) + '</b>' + esc(x.finding) + '</p><span class="bin" style="--c:' + esc(x.color) + '">' + esc(x.bin) + '</span>');
      }).join('');
      return head(s, true) + '<div class="compare">' + start + fork + '<div class="branches">' + rows + '</div></div>' + foot(s);
    },

    demo: function (s) {
      var left = r('', '<a class="go" href="' + esc(D.meta.demoUrl || '#') + '" target="_blank" rel="noopener">' + esc(s.button || 'Open the live demo') + '</a>') + list(s) + foot(s);
      var right = r('', '<div class="screen3d"><video src="' + esc(s.video) + '" poster="' + esc(s.poster || '') + '" muted loop playsinline preload="metadata"></video><span class="live">THE STATION</span></div>');
      return head(s) + '<div class="demo"><div>' + left + '</div>' + right + '</div>';
    },

    /* one camera frame, two models at once: the fast lane lands first with a red stop, the careful lane goes on */
    lanes: function (s) {
      var f = s.fast || {}, c = s.careful || {}, se = s.sensor || {}, fr = s.frame || {};
      var left = r('lsrc',
        '<div class="sensor glass"><i></i><b>' + esc(se.title || 'Sensor') + '</b><small>' + esc(se.text || '') + '</small></div>' +
        '<div class="shot glass"><img src="' + esc(fr.image || '') + '" alt=""><small>' + esc(fr.text || '') + '</small></div>');
      var split = r('split2', '<svg viewBox="0 0 110 480" preserveAspectRatio="none"><path class="p1" d="M0 318 C 70 318, 40 102, 110 102"/><path class="p2" d="M0 318 C 60 318, 50 388, 110 388"/></svg>');
      function lane(cls, x, mid, endCls) {
        return r('lane glass ' + cls,
          '<div class="lmain"><div class="lhead"><h3>' + esc(x.title || '') + '</h3><span class="model">' + esc(x.model || '') + '</span></div>' +
          mid + '</div>' +
          '<div class="end ' + endCls + '"><b>' + esc(x.end || '') + '</b><small>' + esc(x.endNote || '') + '</small></div>');
      }
      var track = '<div class="track"><i class="fill"></i></div>';
      var fastMid = '<p class="q">' + esc(f.text || '') + '</p>' + track +
        (D.alertMeasured ? '<p class="measured"><b>' + esc(s.measuredLabel || 'Alert:') + '</b> ' + esc(D.alertMeasured) + '</p>' : '');
      var carefulMid = ((c.agents || []).length
          ? '<div class="agents">' + c.agents.map(function (a) { return '<span><b>' + esc(a.name) + '</b><small>' + esc(a.does || '') + '</small></span>'; }).join('') + '</div>'
          : '<div class="stages">' + (c.stages || []).map(function (t) { return '<span>' + esc(t) + '</span>'; }).join('') + '</div>') +
        (c.text ? '<p class="q">' + esc(c.text) + '</p>' : '') + track +
        (c.result ? '<p class="measured"><b>' + esc(s.measuredLabel || 'Measured:') + '</b> ' + esc(c.result) + '</p>' : '');
      var extra = D.flags && D.flags.orchestratorLine && D.orchestratorLine ? r('extra', esc(D.orchestratorLine), 'p') : '';
      return head(s, true) + '<div class="lanes">' + left + split + '<div class="lanecol">' +
        lane('fast', f, fastMid, 'stop') + lane('careful', c, carefulMid, 'answer') + '</div></div>' + foot(s) + extra;
    },

    /* items people put in the wrong bin: the usual guess with a cross, then Sorty's answer with a tick */
    flip: function (s) {
      var cards = (s.cards || []).map(function (c) {
        var w = c.wrong || {}, g = c.right || {};
        return r('flipwrap', '<div class="flipcard glass">' +
          '<div class="pic"><img src="' + esc(c.image) + '" alt=""></div>' +
          '<h3>' + esc(c.name) + '</h3>' +
          (c.claim ? '<p class="claim">' + esc(c.claim) + '</p>' : '') +
          '<div class="guess wrong" style="--c:' + esc(w.color || '#24292F') + '"><small>' + esc(s.wrongLabel || 'Most people') + '</small>' +
            '<span class="pill"><i class="mark">' + CROSS + '</i><b>' + esc(w.label) + '</b></span></div>' +
          '<div class="guess right" style="--c:' + esc(g.color || '#2DA44E') + '"><small>' + esc(s.rightLabel || 'Sorty') + '</small>' +
            '<span class="pill"><i class="mark">' + TICK + '</i><b>' + esc(g.label) + '</b></span>' + (c.why ? '<p>' + esc(c.why) + '</p>' : '') + '</div>' +
          src(c.source) + '</div>');
      }).join('');
      return head(s, true) + '<div class="flips">' + cards + '</div>' + foot(s);
    },

    /* two results side by side; a side without a number shows as a dashed "to fill in" tile */
    versus: function (s) {
      var total = Number(s.total) || 0;
      var sides = (s.sides || []).map(function (x) {
        var has = typeof x.value === 'number';
        var share = has && total ? Math.max(0, Math.min(1, x.value / total)) : 0;
        return r('vs glass ' + (x.tone || '') + (has ? '' : ' todo'),
          (has ? '' : '<span class="tag">To fill in</span>') +
          '<h3>' + esc(x.name) + '</h3>' + (x.detail ? '<p class="detail">' + esc(x.detail) + '</p>' : '') +
          '<div class="score">' + (has
            ? '<span class="num" data-count="' + x.value + '" data-prefix="" data-suffix="">0</span>'
            : '<span class="num ph">' + esc(x.placeholder || '[?]') + '</span>') +
          '<span class="of">' + esc(s.unit || ('of ' + total)) + '</span></div>' +
          '<div class="meter"><i data-share="' + share + '"></i></div>' +
          (x.sub ? '<p class="sub">' + esc(x.sub) + '</p>' : ''));
      });
      return head(s, true) + '<div class="versus">' + (sides[0] || '') + r('mid', '<span>vs</span>') + (sides[1] || '') + '</div>' + foot(s);
    },

    split: function (s) {
      var cols = (s.columns || []).map(function (c) {
        return r('col glass ' + (c.tone || ''), '<h3>' + esc(c.title) + '</h3><ul>' + (c.lines || []).map(function (l) { return '<li>' + esc(l) + '</li>'; }).join('') + '</ul>');
      }).join('');
      return head(s, true) + '<div class="split">' + cols + '</div>' + foot(s);
    }
  };

  function render() {
    var wrap = $('slides'), dots = $('dots');
    wrap.innerHTML = S.map(function (s) {
      ri = 0;
      var fn = build[s.layout] || build.cards;
      return '<section class="slide l-' + esc(s.layout) + '" data-id="' + esc(s.id) + '">' + fn(s) + '</section>';
    }).join('');
    dots.innerHTML = S.map(function (s, i) {
      return '<button type="button" aria-label="Slide ' + (i + 1) + ': ' + esc(s.kicker || s.headline || s.id) + '"></button>';
    }).join('');
    Array.prototype.forEach.call(dots.children, function (b, i) { b.addEventListener('click', function () { b.blur(); go(i); }); });
    Array.prototype.forEach.call(wrap.querySelectorAll('.flipcard'), function (card) {
      card.addEventListener('click', function () { card.classList.toggle('flipped'); });
    });
    document.title = (D.meta.title || 'Sorty') + ': pitch';
  }

  /* ------------------------------------------------------------ what moves inside a slide */
  function countUp(el) {
    var end = Number(el.dataset.count) || 0, pre = el.dataset.prefix || '', suf = el.dataset.suffix || '';
    if (reduce) { el.textContent = pre + end + suf; return; }
    var t0 = null, dur = 1200, raf;
    function frame(t) {
      if (t0 === null) t0 = t;
      var p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
      el.textContent = pre + Math.round(end * e) + suf;
      if (p < 1) raf = requestAnimationFrame(frame);
    }
    el.textContent = pre + '0' + suf;
    later(function () { raf = requestAnimationFrame(frame); jobs.push(function () { cancelAnimationFrame(raf); }); }, 520);
  }

  function runPipeline(sl) {
    var steps = sl.querySelectorAll('.step'), rail = sl.querySelector('.rail'), n = steps.length, k = -1;
    function paint() {
      Array.prototype.forEach.call(steps, function (st, i) { st.classList.toggle('on', i === k); st.classList.toggle('done', i < k); });
      if (rail) rail.style.width = k < 0 ? '0' : (92 * k / Math.max(1, n - 1)) + '%';
    }
    if (reduce) { k = n - 1; paint(); return; }
    paint();
    later(function () {
      k = 0; paint();
      var hold = 0;
      every(function () {
        if (k < n - 1) { k++; paint(); return; }
        if (++hold < 3) return;                       // rest on the last step, then start over
        hold = 0; k = -1; paint();
        later(function () { k = 0; paint(); }, 500);
      }, 1250);
    }, 1100);
  }

  function runMoves(sl) {
    var cams = sl.querySelectorAll('.cam img'), outs = sl.querySelectorAll('.wires path.out'), cards = sl.querySelectorAll('.move'), n = cards.length, k = 0;
    function paint(all) {
      for (var i = 0; i < n; i++) {
        var on = all || i === k;
        if (cams[i]) cams[i].classList.toggle('on', i === k);
        if (outs[i]) outs[i].classList.toggle('on', on);
        cards[i].classList.toggle('on', on);
      }
    }
    if (reduce) { paint(true); return; }
    paint(false);
    every(function () { k = (k + 1) % n; paint(false); }, 2500);
  }

  function enter(sl) {
    Array.prototype.forEach.call(sl.querySelectorAll('.num[data-count]'), countUp);
    if (sl.classList.contains('l-pipeline')) runPipeline(sl);
    if (sl.classList.contains('l-moves')) runMoves(sl);
    var lanes = sl.querySelector('.lanes');
    if (lanes) {
      if (reduce) lanes.classList.add('run');
      else {
        later(function () { lanes.classList.add('run'); }, 1300);
        every(function () {                              // start over: both lanes leave together again
          lanes.classList.remove('run');
          later(function () { lanes.classList.add('run'); }, 700);
        }, 10000);
      }
    }
    Array.prototype.forEach.call(sl.querySelectorAll('.flipcard'), function (card, i) {
      if (reduce) { card.classList.add('flipped'); return; }
      later(function () { card.classList.add('flipped'); }, 1700 + i * 650);
    });
    Array.prototype.forEach.call(sl.querySelectorAll('.meter i'), function (bar) {
      var w = (Number(bar.dataset.share) || 0) * 100 + '%';
      if (reduce) { bar.style.width = w; return; }
      later(function () { bar.style.width = w; }, 900);
    });
    var v = sl.querySelector('video');
    if (v) { try { v.currentTime = 0; var p = v.play(); if (p && p.catch) p.catch(function () {}); } catch (e) { /* poster stays */ } }
  }
  function leave(sl) {
    jobs.forEach(function (stop) { stop(); }); jobs = [];
    if (!sl) return;
    Array.prototype.forEach.call(sl.querySelectorAll('.flipcard'), function (card) { card.classList.remove('flipped'); });
    Array.prototype.forEach.call(sl.querySelectorAll('.lanes'), function (box) { box.classList.remove('run'); });
    Array.prototype.forEach.call(sl.querySelectorAll('.meter i'), function (bar) { bar.style.width = '0'; });
    var v = sl.querySelector('video');
    if (v) { try { v.pause(); } catch (e) { /* ignore */ } }
  }

  /* ------------------------------------------------------------ moving between slides */
  function go(i, quiet) {
    i = Math.max(0, Math.min(S.length - 1, i));
    if (i === cur) return;
    var all = $('slides').children;
    if (cur >= 0) leave(all[cur]);
    for (var j = 0; j < all.length; j++) {
      all[j].classList.toggle('is-active', j === i);
      all[j].classList.toggle('is-past', j < i);
    }
    Array.prototype.forEach.call($('dots').children, function (b, j) { b.classList.toggle('on', j === i); });
    $('bar').style.width = (S.length > 1 ? (100 * i / (S.length - 1)) : 100) + '%';
    cur = i;
    enter(all[i]);
    notes();
    if (!quiet) { try { history.replaceState(null, '', '#/' + i); } catch (e) { location.hash = '#/' + i; } }
  }
  function next() { if (started === null && cur >= 0) startTimer(); go(cur + 1); }
  function prev() { go(cur - 1); }
  function fromHash() { var m = /#\/(\d+)/.exec(location.hash || ''); return m ? parseInt(m[1], 10) : 0; }

  /* ------------------------------------------------------------ presenter aids */
  function startTimer() { started = Date.now(); drawTimer(); if (!clock) clock = setInterval(drawTimer, 250); }
  function resetTimer() { started = null; if (clock) { clearInterval(clock); clock = null; } drawTimer(); }
  function fmt(sec) { sec = Math.max(0, Math.floor(sec)); return Math.floor(sec / 60) + ':' + ('0' + (sec % 60)).slice(-2); }
  function drawTimer() {
    var el = $('timer'), target = Number(D.meta.targetSeconds) || 180, sec = started === null ? 0 : (Date.now() - started) / 1000;
    el.textContent = fmt(sec) + ' / ' + fmt(target);
    el.classList.toggle('warn', sec >= target - 30 && sec < target);
    el.classList.toggle('over', sec >= target);
  }
  function notes() {
    var s = S[cur] || {};
    $('notesTitle').textContent = 'Slide ' + (cur + 1) + ' of ' + S.length + (s.kicker ? ': ' + s.kicker : '');
    $('notesText').textContent = s.notes || '';
  }
  function fullscreen() {
    try {
      if (document.fullscreenElement) document.exitFullscreen();
      else document.documentElement.requestFullscreen();
    } catch (e) { /* not allowed here */ }
  }

  /* ------------------------------------------------------------ input */
  document.addEventListener('keydown', function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    var k = e.key;
    if (k === 'ArrowRight' || k === 'PageDown' || k === ' ' || k === 'Spacebar' || k === 'ArrowDown') { e.preventDefault(); next(); }
    else if (k === 'ArrowLeft' || k === 'PageUp' || k === 'Backspace' || k === 'ArrowUp') { e.preventDefault(); prev(); }
    else if (k === 'Home') go(0);
    else if (k === 'End') go(S.length - 1);
    else if (k === 't' || k === 'T') { $('timer').hidden = !$('timer').hidden; drawTimer(); }
    else if (k === 'r' || k === 'R') resetTimer();
    else if (k === 'n' || k === 'N') $('notes').hidden = !$('notes').hidden;
    else if (k === 'f' || k === 'F') fullscreen();
  });
  window.addEventListener('wheel', function (e) {
    var now = Date.now();
    if (now < wheelLock || Math.abs(e.deltaY) < 24) return;
    if ($('notes').contains(e.target)) return;
    wheelLock = now + 950;
    if (e.deltaY > 0) next(); else prev();
  }, { passive: true });
  var touch = null;
  window.addEventListener('touchstart', function (e) { var t = e.changedTouches[0]; touch = { x: t.clientX, y: t.clientY }; }, { passive: true });
  window.addEventListener('touchend', function (e) {
    if (!touch) return;
    var t = e.changedTouches[0], dx = t.clientX - touch.x, dy = t.clientY - touch.y; touch = null;
    if (Math.max(Math.abs(dx), Math.abs(dy)) < 60) return;
    if (Math.abs(dx) > Math.abs(dy)) { if (dx < 0) next(); else prev(); } else { if (dy < 0) next(); else prev(); }
  }, { passive: true });
  window.addEventListener('hashchange', function () { go(fromHash(), true); });

  /* depth: things nearer to the viewer move more when the pointer moves */
  var want = { x: 0, y: 0 }, queued = false;
  function parallax() {
    queued = false;
    var root = document.documentElement;
    root.style.setProperty('--px', want.x.toFixed(3));
    root.style.setProperty('--py', want.y.toFixed(3));
    var sl = $('slides').children[cur];
    if (!sl) return;
    Array.prototype.forEach.call(sl.querySelectorAll('.float[data-depth]'), function (el) {
      var d = Number(el.dataset.depth) || 0;
      el.style.transform = 'translate3d(' + (want.x * d).toFixed(1) + 'px,' + (want.y * d * 0.6).toFixed(1) + 'px,0)';
    });
  }
  if (!reduce) {
    window.addEventListener('pointermove', function (e) {
      want.x = (e.clientX / window.innerWidth) * 2 - 1;
      want.y = (e.clientY / window.innerHeight) * 2 - 1;
      if (!queued) { queued = true; requestAnimationFrame(parallax); }
    }, { passive: true });
  }

  /* the 1920x1080 canvas always fits the window */
  function fit() {
    var k = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
    document.documentElement.style.setProperty('--k', (k > 0 ? k : 1).toFixed(4));
  }
  window.addEventListener('resize', fit);

  fit();
  render();
  drawTimer();
  go(fromHash(), true);

  window.SortyDeck = { go: go, next: next, prev: prev, state: function () { return { slide: cur, of: S.length, id: S[cur] && S[cur].id, timerStarted: started !== null }; } };
})();
