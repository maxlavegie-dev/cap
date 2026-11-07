'use strict';

// Accueil sur l'eau (étape A, 07/11/2026, plan accepté par Max), d'après le travail de Zencoder
// (Cap_eau_essai_v2_2026_11_07, lu sans rien y toucher) :
// - accueil : 3 boutons en colonne (Micro, Chercher, Autre), SOUS l'eau (l'eau passe devant, sans
//   jamais capter un toucher) ; « Chercher » ouvre, en attendant l'étape C, l'écran des tâches ;
// - écran « Autre » : Scanner, Réglages, interrupteur clair / sombre (écrans sur l'eau seulement), Fermer ;
// - écran « Réglages » : les réglages de Cap (textes inchangés) et le curseur d'intensité (MAQUETTE) ;
// - geste net de HAUT EN BAS sur l'accueil (rien d'ouvert) : retour à l'eau seule ;
// - alerte « Redonner l'accès à Google » visible PARTOUT : sous l'eau (sa petite eau à 35 %) sur les
//   écrans de Cap ; posée dans la fenêtre ouverte (musique, visionneuse…), au-dessus de l'eau, sinon.
// Aucun droit Google, aucun champ de connexion : seuls des boutons existants changent de place.
const accueilCap = (() => {
  const CLE_THEME = 'cap_theme_v1';
  const CLE_INTENSITE = 'cap_intensite_eau'; // même clé que la maquette de Zencoder ; NON reliée pour l'instant
  // Couleurs de l'eau en mode sombre : celles de l'eau v2 de Zencoder (fond sombre, pas noir pur).
  const EAU_SOMBRE = Object.freeze([Object.freeze([34, 40, 42]), Object.freeze([16, 20, 22])]);
  // Geste haut-bas : seuils réglables (accord de Max).
  const GESTE = Object.freeze({
    fractionHauteur: 0.3, // au moins 30 % de la hauteur de l'écran
    rapportVertical: 2, // trajet au moins 2 fois plus vertical qu'horizontal
    dureeMaxMs: 1000, // en moins d'une seconde
    bandeHautPx: 48 // départ ignoré tout en haut (rideau des notifications d'Android)
  });

  function brancher(doc, { eau = null, stockage = null, maintenant = () => Date.now(), creerPetiteEau = null } = {}) {
    const el = id => doc.getElementById(id);
    const racine = doc.documentElement;
    const corps = doc.body;
    const autre = el('ecran-autre');
    const reglages = el('ecran-reglages');
    const ouvrirChercher = el('ouvrir-chercher');
    const basculerVue = el('basculer-vue');
    const ecranComplet = el('ecran-complet');
    const alerte = el('alerte-google');
    const placeAlerte = alerte ? doc.createComment(' place de l’alerte Google ') : null;
    if (!autre || !reglages || !ouvrirChercher || !basculerVue || !ecranComplet || !alerte) return null;
    alerte.parentNode.insertBefore(placeAlerte, alerte);

    const lire = cle => { try { return stockage ? stockage.getItem(cle) : null; } catch (e) { return null; } };
    const ecrire = (cle, valeur) => { try { if (stockage) stockage.setItem(cle, valeur); } catch (e) { /* rien */ } };
    const vueComplete = () => corps.classList.contains('vue-complete');

    // ----- Écrans « Autre » et « Réglages » -----
    let ecranOuvert = null;
    function montrer(ecran) {
      for (const e of [autre, reglages]) e.hidden = e !== ecran;
      ecranOuvert = ecran;
      racine.classList.toggle('ecran-cap-ouvert', Boolean(ecran));
      appliquerTheme();
    }
    el('ouvrir-autre').addEventListener('click', () => montrer(autre));
    el('ouvrir-reglages-cap').addEventListener('click', () => montrer(reglages));
    el('fermer-autre').addEventListener('click', () => montrer(null));
    el('fermer-reglages').addEventListener('click', () => montrer(null));

    // « Chercher » : l'écran des tâches et rendez-vous, avec la barre de recherche (en attendant l'étape C).
    ouvrirChercher.addEventListener('click', () => { if (ecranComplet.hidden) basculerVue.click(); });
    const fermerChercher = el('fermer-chercher');
    if (fermerChercher) fermerChercher.addEventListener('click', () => { if (!ecranComplet.hidden) basculerVue.click(); });

    // ----- Mode clair / sombre (écrans sur l'eau seulement ; l'écran des tâches reste clair) -----
    let sombre = lire(CLE_THEME) !== 'clair';
    const boutonTheme = el('bouton-theme-cap');
    function appliquerTheme() {
      const surEau = !vueComplete();
      racine.classList.toggle('theme-cap-sombre', sombre);
      racine.classList.toggle('theme-cap-clair', !sombre);
      if (boutonTheme) boutonTheme.setAttribute('aria-checked', String(sombre));
      // Sombre sur l'eau : couleurs ET effets de l'eau v2 de Zencoder (liseré de crête, houle, lumière).
      const v2 = typeof ecranEau !== 'undefined' ? ecranEau.EAU_V2 : null;
      if (eau && typeof eau.changerCouleurs === 'function') eau.changerCouleurs(sombre && surEau ? EAU_SOMBRE.map(c => [...c]) : null, sombre && surEau ? v2 : null);
    }
    if (boutonTheme) boutonTheme.addEventListener('click', () => { sombre = !sombre; ecrire(CLE_THEME, sombre ? 'sombre' : 'clair'); appliquerTheme(); });
    // L'écran des tâches s'ouvre ou se ferme : l'eau reprend la bonne couleur.
    new doc.defaultView.MutationObserver(appliquerTheme).observe(corps, { attributes: true, attributeFilter: ['class'] });

    // ----- Curseur d'intensité : MAQUETTE (valeur gardée sous la clé de Zencoder, ne commande rien) -----
    const curseur = el('curseur-intensite-eau');
    if (curseur) {
      const gardee = Number(lire(CLE_INTENSITE));
      curseur.value = String(lire(CLE_INTENSITE) !== null && gardee >= 0 && gardee <= 100 ? gardee : 100);
      curseur.addEventListener('input', () => ecrire(CLE_INTENSITE, curseur.value));
    }

    // ----- Geste net de HAUT EN BAS sur l'accueil : retour à l'eau seule -----
    let depart = null;
    const accueilLibre = () => !vueComplete() && !ecranOuvert && !doc.querySelector('dialog[open]')
      && !racine.classList.contains('eau-ouverte');
    function retourEau() {
      const allerEau = el('aller-eau');
      if (allerEau) allerEau.click(); // même chemin que l'ancien bouton « Eau » (rien si l'eau est arrêtée)
    }
    doc.addEventListener('touchstart', e => {
      depart = null;
      if (e.touches.length !== 1 || !accueilLibre()) return;
      const cible = e.target && e.target.closest ? e.target : null;
      if (cible && cible.closest('input, textarea, select, #alerte-google, #ecran-eau')) return;
      const t = e.touches[0];
      if (t.clientY < GESTE.bandeHautPx) return;
      depart = { x: t.clientX, y: t.clientY, quand: maintenant() };
    }, { passive: true });
    doc.addEventListener('touchmove', e => { if (depart && e.touches.length !== 1) depart = null; }, { passive: true });
    doc.addEventListener('touchend', e => {
      const d = depart;
      depart = null;
      if (!d || e.touches.length || e.changedTouches.length !== 1 || !accueilLibre()) return;
      const t = e.changedTouches[0];
      const bas = t.clientY - d.y;
      const cote = Math.abs(t.clientX - d.x);
      const hauteur = doc.defaultView.innerHeight || 1;
      if (bas >= GESTE.fractionHauteur * hauteur && bas >= GESTE.rapportVertical * cote && maintenant() - d.quand <= GESTE.dureeMaxMs) retourEau();
    }, { passive: true });
    doc.addEventListener('touchcancel', () => { depart = null; }, { passive: true });

    // ----- Alerte Google partout -----
    let petiteEau = null;
    function placerAlerte() {
      const fenetres = [...doc.querySelectorAll('dialog[open]')];
      const cible = fenetres.length ? fenetres[fenetres.length - 1] : null;
      if (cible) {
        if (alerte.parentNode !== cible) cible.appendChild(alerte);
      } else if (alerte.previousSibling !== placeAlerte) {
        placeAlerte.parentNode.insertBefore(alerte, placeAlerte.nextSibling);
      }
      // Sous l'eau seulement sur les écrans de Cap (pas dans une fenêtre) et seulement si elle est visible.
      const sousEau = !cible && !alerte.hidden;
      alerte.classList.toggle('alerte-sous-eau', sousEau);
      alerte.classList.toggle('alerte-dans-fenetre', Boolean(cible));
      racine.classList.toggle('alerte-google-visible', !alerte.hidden);
      if (!alerte.hidden) racine.style.setProperty('--hauteur-alerte', `${Math.ceil(alerte.getBoundingClientRect().height) + 16}px`);
      if (!petiteEau && sousEau && typeof creerPetiteEau === 'function') petiteEau = creerPetiteEau(el('eau-alerte'));
      if (petiteEau) { if (sousEau) petiteEau.demarrer(); else petiteEau.arreter(); }
    }
    const observateur = new doc.defaultView.MutationObserver(placerAlerte);
    observateur.observe(doc.body, { subtree: true, attributes: true, attributeFilter: ['open', 'hidden'] });
    placerAlerte();
    appliquerTheme();

    return { GESTE, montrer, placerAlerte, retourEau, theme: () => (sombre ? 'sombre' : 'clair'), ecranOuvert: () => ecranOuvert };
  }

  return { CLE_THEME, CLE_INTENSITE, EAU_SOMBRE, GESTE, brancher };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  let stockage = null;
  try { stockage = window.localStorage; } catch (e) { stockage = null; }
  accueilCap.instance = accueilCap.brancher(document, {
    eau: (typeof ecranEau !== 'undefined' && ecranEau.instance) || null,
    stockage,
    // Petite eau de l'alerte : la même eau que partout, en moins fine (petite surface).
    creerPetiteEau: toile => (toile && typeof ecranEau !== 'undefined' ? ecranEau.creerCouche(toile, { cellules: 6000 }) : null)
  });
}
