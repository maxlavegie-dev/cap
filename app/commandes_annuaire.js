'use strict';

// Comprend, en code pur (sans IA), les commandes vocales qui visent l'annuaire :
// « montre-moi la fiche de X », « appelle X », « mail à X, message ». Les phrases d'ouverture
// viennent de phrases_modifiables.js (Max peut les ajouter/modifier dans « Mes phrases »).
// L'IA ne voit jamais ce fichier ni l'annuaire : la recherche se fait ici, avec la même règle
// que la barre de recherche (annuaire.correspondances).

const commandesAnnuaire = (() => {
  function texte(valeur) {
    return String(valeur || '').trim();
  }

  function detecter(texteBrut) {
    const brut = texte(texteBrut);
    if (!brut) return null;
    const etat = phrasesModifiablesEtat.obtenir();
    const trouve = phrasesModifiables.detecterCommande(etat, brut);
    if (!trouve) return null;
    if (trouve.rubrique === 'fiche_annuaire') {
      const nom = texte(trouve.reste);
      return nom ? { action: 'fiche', nom } : null;
    }
    if (trouve.rubrique === 'appel_annuaire') {
      const nom = texte(trouve.reste);
      return nom ? { action: 'appel', nom } : null;
    }
    if (trouve.rubrique === 'mail_annuaire') {
      const reste = trouve.reste;
      const virgule = reste.indexOf(',');
      const nom = texte(virgule === -1 ? reste : reste.slice(0, virgule));
      const message = virgule === -1 ? '' : texte(reste.slice(virgule + 1));
      return nom ? { action: 'mail', nom, message } : null;
    }
    return null;
  }

  // Même recherche que la barre de recherche de l'annuaire (surnoms compris, tirets/accents tolérés).
  function resoudreContact(nom) {
    const trouves = annuaire.correspondances(nom);
    if (trouves.length === 0) return { statut: 'aucun' };
    if (trouves.length === 1) return { statut: 'un', contact: trouves[0] };
    return { statut: 'plusieurs', contacts: trouves };
  }

  return { detecter, resoudreContact };
})();
if (typeof module !== 'undefined' && module.exports) module.exports = commandesAnnuaire;
