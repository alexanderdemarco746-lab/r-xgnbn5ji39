/* Sorty kiosk - inline SVG icons and animated pictograms (no external assets).
   Line icons use a 24x24 grid in the style of the Lucide set (ISC licence);
   pictograms are original drawings for this project. */
(function () {
  'use strict';

  function line(body, extra) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
      'stroke-linejoin="round" aria-hidden="true" focusable="false"' + (extra || '') + '>' + body + '</svg>';
  }

  var icons = {
    /* bins */
    recycle: line(
      '<path d="M7 19H4.815a1.83 1.83 0 0 1-1.57-.881 1.785 1.785 0 0 1-.004-1.784L7.196 9.5"/>' +
      '<path d="M11 19h8.203a1.83 1.83 0 0 0 1.556-.89 1.784 1.784 0 0 0 0-1.775l-1.226-2.12"/>' +
      '<path d="m14 16-3 3 3 3"/>' +
      '<path d="M8.293 13.596 7.196 9.5 3.1 10.598"/>' +
      '<path d="m9.344 5.811 1.093-1.892A1.83 1.83 0 0 1 11.985 3a1.784 1.784 0 0 1 1.546.888l3.943 6.843"/>' +
      '<path d="m13.378 9.633 4.096 1.098 1.097-4.096"/>'),
    compost: line(
      '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>' +
      '<path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>'),
    landfill: line(
      '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>' +
      '<path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6"/><path d="M14 11v6"/>'),

    /* states */
    question: line('<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>'),
    warning: line('<path d="m21.7 18-8-14a2 2 0 0 0-3.4 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>'),
    eye: line('<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>'),
    eyeoff: line('<path d="M3 3l18 18"/><path d="M10.6 5.1A9.8 9.8 0 0 1 12 5c6.4 0 10 7 10 7a17 17 0 0 1-3 3.9"/>' +
      '<path d="M6.5 6.6C3.7 8.5 2 12 2 12s3.6 7 10 7c1.7 0 3.2-.5 4.5-1.2"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/>'),
    check: line('<path d="M20 6 9 17l-5-5"/>'),
    x: line('<path d="M18 6 6 18"/><path d="m6 6 12 12"/>'),
    pin: line('<path d="M12 22s7-6.3 7-12a7 7 0 1 0-14 0c0 5.7 7 12 7 12Z"/><circle cx="12" cy="10" r="2.6"/>'),
    heart: line('<path d="M12 20.5s-7.5-4.6-9.3-9.6C1.4 7.3 3.7 4 7 4c2 0 3.6 1 5 3 1.4-2 3-3 5-3 3.3 0 5.6 3.3 4.3 6.9-1.8 5-9.3 9.6-9.3 9.6Z"/>'),
    drop: line('<path d="M12 3s6 6.6 6 11.2a6 6 0 0 1-12 0C6 9.6 12 3 12 3Z"/>'),

    /* controls */
    mic: line('<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><path d="M12 19v3"/>'),
    sound: line('<path d="M4 9h3l5-4v14l-5-4H4z"/><path d="M16 9a4 4 0 0 1 0 6"/><path d="M18.8 6.4a8 8 0 0 1 0 11.2"/>'),
    mute: line('<path d="M4 9h3l5-4v14l-5-4H4z"/><path d="m16.5 9.5 5 5"/><path d="m21.5 9.5-5 5"/>'),
    camera: line('<path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z"/><circle cx="12" cy="13" r="3.5"/>'),
    list: line('<path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/>'),
    grid: line('<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/>' +
      '<rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>'),
    full: line('<path d="M4 9V4h5"/><path d="M20 9V4h-5"/><path d="M4 15v5h5"/><path d="M20 15v5h-5"/>'),
    play: line('<path d="M7 4v16l13-8z"/>'),
    stop: line('<rect x="6" y="6" width="12" height="12" rx="2"/>'),
    person: line('<circle cx="12" cy="7.5" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>'),

    /* the big direction arrow (points DOWN; rotated by the app) */
    arrow: '<svg viewBox="0 0 100 100" aria-hidden="true" focusable="false">' +
      '<path d="M39 8h22a4 4 0 0 1 4 4v40h15.5a3 3 0 0 1 2.3 5L52.6 92.6a3.4 3.4 0 0 1-5.2 0L17.2 57a3 3 0 0 1 2.3-5H35V12a4 4 0 0 1 4-4Z" ' +
      'fill="currentColor" stroke="rgba(0,0,0,.28)" stroke-width="2.5" stroke-linejoin="round"/></svg>'
  };

  /* Animated pictograms for "show me again" requests. Classes are animated in styles.css. */
  function pg(body) {
    return '<svg viewBox="24 0 192 190" class="pg" aria-hidden="true" focusable="false"><g class="pg-ink">' + body + '</g></svg>';
  }

  var pictograms = {
    open_show_inside: pg(
      '<path class="pg-fill" d="M52 114h136v58a10 10 0 0 1-10 10H62a10 10 0 0 1-10-10z"/>' +
      '<g class="pg-lid"><rect class="pg-fill2" x="46" y="96" width="148" height="18" rx="7"/></g>' +
      '<g class="pg-peek"><path class="pg-acc" d="M90 70s11-18 30-18 30 18 30 18-11 18-30 18-30-18-30-18z"/>' +
      '<circle class="pg-dot" cx="120" cy="70" r="8"/></g>'),
    flip_over: pg(
      '<g class="pg-flip"><rect class="pg-fill" x="72" y="58" width="96" height="118" rx="14"/>' +
      '<path class="pg-front" d="M94 96h52M94 116h52M94 136h32"/>' +
      '<circle class="pg-back pg-acc" cx="120" cy="117" r="22"/></g>' +
      '<path class="pg-acc" d="M58 44c18-24 106-24 124 0"/><path class="pg-acc" d="M182 44l-3-17M182 44l-17 1"/>'),
    show_bottom: pg(
      '<g class="pg-tilt"><path class="pg-fill" d="M84 52h72l-9 106a9 9 0 0 1-9 8h-36a9 9 0 0 1-9-8z"/>' +
      '<ellipse class="pg-fill2 pg-bottom" cx="120" cy="162" rx="28" ry="7"/></g>' +
      '<path class="pg-acc" d="M44 150c-10-34 2-74 34-96"/><path class="pg-acc" d="M78 54l-18-1M78 54l-4 17"/>'),
    show_label: pg(
      '<path class="pg-fill" d="M104 26h32v20c0 9 16 15 16 32v88a9 9 0 0 1-9 9H97a9 9 0 0 1-9-9V78c0-17 16-23 16-32z"/>' +
      '<rect class="pg-fill2" x="97" y="96" width="46" height="44" rx="5"/><path d="M106 110h28M106 124h18"/>' +
      '<g class="pg-mag"><circle class="pg-acc pg-glass" cx="150" cy="116" r="28"/><path class="pg-acc" d="M170 137l24 24"/></g>'),
    hold_closer: pg(
      '<path class="pg-acc" d="M38 64V34h30M202 64V34h-30M38 136v30h30M202 136v30h-30"/>' +
      '<g class="pg-zoom"><rect class="pg-fill" x="90" y="70" width="60" height="60" rx="12"/>' +
      '<path d="M106 92h28M106 108h18"/></g>'),
    one_at_a_time: pg(
      '<g class="pg-away"><rect class="pg-fill2" x="140" y="70" width="64" height="64" rx="12"/></g>' +
      '<g><circle class="pg-fill" cx="92" cy="102" r="36"/>' +
      '<path class="pg-acc" d="M84 92l10-8v36"/></g>'),
    hold_still: pg(
      '<g class="pg-wob"><rect class="pg-fill" x="88" y="58" width="64" height="88" rx="13"/>' +
      '<path d="M104 86h32M104 104h20"/></g>' +
      '<path class="pg-acc pg-lines" d="M66 78c-9 15-9 33 0 48M174 78c9 15 9 33 0 48"/>' +
      '<path class="pg-acc pg-ok" d="M100 168l14 13 28-28"/>')
  };

  /* display.icon hint -> pictogram key */
  var hintToPictogram = {
    open: 'open_show_inside', flip: 'flip_over', bottom: 'show_bottom', label: 'show_label',
    closer: 'hold_closer', separate: 'one_at_a_time', still: 'hold_still'
  };

  window.Sorty = window.Sorty || {};
  window.Sorty.icons = icons;
  window.Sorty.pictograms = pictograms;
  window.Sorty.hintToPictogram = hintToPictogram;
})();
