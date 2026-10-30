'use strict';

// Vibration très courte quand une action de Max est prise en compte.
const vibration = (() => {
  const DUREE_MS = 30;
  const ECART_MINIMUM_MS = 150;
  let derniere = 0;

  function courte() {
    if (typeof navigator === 'undefined' || typeof navigator.vibrate !== 'function') return false;
    const maintenant = Date.now();
    if (maintenant - derniere < ECART_MINIMUM_MS) return false;
    derniere = maintenant;
    try {
      return navigator.vibrate(DUREE_MS);
    } catch {
      return false;
    }
  }

  return { courte };
})();
