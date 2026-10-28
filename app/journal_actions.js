'use strict';

const journalActions = (() => {
  const cle = 'cap_journal_actions_v1';
  const types = ['ajout', 'fait', 'remise à faire', 'abandon', 'remise'];

  function lire() {
    try {
      const entrees = JSON.parse(localStorage.getItem(cle));
      if (!Array.isArray(entrees)) return [];
      return entrees.filter(entree => entree && typeof entree.heure === 'string'
        && Number.isFinite(Date.parse(entree.heure)) && types.includes(entree.type)
        && typeof entree.texte === 'string').slice(0, 30)
        .map(({ heure, type, texte }) => ({ heure, type, texte }));
    } catch (erreur) {
      return [];
    }
  }

  function noter(type, texte) {
    try {
      if (!types.includes(type) || typeof texte !== 'string') return;
      const entrees = [{ heure: new Date().toISOString(), type, texte }, ...lire()].slice(0, 30);
      localStorage.setItem(cle, JSON.stringify(entrees));
    } catch (erreur) {
      return;
    }
  }

  return { noter, lire };
})();
