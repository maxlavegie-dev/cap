// Service worker : garde une copie de l'appli pour l'ouvrir même sans internet.
// Stratégie : réseau d'abord (nouvelles versions immédiates), copie en cache si hors connexion.
const VERSION_CACHE = 'cap-v9';
const FICHIERS_PRECACHE = [
  "./",
  "index.html",
  "style.css",
  "donnees_fictives.js",
  "etapes_par_defaut.js",
  "stockage.js",
  "taches.js",
  "listes_choix.js",
  "reglages_google.js",
  "google_connexion.js",
  "google_sheets.js",
  "google_agenda.js",
  "synchronisation.js",
  "dictee.js",
  "phrases_clavier.js",
  "preferences_clavier.js",
  "comprendre_demande.js",
  "demandes.js",
  "recherche.js",
  "journal_actions.js",
  "fiche_rendezvous.js",
  "choix_dates.js",
  "fenetres_listes.js",
  "synchro_listes.js",
  "app.js",
  "installation.js",
  "service-worker.js",
  "manifest.webmanifest",
  "icones/icone-192.png",
  "icones/icone-512.png",
  "icones/icone-maskable-512.png",
  "icones/favicon.png"
];
const URLS_PRECACHE = new Set(FICHIERS_PRECACHE.map(chemin => new URL(chemin, self.registration.scope).href));

self.addEventListener('install', evenement => {
  evenement.waitUntil((async () => {
    const cache = await caches.open(VERSION_CACHE);
    await cache.addAll(FICHIERS_PRECACHE.map(chemin => new Request(
      new URL(chemin, self.registration.scope), { cache: 'reload' }
    )));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', evenement => {
  evenement.waitUntil((async () => {
    const noms = await caches.keys();
    await Promise.all(noms.filter(nom => nom.startsWith('cap-') && nom !== VERSION_CACHE)
      .map(nom => caches.delete(nom)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', evenement => {
  const requete = evenement.request;
  const url = new URL(requete.url);
  if (requete.method !== 'GET' || url.origin !== self.location.origin || !URLS_PRECACHE.has(url.href)) return;

  evenement.respondWith((async () => {
    const cache = await caches.open(VERSION_CACHE);
    let reponse;
    try {
      reponse = await fetch(requete, { cache: 'no-cache' });
    } catch (erreur) {
      const sauvegarde = await cache.match(requete);
      if (sauvegarde) return sauvegarde;
      return Response.error();
    }
    if (reponse.ok && reponse.type === 'basic' && !reponse.redirected) {
      try {
        await cache.put(requete, reponse.clone());
      } catch (erreur) {
      }
    }
    if (!reponse.ok) {
      const sauvegarde = await cache.match(requete);
      if (sauvegarde) return sauvegarde;
    }
    return reponse;
  })());
});
