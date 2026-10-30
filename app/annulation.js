'use strict';

// Un seul « Annuler » pour toute l'appli : retient la dernière action annulable pendant 8 secondes.
// Le bouton Annuler affiché et la phrase « Annule » (voix ou clavier) passent tous les deux par ici.
const annulation = (() => {
  const DUREE_MS = 8000;
  const DELAI_ECOUTE_MS = 15000;
  let derniere = null;

  function valide(entree) {
    return Boolean(entree) && !entree.terminee && Date.now() <= entree.jusqua;
  }

  // annuler : défait l'action ; messageApres : ce que Cap dit ensuite ; retirer : enlève le bouton affiché.
  function proposer({ annuler, messageApres = '', retirer } = {}) {
    if (typeof annuler !== 'function') throw new Error('Rien à annuler.');
    if (derniere && derniere.retirer !== retirer) derniere.retirer?.();
    derniere = { annuler, messageApres, retirer, terminee: false, jusqua: Date.now() + DUREE_MS };
    return derniere;
  }

  function executer(entree) {
    if (!entree || entree.terminee) return false;
    entree.annuler();
    entree.terminee = true;
    if (derniere === entree) derniere = null;
    entree.retirer?.();
    return true;
  }

  function expirer(entree) {
    if (derniere === entree) derniere = null;
  }

  // Le micro ou le clavier s'ouvre : on laisse le temps de dire « Annule ».
  function garderPendantEcoute() {
    if (valide(derniere)) derniere.jusqua = Math.max(derniere.jusqua, Date.now() + DELAI_ECOUTE_MS);
  }

  function disponible() {
    return valide(derniere);
  }

  // Renvoie le message à dire, ou '' s'il n'y a plus rien à annuler.
  function annulerDerniere() {
    if (!valide(derniere)) {
      derniere = null;
      return '';
    }
    const entree = derniere;
    executer(entree);
    return entree.messageApres || 'C’est annulé.';
  }

  function normaliser(texte) {
    return String(texte || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr')
      .replace(/[^a-z' ]+/g, ' ').replace(/\s+/g, ' ').trim();
  }

  const PHRASES = /^(?:(?:cap|non|oups|zut) )?(?:annule|annuler|annulez|annules|annule moi) ?(?:ca|cela|ce que tu viens de faire|la derniere action|ma derniere action|stp|s'il te plait)?$/;

  function estDemande(texte) {
    return PHRASES.test(normaliser(texte));
  }

  return { DUREE_MS, proposer, executer, expirer, garderPendantEcoute, disponible, annulerDerniere, estDemande };
})();
