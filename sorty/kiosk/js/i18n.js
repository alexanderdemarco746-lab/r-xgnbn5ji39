/* Sorty kiosk - fixed UI strings (English / Spanish).
   Text that comes from the brain (say, display, verdict steps) already arrives
   in the session language; only the kiosk's own words live here. */
(function () {
  'use strict';
  var STR = {
    en: {
      brand_tag: 'Which bin?',
      idle_headline: 'Show me your item',
      idle_sub: 'I’ll tell you which bin.',
      idle_sub_demo: 'Camera is off. Pick a demo item.',
      boot: 'Waking up…',
      show_here: 'Show it here',
      cam_on: 'Camera on',
      cam_off: 'Camera is off',
      demo_badge: 'DEMO',
      scan: 'Scan',
      demo_items: 'Demo items',
      privacy: 'Photos are not saved.',
      looking: 'Looking…',
      okay: 'Okay…',
      one_moment: 'One moment…',
      still_thinking: 'Still thinking…',
      i_see: 'I see',
      listening: 'Listening. You can just say it.',
      tap_answer: 'Tap your answer',
      you_said: 'You said',
      done: 'Done',
      hold_still_hint: 'I look when you hold it still.',
      person_doing: 'The person does it…',
      thanks: 'Thank you!',
      thanks_sub: 'Every right bin counts.',
      sorted_today: 'Sorted right today',
      error_headline: 'I can’t see well right now.',
      error_sub: 'Please check the labels on the bins.',
      best_guess: 'Best guess',
      take_it_to: 'Take it to',
      not_in_bins: 'Not in these bins',
      no_item_default: 'Hold your item up',
      yes: 'Yes', no: 'No', unsure: 'Not sure',
      demo: 'Demo items',
      demo_title: 'Demo items',
      demo_sub: 'Pick an item to show Sorty.',
      autoplay: 'Auto-play answers',
      autoplay_sub: 'A simulated person answers the questions.',
      play_all: 'Play all',
      stop: 'Stop',
      trace: 'How Sorty decided',
      trace_title: 'How Sorty decided',
      trace_empty: 'Show an item. The steps appear here.',
      sound_hint: 'Tap anywhere to turn sound on',
      sound_on: 'Sound on', sound_off: 'Sound off',
      fullscreen: 'Full screen',
      language: 'Language',
      person: 'Person',
      mode_live: 'LIVE AI', mode_mock: 'PRACTICE',
      close: 'Close',
      turn: 'Turn', ai_time: 'AI time', round_trip: 'round trip',
      session: 'Session', brain: 'Brain', camera: 'Camera',
      motion: 'motion', presence: 'presence', still: 'still',
      shortcuts: 'Space scan · M demo · D steps · L language · S sound · F full screen · Esc cancel',
      k_look: 'Look', k_think: 'Think', k_ask: 'Ask', k_answer: 'Answer', k_show: 'Request',
      k_frame: 'New view', k_specialist: 'Specialist', k_verdict: 'Verdict'
    },
    es: {
      brand_tag: '¿En qué contenedor?',
      idle_headline: 'Muéstrame tu objeto',
      idle_sub: 'Te digo en qué contenedor va.',
      idle_sub_demo: 'La cámara está apagada. Elige un objeto de demostración.',
      boot: 'Despertando…',
      show_here: 'Muéstralo aquí',
      cam_on: 'Cámara encendida',
      cam_off: 'La cámara está apagada',
      demo_badge: 'DEMO',
      scan: 'Escanear',
      demo_items: 'Objetos demo',
      privacy: 'No se guardan fotos.',
      looking: 'Mirando…',
      okay: 'De acuerdo…',
      one_moment: 'Un momento…',
      still_thinking: 'Sigo pensando…',
      i_see: 'Veo',
      listening: 'Te escucho. Puedes decirlo.',
      tap_answer: 'Toca tu respuesta',
      you_said: 'Dijiste',
      done: 'Listo',
      hold_still_hint: 'Miro cuando lo sostienes quieto.',
      person_doing: 'La persona lo hace…',
      thanks: '¡Gracias!',
      thanks_sub: 'Cada contenedor correcto cuenta.',
      sorted_today: 'Bien clasificados hoy',
      error_headline: 'Ahora no veo bien.',
      error_sub: 'Revisa las etiquetas de los contenedores.',
      best_guess: 'Mi mejor respuesta',
      take_it_to: 'Llévalo a',
      not_in_bins: 'No va en estos contenedores',
      no_item_default: 'Levanta tu objeto',
      yes: 'Sí', no: 'No', unsure: 'No sé',
      demo: 'Objetos demo',
      demo_title: 'Objetos de demostración',
      demo_sub: 'Elige un objeto para mostrárselo a Sorty.',
      autoplay: 'Respuestas automáticas',
      autoplay_sub: 'Una persona simulada responde las preguntas.',
      play_all: 'Reproducir todo',
      stop: 'Detener',
      trace: 'Cómo decidió Sorty',
      trace_title: 'Cómo decidió Sorty',
      trace_empty: 'Muestra un objeto. Los pasos aparecen aquí.',
      sound_hint: 'Toca la pantalla para activar el sonido',
      sound_on: 'Sonido activado', sound_off: 'Sonido apagado',
      fullscreen: 'Pantalla completa',
      language: 'Idioma',
      person: 'Persona',
      mode_live: 'IA EN VIVO', mode_mock: 'PRÁCTICA',
      close: 'Cerrar',
      turn: 'Turno', ai_time: 'Tiempo de IA', round_trip: 'ida y vuelta',
      session: 'Sesión', brain: 'Cerebro', camera: 'Cámara',
      motion: 'movimiento', presence: 'presencia', still: 'quieto',
      shortcuts: 'Espacio escanear · M demo · D pasos · L idioma · S sonido · F pantalla completa · Esc cancelar',
      k_look: 'Mirar', k_think: 'Pensar', k_ask: 'Preguntar', k_answer: 'Respuesta', k_show: 'Pedir',
      k_frame: 'Nueva vista', k_specialist: 'Especialista', k_verdict: 'Veredicto'
    }
  };

  var SPEECH = { en: 'en-US', es: 'es-US' };

  window.Sorty = window.Sorty || {};
  window.Sorty.i18n = {
    lang: 'en',
    t: function (key, lang) {
      var l = STR[lang || this.lang] || STR.en;
      if (Object.prototype.hasOwnProperty.call(l, key)) return l[key];
      if (Object.prototype.hasOwnProperty.call(STR.en, key)) return STR.en[key];
      return key;
    },
    setLang: function (l) {
      this.lang = STR[l] ? l : 'en';
      document.documentElement.lang = this.lang;
      return this.lang;
    },
    has: function (l) { return !!STR[l]; },
    speechLang: function (l) { return SPEECH[l || this.lang] || 'en-US'; },
    /* Pick a localized value out of {"en": "...", "es": "..."} or pass strings through. */
    pick: function (v, lang) {
      if (v == null) return '';
      if (typeof v === 'string') return v;
      return v[lang || this.lang] || v.en || v[Object.keys(v)[0]] || '';
    }
  };
})();
