'use strict';

// Journaux de chantier (05/11/2026), sans DOM : « Journal Numérisation » et « Journal Général »,
// deux Google Sheets créés par Cap dans App Cap › Journaux (droit drive.file, aucun autre).
// Verrous : Cap AJOUTE seulement des lignes à la fin (jamais de modification ni d'effacement ;
// une correction est une nouvelle ligne datée) ; le texte est écrit tel quel (RAW : jamais
// interprété comme une formule) ; si Google ne répond pas, la ligne attend sur le téléphone et
// ne quitte la file qu'après réussite. Ces journaux restent dans le Drive, jamais dans GitHub.
const journaux = (() => {
  const cleFile = 'cap_journaux_file_v1';
  const drive = 'https://www.googleapis.com/drive/v3/files';
  const sheets = 'https://sheets.googleapis.com/v4/spreadsheets';
  const typeDossier = 'application/vnd.google-apps.folder';
  const typeTableur = 'application/vnd.google-apps.spreadsheet';
  const longueurMax = 1000;
  const definitions = Object.freeze({
    numerisation: { role: 'journal_numerisation', nom: () => REGLAGES_GOOGLE.journaux.numerisation,
      entetes: ['Date', 'Heure', 'Action', 'Résultat', 'Détails'] },
    general: { role: 'journal_general', nom: () => REGLAGES_GOOGLE.journaux.general,
      entetes: ['Date', 'Heure', 'Action', 'Résultat', 'Détails', 'Chantier'] }
  });
  let enCours = null;

  // ----- File d'attente sur le téléphone -----

  function lireFile() {
    try {
      const file = JSON.parse(localStorage.getItem(cleFile) || '[]');
      return Array.isArray(file) ? file : [];
    } catch (erreur) {
      return [];
    }
  }

  function ecrireFile(file) {
    const texte = JSON.stringify(file);
    localStorage.setItem(cleFile, texte);
    if (localStorage.getItem(cleFile) !== texte) throw new Error('La ligne du journal n’a pas pu être gardée sur le téléphone.');
  }

  function horodatage(date = new Date()) {
    const parties = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Paris', year: 'numeric', month: '2-digit',
      day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }).formatToParts(date);
    const v = type => parties.find(partie => partie.type === type).value;
    return { date: `${v('year')}-${v('month')}-${v('day')}`, heure: `${v('hour')}:${v('minute')}:${v('second')}` };
  }

  function texte(valeur) {
    return String(valeur ?? '').replace(/\s+/g, ' ').trim().slice(0, longueurMax);
  }

  // Ajoute une ligne à la file (heure prise MAINTENANT), puis tente l'envoi sans attendre.
  function ajouter(journal, { action, resultat = '', details = '', chantier = '' } = {}) {
    if (!Object.hasOwn(definitions, journal)) throw new Error('Journal inconnu.');
    if (!texte(action)) throw new Error('Une ligne de journal doit dire l’action.');
    const { date, heure } = horodatage();
    const ligne = [date, heure, texte(action), texte(resultat), texte(details)];
    if (journal === 'general') ligne.push(texte(chantier));
    const entree = { id: `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`, journal, ligne };
    ecrireFile([...lireFile(), entree]);
    void envoyer().catch(() => {});
    return entree;
  }

  // ----- Dossier et tableurs dans le Drive -----

  function echapper(nom) { return nom.replace(/\\/g, '\\\\').replace(/'/g, "\\'"); }

  async function lireJson(url, options) {
    return (await googleConnexion.appeler(url, options)).json();
  }

  async function chercher(nom, type, parent) {
    const parametres = new URLSearchParams({
      q: `name='${echapper(nom)}' and mimeType='${type}' and '${echapper(parent)}' in parents and trashed=false`,
      fields: 'files(id)', pageSize: '10'
    });
    const trouves = await lireJson(`${drive}?${parametres}`);
    return trouves.files?.[0]?.id || '';
  }

  async function creer(nom, type, parent) {
    const cree = await lireJson(`${drive}?fields=id`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: nom, mimeType: type, parents: [parent] })
    });
    if (!cree.id) throw new Error(`« ${nom} » n’a pas pu être créé dans le Drive.`);
    return cree.id;
  }

  async function retenu(role) {
    return googlePicker.dossierChoisi(role) || await googlePicker.retrouverDepuisDrive(role);
  }

  async function retenir(id, nom, role) {
    googlePicker.enregistrerDossier(id, nom, role);
    try { await googlePicker.rangerDansDrive(role); } catch (erreur) {}
  }

  async function ajouterLignes(id, lignes) {
    const plage = encodeURIComponent('A1');
    await googleConnexion.appeler(`${sheets}/${encodeURIComponent(id)}/values/${plage}:append`
      + '?valueInputOption=RAW&insertDataOption=INSERT_ROWS', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ values: lignes })
    });
  }

  async function dossierJournaux() {
    const deja = await retenu('dossier_journaux');
    if (deja) return deja.id;
    const appCap = googlePicker.dossierAppCap();
    if (!appCap) throw new Error('Choisis d’abord le dossier « App Cap » dans « Réglages du Drive ». Les lignes du journal attendent sur le téléphone.');
    const nom = REGLAGES_GOOGLE.dossier_journaux;
    const id = await chercher(nom, typeDossier, appCap.id) || await creer(nom, typeDossier, appCap.id);
    await retenir(id, nom, 'dossier_journaux');
    return id;
  }

  // Trouve ou crée chaque journal. Une création est notée dans le Journal Général.
  async function preparer() {
    const ids = {};
    for (const [journal, definition] of Object.entries(definitions)) {
      const deja = await retenu(definition.role);
      if (deja) { ids[journal] = deja.id; continue; }
      const parent = await dossierJournaux();
      const nom = definition.nom();
      let id = await chercher(nom, typeTableur, parent);
      if (!id) {
        id = await creer(nom, typeTableur, parent);
        await retenir(id, nom, definition.role);
        // En-têtes EN TÊTE de la file (avant les lignes de ce journal) : comme toute ligne, ils ne
        // quittent la file qu'après réussite, même si Google tombe juste après la création.
        const { date, heure } = horodatage();
        ecrireFile([{ id: `${Date.now()}-${journal}-entetes`, journal, ligne: definition.entetes }, ...lireFile(),
          { id: `${Date.now()}-${journal}-creation`, journal: 'general',
            ligne: [date, heure, 'Création du journal', 'créé', nom, 'Numérisation'] }]);
        ids[journal] = id;
        continue;
      }
      await retenir(id, nom, definition.role);
      ids[journal] = id;
    }
    return ids;
  }

  // Envoie les lignes en attente, journal par journal. Une ligne ne quitte la file qu'après la
  // réussite de son envoi. Hors connexion ou sans Google : rien n'est tenté, rien n'est perdu.
  async function executer() {
    if (!lireFile().length) return { envoyees: 0, restantes: 0 };
    if ((typeof navigator !== 'undefined' && navigator.onLine === false) || !googleConnexion.connecte()) {
      return { envoyees: 0, restantes: lireFile().length };
    }
    const ids = await preparer();
    let envoyees = 0;
    for (const journal of Object.keys(definitions)) {
      const paquet = lireFile().filter(entree => entree.journal === journal);
      if (!paquet.length) continue;
      await ajouterLignes(ids[journal], paquet.map(entree => entree.ligne));
      const partis = new Set(paquet.map(entree => entree.id));
      ecrireFile(lireFile().filter(entree => !partis.has(entree.id)));
      envoyees += paquet.length;
    }
    return { envoyees, restantes: lireFile().length };
  }

  function envoyer() {
    if (!enCours) enCours = executer().finally(() => { enCours = null; });
    return enCours;
  }

  return { ajouter, envoyer, enAttente: () => lireFile().length, horodatage };
})();
