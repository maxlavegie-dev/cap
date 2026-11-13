'use strict';

// 10/11/2026 (accord de Max, c90) : JOURNAUX DES RELATIONS, dans le Drive du COMPTE CAP.
// - Un seul dossier créé par Cap, « Journaux des relations » (à la racine, marque invisible cap_relations_journaux), avec
//   UN journal par personne (document Google « Journal – nom »), relié au dossier de relation (« Relations » › « r_… ») par
//   une marque invisible (cap_relation_journal = identifiant Drive du dossier de relation : le lien tient même si le
//   dossier est renommé).
// - Première ligne datée : « Journal ouvert par Cap le JJ/MM/AAAA à HH h MM pour le dossier « r_… ». » (date de création
//   du JOURNAL, lue dans le Drive, jamais inventée), écrite seulement si elle n'y est pas déjà.
// - Le dossier de relation n'est JAMAIS touché (lu seulement) ; rien d'effacé, renommé, déplacé ni partagé.
// - Rien sans le Oui de Max à l'écran. 10/11/2026 (c103, accord de Max) : PLUS DE LIMITE du nombre de journaux ; toujours
//   UN journal à la fois, seulement quand Max le demande, liste d'abord, aucune création en série ; verrou : une seule
//   création en cours (un deuxième appui pendant la création est refusé sans rien créer).
// - Mise à niveau cumulative : les journaux déjà créés reçoivent ce qui leur manque (aujourd'hui : la ligne datée), liste
//   montrée d'abord, Oui, aucun doublon.
// Droits : ceux d'aujourd'hui (lecture : drive.readonly ; création et ajout à la fin d'un document créé par Cap : drive.file
// et le service Google Docs, activé par Max le 10/11/2026).
const journauxRelations = (() => {
  const DRIVE = 'https://www.googleapis.com/drive/v3/files';
  const DOCS = 'https://docs.googleapis.com/v1/documents';
  const DOSSIER = 'application/vnd.google-apps.folder';
  const DOC = 'application/vnd.google-apps.document';
  const NOM_RACINE = 'Journaux des relations';
  const MARQUES = Object.freeze({ racine: 'cap_relations_journaux', journal: 'cap_relation_journal' });
  // 10/11/2026 (c103, accord de Max) : limite RETIRÉE. Avant : 2 (c91), 1 (c90).
  const DEBUT_LIGNE = 'Journal ouvert par Cap le';
  const echapper = texte => String(texte).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
  const deux = n => String(n).padStart(2, '0');

  // 10/11/2026 (c103) : lit TOUTES les pages (sans limite, il peut y avoir plus de 200 journaux) ; 50 pages au plus.
  async function lister(compte, q) {
    const tous = [];
    let page = '';
    let tours = 0;
    do {
      const params = { q, fields: 'nextPageToken,files(id,name,appProperties,createdTime)', pageSize: '200', spaces: 'drive' };
      if (page) params.pageToken = page;
      const corps = await (await compte.appeler(`${DRIVE}?${new URLSearchParams(params)}`)).json();
      tous.push(...(Array.isArray(corps.files) ? corps.files : []));
      page = corps.nextPageToken || '';
    } while (page && ++tours < 50);
    if (page) throw new Error('Le compte Cap a trop d’éléments à lire d’un coup : rien ne sera créé. Préviens Claude Code.');
    return tous;
  }
  const parMarque = (compte, cle, valeur, type) => lister(compte,
    `appProperties has { key='${cle}' and value='${echapper(valeur)}' } and mimeType='${type}' and trashed=false`);
  const unSeul = (liste, quoi) => {
    if (liste.length > 1) throw new Error(`Le compte Cap a ${liste.length} ${quoi} avec la même marque : rien ne sera créé. Préviens Claude Code.`);
    return liste[0] || null;
  };

  // Nom du journal : « Journal – » + le nom du dossier sans « r_ », sans caractères gênants, 120 caractères au plus.
  function nomJournal(nomDossier) {
    const nom = String(nomDossier || '').replace(/^r_/, '').replace(/[\\/:*?"<>|\u0000-\u001f]+/g, '-').replace(/\s+/g, ' ').trim().slice(0, 110).trim();
    return `Journal – ${nom || 'relation'}`;
  }
  function texteLigne(nomDossier, quand) {
    const d = new Date(quand);
    const date = !quand || Number.isNaN(d.getTime()) ? 'une date que je n’ai pas pu lire'
      : `${deux(d.getDate())}/${deux(d.getMonth() + 1)}/${d.getFullYear()} à ${deux(d.getHours())} h ${deux(d.getMinutes())}`;
    return `${DEBUT_LIGNE} ${date} pour le dossier « ${nomDossier} ».`;
  }
  const ligneDejaLa = texte => String(texte || '').split(/\r?\n/).some(l => l.trim().startsWith(DEBUT_LIGNE));
  async function lireJournal(compte, id) {
    return (await compte.appeler(`${DRIVE}/${encodeURIComponent(id)}/export?mimeType=${encodeURIComponent('text/plain')}`)).text();
  }
  async function ajouterLigne(compte, journal, nomDossier) {
    const texte = await lireJournal(compte, journal.id);
    if (ligneDejaLa(texte)) return false;
    const ligne = texteLigne(nomDossier, journal.createdTime);
    const corps = { requests: [{ insertText: { endOfSegmentLocation: {}, text: String(texte || '').trim() ? `\n${ligne}` : ligne } }] };
    await compte.appelerEcriture(`${DOCS}/${encodeURIComponent(journal.id)}:batchUpdate`, { method: 'POST', body: JSON.stringify(corps) });
    return true;
  }
  async function creerUn(compte, corps) {
    const reponse = await compte.appelerEcriture(`${DRIVE}?fields=id,createdTime`, { method: 'POST', body: JSON.stringify(corps) });
    const f = await reponse.json();
    if (!f || !f.id) throw new Error('Google n’a pas rendu l’élément créé.');
    return f;
  }

  // Les dossiers de relation : dans « Relations » (à la racine du compte Cap, un seul), nom commençant par « r_ » (LECTURE).
  async function listerRelations(compte) {
    const racines = (await lister(compte, `'root' in parents and mimeType='${DOSSIER}' and trashed=false`)).filter(f => f.name === 'Relations');
    if (racines.length !== 1) throw new Error(racines.length ? 'Plusieurs dossiers « Relations » à la racine du compte Cap : garde-en un seul.' : 'Aucun dossier « Relations » à la racine du compte Cap.');
    return (await lister(compte, `'${echapper(racines[0].id)}' in parents and mimeType='${DOSSIER}' and trashed=false`))
      .filter(f => String(f.name).startsWith('r_'))
      .map(f => ({ id: f.id, nom: String(f.name) }))
      .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));
  }
  // Les journaux déjà créés : Map identifiant du dossier de relation → journal (LECTURE).
  async function journauxExistants(compte) {
    const racine = unSeul(await parMarque(compte, MARQUES.racine, '1', DOSSIER), `dossiers « ${NOM_RACINE} »`);
    const existants = new Map();
    if (!racine) return existants;
    for (const f of await lister(compte, `'${echapper(racine.id)}' in parents and mimeType='${DOC}' and trashed=false`)) {
      const id = f.appProperties && f.appProperties[MARQUES.journal];
      if (id && !existants.has(id)) existants.set(id, f);
    }
    return existants;
  }

  // Ce qui serait créé pour une relation (LECTURE SEULE).
  async function preparer(compte, relation) {
    if (!relation || !relation.id) throw new Error('Dossier de relation inconnu : rien ne sera créé.');
    const racine = unSeul(await parMarque(compte, MARQUES.racine, '1', DOSSIER), `dossiers « ${NOM_RACINE} »`);
    const journal = unSeul(await parMarque(compte, MARQUES.journal, relation.id, DOC), 'journaux pour cette relation');
    let dejaCrees = 0;
    if (racine) dejaCrees = (await lister(compte, `'${echapper(racine.id)}' in parents and mimeType='${DOC}' and trashed=false`)).filter(f => f.appProperties && f.appProperties[MARQUES.journal]).length;
    const aCreer = [];
    if (!racine) aCreer.push(`le dossier « ${NOM_RACINE} » (première fois)`);
    if (!journal) aCreer.push(`le journal « ${nomJournal(relation.nom)} » dans ce dossier`);
    if (!journal || !ligneDejaLa(await lireJournal(compte, journal.id))) aCreer.push(`la ligne « ${DEBUT_LIGNE} (date) pour le dossier « ${relation.nom} ». » dans ce journal`);
    return { racine, journal, dejaCrees, aCreer };
  }

  // Crée ce qui manque, APRÈS le Oui de Max (tout est revérifié juste avant).
  // 10/11/2026 (c103) : verrou : une seule création à la fois (jamais deux journaux en même temps, jamais en série).
  let creationEnCours = false;
  async function creer(compte, relation) {
    if (creationEnCours) throw new Error('Une création est déjà en cours : attends qu’elle finisse. Rien de plus n’a été créé.');
    creationEnCours = true;
    try { return await creerSansVerrou(compte, relation); } finally { creationEnCours = false; }
  }
  async function creerSansVerrou(compte, relation) {
    const plan = await preparer(compte, relation);
    if (!plan.aCreer.length) return { cree: [], dejaLa: true, ligneErreur: '' };
    const cree = [];
    let ligneErreur = '';
    const racine = plan.racine || await creerUn(compte, { name: NOM_RACINE, mimeType: DOSSIER, parents: ['root'], appProperties: { [MARQUES.racine]: '1' } });
    if (!plan.racine) cree.push(NOM_RACINE);
    const journal = plan.journal || await creerUn(compte, { name: nomJournal(relation.nom), mimeType: DOC, parents: [racine.id], appProperties: { [MARQUES.journal]: relation.id } });
    if (!plan.journal) cree.push(nomJournal(relation.nom));
    try {
      if (await ajouterLigne(compte, journal, relation.nom)) cree.push('la ligne datée du journal');
    } catch (erreur) { ligneErreur = erreur && erreur.message ? erreur.message : 'raison inconnue'; }
    return { cree, dejaLa: false, ligneErreur };
  }

  // Mise à niveau cumulative des journaux DÉJÀ créés (lecture seule, puis application après le Oui).
  async function planMiseANiveau(compte) {
    const existants = await journauxExistants(compte);
    if (!existants.size) return [];
    const noms = new Map();
    try { for (const r of await listerRelations(compte)) noms.set(r.id, r.nom); } catch (erreur) { /* noms inconnus : le nom du journal sert */ }
    const plan = [];
    for (const [idRelation, journal] of existants) {
      const nomDossier = noms.get(idRelation) || String(journal.name).replace(/^Journal – /, 'r_');
      if (!ligneDejaLa(await lireJournal(compte, journal.id))) plan.push({ idRelation, nom: journal.name, nomDossier, journal, changements: [`ajouter « ${texteLigne(nomDossier, journal.createdTime)} »`] });
    }
    return plan;
  }
  async function appliquerMiseANiveau(compte) {
    const plan = await planMiseANiveau(compte);
    const faits = [];
    for (const p of plan) {
      try {
        await ajouterLigne(compte, p.journal, p.nomDossier);
        faits.push(p.nom);
      } catch (erreur) {
        const e = new Error(`Arrêt à « ${p.nom} » : ${erreur && erreur.message ? erreur.message : 'raison inconnue'}${faits.length ? ` Déjà mis à niveau : ${faits.map(n => `« ${n} »`).join(', ')}.` : ''} Rien n’a été effacé ; relancer ne refait que ce qui manque.`);
        e.faits = faits;
        throw e;
      }
    }
    return { faits };
  }

  // 10/11/2026 (c91) : adresses ouvertes HORS de Cap (lecture seule) : le journal (Google Docs) et le dossier de relation (Drive).
  const adresseJournal = id => `https://docs.google.com/document/d/${encodeURIComponent(id)}/edit`;
  const adresseDossier = id => `https://drive.google.com/drive/folders/${encodeURIComponent(id)}`;

  return { NOM_RACINE, MARQUES, DEBUT_LIGNE, nomJournal, texteLigne, listerRelations, journauxExistants, preparer, creer, planMiseANiveau, appliquerMiseANiveau, adresseJournal, adresseDossier };
})();

// ----- L'écran « Journaux des relations » (Réglages du Drive) : gros boutons numérotés sur l'eau, une question avant toute
// création (« Oui, créer » / « Non », collés en bas, en mode confirmation), mise à niveau avec la liste d'abord.
const journauxRelationsEcran = (() => {
  function brancher(doc, {
    logique = journauxRelations,
    compteCap = (typeof googleCompteRelations !== 'undefined' ? googleCompteRelations : null),
    transition = (typeof choixSurEau !== 'undefined' ? choixSurEau : null),
    // 12/11/2026 (c150, A1) : mémoire des relations sur le téléphone, mise à jour à chaque lecture complète.
    stockage = (typeof localStorage !== 'undefined' ? localStorage : null),
    memoire = (typeof memoireRelations !== 'undefined' ? memoireRelations : null),
    // 11/11/2026 (c144) : le téléphone a-t-il du réseau ? (remplaçable dans les tests)
    enLigne = () => (typeof navigator === 'undefined' || navigator.onLine !== false)
  } = {}) {
    const el = id => doc.getElementById(id);
    const fenetre = el('journaux-relations');
    const ouvrirBouton = el('ouvrir-journaux-relations');
    const etat = el('etat-journaux-relations');
    const liste = el('liste-journaux-relations');
    const question = el('question-journal-relation');
    const oui = el('oui-journal-relation');
    const non = el('non-journal-relation');
    const fermer = el('fermer-journaux-relations');
    // 10/11/2026 (c91) : deux liens hors de Cap, seulement pour une personne qui a déjà un journal.
    const liens = el('liens-journal-relation');
    const lienJournal = el('ouvrir-journal-relation');
    const lienDossier = el('ouvrir-dossier-relation');
    if (![fenetre, etat, liste, question, oui, non, fermer].every(Boolean)) return null;
    let choisie = null;
    function montrerLiens() {
      if (!liens || !lienJournal || !lienDossier) return;
      const journal = choisie && existants.get(choisie.id);
      liens.hidden = !journal;
      if (journal) { lienJournal.href = logique.adresseJournal(journal.id); lienDossier.href = logique.adresseDossier(choisie.id); }
      else { lienJournal.removeAttribute('href'); lienDossier.removeAttribute('href'); }
    }
    const noeud = (balise, classe, texte) => { const n = doc.createElement(balise); if (classe) n.className = classe; if (texte !== undefined) n.textContent = texte; return n; };
    const raison = e => (e && e.message ? e.message : 'raison inconnue');
    let relations = [];
    let existants = new Map();
    let action = null; // { type: 'creation', relation } (c147 : plus de { type: 'maj' }, « Tout synchroniser » le fait)
    const connecte = () => Boolean(compteCap) && !(typeof compteCap.connecte === 'function' && !compteCap.connecte());
    const dire = texte => { etat.hidden = !texte; etat.textContent = texte || ''; };
    function etape(nom, texte = '') {
      question.hidden = !texte;
      question.textContent = texte;
      oui.hidden = non.hidden = nom !== 'question';
      oui.disabled = nom === 'travail';
      fenetre.classList.toggle('mode-confirmation', nom === 'question' || nom === 'travail');
      if (nom === 'question') { try { fenetre.scrollTop = 0; } catch (e) { /* rien */ } }
    }
    function afficher() {
      liste.replaceChildren(...relations.map((r, i) => {
        const b = noeud('button', 'ligne-morceau ligne-choix-voix ligne-relation');
        b.type = 'button';
        b.append(noeud('span', 'numero-morceau', String(i + 1)), noeud('span', 'nom-morceau', r.nom));
        if (existants.has(r.id)) b.append(noeud('span', 'marque-journal', 'journal'));
        b.addEventListener('click', () => { choisie = r; montrerLiens(); void demanderCreation(r); }); // c91 : + les liens
        return b;
      }));
    }
    // 11/11/2026 (accord de Max, c144, ligne 120 ; même idée que c139 à c143) : SANS RÉSEAU, la vraie cause, « Pas de réseau »,
    // au lieu de « compte Cap pas connecté : touche « Autoriser… » » (page d'erreur de Chrome) ; rien n'est tenté.
    const pasDeReseau = fin => `Pas de réseau : les journaux des relations sont dans le Drive du compte Cap, sur Internet. Reconnecte le téléphone, puis réessaie. ${fin}`;
    // c150 (A1) : après une lecture COMPLÈTE réussie seulement (relations ET journaux lus).
    function memoriser() { try { if (memoire) memoire.garder(stockage, relations, existants); } catch (e) { /* rien de cassé */ } }
    async function lire() {
      if (!enLigne()) { dire(pasDeReseau('Rien n’a été lu.')); return; } // c144
      if (!connecte()) { dire('Le compte Cap n’est pas connecté (ou la connexion a expiré) : touche « Autoriser la lecture du compte Cap », puis reviens ici. Rien n’a été créé.'); return; }
      dire('Je lis les dossiers de « Relations »… (rien n’est modifié)');
      try {
        relations = await logique.listerRelations(compteCap);
        existants = await logique.journauxExistants(compteCap);
        memoriser();
        afficher();
        dire(relations.length ? '' : 'Aucun dossier « r_ » dans « Relations ».');
      } catch (erreur) { dire(`${raison(erreur)} Rien n’a été créé.`); }
    }
    async function ouvrir() {
      action = null;
      choisie = null; montrerLiens(); // c91
      etape('depart');
      liste.replaceChildren();
      if (transition) transition.ouvrir(fenetre); else if (!fenetre.open) fenetre.showModal();
      await lire();
    }
    async function demanderCreation(relation) {
      action = { type: 'creation', relation };
      if (!enLigne()) { action = null; const t = pasDeReseau('Rien n’a été créé.'); etape('fini', t); return t; } // c144
      etape('travail', 'Je regarde ce qui existe déjà… (rien n’est créé)');
      let plan;
      try { plan = await logique.preparer(compteCap, relation); } catch (erreur) { action = null; etape('fini', `${raison(erreur)} Rien n’a été créé.`); return ''; }
      if (!plan.aCreer.length) { action = null; const t = `« ${relation.nom} » a déjà son journal : rien à créer.`; etape('fini', t); return t; }
      // 10/11/2026 (c103) : plus de limite du nombre de journaux ; toujours un seul, après la liste et le Oui de Max.
      const t = `Je vais créer, dans le Drive du compte Cap : ${plan.aCreer.join(', puis ')}. Rien dans le dossier « ${relation.nom} » lui-même, rien d’autre. Je crée ?`;
      etape('question', t);
      return t;
    }
    async function confirmer() {
      const a = action;
      if (!a) return '';
      etape('travail', 'Création en cours… (rien n’est effacé)');
      try {
        const r = await logique.creer(compteCap, a.relation);
        let t = r.dejaLa ? `« ${a.relation.nom} » avait déjà son journal : rien créé.` : `C’est fait, dans le Drive du compte Cap : ${r.cree.map(n => `« ${n} »`).join(', ')}.`;
        if (r.ligneErreur) t += ` Mais la ligne datée n’a pas pu être écrite : ${r.ligneErreur}`;
        action = null;
        etape('fini', t);
        try { existants = await logique.journauxExistants(compteCap); memoriser(); afficher(); montrerLiens(); } catch (e) { /* la marque viendra à la prochaine ouverture */ }
        return t;
      } catch (erreur) {
        action = null;
        const t = `${raison(erreur)} Rien n’a été effacé ; tu peux réessayer : ce qui existe déjà ne sera pas recréé.`;
        etape('fini', t);
        return t;
      }
    }
    if (ouvrirBouton) ouvrirBouton.addEventListener('click', () => { void ouvrir(); });
    oui.addEventListener('click', () => { void confirmer(); });
    non.addEventListener('click', () => { action = null; etape('fini', 'Rien n’a été créé.'); });
    // 12/11/2026 (c147, décision de Max, ligne 92) : bouton « Mettre à niveau les journaux des relations » RETIRÉ (« Tout synchroniser »).
    const fermerFenetre = () => { if (!fenetre.open) return; if (transition) transition.fermer(fenetre); else fenetre.close(); };
    fermer.addEventListener('click', fermerFenetre);
    // Double toucher (hors boutons) pendant une question = « Non ».
    let dernier = null;
    fenetre.addEventListener('pointerup', e => {
      if (!fenetre.classList.contains('mode-confirmation') || non.hidden || (e.target && e.target.closest && e.target.closest('button'))) { dernier = null; return; }
      const t = Date.now();
      if (dernier && t - dernier.t < 350 && Math.hypot(e.clientX - dernier.x, e.clientY - dernier.y) < 40) { dernier = null; non.click(); return; }
      dernier = { t, x: e.clientX, y: e.clientY };
    });
    return { ouvrir, demanderCreation, confirmer, fermer: fermerFenetre };
  }
  return { brancher };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  journauxRelationsEcran.instance = journauxRelationsEcran.brancher(document);
}
