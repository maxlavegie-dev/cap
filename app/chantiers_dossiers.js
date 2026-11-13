'use strict';

// 10/11/2026 (accord de Max, CHANTIERS, séance 3 sur 7) : un DOSSIER par chantier, dans le Drive du COMPTE CAP.
// - Dans le dossier « Chantiers » (à la racine du Drive du compte Cap, créé la première fois), un dossier au nom du
//   chantier, avec un « Journal de bord » vide dedans (document Google).
// - Chaque élément porte une marque INVISIBLE (appProperties) : « Chantiers » (cap_chantiers_racine), le dossier
//   (cap_chantier = CH-xxx), le journal (cap_chantier_journal = CH-xxx). Avant toute création, Cap cherche la marque :
//   ce qui existe déjà n'est jamais recréé (aucun doublon), une coupure au milieu se reprend sans rien refaire.
// - Rien n'est jamais effacé, renommé, déplacé ni partagé (le compte Cap ne peut que lire et créer : voir
//   google_compte_relations.js). Rien n'est écrit dans la Liste des chantiers.
// - Rien n'est créé sans le Oui de Max à l'écran (chantiers_ecran.js montre d'abord ce qui va être créé).
// - 10/11/2026 (c102, accord de Max) : PLUS DE LIMITE du nombre de dossiers. Mais toujours UN chantier à la fois, seulement
//   quand Max le demande, après la liste et son Oui ; aucune création en série (aucune fonction ne crée plusieurs chantiers) ;
//   une seule création en cours à la fois (verrou : un deuxième appui pendant la création est refusé, sans rien créer).
// Sans DOM.
const chantiersDossiers = (() => {
  const DRIVE = 'https://www.googleapis.com/drive/v3/files';
  const DOSSIER = 'application/vnd.google-apps.folder';
  const DOC = 'application/vnd.google-apps.document';
  const NOM_RACINE = 'Chantiers';
  const NOM_JOURNAL = 'Journal de bord';
  const MARQUES = Object.freeze({ racine: 'cap_chantiers_racine', chantier: 'cap_chantier', journal: 'cap_chantier_journal', documents: 'cap_chantier_documents' }); // c89 : + documents
  // 10/11/2026 (c102, accord de Max) : limite RETIRÉE. Avant : 3 (c89), 2 (c88), 1 (c85).
  // 10/11/2026 (c89, marche 3) : un sous-dossier « Documents » dans chaque dossier de chantier (marque invisible).
  const NOM_DOCUMENTS = 'Documents';
  // 10/11/2026 (c88, marche 2) : première ligne DATÉE du journal, avec la date de création du DOSSIER lue dans le Drive
  // (jamais inventée). Écrite seulement si elle n'y est pas déjà (sûr à relancer).
  const DEBUT_LIGNE = 'Dossier créé par Cap le';
  const DOCS = 'https://docs.googleapis.com/v1/documents';

  // Nom du dossier : le nom du chantier, sans les caractères qui gênent dans un nom de fichier (/ \ : * ? " < > | et les
  // caractères invisibles), espaces resserrés, 120 caractères au plus ; vide : l'identifiant.
  function nomDossier(c) {
    const nom = String((c && c.nom) || '').replace(/[\\/:*?"<>|\u0000-\u001f]+/g, '-').replace(/\s+/g, ' ').replace(/^[\s.-]+|[\s.-]+$/g, '').slice(0, 120).trim();
    return nom || String((c && c.id) || '').trim();
  }
  const identifiantValide = id => /^CH-\d{1,6}$/.test(String(id || '').trim());
  const echapper = texte => String(texte).replace(/\\/g, '\\\\').replace(/'/g, "\\'");

  // 10/11/2026 (c102) : lit TOUTES les pages (sans limite, il peut y avoir plus de 100 dossiers) ; 50 pages au plus.
  async function lister(compte, q) {
    const tous = [];
    let page = '';
    let tours = 0;
    do {
      const params = { q, fields: 'nextPageToken,files(id,name,appProperties,createdTime)', pageSize: '100', spaces: 'drive' }; // 10/11/2026 : + createdTime
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

  // Ce qui existe déjà et ce qui serait créé (LECTURE SEULE). Rend { id, nom, racine, dossier, journal, dejaCrees, aCreer }. Plusieurs éléments avec la même marque : Cap s'arrête et le dit (jamais de choix au hasard).
  async function preparer(compte, chantier) {
    const id = String((chantier && chantier.id) || '').trim();
    if (!identifiantValide(id)) throw new Error('Ce chantier n’a pas d’identifiant CH-xxx dans la Liste : rien ne sera créé.');
    const nom = nomDossier(chantier);
    const unSeul = (liste, quoi) => {
      if (liste.length > 1) throw new Error(`Le compte Cap a ${liste.length} ${quoi} avec la même marque : rien ne sera créé. Préviens Claude Code.`);
      return liste[0] || null;
    };
    const racine = unSeul(await parMarque(compte, MARQUES.racine, '1', DOSSIER), 'dossiers « Chantiers »');
    const dossier = unSeul(await parMarque(compte, MARQUES.chantier, id, DOSSIER), `dossiers pour ${id}`);
    const journal = dossier ? unSeul(await parMarque(compte, MARQUES.journal, id, DOC), `journaux pour ${id}`) : null;
    const documents = dossier ? unSeul(await parMarque(compte, MARQUES.documents, id, DOSSIER), `dossiers « ${NOM_DOCUMENTS} » pour ${id}`) : null; // c89
    let dejaCrees = 0;
    if (racine) {
      const enfants = await lister(compte, `'${echapper(racine.id)}' in parents and mimeType='${DOSSIER}' and trashed=false`);
      dejaCrees = enfants.filter(f => f.appProperties && f.appProperties[MARQUES.chantier]).length;
    }
    const aCreer = [];
    if (!racine) aCreer.push(`le dossier « ${NOM_RACINE} » (première fois)`);
    if (!dossier) aCreer.push(`le dossier « ${nom} »`);
    if (!journal) aCreer.push(`un « ${NOM_JOURNAL} » dans ce dossier`);
    // 10/11/2026 (c88) : la ligne datée, si elle manque (journal absent, ou présent sans elle).
    const ligneManque = !journal || !ligneDejaLa(await lireJournal(compte, journal.id), id);
    if (ligneManque) aCreer.push(`la ligne « ${DEBUT_LIGNE} (date de création du dossier) (${id}). » dans ce journal`);
    if (!documents) aCreer.push(`un sous-dossier « ${NOM_DOCUMENTS} » dans ce dossier`); // c89
    return { id, nom, racine, dossier, journal, documents, dejaCrees, aCreer, ligneManque };
  }

  // ----- 10/11/2026 (c88, marche 2) : la ligne datée du journal -----
  const deux = n => String(n).padStart(2, '0');
  function texteLigne(id, quand) {
    const d = new Date(quand);
    if (!quand || Number.isNaN(d.getTime())) return `${DEBUT_LIGNE} une date que je n’ai pas pu lire (${id}).`; // jamais inventée
    return `${DEBUT_LIGNE} ${deux(d.getDate())}/${deux(d.getMonth() + 1)}/${d.getFullYear()} à ${deux(d.getHours())} h ${deux(d.getMinutes())} (${id}).`;
  }
  const ligneDejaLa = (texte, id) => String(texte || '').split(/\r?\n/).some(l => l.trim().startsWith(DEBUT_LIGNE) && l.includes(`(${id})`));
  async function lireJournal(compte, idJournal) {
    const url = `${DRIVE}/${encodeURIComponent(idJournal)}/export?mimeType=${encodeURIComponent('text/plain')}`;
    return (await compte.appeler(url)).text();
  }
  // Ajoute la ligne À LA FIN du journal (une seule demande « insertText » ; rien d'effacé), après avoir relu le journal.
  async function ajouterLigne(compte, idJournal, id, quandDossier) {
    const texte = await lireJournal(compte, idJournal);
    if (ligneDejaLa(texte, id)) return false;
    const ligne = texteLigne(id, quandDossier);
    const corps = { requests: [{ insertText: { endOfSegmentLocation: {}, text: String(texte || '').trim() ? `\n${ligne}` : ligne } }] };
    await compte.appelerEcriture(`${DOCS}/${encodeURIComponent(idJournal)}:batchUpdate`, { method: 'POST', body: JSON.stringify(corps) });
    return true;
  }

  async function creerUn(compte, corps) {
    const reponse = await compte.appelerEcriture(`${DRIVE}?fields=id,createdTime`, { method: 'POST', body: JSON.stringify(corps) }); // 10/11/2026 : + createdTime
    const fichier = await reponse.json();
    if (!fichier || !fichier.id) throw new Error('Google n’a pas rendu l’élément créé.');
    return fichier;
  }

  // Crée ce qui manque, dans l'ordre (« Chantiers », le dossier, le journal), APRÈS le Oui de Max. Tout est revérifié juste
  // avant (preparer) : rien n'est créé en double. Rend { cree: [...], dejaLa: bool }.
  // 10/11/2026 (c102) : verrou : une seule création à la fois (jamais deux chantiers en même temps, jamais en série).
  let creationEnCours = false;
  async function creer(compte, chantier) {
    if (creationEnCours) throw new Error('Une création est déjà en cours : attends qu’elle finisse. Rien de plus n’a été créé.');
    creationEnCours = true;
    try { return await creerSansVerrou(compte, chantier); } finally { creationEnCours = false; }
  }
  async function creerSansVerrou(compte, chantier) {
    const plan = await preparer(compte, chantier);
    if (!plan.aCreer.length) return { cree: [], dejaLa: true };
    const cree = [];
    let ligneErreur = '';
    const racine = plan.racine || await creerUn(compte, { name: NOM_RACINE, mimeType: DOSSIER, parents: ['root'], appProperties: { [MARQUES.racine]: '1' } });
    if (!plan.racine) cree.push(NOM_RACINE);
    const dossier = plan.dossier || await creerUn(compte, { name: plan.nom, mimeType: DOSSIER, parents: [racine.id], appProperties: { [MARQUES.chantier]: plan.id } });
    if (!plan.dossier) cree.push(plan.nom);
    let journal = plan.journal;
    if (!journal) {
      journal = await creerUn(compte, { name: NOM_JOURNAL, mimeType: DOC, parents: [dossier.id], appProperties: { [MARQUES.journal]: plan.id } });
      cree.push(NOM_JOURNAL);
    }
    // 10/11/2026 (c89) : le sous-dossier « Documents » (création seule), AVANT la ligne (une ligne impossible ne le bloque pas).
    let nouveauDocuments = false;
    if (!plan.documents) {
      await creerUn(compte, { name: NOM_DOCUMENTS, mimeType: DOSSIER, parents: [dossier.id], appProperties: { [MARQUES.documents]: plan.id } });
      nouveauDocuments = true;
    }
    // 10/11/2026 (c88) : la ligne datée. Si elle ne peut pas être écrite, le dossier et le journal restent (rien d'effacé) et
    // la raison est rendue ; une nouvelle tentative n'écrira que la ligne.
    try {
      if (await ajouterLigne(compte, journal.id, plan.id, dossier.createdTime)) cree.push('la ligne datée du journal');
    } catch (erreur) { ligneErreur = erreur && erreur.message ? erreur.message : 'raison inconnue'; }
    if (nouveauDocuments) cree.push(NOM_DOCUMENTS);
    return { cree, dejaLa: false, ligneErreur };
  }

  // ----- 10/11/2026 (c88, décision de Max) : MISE À NIVEAU CUMULATIVE de TOUS les chantiers déjà créés -----
  // planMiseANiveau : LECTURE SEULE ; pour chaque dossier de chantier (marque CH-xxx) dans « Chantiers » : ce qui lui manque
  // par rapport à la marche actuelle (journal, ligne datée). appliquerMiseANiveau : APRÈS le Oui de Max, refait le plan
  // (rien en double), applique chantier par chantier, s'arrête au premier problème (ce qui est fait reste fait).
  async function planMiseANiveau(compte) {
    const racines = await parMarque(compte, MARQUES.racine, '1', DOSSIER);
    if (racines.length > 1) throw new Error(`Le compte Cap a ${racines.length} dossiers « ${NOM_RACINE} » avec la même marque : rien ne sera changé. Préviens Claude Code.`);
    if (!racines.length) return [];
    const dossiers = (await lister(compte, `'${echapper(racines[0].id)}' in parents and mimeType='${DOSSIER}' and trashed=false`))
      .filter(f => f.appProperties && identifiantValide(f.appProperties[MARQUES.chantier]))
      .sort((a, b) => String(a.createdTime || '').localeCompare(String(b.createdTime || '')));
    const plan = [];
    for (const dossier of dossiers) {
      const id = dossier.appProperties[MARQUES.chantier];
      const journaux = await parMarque(compte, MARQUES.journal, id, DOC);
      if (journaux.length > 1) throw new Error(`Le compte Cap a ${journaux.length} journaux pour ${id} : rien ne sera changé. Préviens Claude Code.`);
      const journal = journaux[0] || null;
      const changements = [];
      if (!journal) changements.push(`créer le « ${NOM_JOURNAL} »`);
      if (!journal || !ligneDejaLa(await lireJournal(compte, journal.id), id)) changements.push(`ajouter « ${texteLigne(id, dossier.createdTime)} »`);
      // 10/11/2026 (c89) : le sous-dossier « Documents ».
      const lesDocuments = await parMarque(compte, MARQUES.documents, id, DOSSIER);
      if (lesDocuments.length > 1) throw new Error(`Le compte Cap a ${lesDocuments.length} dossiers « ${NOM_DOCUMENTS} » pour ${id} : rien ne sera changé. Préviens Claude Code.`);
      const documents = lesDocuments[0] || null;
      if (!documents) changements.push(`créer le sous-dossier « ${NOM_DOCUMENTS} »`);
      if (changements.length) plan.push({ id, nom: dossier.name, dossier, journal, documents, changements });
    }
    return plan;
  }
  async function appliquerMiseANiveau(compte) {
    const plan = await planMiseANiveau(compte);
    const faits = [];
    for (const p of plan) {
      try {
        let journal = p.journal;
        if (!journal) journal = await creerUn(compte, { name: NOM_JOURNAL, mimeType: DOC, parents: [p.dossier.id], appProperties: { [MARQUES.journal]: p.id } });
        await ajouterLigne(compte, journal.id, p.id, p.dossier.createdTime);
        if (!p.documents) await creerUn(compte, { name: NOM_DOCUMENTS, mimeType: DOSSIER, parents: [p.dossier.id], appProperties: { [MARQUES.documents]: p.id } }); // c89
        faits.push(p.nom);
      } catch (erreur) {
        const e = new Error(`Arrêt à « ${p.nom} » : ${erreur && erreur.message ? erreur.message : 'raison inconnue'}${faits.length ? ` Déjà mis à niveau : ${faits.map(n => `« ${n} »`).join(', ')}.` : ''} Rien n’a été effacé ; relancer ne refait que ce qui manque.`);
        e.faits = faits;
        throw e;
      }
    }
    return { faits };
  }

  // ----- 10/11/2026 (accord de Max, c92) : NOTE de Max ajoutée À LA FIN du journal d'un chantier -----
  // La ligne est préparée et MONTRÉE à Max d'abord (texteNote), puis écrite telle quelle après son Oui (ajouterNote).
  // Seulement un ajout à la fin : jamais de modification ni d'effacement. Pas de dossier ou pas de journal : rien n'est écrit
  // (le journal n'est jamais créé ici : c'est le rôle de « Créer le dossier » et de « Tout synchroniser », c147).
  // 11/11/2026 (c106, décision de Max) : PLUS DE LIMITE de longueur (avant : 500 caractères, ici, dans ajouterNote et dans
  // le champ de saisie de index.html). Seule la note vide est refusée, avec un message clair.
  function texteNote(texte, quand = Date.now()) {
    const propre = String(texte || '').replace(/\s+/g, ' ').trim();
    if (!propre) throw new Error('Écris d’abord ta note : rien n’a été ajouté.');
    const d = new Date(quand);
    return `${deux(d.getDate())}/${deux(d.getMonth() + 1)}/${d.getFullYear()} à ${deux(d.getHours())} h ${deux(d.getMinutes())} — ${propre}`;
  }
  // Un seul élément avec cette marque, sinon arrêt (jamais de choix au hasard).
  const seulOuRien = (liste, quoi) => {
    if (liste.length > 1) throw new Error(`Le compte Cap a ${liste.length} ${quoi} avec la même marque : rien n’a été ajouté. Préviens Claude Code.`);
    return liste[0] || null;
  };
  async function ajouterNote(compte, chantier, ligne) {
    const id = String((chantier && chantier.id) || '').trim();
    if (!identifiantValide(id)) throw new Error('Ce chantier n’a pas d’identifiant CH-xxx : rien n’a été ajouté.');
    if (!String(ligne || '').trim()) throw new Error('Ta note est vide : rien n’a été ajouté.'); // c106 : plus de limite de longueur
    const dossier = seulOuRien(await parMarque(compte, MARQUES.chantier, id, DOSSIER), `dossiers pour ${id}`);
    if (!dossier) throw new Error('Ce chantier n’a pas encore de dossier : rien n’a été ajouté.');
    const journal = seulOuRien(await parMarque(compte, MARQUES.journal, id, DOC), `journaux pour ${id}`);
    if (!journal) throw new Error('Ce chantier n’a pas de journal : touche le bouton « Tout synchroniser », il complète les dossiers déjà créés. Rien n’a été ajouté.');
    const texte = await lireJournal(compte, journal.id);
    const corps = { requests: [{ insertText: { endOfSegmentLocation: {}, text: String(texte || '').trim() ? `\n${ligne}` : ligne } }] };
    await compte.appelerEcriture(`${DOCS}/${encodeURIComponent(journal.id)}:batchUpdate`, { method: 'POST', body: JSON.stringify(corps) });
    return ligne;
  }

  // ----- 10/11/2026 (accord de Max, c93) : LIRE les dernières lignes du journal d'un chantier (LECTURE SEULE, rien écrit).
  async function lireDernieresLignes(compte, chantier, nombre = 5) {
    const id = String((chantier && chantier.id) || '').trim();
    if (!identifiantValide(id)) throw new Error('Ce chantier n’a pas d’identifiant CH-xxx.');
    const dossier = seulOuRien(await parMarque(compte, MARQUES.chantier, id, DOSSIER), `dossiers pour ${id}`);
    if (!dossier) throw new Error('Ce chantier n’a pas encore de dossier.');
    const journal = seulOuRien(await parMarque(compte, MARQUES.journal, id, DOC), `journaux pour ${id}`);
    if (!journal) throw new Error('Ce chantier n’a pas de journal : touche le bouton « Tout synchroniser », il complète les dossiers déjà créés.');
    const lignes = String(await lireJournal(compte, journal.id) || '').split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    return lignes.slice(-Math.max(1, nombre));
  }

  // ----- 10/11/2026 (accord de Max, c96) : VOIR les documents d'un chantier : le contenu de son sous-dossier « Documents »
  // (LECTURE SEULE : rien n'est ouvert, écrit ni envoyé). Rend { total, noms (les « max » premiers, par ordre de nom) }.
  async function listerDocuments(compte, chantier, max = 10) {
    const id = String((chantier && chantier.id) || '').trim();
    if (!identifiantValide(id)) throw new Error('Ce chantier n’a pas d’identifiant CH-xxx.');
    const dossier = seulOuRien(await parMarque(compte, MARQUES.chantier, id, DOSSIER), `dossiers pour ${id}`);
    if (!dossier) throw new Error('Ce chantier n’a pas encore de dossier.');
    const documents = seulOuRien(await parMarque(compte, MARQUES.documents, id, DOSSIER), `dossiers « ${NOM_DOCUMENTS} » pour ${id}`);
    if (!documents) throw new Error(`Ce chantier n’a pas de sous-dossier « ${NOM_DOCUMENTS} » : touche le bouton « Tout synchroniser », il complète les dossiers déjà créés.`);
    const tous = [];
    let page = '';
    let tours = 0;
    do {
      const params = { q: `'${echapper(documents.id)}' in parents and trashed=false`, fields: 'nextPageToken,files(id,name,mimeType)', pageSize: '1000', spaces: 'drive' };
      if (page) params.pageToken = page;
      const corps = await (await compte.appeler(`${DRIVE}?${new URLSearchParams(params)}`)).json();
      tous.push(...(Array.isArray(corps.files) ? corps.files : []));
      page = corps.nextPageToken || '';
    } while (page && ++tours < 20);
    const noms = tous.map(f => `${String(f.name || 'sans nom')}${f.mimeType === DOSSIER ? ' (dossier)' : ''}`)
      .sort((a, b) => a.localeCompare(b, 'fr', { numeric: true, sensitivity: 'base' }));
    // 11/11/2026 (accord de Max, c109, séance 4, marche 1) : la SORTE de chaque fichier (PDF, image, musique, vidéo,
    // dossier, autre), décidée au seul endroit prévu (types_fichiers.js), pour la mosaïque de la fiche. Noms et types
    // seulement : aucun contenu n'est lu.
    const sorteDe = f => (typeof typesFichiers !== 'undefined' ? typesFichiers.analyser(f).sorte : (f.mimeType === DOSSIER ? 'dossier' : 'autres'));
    // c110 : + l'identifiant Drive (pour ouvrir un PDF ou une image dans la visionneuse ; jamais montré ni gardé).
    const fichiers = tous.map(f => ({ id: String(f.id || ''), nom: String(f.name || 'sans nom'), sorte: sorteDe(f) }))
      .sort((a, b) => a.nom.localeCompare(b.nom, 'fr', { numeric: true, sensitivity: 'base' }));
    return { total: noms.length, noms: noms.slice(0, Math.max(1, max)), fichiers: fichiers.slice(0, Math.max(1, max)) };
  }

  // 10/11/2026 (c89) : les chantiers qui ont déjà un dossier (LECTURE SEULE) : Map CH-xxx → { id (du dossier), nom }.
  async function dossiersExistants(compte) {
    const racines = await parMarque(compte, MARQUES.racine, '1', DOSSIER);
    const existants = new Map();
    if (racines.length !== 1) return existants;
    for (const f of await lister(compte, `'${echapper(racines[0].id)}' in parents and mimeType='${DOSSIER}' and trashed=false`)) {
      const id = f.appProperties && f.appProperties[MARQUES.chantier];
      if (identifiantValide(id) && !existants.has(id)) existants.set(id, { id: f.id, nom: f.name });
    }
    return existants;
  }
  // 12/11/2026 (c152, C1 de la « carte complète ») : copie SUR LE TÉLÉPHONE de l'identifiant Drive de chaque dossier de
  // chantier (CH-xxx → identifiant), pour le lien « Dossier » de la carte. Écrite à chaque lecture des dossiers (écran des
  // chantiers, « Tout synchroniser ») ; une lecture vide ou ratée ne l'efface pas. Jamais envoyée, jamais à l'IA.
  const CLE_IDS = 'cap_chantiers_dossiers_ids_v1';
  function garderIds(stockage, existants) {
    if (!stockage || !existants || typeof existants.forEach !== 'function') return false;
    const ids = {};
    existants.forEach((d, code) => { if (identifiantValide(code) && d && d.id) ids[code] = String(d.id); });
    if (!Object.keys(ids).length) return false;
    try { stockage.setItem(CLE_IDS, JSON.stringify(ids)); return true; } catch (erreur) { return false; }
  }
  function lireIds(stockage) {
    try { const ids = JSON.parse(stockage && stockage.getItem(CLE_IDS)); return ids && typeof ids === 'object' ? ids : {}; } catch (erreur) { return {}; }
  }
  // Adresse du dossier dans Google Drive (ouverte hors de Cap ; lecture seule).
  const adresseDossier = idDossier => `https://drive.google.com/drive/folders/${encodeURIComponent(idDossier)}`;

  return { CLE_IDS, garderIds, lireIds, adresseDossier, NOM_RACINE, NOM_JOURNAL, NOM_DOCUMENTS, MARQUES, DEBUT_LIGNE, nomDossier, texteLigne, texteNote, preparer, creer, planMiseANiveau, appliquerMiseANiveau, ajouterNote, lireDernieresLignes, listerDocuments, dossiersExistants, adresseDossier };
})();
