'use strict';

const googleSheets = (() => {
  const cle = 'cap_google_fichier_v1';
  const base = 'https://sheets.googleapis.com/v4/spreadsheets';
  const champs = ['id', 'intitule', 'categorie', 'sous_categorie', 'fait', 'date_entree',
    'echeance', 'date_realisation', 'priorite', 'parente', 'note', 'avant_le', 'abandonnee_le', 'origine', 'fictif'];
  const entetes = ['Identifiant', 'Intitulé', 'Catégorie', 'Sous-catégorie', 'Fait', "Date d'entrée",
    'Échéance', 'Date de réalisation', 'Priorité', 'Tâche parente', 'Note', 'Avant le', 'Abandonnée le', 'Origine', 'Fictif'];
  const entetesModeles = ['Modèle', 'Étape', 'Retirée le', 'Modifiée le'];
  const entetesCategories = ['Catégorie', 'Sous-catégorie de', 'Couleur', 'Retirée le', 'Modifiée le', 'Ordre'];
  const entetesJournal = ['Date et heure', 'Venu de', 'Ce que Max a dit ou touché', 'Ce que Cap a compris', 'Ce que Cap a fait'];
  let fichier = '';
  let ouverture = null;

  function plage(nom, cellules) { return `'${nom.replace(/'/g, "''")}'!${cellules}`; }
  function adresse(suite) {
    if (!fichier) throw new Error('Le tableau Google n’est pas encore prêt.');
    return `${base}/${encodeURIComponent(fichier)}${suite}`;
  }
  async function lire(url) { return (await googleConnexion.appeler(url)).json(); }
  async function poster(url, contenu) {
    const resultat = await (await googleConnexion.appeler(url, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(contenu)
    })).json();
    if (url.includes('/values')) {
      try { localStorage.setItem('cap_google_dernier_envoi_v1', String(Date.now())); } catch (erreur) {}
      window.dispatchEvent(new Event('cap-google-etat'));
    }
    return resultat;
  }
  function valeurs(tache) { return champs.map(champ => tache[champ]); }

  async function ouvrir() {
    const garde = localStorage.getItem(cle);
    if (garde) {
      try {
        const resultat = await lire(`https://www.googleapis.com/drive/v3/files/${encodeURIComponent(garde)}?fields=id,trashed`);
        if (!resultat.trashed && resultat.id) {
          fichier = resultat.id;
          return { id: fichier, cree: false };
        }
      } catch (erreur) {
        if (erreur.statut !== 404) throw erreur;
      }
    }
    const nom = REGLAGES_GOOGLE.nom_fichier_taches.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
    const parametres = new URLSearchParams({
      q: `name='${nom}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false`,
      fields: 'files(id),nextPageToken', pageSize: '100'
    });
    let page = '';
    do {
      if (page) parametres.set('pageToken', page);
      const trouves = await lire(`https://www.googleapis.com/drive/v3/files?${parametres}`);
      if (trouves.files?.length) {
        fichier = trouves.files[0].id;
        localStorage.setItem(cle, fichier);
        return { id: fichier, cree: false };
      }
      page = trouves.nextPageToken || '';
    } while (page);
    const copie = TACHES.map(tache => ({ ...tache }));
    stockage.verifier(copie);
    const resultat = await poster(base, {
      properties: { title: REGLAGES_GOOGLE.nom_fichier_taches },
      sheets: Object.values(REGLAGES_GOOGLE.onglets).map((title, sheetId) => ({
        properties: { sheetId, title, gridProperties: { frozenRowCount: 1 } }
      }))
    });
    fichier = resultat.spreadsheetId;
    localStorage.setItem(cle, fichier);
    await poster(adresse('/values:batchUpdate'), {
      valueInputOption: 'RAW', data: [
        { range: plage(REGLAGES_GOOGLE.onglets.taches, 'A1:O'), values: [entetes, ...copie.map(valeurs)] },
        { range: plage(REGLAGES_GOOGLE.onglets.etapes_par_defaut, 'A1:D'),
          values: [entetesModeles, ...Object.entries(ETAPES_PAR_DEFAUT).flatMap(([modele, etapes]) => etapes.map(etape => [modele, etape, '', '']))] },
        { range: plage(REGLAGES_GOOGLE.onglets.categories, 'A1:F'), values: [entetesCategories] },
        { range: plage(REGLAGES_GOOGLE.onglets.journal, 'A1:E'), values: [entetesJournal] },
        { range: plage(REGLAGES_GOOGLE.onglets.phrases_clavier, 'A1:E'),
          values: [['Identifiant', 'Catégorie', 'Début', 'À compléter', 'Action'],
            ...PHRASES_CLAVIER.map(phrase => [phrase.id, phrase.categorie, phrase.debut, phrase.a_completer, phrase.action])] }
      ]
    });
    await poster(adresse(':batchUpdate'), {
      requests: [4, 14].map(colonne => ({ setDataValidation: {
        range: { sheetId: 0, startRowIndex: 1, startColumnIndex: colonne, endColumnIndex: colonne + 1 },
        rule: { condition: { type: 'BOOLEAN' }, strict: true, showCustomUi: true }
      } }))
    });
    return { id: fichier, cree: true };
  }

  function trouverOuCreer() {
    if (!ouverture) ouverture = ouvrir().finally(() => { ouverture = null; });
    return ouverture;
  }

  function convertir(ligne) {
    const tache = {};
    champs.forEach((champ, indice) => {
      const cellule = ligne[indice] ?? '';
      if (champ === 'fait' || champ === 'fictif') {
        if (cellule === '' || cellule === false || cellule === 'FALSE') tache[champ] = false;
        else if (cellule === true || cellule === 'TRUE') tache[champ] = true;
        else throw new Error('Case à cocher illisible');
      } else tache[champ] = cellule;
    });
    if (typeof tache.parente !== 'string') throw new Error('Lien de parenté illisible');
    stockage.verifier([{ ...tache, parente: '' }]);
    return tache;
  }

  async function lireTaches() {
    const resultat = await lire(adresse(`/values/${encodeURIComponent(plage(REGLAGES_GOOGLE.onglets.taches, 'A:O'))}?valueRenderOption=UNFORMATTED_VALUE`));
    const lignes = resultat.values || [];
    if (JSON.stringify(lignes[0]) !== JSON.stringify(entetes)) {
      throw new Error('Les colonnes du tableau sont illisibles. Je n’y touche pas.');
    }
    const valides = [];
    const illisibles = [];
    const occurrences = new Map();
    lignes.slice(1).forEach((ligne, indice) => {
      if (ligne.every(cellule => cellule === '' || cellule === null)) return;
      const entree = { ligne: indice + 2, id: typeof ligne[0] === 'string' ? ligne[0] : '', valeurs: ligne };
      if (entree.id) occurrences.set(entree.id, (occurrences.get(entree.id) || 0) + 1);
      try { valides.push({ ...entree, tache: convertir(ligne) }); }
      catch (erreur) { illisibles.push(entree); }
    });
    const uniques = valides.filter(entree => {
      if (occurrences.get(entree.id) === 1) return true;
      illisibles.push(entree);
      return false;
    });
    const parents = new Map(uniques.map(entree => [entree.id, entree.tache]));
    const bonnes = uniques.filter(entree => {
      try {
        if (entree.tache.parente) stockage.verifier([entree.tache, parents.get(entree.tache.parente)]);
        return true;
      } catch (erreur) { illisibles.push(entree); return false; }
    });
    return { taches: bonnes.map(entree => entree.tache), illisibles,
      lignes: new Map(bonnes.map(entree => [entree.id, entree.ligne])) };
  }

  async function ecrireTaches(listeTaches) {
    const lecture = await lireTaches();
    const interdits = new Set(lecture.illisibles.map(entree => entree.id));
    const uniques = new Map(listeTaches.map(tache => [tache.id, tache]));
    const modifications = [];
    const ajouts = [];
    for (const tache of uniques.values()) {
      stockage.verifier([{ ...tache, parente: '' }]);
      if (interdits.has(tache.id)) continue;
      if (lecture.lignes.has(tache.id)) modifications.push(tache);
      else ajouts.push(tache);
    }
    const ecrits = [];
    if (modifications.length) {
      await poster(adresse('/values:batchUpdate'), { valueInputOption: 'RAW',
        data: modifications.map(tache => ({
          range: plage(REGLAGES_GOOGLE.onglets.taches, `A${lecture.lignes.get(tache.id)}:O${lecture.lignes.get(tache.id)}`),
          values: [valeurs(tache)]
        })) });
      ecrits.push(...modifications.map(tache => tache.id));
    }
    try {
      if (ajouts.length) {
        await poster(adresse(`/values/${encodeURIComponent(plage(REGLAGES_GOOGLE.onglets.taches, 'A:O'))}:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS`), {
          values: ajouts.map(valeurs)
        });
        ecrits.push(...ajouts.map(tache => tache.id));
      }
    } catch (erreur) {
      erreur.ecrits = ecrits;
      throw erreur;
    }
    return ecrits;
  }

  const vide = cellule => cellule === '' || cellule === null || cellule === undefined;

  async function lireOnglet(nom, colonnes, entete, attendues) {
    const lignes = (await lire(adresse(`/values/${encodeURIComponent(plage(nom, colonnes))}?valueRenderOption=UNFORMATTED_VALUE`))).values || [];
    const premiere = JSON.stringify(lignes[0] || []);
    if (lignes.length && !attendues.some(longueur => premiere === JSON.stringify(entete.slice(0, longueur)))) {
      throw new Error(`Les colonnes de l’onglet « ${nom} » sont illisibles. Je n’y touche pas.`);
    }
    const contenu = lignes.slice(1).filter(ligne => !ligne.every(vide)).map(ligne => {
      const cellules = entete.map((titre, indice) => (vide(ligne[indice]) ? ''
        : titre === 'Ordre' && Number.isFinite(ligne[indice]) ? String(ligne[indice]) : ligne[indice]));
      if (cellules.some(cellule => typeof cellule !== 'string') || !cellules[0].trim()) {
        throw new Error(`Une ligne de l’onglet « ${nom} » est illisible. Je n’y touche pas.`);
      }
      return cellules.map(cellule => cellule.trim());
    });
    return { lignes: lignes.length, contenu };
  }

  async function lireListes() {
    const titres = ((await lire(adresse('?fields=sheets.properties.title'))).sheets || []).map(feuille => feuille.properties?.title);
    const nomModeles = REGLAGES_GOOGLE.onglets.etapes_par_defaut;
    const nomCategories = REGLAGES_GOOGLE.onglets.categories;
    const resultat = { modeles: [], categories: [], lignesModeles: 0, lignesCategories: 0,
      manquants: [nomModeles, nomCategories].filter(nom => !titres.includes(nom)) };
    if (titres.includes(nomModeles)) {
      const onglet = await lireOnglet(nomModeles, 'A:D', entetesModeles, [2, 4]);
      resultat.lignesModeles = onglet.lignes;
      for (const [nom, etape, retiree, modifiee] of onglet.contenu) {
        if (!etape) throw new Error(`Une ligne de l’onglet « ${nomModeles} » est illisible. Je n’y touche pas.`);
        let modele = resultat.modeles.find(item => item.nom.toLocaleLowerCase('fr') === nom.toLocaleLowerCase('fr'));
        if (!modele) {
          modele = { nom, etapes: [], retiree_le: retiree, modifie_le: modifiee };
          resultat.modeles.push(modele);
        }
        modele.etapes.push(etape);
      }
    }
    if (titres.includes(nomCategories)) {
      const onglet = await lireOnglet(nomCategories, 'A:F', entetesCategories, [5, 6]);
      resultat.lignesCategories = onglet.lignes;
      resultat.categories = onglet.contenu.map(([nom, parente, couleur, retiree, modifiee, ordre]) => ({
        nom, parente, couleur, retiree_le: retiree, modifie_le: modifiee, ordre
      }));
    }
    return resultat;
  }

  async function ecrireListes(donnees) {
    const lecture = await lireListes();
    if (lecture.manquants.length) {
      await poster(adresse(':batchUpdate'), { requests: lecture.manquants.map(title => ({
        addSheet: { properties: { title, gridProperties: { frozenRowCount: 1 } } }
      })) });
    }
    const completer = (lignes, total, largeur) => {
      while (lignes.length < total) lignes.push(Array(largeur).fill(''));
      return lignes;
    };
    const modeles = [entetesModeles, ...donnees.modeles.flatMap(modele => modele.etapes.map(etape =>
      [modele.nom, etape, modele.retiree_le, modele.modifie_le]))];
    const categories = [entetesCategories, ...donnees.categories.map(categorie =>
      [categorie.nom, categorie.parente, categorie.couleur, categorie.retiree_le, categorie.modifie_le, categorie.ordre ? String(categorie.ordre) : ''])];
    await poster(adresse('/values:batchUpdate'), { valueInputOption: 'RAW', data: [
      { range: plage(REGLAGES_GOOGLE.onglets.etapes_par_defaut, 'A1:D'), values: completer(modeles, lecture.lignesModeles, 4) },
      { range: plage(REGLAGES_GOOGLE.onglets.categories, 'A1:F'), values: completer(categories, lecture.lignesCategories, 6) }
    ] });
  }

  async function ajouterJournal(lignes) {
    if (!fichier) await trouverOuCreer();
    const nom = REGLAGES_GOOGLE.onglets.journal;
    const titres = ((await lire(adresse('?fields=sheets.properties.title'))).sheets || []).map(feuille => feuille.properties?.title);
    if (!titres.includes(nom)) {
      await poster(adresse(':batchUpdate'), { requests: [{
        addSheet: { properties: { title: nom, gridProperties: { frozenRowCount: 1 } } }
      }] });
      await poster(adresse('/values:batchUpdate'), { valueInputOption: 'RAW', data: [
        { range: plage(nom, 'A1:E1'), values: [entetesJournal] }
      ] });
    }
    await poster(adresse(`/values/${encodeURIComponent(plage(nom, 'A:E'))}:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS`), {
      values: lignes
    });
  }

  return { trouverOuCreer, lireTaches, ecrireTaches, lireListes, ecrireListes, ajouterJournal };
})();
