'use strict';

// Réglages de la connexion Google. L'identifiant client est public : il n'y a AUCUN secret ici.
// Le code secret du client ne doit jamais être mis dans ce projet.
const REGLAGES_GOOGLE = Object.freeze({
  id_client: '76369259152-qa9lvi5i0oll867nogo7p6jsnq2jod1g.apps.googleusercontent.com',
  adresse_retour: 'https://maxlavegie-dev.github.io/cap/app/',
  autorisations: Object.freeze([
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/calendar.app.created'
  ]),
  nom_fichier_taches: 'Cap – FICTIF – Tâches',
  onglets: Object.freeze({
    taches: 'Tâches',
    etapes_par_defaut: 'Étapes par défaut',
    phrases_clavier: 'Phrases du clavier',
    categories: 'Catégories',
    journal: 'Journal',
    annuaire: 'Annuaire'
  }),
  dossier_sauvegardes: 'Cap – FICTIF – Sauvegardes',
  sauvegardes_a_garder: 5,
  dossier_archives: 'ARCHIVES_PERSONNELLES - FICTIF',
  dossier_a_classer: '00_A_CLASSER',
  nom_agenda: 'Cap – FICTIF',
  dossier_fichiers_vocaux: 'Fichiers vocaux',
  fichiers_vocaux: Object.freeze({
    liste_courses: 'Liste de courses.md',
    choses_a_acheter: 'Choses à acheter.md',
    films_a_voir: 'Films à voir.md',
    livres_a_lire: 'Livres à lire.md',
    bloc_notes: 'Bloc-notes.md',
    brouillon_vocal: 'Brouillon vocal.md',
    echeancier: 'Échéancier.md',
    a_faire: 'À faire.md'
  })
});
