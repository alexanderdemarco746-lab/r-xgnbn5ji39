/* Sorty kiosk - talks to the brain. Uses the server's /api/* when it is there,
   otherwise (or with ?mock=1) the built-in mock brain in mock.js. Same calls either way. */
(function () {
  'use strict';
  var mock = window.Sorty.mock;
  var useMock = false;
  var config = null;

  var CONFIG_TIMEOUT = 2500;     // ms: decide quickly whether a server is there
  var TURN_TIMEOUT = 45000;      // ms: an AI turn can take a while; the screen shows "One moment..."
  var SMALL_TIMEOUT = 15000;

  function http(method, url, body, timeoutMs) {
    var ctrl = (typeof AbortController !== 'undefined') ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctrl) ctrl.abort(); }, timeoutMs);
    var opts = { method: method, cache: 'no-store', signal: ctrl ? ctrl.signal : undefined };
    if (body !== undefined && body !== null) {
      opts.headers = { 'Content-Type': 'application/json' };
      opts.body = JSON.stringify(body);
    }
    return fetch(url, opts).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status + ' from ' + url);
      return r.json();
    }).finally(function () { clearTimeout(timer); });
  }

  function validConfig(c) {
    return c && c.station && Array.isArray(c.station.bins) && c.station.bins.length >= 1 &&
      c.station.bins.every(function (b) { return b && typeof b.id === 'string'; });
  }

  /* Fill anything optional the server left out, so the rest of the app never has to check. */
  function normalize(c) {
    c.assistant_name = c.assistant_name || 'Sorty';
    c.lang_default = c.lang_default || 'en';
    c.languages = (Array.isArray(c.languages) && c.languages.length) ? c.languages : ['en'];
    var t = c.timeouts || {};
    c.timeouts = {
      answer_s: Number(t.answer_s) > 0 ? Number(t.answer_s) : 12,
      show_s: Number(t.show_s) > 0 ? Number(t.show_s) : 10,
      verdict_hold_s: Number(t.verdict_hold_s) > 0 ? Number(t.verdict_hold_s) : 8
    };
    var n = c.station.bins.length;
    c.station.bins.forEach(function (b, i) {
      if (typeof b.label === 'string') b.label = { en: b.label };
      b.label = b.label || { en: b.id };
      if (typeof b.color_name === 'string') b.color_name = { en: b.color_name };
      b.color_name = b.color_name || { en: '' };
      b.color = b.color || '#444B53';
      b.icon = b.icon || b.id;
      if (b.position !== 'left' && b.position !== 'center' && b.position !== 'right') {
        b.position = n === 1 ? 'center' : (i === 0 ? 'left' : (i === n - 1 ? 'right' : 'center'));
      }
    });
    return c;
  }

  function init() {
    var q;
    try { q = new URLSearchParams(window.location.search); } catch (e) { q = { get: function () { return null; } }; }
    if (q.get('mock') === '1') {
      useMock = true; config = normalize(mock.config());
      return Promise.resolve({ config: config, useMock: true, why: 'forced' });
    }
    return http('GET', '/api/config', null, CONFIG_TIMEOUT).then(function (c) {
      if (!validConfig(c)) throw new Error('bad config');
      useMock = false; config = normalize(c);
      return { config: config, useMock: false, why: 'server' };
    }).catch(function (err) {
      useMock = true; config = normalize(mock.config());
      return { config: config, useMock: true, why: String(err && err.message || err) };
    });
  }

  window.Sorty = window.Sorty || {};
  window.Sorty.api = {
    init: init,
    isMock: function () { return useMock; },
    config: function () { return config; },
    startSession: function (body) {
      return useMock ? mock.startSession(body) : http('POST', '/api/session', body, TURN_TIMEOUT);
    },
    reply: function (sid, body) {
      return useMock ? mock.reply(sid, body) : http('POST', '/api/session/' + encodeURIComponent(sid) + '/reply', body, TURN_TIMEOUT);
    },
    end: function (sid) {
      if (!sid) return Promise.resolve({});
      var p = useMock ? mock.end(sid) : http('POST', '/api/session/' + encodeURIComponent(sid) + '/end', {}, SMALL_TIMEOUT);
      return p.catch(function () { return {}; });
    },
    scenarios: function () {
      return useMock ? mock.scenarios() : http('GET', '/api/demo/scenarios', null, SMALL_TIMEOUT);
    },
    demoAnswer: function (body) {
      return useMock ? mock.demoAnswer(body) : http('POST', '/api/demo/answer', body, TURN_TIMEOUT);
    }
  };
})();
