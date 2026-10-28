'use strict';

const synchronisation = (() => {
  const cle = 'cap_google_file_v1';
  let envoi = null;
  let demarrage = null;
  let pret = false;
  let erreurEtat = '';
  let nombreIllisibles = 0;

  function file() {
    const contenu = localStorage.getItem(cle);
    const ids = contenu === null ? [] : JSON.parse(contenu);
    if (!Array.isArray(ids) || ids.some(id => typeof id !== 'string' || !id)) {
      throw new Error('La file de synchronisation est illisible. Elle reste intacte.');
    }
    return [...new Set(ids)];
  }

  function publier() { window.dispatchEvent(new Event('cap-google-etat')); }

  function etat() {
    let nombre;
    try { nombre = file().length; } catch (erreur) { return erreur.message; }
    let texte = !navigator.onLine ? `hors connexion, ${nombre} en attente`
      : !googleConnexion.connecte() ? 'non connecté'
        : erreurEtat || (nombre ? `${nombre} changements en attente` : 'synchronisé');
    if (nombreIllisibles) texte += ` — ${nombreIllisibles} lignes du tableau sont illisibles, je n’y touche pas`;
    return texte;
  }

  function ajouter(ids) {
    localStorage.setItem(cle, JSON.stringify([...new Set([...file(), ...ids])]));
  }

  function signaler(ids) {
    try {
      ajouter(ids);
      erreurEtat = '';
      publier();
      if (googleConnexion.connecte() && navigator.onLine) void envoyer();
    } catch (erreur) {
      erreurEtat = 'Impossible de garder la file de synchronisation. Les tâches restent sur ce téléphone.';
      publier();
    }
  }

  function acquitter(ids, copies) {
    const ecrits = new Set(ids.filter(id => {
      const actuelle = TACHES.find(tache => tache.id === id);
      return actuelle && JSON.stringify(actuelle) === copies.get(id);
    }));
    localStorage.setItem(cle, JSON.stringify(file().filter(id => !ecrits.has(id))));
  }

  function envoyer() {
    if (envoi) return envoi;
    if (!pret || demarrage || !googleConnexion.connecte() || !navigator.onLine) {
      publier();
      return Promise.resolve(etat());
    }
    envoi = Promise.resolve().then(async () => {
      try {
        while (googleConnexion.connecte() && navigator.onLine) {
          const ids = new Set(file());
          const taches = TACHES.filter(tache => ids.has(tache.id)).map(tache => ({ ...tache }));
          if (!taches.length) break;
          const copies = new Map(taches.map(tache => [tache.id, JSON.stringify(tache)]));
          let ecrits;
          try { ecrits = await googleSheets.ecrireTaches(taches); }
          catch (erreur) {
            if (erreur.ecrits?.length) acquitter(erreur.ecrits, copies);
            throw erreur;
          }
          acquitter(ecrits, copies);
          erreurEtat = '';
          if (!ecrits.length) break;
        }
      } catch (erreur) {
        erreurEtat = erreur instanceof TypeError
          ? 'Connexion impossible : les changements restent en attente.' : erreur.message;
      }
    }).finally(() => {
      envoi = null;
      publier();
    }).then(() => etat());
    return envoi;
  }

  function demarrer() {
    if (demarrage) return demarrage;
    demarrage = Promise.resolve().then(async () => {
      try {
        if (envoi) await envoi;
        pret = false;
        if (!googleConnexion.connecte() || !navigator.onLine) return;
        const ouverture = await googleSheets.trouverOuCreer();
        if (!ouverture.cree) {
          const distant = await googleSheets.lireTaches();
          nombreIllisibles = distant.illisibles.length;
          const attente = new Set(file());
          const fusion = TACHES.map(tache => ({ ...tache }));
          const positions = new Map(fusion.map((tache, indice) => [tache.id, indice]));
          const distants = new Set(distant.taches.map(tache => tache.id));
          const proteges = new Set(distant.illisibles.map(ligne => ligne.id));
          for (const tache of distant.taches) {
            if (!positions.has(tache.id)) fusion.push({ ...tache });
            else if (!attente.has(tache.id)) fusion[positions.get(tache.id)] = { ...tache };
          }
          stockage.verifier(fusion);
          const absentes = TACHES.filter(tache => !distants.has(tache.id) && !proteges.has(tache.id)).map(tache => tache.id);
          ajouter(absentes);
          stockage.enregistrer(fusion);
          TACHES.splice(0, TACHES.length, ...fusion);
          window.dispatchEvent(new Event('cap-google-fusion'));
        }
        pret = true;
        erreurEtat = '';
      } catch (erreur) {
        erreurEtat = `Synchronisation interrompue : ${erreur instanceof TypeError ? 'connexion impossible' : erreur.message}. Aucune tâche locale n’a été retirée.`;
      }
    }).finally(() => {
      demarrage = null;
      publier();
    }).then(() => envoyer());
    return demarrage;
  }

  window.addEventListener('online', () => { if (pret) void envoyer(); else void demarrer(); });
  window.addEventListener('offline', publier);
  window.addEventListener('cap-google-deconnecte', () => { pret = false; publier(); });
  return { signaler, envoyer, demarrer, etat };
})();
