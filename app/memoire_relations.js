'use strict';

// 12/11/2026 (accord de Max, c150, marche A1 de la « carte complète ») : MÉMOIRE DES RELATIONS, sur le téléphone seulement.
// Pour chaque dossier « r_… » de « Relations » (compte Cap) : son nom, son identifiant Drive, et l'identifiant de son journal
// (« Journaux des relations ») s'il existe. Rien n'est affiché ici : la carte de la recherche (A2) s'en servira.
// - Mise à jour à chaque lecture complète réussie (« Tout synchroniser », ouverture de « Journaux des relations ») : un dossier
//   créé plus tard apparaît après la synchro suivante, sans toucher au code.
// - Lecture ratée : l'ancienne mémoire est GARDÉE telle quelle (jamais vidée par une erreur).
// - Sans DOM. Jamais envoyé à l'IA, jamais écrit dans le Drive (un test vérifie que les fichiers de l'IA et la sauvegarde ne
//   lisent pas cette clé). Aucun vrai nom dans le dépôt : les tests n'utilisent que des noms FICTIFS.
const memoireRelations = (() => {
  const CLE = 'cap_memoire_relations_v1';
  const PREFIXE = 'r_';

  // relations : [{ id, nom: 'r_…' }] (journauxRelations.listerRelations) ;
  // journaux : Map identifiant du dossier → { id, … } (journauxRelations.journauxExistants).
  function construire(relations, journaux, maintenant = Date.now()) {
    const liste = (Array.isArray(relations) ? relations : [])
      .filter(r => r && r.id && String(r.nom || '').startsWith(PREFIXE))
      .map(r => {
        const j = journaux && typeof journaux.get === 'function' ? journaux.get(r.id) : null;
        return { nom: String(r.nom).slice(PREFIXE.length).trim(), nomDossier: String(r.nom), idDossier: String(r.id), idJournal: j && j.id ? String(j.id) : '' };
      });
    return { version: 1, quand: maintenant, relations: liste };
  }

  // Remplace la mémoire par une lecture complète. Rend la copie gardée (ou null si le téléphone refuse d'écrire).
  function garder(stockage, relations, journaux, maintenant = Date.now()) {
    const copie = construire(relations, journaux, maintenant);
    if (!stockage) return null;
    try { stockage.setItem(CLE, JSON.stringify(copie)); } catch (erreur) { return null; } // mémoire pleine : rien de cassé
    return copie;
  }

  function lire(stockage) {
    if (!stockage) return null;
    try {
      const c = JSON.parse(stockage.getItem(CLE));
      return c && Array.isArray(c.relations) ? c : null;
    } catch (erreur) { return null; }
  }

  return { CLE, construire, garder, lire };
})();
