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

  // Une conversation par ouverture de Cap : elle est repérée par l'heure de son début.
  let conversation = new Date().toISOString();

  function nouvelleConversation() {
    conversation = new Date().toISOString();
    return conversation;
  }

  function noter({ dit, repondu = '', action = '' }) {
    const entree = { heure: new Date().toISOString(), conversation, dit: court(dit), repondu: court(repondu), action: court(action) };
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

  // Les échanges regroupés par conversation, la plus récente d'abord ; dans chacune, les échanges dans l'ordre où ils ont eu lieu.
  function conversations() {
    const groupes = new Map();
    lire().forEach(entree => {
      const debut = typeof entree.conversation === 'string' ? entree.conversation : entree.heure;
      if (!groupes.has(debut)) groupes.set(debut, []);
      groupes.get(debut).unshift(entree);
    });
    return [...groupes].map(([debut, echanges]) => ({ debut, echanges }))
      .sort((a, b) => b.debut.localeCompare(a.debut));
  }

  return { lire, noter, effacer, conversations, nouvelleConversation };
})();
