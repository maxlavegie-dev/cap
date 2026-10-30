'use strict';

// Cap répond à voix haute, avec la voix du téléphone, sauf si « Réponse silencieuse » est allumée.
const voix = (() => {
  function disponible() {
    return typeof speechSynthesis !== 'undefined' && typeof SpeechSynthesisUtterance === 'function';
  }

  function dire(texte) {
    const phrase = String(texte || '').trim();
    if (!phrase || preferencesClavier.silencieux() || !disponible()) return false;
    try {
      speechSynthesis.cancel();
      const enonce = new SpeechSynthesisUtterance(phrase);
      enonce.lang = 'fr-FR';
      speechSynthesis.speak(enonce);
      return true;
    } catch (erreur) {
      return false;
    }
  }

  return { disponible, dire };
})();
