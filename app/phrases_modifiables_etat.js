'use strict';

// Garde l'état courant de phrases_modifiables.js UNIQUEMENT sur ce téléphone (localStorage), jamais
// dans le dépôt, jamais envoyé à l'IA. Un seul but : fournir et sauvegarder cet état aux autres
// fichiers (fichiers_vocaux*.js, et plus tard l'écran "Mes phrases" des réglages).
const phrasesModifiablesEtat = (() => {
  const CLE = 'cap_phrases_modifiables';
  let etat = null;

  function obtenir() {
    if (etat) return etat;
    let brut = null;
    try { brut = typeof localStorage !== 'undefined' ? localStorage.getItem(CLE) : null; } catch (erreur) {}
    etat = brut ? phrasesModifiables.chargerJSON(brut).etat : phrasesModifiables.creerEtat();
    return etat;
  }

  function enregistrer(nouvelEtat) {
    etat = nouvelEtat;
    try {
      if (typeof localStorage !== 'undefined') localStorage.setItem(CLE, phrasesModifiables.exporterJSON(etat));
    } catch (erreur) {}
  }

  return { obtenir, enregistrer };
})();
if (typeof module !== 'undefined' && module.exports) module.exports = phrasesModifiablesEtat;
