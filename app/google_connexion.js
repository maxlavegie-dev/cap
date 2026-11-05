'use strict';

const googleConnexion = (() => {
  const cleJeton = 'cap_google_jeton_v1';
  const cleEtat = 'cap_google_etat_v1';
  const cleSilencieux = 'cap_google_silencieux_v1';
  const cleEtatSilencieux = 'cap_google_etat_silencieux_v1';
  const cleConnu = 'cap_google_deja_connecte_v1';
  const cleGeste = 'cap_google_besoin_geste_v1';
  let message = '';
  let reconnexion = lireEtat(localStorage, cleConnu) === 'oui';
  let besoinGeste = lireEtat(localStorage, cleGeste) === 'oui';

  function memoriserConnexion() {
    reconnexion = true;
    try { localStorage.setItem(cleConnu, 'oui'); } catch (erreur) {}
  }

  function lireEtat(espace, cle = cleEtat) {
    try { return espace.getItem(cle); } catch (erreur) { return null; }
  }

  function deconnecter() {
    localStorage.removeItem(cleJeton);
    memoriserConnexion();
  }

  const retour = new URLSearchParams(location.hash.slice(1));
  if (retour.has('access_token') || retour.has('error')) {
    const etat = retour.get('state');
    const valide = Boolean(etat) && (etat === lireEtat(sessionStorage) || etat === lireEtat(localStorage));
    const silencieux = Boolean(etat) && etat === localStorage.getItem(cleEtatSilencieux);
    localStorage.removeItem(cleEtatSilencieux);
    history.replaceState(null, '', location.pathname + location.search);
    for (const espace of [sessionStorage, localStorage]) {
      try { espace.removeItem(cleEtat); } catch (erreur) {}
    }
    try {
      if (!valide) throw new Error('Connexion Google refusée : la vérification de sécurité a échoué. Réessaie avec le bouton.');
      if (retour.has('error')) {
        besoinGeste = silencieux && ['interaction_required', 'login_required', 'consent_required',
          'account_selection_required'].includes(retour.get('error'));
        if (besoinGeste) localStorage.setItem(cleGeste, 'oui');
        throw new Error(besoinGeste ? 'Google demande ton accord pour continuer.'
          : 'La connexion Google n’a pas été autorisée. Tu peux réessayer avec le bouton.');
      }
      const secondes = Number(retour.get('expires_in'));
      if (!retour.get('access_token') || !Number.isFinite(secondes) || secondes <= 60
        || (retour.get('token_type') || '').toLowerCase() !== 'bearer') {
        throw new Error('La réponse de Google est incomplète. Reconnecte-toi avec le bouton.');
      }
      localStorage.setItem(cleJeton, JSON.stringify({
        jeton: retour.get('access_token'), expiration: Date.now() + secondes * 1000
      }));
      memoriserConnexion();
      besoinGeste = false;
      localStorage.removeItem(cleGeste);
    } catch (erreur) {
      message = erreur.message;
      deconnecter();
    }
  }

  function jeton() {
    try {
      const valeur = localStorage.getItem(cleJeton);
      if (!valeur) return '';
      memoriserConnexion();
      const sauvegarde = JSON.parse(valeur);
      return typeof sauvegarde.jeton === 'string' && Number.isFinite(sauvegarde.expiration)
        && sauvegarde.expiration > Date.now() + 60000 ? sauvegarde.jeton : '';
    } catch (erreur) {
      return '';
    }
  }

  function connecte() { return Boolean(jeton()); }

  function expiration() {
    try {
      const sauvegarde = JSON.parse(localStorage.getItem(cleJeton));
      return typeof sauvegarde?.jeton === 'string' && Number.isFinite(sauvegarde.expiration)
        ? sauvegarde.expiration : 0;
    } catch (erreur) { return 0; }
  }

  function tenterSilencieux(conditionsOk) {
    jeton();
    const derniere = Number(localStorage.getItem(cleSilencieux));
    if (!conditionsOk || !reconnexion || besoinGeste || message || !navigator.onLine
      || expiration() >= Date.now() + 300000
      || (derniere && Date.now() - derniere <= 600000)) return false;
    seConnecter({ silencieux: true });
    return true;
  }

  function seConnecter({ silencieux = false } = {}) {
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
    if (silencieux) {
      url.searchParams.set('prompt', 'none');
      localStorage.setItem(cleSilencieux, String(Date.now()));
      localStorage.setItem(cleEtatSilencieux, etat);
    } else localStorage.removeItem(cleEtatSilencieux);
    location.assign(url.href);
  }

  const raisonsSansDeconnexion = new Set(['SERVICE_DISABLED', 'accessNotConfigured', 'appNotAuthorizedToFile',
    'cannotExportFile', 'exportSizeLimitExceeded', 'rateLimitExceeded', 'userRateLimitExceeded',
    'dailyLimitExceeded', 'storageQuotaExceeded', 'RATE_LIMIT_EXCEEDED']);

  // Code de raison donné par Google dans sa réponse d'erreur (lettres et « _ » seulement).
  async function raisonRefus(reponse) {
    try {
      const corps = await reponse.clone().json();
      const brute = corps?.error?.details?.find(detail => detail?.reason)?.reason
        || corps?.error?.errors?.[0]?.reason || corps?.error?.status || '';
      return /^[A-Za-z_]{1,60}$/.test(brute) ? brute : '';
    } catch (erreur) {
      return '';
    }
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
    // Refus 403 dont la raison n'est PAS la connexion (05/11/2026) : service non activé, fichier non
    // accessible, limites. Se déconnecter n'y changerait rien : on garde la connexion et on donne la
    // raison de Google (un code court, jamais le jeton). Raison inconnue ou de droits : comme avant.
    if (reponse.status === 403) {
      const raison = await raisonRefus(reponse);
      if (raisonsSansDeconnexion.has(raison)) {
        const erreur = new Error(`Google a refusé cette action (erreur 403, raison : ${raison}). La connexion reste active.`);
        erreur.statut = 403;
        erreur.raison = raison;
        throw erreur;
      }
    }
    if (reponse.status === 401 || reponse.status === 403) {
      message = reponse.status === 401 ? 'La connexion Google a expiré. Touche « Se reconnecter ».'
        : 'Google a refusé l’accès (erreur 403). Redonne l’accès avec le bouton.';
      deconnecter();
      window.dispatchEvent(new Event('cap-google-deconnecte'));
      const erreur = new Error(message);
      erreur.statut = reponse.status;
      throw erreur;
    }
    if (!reponse.ok) {
      const erreur = new Error(`Google n’a pas pu effectuer l’action (erreur ${reponse.status}). Réessaie plus tard.`);
      erreur.statut = reponse.status;
      throw erreur;
    }
    return reponse;
  }

  return { connecte, seConnecter, tenterSilencieux, expiration, jeton, deconnecter, appeler,
    besoinGeste: () => besoinGeste,
    message: () => message || (besoinGeste ? 'Google demande ton accord pour continuer.' : ''),
    reconnexion: () => reconnexion };
})();
