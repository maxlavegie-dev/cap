'use strict';

// Classement des scans, étape 1 (05/11/2026) : lecture du tableur « Classement documents
// administratifs » et de la STRUCTURE du Doc « Architecture officielle des archives », sans DOM.
// Ces deux fichiers sont choisis une fois par Max (sélecteur Google, droit drive.file) et lus à
// chaque besoin, sur le téléphone. Ils contiennent de vrais noms : rien n'en est copié ailleurs
// (ni journal, ni console). Ce module ne crée, ne nomme et ne range RIEN : il lit et vérifie.
const classement = (() => {
  const separateurChemin = /\s+\/\s+/;

  // Comparaison sans accents ni majuscules ; le nom exact du Doc est toujours gardé à part.
  function cle(texte) {
    return String(texte || '').normalize('NFD').replace(/[̀-ͯ]/g, '')
      .toLowerCase().replace(/\s+/g, ' ').trim();
  }

  // « Prenom_fictif (aucun sous-dossier pour l'instant) » → « Prenom_fictif ».
  function nomDossier(texte) {
    return String(texte || '').replace(/\u000b/g, ' ').split('(')[0].replace(/\s+/g, ' ').trim();
  }

  // Sections jamais lues comme des dossiers : les règles pour Cap, et les archives faites à la
  // main (« 00_A_CLASSER (le premier) »), que Cap ne crée jamais.
  function sectionIgnoree(titre) {
    const texte = cle(titre);
    return texte.startsWith('regles pour cap') || texte.startsWith('00_a_classer');
  }

  // Le Doc est lu par le Drive, exporté en page HTML (05/11/2026 : le service Google Docs n'est pas
  // utilisé). Google y écrit chaque niveau de puce comme une liste à part, dont la classe finit par
  // « -N » (N = retrait, 0 pour le premier niveau) ; les titres sont h1…h6, le titre du Doc p.title.
  function paragraphesDepuisHtml(html) {
    const page = new DOMParser().parseFromString(String(html || ''), 'text/html');
    const paragraphes = [];
    for (const element of page.body ? page.body.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li') : []) {
      const balise = element.tagName.toLowerCase();
      if (balise === 'p' && element.closest('li')) continue;
      const texte = element.textContent.replace(/\u00a0/g, ' ');
      if (balise === 'li') {
        const liste = element.closest('ul,ol');
        const retrait = /(?:^|\s)lst-[^\s]*-(\d+)(?:\s|$)/.exec(liste ? liste.className : '');
        paragraphes.push({ style: 'NORMAL_TEXT', texte, niveau: retrait ? Number(retrait[1]) : 0 });
      } else if (/^h\d$/.test(balise)) {
        paragraphes.push({ style: `HEADING_${balise[1]}`, texte });
      } else {
        const titre = element.classList.contains('title') || element.classList.contains('subtitle');
        paragraphes.push({ style: titre ? 'TITLE' : 'NORMAL_TEXT', texte });
      }
    }
    return paragraphes;
  }

  // Structure du Doc → arbre : un titre de niveau 2 = un dossier principal ; dessous, une puce par
  // sous-dossier, un retrait par niveau. Tout le reste est ignoré. Reçoit la page HTML exportée.
  function analyserArchitecture(html) {
    const racine = { nom: '', enfants: [] };
    const doutes = [];
    let principal = null;
    let pile = [];
    let ignorees = 0;
    for (const { style, texte, niveau } of paragraphesDepuisHtml(html)) {
      if (/^(HEADING_\d|TITLE)$/.test(style)) {
        principal = null;
        pile = [];
        if (style !== 'HEADING_2') continue;
        if (sectionIgnoree(texte)) { ignorees++; continue; }
        const nom = nomDossier(texte);
        if (!nom) continue;
        principal = ajouterEnfant(racine, nom, doutes);
        continue;
      }
      if (niveau === undefined || !principal) continue;
      const nom = nomDossier(texte);
      if (!nom) continue;
      const parent = niveau === 0 ? principal : pile[niveau - 1];
      if (!parent) {
        doutes.push({ type: 'niveau_saute', nom });
        continue;
      }
      pile[niveau] = ajouterEnfant(parent, nom, doutes);
      pile.length = niveau + 1;
    }
    return { racine, doutes, sections_ignorees: ignorees };
  }

  // Deux noms identiques sans accents ni majuscules au même endroit : doute, jamais de choix.
  function ajouterEnfant(parent, nom, doutes) {
    const existant = parent.enfants.find(enfant => cle(enfant.nom) === cle(nom));
    if (existant) {
      existant.double = true;
      doutes.push({ type: 'double', nom });
      return existant;
    }
    const enfant = { nom, enfants: [] };
    parent.enfants.push(enfant);
    return enfant;
  }

  function compterDossiers(noeud) {
    return noeud.enfants.reduce((total, enfant) => total + 1 + compterDossiers(enfant), 0);
  }

  // Valeurs de la première feuille → lignes du tableur. Première ligne = en-têtes ; colonnes dans
  // l'ordre : Mot-clé repéré, Organisme, Chemin de destination, Type de document, Modèle de titre.
  function analyserTableur(valeurs) {
    const lignes = [];
    const ignorees = [];
    (valeurs || []).slice(1).forEach((brute, indice) => {
      const [mot_cle, organisme, chemin, type, modele] = Array.from({ length: 5 },
        (_, colonne) => String(brute?.[colonne] ?? '').trim());
      const numero = indice + 2;
      if (!mot_cle && !chemin && !modele) return;
      if (!mot_cle || !chemin || !modele) { ignorees.push({ numero, raison: 'incomplete' }); return; }
      const morceaux = chemin.split(separateurChemin).map(morceau => morceau.trim()).filter(Boolean);
      lignes.push({ numero, mot_cle, organisme, chemin: morceaux, type, modele });
    });
    return { lignes, ignorees };
  }

  // Le chemin du tableur existe-t-il dans le Doc ? Renvoie les noms EXACTS du Doc (accents
  // compris) pour chaque niveau, ou la raison du refus. Dans le doute, on refuse.
  function verifierChemin(morceaux, architecture) {
    let noeud = architecture.racine;
    const noms = [];
    for (const morceau of morceaux) {
      const trouves = noeud.enfants.filter(enfant => cle(enfant.nom) === cle(morceau));
      if (!trouves.length) return { ok: false, raison: 'absent_du_doc', niveau: noms.length };
      if (trouves.length > 1 || trouves[0].double) return { ok: false, raison: 'double_dans_le_doc', niveau: noms.length };
      noeud = trouves[0];
      noms.push(noeud.nom);
    }
    return noms.length ? { ok: true, noms } : { ok: false, raison: 'vide', niveau: 0 };
  }

  // Résumé de contrôle : des NOMBRES seulement (jamais un nom du Doc ni du tableur).
  function resumer(tableur, architecture) {
    const verifications = tableur.lignes.map(ligne => verifierChemin(ligne.chemin, architecture));
    return {
      lignes: tableur.lignes.length,
      lignes_ignorees: tableur.ignorees.length,
      dossiers_principaux: architecture.racine.enfants.length,
      dossiers: compterDossiers(architecture.racine),
      sections_ignorees: architecture.sections_ignorees,
      doutes_doc: architecture.doutes.length,
      chemins_trouves: verifications.filter(v => v.ok).length,
      chemins_absents: verifications.filter(v => !v.ok && v.raison === 'absent_du_doc').length,
      chemins_douteux: verifications.filter(v => !v.ok && v.raison !== 'absent_du_doc').length
    };
  }

  function texteResume(resume) {
    return [
      `Tableur : ${resume.lignes} ligne(s) lue(s)${resume.lignes_ignorees ? `, ${resume.lignes_ignorees} incomplète(s) ignorée(s)` : ''}.`,
      `Doc : ${resume.dossiers_principaux} dossier(s) principal(aux), ${resume.dossiers} dossier(s) en tout.`,
      `Parties écartées (règles pour Cap, 00_A_CLASSER le premier) : ${resume.sections_ignorees}.`,
      `Chemins du tableur trouvés dans le Doc : ${resume.chemins_trouves} sur ${resume.lignes}`
        + ` (absents : ${resume.chemins_absents}, douteux : ${resume.chemins_douteux}).`,
      resume.doutes_doc ? `Doutes dans le Doc (noms en double, niveaux sautés) : ${resume.doutes_doc}.` : 'Aucun doute dans le Doc.'
    ].join('\n');
  }

  // ----- Lecture dans le Drive (fichiers choisis par Max) -----

  async function lireJson(url) {
    return (await googleConnexion.appeler(url)).json();
  }

  async function lireTableur(id) {
    const base = `https://sheets.googleapis.com/v4/spreadsheets/${encodeURIComponent(id)}`;
    const infos = await lireJson(`${base}?fields=sheets.properties.title`);
    const titre = infos.sheets?.[0]?.properties?.title;
    if (!titre) throw new Error('Le tableur de classement n’a aucune feuille lisible.');
    // Première feuille, quel que soit son nom.
    const plage = `'${titre.replace(/'/g, "''")}'!A:E`;
    const donnees = await lireJson(`${base}/values/${encodeURIComponent(plage)}?valueRenderOption=FORMATTED_VALUE`);
    return analyserTableur(donnees.values || []);
  }

  async function lireArchitecture(id) {
    const reponse = await googleConnexion.appeler(
      `https://www.googleapis.com/drive/v3/files/${encodeURIComponent(id)}/export?mimeType=${encodeURIComponent('text/html')}`);
    return analyserArchitecture(await reponse.text());
  }

  async function fichierChoisi(role) {
    return googlePicker.dossierChoisi(role) || await googlePicker.retrouverDepuisDrive(role);
  }

  // Lit les deux fichiers, à chaque appel (jamais de copie gardée).
  async function lire() {
    const architecture = await fichierChoisi('architecture');
    const tableur = await fichierChoisi('tableur_classement');
    if (!architecture || !tableur) {
      throw new Error('Choisis d’abord le Doc d’architecture et le tableur de classement dans « Réglages du Drive », '
        + 'avec Cap ouvert dans Chrome.');
    }
    // L'un après l'autre, avec un message par fichier (seulement l'erreur et le code de raison de
    // Google, jamais un nom, un identifiant, la clé ni le jeton).
    let lignes = null;
    let arbre = null;
    const etats = [];
    try { lignes = await lireTableur(tableur.id); etats.push('Tableur : lu.'); } catch (erreur) { etats.push(`Tableur : ${refus(erreur)}`); }
    try { arbre = await lireArchitecture(architecture.id); etats.push('Doc : lu.'); } catch (erreur) { etats.push(`Doc : ${refus(erreur)}`); }
    if (!lignes || !arbre) throw new Error(etats.join('\n'));
    return { tableur: lignes, architecture: arbre, resume: resumer(lignes, arbre), etats };
  }

  // Étape 3 : pour proposer un nom, seul le tableur est lu (à chaque scan, rien gardé).
  async function lireTableurChoisi() {
    const tableur = await fichierChoisi('tableur_classement');
    if (!tableur) throw new Error('Choisis d’abord le tableur de classement dans « Réglages du Drive », avec Cap ouvert dans Chrome.');
    return (await lireTableur(tableur.id)).lignes;
  }

  // 06/11/2026 : tableur « Cap – Mots-clés courts – à valider », choisi une fois par Max. Ses quatre
  // onglets sont lus à chaque scan (rien gardé). Pas encore choisi : null (recherche stricte).
  const ONGLETS_MOTS_COURTS = Object.freeze({ types: 'Types', organismes: 'Organismes', personnes: 'Personnes', courants: 'Mots trop courants' });
  async function lireMotsCourts() {
    const fichier = await fichierChoisi('mots_cles_courts');
    if (!fichier) return null;
    const base = `https://sheets.googleapis.com/v4/spreadsheets/${encodeURIComponent(fichier.id)}/values:batchGet`;
    const plages = Object.values(ONGLETS_MOTS_COURTS).map(titre => `ranges=${encodeURIComponent(`'${titre.replace(/'/g, "''")}'!A:J`)}`);
    const donnees = await lireJson(`${base}?${plages.join('&')}&valueRenderOption=FORMATTED_VALUE`);
    const valeurs = (donnees.valueRanges || []).map(plage => plage.values || []);
    const onglets = Object.fromEntries(Object.keys(ONGLETS_MOTS_COURTS).map((nom, i) => [nom, valeurs[i] || []]));
    return motsCourts.analyser(onglets);
  }

  // 06/11/2026 : Dictionnaire général (choisi une fois par Max), pour reconnaître l'émetteur.
  // Seules les colonnes autorisées par emetteur.js sont DEMANDÉES au Drive (jamais les notes ni les
  // dates de naissance). Gardé EN MÉMOIRE seulement, tant que l'application est ouverte : rien n'est
  // écrit sur le téléphone (ni cache, ni stockage local, ni journal).
  let memoireDictionnaire = null;
  function lettreColonne(index) {
    let n = index + 1;
    let lettres = '';
    while (n) { const r = (n - 1) % 26; lettres = String.fromCharCode(65 + r) + lettres; n = Math.floor((n - 1) / 26); }
    return lettres;
  }
  async function lireDictionnaire() {
    const fichier = await fichierChoisi('dictionnaire');
    if (!fichier) return null;
    if (memoireDictionnaire && memoireDictionnaire.id === fichier.id) return memoireDictionnaire.entrees;
    const base = `https://sheets.googleapis.com/v4/spreadsheets/${encodeURIComponent(fichier.id)}/values:batchGet`;
    const plage = (onglet, morceau) => `ranges=${encodeURIComponent(`'${onglet.replace(/'/g, "''")}'!${morceau}`)}`;
    const entetes = await lireJson(`${base}?${emetteur.ONGLETS.map(o => plage(o, '1:1')).join('&')}`);
    const onglets = {};
    const demandes = [];
    emetteur.ONGLETS.forEach((onglet, i) => {
      const ligne = entetes.valueRanges?.[i]?.values?.[0] || [];
      const colonnes = emetteur.colonnesALire(onglet, ligne);
      onglets[onglet] = { ligne, colonnes };
      for (const c of colonnes) demandes.push({ onglet, c, morceau: `${lettreColonne(c)}:${lettreColonne(c)}` });
    });
    const valeurs = demandes.length
      ? await lireJson(`${base}?${demandes.map(d => plage(d.onglet, d.morceau)).join('&')}&majorDimension=COLUMNS`) : { valueRanges: [] };
    const parOnglet = {};
    demandes.forEach((d, i) => { (parOnglet[d.onglet] ||= []).push(valeurs.valueRanges?.[i]?.values?.[0] || []); });
    const lignes = {};
    for (const onglet of emetteur.ONGLETS) {
      const colonnes = parOnglet[onglet] || [];
      const hauteur = Math.max(0, ...colonnes.map(c => c.length));
      lignes[onglet] = Array.from({ length: hauteur }, (_, r) => colonnes.map(c => c[r] ?? ''));
    }
    memoireDictionnaire = { id: fichier.id, entrees: emetteur.analyser(lignes) };
    return memoireDictionnaire.entrees;
  }

  // 06/11/2026, dossiers « Relations », étape 2 (calcul seulement) : onglet « Dictionnaire » seul,
  // colonnes Prénom, Nom et Type seulement (relations.colonnesALire). Lecture (GET) à chaque calcul,
  // rien gardé ni écrit nulle part. Retour : lignes [en-têtes, …] de ces colonnes, ou null si le
  // Dictionnaire n'est pas encore choisi.
  async function lireDictionnairePersonnes() {
    const fichier = await fichierChoisi('dictionnaire');
    if (!fichier) return null;
    const base = `https://sheets.googleapis.com/v4/spreadsheets/${encodeURIComponent(fichier.id)}/values:batchGet`;
    const plage = morceau => `ranges=${encodeURIComponent(`'${relations.ONGLET}'!${morceau}`)}`;
    const entetes = await lireJson(`${base}?${plage('1:1')}`);
    const colonnes = relations.colonnesALire(entetes.valueRanges?.[0]?.values?.[0] || []);
    if (!colonnes.length) return [[]];
    const valeurs = await lireJson(`${base}?${colonnes.map(c => plage(`${lettreColonne(c)}:${lettreColonne(c)}`)).join('&')}&majorDimension=COLUMNS`);
    const parColonne = colonnes.map((_, i) => valeurs.valueRanges?.[i]?.values?.[0] || []);
    const hauteur = Math.max(0, ...parColonne.map(c => c.length));
    return Array.from({ length: hauteur }, (_, r) => parColonne.map(c => c[r] ?? ''));
  }

  function refus(erreur) {
    if (erreur && erreur.statut) {
      return `refusé (erreur ${erreur.statut}${erreur.raison ? `, raison : ${erreur.raison}` : ''}).`;
    }
    return `pas lu (${erreur && erreur.message ? erreur.message : 'erreur inconnue'}).`;
  }

  return { cle, nomDossier, paragraphesDepuisHtml, analyserArchitecture, analyserTableur, verifierChemin, resumer, texteResume, lire, lireTableurChoisi, lireMotsCourts, lireDictionnaire, lireDictionnairePersonnes };
})();
