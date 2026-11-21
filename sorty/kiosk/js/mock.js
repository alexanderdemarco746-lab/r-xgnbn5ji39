/* Sorty kiosk - built-in MOCK brain.
   Used automatically when the server's /api/config cannot be reached (or with ?mock=1), so the
   whole interface can be shown with no server and no AI key. It plays scripted turns that cover
   every turn type in the API contract. Extras for testing: ?bins=2 (two-bin station), ?slow=1. */
(function () {
  'use strict';
  var i18n = window.Sorty.i18n;
  var q;
  try { q = new URLSearchParams(window.location.search); } catch (e) { q = { get: function () { return null; } }; }
  var twoBins = q.get('bins') === '2';
  var slow = q.get('slow') === '1';

  function L(en, es) { return { en: en, es: es }; }

  var RECYCLE = { id: 'recycle', label: L('Recycle', 'Reciclaje'), color: '#1F6FEB', color_name: L('blue', 'azul'), position: 'left', icon: 'recycle' };
  var COMPOST = { id: 'compost', label: L('Compost', 'Composta'), color: '#2DA44E', color_name: L('green', 'verde'), position: 'center', icon: 'compost' };
  var LANDFILL = { id: 'landfill', label: L('Landfill', 'Basura'), color: '#24292F', color_name: L('black', 'negro'), position: 'right', icon: 'landfill' };

  var CONFIG = {
    assistant_name: 'Sorty',
    mode: 'mock',
    lang_default: 'en',
    languages: ['en', 'es'],
    station: { id: twoBins ? '2bin' : '3bin', bins: twoBins ? [RECYCLE, LANDFILL] : [RECYCLE, COMPOST, LANDFILL] },
    timeouts: { answer_s: 12, show_s: 10, verdict_hold_s: 8 }
  };

  /* ---------- small helpers ---------- */
  function isLoc(v) { return v && typeof v === 'object' && !Array.isArray(v) && typeof v.en === 'string'; }
  function loc(v, lang) {
    if (isLoc(v)) return v[lang] || v.en;
    if (Array.isArray(v)) return v.map(function (x) { return loc(x, lang); });
    if (v && typeof v === 'object') { var o = {}; Object.keys(v).forEach(function (k) { o[k] = loc(v[k], lang); }); return o; }
    return v;
  }
  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
  var POS = { left: L('on your left', 'a tu izquierda'), center: L('in the middle', 'en el centro'), right: L('on your right', 'a tu derecha') };

  /* A station without compost sends compostables to the last bin (landfill). */
  function binFor(id) {
    var bins = CONFIG.station.bins;
    for (var i = 0; i < bins.length; i++) if (bins[i].id === id) return bins[i];
    return bins[bins.length - 1];
  }
  function where(id) {
    var b = binFor(id);
    return L(cap(b.color_name.en) + ' bin, ' + POS[b.position].en, 'Contenedor ' + b.color_name.es + ', ' + POS[b.position].es);
  }
  function binStep(id, item) {
    var b = binFor(id);
    return { kind: 'bin', item: item, bin: b.id, position: b.position, text: where(id) };
  }
  function sent(v) { return L(v.en + '.', v.es + '.'); }
  function join() {
    var parts = Array.prototype.slice.call(arguments);
    return L(parts.map(function (p) { return isLoc(p) ? p.en : p; }).join(' '),
             parts.map(function (p) { return isLoc(p) ? p.es : p; }).join(' '));
  }
  var YESNO = [
    { id: 'yes', label: L('Yes', 'Sí') },
    { id: 'no', label: L('No', 'No') },
    { id: 'unsure', label: L('Not sure', 'No sé') }
  ];
  function plain(t) { return String(t || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); }
  function saysUnsure(t) { return /(not sure|unsure|no se|don'?t know|dunno|maybe|quizas)/.test(plain(t)); }
  function saysYes(t) { return !saysUnsure(t) && /(yes|yeah|yep|yup|sure|some|little|half|full|si|un poco|algo|mitad)/.test(plain(t)); }
  function saysNo(t) { return !saysUnsure(t) && /(no|nope|empty|nothing|vacia|vacio|nada)/.test(plain(t)); }

  /* ---------- placeholder pictures (canvas-drawn, stand-ins for camera frames) ---------- */
  var FONT = '"Segoe UI",system-ui,-apple-system,Arial,sans-serif';
  function picture(fn) {
    var c = document.createElement('canvas');
    c.width = 640; c.height = 480;
    var x = c.getContext('2d');
    var g = x.createLinearGradient(0, 0, 0, 480);
    g.addColorStop(0, '#e4e8ed'); g.addColorStop(0.6, '#cfd5dc'); g.addColorStop(0.6, '#b8b1a4'); g.addColorStop(1, '#a59d8e');
    x.fillStyle = g; x.fillRect(0, 0, 640, 480);
    fn(x);
    return c.toDataURL('image/jpeg', 0.9);
  }
  function shadow(x, cx, cy, rx, ry) {
    x.save(); x.fillStyle = 'rgba(0,0,0,.18)'; x.beginPath(); x.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2); x.fill(); x.restore();
  }
  function poly(x, pts, fill, stroke) {
    x.beginPath();
    pts.forEach(function (p, i) { if (i) x.lineTo(p[0], p[1]); else x.moveTo(p[0], p[1]); });
    x.closePath();
    if (fill) { x.fillStyle = fill; x.fill(); }
    if (stroke) { x.strokeStyle = stroke; x.lineWidth = 3; x.stroke(); }
  }
  function rrect(x, X, Y, W, H, R, fill, stroke) {
    x.beginPath();
    if (x.roundRect) x.roundRect(X, Y, W, H, R); else x.rect(X, Y, W, H);
    if (fill) { x.fillStyle = fill; x.fill(); }
    if (stroke) { x.strokeStyle = stroke; x.lineWidth = 3; x.stroke(); }
  }
  function label(x, s, X, Y, size, color) {
    x.fillStyle = color; x.font = '800 ' + size + 'px ' + FONT; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(s, X, Y);
  }
  function dot(x, X, Y, r, fill) { x.fillStyle = fill; x.beginPath(); x.arc(X, Y, r, 0, Math.PI * 2); x.fill(); }

  var draw = {
    pizzaClosed: function (x) {
      shadow(x, 320, 378, 232, 24);
      poly(x, [[170, 190], [470, 190], [530, 330], [110, 330]], '#c9995a', '#8a6230');
      poly(x, [[110, 330], [530, 330], [530, 374], [110, 374]], '#a87a40', '#8a6230');
      x.save(); x.translate(320, 262); x.transform(1, 0, 0, 0.6, 0, 0); label(x, 'PIZZA', 0, 0, 70, '#b3261e'); x.restore();
    },
    pizzaOpen: function (x) {
      shadow(x, 320, 396, 242, 24);
      poly(x, [[178, 70], [462, 70], [470, 196], [170, 196]], '#b98a4b', '#8a6230');
      label(x, 'PIZZA', 320, 132, 44, 'rgba(140,40,30,.5)');
      poly(x, [[170, 196], [470, 196], [536, 350], [104, 350]], '#d9b37b', '#8a6230');
      poly(x, [[104, 350], [536, 350], [536, 392], [104, 392]], '#a87a40', '#8a6230');
      [[250, 268, 72, 36], [384, 248, 54, 28], [330, 316, 92, 22], [198, 322, 40, 16], [446, 310, 46, 20]].forEach(function (b) {
        x.fillStyle = 'rgba(112,62,14,.5)'; x.beginPath(); x.ellipse(b[0], b[1], b[2], b[3], 0, 0, Math.PI * 2); x.fill();
      });
      [[230, 240], [300, 290], [352, 262], [410, 300], [270, 326], [380, 330], [322, 232]].forEach(function (p) { dot(x, p[0], p[1], 4, '#8a5a1c'); });
      [[290, 250], [404, 276], [246, 300]].forEach(function (p) { poly(x, [[p[0], p[1]], [p[0] + 16, p[1] + 4], [p[0] + 6, p[1] + 14]], '#f0c64a'); });
    },
    can: function (x, ox) {
      ox = ox || 320;
      shadow(x, ox, 394, 76, 15);
      var g = x.createLinearGradient(ox - 56, 0, ox + 56, 0);
      g.addColorStop(0, '#8f1410'); g.addColorStop(0.35, '#e0362d'); g.addColorStop(0.7, '#c2231c'); g.addColorStop(1, '#7c100c');
      rrect(x, ox - 56, 150, 112, 240, 14, g, '#5c0c09');
      x.fillStyle = '#c9ced4'; x.beginPath(); x.ellipse(ox, 152, 56, 13, 0, 0, Math.PI * 2); x.fill();
      x.strokeStyle = '#8d949c'; x.lineWidth = 3; x.stroke();
      x.fillStyle = '#9aa1a9'; x.beginPath(); x.ellipse(ox, 152, 40, 8, 0, 0, Math.PI * 2); x.fill();
      label(x, 'COLA', ox, 270, 34, '#fff');
      x.fillStyle = 'rgba(255,255,255,.18)'; x.fillRect(ox - 40, 172, 12, 200);
    },
    chipBag: function (x) {
      shadow(x, 320, 400, 152, 18);
      x.save(); x.translate(320, 250); x.rotate(-0.08);
      poly(x, [[-120, -130], [120, -130], [134, 120], [-134, 120]], '#f2b705', '#b8860b');
      x.fillStyle = '#d99e04'; x.fillRect(-120, -146, 240, 18); x.fillRect(-134, 118, 268, 18);
      rrect(x, -96, -64, 192, 96, 48, '#c62828');
      label(x, 'CHIPS', 0, -16, 46, '#fff');
      x.fillStyle = 'rgba(255,255,255,.28)'; x.beginPath(); x.ellipse(-70, -100, 26, 10, -0.4, 0, Math.PI * 2); x.fill();
      x.restore();
    },
    banana: function (x, ox, oy, s) {
      x.save(); x.translate(ox || 320, oy || 290); x.scale(s || 1, s || 1);
      shadow(x, 0, 74, 160, 20);
      x.fillStyle = '#f4d03f'; x.strokeStyle = '#b7950b'; x.lineWidth = 4;
      [-0.25, 1.95, 3.55].forEach(function (a) {
        x.save(); x.rotate(a); x.beginPath(); x.moveTo(0, 0);
        x.bezierCurveTo(30, -34, 120, -42, 172, 18); x.bezierCurveTo(120, 8, 50, 30, 0, 26);
        x.closePath(); x.fill(); x.stroke(); x.restore();
      });
      dot(x, 0, 12, 14, '#6e4b1a');
      [[70, -12], [112, -2], [-58, 44], [-92, 66], [-20, -80]].forEach(function (p) { dot(x, p[0], p[1], 5, 'rgba(110,75,26,.65)'); });
      x.restore();
    },
    bottle: function (x, ox, oy, s) {
      x.save(); x.translate(ox || 320, oy || 250); x.scale(s || 1, s || 1);
      shadow(x, 0, 152, 62, 13);
      x.fillStyle = 'rgba(160,210,240,.4)'; x.strokeStyle = 'rgba(60,120,160,.9)'; x.lineWidth = 4;
      x.beginPath(); x.moveTo(-18, -150); x.lineTo(18, -150); x.lineTo(18, -118);
      x.bezierCurveTo(50, -100, 50, -80, 50, -60); x.lineTo(50, 130); x.quadraticCurveTo(50, 148, 32, 148);
      x.lineTo(-32, 148); x.quadraticCurveTo(-50, 148, -50, 130); x.lineTo(-50, -60);
      x.bezierCurveTo(-50, -80, -50, -100, -18, -118); x.closePath(); x.fill(); x.stroke();
      rrect(x, -20, -172, 40, 24, 5, '#1e88e5', '#125a9c');
      x.strokeStyle = 'rgba(255,255,255,.75)'; x.lineWidth = 5; x.beginPath(); x.moveTo(-34, -50); x.lineTo(-34, 110); x.stroke();
      x.restore();
    },
    battery: function (x) {
      [[300, 210], [344, 300]].forEach(function (p) {
        var cx = p[0], cy = p[1];
        shadow(x, cx, cy + 36, 124, 10);
        var g = x.createLinearGradient(0, cy - 30, 0, cy + 30);
        g.addColorStop(0, '#444'); g.addColorStop(0.5, '#111'); g.addColorStop(1, '#2c2c2c');
        rrect(x, cx - 110, cy - 30, 184, 60, 10, g, '#000');
        rrect(x, cx + 70, cy - 30, 46, 60, 8, '#d4a017', '#8a6a0c');
        rrect(x, cx + 116, cy - 12, 12, 24, 3, '#c0c0c0', '#777');
        label(x, 'AA', cx - 30, cy, 30, '#f5c518'); label(x, '+', cx + 93, cy, 34, '#3a2a00');
      });
    },
    phone: function (x) {
      shadow(x, 320, 400, 112, 16);
      x.save(); x.translate(320, 240); x.rotate(0.12);
      rrect(x, -92, -170, 184, 340, 26, '#15181d', '#000');
      var g = x.createLinearGradient(-80, -150, 80, 150); g.addColorStop(0, '#3949ab'); g.addColorStop(1, '#00acc1');
      rrect(x, -80, -156, 160, 312, 16, g);
      dot(x, 0, -144, 6, '#0b0d10'); label(x, '12:30', 0, -60, 36, '#fff');
      x.restore();
    },
    tiedBag: function (x) {
      shadow(x, 320, 400, 172, 20);
      x.fillStyle = '#f3f3f1'; x.strokeStyle = '#b9b9b4'; x.lineWidth = 4;
      x.beginPath(); x.moveTo(300, 150); x.bezierCurveTo(180, 170, 140, 300, 190, 380);
      x.bezierCurveTo(260, 410, 400, 410, 450, 380); x.bezierCurveTo(500, 300, 460, 170, 340, 150); x.closePath(); x.fill(); x.stroke();
      x.beginPath(); x.moveTo(305, 150); x.bezierCurveTo(270, 110, 250, 90, 270, 80); x.bezierCurveTo(300, 90, 315, 120, 320, 148); x.closePath(); x.fill(); x.stroke();
      x.beginPath(); x.moveTo(335, 150); x.bezierCurveTo(360, 105, 385, 90, 372, 78); x.bezierCurveTo(345, 88, 328, 120, 322, 148); x.closePath(); x.fill(); x.stroke();
      x.strokeStyle = 'rgba(120,120,115,.5)'; x.lineWidth = 3; x.beginPath();
      x.moveTo(320, 170); x.quadraticCurveTo(300, 260, 260, 360); x.moveTo(330, 170); x.quadraticCurveTo(360, 270, 400, 370); x.stroke();
    },
    cupSide: function (x) {
      shadow(x, 320, 394, 86, 16);
      x.fillStyle = 'rgba(200,225,240,.45)'; x.strokeStyle = 'rgba(70,120,150,.9)'; x.lineWidth = 4;
      x.beginPath(); x.moveTo(236, 140); x.lineTo(404, 140); x.lineTo(378, 388); x.lineTo(262, 388); x.closePath(); x.fill(); x.stroke();
      x.beginPath(); x.ellipse(320, 140, 84, 16, 0, 0, Math.PI * 2); x.stroke();
      x.strokeStyle = 'rgba(255,255,255,.8)'; x.lineWidth = 5; x.beginPath(); x.moveTo(262, 170); x.lineTo(280, 360); x.stroke();
    },
    cupBottom: function (x) {
      x.fillStyle = 'rgba(205,228,240,.75)'; x.strokeStyle = 'rgba(70,120,150,.9)'; x.lineWidth = 6;
      x.beginPath(); x.arc(320, 240, 172, 0, Math.PI * 2); x.fill(); x.stroke();
      x.strokeStyle = '#2da44e'; x.lineWidth = 10; x.beginPath(); x.arc(320, 240, 140, 0, Math.PI * 2); x.stroke();
      label(x, 'COMPOSTABLE', 320, 214, 32, '#1c6630'); label(x, 'PLA  7', 320, 268, 40, '#1c6630');
    },
    blurry: function (x) {
      x.save(); x.filter = 'blur(11px)'; draw.chipBag(x); x.restore();
      x.fillStyle = 'rgba(10,12,16,.5)'; x.fillRect(0, 0, 640, 480);
    },
    empty: function () { /* just the backdrop */ },
    hiccup: function (x) {
      shadow(x, 320, 384, 150, 18);
      rrect(x, 200, 150, 240, 230, 22, '#8d99a6', '#5e6975');
      label(x, '?', 320, 266, 150, '#fff');
    },
    two: function (x) { draw.banana(x, 214, 318, 0.78); draw.bottle(x, 452, 248, 0.92); }
  };

  /* ---------- scripted scenarios ---------- */
  var G = {
    look: L('Needs a second look', 'Necesita mirar otra vez'),
    ask: L('Needs a question', 'Necesita una pregunta'),
    see: L('Sees it right away', 'Lo ve de inmediato'),
    special: L('Special cases', 'Casos especiales'),
    edge: L('Edge cases', 'Casos límite')
  };

  function verdict(primary, steps, reason, extra) {
    var v = { primary_bin: primary, steps: steps, reason: reason, special_dest: null, confidence: 'high' };
    if (extra) Object.keys(extra).forEach(function (k) { v[k] = extra[k]; });
    return v;
  }

  var SCENARIOS = [
    {
      id: 'pizza_box', title: L('Pizza box, closed', 'Caja de pizza cerrada'), group: G.look,
      frames: { initial: 'pizzaClosed', open_show_inside: 'pizzaOpen' },
      start: function () {
        return { type: 'show',
          trace: [['look', L('Closed pizza box. I cannot see the inside.', 'Caja de pizza cerrada. No veo el interior.')],
                  ['think', L('Grease decides the bin, so I need a look inside.', 'La grasa decide el contenedor; necesito ver el interior.')],
                  ['show', L('Asked the person to open the box.', 'Pedí que abran la caja.')]],
          say: L('Open the box and show me the inside.', 'Abre la caja y muéstrame el interior.'),
          display: { headline: L('Open the box', 'Abre la caja'), sub: L('Show me the inside.', 'Muéstrame el interior.'), item_label: L('Pizza box', 'Caja de pizza'), icon: 'open' },
          show: { action: 'open_show_inside', hint: L('Open the box', 'Abre la caja') } };
      },
      reply: function () {
        var b = binFor('compost');
        return { type: 'verdict',
          trace: [['frame', L('New view: the box is open.', 'Nueva vista: la caja está abierta.')],
                  ['specialist', L('Grease check: heavy stains on about 40% of the base.', 'Revisión de grasa: manchas fuertes en un 40% de la base.')],
                  ['verdict', L('Greasy cardboard cannot be recycled.', 'El cartón grasoso no se recicla.')]],
          say: join(L('Greasy box.', 'Caja grasosa.'), sent(where('compost')), L('Grease ruins paper recycling.', 'La grasa arruina el reciclaje de papel.')),
          display: { headline: where('compost'), sub: '', item_label: L('Greasy pizza box', 'Caja de pizza grasosa'), icon: 'eye' },
          verdict: verdict(b.id, [binStep('compost', L('Greasy pizza box', 'Caja de pizza grasosa'))], L('Grease ruins paper recycling.', 'La grasa arruina el reciclaje de papel.')) };
      }
    },
    {
      id: 'compost_cup', title: L('Clear cup, no marks visible', 'Vaso transparente sin marcas'), group: G.look,
      frames: { initial: 'cupSide', show_bottom: 'cupBottom' },
      start: function () {
        return { type: 'show',
          trace: [['look', L('Clear plastic cup. Compostable and regular plastic look the same.', 'Vaso de plástico transparente. El compostable y el normal se ven igual.')],
                  ['think', L('The marking on the bottom tells them apart.', 'La marca del fondo los distingue.')],
                  ['show', L('Asked to see the bottom.', 'Pedí ver el fondo.')]],
          say: L('Show me the bottom of the cup.', 'Muéstrame el fondo del vaso.'),
          display: { headline: L('Show me the bottom', 'Muéstrame el fondo'), sub: L('I am looking for a small mark.', 'Busco una marca pequeña.'), item_label: L('Plastic cup', 'Vaso de plástico'), icon: 'bottom' },
          show: { action: 'show_bottom', hint: L('Turn it over', 'Dale la vuelta') } };
      },
      reply: function () {
        var b = binFor('compost');
        return { type: 'verdict',
          trace: [['frame', L('New view: the bottom of the cup.', 'Nueva vista: el fondo del vaso.')],
                  ['specialist', L('Label reader: found "COMPOSTABLE, PLA 7".', 'Lector de etiquetas: dice "COMPOSTABLE, PLA 7".')],
                  ['verdict', L('Marked compostable.', 'Marcado como compostable.')]],
          say: join(L('Compostable cup.', 'Vaso compostable.'), sent(where('compost')), L('It is made from plants.', 'Está hecho de plantas.')),
          display: { headline: where('compost'), sub: '', item_label: L('Compostable cup', 'Vaso compostable'), icon: 'eye' },
          verdict: verdict(b.id, [binStep('compost', L('Compostable cup', 'Vaso compostable'))], L('It is made from plants.', 'Está hecho de plantas.')) };
      }
    },
    {
      id: 'soda_can', title: L('Soda can', 'Lata de refresco'), group: G.ask,
      frames: { initial: 'can' },
      auto: L('Yes, there is a little left.', 'Sí, queda un poco.'),
      start: function () {
        return { type: 'ask',
          trace: [['look', L('Aluminum soda can, upright. I cannot see inside.', 'Lata de aluminio, de pie. No veo adentro.')],
                  ['think', L('No camera can tell if it is empty, so I ask.', 'Ninguna cámara sabe si está vacía; pregunto.')],
                  ['ask', L('Is there liquid inside?', '¿Tiene líquido adentro?')]],
          say: L('Is there liquid inside?', '¿Tiene líquido adentro?'),
          display: { headline: L('Is there liquid inside?', '¿Tiene líquido adentro?'), sub: L('I can’t see through the can.', 'No puedo ver a través de la lata.'), item_label: L('Soda can', 'Lata de refresco'), icon: 'question' },
          ask: { kind: 'yes_no', options: YESNO } };
      },
      reply: function (s, body) {
        var text = body.type === 'answer' ? String(body.text || '') : '';
        var item = L('Soda can', 'Lata de refresco');
        var why = L('Empty cans recycle again and again.', 'Las latas vacías se reciclan una y otra vez.');
        var b = binFor('recycle');
        var answered = body.type === 'answer'
          ? ['answer', L('Person: "' + text + '"', 'Persona: "' + text + '"')]
          : ['answer', L('No answer. The person may have left.', 'Sin respuesta. Quizá la persona se fue.')];
        if (saysNo(text)) {
          return { type: 'verdict', trace: [answered, ['verdict', L('Empty can: recyclable as is.', 'Lata vacía: reciclable.')]],
            say: join(sent(where('recycle')), why),
            display: { headline: where('recycle'), sub: '', item_label: item, icon: 'eye' },
            verdict: verdict(b.id, [binStep('recycle', item)], why) };
        }
        if (saysYes(text)) {
          return { type: 'verdict', trace: [answered, ['verdict', L('Liquid first, then the can is recyclable.', 'Primero el líquido; luego la lata se recicla.')]],
            say: join(L('Pour out the liquid first. Then:', 'Primero vacía el líquido. Luego:'), sent(where('recycle')), why),
            display: { headline: where('recycle'), sub: '', item_label: item, icon: 'eye' },
            verdict: verdict(b.id, [{ kind: 'prep', text: L('Pour out the liquid', 'Vacía el líquido') }, binStep('recycle', item)], why) };
        }
        return { type: 'verdict', trace: [answered, ['verdict', L('Unknown, so give the safe instruction.', 'No se sabe; doy la instrucción segura.')]],
          say: join(L('Pour out any liquid first. Then:', 'Vacía cualquier líquido primero. Luego:'), sent(where('recycle')), L('Liquid spoils the recycling.', 'El líquido arruina el reciclaje.')),
          display: { headline: where('recycle'), sub: '', item_label: item, icon: 'eye' },
          verdict: verdict(b.id, [{ kind: 'prep', text: L('Pour out any liquid', 'Vacía cualquier líquido') }, binStep('recycle', item)],
            L('Liquid spoils the recycling.', 'El líquido arruina el reciclaje.'), { confidence: 'medium' }) };
      }
    },
    {
      id: 'tied_bag', title: L('Tied bag', 'Bolsa amarrada'), group: G.ask,
      frames: { initial: 'tiedBag' },
      auto: L('Food scraps from lunch.', 'Restos de comida del almuerzo.'),
      start: function () {
        return { type: 'ask',
          trace: [['look', L('Tied plastic bag with something inside.', 'Bolsa de plástico amarrada con algo adentro.')],
                  ['think', L('The contents decide. Opening it here is messy, so I ask.', 'El contenido decide. Abrirla aquí ensucia; pregunto.')],
                  ['ask', L('What is inside the bag?', '¿Qué hay en la bolsa?')]],
          say: L('What is inside the bag?', '¿Qué hay en la bolsa?'),
          display: { headline: L('What is inside the bag?', '¿Qué hay en la bolsa?'), sub: L('I can’t see through it.', 'No puedo ver a través de ella.'), item_label: L('Tied bag', 'Bolsa amarrada'), icon: 'question' },
          ask: { kind: 'choice', options: [
            { id: 'food', label: L('Food scraps', 'Restos de comida') },
            { id: 'mixed', label: L('Mixed trash', 'Basura mezclada') },
            { id: 'unsure', label: L('Not sure', 'No sé') }] } };
      },
      reply: function (s, body) {
        var text = body.type === 'answer' ? String(body.text || '') : '';
        var answered = ['answer', body.type === 'answer' ? L('Person: "' + text + '"', 'Persona: "' + text + '"') : L('No answer.', 'Sin respuesta.')];
        if (/food|comida|restos|scraps/i.test(text)) {
          var steps = [binStep('compost', L('Food scraps', 'Restos de comida')), binStep('landfill', L('Plastic bag', 'Bolsa de plástico'))];
          return { type: 'verdict', trace: [answered, ['verdict', L('Food can be composted, the bag cannot.', 'La comida se composta; la bolsa no.')]],
            say: twoBins ? join(sent(where('landfill')), L('This station has no compost bin.', 'Esta estación no tiene composta.'))
                         : L('Empty the food into the green bin, in the middle. The bag goes in the black bin, on your right.', 'Vacía la comida en el contenedor verde, en el centro. La bolsa va en el negro, a tu derecha.'),
            display: { headline: L('Food and bag go apart', 'Comida y bolsa van aparte'), sub: '', item_label: L('Bag of food scraps', 'Bolsa con restos de comida'), icon: 'eye' },
            verdict: verdict(binFor('compost').id, steps, L('Food can be composted, the bag cannot.', 'La comida se composta; la bolsa no.')) };
        }
        return { type: 'verdict', trace: [answered, ['verdict', L('Mixed or unknown contents: landfill is the safe choice.', 'Contenido mezclado o desconocido: basura es lo seguro.')]],
          say: join(sent(where('landfill')), L('Mixed trash goes to landfill.', 'La basura mezclada va al relleno.')),
          display: { headline: where('landfill'), sub: '', item_label: L('Bag of mixed trash', 'Bolsa de basura mezclada'), icon: 'eye' },
          verdict: verdict('landfill', [binStep('landfill', L('Bag of mixed trash', 'Bolsa de basura mezclada'))],
            L('Mixed trash goes to landfill.', 'La basura mezclada va al relleno.'), { confidence: (saysUnsure(text) || !text) ? 'low' : 'high' }) };
      }
    },
    {
      id: 'clear_bottle', title: L('Clear bottle, empty', 'Botella transparente vacía'), group: G.see,
      frames: { initial: 'bottle' },
      start: function () {
        var item = L('Empty water bottle', 'Botella de agua vacía'), why = L('Empty bottles get a new life.', 'Las botellas vacías tienen nueva vida.');
        return { type: 'verdict',
          trace: [['look', L('Clear plastic bottle. I can see that it is empty.', 'Botella transparente. Veo que está vacía.')],
                  ['think', L('No question needed: the camera can see inside.', 'Sin preguntas: la cámara ve el interior.')],
                  ['verdict', L('Empty plastic bottle: recycle.', 'Botella vacía: reciclar.')]],
          say: join(sent(where('recycle')), why),
          display: { headline: where('recycle'), sub: '', item_label: item, icon: 'eye' },
          verdict: verdict('recycle', [binStep('recycle', item)], why) };
      }
    },
    {
      id: 'banana_peel', title: L('Banana peel', 'Cáscara de plátano'), group: G.see,
      frames: { initial: 'banana' },
      start: function () {
        var item = L('Banana peel', 'Cáscara de plátano'), why = L('Food scraps turn into soil.', 'Los restos de comida se vuelven tierra.');
        return { type: 'verdict',
          trace: [['look', L('Banana peel. Nothing hidden.', 'Cáscara de plátano. Nada oculto.')], ['verdict', L('Food scraps: compost.', 'Restos de comida: composta.')]],
          say: join(sent(where('compost')), why),
          display: { headline: where('compost'), sub: '', item_label: item, icon: 'eye' },
          verdict: verdict(binFor('compost').id, [binStep('compost', item)], why) };
      }
    },
    {
      id: 'chip_bag', title: L('Chip bag', 'Bolsa de papas'), group: G.see,
      frames: { initial: 'chipBag' },
      start: function () {
        var item = L('Chip bag', 'Bolsa de papas'), why = L('Chip bags can’t be recycled.', 'Las bolsas de papas no se reciclan.');
        return { type: 'verdict',
          trace: [['look', L('Empty chip bag: shiny plastic film, not foil.', 'Bolsa de papas vacía: plástico brillante, no aluminio.')], ['verdict', L('Film wrappers: landfill.', 'Envolturas: basura.')]],
          say: join(sent(where('landfill')), why),
          display: { headline: where('landfill'), sub: '', item_label: item, icon: 'eye' },
          verdict: verdict('landfill', [binStep('landfill', item)], why) };
      }
    },
    {
      id: 'two_items', title: L('Two items at once', 'Dos objetos a la vez'), group: G.see,
      frames: { initial: 'two' },
      start: function () {
        return { type: 'verdict',
          trace: [['look', L('Two items: a banana peel and an empty clear bottle.', 'Dos objetos: cáscara de plátano y botella vacía.')], ['verdict', L('One bin for each.', 'Un contenedor para cada uno.')]],
          say: twoBins ? L('Bottle: blue bin, on your left. Peel: black bin, on your right.', 'Botella: contenedor azul, a tu izquierda. Cáscara: contenedor negro, a tu derecha.')
                       : L('Two items. Bottle: blue bin, on your left. Peel: green bin, in the middle.', 'Dos objetos. Botella: contenedor azul, a tu izquierda. Cáscara: contenedor verde, en el centro.'),
          display: { headline: L('Two items, two bins', 'Dos objetos, dos contenedores'), sub: '', item_label: L('Banana peel and bottle', 'Cáscara y botella'), icon: 'eye' },
          verdict: verdict('recycle', [binStep('compost', L('Banana peel', 'Cáscara')), binStep('recycle', L('Bottle', 'Botella'))], L('Each one has its own bin.', 'Cada uno tiene su contenedor.')) };
      }
    },
    {
      id: 'battery', title: L('Batteries', 'Pilas'), group: G.special,
      frames: { initial: 'battery' },
      start: function () {
        return { type: 'verdict',
          trace: [['look', L('Two AA batteries.', 'Dos pilas AA.')], ['think', L('Fire risk. They never go in these bins.', 'Riesgo de incendio. Nunca van en estos contenedores.')], ['verdict', L('Send to the battery drop-off.', 'Enviar al punto de pilas.')]],
          say: L('Not in these bins. Batteries can start fires. Please take them to the battery drop-off.', 'No va en estos contenedores. Las pilas pueden causar incendios. Llévalas al punto de pilas.'),
          display: { headline: L('Not in these bins', 'No va en estos contenedores'), sub: '', item_label: L('Batteries', 'Pilas'), icon: 'warning' },
          verdict: verdict('special', [{ kind: 'special', item: L('Batteries', 'Pilas'), text: L('Not in these bins', 'No va en estos contenedores'), dest: L('Battery drop-off', 'Punto de pilas') }],
            L('Batteries can start fires in the truck.', 'Las pilas pueden causar incendios en el camión.'), { special_dest: L('Battery drop-off', 'Punto de pilas') }) };
      }
    },
    {
      id: 'phone', title: L('A phone (not trash)', 'Un teléfono (no es basura)'), group: G.special,
      frames: { initial: 'phone' },
      start: function () {
        return { type: 'verdict',
          trace: [['look', L('A smartphone that looks fine.', 'Un teléfono que se ve bien.')], ['verdict', L('Not trash.', 'No es basura.')]],
          say: L('That looks like a phone, not trash. Keep it.', 'Eso parece un teléfono, no basura. Consérvalo.'),
          display: { headline: L('That is not trash', 'Eso no es basura'), sub: '', item_label: L('Phone', 'Teléfono'), icon: 'eye' },
          verdict: verdict('not_trash', [{ kind: 'keep', text: L('That is not trash', 'Eso no es basura') }], L('If it is broken, take it to e-waste.', 'Si está roto, llévalo a residuos electrónicos.')) };
      }
    },
    {
      id: 'blurry', title: L('Blurry, dark view', 'Imagen borrosa y oscura'), group: G.edge,
      frames: { initial: 'blurry', hold_still: 'chipBag' },
      start: function () {
        return { type: 'show',
          trace: [['look', L('Too dark and blurry to tell.', 'Muy oscuro y borroso para saber.')], ['show', L('Asked to hold it still.', 'Pedí sostenerlo quieto.')]],
          say: L('Hold it still for a moment.', 'Sosténlo quieto un momento.'),
          display: { headline: L('Hold it still', 'Sosténlo quieto'), sub: L('It looks blurry to me.', 'Lo veo borroso.'), item_label: '', icon: 'still' },
          show: { action: 'hold_still', hint: L('Hold it still', 'Sosténlo quieto') } };
      },
      reply: function () {
        var item = L('Chip bag', 'Bolsa de papas'), why = L('Chip bags can’t be recycled.', 'Las bolsas de papas no se reciclan.');
        return { type: 'verdict',
          trace: [['frame', L('New view: sharp now.', 'Nueva vista: ya nítida.')], ['verdict', L('Film wrapper: landfill.', 'Envoltura: basura.')]],
          say: join(sent(where('landfill')), why),
          display: { headline: where('landfill'), sub: '', item_label: item, icon: 'eye' },
          verdict: verdict('landfill', [binStep('landfill', item)], why) };
      }
    },
    {
      id: 'nothing', title: L('Nothing shown', 'No se muestra nada'), group: G.edge,
      frames: { initial: 'empty' },
      start: function () {
        return { type: 'no_item',
          trace: [['look', L('No item in view.', 'No hay objeto a la vista.')]],
          say: L('I don’t see an item. Hold it up to the camera.', 'No veo un objeto. Levántalo hacia la cámara.'),
          display: { headline: L('Hold your item up', 'Levanta tu objeto'), sub: L('A little closer to the camera.', 'Un poco más cerca de la cámara.'), item_label: '', icon: 'eye' } };
      }
    },
    {
      id: 'hiccup', title: L('Brain hiccup (error)', 'Fallo del cerebro (error)'), group: G.edge,
      frames: { initial: 'hiccup' },
      start: function () {
        return { type: 'error', trace: [['look', L('The brain could not answer.', 'El cerebro no pudo responder.')]],
          say: L('I can’t see well right now. Please check the labels on the bins.', 'Ahora no veo bien. Revisa las etiquetas de los contenedores.'),
          display: { headline: L('I can’t see well right now.', 'Ahora no veo bien.'), sub: L('Please check the labels on the bins.', 'Revisa las etiquetas de los contenedores.'), item_label: '', icon: 'warning' } };
      }
    }
  ];

  var byId = {};
  SCENARIOS.forEach(function (s) { byId[s.id] = s; });
  var CAMERA_CYCLE = ['soda_can', 'pizza_box', 'clear_bottle', 'chip_bag', 'banana_peel', 'battery'];
  var cycleAt = 0;

  /* ---------- sessions ---------- */
  var sessions = {}, counter = 0, lastLang = 'en';
  var pics = {};
  function pic(name) { if (!pics[name]) pics[name] = picture(function (x) { draw[name](x); }); return pics[name]; }

  function latency() { return Math.round((slow ? 4200 : 650) + Math.random() * 600); }
  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  function build(s, r) {
    var ms = latency();
    var base = Date.now() - s.t0;
    (r.trace || []).forEach(function (e, i, arr) {
      s.trace.push({ t_ms: Math.round(base + ms * (i + 1) / (arr.length + 1)), kind: e[0], text: loc(e[1], s.lang) });
    });
    s.turn++;
    var t = { session_id: s.id, turn: s.turn, type: r.type, say: r.say, display: r.display };
    if (r.ask) t.ask = r.ask;
    if (r.show) t.show = r.show;
    if (r.verdict) t.verdict = r.verdict;
    t = loc(t, s.lang);
    t.trace = s.trace.slice();          // the mock sends the whole session trace every turn
    t.timing_ms = ms;
    if (r.type === 'verdict' || r.type === 'no_item' || r.type === 'error') s.done = true;
    return wait(ms).then(function () { return t; });
  }

  function startSession(body) {
    var sc = (body && body.demo_scenario && byId[body.demo_scenario]) || byId[CAMERA_CYCLE[cycleAt++ % CAMERA_CYCLE.length]];
    var lang = (body && body.lang === 'es') ? 'es' : 'en';
    lastLang = lang;
    var id = 's_m' + (++counter).toString(36) + Math.random().toString(36).slice(2, 5);
    var s = sessions[id] = { id: id, sc: sc, lang: lang, turn: 0, t0: Date.now(), trace: [], done: false };
    return build(s, sc.start(s));
  }

  function reply(sid, body) {
    var s = sessions[sid];
    if (!s || s.done) return wait(120).then(function () { throw new Error('mock: unknown or finished session'); });
    if (!s.sc.reply) return build(s, { type: 'error', say: 'Unexpected reply.', display: { headline: 'Unexpected reply', sub: '', item_label: '', icon: 'warning' } });
    return build(s, s.sc.reply(s, body || {}));
  }

  function end(sid) { if (sessions[sid]) sessions[sid].done = true; return Promise.resolve({}); }

  function scenarios() {
    var lang = i18n.lang;
    return Promise.resolve(SCENARIOS.map(function (s) {
      var frames = {};
      Object.keys(s.frames).forEach(function (k) { frames[k] = pic(s.frames[k]); });
      return { id: s.id, title: loc(s.title, lang), group: loc(s.group, lang), frames: frames };
    }));
  }

  function demoAnswer(body) {
    var sc = byId[body && body.scenario_id];
    var text = sc && sc.auto ? loc(sc.auto, lastLang) : loc(L('Not sure.', 'No sé.'), lastLang);
    return wait(450).then(function () { return { text: text }; });
  }

  window.Sorty = window.Sorty || {};
  window.Sorty.mock = {
    config: function () { return JSON.parse(JSON.stringify(CONFIG)); },
    startSession: startSession,
    reply: reply,
    end: end,
    scenarios: scenarios,
    demoAnswer: demoAnswer
  };
})();
