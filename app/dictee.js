'use strict';

// Dictée : enveloppe la reconnaissance vocale du navigateur (une seule écoute à la fois).
// Aucune logique de tâches ici : on transmet seulement le texte entendu.
const dictee = (() => {
  let session = null;

  function disponible() {
    return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  function sansAction() {}

  function rappelsDe(options) {
    return {
      surProvisoire: options.surProvisoire || sansAction,
      surFinal: options.surFinal || sansAction,
      surErreur: options.surErreur || sansAction,
      surFin: options.surFin || sansAction
    };
  }

  function echouer(courante, code) {
    session = null;
    courante.rappels.surErreur(code);
    courante.rappels.surFin();
  }

  // Lance une écoute en français et appelle les rappels (texte provisoire, final, erreur, fin)
  function demarrer(options = {}) {
    const rappels = rappelsDe(options);
    if (session) {
      rappels.surErreur('occupee');
      return;
    }
    const Constructeur = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Constructeur) {
      rappels.surErreur('indisponible');
      rappels.surFin();
      return;
    }
    const courante = { instance: null, rappels };
    session = courante;
    try {
      courante.instance = new Constructeur();
    } catch (erreur) {
      echouer(courante, 'constructeur');
      return;
    }
    const instance = courante.instance;
    instance.lang = 'fr-FR';
    instance.interimResults = true;
    instance.continuous = false;
    instance.maxAlternatives = 1;
    instance.onresult = evenement => {
      if (session !== courante) return;
      for (let i = evenement.resultIndex; i < evenement.results.length; i++) {
        const segment = evenement.results[i];
        const texte = segment[0].transcript;
        if (segment.isFinal) {
          rappels.surFinal(texte);
        } else {
          rappels.surProvisoire(texte);
        }
      }
    };
    instance.onerror = evenement => {
      if (session !== courante) return;
      rappels.surErreur(evenement && evenement.error ? evenement.error : 'inconnue');
    };
    instance.onend = () => {
      if (session !== courante) return;
      session = null;
      rappels.surFin();
    };
    try {
      instance.start();
    } catch (erreur) {
      echouer(courante, 'demarrage');
    }
  }

  function arreter() {
    const courante = session;
    if (!courante || courante.arretDemande) return;
    courante.arretDemande = true;
    try {
      courante.instance.stop();
    } catch (erreur) {
      courante.arretDemande = false;
      courante.rappels.surErreur('arret');
    }
  }

  return {
    disponible,
    demarrer,
    arreter,
    enCours: () => session !== null
  };
})();
