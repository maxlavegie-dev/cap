'use strict';

// Sélecteur de dossier Google (une seule fois) : avec le droit limité "drive.file", Cap ne voit
// que les fichiers qu'il crée lui-même. Pour écrire dans le dossier "App Cap" (créé à la main par
// Max), Max doit le choisir une fois dans la fenêtre officielle de Google ; Cap garde ensuite
// l'accès à ce dossier précis, sans jamais voir le reste du Drive de Max.
const googlePicker = (() => {
  // Un dossier choisi par rôle (05/11/2026) : « App Cap » (fichiers vocaux) et « Documents
  // Personnels » (où Cap crée 00_A_CLASSER pour les scans). Chacun est choisi une fois par Max.
  const cles = Object.freeze({
    app_cap: 'cap_dossier_app_cap_v1',
    documents_personnels: 'cap_dossier_documents_personnels_v1'
  });
  const titres = Object.freeze({
    app_cap: 'Choisis le dossier « App Cap »',
    documents_personnels: 'Choisis le dossier « Documents Personnels »'
  });
  function cleDe(role) {
    if (!Object.hasOwn(cles, role)) throw new Error('Dossier inconnu.');
    return cles[role];
  }
  let chargement = null;

  function dossierChoisi(role) {
    try {
      const brut = JSON.parse(localStorage.getItem(cleDe(role)));
      return brut && typeof brut.id === 'string' && brut.id ? brut : null;
    } catch (erreur) {
      return null;
    }
  }

  function dossierAppCap() { return dossierChoisi('app_cap'); }
  function dossierDocumentsPersonnels() { return dossierChoisi('documents_personnels'); }

  function enregistrerDossier(id, nom, role = 'app_cap') {
    localStorage.setItem(cleDe(role), JSON.stringify({ id, nom: nom || '' }));
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
  async function choisir(role = 'app_cap') {
    cleDe(role);
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
        .setTitle(titres[role])
        .setCallback(reponse => {
          if (reponse.action === google.picker.Action.PICKED) {
            const choix = reponse.docs && reponse.docs[0];
            if (choix && choix.id) {
              enregistrerDossier(choix.id, choix.name, role);
              resoudre(dossierChoisi(role));
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

  // Secours (05/11/2026) : la fenêtre du sélecteur ne s'ouvre pas dans la coque Android (elle n'a
  // pas la session Google, restée dans Chrome). Max choisit donc « Documents Personnels » dans
  // Chrome ; son identifiant est rangé en information invisible (appProperties) sur le tableau des
  // tâches, que la coque retrouve avec le même droit drive.file, comme l'agenda (google_agenda.js).
  const proprietesDrive = Object.freeze({ documents_personnels: 'cap_dossier_documents_personnels' });
  const nomsParDefaut = Object.freeze({ documents_personnels: 'Documents Personnels' });
  function cleRangeDrive(role) { return `${cleDe(role)}_drive`; }

  async function adresseTableau() {
    const tableau = await googleSheets.trouverOuCreer();
    if (typeof tableau?.id !== 'string' || !tableau.id) throw new Error('Le tableau Google n’est pas encore prêt.');
    return `https://www.googleapis.com/drive/v3/files/${encodeURIComponent(tableau.id)}`;
  }

  async function ecrireDansDrive(role, valeur) {
    await googleConnexion.appeler(`${await adresseTableau()}?fields=id`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ appProperties: { [proprietesDrive[role]]: valeur } })
    });
  }

  // Range le dossier choisi sur cet appareil dans le Drive (une seule fois par dossier).
  async function rangerDansDrive(role) {
    const dossier = dossierChoisi(role);
    if (!Object.hasOwn(proprietesDrive, role) || !dossier) return;
    if (localStorage.getItem(cleRangeDrive(role)) === dossier.id) return;
    await ecrireDansDrive(role, dossier.id);
    localStorage.setItem(cleRangeDrive(role), dossier.id);
  }

  // Sur un appareil où le dossier n'a pas été choisi (la coque) : le relit dans le Drive.
  async function retrouverDepuisDrive(role) {
    const deja = dossierChoisi(role);
    if (deja || !Object.hasOwn(proprietesDrive, role)) return deja;
    const reponse = await googleConnexion.appeler(`${await adresseTableau()}?fields=appProperties`);
    const id = (await reponse.json()).appProperties?.[proprietesDrive[role]];
    if (typeof id !== 'string' || !id) return null;
    enregistrerDossier(id, nomsParDefaut[role], role);
    localStorage.setItem(cleRangeDrive(role), id);
    return dossierChoisi(role);
  }

  // Oublie le dossier sur cet appareil, et aussi dans le Drive s'il y est rangé (sinon un autre
  // appareil le retrouverait). Ne touche à aucun fichier ni dossier de Max.
  async function oublierDossier(role = 'app_cap') {
    localStorage.removeItem(cleDe(role));
    localStorage.removeItem(cleRangeDrive(role));
    if (Object.hasOwn(proprietesDrive, role)) await ecrireDansDrive(role, null);
  }

  return { dossierAppCap, dossierDocumentsPersonnels, dossierChoisi, enregistrerDossier, oublierDossier,
    rangerDansDrive, retrouverDepuisDrive, disponible, choisir };
})();
