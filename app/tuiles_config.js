'use strict';

// 12/11/2026 (accord de Max, c172, plan de l'agent 2 vérifié) : LES TUILES FIXES DE L'ÉCRAN « TOUT VOIR », À UN SEUL ENDROIT.
// Pour chaque tuile : son identifiant, son NOM affiché, son ORDRE (l'ordre de ce tableau), ce qu'elle COMPTE (« compteur » :
// nom d'un calcul d'app.js ; absent = pas de nombre) et ce qu'elle OUVRE (« ouvre » : « vue » = la vue du même nom, sinon le
// nom d'une action d'app.js). Les « fixes » viennent avant les catégories, les « finales » après.
// Les CATÉGORIES restent des données de Max (noms, couleurs, ordre modifiés dans Cap, listes_choix.js) : pas ici.
// Avant (jusqu'à c171) : titres et compteurs écrits dans app.js (afficherTuiles), actions dans une suite de « if » (ouvrirTuile).
const TUILES_CONFIG = Object.freeze({
  fixes: Object.freeze([
    Object.freeze({ id: 'actions', titre: 'Dernières actions', compteur: 'actions', ouvre: 'vue' }),
    Object.freeze({ id: 'rendez-vous', titre: 'Prochains rendez-vous', compteur: 'rendez-vous', ouvre: 'vue' }),
    Object.freeze({ id: 'aujourdhui', titre: 'Aujourd’hui', compteur: 'aujourdhui', ouvre: 'vue' }),
    Object.freeze({ id: 'annuaire', titre: 'Annuaire', compteur: 'annuaire', ouvre: 'annuaire' }),
    Object.freeze({ id: 'trier', titre: 'Trier', compteur: 'a-trier', ouvre: 'trier' })
  ]),
  finales: Object.freeze([
    Object.freeze({ id: 'tout', titre: 'Tout', compteur: 'tout', ouvre: 'vue' }),
    Object.freeze({ id: 'ajouter-categorie', titre: '+ Ajouter', ouvre: 'ajouter-categorie' }),
    Object.freeze({ id: 'modifier-categories', titre: 'Modifier', ouvre: 'modifier-categories' })
  ])
});
