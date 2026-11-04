'use strict';

// Dictée libre jusqu'à "terminé" (Bloc-notes, Brouillon vocal). Code pur, sans IA : ce fichier ne
// fait que reconnaître les phrases d'ouverture/fin et mettre en forme l'entrée. La session (ce qui
// a été dicté) est gardée par fichiers_vocaux_controleur.js, pas ici.
const fichiersVocauxNotes = (() => {
  // "bloc-notes, note" ou "brouillon vocal, note" ouvre une session ; le reste est accumulé ensuite.
  // Les phrases "bloc-notes" / "brouillon vocal" et le mot d'action "note" viennent de
  // phrases_modifiables.js : Max peut les ajouter/modifier/retirer dans les réglages, sans toucher
  // au code.
  function detecterOuverture(texteBrut) {
    const texte = String(texteBrut || '').trim();
    const etat = phrasesModifiablesEtat.obtenir();
    const trouve = phrasesModifiables.detecterCommande(etat, texte);
    if (!trouve || (trouve.rubrique !== 'bloc_notes' && trouve.rubrique !== 'brouillon_vocal')) return null;
    const action = phrasesModifiables.detecterAction(etat, trouve.reste);
    if (!action || action.rubrique !== 'action_note') return null;
    return { fichier: trouve.rubrique };
  }

  function estTerminer(texteBrut) {
    return phrasesModifiables.estExactement(phrasesModifiablesEtat.obtenir(), 'action_terminer', texteBrut);
  }

  function normaliserMot(mot) {
    return mot.toLowerCase().normalize('NFD').replace(/\p{M}/gu, '');
  }

  function jetons(texte) {
    const resultat = [];
    const motif = /[\p{L}\p{N}]+/gu;
    const source = String(texte || '');
    let trouve;
    while ((trouve = motif.exec(source)) !== null) {
      resultat.push({ mot: normaliserMot(trouve[0]), debut: trouve.index, fin: trouve.index + trouve[0].length });
    }
    return resultat;
  }

  // Trouve, parmi les phrases actives de "terminer" (phrases_modifiables.js), la plus longue qui
  // termine exactement le texte (mot entier par mot entier).
  function correspondanceFin(texte) {
    const mots = jetons(texte);
    if (!mots.length) return null;
    const phrases = phrasesModifiables.phrasesActives(phrasesModifiablesEtat.obtenir(), 'action_terminer');
    let meilleur = null;
    for (const phrase of phrases) {
      const motsPhrase = jetons(phrase);
      if (!motsPhrase.length || motsPhrase.length > mots.length) continue;
      const debutComparaison = mots.length - motsPhrase.length;
      const correspond = motsPhrase.every((jeton, i) => jeton.mot === mots[debutComparaison + i].mot);
      if (correspond && (!meilleur || motsPhrase.length > meilleur.longueur)) {
        meilleur = { debut: mots[debutComparaison].debut, longueur: motsPhrase.length };
      }
    }
    return meilleur;
  }

  // Coupe le mot "terminé" (et ce qu'il y a après) à la fin d'une phrase dictée, même s'il arrive
  // dans le même souffle que la fin de la dictée ("range le lait terminé"). Le mot "terminé" ne doit
  // JAMAIS se retrouver écrit dans la note : seul ce qui est dit AVANT lui est gardé.
  function decouperFin(texteBrut) {
    const texte = String(texteBrut || '').trim();
    const trouve = correspondanceFin(texte);
    if (!trouve) return { avant: texte, termine: false };
    const avant = texte.slice(0, trouve.debut).replace(/[\s,;:.!?\-–—]+$/u, '').trim();
    return { avant, termine: true };
  }

  function deuxChiffres(valeur) {
    return String(valeur).padStart(2, '0');
  }

  function dateHeure(maintenant = new Date()) {
    return `${deuxChiffres(maintenant.getDate())}/${deuxChiffres(maintenant.getMonth() + 1)}/${maintenant.getFullYear()} `
      + `${deuxChiffres(maintenant.getHours())}:${deuxChiffres(maintenant.getMinutes())}`;
  }

  // Titre court automatique : début de la première phrase, sans dépasser 60 caractères.
  function titreCourt(contenuBrut) {
    const propre = String(contenuBrut || '').trim().replace(/\s+/g, ' ');
    if (!propre) return 'Note';
    const premierePhrase = (propre.split(/(?<=[.!?])\s+/)[0] || propre).trim();
    const mots = premierePhrase.split(' ');
    let titre = mots.slice(0, 8).join(' ');
    if (mots.length > 8 || titre.length < propre.length) titre += '…';
    return titre.length > 60 ? `${titre.slice(0, 57)}…` : titre;
  }

  // Ajoute une entrée à la fin, sans jamais toucher à ce qui existe déjà (zéro perte).
  function ajouterEntree(contenu, titre, texte, maintenant = new Date()) {
    const base = String(contenu || '');
    const propre = base && !base.endsWith('\n') ? `${base}\n` : base;
    return `${propre}\n## ${dateHeure(maintenant)} — ${titre}\n\n${texte}\n`;
  }

  return { detecterOuverture, estTerminer, decouperFin, titreCourt, ajouterEntree, dateHeure };
})();
