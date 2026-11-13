'use strict';

// Écrans de choix « sur l'eau » (08/11/2026, règle générale de Max, valable pour toutes les fenêtres de choix) :
// pas de grande fenêtre ni de cadre, de gros boutons identiques posés directement sur l'eau (« Fermer » compris).
// Transition : l'ancien écran disparaît dans le rien (fondu court), PUIS les boutons sortent de sous le sable
// (comme l'accueil à la montée). À la fermeture : les boutons disparaissent dans le rien, puis l'écran d'avant
// remonte de sous le sable. Animations réduites : rien de tout cela, ouverture et fermeture d'un coup.
// La fenêtre (un <dialog class="fenetre-choix">) s'ouvre TOUT DE SUITE (son contenu est prêt, et lisible par les
// lecteurs d'écran) ; seul l'affichage est retardé, en CSS. Repli si ça saccade : retirer le flou des keyframes.
const choixSurEau = (() => {
  const REGLAGES = Object.freeze({ sortieMs: 450, entreeMs: 1000 });

  function reduit(fenetre) {
    const vue = fenetre.ownerDocument.defaultView;
    return Boolean(vue && vue.matchMedia && vue.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }

  // État par fenêtre : minuterie de fermeture en cours, fenêtres cachées dessous.
  const etats = new WeakMap();
  function etat(fenetre) {
    if (!etats.has(fenetre)) {
      const e = { fermeture: null, retour: null, dessous: [] };
      etats.set(fenetre, e);
      // Fermeture par le retour du téléphone (« cancel » puis « close ») : l'écran d'avant revient quand même.
      fenetre.addEventListener('close', () => { if (!fenetre.open) revenir(fenetre); });
    }
    return etats.get(fenetre);
  }

  // L'écran d'avant (accueil, Autre, fenêtres ouvertes dessous) remonte de sous le sable.
  function revenir(fenetre) {
    const e = etat(fenetre);
    const doc = fenetre.ownerDocument;
    const html = doc.documentElement;
    if (e.fermeture !== null) { clearTimeout(e.fermeture); e.fermeture = null; }
    fenetre.classList.remove('choix-entree', 'choix-sortie');
    if (!html.classList.contains('choix-ouvert')) return;
    html.classList.remove('choix-ouvert');
    for (const d of e.dessous) d.classList.remove('cache-sous-choix');
    const dessous = e.dessous;
    e.dessous = [];
    if (reduit(fenetre)) return;
    html.classList.add('choix-retour');
    for (const d of dessous) d.classList.add('retour-sous-choix');
    if (e.retour !== null) clearTimeout(e.retour);
    e.retour = setTimeout(() => {
      e.retour = null;
      html.classList.remove('choix-retour');
      for (const d of dessous) d.classList.remove('retour-sous-choix');
    }, REGLAGES.entreeMs);
  }

  function ouvrir(fenetre) {
    const e = etat(fenetre);
    const doc = fenetre.ownerDocument;
    const html = doc.documentElement;
    // Rouverte pendant sa fermeture : la fermeture est annulée, elle reste là.
    if (e.fermeture !== null) {
      clearTimeout(e.fermeture);
      e.fermeture = null;
      fenetre.classList.remove('choix-sortie');
      return;
    }
    if (fenetre.open) return;
    const animer = !reduit(fenetre);
    html.style.setProperty('--choix-sortie', `${REGLAGES.sortieMs}ms`);
    html.style.setProperty('--choix-entree', `${REGLAGES.entreeMs}ms`);
    html.classList.remove('choix-retour');
    e.dessous = [...doc.querySelectorAll('dialog[open]')].filter(d => d !== fenetre);
    for (const d of e.dessous) { d.classList.remove('retour-sous-choix'); d.classList.add('cache-sous-choix'); }
    html.classList.add('choix-ouvert');
    fenetre.classList.remove('choix-sortie');
    fenetre.classList.toggle('choix-entree', animer);
    fenetre.showModal();
  }

  function fermer(fenetre) {
    const e = etat(fenetre);
    if (!fenetre.open || e.fermeture !== null) return;
    if (reduit(fenetre)) { fenetre.close(); revenir(fenetre); return; } // tout de suite (sans attendre « close »)
    fenetre.classList.remove('choix-entree');
    fenetre.classList.add('choix-sortie');
    e.fermeture = setTimeout(() => {
      e.fermeture = null;
      fenetre.classList.remove('choix-sortie');
      if (fenetre.open) fenetre.close();
      revenir(fenetre); // tout de suite (« close » le refera sans effet)
    }, REGLAGES.sortieMs);
  }

  // 08/11/2026 (demande de Max) : changement d'écran DANS une fenêtre de choix (dossiers ↔ morceaux) : la mise à jour
  // se fait tout de suite (le contenu est prêt) ; une copie inerte de l'ancien écran (« fantôme », sans identifiants)
  // disparaît dans le rien, puis le nouvel écran sort de sous le sable. Animations réduites : mise à jour seule.
  function changer(fenetre, miseAJour) {
    if (!fenetre.open || reduit(fenetre)) { miseAJour(); return; }
    const doc = fenetre.ownerDocument;
    const ancien = doc.querySelector('.choix-fantome');
    if (ancien) ancien.remove();
    const fantome = doc.createElement('div');
    fantome.className = 'choix-fantome';
    fantome.setAttribute('aria-hidden', 'true');
    fantome.inert = true;
    const placesCopies = []; // c171 : [copie, position gauche de l'original]
    for (const enfant of [...fenetre.children]) {
      if (enfant.hidden || enfant.classList.contains('pas-de-fantome') || enfant.classList.contains('choix-fantome')) continue;
      // 12/11/2026 (c173, défaut de c171 vu par Max) : un élément caché par le style (ex. les compteurs des chantiers quand une
      // fiche est ouverte) n'a pas de place : sa copie, à largeur 0, apparaissait écrasée à gauche pendant le fondu.
      if (!enfant.getClientRects().length) continue;
      const copie = enfant.cloneNode(true);
      for (const x of [copie, ...copie.querySelectorAll('[id]')]) x.removeAttribute('id');
      // 12/11/2026 (c171) : la copie garde la LARGEUR EXACTE de l'original (les carrés des chantiers suivent la largeur : une
      // copie un peu plus large les grandissait pendant le fondu).
      const place = enfant.getBoundingClientRect();
      copie.style.boxSizing = 'border-box';
      copie.style.width = `${place.width}px`;
      placesCopies.push([copie, place.left]);
      fantome.appendChild(copie);
    }
    miseAJour();
    fenetre.scrollTop = 0;
    fenetre.appendChild(fantome);
    // c171 : chaque copie reprend la position GAUCHE exacte de l'original (la fenêtre peut avoir une barre de défilement qui
    // décale son contenu ; la boîte des copies n'en a pas) : rien ne saute au toucher.
    for (const [copie, gauche] of placesCopies) {
      const ecart = gauche - copie.getBoundingClientRect().left;
      if (Math.abs(ecart) > 0.5) copie.style.transform = `translateX(${ecart}px)`;
    }
    reapparaitre(fenetre);
    void fantome.offsetWidth;
    fantome.classList.add('choix-fantome-part');
    setTimeout(() => fantome.remove(), REGLAGES.sortieMs + 50);
  }

  // 08/11/2026 : l'écran de la fenêtre ressort de sous le sable (après la disparition de ce qui était devant :
  // un autre écran de la même fenêtre, ou le lecteur qui s'en va en vapeur).
  function reapparaitre(fenetre) {
    if (!fenetre.open || reduit(fenetre)) return;
    fenetre.classList.remove('choix-entree', 'choix-sortie');
    void fenetre.offsetWidth; // l'animation repart du début
    fenetre.classList.add('choix-entree');
  }

  return { REGLAGES, ouvrir, fermer, changer, reapparaitre, enFermeture: fenetre => etat(fenetre).fermeture !== null };
})();
