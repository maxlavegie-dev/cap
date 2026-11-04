'use strict';

// Dictée libre jusqu'à "terminé" (Bloc-notes, Brouillon vocal). Code pur, sans IA : ce fichier ne
// fait que reconnaître les phrases d'ouverture/fin et mettre en forme l'entrée. La session (ce qui
// a été dicté) est gardée par fichiers_vocaux_controleur.js, pas ici.
const fichiersVocauxNotes = (() => {
  const CATALOGUE = [
    { fichier: 'bloc_notes', motif: /^bloc[- ]notes?\b/i },
    { fichier: 'brouillon_vocal', motif: /^brouillon(?:\s+vocal)?\b/i }
  ];

  // "bloc-notes, note" ou "brouillon vocal, note" ouvre une session ; le reste est accumulé ensuite.
  function detecterOuverture(texteBrut) {
    const texte = String(texteBrut || '').trim();
    for (const entree of CATALOGUE) {
      if (!entree.motif.test(texte)) continue;
      const reste = texte.replace(entree.motif, '').replace(/^\s*,?\s*/, '');
      if (/^note\b/i.test(reste)) return { fichier: entree.fichier };
    }
    return null;
  }

  function estTerminer(texteBrut) {
    return /^\s*termin[eé]e?s?\s*\.?\s*$/i.test(String(texteBrut || ''));
  }

  // Coupe le mot "terminé" (et ce qu'il y a après) à la fin d'une phrase dictée, même s'il arrive
  // dans le même souffle que la fin de la dictée ("range le lait terminé"). Le mot "terminé" ne doit
  // JAMAIS se retrouver écrit dans la note : seul ce qui est dit AVANT lui est gardé.
  function decouperFin(texteBrut) {
    const texte = String(texteBrut || '').trim();
    const correspondance = /^(.*?)\s*,?\s*termin[eé]e?s?\s*\.?\s*$/i.exec(texte);
    if (!correspondance) return { avant: texte, termine: false };
    return { avant: correspondance[1].trim(), termine: true };
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
