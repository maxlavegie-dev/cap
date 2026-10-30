'use strict';

// Réglages de l'IA de Cap. Aucun secret ici : la clé de Max est tapée dans Cap et reste sur son téléphone.
const REGLAGES_IA = {
  nom: 'Claude Haiku',
  modele: 'claude-haiku-4-5',
  adresse: 'https://api.anthropic.com/v1/messages',
  version_api: '2023-06-01',
  debut_cle: 'sk-ant-',
  fichier_consignes: 'consignes_cap.txt',
  marqueur_brouillon: 'BROUILLON',
  limite_par_defaut: 60,
  limite_maximum: 1000,
  plafond_mensuel_par_defaut: 4,
  fiche_maximum_caracteres: 20000,
  plafond_mensuel_maximum: 1000,
  attente_consignes_ms: 1500,
  journal_ia_maximum: 200,
  reponse_max_jetons: 300,
  echanges_retenus: 6,
  delai_ms: 20000,
  dollars_par_million_entree: 1,
  dollars_par_million_sortie: 5,
  euros_par_dollar: 0.92
};
