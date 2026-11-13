'use strict';

// 11/11/2026 (accord de Max, c138) : bouton « Matières » des Réglages (livraison de Haiku, validée par Max).
// Il ouvre, en plein écran, la page de choix des matières (eau, slime, sable, feuille blanche : copies des pages
// d'essai, dans app/matieres/). Cette page n'a pas de bouton retour : Cap ajoute une barre avec « Fermer » au-dessus
// d'elle. « Fermer », le geste retour ou la touche Échap (« cancel ») ferment la fenêtre : on retrouve les Réglages,
// et la page est VIDÉE (l'eau, la vidéo et les dessins s'arrêtent, rien n'est gardé). Aucun appel réseau, rien
// d'enregistré : le choix d'une matière ne change pas encore l'allure de Cap.
const matieresEcran = (() => {
  const PAGE = 'matieres/choix_matieres.html';
  const VIDE = 'about:blank';

  function brancher(doc) {
    const el = id => doc.getElementById(id);
    const bouton = el('ouvrir-matieres');
    const fenetre = el('matieres-cap');
    const cadre = el('cadre-matieres');
    const fermer = el('fermer-matieres');
    if (!bouton || !fenetre || !cadre || !fermer) return null;
    const vider = () => { if (cadre.getAttribute('src') !== VIDE) cadre.setAttribute('src', VIDE); };
    function ouvrir() {
      cadre.setAttribute('src', PAGE);
      if (!fenetre.open) fenetre.showModal();
    }
    function fermerFenetre() {
      if (fenetre.open) fenetre.close();
      vider();
    }
    bouton.addEventListener('click', ouvrir);
    fermer.addEventListener('click', fermerFenetre);
    fenetre.addEventListener('close', vider); // aussi après « cancel » (Échap, retour)
    return { ouvrir, fermer: fermerFenetre, ouverte: () => fenetre.open };
  }

  return { PAGE, VIDE, brancher };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  matieresEcran.instance = matieresEcran.brancher(document);
}
