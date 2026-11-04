'use strict';

// La clé API du sélecteur Google (Picker) : tapée une seule fois par Max dans Cap, gardée
// seulement sur ce téléphone, dans les réglages. Jamais dans le code, jamais dans le dépôt.
const clePicker = (() => {
  const cle = 'cap_cle_picker_v1';

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
    if (!texte.startsWith('AIza') || texte.length < 30 || /\s/.test(texte)) {
      throw new Error('Cette clé ne ressemble pas à une clé API Google (elle commence par « AIza »). Rien n’a été enregistré.');
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
