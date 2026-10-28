'use strict';

const googleConnexion = (() => {
  const cleJeton = 'cap_google_jeton_v1';
  const cleEtat = 'cap_google_etat_v1';
  let message = '';
  let reconnexion = false;

  function lireEtat(espace) {
    try { return espace.getItem(cleEtat); } catch (erreur) { return null; }
  }

  function deconnecter() {
    localStorage.removeItem(cleJeton);
    reconnexion = true;
  }

  const retour = new URLSearchParams(location.hash.slice(1));
  if (retour.has('access_token') || retour.has('error')) {
    const etat = retour.get('state');
    const valide = Boolean(etat) && (etat === lireEtat(sessionStorage) || etat === lireEtat(localStorage));
    history.replaceState(null, '', location.pathname + location.search);
    for (const espace of [sessionStorage, localStorage]) {
      try { espace.removeItem(cleEtat); } catch (erreur) {}
    }
    try {
      if (!valide) throw new Error('Connexion Google refusée : la vérification de sécurité a échoué. Réessaie avec le bouton.');
      if (retour.has('error')) throw new Error('La connexion Google n’a pas été autorisée. Tu peux réessayer avec le bouton.');
      const secondes = Number(retour.get('expires_in'));
      if (!retour.get('access_token') || !Number.isFinite(secondes) || secondes <= 60
        || (retour.get('token_type') || '').toLowerCase() !== 'bearer') {
        throw new Error('La réponse de Google est incomplète. Reconnecte-toi avec le bouton.');
      }
      localStorage.setItem(cleJeton, JSON.stringify({
        jeton: retour.get('access_token'), expiration: Date.now() + secondes * 1000
      }));
    } catch (erreur) {
      message = erreur.message;
      deconnecter();
    }
  }

  function jeton() {
    try {
      const valeur = localStorage.getItem(cleJeton);
      if (!valeur) return '';
      reconnexion = true;
      const sauvegarde = JSON.parse(valeur);
      return typeof sauvegarde.jeton === 'string' && Number.isFinite(sauvegarde.expiration)
        && sauvegarde.expiration > Date.now() + 60000 ? sauvegarde.jeton : '';
    } catch (erreur) {
      return '';
    }
  }

  function connecte() { return Boolean(jeton()); }

  function seConnecter() {
    const octets = crypto.getRandomValues(new Uint8Array(32));
    const etat = Array.from(octets, octet => octet.toString(16).padStart(2, '0')).join('');
    localStorage.setItem(cleEtat, etat);
    try { sessionStorage.setItem(cleEtat, etat); } catch (erreur) {}
    const url = new URL('https://accounts.google.com/o/oauth2/v2/auth');
    url.search = new URLSearchParams({
      client_id: REGLAGES_GOOGLE.id_client,
      redirect_uri: REGLAGES_GOOGLE.adresse_retour,
      response_type: 'token',
      scope: REGLAGES_GOOGLE.autorisations.join(' '),
      include_granted_scopes: 'true',
      state: etat
    }).toString();
    location.assign(url.href);
  }

  async function appeler(adresse, options = {}) {
    const url = new URL(adresse);
    if (url.protocol !== 'https:' || !['www.googleapis.com', 'sheets.googleapis.com'].includes(url.hostname)) {
      throw new Error('Adresse Google non autorisée.');
    }
    const valeur = jeton();
    if (!valeur) throw new Error('La connexion Google a expiré. Touche « Se reconnecter ».');
    const entetes = new Headers(options.headers);
    entetes.set('Authorization', `Bearer ${valeur}`);
    const reponse = await fetch(url.href, { ...options, headers: entetes, cache: 'no-store', redirect: 'error' });
    if (reponse.status === 401) {
      deconnecter();
      window.dispatchEvent(new Event('cap-google-deconnecte'));
      throw new Error('La connexion Google a expiré. Touche « Se reconnecter ».');
    }
    if (!reponse.ok) {
      const erreur = new Error(`Google n’a pas pu effectuer l’action (erreur ${reponse.status}). Réessaie plus tard.`);
      erreur.statut = reponse.status;
      throw erreur;
    }
    return reponse;
  }

  return { connecte, seConnecter, jeton, deconnecter, appeler,
    message: () => message, reconnexion: () => reconnexion };
})();
