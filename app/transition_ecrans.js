'use strict';

// 08/11/2026 (accord de Max, étape 1 de l'écran Micro) : ouvertures DOUCES des écrans de Cap.
// Règle de Max : l'écran d'avant disparaît doucement dans le rien (fondu de 450 ms), PUIS les nouveaux boutons
// sortent de sous le sable (1 s, mêmes keyframes que la montée de l'accueil). Animations réduites : rien, d'un coup.
// Écrans concernés : l'accueil (ses 3 boutons), « Autre », « Réglages », « Chercher » (« Tout voir » et sa barre).
// Le changement d'état se fait TOUT DE SUITE (mêmes règles qu'avant, mêmes boutons touchables) ; seul l'affichage
// suit : l'écran qui part reste dessiné à sa place, sans capter aucun toucher, le temps de son fondu.
const transitionEcrans = (() => {
  const REGLAGES = Object.freeze({ sortieMs: 450, entreeMs: 1000 });
  // 08/11/2026 (étape 2) : + « ecran-micro ».
  // 09/11/2026 : + « ecran-chercher » (écran Chercher de Zencoder).
  // Avant : const ECRANS = ['accueil-boutons', 'ecran-autre', 'ecran-reglages', 'ecran-micro', 'ecran-complet', 'zone-recherche'];
  const ECRANS = ['accueil-boutons', 'ecran-autre', 'ecran-reglages', 'ecran-micro', 'ecran-chercher', 'ecran-complet', 'zone-recherche'];
  // 09/11/2026 : un changement demandé PENDANT la mise à jour d'un autre (Chercher → To-do : l'écran des tâches
  // s'ouvre par son propre bouton) se fait tout de suite, dans la même transition (pas de transition dans la transition).
  const dedans = new WeakSet();
  const PROPRIETES = ['display', 'position', 'top', 'left', 'width', 'height', 'margin', 'box-sizing', 'pointer-events', 'z-index'];
  const encours = new WeakMap(); // doc -> { minuteries, partants, arrivants }

  function reduit(doc) {
    const vue = doc.defaultView;
    return Boolean(vue && vue.matchMedia && vue.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }
  const visible = el => el.getClientRects().length > 0;

  // Termine tout de suite une transition en cours (changement rapide d'écran).
  function terminer(doc) {
    const e = encours.get(doc);
    if (!e) return;
    encours.delete(doc);
    e.minuteries.forEach(clearTimeout);
    e.partants.forEach(nettoyerPartant);
    e.arrivants.forEach(el => el.classList.remove('ecran-entree', 'ecran-entree-directe'));
  }

  function nettoyerPartant({ el, ancien }) {
    el.classList.remove('ecran-part');
    el.inert = ancien.inert;
    for (const p of PROPRIETES) {
      if (ancien.styles[p]) el.style.setProperty(p, ancien.styles[p][0], ancien.styles[p][1]);
      else el.style.removeProperty(p);
    }
  }

  // miseAJour : la fonction d'avant (elle montre / cache les écrans) ; elle est appelée tout de suite.
  function changer(doc, miseAJour) {
    if (doc && dedans.has(doc)) { miseAJour(); return; } // 09/11/2026
    if (!doc || reduit(doc)) { if (doc) terminer(doc); miseAJour(); return; }
    terminer(doc);
    const els = ECRANS.map(id => doc.getElementById(id)).filter(Boolean);
    const avant = new Map();
    for (const el of els) if (visible(el)) {
      const r = el.getBoundingClientRect();
      avant.set(el, { r, display: doc.defaultView.getComputedStyle(el).display });
    }
    dedans.add(doc); // 09/11/2026
    try { miseAJour(); } finally { dedans.delete(doc); }
    const partis = els.filter(el => avant.has(el) && !visible(el));
    const arrives = els.filter(el => !avant.has(el) && visible(el));
    if (!partis.length && !arrives.length) return;
    const e = { minuteries: [], partants: [], arrivants: arrives };
    encours.set(doc, e);
    // L'écran qui part reste dessiné à sa place, inerte, et fond (sauf s'il a déjà fondu : geste de retour).
    for (const el of partis) {
      if (el.classList.contains('geste-retour-sortie')) continue;
      const { r, display } = avant.get(el);
      const ancien = { inert: el.inert, styles: {} };
      for (const p of PROPRIETES) {
        const v = el.style.getPropertyValue(p);
        if (v) ancien.styles[p] = [v, el.style.getPropertyPriority(p)];
      }
      const forcer = { display, position: 'fixed', top: `${r.top}px`, left: `${r.left}px`, width: `${r.width}px`,
        height: `${r.height}px`, margin: '0', 'box-sizing': 'border-box', 'pointer-events': 'none', 'z-index': '1' };
      for (const [p, v] of Object.entries(forcer)) el.style.setProperty(p, v, 'important');
      el.inert = true;
      el.classList.add('ecran-part');
      e.partants.push({ el, ancien });
    }
    const attente = e.partants.length > 0;
    for (const el of arrives) el.classList.add(attente ? 'ecran-entree' : 'ecran-entree-directe');
    e.minuteries.push(setTimeout(() => { e.partants.forEach(nettoyerPartant); e.partants = []; }, REGLAGES.sortieMs));
    e.minuteries.push(setTimeout(() => {
      arrives.forEach(el => el.classList.remove('ecran-entree', 'ecran-entree-directe'));
      if (encours.get(doc) === e) encours.delete(doc);
    }, (attente ? REGLAGES.sortieMs : 0) + REGLAGES.entreeMs));
  }

  return { REGLAGES, ECRANS, changer, terminer };
})();
