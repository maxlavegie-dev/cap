'use strict';

// 08/11/2026 (accord de Max, choix A) : geste RETOUR universel.
// Un glissement net de HAUT EN BAS, parti de n'importe où dans la fenêtre (ou l'écran) du dessus, la ferme comme
// son bouton « Fermer », avec la même sortie douce que le lecteur MP3 (fondu de 450 ms ; rien si animations réduites).
// - Fenêtres connues de fermeture_fenetres.js : même sortie commune (« Garder / Jeter » si Max a commencé à écrire).
// - Autres fenêtres et écrans « Autre » / « Réglages » : le geste touche leur bouton « Fermer » (qui reste en secours).
// - Jamais : visionneuse PDF, visionneuse et lecteur MP3 (le lecteur garde son geste du bord droit).
// - Ignoré : départ tout en haut de l'écran (rideau des notifications), champs de texte, curseurs, déplacement
//   d'une tuile, liste qui n'est pas tout en haut (le doigt sert alors à la faire défiler).
// L'accueil et « Tout voir » gardent leurs propres gestes (accueil_cap.js, app.js) : ce module ne s'en mêle pas.
const gesteRetour = (() => {
  const REGLAGES = Object.freeze({
    fractionHauteur: 0.2, // au moins 20 % de la hauteur de l'écran (comme le lecteur)
    rapportVertical: 2, // trajet au moins 2 fois plus vertical qu'horizontal
    dureeMaxMs: 1500, // en moins de 1,5 s
    bandeHautPx: 48, // départ ignoré tout en haut (rideau des notifications d'Android)
    fonduMs: 450 // même durée que la vapeur du lecteur
  });
  // Fenêtres qui gardent leur bouton ou leur propre geste.
  const EXCLUES = new Set(['lecteur-pdf-relations', 'visionneuse-cap', 'lecteur-mp3-relations']);
  const CHAMPS = 'input, textarea, select, [contenteditable], [contenteditable=""], [contenteditable="true"], iframe, #geste-fermer-lecteur';
  // 09/11/2026 (défaut 3 vu par Max : la fenêtre du « + » ne se fermait pas à chaque fois) : ses champs d'une ligne et ses
  // listes à choisir couvrent presque toute la fenêtre ; un geste parti d'eux était ignoré. Il compte maintenant (un
  // glissement net de haut en bas n'écrit rien et n'ouvre pas la liste). Restent exclus : texte sur plusieurs lignes,
  // zones modifiables, cadres, curseurs. Avant : CHAMPS servait aussi au départ du geste.
  const CHAMPS_DEPART = 'textarea, [contenteditable], [contenteditable=""], [contenteditable="true"], iframe, #geste-fermer-lecteur, input[type="range"]';

  function brancher(doc, { fermetureFenetres = null, maintenant = () => Date.now() } = {}) {
    const vue = doc.defaultView;
    const racine = doc.documentElement;
    const reduit = () => Boolean(vue && vue.matchMedia && vue.matchMedia('(prefers-reduced-motion: reduce)').matches);
    let depart = null;
    let enCours = false;

    // La fenêtre (ou l'écran) que le geste fermerait, ou null.
    function fenetreDu(cible) {
      const ouverte = cible && cible.closest ? cible.closest('dialog[open]') : null;
      if (ouverte) return EXCLUES.has(ouverte.id) ? null : ouverte;
      if (doc.querySelector('dialog[open]')) return null; // une fenêtre est ouverte ailleurs : rien
      if (!racine.classList.contains('ecran-cap-ouvert')) return null; // accueil, « Tout voir » : leurs gestes à eux
      return doc.querySelector('.ecran-cap:not([hidden])');
    }

    // Une liste défilée (même un peu) entre le doigt et le haut de la page : le geste la fait défiler, il ne ferme pas.
    function listeEnHaut(cible) {
      for (let el = cible; el && el.nodeType === 1; el = el.parentElement) if (el.scrollTop > 0) return false;
      return !(doc.scrollingElement && doc.scrollingElement.scrollTop > 0);
    }

    function boutonFermer(fenetre) {
      return Array.from(fenetre.querySelectorAll('button')).find(b => b.textContent.trim() === 'Fermer'
        && !b.disabled && b.getClientRects().length > 0) || null;
    }

    function sortieDouce(fenetre, fin) {
      if (reduit()) { fin(); return; }
      enCours = true;
      fenetre.classList.add('geste-retour-sortie');
      vue.setTimeout(() => {
        enCours = false;
        fin();
        fenetre.classList.remove('geste-retour-sortie'); // même tâche que la fermeture : pas d'éclair
      }, REGLAGES.fonduMs);
    }

    // 08/11/2026 (décision de Max) : « Fermer » caché sur « Autre » et l'écran Micro : le geste touche le bouton caché.
    // 09/11/2026 : + l'écran Chercher (« Fermer » visible ; le geste touche le même bouton).
    const FERMER_ECRANS = { 'ecran-autre': 'fermer-autre', 'ecran-reglages': 'fermer-reglages', 'ecran-micro': 'fermer-micro', 'ecran-chercher': 'fermer-chercher-cap', 'ecran-bureau': 'fermer-bureau' }; // c165 : + Bureau

    function fermer(fenetre) {
      if (fenetre.tagName === 'DIALOG' && fermetureFenetres && fermetureFenetres.gerer
        && fermetureFenetres.gerer(fenetre, fin => sortieDouce(fenetre, fin))) return true;
      // Avant le 08/11/2026 : toujours « const bouton = boutonFermer(fenetre); » (bouton visible seulement).
      const cache = FERMER_ECRANS[fenetre.id] ? doc.getElementById(FERMER_ECRANS[fenetre.id]) : null;
      const bouton = cache || boutonFermer(fenetre);
      if (!bouton) return false;
      // Fenêtre de choix : « Fermer » fait déjà sa propre sortie (choix_sur_eau.js).
      if (fenetre.classList.contains('fenetre-choix')) bouton.click();
      else sortieDouce(fenetre, () => { if (bouton.isConnected && (bouton === cache || bouton.getClientRects().length > 0)) bouton.click(); });
      return true;
    }

    doc.addEventListener('touchstart', e => {
      depart = null;
      if (enCours || e.touches.length !== 1) return;
      const cible = e.target && e.target.closest ? e.target : null;
      if (!cible || cible.closest(CHAMPS_DEPART)) return; // 09/11/2026 (défaut 3). Avant : cible.closest(CHAMPS)
      const t = e.touches[0];
      if (t.clientY < REGLAGES.bandeHautPx) return;
      const fenetre = fenetreDu(cible);
      if (!fenetre || !listeEnHaut(cible) || doc.querySelector('.tuile.en-deplacement')) return;
      depart = { x: t.clientX, y: t.clientY, quand: maintenant(), cible, fenetre };
    }, { passive: true });
    doc.addEventListener('touchmove', e => {
      if (depart && (e.touches.length !== 1 || doc.querySelector('.tuile.en-deplacement'))) depart = null;
    }, { passive: true });
    doc.addEventListener('touchend', e => {
      const d = depart;
      depart = null;
      if (!d || enCours || e.touches.length || e.changedTouches.length !== 1) return;
      const t = e.changedTouches[0];
      const bas = t.clientY - d.y;
      const cote = Math.abs(t.clientX - d.x);
      const hauteur = (vue && vue.innerHeight) || 1;
      if (bas < REGLAGES.fractionHauteur * hauteur || bas < REGLAGES.rapportVertical * cote
        || maintenant() - d.quand > REGLAGES.dureeMaxMs) return;
      // Revérifié à la fin : la fenêtre est toujours là, la liste n'a pas défilé, aucune tuile n'est déplacée.
      if (doc.querySelector('.tuile.en-deplacement') || !listeEnHaut(d.cible) || fenetreDu(d.cible) !== d.fenetre) return;
      fermer(d.fenetre);
    }, { passive: true });
    doc.addEventListener('touchcancel', () => { depart = null; }, { passive: true });

    return { REGLAGES, fermer };
  }

  return { REGLAGES, brancher };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  gesteRetour.instance = gesteRetour.brancher(document, {
    fermetureFenetres: typeof fermetureFenetres !== 'undefined' ? fermetureFenetres : null
  });
}
