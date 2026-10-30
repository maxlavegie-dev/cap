'use strict';

// Indices évidents pour ranger une phrase dans une sous-catégorie, quelle que soit sa catégorie.
// Clé : le nom de la sous-catégorie ; valeur : les mots ou titres qui la désignent clairement.
// Singulier, pluriel, accents et majuscules sont tolérés. Si deux sous-catégories sont désignées, rien n'est deviné.
const INDICES_RANGEMENT = {
  'Scénarios': ['scène', 'séquence', 'dialogue', 'scénario'],
  'Roman': ['chapitre', 'personnage', 'roman', 'Les jardins suspendus de minuit']
};
