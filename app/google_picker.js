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
    documents_personnels: 'cap_dossier_documents_personnels_v1',
    // Classement des scans (05/11/2026) : deux FICHIERS choisis par Max (pas des dossiers).
    architecture: 'cap_fichier_architecture_v1',
    tableur_classement: 'cap_fichier_tableur_classement_v1',
    // Journaux de chantier (05/11/2026) : créés par Cap (pas choisis), retenus de la même façon.
    dossier_journaux: 'cap_dossier_journaux_v1',
    journal_numerisation: 'cap_journal_numerisation_v1',
    journal_general: 'cap_journal_general_v1'
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
  // Diagnostic (05/11/2026) : `noter` reçoit chaque étape franchie, en mots simples, pour l'afficher
  // à Max ; `surSilence` est appelé si Google ne répond pas du tout. JAMAIS la clé ni le jeton dans
  // ces textes : seulement des étapes et le type de réponse de Google (vérifié par les tests).
  async function choisir(role = 'app_cap', { noter = () => {}, surSilence = () => {}, delaiSilence = 20000 } = {}) {
    cleDe(role);
    if (!clePicker.presente()) throw new Error('Le sélecteur Google n’est pas encore réglé : ajoute ta clé dans les réglages.');
    noter('Clé du sélecteur : présente sur ce téléphone.');
    if (!googleConnexion.connecte()) throw new Error('Connecte-toi à Google avant de choisir un dossier.');
    noter('Connexion à Google : oui.');
    await chargerScript();
    noter('Bibliothèque de Google : chargée.');
    await chargerPicker();
    noter('Sélecteur de Google : chargé.');
    return new Promise((resoudre, rejeter) => {
      let repondu = false;
      const minuterie = setTimeout(() => {
        if (repondu) return;
        noter(`La fenêtre de Google n’a pas répondu après ${Math.round(delaiSilence / 1000)} secondes.`);
        surSilence();
      }, delaiSilence);
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
          repondu = true;
          noter(`Réponse de Google : « ${String(reponse && reponse.action).slice(0, 40)} ».`);
          if (reponse.action === google.picker.Action.PICKED) {
            const choix = reponse.docs && reponse.docs[0];
            if (choix && choix.id) {
              clearTimeout(minuterie);
              enregistrerDossier(choix.id, choix.name, role);
              resoudre(dossierChoisi(role));
              return;
            }
          }
          if (reponse.action === google.picker.Action.CANCEL) { clearTimeout(minuterie); resoudre(null); return; }
          if (reponse.action !== google.picker.Action.LOADED) {
            clearTimeout(minuterie);
            rejeter(new Error('Le choix du dossier a échoué.'));
          }
        })
        .build();
      noter('Fenêtre de Google demandée.');
      selecteur.setVisible(true);
    });
  }

  const typeDoc = 'application/vnd.google-apps.document';
  const typeTableur = 'application/vnd.google-apps.spreadsheet';

  // Classement des scans (05/11/2026) : sur le téléphone, la fenêtre de Google ne permet pas la
  // sélection multiple. Max choisit donc chaque fichier À PART : le Doc d'architecture, puis le
  // tableur de classement. La fenêtre ne montre que le bon type, et le type est revérifié au retour
  // (sinon rien n'est gardé). Même diagnostic que choisir() : jamais la clé ni le jeton.
  const fichiersAttendus = Object.freeze({
    architecture: { type: typeDoc, titre: 'Choisis le Doc d’architecture des archives', libelle: 'un Google Doc' },
    tableur_classement: { type: typeTableur, titre: 'Choisis le tableur de classement', libelle: 'un tableur Google Sheets' }
  });

  // Numéro du projet Cap (05/11/2026) : avec le droit drive.file, Google ne rattache un fichier
  // choisi à Cap que si la fenêtre connaît ce numéro (`setAppId`) ; sans lui : « appNotAuthorizedToFile »
  // ou 404. C'est le début, public, de l'identifiant client (aucun secret, aucun droit en plus).
  function numeroProjet() {
    const numero = String(REGLAGES_GOOGLE.id_client || '').split('-')[0];
    if (!/^\d+$/.test(numero)) throw new Error('Le numéro du projet Cap est introuvable dans les réglages Google.');
    return numero;
  }

  async function choisirFichier(role, { noter = () => {}, surSilence = () => {}, delaiSilence = 20000 } = {}) {
    if (!Object.hasOwn(fichiersAttendus, role)) throw new Error('Fichier inconnu.');
    const attendu = fichiersAttendus[role];
    if (!clePicker.presente()) throw new Error('Le sélecteur Google n’est pas encore réglé : ajoute ta clé dans les réglages.');
    noter('Clé du sélecteur : présente sur ce téléphone.');
    if (!googleConnexion.connecte()) throw new Error('Connecte-toi à Google avant de choisir un fichier.');
    noter('Connexion à Google : oui.');
    await chargerScript();
    noter('Bibliothèque de Google : chargée.');
    await chargerPicker();
    noter('Sélecteur de Google : chargé.');
    return new Promise((resoudre, rejeter) => {
      let repondu = false;
      const minuterie = setTimeout(() => {
        if (repondu) return;
        noter(`La fenêtre de Google n’a pas répondu après ${Math.round(delaiSilence / 1000)} secondes.`);
        surSilence();
      }, delaiSilence);
      const vue = new google.picker.DocsView(google.picker.ViewId.DOCS)
        .setIncludeFolders(true)
        .setMimeTypes(attendu.type);
      const selecteur = new google.picker.PickerBuilder()
        .addView(vue)
        .setAppId(numeroProjet())
        .setOAuthToken(googleConnexion.jeton())
        .setDeveloperKey(clePicker.lire())
        .setTitle(attendu.titre)
        .setCallback(reponse => {
          repondu = true;
          noter(`Réponse de Google : « ${String(reponse && reponse.action).slice(0, 40)} ».`);
          if (reponse.action === google.picker.Action.LOADED) return;
          clearTimeout(minuterie);
          if (reponse.action === google.picker.Action.CANCEL) { resoudre(null); return; }
          if (reponse.action !== google.picker.Action.PICKED) { rejeter(new Error('Le choix du fichier a échoué.')); return; }
          const choix = (reponse.docs || []).find(doc => doc && doc.id);
          if (!choix || choix.mimeType !== attendu.type) {
            noter('Type du fichier choisi : pas le bon.');
            rejeter(new Error(`Ce fichier n’est pas ${attendu.libelle}. Rien n’a été gardé.`));
            return;
          }
          noter('Type du fichier choisi : le bon.');
          enregistrerDossier(choix.id, choix.name, role);
          resoudre(dossierChoisi(role));
        })
        .build();
      noter('Fenêtre de Google demandée.');
      selecteur.setVisible(true);
    });
  }

  // Secours (05/11/2026) : la fenêtre du sélecteur ne s'ouvre pas dans la coque Android (elle n'a
  // pas la session Google, restée dans Chrome). Max choisit donc « Documents Personnels » dans
  // Chrome ; son identifiant est rangé en information invisible (appProperties) sur le tableau des
  // tâches, que la coque retrouve avec le même droit drive.file, comme l'agenda (google_agenda.js).
  const proprietesDrive = Object.freeze({
    documents_personnels: 'cap_dossier_documents_personnels',
    architecture: 'cap_fichier_architecture',
    tableur_classement: 'cap_fichier_tableur_classement',
    dossier_journaux: 'cap_dossier_journaux',
    journal_numerisation: 'cap_journal_numerisation',
    journal_general: 'cap_journal_general'
  });
  const nomsParDefaut = Object.freeze({
    documents_personnels: 'Documents Personnels',
    architecture: 'Doc d’architecture',
    tableur_classement: 'Tableur de classement',
    dossier_journaux: 'Journaux',
    journal_numerisation: 'Journal Numérisation',
    journal_general: 'Journal Général'
  });
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
    rangerDansDrive, retrouverDepuisDrive, disponible, choisir, choisirFichier };
})();
