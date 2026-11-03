'use strict';

// Lit et écrit les fichiers Markdown du dossier "Fichiers vocaux" (dans "App Cap", choisi une
// fois par Max via googlePicker). Ne crée jamais rien ailleurs ; ne touche à aucun fichier
// existant ; n'efface jamais une ligne (voir fichiers_vocaux.js pour les règles de contenu).
const fichiersVocauxDrive = (() => {
  const drive = 'https://www.googleapis.com/drive/v3/files';
  const envoi = 'https://www.googleapis.com/upload/drive/v3/files';
  const typeDossier = 'application/vnd.google-apps.folder';
  const typeFichier = 'text/markdown';
  const cleFichiers = 'cap_fichiers_vocaux_v1';
  let sousDossierId = '';

  function lireFichiers() {
    try {
      const brut = JSON.parse(localStorage.getItem(cleFichiers));
      return brut && typeof brut === 'object' ? brut : {};
    } catch (erreur) {
      return {};
    }
  }

  function garderFichier(cle, id) {
    try {
      const fichiers = lireFichiers();
      fichiers[cle] = id;
      localStorage.setItem(cleFichiers, JSON.stringify(fichiers));
    } catch (erreur) {}
  }

  function echapper(texte) {
    return texte.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
  }

  async function demander(url, options) {
    return (await googleConnexion.appeler(url, options)).json();
  }

  async function existe(id) {
    if (!id) return false;
    try {
      const resultat = await demander(`${drive}/${encodeURIComponent(id)}?fields=id,trashed`);
      return Boolean(resultat.id) && !resultat.trashed;
    } catch (erreur) {
      if (erreur.statut === 404) return false;
      throw erreur;
    }
  }

  async function sousDossier() {
    if (sousDossierId && await existe(sousDossierId)) return sousDossierId;
    const parent = googlePicker.dossierAppCap();
    if (!parent) throw new Error('Choisis d’abord le dossier « App Cap » dans les réglages de Cap.');
    const nom = REGLAGES_GOOGLE.dossier_fichiers_vocaux;
    const parametres = new URLSearchParams({
      q: `name='${echapper(nom)}' and mimeType='${typeDossier}' and trashed=false and '${echapper(parent.id)}' in parents`,
      fields: 'files(id)', pageSize: '10'
    });
    const trouves = await demander(`${drive}?${parametres}`);
    const id = trouves.files?.[0]?.id || (await demander(`${drive}?fields=id`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: nom, mimeType: typeDossier, parents: [parent.id] })
    })).id;
    if (!id) throw new Error('Le dossier « Fichiers vocaux » n’a pas pu être préparé.');
    sousDossierId = id;
    return id;
  }

  async function trouverOuCreerFichier(cle, nomFichier) {
    const gardes = lireFichiers();
    if (gardes[cle] && await existe(gardes[cle])) return gardes[cle];
    const dossier = await sousDossier();
    const parametres = new URLSearchParams({
      q: `name='${echapper(nomFichier)}' and mimeType='${typeFichier}' and trashed=false and '${echapper(dossier)}' in parents`,
      fields: 'files(id)', pageSize: '10'
    });
    const trouves = await demander(`${drive}?${parametres}`);
    const id = trouves.files?.[0]?.id || (await demander(`${drive}?fields=id`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: nomFichier, mimeType: typeFichier, parents: [dossier] })
    })).id;
    if (!id) throw new Error(`Le fichier « ${nomFichier} » n’a pas pu être préparé.`);
    garderFichier(cle, id);
    return id;
  }

  async function lireTexte(id) {
    const reponse = await googleConnexion.appeler(`${drive}/${encodeURIComponent(id)}?alt=media`);
    return reponse.text();
  }

  async function ecrireTexte(id, texte) {
    const reponse = await googleConnexion.appeler(
      `${envoi}/${encodeURIComponent(id)}?uploadType=media`,
      { method: 'PATCH', headers: { 'Content-Type': 'text/markdown; charset=UTF-8' }, body: texte }
    );
    return (await reponse.json()).id === id;
  }

  // Ajoute en code pur, sans écraser : relit le contenu actuel juste avant d'écrire.
  async function modifier(cle, nomFichier, transformer) {
    const id = await trouverOuCreerFichier(cle, nomFichier);
    const avant = await lireTexte(id);
    const resultat = transformer(avant);
    if (resultat.contenu !== avant) await ecrireTexte(id, resultat.contenu);
    return resultat;
  }

  return { trouverOuCreerFichier, lireTexte, ecrireTexte, modifier, sousDossier };
})();
