'use strict';

// 08/11/2026 (accord de Max, étape 1 du codage des commandes vocales) : actions de NAVIGATION dites au micro du milieu.
// Chaque action touche le MÊME bouton que le doigt (mêmes écrans, mêmes transitions douces, même geste de retour) :
// aucun écran n'est ouvert « à côté » du code d'avant. Rien n'est envoyé à l'IA ; rien n'est effacé.
// Écrans qui n'existent pas encore : Cap le dit (« pas encore prêt »). Quitter Cap : Android ne le permet pas à une
// page ; Cap le dit franchement (une sortie par la coque Android pourra être ajoutée plus tard, avec l'accord de Max).
const commandesNavigation = (() => {
  const PAS_PRET = {
    'NAV-05': 'Agenda', 'NAV-06': 'Notes', 'NAV-12': 'La liste de courses', 'NAV-14': 'L’échéancier',
    'NAV-15': 'Le journal de bord', 'NAV-16': 'Le dictionnaire des personnes', 'NAV-17': 'La biographie',
    'NAV-18': 'Les archives', 'NAV-19': 'Les mails', 'NAV-20': 'Le répertoire', 'NAV-23': 'Le profil'
  };

  // 09/11/2026 : + « eau » (l'écran d'eau de Cap ; remplaçable dans les tests).
  function brancher(doc, { commandes = (typeof commandesVocales !== 'undefined' ? commandesVocales : null),
    geste = () => (typeof gesteRetour !== 'undefined' ? gesteRetour.instance : null),
    eau = () => (typeof ecranEau !== 'undefined' ? ecranEau.instance : null) } = {}) {
    if (!commandes) return null;
    const el = id => doc.getElementById(id);
    const toucher = id => { const b = el(id); if (b) b.click(); return Boolean(b); };
    const racine = doc.documentElement;
    const vueComplete = () => doc.body.classList.contains('vue-complete');
    const ecranCap = () => doc.querySelector('.ecran-cap:not([hidden])');
    // 09/11/2026 : + l'écran Chercher (son « Fermer » est visible).
    const FERMER_ECRAN = { 'ecran-autre': 'fermer-autre', 'ecran-reglages': 'fermer-reglages', 'ecran-micro': 'fermer-micro', 'ecran-chercher': 'fermer-chercher-cap', 'ecran-bureau': 'fermer-bureau' }; // c165 : + Bureau

    // 09/11/2026 (défaut vu par Max sur c60) : sur l'ÉCRAN D'EAU, les commandes changeaient d'écran SOUS l'eau (elle reste
    // par-dessus tout) : rien ne se voyait. Maintenant, une commande qui ouvre un écran fait d'abord entrer dans Cap
    // (même chemin que le glissement vers le haut).
    function sortirDeLEau() {
      if (!racine.classList.contains('eau-ouverte')) return;
      const e = eau();
      if (e && typeof e.entrerDansCap === 'function') e.entrerDansCap();
    }
    // 09/11/2026 (défauts 2 et 3 vus par Max sur c72 : « retourne à l'accueil », « remets l'eau » : pouce, mais rien ne
    // change) : la visionneuse (et ses vignettes), la fenêtre « Musique », ses choix ou le lecteur restaient PAR-DESSUS
    // l'accueil. Ils sont maintenant fermés d'abord, par leurs propres boutons (mémoire libérée comme au doigt). Le lecteur
    // qui joue passe en arrière-plan (la musique continue, la note ronde reste). Les fenêtres où Max écrit ne sont pas
    // touchées (rien de ce qu'il a tapé n'est perdu).
    function fermerFenetresDessus() {
      const vi = typeof visionneuseCap !== 'undefined' ? visionneuseCap.instance : null;
      for (let i = 0; i < 3 && vi && vi.fermerParVoix && (vi.ouverte() || vi.vignettesOuvertes()); i++) vi.fermerParVoix();
      const ouverte = id => { const f = el(id); return Boolean(f && f.open); };
      if (ouverte('choix-voix')) toucher('fermer-choix-voix');
      if (ouverte('musique-relations')) toucher('fermer-musique-relations');
      if (ouverte('chantiers-cap')) toucher('fermer-chantiers'); // 09/11/2026 (chantiers, séance 1)
      const lecteur = typeof relationsMp3 !== 'undefined' ? relationsMp3.instance : null;
      if (ouverte('lecteur-mp3-relations') && lecteur && lecteur.etat && lecteur.etat().actif) lecteur.arrierePlan();
      else if (ouverte('lecteur-mp3-relations')) el('lecteur-mp3-relations').close();
    }
    const viderPile = () => doc.dispatchEvent(new doc.defaultView.CustomEvent('cap-vider-pile')); // 09/11/2026 (étape 3)
    // Revenir à l'accueil : ferme l'écran de Cap ouvert (Autre, Réglages, Micro) ou « Tout voir ».
    // 09/11/2026 (étape 3) : vide d'abord la pile (sinon « Fermer » reviendrait à l'écran d'avant, pas à l'accueil).
    function accueil() {
      fermerFenetresDessus(); // 09/11/2026 (défauts 2 et 3)
      viderPile();
      const e = ecranCap();
      if (e && FERMER_ECRAN[e.id]) toucher(FERMER_ECRAN[e.id]);
      if (vueComplete()) toucher('fermer-chercher');
      // 12/11/2026 (c167) : la ligne de recherche de l'accueil se ferme aussi (accueil propre, comme l'ancien écran Chercher).
      const bandeRecherche = el('bande-recherche-accueil');
      if (bandeRecherche) bandeRecherche.hidden = true;
    }

    const actions = {
      // 09/11/2026 : « Chercher » ouvre maintenant l'écran Chercher (4 icônes, barre) : depuis l'écran des tâches, on
      // le ferme d'abord ; déjà sur Chercher, rien ne bouge. Avant : const e = ecranCap(); if (e && FERMER_ECRAN[e.id])
      // toucher(FERMER_ECRAN[e.id]); toucher('ouvrir-chercher'); return 'J’ouvre Chercher.';
      'NAV-01': () => {
        const e = ecranCap();
        if (e && e.id === 'ecran-chercher') return 'Chercher est déjà ouvert.';
        // 12/11/2026 (c167) : la ligne de recherche de l'accueil : déjà ouverte, rien ne bouge ; un écran ouvert se ferme d'abord.
        const bande = el('bande-recherche-accueil');
        if (bande) {
          if (!bande.hidden && !e && !vueComplete()) return 'Chercher est déjà ouvert.';
          if (vueComplete()) toucher('fermer-chercher');
          if (e && FERMER_ECRAN[e.id]) toucher(FERMER_ECRAN[e.id]);
          if (bande.hidden) toucher('ouvrir-chercher');
          return 'J’ouvre Chercher.';
        }
        if (vueComplete()) toucher('fermer-chercher');
        if (!el('ecran-chercher') && e && FERMER_ECRAN[e.id]) toucher(FERMER_ECRAN[e.id]);
        toucher('ouvrir-chercher');
        return 'J’ouvre Chercher.';
      },
      'NAV-02': () => { if (vueComplete()) toucher('fermer-chercher'); toucher('ouvrir-autre'); return 'J’ouvre Autre.'; },
      'NAV-03': () => { if (vueComplete()) toucher('fermer-chercher'); toucher('ouvrir-reglages-cap'); return 'J’ouvre Réglages.'; },
      'NAV-04': () => (toucher('ouvrir-scanner') ? 'J’ouvre le scanner.' : 'Le scanner n’est pas disponible ici.'),
      'NAV-07': () => { accueil(); return 'Retour à l’accueil.'; },
      'NAV-08': () => {
        accueil();
        const eau = el('ecran-eau');
        if (!eau || !el('aller-eau')) return 'L’eau seule n’est pas disponible ici.';
        toucher('aller-eau');
        return 'Retour à l’eau.';
      },
      'NAV-09': () => {
        // 08/11/2026 (étape 3c) : d'abord la visionneuse (document en grand, puis vignettes) et la fenêtre de choix.
        const vi = typeof visionneuseCap !== 'undefined' ? visionneuseCap.instance : null;
        if (vi && vi.fermerParVoix && (vi.ouverte() || vi.vignettesOuvertes())) return vi.fermerParVoix();
        if (el('choix-voix') && el('choix-voix').open) { toucher('fermer-choix-voix'); return 'Je ferme.'; }
        // 11/11/2026 (c130) : comme le bouton « Fermer » : sur une fiche, retour à la liste ; sur la liste, fermeture.
        if (el('chantiers-cap') && el('chantiers-cap').open) { const fiche = el('chantiers-cap').classList.contains('fiche-ouverte'); toucher('fermer-chantiers'); return fiche ? 'Je reviens à la liste des chantiers.' : 'Je ferme les chantiers.'; } // 09/11/2026
        const e = ecranCap();
        const fenetre = e || null;
        if (fenetre) {
          const g = geste();
          if (g && g.fermer) g.fermer(fenetre); else toucher(FERMER_ECRAN[fenetre.id]);
          return 'Je ferme.';
        }
        if (vueComplete()) { toucher('fermer-chercher'); return 'Je ferme.'; }
        // 12/11/2026 (décision de Max, c167) : la ligne de recherche de l'accueil se ferme aussi à la voix.
        const bandeRecherche = el('bande-recherche-accueil');
        if (bandeRecherche && !bandeRecherche.hidden) { bandeRecherche.hidden = true; return 'Je ferme.'; }
        return 'Il n’y a rien à fermer.';
      },
      'NAV-10': () => theme(true),
      'NAV-11': () => theme(false),
      // 09/11/2026 : « tes tâches » = l'icône To-do de Chercher (l'écran des tâches directement).
      // Avant : 'NAV-13': () => actions['NAV-01']().replace('Chercher', 'tes tâches'),
      'NAV-13': () => {
        if (vueComplete()) return 'Tes tâches sont déjà ouvertes.';
        if (!el('chercher-todo')) return actions['NAV-01']().replace('Chercher', 'tes tâches');
        toucher('chercher-todo');
        return 'J’ouvre tes tâches.';
      },
      'NAV-21': () => (toucher('ouvrir-aide') ? 'J’ouvre l’aide.' : 'L’aide n’est pas disponible ici.'),
      // 09/11/2026 (étape 2) : plus d'écran Micro : retour à l'accueil, « + » et la nouvelle icône apparaissent autour du
      // gros micro (sans écouter). Avant : if (vueComplete()) toucher('fermer-chercher'); toucher('ouvrir-micro');
      'NAV-22': () => {
        accueil();
        if (!el('rangee-micro-accueil')) { toucher('ouvrir-micro'); return 'Voici le micro.'; }
        doc.dispatchEvent(new doc.defaultView.CustomEvent('cap-montrer-outils-micro'));
        return 'Voici le micro.';
      },
      'NAV-24': () => 'Je ne peux pas fermer Cap moi-même : utilise le bouton des applications d’Android.'
    };
    // Mode sombre (true) ou clair (false) : l'interrupteur lune / soleil de « Autre » (même bouton que le doigt).
    function theme(sombre) {
      const bouton = el('bouton-theme-cap');
      if (!bouton) return 'Le réglage clair / sombre n’est pas disponible ici.';
      const estSombre = bouton.getAttribute('aria-checked') === 'true';
      if (estSombre === sombre) return sombre ? 'C’est déjà le mode sombre.' : 'C’est déjà le mode clair.';
      bouton.click();
      return sombre ? 'Mode sombre.' : 'Mode clair.';
    }
    for (const [code, nom] of Object.entries(PAS_PRET)) actions[code] = () => `${nom} : pas encore prêt.`;
    // 09/11/2026 : les commandes qui montrent un écran quittent d'abord l'écran d'eau (NAV-08 y va, il n'en sort pas).
    for (const code of ['NAV-01', 'NAV-02', 'NAV-03', 'NAV-04', 'NAV-07', 'NAV-13', 'NAV-21', 'NAV-22']) {
      const action = actions[code];
      if (action) actions[code] = (...args) => { sortirDeLEau(); return action(...args); };
    }
    for (const [code, action] of Object.entries(actions)) commandes.brancherAction(code, action);
    return { actions, accueil, theme };
  }

  return { brancher, PAS_PRET };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  commandesNavigation.instance = commandesNavigation.brancher(document);
}
