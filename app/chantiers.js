'use strict';

// 09/11/2026 (accord de Max, CHANTIERS, séance 1 sur 7) : lecture SEULE du tableur « Liste des chantiers » (Drive de Max,
// dossier « Cerveau de Cap »). Aucune écriture, aucune suppression, aucun renommage : ce fichier n'envoie que des lectures.
// Deux chemins, sans nouvelle autorisation Google et sans aucun identifiant de fichier écrit dans le code :
//  1. le tableur choisi une fois avec le sélecteur de Cap (droit drive.file du compte personnel ; la fenêtre de Google ne
//     s'ouvre que dans Chrome, puis l'appli Android le retrouve dans le Drive, comme les autres fichiers choisis) ;
//  2. sinon, le tableur partagé par Max avec le compte Cap en lecture seule (droit drive.readonly), retrouvé par son nom,
//     comme « Commandes vocales ».
// Une copie réduite reste sur le téléphone : l'écran « Chantiers » s'affiche aussi sans réseau.
// Les lignes d'exemple (nom commençant par « EXEMPLE FICTIF ») sont masquées. Le voyant est LU (colonne « Voyant ») ;
// le calcul du voyant viendra à la séance 2. Rien ne va à l'IA.
const chantiers = (() => {
  const NOM_TABLEUR = 'Liste des chantiers';
  const CLE_COPIE = 'cap_chantiers_copie_v1';
  const ROLE = 'chantiers';
  const ORDRE_VOYANT = { rouge: 0, orange: 1, vert: 2 };
  const plier = texte => String(texte || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
  const estExemple = nom => /^exemple fictif\b/.test(plier(nom));

  // Colonnes retrouvées par leur TITRE (première ligne), quel que soit leur ordre.
  const TITRES = { nom: 'nom du chantier', famille: 'famille', type: 'type', voyant: 'voyant', statut: 'statut',
    id: 'identifiant', parent: 'chantier parent', dateLimite: 'date limite', prochaine: 'prochaine action',
    // 10/11/2026 (séance 2) : deux colonnes de dates de plus, pour le voyant calculé.
    dateRetour: 'date de retour', dateProchaine: 'date de la prochaine action',
    // 10/11/2026 (c94) : le « Prompt » écrit par Max (LU seulement : jamais modifié, jamais envoyé à l'IA ici).
    prompt: 'prompt' };
  function colonnes(entete) {
    const titres = (entete || []).map(plier);
    const col = {};
    for (const [cle, titre] of Object.entries(TITRES)) col[cle] = titres.indexOf(titre);
    return col;
  }

  // lignes : le tableau lu (la première ligne = les titres). Rend { chantiers, exemples, manquantes }.
  function analyser(lignes) {
    const col = colonnes((lignes || [])[0]);
    // 10/11/2026 (séance 2) : les trois colonnes de dates du voyant calculé sont signalées si leur titre est introuvable.
    const manquantes = ['nom', 'voyant', 'statut', 'id', 'parent', 'dateLimite', 'dateProchaine', 'dateRetour'].filter(c => col[c] < 0).map(c => TITRES[c]);
    if (col.nom < 0) return { chantiers: [], exemples: 0, manquantes };
    const cellule = (ligne, c) => (c >= 0 ? String(ligne[c] || '').trim() : '');
    const liste = [];
    let exemples = 0;
    for (const ligne of (lignes || []).slice(1)) {
      const nom = cellule(ligne, col.nom);
      if (!nom) continue;
      if (estExemple(nom)) { exemples++; continue; }
      liste.push({ id: cellule(ligne, col.id), nom, famille: cellule(ligne, col.famille), type: cellule(ligne, col.type),
        voyant: plier(cellule(ligne, col.voyant)), statut: cellule(ligne, col.statut), parent: cellule(ligne, col.parent),
        dateLimite: cellule(ligne, col.dateLimite), prochaine: cellule(ligne, col.prochaine),
        dateRetour: cellule(ligne, col.dateRetour), dateProchaine: cellule(ligne, col.dateProchaine),
        prompt: col.prompt >= 0 ? String(ligne[col.prompt] || '').trim() : '' }); // c94 : retours à la ligne gardés
    }
    return { chantiers: liste, exemples, manquantes };
  }

  // Ordre de l'écran : voyant (rouge, orange, vert, puis sans voyant), puis nom. Chaque sous-chantier vient juste sous son
  // parent (colonne « Chantier parent » : l'identifiant du parent, ou son nom), un cran en retrait. Un parent introuvable :
  // le sous-chantier est rangé avec les autres. Profondeur limitée (3 crans) : jamais de boucle.
  // 10/11/2026 (décision de Max, ligne 53) : pour le TRI, un parent prend le pire voyant entre le sien et ceux de ses
  // sous-chantiers (à tous les crans) : un sous-chantier rouge fait remonter son parent avec les rouges. Le voyant AFFICHÉ
  // reste celui de la Liste (rien n'est changé dans les données). Avant : le parent était trié sur son seul voyant.
  // 10/11/2026 (décision de Max) : à l'intérieur de chaque couleur, « en cours », puis sans statut (ou statut inconnu), puis
  // « en veille » ; tous les « archivé » tout en bas, après toutes les couleurs (un sous-chantier archivé ne fait pas remonter
  // son parent). Avant : couleur, puis nom seulement.
  function rangStatut(c) {
    const p = plier(c.statut);
    if (p.startsWith('archiv')) return 9;
    if (p === 'en cours') return 0;
    if (p === 'en veille') return 2;
    return 1;
  }
  function trier(liste) {
    // 10/11/2026 (séance 2) : si le voyant a été calculé (evaluer), le tri suit la plus grave des deux couleurs.
    const voyantDe = c => (c.voyantTri !== undefined ? c.voyantTri : c.voyant);
    const rang = c => (Object.hasOwn(ORDRE_VOYANT, voyantDe(c)) ? ORDRE_VOYANT[voyantDe(c)] : 3);
    const archive = c => (rangStatut(c) === 9 ? 1 : 0);
    const pire = new Map();
    const rangTri = (c, chemin = new Set()) => {
      if (pire.has(c)) return pire.get(c);
      if (chemin.has(c)) return rang(c); // boucle de parents : on s'arrête
      chemin.add(c);
      let r = rang(c);
      for (const e of enfants.get(c) || []) if (!archive(e)) r = Math.min(r, rangTri(e, chemin));
      chemin.delete(c);
      pire.set(c, r);
      return r;
    };
    const comparer = (a, b) => archive(a) - archive(b) || rangTri(a) - rangTri(b) || rangStatut(a) - rangStatut(b)
      || a.nom.localeCompare(b.nom, 'fr', { sensitivity: 'base' });
    const parCle = new Map();
    for (const c of liste) { if (c.id) parCle.set(plier(c.id), c); parCle.set(plier(c.nom), c); }
    const parentDe = c => { const p = c.parent ? parCle.get(plier(c.parent)) : null; return p && p !== c ? p : null; };
    const enfants = new Map();
    const racines = [];
    for (const c of liste) {
      const p = parentDe(c);
      if (p) { if (!enfants.has(p)) enfants.set(p, []); enfants.get(p).push(c); } else racines.push(c);
    }
    const sortie = [];
    const vus = new Set();
    const poser = (c, niveau) => {
      if (vus.has(c)) return;
      vus.add(c);
      sortie.push({ ...c, niveau });
      for (const e of (enfants.get(c) || []).sort(comparer)) poser(e, Math.min(niveau + 1, 3));
    };
    for (const c of racines.sort(comparer)) poser(c, 0);
    for (const c of liste) poser(c, 0); // ce qui reste (boucle de parents) : rangé en tête de liste, jamais perdu
    return sortie;
  }

  // ----- 10/11/2026 (accord de Max, séance 2 sur 7) : VOYANT CALCULÉ. Les règles sont dans regles_voyant.js (réglages
  // seulement) ; ici, seulement la façon de les appliquer. Rien n'est écrit dans la Liste : le résultat est montré à côté.
  const MOIS = { janv: 1, janvier: 1, fevr: 2, fev: 2, fevrier: 2, mars: 3, avr: 4, avril: 4, mai: 5, juin: 6, juil: 7, juillet: 7,
    aout: 8, sept: 9, septembre: 9, oct: 10, octobre: 10, nov: 11, novembre: 11, dec: 12, decembre: 12 };
  // Une date écrite dans la Liste (export du tableur : texte). Rend { vide } ou { date } (minuit, heure du téléphone) ou
  // { illisible }. Formats compris : 10/11/2026, 10/11/26, 10-11-2026, 10.11.2026 (jour d'abord, comme en France),
  // 2026-11-10, « 10 novembre 2026 », « 10 nov. 2026 » ; une heure après la date est ignorée. Jamais deviné : une date
  // impossible (31/02) ou un autre texte = illisible.
  function lireDate(texte) {
    const t = String(texte || '').trim();
    if (!t) return { vide: true };
    let j, m, a;
    let x = /^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4}|\d{2})(?:[\sT].*)?$/.exec(t);
    if (x) { j = +x[1]; m = +x[2]; a = +x[3] + (x[3].length === 2 ? 2000 : 0); }
    if (!x && (x = /^(\d{4})-(\d{1,2})-(\d{1,2})(?:[\sT].*)?$/.exec(t))) { a = +x[1]; m = +x[2]; j = +x[3]; }
    // « 10 novembre 2026 », « 1er déc. 2026 » : accents et majuscules retirés avant de lire le mois.
    const sansAccents = t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    if (!x && (x = /^(\d{1,2})(?:er)?\s+([a-z]+)\.?\s+(\d{4})(?:\s.*)?$/.exec(sansAccents))) {
      j = +x[1]; m = MOIS[x[2]]; a = +x[3];
    }
    if (!x || !m) return { illisible: true };
    const date = new Date(a, m - 1, j);
    if (date.getFullYear() !== a || date.getMonth() !== m - 1 || date.getDate() !== j) return { illisible: true };
    return { date };
  }
  const debutDuJour = maintenant => { const d = new Date(maintenant); return new Date(d.getFullYear(), d.getMonth(), d.getDate()); };
  const joursEntre = (aujourdhui, date) => Math.round((date - aujourdhui) / 86400000);
  const statutEst = (statut, liste) => { const p = plier(statut); return (liste || []).some(s => p.startsWith(plier(s))); };
  const rangVoyant = v => (Object.hasOwn(ORDRE_VOYANT, v) ? ORDRE_VOYANT[v] : 3);
  // La plus grave de deux couleurs (rouge, puis orange, puis vert) ; '' si aucune n'est une couleur.
  const plusGrave = (a, b) => { const r = Math.min(rangVoyant(a), rangVoyant(b)); return r === 3 ? '' : (rangVoyant(a) === r ? a : b); };
  const reglesParDefaut = () => (typeof reglesVoyant !== 'undefined' ? reglesVoyant : { regles: [], statutsSansCouleur: [], statutsEnVeille: [], couleurParDefaut: '' });

  // Un chantier : { couleur (rouge, orange, vert, ou '' = pas de couleur calculée), illisible (au moins une date pas lue) }.
  function calculer(c, maintenant = Date.now(), regles = reglesParDefaut()) {
    const aujourdhui = debutDuJour(maintenant);
    const colonnesDates = [...new Set(regles.regles.map(r => r.colonne))];
    const dates = {};
    let illisible = false;
    for (const col of colonnesDates) { dates[col] = lireDate(c[col]); if (dates[col].illisible) illisible = true; }
    if (statutEst(c.statut, regles.statutsSansCouleur)) return { couleur: '', illisible };
    const enVeille = statutEst(c.statut, regles.statutsEnVeille);
    let couleur = '';
    for (const r of regles.regles) {
      if (r.statut ? !statutEst(c.statut, [r.statut]) : enVeille) continue;
      const d = dates[r.colonne];
      if (!d || !d.date) continue; // vide ou illisible : ne change pas la couleur
      const n = joursEntre(aujourdhui, d.date);
      const oui = (r.quand === 'passee' && n < 0) || (r.quand === 'arrivee' && n <= 0)
        || (r.quand === 'dans_les_jours' && n >= 0 && n <= Number(r.jours || 0));
      if (oui) couleur = plusGrave(couleur, r.couleur);
    }
    if (!couleur && !enVeille) couleur = regles.couleurParDefaut || '';
    return { couleur, illisible };
  }

  // Toute la liste : chaque chantier reçoit voyantEcrit (la Liste), voyantCalcule, voyantTri (la plus grave des deux) et
  // dateIllisible ; plus les compteurs (sans aucun nom).
  function evaluer(liste, maintenant = Date.now(), regles = reglesParDefaut()) {
    const compteurs = { rouge: 0, orange: 0, vert: 0, sansCouleur: 0, illisibles: 0 };
    const chantiersEvalues = (liste || []).map(c => {
      const r = calculer(c, maintenant, regles);
      if (r.couleur) compteurs[r.couleur]++; else compteurs.sansCouleur++;
      if (r.illisible) compteurs.illisibles++;
      return { ...c, voyantEcrit: c.voyant, voyantCalcule: r.couleur, voyantTri: plusGrave(r.couleur, c.voyant), dateIllisible: r.illisible };
    });
    return { chantiers: chantiersEvalues, compteurs };
  }

  function garder(stockage, analyse, source, maintenant = Date.now()) {
    const copie = { lu_le: new Date(maintenant).toISOString(), source, chantiers: analyse.chantiers, exemples: analyse.exemples, manquantes: analyse.manquantes };
    try { stockage.setItem(CLE_COPIE, JSON.stringify(copie)); } catch (erreur) { /* mémoire pleine : la lecture sert quand même */ }
    return copie;
  }
  function copie(stockage = (typeof localStorage !== 'undefined' ? localStorage : null)) {
    try { const c = JSON.parse(stockage.getItem(CLE_COPIE)); return c && Array.isArray(c.chantiers) ? c : null; } catch (erreur) { return null; }
  }

  // Lecture : d'abord le tableur choisi avec le sélecteur (compte personnel), sinon le tableur partagé avec le compte Cap.
  async function lire({
    personnel = (typeof googleConnexion !== 'undefined' ? googleConnexion : null),
    selecteur = (typeof googlePicker !== 'undefined' ? googlePicker : null),
    compteCap = (typeof googleCompteRelations !== 'undefined' ? googleCompteRelations : null),
    lireCsv = texte => commandesVocales.lireCsv(texte),
    stockage = (typeof localStorage !== 'undefined' ? localStorage : null),
    enLigne = () => (typeof navigator === 'undefined' || navigator.onLine !== false),
    maintenant = Date.now()
  } = {}) {
    if (!enLigne()) throw new Error('Pas de réseau : je ne peux pas relire la Liste des chantiers.');
    const exporter = async (appeler, id) => (await appeler(`https://www.googleapis.com/drive/v3/files/${encodeURIComponent(id)}/export?mimeType=${encodeURIComponent('text/csv')}`)).text();
    // 1. Choisi avec le sélecteur (et retrouvé dans le Drive sur l'appli Android).
    if (personnel && selecteur && typeof personnel.connecte === 'function' && personnel.connecte()) {
      let choisi = null;
      try { choisi = selecteur.dossierChoisi(ROLE) || await selecteur.retrouverDepuisDrive(ROLE); } catch (erreur) { choisi = null; }
      if (choisi && choisi.id) return garder(stockage, analyser(lireCsv(await exporter(url => personnel.appeler(url), choisi.id))), 'selecteur', maintenant);
    }
    // 2. Partagé avec le compte Cap (lecture seule), retrouvé par son nom.
    if (compteCap && typeof compteCap.connecte === 'function' && compteCap.connecte()) {
      const q = `name='${NOM_TABLEUR}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false`;
      const liste = await (await compteCap.appeler(`https://www.googleapis.com/drive/v3/files?${new URLSearchParams({ q, fields: 'files(id)', pageSize: '10' })}`)).json();
      const trouves = Array.isArray(liste.files) ? liste.files : [];
      if (trouves.length > 1) throw new Error(`Le compte Cap voit ${trouves.length} tableurs « ${NOM_TABLEUR} » : garde-en un seul partagé avec lui.`);
      if (trouves.length === 1) return garder(stockage, analyser(lireCsv(await exporter(url => compteCap.appeler(url), trouves[0].id))), 'compte_cap', maintenant);
    } else if (compteCap && typeof compteCap.connecte === 'function') {
      // 10/11/2026 (demande de Max) : connexion du compte Cap absente ou expirée (au bout d'environ 1 h) : dire le bon geste.
      // Avant : le message disait « partage-la avec le compte Cap », alors que la Liste est peut-être déjà partagée.
      throw new Error(`Le compte Cap n’est pas connecté (ou la connexion a expiré, au bout d’environ 1 h) : touche « Autoriser la lecture du compte Cap », puis rouvre les chantiers.`);
    }
    throw new Error(`Je ne peux pas encore lire la « ${NOM_TABLEUR} » : partage-la avec le compte Cap (lecture seule), ou choisis-la avec le sélecteur de Cap dans Chrome.`);
  }

  // ==============================================================
  // 11/11/2026 (accord de Max, c127, SÉANCE 6a) : l'onglet « Prêt » du tableur « À faire », en LECTURE SEULE, par le
  // compte Cap (droit drive.readonly déjà donné ; le tableur doit être partagé avec lui en lecture). Cap ne coche rien,
  // n'écrit rien dans « À faire », ne garde rien sur le téléphone (en mémoire seulement). Le tableur est retrouvé par
  // son NOM (aucun identifiant dans le code). Le verrou du compte Cap ne permet que les lectures « drive/v3 » : l'onglet
  // est donc lu dans l'export du tableur (fichier .xlsx, lu sur le téléphone), pas par l'API Sheets (refusée).
  // ==============================================================
  const NOM_A_FAIRE = 'À faire';
  const ONGLET_PRET = 'Prêt';
  const XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

  // Lecture d'un .xlsx (un « zip » de fichiers XML) : seulement ce qu'il faut pour lire les cellules d'un onglet.
  async function lireZip(octets) {
    const v = new DataView(octets.buffer, octets.byteOffset, octets.byteLength);
    let fin = -1;
    for (let i = octets.length - 22; i >= Math.max(0, octets.length - 65558); i--) if (v.getUint32(i, true) === 0x06054b50) { fin = i; break; }
    if (fin < 0) throw new Error('Fichier « À faire » illisible (format inattendu).');
    const nombre = v.getUint16(fin + 10, true);
    let p = v.getUint32(fin + 16, true);
    const fichiers = new Map();
    for (let k = 0; k < nombre; k++) {
      if (v.getUint32(p, true) !== 0x02014b50) throw new Error('Fichier « À faire » illisible (sommaire abîmé).');
      const methode = v.getUint16(p + 10, true), taille = v.getUint32(p + 20, true);
      const lnom = v.getUint16(p + 28, true), lext = v.getUint16(p + 30, true), lcom = v.getUint16(p + 32, true);
      const local = v.getUint32(p + 42, true);
      const nom = new TextDecoder().decode(octets.subarray(p + 46, p + 46 + lnom));
      fichiers.set(nom, { methode, taille, local });
      p += 46 + lnom + lext + lcom;
    }
    return async nom => {
      const f = fichiers.get(nom);
      if (!f) return null;
      const debut = f.local + 30 + v.getUint16(f.local + 26, true) + v.getUint16(f.local + 28, true);
      const donnees = octets.subarray(debut, debut + f.taille);
      if (f.methode === 0) return new TextDecoder().decode(donnees);
      if (f.methode !== 8) throw new Error('Fichier « À faire » illisible (compression inconnue).');
      const flux = new Blob([donnees]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
      return new TextDecoder().decode(await new Response(flux).arrayBuffer());
    };
  }
  const colonneDe = ref => { const l = /^[A-Z]+/.exec(ref || '') ; let n = 0; for (const ch of (l ? l[0] : 'A')) n = n * 26 + (ch.charCodeAt(0) - 64); return n - 1; };
  // Les lignes (tableaux de textes ou de nombres) de l'onglet nommé `onglet`, ou null s'il n'existe pas.
  async function lireOngletXlsx(octets, onglet) {
    const lire = await lireZip(octets);
    const xml = async nom => { const t = await lire(nom); return t === null ? null : new DOMParser().parseFromString(t, 'application/xml'); };
    const classeur = await xml('xl/workbook.xml');
    const liens = await xml('xl/_rels/workbook.xml.rels');
    if (!classeur || !liens) throw new Error('Fichier « À faire » illisible (classeur absent).');
    const feuille = [...classeur.getElementsByTagName('sheet')].find(f => plier(f.getAttribute('name')) === plier(onglet));
    if (!feuille) return null;
    const rid = feuille.getAttribute('r:id') || feuille.getAttributeNS('http://schemas.openxmlformats.org/officeDocument/2006/relationships', 'id');
    const lien = [...liens.getElementsByTagName('Relationship')].find(r => r.getAttribute('Id') === rid);
    if (!lien) throw new Error('Fichier « À faire » illisible (onglet introuvable).');
    const cible = lien.getAttribute('Target').replace(/^\/?(xl\/)?/, '');
    const partages = await xml('xl/sharedStrings.xml');
    const textes = partages ? [...partages.getElementsByTagName('si')].map(si => [...si.getElementsByTagName('t')].map(t => t.textContent).join('')) : [];
    const page = await xml(`xl/${cible}`);
    if (!page) throw new Error('Fichier « À faire » illisible (onglet vide).');
    const lignes = [];
    for (const row of page.getElementsByTagName('row')) {
      const ligne = [];
      for (const c of row.getElementsByTagName('c')) {
        const type = c.getAttribute('t');
        const val = c.getElementsByTagName('v')[0];
        let x = '';
        if (type === 's') x = textes[Number(val && val.textContent)] || '';
        else if (type === 'inlineStr') x = [...c.getElementsByTagName('t')].map(t => t.textContent).join('');
        else if (type === 'b') x = val && val.textContent === '1';
        else if (type === 'str' || type === 'e') x = val ? val.textContent : '';
        else x = val ? Number(val.textContent) : '';
        ligne[colonneDe(c.getAttribute('r'))] = x;
      }
      const n = Number(row.getAttribute('r')) - 1;
      lignes[Number.isFinite(n) && n >= 0 ? n : lignes.length] = ligne;
    }
    return Array.from(lignes, l => Array.from(l || [], x => (x === undefined ? '' : x)));
  }

  // Une date du tableur (nombre de jours depuis le 30/12/1899, ou texte) en « JJ/MM/AAAA » ; sinon le texte tel quel.
  function texteDate(x) {
    if (typeof x === 'number' && x > 0) { const d = new Date(Date.UTC(1899, 11, 30) + Math.round(x) * 86400000); return `${String(d.getUTCDate()).padStart(2, '0')}/${String(d.getUTCMonth() + 1).padStart(2, '0')}/${d.getUTCFullYear()}`; }
    return String(x || '').trim();
  }
  const estFaite = x => x === true || /^(vrai|true|oui|x|fait|faite|termine|terminee|1|✓|✔)$/.test(plier(x) || String(x || '').trim());
  // Les tâches de « Prêt », rangées par chantier (numéro CH-xxx trouvé dans la colonne « Chantier »).
  function analyserPret(lignes) {
    const titres = (lignes[0] || []).map(t => plier(t));
    const col = nom => titres.findIndex(t => t === nom || t.startsWith(`${nom} `));
    const c = { faite: col('terminee'), tache: col('tache'), priorite: col('priorite'), echeance: col('date d echeance'), chantier: col('chantier') };
    if (c.tache < 0 || c.chantier < 0) throw new Error('Onglet « Prêt » : colonnes « Tâche » ou « Chantier » introuvables.');
    const parChantier = new Map();
    let sansChantier = 0;
    for (const l of lignes.slice(1)) {
      if (!l || !String(l[c.tache] || '').trim()) continue;
      const m = /CH-\d{1,6}/i.exec(String(l[c.chantier] || ''));
      if (!m) { sansChantier++; continue; }
      const id = m[0].toUpperCase();
      if (!parChantier.has(id)) parChantier.set(id, { enCours: [], terminees: 0 });
      const e = parChantier.get(id);
      if (c.faite >= 0 && estFaite(l[c.faite])) { e.terminees++; continue; }
      e.enCours.push({ tache: String(l[c.tache]).trim(), priorite: c.priorite >= 0 ? String(l[c.priorite] || '').trim() : '', echeance: c.echeance >= 0 ? texteDate(l[c.echeance]) : '' });
    }
    return { parChantier, sansChantier, lignes: Math.max(0, lignes.length - 1) };
  }
  // Lecture par le compte Cap (lecture seule). Rien n'est gardé sur le téléphone.
  async function lirePret({ compteCap = (typeof googleCompteRelations !== 'undefined' ? googleCompteRelations : null),
    enLigne = () => (typeof navigator === 'undefined' || navigator.onLine !== false) } = {}) {
    if (!enLigne()) throw new Error('Pas de réseau : je ne peux pas lire l’onglet « Prêt ».');
    if (!compteCap || typeof compteCap.connecte !== 'function' || !compteCap.connecte()) throw new Error('Le compte Cap n’est pas connecté (ou la connexion a expiré) : touche « Tout synchroniser ».');
    const q = `name='${NOM_A_FAIRE}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false`;
    const liste = await (await compteCap.appeler(`https://www.googleapis.com/drive/v3/files?${new URLSearchParams({ q, fields: 'files(id)', pageSize: '10' })}`)).json();
    const trouves = Array.isArray(liste.files) ? liste.files : [];
    if (trouves.length > 1) throw new Error(`Le compte Cap voit ${trouves.length} tableurs « ${NOM_A_FAIRE} » : garde-en un seul partagé avec lui.`);
    if (!trouves.length) throw new Error(`Je ne vois pas le tableur « ${NOM_A_FAIRE} » : partage-le avec le compte Cap (lecture seule).`);
    const reponse = await compteCap.appeler(`https://www.googleapis.com/drive/v3/files/${encodeURIComponent(trouves[0].id)}/export?mimeType=${encodeURIComponent(XLSX)}`);
    const lignes = await lireOngletXlsx(new Uint8Array(await reponse.arrayBuffer()), ONGLET_PRET);
    if (!lignes) throw new Error(`Le tableur « ${NOM_A_FAIRE} » n’a pas d’onglet « ${ONGLET_PRET} ».`);
    return analyserPret(lignes);
  }

  return { NOM_TABLEUR, CLE_COPIE, ROLE, plier, estExemple, colonnes, analyser, rangStatut, trier, lireDate, calculer, evaluer, garder, copie, lire,
    NOM_A_FAIRE, ONGLET_PRET, lireOngletXlsx, analyserPret, lirePret, texteDate }; // c127
})();
