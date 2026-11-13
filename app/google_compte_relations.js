'use strict';

// Second compte Google, UNIQUEMENT pour « Relations » (07/11/2026, demandé par Max).
// Compte neuf créé par Max, qui ne contient que ce que Cap y crée ou que Max y dépose.
// - Droit demandé pour CE compte seulement : REGLAGES_GOOGLE.autorisations_relations (lecture seule de
//   son Drive). Le compte personnel de Max garde ses deux droits limités (google_connexion.js).
// - L'identifiant du compte reste sur le téléphone (localStorage), jamais dans le dépôt.
// - Avant la première lecture, Cap demande au Drive QUEL compte a été connecté : si ce n'est pas
//   l'identifiant enregistré, le jeton est jeté tout de suite et rien n'est lu.
// - Lecture seule codée : avec ce jeton, seules des lectures (GET) du Drive sont possibles.
// Chargé AVANT google_connexion.js : il prend le retour de Google qui le concerne (état à lui) et
// laisse les autres intacts ; sinon google_connexion.js le prendrait pour un retour falsifié.
const googleCompteRelations = (() => {
  const cleJeton = 'cap_google_relations_jeton_v1';
  const cleEtat = 'cap_google_relations_etat_v1';
  const cleAdresse = 'cap_google_relations_adresse_v1';
  const DRIVE = 'https://www.googleapis.com/drive/v3/';
  let message = '';
  // Vrai si CE chargement de la page vient d'un retour de Google pour le compte Cap.
  let retourRecent = false;

  const lire = (espace, cle) => { try { return espace.getItem(cle); } catch (erreur) { return null; } };
  const ecrire = (espace, cle, valeur) => { try { espace.setItem(cle, valeur); } catch (erreur) {} };
  const effacer = (espace, cle) => { try { espace.removeItem(cle); } catch (erreur) {} };
  const normaliser = texte => String(texte || '').trim().toLowerCase();

  function adresse() { return normaliser(lire(localStorage, cleAdresse)); }

  function enregistrerAdresse(texte) {
    const propre = normaliser(texte);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(propre)) {
      throw new Error('Identifiant du compte Cap incomplet : il ressemble à « nom@id.gle » ou « nom@gmail.com ».');
    }
    if (propre !== adresse()) effacer(localStorage, cleJeton);
    ecrire(localStorage, cleAdresse, propre);
    return propre;
  }

  // Retour de Google : seulement s'il porte l'état préparé par CE module.
  const retour = new URLSearchParams(location.hash.slice(1));
  const etatRecu = retour.get('state');
  if (etatRecu && (retour.has('access_token') || retour.has('error'))
    && (etatRecu === lire(sessionStorage, cleEtat) || etatRecu === lire(localStorage, cleEtat))) {
    history.replaceState(null, '', location.pathname + location.search);
    retourRecent = true;
    effacer(sessionStorage, cleEtat);
    effacer(localStorage, cleEtat);
    const secondes = Number(retour.get('expires_in'));
    if (retour.has('error')) {
      // Le code de Google est montré tel quel (lettres et « _ » seulement), pour comprendre le refus.
      const code = String(retour.get('error')).replace(/[^a-z_]/gi, '').slice(0, 60);
      message = `Le compte Cap n’a pas été connecté (refusé ou annulé ; réponse de Google : « ${code} »). Rien n’a été lu.`;
    } else if (!retour.get('access_token') || !Number.isFinite(secondes) || secondes <= 60
      || (retour.get('token_type') || '').toLowerCase() !== 'bearer') {
      message = 'La réponse de Google est incomplète. Reconnecte le compte Cap.';
    } else {
      ecrire(localStorage, cleJeton, JSON.stringify({
        jeton: retour.get('access_token'), expiration: Date.now() + secondes * 1000, compte: ''
      }));
      message = 'Google a répondu : connexion reçue. Vérification du compte…';
    }
  }

  function sauvegarde() {
    try {
      const s = JSON.parse(lire(localStorage, cleJeton));
      return s && typeof s.jeton === 'string' && Number.isFinite(s.expiration) ? s : null;
    } catch (erreur) { return null; }
  }

  function connecte() {
    const s = sauvegarde();
    return Boolean(s && s.expiration > Date.now() + 60000);
  }

  // Minutes avant la fin de la connexion du compte Cap (0 si pas connecté) : pour prévenir avant un album.
  function minutesRestantes() {
    const s = sauvegarde();
    return s ? Math.max(0, Math.floor((s.expiration - Date.now()) / 60000)) : 0;
  }

  // Jette le jeton de ce téléphone (rien d'autre).
  function oublier() { effacer(localStorage, cleJeton); }

  function seConnecter() {
    const compte = adresse();
    if (!compte) throw new Error('Écris d’abord l’identifiant du compte Cap.');
    const octets = crypto.getRandomValues(new Uint8Array(32));
    const etat = Array.from(octets, octet => octet.toString(16).padStart(2, '0')).join('');
    ecrire(localStorage, cleEtat, etat);
    ecrire(sessionStorage, cleEtat, etat);
    const url = new URL('https://accounts.google.com/o/oauth2/v2/auth');
    url.search = new URLSearchParams({
      client_id: REGLAGES_GOOGLE.id_client,
      redirect_uri: REGLAGES_GOOGLE.adresse_retour,
      response_type: 'token',
      scope: REGLAGES_GOOGLE.autorisations_relations.join(' '),
      // Jamais les droits du compte personnel avec ceux-ci, ni l'inverse.
      include_granted_scopes: 'false',
      // Google propose directement ce compte-là (pas une obligation : d'où la vérification ci-dessous).
      login_hint: compte,
      state: etat
    }).toString();
    location.assign(url.href);
  }

  async function lireCompteConnecte(jeton) {
    const reponse = await fetch(`${DRIVE}about?fields=user(emailAddress)`, {
      method: 'GET', headers: { Authorization: `Bearer ${jeton}` }, cache: 'no-store', redirect: 'error'
    });
    if (!reponse.ok) return '';
    try { return normaliser((await reponse.json())?.user?.emailAddress); } catch (erreur) { return ''; }
  }

  async function appeler(adresseUrl, options = {}) {
    const url = new URL(adresseUrl);
    if (url.protocol !== 'https:' || url.hostname !== 'www.googleapis.com' || !url.pathname.startsWith('/drive/v3/')) {
      throw new Error('Adresse non autorisée pour le compte Cap.');
    }
    if (String(options.method || 'GET').toUpperCase() !== 'GET' || options.body !== undefined) {
      throw new Error('Lecture seule : le compte Cap ne sert qu’à lire.');
    }
    const s = await jetonVerifie(); // 09/11/2026 : vérification mise à part (servie aussi à l'écriture limitée)
    const reponse = await fetch(url.href, {
      method: 'GET', headers: { Authorization: `Bearer ${s.jeton}` }, cache: 'no-store', redirect: 'error'
    });
    if (reponse.status === 401) {
      oublier();
      throw new Error('Connexion du compte Cap expirée. Touche « Autoriser la lecture du compte Cap ».');
    }
    if (!reponse.ok) throw new Error(`Google n’a pas pu lire (erreur ${reponse.status}). Rien n’a été modifié.`);
    return reponse;
  }

  // 09/11/2026 : le jeton du compte Cap, vérifié (pas expiré ; c'est bien le compte enregistré, sinon jeté). Même code
  // qu'avant dans appeler().
  async function jetonVerifie() {
    const s = sauvegarde();
    if (!s || !(s.expiration > Date.now() + 60000)) {
      throw new Error('Compte Cap pas connecté (ou connexion expirée). Touche « Autoriser la lecture du compte Cap ».');
    }
    if (!s.compte) {
      const compte = await lireCompteConnecte(s.jeton);
      if (!compte || compte !== adresse()) {
        oublier();
        message = `Mauvais compte : Google a connecté « ${compte || 'compte inconnu'} », pas le compte Cap enregistré. `
          + 'Rien n’a été lu, la connexion est jetée. Préviens Claude Code avant de recommencer.';
        throw new Error(message);
      }
      s.compte = compte;
      ecrire(localStorage, cleJeton, JSON.stringify(s));
    }
    return s;
  }

  // ----- 09/11/2026 (décision de Max) : ÉCRITURE LIMITÉE du compte Cap, pour le tableur « Commandes vocales (Cap) » -----
  // Avec le droit drive.file, Google ne laisse modifier que les fichiers créés par Cap. En plus, le CODE ne laisse passer
  // que ces demandes-là (tout le reste est refusé avant d'aller chez Google) :
  //  - créer un tableur : POST https://sheets.googleapis.com/v4/spreadsheets ;
  //  - poser la marque invisible : PATCH https://www.googleapis.com/drive/v3/files/{id}, corps = appProperties SEULEMENT,
  //    sans autre paramètre que « fields » (donc ni déplacement, ni renommage, ni corbeille) ;
  //  - écrire des cases : PUT …/v4/spreadsheets/{id}/values/{plage} ; ajouter des lignes : POST …/values/{plage}:append.
  // Jamais de suppression, d'effacement, de partage. La lecture (appeler) reste en lecture seule.
  // 10/11/2026 (accord de Max, CHANTIERS, séance 3) : + CRÉER un dossier ou un document Google VIDE :
  //  - POST https://www.googleapis.com/drive/v3/files (seul paramètre permis : « fields ») ; corps limité à name, mimeType,
  //    parents (un seul parent) et appProperties ; mimeType = dossier ou document Google seulement. Aucun contenu envoyé,
  //    aucun déplacement, renommage, corbeille, suppression ni partage (tout autre champ ou paramètre est refusé).
  const ID_FICHIER = '[A-Za-z0-9_-]{10,200}';
  const TYPES_CREES = ['application/vnd.google-apps.folder', 'application/vnd.google-apps.document'];
  // 10/11/2026 (accord de Max, c88) : + AJOUTER du texte à la FIN d'un document Google (le journal d'un chantier) :
  //  POST https://docs.googleapis.com/v1/documents/{id}:batchUpdate, sans paramètre, corps = UNE seule demande
  //  « insertText » à la fin du document (endOfSegmentLocation, sans autre champ), texte non vide. 11/11/2026 (c106, décision de
  //  Max : plus de limite de longueur des notes) : avant, 2000 caractères au plus ; la forme (un seul ajout, à la fin) reste exigée.
  //  Rien d'autre : ni effacement, ni remplacement, ni mise en forme, ni écriture au milieu. Google ne laisse de toute façon
  //  écrire que dans les documents créés par Cap (droit drive.file).
  function ajoutAutorise(params, corps) {
    if (params.length) return false;
    let c;
    try { c = JSON.parse(corps); } catch (erreur) { return false; }
    if (!c || typeof c !== 'object' || Object.keys(c).join() !== 'requests' || !Array.isArray(c.requests) || c.requests.length !== 1) return false;
    const r = c.requests[0];
    if (!r || typeof r !== 'object' || Object.keys(r).join() !== 'insertText') return false;
    const i = r.insertText;
    if (!i || typeof i !== 'object' || Object.keys(i).sort().join() !== 'endOfSegmentLocation,text') return false;
    if (!i.endOfSegmentLocation || typeof i.endOfSegmentLocation !== 'object' || Object.keys(i.endOfSegmentLocation).length) return false;
    return typeof i.text === 'string' && i.text.length >= 1;
  }
  function creationAutorisee(params, corps) {
    if (params.some(p => p !== 'fields')) return false;
    let c;
    try { c = JSON.parse(corps); } catch (erreur) { return false; }
    if (!c || typeof c !== 'object' || Array.isArray(c)) return false;
    if (Object.keys(c).some(k => !['name', 'mimeType', 'parents', 'appProperties'].includes(k))) return false;
    if (typeof c.name !== 'string' || !c.name.trim() || !TYPES_CREES.includes(c.mimeType)) return false;
    if (!Array.isArray(c.parents) || c.parents.length !== 1 || !new RegExp(`^(${ID_FICHIER}|root)$`).test(String(c.parents[0]))) return false;
    return c.appProperties === undefined || (typeof c.appProperties === 'object' && !Array.isArray(c.appProperties));
  }
  function ecritureAutorisee(url, methode, corps) {
    if (url.protocol !== 'https:' || url.username || url.password || url.port) return false;
    const params = [...url.searchParams.keys()];
    if (methode === 'POST' && url.hostname === 'sheets.googleapis.com' && url.pathname === '/v4/spreadsheets') return params.length === 0;
    if (methode === 'POST' && url.hostname === 'www.googleapis.com' && url.pathname === '/drive/v3/files') return creationAutorisee(params, corps); // 10/11/2026
    if (methode === 'POST' && url.hostname === 'docs.googleapis.com' && new RegExp(`^/v1/documents/${ID_FICHIER}:batchUpdate$`).test(url.pathname)) return ajoutAutorise(params, corps); // 10/11/2026 (c88)
    if (methode === 'PATCH' && url.hostname === 'www.googleapis.com' && new RegExp(`^/drive/v3/files/${ID_FICHIER}$`).test(url.pathname)) {
      if (params.some(p => p !== 'fields')) return false;
      try { const c = JSON.parse(corps); return c && typeof c === 'object' && Object.keys(c).length === 1 && c.appProperties && typeof c.appProperties === 'object'; } catch (erreur) { return false; }
    }
    if (url.hostname === 'sheets.googleapis.com' && params.every(p => ['valueInputOption', 'insertDataOption'].includes(p))) {
      if (methode === 'PUT' && new RegExp(`^/v4/spreadsheets/${ID_FICHIER}/values/[^/:]+$`).test(url.pathname)) return true;
      if (methode === 'POST' && new RegExp(`^/v4/spreadsheets/${ID_FICHIER}/values/[^/:]+:append$`).test(url.pathname)) return true;
    }
    return false;
  }
  async function appelerEcriture(adresseUrl, options = {}) {
    const url = new URL(adresseUrl);
    const methode = String(options.method || 'GET').toUpperCase();
    const corps = typeof options.body === 'string' ? options.body : '';
    if (!ecritureAutorisee(url, methode, corps)) throw new Error('Écriture non autorisée pour le compte Cap.');
    const s = await jetonVerifie();
    const reponse = await fetch(url.href, {
      method: methode, headers: { Authorization: `Bearer ${s.jeton}`, 'Content-Type': 'application/json' }, body: corps,
      cache: 'no-store', redirect: 'error'
    });
    if (reponse.status === 401) {
      oublier();
      throw new Error('Connexion du compte Cap expirée. Touche « Autoriser la lecture du compte Cap ».');
    }
    if (reponse.status === 403) {
      // 10/11/2026 (c88) : service Google Docs pas activé dans le projet de Cap : le dire (ce n'est pas un droit à redonner).
      let detail = '';
      try { detail = JSON.stringify(await reponse.clone().json()); } catch (e) { detail = ''; }
      if (/SERVICE_DISABLED|accessNotConfigured|has not been used|is disabled/i.test(detail)) {
        const erreur = new Error('Le service Google Docs n’est pas activé dans le projet Google de Cap : rien n’a été écrit. L’activer est un réglage chez Google, à décider par Max.');
        erreur.statut = 403;
        erreur.service = true;
        throw erreur;
      }
      const erreur = new Error('Le compte Cap n’a pas encore le droit d’écrire : touche « Autoriser la lecture du compte Cap » (Google demandera le nouveau droit).');
      erreur.statut = 403;
      throw erreur;
    }
    if (!reponse.ok) { const erreur = new Error(`Google n’a pas pu écrire (erreur ${reponse.status}).`); erreur.statut = reponse.status; throw erreur; }
    return reponse;
  }

  // Après le retour : demande au Drive quel compte est connecté (lecture seule), pour l'afficher.
  async function verifier() {
    const reponse = await appeler(`${DRIVE}about?fields=user(emailAddress)`);
    const compte = normaliser((await reponse.json())?.user?.emailAddress);
    message = `Compte Cap connecté : ${compte}. Touche « Compter ce que Cap voit dans le compte Cap ».`;
    return message;
  }

  // 09/11/2026 : + appelerEcriture, ecritureAutorisee (écriture limitée, voir plus haut).
  return { adresse, enregistrerAdresse, connecte, minutesRestantes, seConnecter, appeler, appelerEcriture, ecritureAutorisee, oublier, verifier,
    message: () => message, retourRecent: () => retourRecent };
})();
