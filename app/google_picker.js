'use strict';

// Sélecteur de dossier Google (une seule fois) : avec le droit limité "drive.file", Cap ne voit
// que les fichiers qu'il crée lui-même. Pour écrire dans le dossier "App Cap" (créé à la main par
// Max), Max doit le choisir une fois dans la fenêtre officielle de Google ; Cap garde ensuite
// l'accès à ce dossier précis, sans jamais voir le reste du Drive de Max.
const googlePicker = (() => {
  const cleDossier = 'cap_dossier_app_cap_v1';
  let chargement = null;

  function dossierAppCap() {
    try {
      const brut = JSON.parse(localStorage.getItem(cleDossier));
      return brut && typeof brut.id === 'string' && brut.id ? brut : null;
    } catch (erreur) {
      return null;
    }
  }

  function enregistrerDossier(id, nom) {
    localStorage.setItem(cleDossier, JSON.stringify({ id, nom: nom || '' }));
  }

  function disponible() {
    return clePicker.presente() && googleConnexion.connecte();
  }

  function chargerScript() {
    if (window.gapi) return Promise.resolve();
    if (!chargement) {
      chargement = new Promise((resoudre, rejeter) => {
        const script = document.createElement('script');
        script.src = 'https://apis.google.com/js/api.js';
        script.onload = resoudre;
        script.onerror = () => rejeter(new Error('Le sélecteur Google n’a pas pu se charger.'));
        document.head.appendChild(script);
      });
    }
    return chargement;
  }

  function chargerPicker() {
    return new Promise((resoudre, rejeter) => {
      window.gapi.load('picker', { callback: resoudre, onerror: () => rejeter(new Error('Le sélecteur Google n’a pas pu se charger.')) });
    });
  }

  // Ouvre la fenêtre Google : Max choisit "App Cap" une seule fois, son choix est gardé sur le téléphone.
  async function choisir() {
    if (!clePicker.presente()) throw new Error('Le sélecteur Google n’est pas encore réglé : ajoute ta clé dans les réglages.');
    if (!googleConnexion.connecte()) throw new Error('Connecte-toi à Google avant de choisir un dossier.');
    await chargerScript();
    await chargerPicker();
    return new Promise((resoudre, rejeter) => {
      const vue = new google.picker.DocsView(google.picker.ViewId.FOLDERS)
        .setSelectFolderEnabled(true)
        .setIncludeFolders(true)
        .setMimeTypes('application/vnd.google-apps.folder');
      const selecteur = new google.picker.PickerBuilder()
        .addView(vue)
        .setOAuthToken(googleConnexion.jeton())
        .setDeveloperKey(clePicker.lire())
        .setCallback(reponse => {
          if (reponse.action === google.picker.Action.PICKED) {
            const choix = reponse.docs && reponse.docs[0];
            if (choix && choix.id) {
              enregistrerDossier(choix.id, choix.name);
              resoudre(dossierAppCap());
              return;
            }
          }
          if (reponse.action === google.picker.Action.CANCEL) { resoudre(null); return; }
          if (reponse.action !== google.picker.Action.LOADED) rejeter(new Error('Le choix du dossier a échoué.'));
        })
        .build();
      selecteur.setVisible(true);
    });
  }

  function oublierDossier() {
    localStorage.removeItem(cleDossier);
  }

  return { dossierAppCap, enregistrerDossier, oublierDossier, disponible, choisir };
})();
