'use strict';

// Cap répond à voix haute, avec la voix du téléphone, sauf si « Réponse silencieuse » est allumée.
const voix = (() => {
  function disponible() {
    return typeof speechSynthesis !== 'undefined' && typeof SpeechSynthesisUtterance === 'function';
  }

  let enTrain = false;

  function dire(texte) {
    const phrase = String(texte || '').trim();
    if (!phrase || preferencesClavier.silencieux() || !disponible()) return false;
    try {
      speechSynthesis.cancel();
      const enonce = new SpeechSynthesisUtterance(phrase);
      enonce.lang = 'fr-FR';
      enTrain = true;
      enonce.onend = () => { enTrain = false; };
      enonce.onerror = () => { enTrain = false; };
      speechSynthesis.speak(enonce);
      return true;
    } catch (erreur) {
      enTrain = false;
      return false;
    }
  }

  // Cap est-il en train de parler ? (le mode conversation attend la fin pour ne pas s'écouter lui-même)
  function parle() {
    if (!disponible()) return false;
    return enTrain && (speechSynthesis.speaking !== false || speechSynthesis.pending === true);
  }

  return { disponible, dire, parle };
})();
