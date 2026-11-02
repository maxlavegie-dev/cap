'use strict';

// Dépôt des scans dans le dossier 00_A_CLASSER du Drive (ici un faux dossier FICTIF créé par Cap).
// Aucune suppression, aucune modification d'un fichier existant : seulement des créations.
const scanDepot = (() => {
  const cleDossiers = 'cap_scan_dossiers_v1';
  const drive = 'https://www.googleapis.com/drive/v3/files';
  const envoi = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name';
  const typeDossier = 'application/vnd.google-apps.folder';
  let enCours = null;

  function lireDossiers() {
    try {
      const brut = JSON.parse(localStorage.getItem(cleDossiers));
      return brut && typeof brut === 'object' ? brut : {};
    } catch (erreur) {
      return {};
    }
  }

  function garderDossiers(modifications) {
    try {
      localStorage.setItem(cleDossiers, JSON.stringify({ ...lireDossiers(), ...modifications }));
    } catch (erreur) {}
  }

  async function demander(url, options) {
    return (await googleConnexion.appeler(url, options)).json();
  }

  function echapper(texte) {
    return texte.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
  }

  async function dossierValide(id) {
    if (!id) return false;
    try {
      const resultat = await demander(`${drive}/${encodeURIComponent(id)}?fields=id,trashed`);
      return Boolean(resultat.id) && !resultat.trashed;
    } catch (erreur) {
      if (erreur.statut === 404) return false;
      throw erreur;
    }
  }

  async function trouverOuCreerDossier(nom, parent) {
    const filtre = parent ? ` and '${echapper(parent)}' in parents` : '';
    const parametres = new URLSearchParams({
      q: `name='${echapper(nom)}' and mimeType='${typeDossier}' and trashed=false${filtre}`,
      fields: 'files(id)', pageSize: '10'
    });
    const trouves = await demander(`${drive}?${parametres}`);
    if (trouves.files?.[0]?.id) return trouves.files[0].id;
    const corps = { name: nom, mimeType: typeDossier };
    if (parent) corps.parents = [parent];
    const cree = await demander(`${drive}?fields=id`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps)
    });
    if (!cree.id) throw new Error(`Le dossier « ${nom} » n’a pas pu être préparé.`);
    return cree.id;
  }

  async function dossierAClasser() {
    const gardes = lireDossiers();
    if (gardes.a_classer && await dossierValide(gardes.a_classer)) return gardes.a_classer;
    let racine = gardes.archives;
    if (!(racine && await dossierValide(racine))) {
      racine = await trouverOuCreerDossier(REGLAGES_GOOGLE.dossier_archives, '');
    }
    const aClasser = await trouverOuCreerDossier(REGLAGES_GOOGLE.dossier_a_classer, racine);
    garderDossiers({ archives: racine, a_classer: aClasser });
    return aClasser;
  }

  // Reprise sans doublon : on reconnaît le scan par son nom d'origine (unique), jamais par le nom choisi par Max,
  // pour qu'un autre document du même nom ne soit pas pris à tort pour déjà déposé.
  async function dejaPresent(nom, dossier, origine = '') {
    const critere = origine
      ? `appProperties has { key='cap_origine' and value='${echapper(origine)}' }`
      : `name='${echapper(nom)}'`;
    const parametres = new URLSearchParams({
      q: `${critere} and '${echapper(dossier)}' in parents and trashed=false`,
      fields: 'files(id)', pageSize: '1'
    });
    return (await demander(`${drive}?${parametres}`)).files?.[0]?.id || '';
  }

  async function televerser(nom, pdf, dossier, origine = '') {
    const limite = `cap${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`;
    const infos = { name: nom, parents: [dossier], mimeType: 'application/pdf' };
    if (origine) {
      infos.description = `Nom d’origine : ${origine}`;
      infos.appProperties = { cap_origine: origine };
    }
    const meta = JSON.stringify(infos);
    const corps = new Blob([
      `--${limite}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${meta}\r\n`,
      `--${limite}\r\nContent-Type: application/pdf\r\n\r\n`, pdf, `\r\n--${limite}--`
    ]);
    const resultat = await demander(envoi, {
      method: 'POST', headers: { 'Content-Type': `multipart/related; boundary=${limite}` }, body: corps
    });
    if (!resultat.id) throw new Error('Le dépôt du scan n’a pas été confirmé.');
    return resultat.id;
  }

  async function deposerUn(fiche, file) {
    const dossier = await dossierAClasser();
    const nomDepose = fiche.nom_valide || fiche.nom;
    const origine = fiche.nom_valide ? fiche.nom : '';
    let id = await dejaPresent(nomDepose, dossier, origine);
    if (!id) id = await televerser(nomDepose, fiche.pdf, dossier, origine);
    await file.marquerDepose(fiche.id, id);
    return id;
  }

  function pret() {
    return typeof navigator === 'undefined' || navigator.onLine !== false
      ? googleConnexion.connecte() : false;
  }

  async function executer(file, apres) {
    let deposes = 0;
    let erreur = '';
    for (const fiche of await file.enAttente()) {
      if (!fiche.pdf) continue;
      try {
        await deposerUn(fiche, file);
        deposes++;
        if (apres) apres(fiche);
      } catch (e) {
        erreur = e && e.message ? e.message : String(e);
        try { await file.marquerErreur(fiche.id, erreur); } catch (autre) {}
        break;
      }
    }
    return { deposes, restants: (await file.enAttente()).length, erreur };
  }

  // Dépose les scans en attente, un par un. Si le réseau ou Google échoue, tout reste sur le téléphone.
  function deposerEnAttente(file, apres) {
    if (!pret()) return file.enAttente().then(liste => ({ deposes: 0, restants: liste.length, erreur: '' }));
    if (!enCours) enCours = executer(file, apres).finally(() => { enCours = null; });
    return enCours;
  }

  return { deposerEnAttente, dossierAClasser, pret };
})();
