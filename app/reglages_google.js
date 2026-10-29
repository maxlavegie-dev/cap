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
    categories: 'Catégories'
  }),
  nom_agenda: 'Cap – FICTIF'
});
