'use strict';

// La clé de l'IA : tapée une seule fois par Max dans Cap, gardée seulement sur ce téléphone.
// Elle n'est jamais dans le code, jamais affichée en entier, jamais écrite dans le journal ni dans le tableau.
const cleIA = (() => {
  const cle = 'cap_cle_ia_v1';

  function lire() {
    try {
      return localStorage.getItem(cle) || '';
    } catch (erreur) {
      return '';
    }
  }

  function presente() {
    return Boolean(lire());
  }

  function enregistrer(valeur) {
    const texte = String(valeur || '').trim();
    if (!texte.startsWith(REGLAGES_IA.debut_cle) || texte.length < 30 || /\s/.test(texte)) {
      throw new Error(`Cette clé ne ressemble pas à une clé Claude (elle commence par « ${REGLAGES_IA.debut_cle} »). Rien n’a été enregistré.`);
    }
    try {
      localStorage.setItem(cle, texte);
    } catch (erreur) {
      throw new Error('La clé n’a pas pu être enregistrée sur ce téléphone.');
    }
  }

  function retirer() {
    try {
      localStorage.removeItem(cle);
    } catch (erreur) {
    }
  }

  // Seulement les 4 derniers caractères, pour que Max reconnaisse sa clé.
  function apercu() {
    const texte = lire();
    return texte ? `…${texte.slice(-4)}` : '';
  }

  return { lire, presente, enregistrer, retirer, apercu };
})();
