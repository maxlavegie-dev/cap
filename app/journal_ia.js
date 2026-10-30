'use strict';

// Historique des échanges avec l'IA payante : ce que Max a dit, ce que l'IA a répondu ou proposé, l'action demandée.
// Gardé sur le téléphone pour que Max puisse vérifier ; Max peut l'effacer d'un seul geste. La clé n'y est jamais écrite.
const journalIA = (() => {
  const cle = 'cap_journal_ia_v1';

  function court(valeur) {
    return String(valeur ?? '').replace(/\s+/g, ' ').trim().slice(0, 500);
  }

  function lire() {
    try {
      const entrees = JSON.parse(localStorage.getItem(cle));
      return Array.isArray(entrees) ? entrees.filter(entree => entree && typeof entree.heure === 'string' && typeof entree.dit === 'string') : [];
    } catch (erreur) {
      return [];
    }
  }

  function noter({ dit, repondu = '', action = '' }) {
    const entree = { heure: new Date().toISOString(), dit: court(dit), repondu: court(repondu), action: court(action) };
    try {
      localStorage.setItem(cle, JSON.stringify([entree, ...lire()].slice(0, REGLAGES_IA.journal_ia_maximum)));
    } catch (erreur) {
      return;
    }
  }

  function effacer() {
    try {
      localStorage.removeItem(cle);
    } catch (erreur) {
      return;
    }
  }

  return { lire, noter, effacer };
})();
