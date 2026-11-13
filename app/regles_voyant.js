'use strict';

// 10/11/2026 (accord de Max, CHANTIERS, séance 2 sur 7) : RÈGLES DU VOYANT CALCULÉ, toutes ici, et nulle part ailleurs.
// Ce fichier ne contient que des réglages : pour changer une règle (une couleur, une colonne, un nombre de jours, un statut),
// on change seulement ce fichier, en quelques minutes, sans toucher au code (chantiers.js les applique).
// Rappels de Max :
//  - la Liste des chantiers n'est JAMAIS modifiée : le voyant calculé est seulement montré à côté de la couleur écrite ;
//  - une date que Cap ne sait pas lire ne change pas la couleur (Cap dit seulement combien de chantiers en ont une) ;
//  - quand plusieurs règles s'appliquent, la plus grave gagne (rouge, puis orange, puis vert).
// Colonnes possibles : dateLimite (« Date limite »), dateProchaine (« Date de la prochaine action »), dateRetour (« Date de
// retour »). Moments possibles :
//  - 'passee'          : la date est avant aujourd'hui ;
//  - 'arrivee'         : la date est aujourd'hui ou avant ;
//  - 'dans_les_jours'  : la date est entre aujourd'hui et aujourd'hui + « jours » (bornes comprises).
// Une règle sans « statut » vaut pour les chantiers actifs (ni en veille, ni archivés) ; une règle avec « statut » ne vaut
// que pour ce statut. Les statuts sont comparés sans majuscules ni accents, par leur début (« archivé » = « Archivée »…).
const reglesVoyant = Object.freeze({
  // Aucune couleur calculée pour ces statuts.
  statutsSansCouleur: Object.freeze(['archivé']),
  // Pour ces statuts, seules les règles qui les nomment s'appliquent ; sinon, pas de couleur calculée.
  statutsEnVeille: Object.freeze(['en veille']),
  // Chantier actif sans aucune règle qui s'applique.
  couleurParDefaut: 'vert',
  regles: Object.freeze([
    // 1. Rouge : la date limite est passée.
    Object.freeze({ couleur: 'rouge', colonne: 'dateLimite', quand: 'passee' }),
    // 2. Orange : la date de la prochaine action, ou la date de retour, est arrivée.
    Object.freeze({ couleur: 'orange', colonne: 'dateProchaine', quand: 'arrivee' }),
    Object.freeze({ couleur: 'orange', colonne: 'dateRetour', quand: 'arrivee' }),
    // 3. Orange : la date limite tombe dans les 7 jours.
    Object.freeze({ couleur: 'orange', colonne: 'dateLimite', quand: 'dans_les_jours', jours: 7 }),
    // 4. En veille : pas de calcul, SAUF date limite passée : orange (jamais une couleur qui cache une alerte).
    Object.freeze({ couleur: 'orange', colonne: 'dateLimite', quand: 'passee', statut: 'en veille' })
  ])
});
