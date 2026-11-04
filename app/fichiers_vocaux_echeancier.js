'use strict';

// Comprend les phrases "échéance ..." (code pur, sans IA) et tient à jour le tableau Markdown de
// l'Échéancier (deux sections : "À venir" et "Terminées"). Jamais d'effacement : une échéance
// terminée est déplacée, avec sa date, dans "Terminées".
const fichiersVocauxEcheancier = (() => {
  const SECTION_A_VENIR = 'À venir';
  const SECTION_TERMINEES = 'Terminées';
  const COLONNES = ['Échéance', 'Date', 'Date approximative', 'Type', 'Personne ou organisme concerné',
    'Délai de rappel', 'Date du rappel', 'Note', 'Ajoutée le'];
  const COLONNES_TERMINEES = [...COLONNES, 'Terminée le'];
  const DELAI_PAR_DEFAUT = 30;

  function deuxChiffres(valeur) {
    return String(valeur).padStart(2, '0');
  }

  function dateDuJour(maintenant = new Date()) {
    return `${deuxChiffres(maintenant.getDate())}/${deuxChiffres(maintenant.getMonth() + 1)}/${maintenant.getFullYear()}`;
  }

  function isoVersLisible(iso) {
    if (!iso) return '';
    const [annee, mois, jour] = iso.split('-');
    return `${jour}/${mois}/${annee}`;
  }

  function moinsJours(iso, jours) {
    const date = new Date(`${iso}T12:00:00`);
    date.setDate(date.getDate() - jours);
    return `${date.getFullYear()}-${deuxChiffres(date.getMonth() + 1)}-${deuxChiffres(date.getDate())}`;
  }

  function normaliser(texte) {
    return recherche.normaliser(String(texte || '')).replace(/\s+/g, ' ').trim();
  }

  // "échéance anniversaire de Léa le 8 mars, rappel 15 jours avant" -> {element, date, delaiJours}
  // La phrase qui ouvre "échéance" vient de phrases_modifiables.js (rubrique "echeancier") : Max
  // peut l'ajouter/modifier/retirer dans les réglages, sans toucher au code.
  function detecterCommande(texteBrut, maintenant = new Date()) {
    const texte = String(texteBrut || '').trim();
    const ouverture = phrasesModifiables.detecterCommande(phrasesModifiablesEtat.obtenir(), texte);
    if (!ouverture || ouverture.rubrique !== 'echeancier') return null;
    const reste = ouverture.reste;
    if (!reste) return null;
    if (/^lis[- ]?moi\b/i.test(reste)) return { type: 'lire' };
    const terminer = /^termin[eé]e?\s+(.+)/i.exec(reste);
    if (terminer) return { type: 'terminer', element: terminer[1].trim() };

    const pasDeRappel = /\b(?:pas\s+(?:de\s+)?rappel|sans\s+rappel|aucun\s+rappel)\b/i.test(reste);
    const delaiMatch = /\b(?:dans|rappel(?:\s+de)?)\s+(\d{1,3})\s+jours?\s*(?:avant)?\b/i.exec(reste);
    const delaiJours = pasDeRappel ? null : delaiMatch ? Number(delaiMatch[1]) : DELAI_PAR_DEFAUT;

    let texteSansDelai = reste;
    if (delaiMatch) texteSansDelai = texteSansDelai.replace(delaiMatch[0], ' ');
    if (pasDeRappel) {
      texteSansDelai = texteSansDelai.replace(/\b(?:pas\s+(?:de\s+)?rappel|sans\s+rappel|aucun\s+rappel)\b/i, ' ');
    }

    const trouve = comprendreDates.trouver(texteSansDelai, maintenant);
    const dateIso = trouve.date || (trouve.choix && trouve.choix[0]) || '';
    if (!dateIso) return null;
    const element = texteSansDelai.replace(trouve.morceau, ' ').replace(/\s*,\s*$/, '').replace(/\s+/g, ' ').trim();
    if (!element) return null;

    return {
      type: 'ajouter', element, date: dateIso, dateLisible: isoVersLisible(dateIso),
      delaiJours, dateRappel: delaiJours === null ? '' : moinsJours(dateIso, delaiJours)
    };
  }

  function ligneAVenir(commande, maintenant = new Date()) {
    return [
      commande.element, commande.dateLisible, '', '', '',
      commande.delaiJours === null ? 'Aucun' : `${commande.delaiJours} jours`,
      commande.dateRappel ? isoVersLisible(commande.dateRappel) : '',
      '', dateDuJour(maintenant)
    ];
  }

  function fichierVide() {
    return fichiersVocauxTableau.construireFichier([
      { titre: SECTION_A_VENIR, colonnes: COLONNES },
      { titre: SECTION_TERMINEES, colonnes: COLONNES_TERMINEES }
    ]);
  }

  function ajouter(contenu, commande, maintenant = new Date()) {
    const base = contenu && contenu.trim() ? contenu : fichierVide();
    return { contenu: fichiersVocauxTableau.ajouterLigne(base, SECTION_A_VENIR, COLONNES, ligneAVenir(commande, maintenant)) };
  }

  // Déplace la ligne de "À venir" vers "Terminées" avec la date du jour (zéro perte : rien n'est effacé).
  function terminer(contenu, elementBrut, maintenant = new Date()) {
    const cible = normaliser(elementBrut);
    const corps = fichiersVocauxTableau.corpsSection(contenu, SECTION_A_VENIR);
    if (corps === null) return { contenu, trouve: false, element: '' };
    const lignes = fichiersVocauxTableau.lignesDonnees(corps);
    const index = lignes.findIndex(ligne => normaliser(fichiersVocauxTableau.cellules(ligne)[0]) === cible);
    if (index === -1) return { contenu, trouve: false, element: '' };
    const valeurs = fichiersVocauxTableau.cellules(lignes[index]);
    const corpsSansLigne = fichiersVocauxTableau.retirerLigneParIndex(corps, index);
    let resultatContenu = fichiersVocauxTableau.remplacerSection(contenu, SECTION_A_VENIR, corpsSansLigne);
    resultatContenu = fichiersVocauxTableau.ajouterLigne(resultatContenu, SECTION_TERMINEES, COLONNES_TERMINEES,
      [...valeurs, dateDuJour(maintenant)]);
    return { contenu: resultatContenu, trouve: true, element: valeurs[0] };
  }

  function lireAVenir(contenu) {
    const corps = fichiersVocauxTableau.corpsSection(contenu, SECTION_A_VENIR);
    if (corps === null) return [];
    return fichiersVocauxTableau.lignesDonnees(corps)
      .map(ligne => fichiersVocauxTableau.cellules(ligne))
      .map(c => ({ element: c[0], dateLisible: c[1], dateTri: `${c[1].split('/').reverse().join('-')}` }))
      .sort((a, b) => a.dateTri.localeCompare(b.dateTri));
  }

  return {
    detecterCommande, ajouter, terminer, lireAVenir,
    SECTION_A_VENIR, SECTION_TERMINEES, COLONNES, COLONNES_TERMINEES
  };
})();
