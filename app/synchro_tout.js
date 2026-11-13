'use strict';

// 10/11/2026 (accord de Max, c98, priorité n° 1) : UN SEUL BOUTON « Tout synchroniser », présent sur tous les écrans (il suit
// la fenêtre ouverte du dessus, comme le petit micro et le petit livre). Il enchaîne :
//  1. la connexion du compte Cap : si elle manque ou finit dans moins de 5 minutes, Google s'ouvre (mêmes droits qu'avant,
//     aucun nouveau) ; Max valide lui-même ; au retour, Cap REPREND tout seul ici (marque « synchro en cours », 10 minutes) ;
//  2. le rafraîchissement de ce que Cap lit dans le Drive : la Liste des chantiers, les dossiers des chantiers, les journaux
//     des relations (LECTURES seulement) ;
//  3. la mise à niveau cumulative de tout ce qui existe (dossiers des chantiers et journaux des relations) : la LISTE
//     COMPLÈTE d'abord, puis UN SEUL « Oui » de Max avant toute écriture ; « Non » ne change rien ; relancé : aucun doublon ;
//     arrêt au premier problème.
// Rien n'est effacé, renommé ni déplacé. Écrit seulement après le Oui, et seulement ce qui est déjà permis (créer, ajouter
// à la fin d'un document créé par Cap).
const synchroTout = (() => {
  const CLE_RETOUR = 'cap_retour_synchro_v1';
  const DUREE_RETOUR_MS = 10 * 60 * 1000;
  const deux = n => String(n).padStart(2, '0');
  const heure = t => { const d = new Date(t); return `${deux(d.getHours())} h ${deux(d.getMinutes())}`; };

  // La marque posée juste avant d'aller chez Google (lue par relations_compte.js pour ne pas ouvrir « Réglages du Drive »).
  function retourEnAttente(stockage, maintenant = Date.now()) {
    try {
      const m = JSON.parse(stockage.getItem(CLE_RETOUR));
      return Boolean(m && Number.isFinite(m.quand) && maintenant - m.quand >= 0 && maintenant - m.quand < DUREE_RETOUR_MS);
    } catch (erreur) { return false; }
  }

  function brancher(doc, {
    compteCap = (typeof googleCompteRelations !== 'undefined' ? googleCompteRelations : null),
    liste = () => (typeof chantiers !== 'undefined' ? chantiers : null),
    dossiers = () => (typeof chantiersDossiers !== 'undefined' ? chantiersDossiers : null),
    journaux = () => (typeof journauxRelations !== 'undefined' ? journauxRelations : null),
    // 12/11/2026 (c150, A1) : mémoire des relations sur le téléphone (memoire_relations.js), mise à jour à chaque synchro.
    memoire = () => (typeof memoireRelations !== 'undefined' ? memoireRelations : null),
    // 12/11/2026 (c153, A4) : le Dictionnaire général (compte PERSONNEL, fichier choisi une fois, lecture seule, en mémoire)
    // et la règle de nom des dossiers « r_… » (relations.js), pour compter les écarts.
    // 12/11/2026 (c154, A3a, décision de Max) : l'onglet « Dictionnaire » est lu EN ENTIER (toutes ses colonnes), une seule fois,
    // pour les écarts ET pour la copie des coordonnées des relations (coordonnees_relations.js, sur le téléphone seulement).
    dictionnaire = () => (typeof classement !== 'undefined' && typeof googleConnexion !== 'undefined'
      ? { connecte: () => googleConnexion.connecte(), lire: () => (typeof classement.lireDictionnaireComplet === 'function' ? classement.lireDictionnaireComplet() : classement.lireDictionnairePersonnes()) } : null),
    regleRelations = () => (typeof relations !== 'undefined' ? relations : null),
    coordonnees = () => (typeof coordonneesRelations !== 'undefined' ? coordonneesRelations : null),
    ecranChantiers = () => (typeof chantiersEcran !== 'undefined' ? chantiersEcran.instance : null),
    stockage = (typeof localStorage !== 'undefined' ? localStorage : null),
    maintenant = () => Date.now(),
    transition = (typeof choixSurEau !== 'undefined' ? choixSurEau : null),
    attendreAvantGoogle = 1500,
    minuteur = (f, ms) => setTimeout(f, ms),
    // 11/11/2026 (c143) : le téléphone a-t-il du réseau ? (remplaçable dans les tests)
    enLigne = () => (typeof navigator === 'undefined' || navigator.onLine !== false)
  } = {}) {
    // 10/11/2026 (c101) : les éléments sont cherchés DANS la fenêtre, jamais ailleurs dans la page (avant : getElementById
    // de « etat-synchro », un identifiant déjà pris par l'écran Réglages : le texte partait là, la fenêtre restait vide).
    const bouton = doc.getElementById('bouton-synchro');
    const fenetre = doc.getElementById('synchro-tout');
    if (!fenetre) return null;
    const dans = id => fenetre.querySelector(`#${id}`);
    let etat = dans('texte-synchro-tout');
    if (!etat) { // jamais de fenêtre vide : la zone de texte est créée si elle manque
      etat = doc.createElement('p');
      etat.id = 'texte-synchro-tout';
      etat.className = 'relations-gros';
      etat.setAttribute('role', 'status');
      fenetre.insertBefore(etat, fenetre.firstChild);
    }
    const oui = dans('oui-synchro-tout');
    const non = dans('non-synchro-tout');
    const fermer = dans('fermer-synchro-tout');
    if (![oui, non, fermer].every(Boolean)) return null;
    const raison = e => (e && e.message ? e.message : 'raison inconnue');
    // 12/11/2026 (c153, A4) : combien de dossiers « r_… » n'ont pas de ligne dans le Dictionnaire, combien de lignes n'ont
    // pas de dossier : des NOMBRES seulement, jamais un nom ; rien gardé, rien écrit. Pas de compte personnel connecté ou
    // pas de Dictionnaire choisi : Cap le dit, sans ouvrir Google.
    async function direEcarts(lues) {
      const D = dictionnaire(); const R = regleRelations();
      if (!D || !R || typeof R.ecarts !== 'function') return;
      const debut = '   Relations et Dictionnaire :';
      if (!D.connecte()) { dire(`${debut} pas comparés (ton compte Google personnel n’est pas connecté : « Autoriser Cap (agenda et Drive) » dans les Réglages).`); return; }
      try {
        const valeurs = await D.lire();
        if (!valeurs) { dire(`${debut} pas comparés (Dictionnaire général pas encore choisi dans « Réglages du Drive »).`); return; }
        const e = R.ecarts(valeurs, lues.map(r => r.nom));
        dire(`${debut} ${e.dossiersSansLigne} dossier${e.dossiersSansLigne > 1 ? 's' : ''} « r_ » sans ligne dans le Dictionnaire, ${e.lignesSansDossier} ligne${e.lignesSansDossier > 1 ? 's' : ''} sans dossier.`);
        direCoordonnees(valeurs, lues, R); // c154 (A3a)
      } catch (erreur) { dire(`${debut} pas comparés (le Dictionnaire n’a pas pu être lu).`); }
    }
    // 12/11/2026 (c154, A3a) : copie des fiches des personnes qui ont un dossier « r_… », sur le téléphone seulement ; l'écran
    // ne montre que des NOMBRES. Lecture ratée ou copie refusée : l'ancienne copie reste.
    function direCoordonnees(valeurs, lues, R) {
      const C = coordonnees();
      if (!C) return;
      const copie = C.garder(stockage, valeurs, lues.map(r => r.nom), R, maintenant());
      if (!copie) { dire('   Coordonnées des relations : pas gardées (l’ancienne copie reste).'); return; }
      const n = C.compter(copie);
      dire(`   Coordonnées des relations : ${n.trouvees} fiche${n.trouvees > 1 ? 's' : ''} gardée${n.trouvees > 1 ? 's' : ''} sur le téléphone seulement (${n.homonymes} nom${n.homonymes > 1 ? 's' : ''} avec homonymes, ${n.absentes} dossier${n.absentes > 1 ? 's' : ''} sans fiche).`);
    }
    let lignes = [];
    let plans = null;
    let enCours = false;
    const dire = texte => { lignes.push(texte); etat.textContent = lignes.join('\n'); etat.hidden = false; };
    function question(montrer) {
      oui.hidden = non.hidden = !montrer;
      oui.disabled = false;
      fenetre.classList.toggle('mode-confirmation', montrer);
    }
    function ouvrir() {
      if (transition) transition.ouvrir(fenetre); else if (!fenetre.open) fenetre.showModal();
    }
    function finir(texte) { if (texte) dire(texte); question(false); enCours = false; plans = null; }

    async function lancer({ apresRetour = false } = {}) {
      if (enCours) return '';
      enCours = true;
      lignes = [];
      plans = null;
      question(false);
      ouvrir();
      dire('Tout synchroniser… (rien n’est effacé)');
      // 11/11/2026 (accord de Max, c143, ligne 120 ; même idée que c139 à c142) : SANS RÉSEAU, rien n'est tenté : ni Google
      // (la page d'erreur de Chrome s'ouvrait si la connexion était à refaire), ni lecture, ni écriture. Avant : l'étape 1
      // ouvrait Google, ou chaque étape échouait l'une après l'autre.
      if (!enLigne()) {
        finir('Pas de réseau : « Tout synchroniser » passe par Internet. Reconnecte le téléphone, puis touche de nouveau « Tout synchroniser ». Rien n’a été fait.');
        return etat.textContent;
      }
      // 1. Connexion du compte Cap.
      if (!compteCap || (typeof compteCap.adresse === 'function' && !compteCap.adresse())) {
        finir('1. Identifiant du compte Cap absent : écris-le d’abord dans « Réglages du Drive ». Rien n’a été fait.');
        return etat.textContent;
      }
      const minutes = typeof compteCap.minutesRestantes === 'function' ? compteCap.minutesRestantes() : 60;
      if (!compteCap.connecte() || minutes < 5) {
        if (apresRetour) {
          const m = typeof compteCap.message === 'function' ? compteCap.message() : '';
          finir(`1. La connexion du compte Cap n’a pas abouti${m ? ` : ${m}` : ''}. Rien d’autre n’a été fait ; touche de nouveau « Tout synchroniser ».`);
          return etat.textContent;
        }
        dire('1. Connexion du compte Cap : Google va s’ouvrir. Valide-le toi-même (mêmes droits qu’avant), puis Cap reprendra tout seul ici.');
        try { if (stockage) stockage.setItem(CLE_RETOUR, JSON.stringify({ quand: maintenant() })); } catch (erreur) { /* sans marque : il faudra retoucher le bouton */ }
        minuteur(() => {
          try { compteCap.seConnecter(); } catch (erreur) {
            try { if (stockage) stockage.removeItem(CLE_RETOUR); } catch (e) { /* rien */ }
            finir(`La connexion n’a pas pu s’ouvrir : ${raison(erreur)}`);
          }
        }, attendreAvantGoogle);
        enCours = false;
        return etat.textContent;
      }
      dire('1. Compte Cap connecté.');
      // 2. Rafraîchir les lectures (rien n'est écrit).
      const L = liste(); const D = dossiers(); const J = journaux();
      if (L && typeof L.lire === 'function') {
        try {
          const copie = await L.lire();
          dire(`2. Liste des chantiers relue : ${copie.chantiers.length} chantier${copie.chantiers.length > 1 ? 's' : ''}.`);
          const ecran = ecranChantiers();
          if (ecran && typeof ecran.ouverte === 'function' && ecran.ouverte() && typeof ecran.afficher === 'function') ecran.afficher(copie);
        } catch (erreur) { dire(`2. Liste des chantiers : ${raison(erreur)}`); }
      }
      if (D) {
        try {
          const existantsD = await D.dossiersExistants(compteCap);
          dire(`   Dossiers de chantier : ${existantsD.size}.`);
          try { if (typeof D.garderIds === 'function') D.garderIds(stockage, existantsD); } catch (e) { /* c152 : copie pas gardée, rien de grave */ }
        } catch (erreur) { dire(`   Dossiers de chantier : ${raison(erreur)}`); }
      }
      if (J) {
        try {
          const existantsJ = await J.journauxExistants(compteCap);
          dire(`   Journaux des relations : ${existantsJ.size}.`);
          // c150 (A1) : noms, dossiers et journaux des relations gardés sur le téléphone (rien d'affiché ; lecture ratée :
          // l'ancienne mémoire reste). Avant : seulement le nombre de journaux.
          let lues = null;
          try { if (typeof J.listerRelations === 'function') lues = await J.listerRelations(compteCap); } catch (e) { lues = null; /* ancienne mémoire gardée */ }
          try { const M = memoire(); if (M && lues) M.garder(stockage, lues, existantsJ, maintenant()); } catch (e) { /* ancienne mémoire gardée */ }
          if (lues) await direEcarts(lues); // c153 (A4)
        } catch (erreur) { dire(`   Journaux des relations : ${raison(erreur)}`); }
      }
      // 3. Mise à niveau : la liste complète d'abord.
      let planC = [];
      let planR = [];
      try {
        if (D) planC = await D.planMiseANiveau(compteCap);
        if (J) planR = await J.planMiseANiveau(compteCap);
      } catch (erreur) { finir(`3. Mise à niveau : ${raison(erreur)} Rien n’a été changé.`); return etat.textContent; }
      if (!planC.length && !planR.length) { finir(`3. Mise à niveau : rien à changer.\nSynchronisé à ${heure(maintenant())}.`); return etat.textContent; }
      plans = { planC, planR };
      const listeTexte = [...planC.map(p => `• Chantier « ${p.nom} » : ${p.changements.join(' ; ')}`), ...planR.map(p => `• Relation « ${p.nom} » : ${p.changements.join(' ; ')}`)];
      dire(`3. À mettre à niveau, dans le Drive du compte Cap :\n${listeTexte.join('\n')}\nRien d’effacé, renommé ni déplacé. Je le fais ?`);
      question(true);
      try { fenetre.scrollTop = fenetre.scrollHeight; } catch (e) { /* rien */ }
      return etat.textContent;
    }

    async function confirmer() {
      if (!plans) return '';
      const { planC, planR } = plans;
      plans = null;
      question(false);
      oui.disabled = true;
      dire('Mise à niveau en cours… (rien n’est effacé)');
      const D = dossiers(); const J = journaux();
      try {
        if (planC.length && D) { const r = await D.appliquerMiseANiveau(compteCap); dire(`Chantiers mis à niveau : ${r.faits.length}.`); }
        if (planR.length && J) { const r = await J.appliquerMiseANiveau(compteCap); dire(`Journaux des relations mis à niveau : ${r.faits.length}.`); }
        finir(`Synchronisé à ${heure(maintenant())}.`);
      } catch (erreur) { finir(raison(erreur)); }
      return etat.textContent;
    }

    // 10/11/2026 (c101) : toute erreur inattendue s'écrit en clair (jamais de fenêtre vide ni d'échec muet).
    const lancerSur = options => Promise.resolve().then(() => lancer(options)).catch(erreur => {
      enCours = false;
      if (!fenetre.open) ouvrir();
      finir(`La synchronisation s’est arrêtée : ${raison(erreur)}`);
      return etat.textContent;
    });
    if (bouton) bouton.addEventListener('click', () => { void lancerSur(); });
    oui.addEventListener('click', () => { void confirmer(); });
    non.addEventListener('click', () => { if (plans) finir('Rien n’a été changé.'); });
    fermer.addEventListener('click', () => { if (!fenetre.open) return; if (transition) transition.fermer(fenetre); else fenetre.close(); });
    // Double toucher (hors boutons) pendant la question = « Non ».
    let dernier = null;
    fenetre.addEventListener('pointerup', e => {
      if (!fenetre.classList.contains('mode-confirmation') || non.hidden || (e.target && e.target.closest && e.target.closest('button'))) { dernier = null; return; }
      const t = Date.now();
      if (dernier && t - dernier.t < 350 && Math.hypot(e.clientX - dernier.x, e.clientY - dernier.y) < 40) { dernier = null; non.click(); return; }
      dernier = { t, x: e.clientX, y: e.clientY };
    });

    // Retour de Google pendant une synchronisation : reprendre tout seul (une fois), quand tous les scripts sont chargés.
    function reprendreSiRetour() {
      if (!stockage || !compteCap || typeof compteCap.retourRecent !== 'function' || !compteCap.retourRecent()) return false;
      if (!retourEnAttente(stockage, maintenant())) return false;
      try { stockage.removeItem(CLE_RETOUR); } catch (erreur) { /* rien */ }
      void lancerSur({ apresRetour: true });
      return true;
    }
    return { lancer: lancerSur, confirmer, reprendreSiRetour };
  }
  return { CLE_RETOUR, retourEnAttente, brancher };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  const brancherSynchro = () => {
    synchroTout.instance = synchroTout.brancher(document);
    if (synchroTout.instance) synchroTout.instance.reprendreSiRetour();
  };
  // Après le chargement de TOUS les scripts (chantiers, journaux…) : la page se recharge au retour de Google.
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', brancherSynchro, { once: true });
  else brancherSynchro();
}
