'use strict';

const sauvegardeDrive = (() => {
  const cleEtat = 'cap_sauvegarde_v1';
  const drive = 'https://www.googleapis.com/drive/v3/files';
  const semaine = 7 * 24 * 60 * 60 * 1000;
  const formatDate = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
  let enCours = null;

  function etat() {
    try {
      const brut = JSON.parse(localStorage.getItem(cleEtat));
      return brut && typeof brut === 'object' ? {
        derniere: typeof brut.derniere === 'string' ? brut.derniere : '',
        dossier: typeof brut.dossier === 'string' ? brut.dossier : '',
        nombre: Number.isInteger(brut.nombre) ? brut.nombre : 0
      } : { derniere: '', dossier: '', nombre: 0 };
    } catch (erreur) {
      return { derniere: '', dossier: '', nombre: 0 };
    }
  }

  function garder(modifications) {
    try {
      localStorage.setItem(cleEtat, JSON.stringify({ ...etat(), ...modifications }));
    } catch (erreur) {}
    window.dispatchEvent(new Event('cap-sauvegarde-etat'));
  }

  async function demander(url, options) {
    return (await googleConnexion.appeler(url, options)).json();
  }

  function envoyerJson(url, contenu) {
    return demander(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(contenu) });
  }

  async function trouverDossier() {
    const garde = etat().dossier;
    if (garde) {
      try {
        const resultat = await demander(`${drive}/${encodeURIComponent(garde)}?fields=id,trashed`);
        if (resultat.id && !resultat.trashed) return resultat.id;
      } catch (erreur) {
        if (erreur.statut !== 404) throw erreur;
      }
    }
    const nom = REGLAGES_GOOGLE.dossier_sauvegardes.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
    const parametres = new URLSearchParams({
      q: `name='${nom}' and mimeType='application/vnd.google-apps.folder' and trashed=false`,
      fields: 'files(id)', pageSize: '10'
    });
    const trouves = await demander(`${drive}?${parametres}`);
    const id = trouves.files?.[0]?.id || (await envoyerJson(`${drive}?fields=id`, {
      name: REGLAGES_GOOGLE.dossier_sauvegardes, mimeType: 'application/vnd.google-apps.folder'
    })).id;
    if (!id) throw new Error('Le dossier des sauvegardes n’a pas pu être préparé.');
    garder({ dossier: id });
    return id;
  }

  async function lister(dossier) {
    const parametres = new URLSearchParams({
      q: `'${dossier}' in parents and trashed=false`,
      orderBy: 'createdTime desc', fields: 'files(id,name,createdTime)', pageSize: '100'
    });
    return (await demander(`${drive}?${parametres}`)).files || [];
  }

  async function executer() {
    const { id } = await googleSheets.trouverOuCreer();
    const dossier = await trouverDossier();
    const nom = `${REGLAGES_GOOGLE.nom_fichier_taches} – sauvegarde du ${formatDate.format(new Date())}`;
    const copie = await envoyerJson(`${drive}/${encodeURIComponent(id)}/copy?fields=id,name`, { name: nom, parents: [dossier] });
    if (!copie.id) throw new Error('La copie n’a pas été créée.');
    const copies = await lister(dossier);
    garder({ derniere: new Date().toISOString(), nombre: copies.length });
    if (typeof journalActions !== 'undefined') {
      journalActions.consigner({ source: 'Cap', compris: 'sauvegarde du tableau', fait: `copie créée : ${nom}` });
    }
    return { nom, nombre: copies.length, enTrop: Math.max(0, copies.length - REGLAGES_GOOGLE.sauvegardes_a_garder) };
  }

  function sauvegarder() {
    if (!googleConnexion.connecte()) return Promise.reject(new Error('Connecte-toi à Google pour sauvegarder.'));
    if (!enCours) enCours = executer().finally(() => { enCours = null; });
    return enCours;
  }

  function aFaire(maintenant = Date.now()) {
    const derniere = Date.parse(etat().derniere);
    return Number.isFinite(derniere) && maintenant - derniere >= semaine;
  }

  async function verifierAutomatique() {
    if (!aFaire() || !googleConnexion.connecte()) return null;
    try {
      return await sauvegarder();
    } catch (erreur) {
      return null;
    }
  }

  return { etat, sauvegarder, verifierAutomatique, aFaire };
})();
