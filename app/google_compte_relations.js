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
    effacer(sessionStorage, cleEtat);
    effacer(localStorage, cleEtat);
    const secondes = Number(retour.get('expires_in'));
    if (retour.has('error')) {
      message = 'Le compte Cap n’a pas été connecté (refusé ou annulé). Rien n’a été lu.';
    } else if (!retour.get('access_token') || !Number.isFinite(secondes) || secondes <= 60
      || (retour.get('token_type') || '').toLowerCase() !== 'bearer') {
      message = 'La réponse de Google est incomplète. Reconnecte le compte Cap.';
    } else {
      ecrire(localStorage, cleJeton, JSON.stringify({
        jeton: retour.get('access_token'), expiration: Date.now() + secondes * 1000, compte: ''
      }));
      message = '';
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

  return { adresse, enregistrerAdresse, connecte, seConnecter, appeler, oublier, message: () => message };
})();
