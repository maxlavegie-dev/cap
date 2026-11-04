'use strict';

// Comprend les phrases "à faire ...", "ma to-do ...", "il faut que je ...", "rappelle-moi de ..."
// (code pur, sans IA) et tient à jour le tableau Markdown "À faire". C'est un fichier DISTINCT du
// tableau de tâches FICTIF déjà géré par taches.js/stockage.js : rien n'est mélangé entre les deux.
// Jamais d'effacement : coche et retrait sont des marquages, jamais une suppression.
const fichiersVocauxAFaire = (() => {
  const SECTION = 'Tâches';
  const COLONNES = ['Terminée ?', 'Domaine', 'Projet', 'Élément', 'Personne concernée', 'Tâche',
    'Priorité', "Date d'inscription", 'Jours restants', "Date d'échéance", 'Notes / contexte'];

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

  function joursRestants(iso, maintenant = new Date()) {
    if (!iso) return '';
    const aujourdhui = new Date(maintenant.getFullYear(), maintenant.getMonth(), maintenant.getDate(), 12);
    const cible = new Date(`${iso}T12:00:00`);
    return String(Math.round((cible - aujourdhui) / 86400000));
  }

  function normaliser(texte) {
    return recherche.normaliser(String(texte || '')).replace(/\s+/g, ' ').trim();
  }

  // La phrase qui ouvre "à faire" vient de phrases_modifiables.js (rubrique "a_faire") : Max peut
  // l'ajouter/modifier/retirer dans les réglages, sans toucher au code.
  function detecterCommande(texteBrut, maintenant = new Date()) {
    const texte = String(texteBrut || '').trim();
    const ouverture = phrasesModifiables.detecterCommande(phrasesModifiablesEtat.obtenir(), texte);
    if (!ouverture || ouverture.rubrique !== 'a_faire') return null;
    const reste = ouverture.reste;
    if (!reste) return null;
    if (/^lis[- ]?moi\b/i.test(reste)) return { type: 'lire' };
    const coche = /^coche\s+(.+)/i.exec(reste);
    if (coche) return { type: 'coche', element: coche[1].trim() };
    const retire = /^retir[eé]\w*\s+(.+)/i.exec(reste);
    if (retire) return { type: 'retirer', element: retire[1].trim() };

    const priorite = /\b(?:urgent|urgente|prioritaire)\b/i.test(reste) ? 'Haute' : '';
    const trouve = comprendreDates.trouver(reste, maintenant);
    const dateIso = trouve.date || (trouve.choix && trouve.choix[0]) || '';
    let tache = reste;
    if (trouve.morceau) tache = tache.replace(trouve.morceau, ' ');
    tache = tache.replace(/\b(?:urgent|urgente|prioritaire)\b/gi, ' ').replace(/\s*,\s*/g, ', ').replace(/\s+/g, ' ').trim();
    tache = tache.replace(/^,\s*/, '').replace(/,\s*$/, '');
    if (!tache) return null;

    return {
      type: 'ajouter', tache, priorite,
      date: dateIso, dateLisible: isoVersLisible(dateIso), joursRestants: dateIso ? joursRestants(dateIso, maintenant) : ''
    };
  }

  function ligneTache(commande, maintenant = new Date()) {
    return [
      '', '', '', '', 'Max', commande.tache, commande.priorite,
      dateDuJour(maintenant), commande.joursRestants, commande.dateLisible, ''
    ];
  }

  function estCochee(valeur) {
    return /^(?:x|✓|oui|vrai)$/i.test(String(valeur || '').trim());
  }

  function estRetiree(valeurTache) {
    return /\(retiré(?:e)? le \d{2}\/\d{2}\/\d{4}\)\s*$/.test(String(valeurTache || ''));
  }

  function fichierVide() {
    return fichiersVocauxTableau.sectionVide(SECTION, COLONNES);
  }

  function ajouter(contenu, commande, maintenant = new Date()) {
    const base = contenu && contenu.trim() ? contenu : fichierVide();
    return { contenu: fichiersVocauxTableau.ajouterLigne(base, SECTION, COLONNES, ligneTache(commande, maintenant)) };
  }

  function modifierLigne(contenu, elementBrut, transformer) {
    const cible = normaliser(elementBrut);
    const corps = fichiersVocauxTableau.corpsSection(contenu, SECTION);
    if (corps === null) return { contenu, trouve: false, element: '' };
    const lignes = fichiersVocauxTableau.lignesDonnees(corps);
    const index = lignes.findIndex(ligne => normaliser(fichiersVocauxTableau.cellules(ligne)[5]) === cible);
    if (index === -1) return { contenu, trouve: false, element: '' };
    const valeurs = fichiersVocauxTableau.cellules(lignes[index]);
    const nouvellesValeurs = transformer([...valeurs]);
    const corpsSansLigne = fichiersVocauxTableau.retirerLigneParIndex(corps, index);
    const resultatContenu = fichiersVocauxTableau.ajouterLigne(
      fichiersVocauxTableau.remplacerSection(contenu, SECTION, corpsSansLigne), SECTION, COLONNES, nouvellesValeurs);
    return { contenu: resultatContenu, trouve: true, element: valeurs[5] };
  }

  // Coche sans supprimer (zéro perte) : met "x" dans "Terminée ?".
  function coche(contenu, elementBrut) {
    return modifierLigne(contenu, elementBrut, valeurs => {
      valeurs[0] = 'x';
      return valeurs;
    });
  }

  // Retire sans effacer : marque la tâche avec la date du jour (zéro perte).
  function retirer(contenu, elementBrut, maintenant = new Date()) {
    return modifierLigne(contenu, elementBrut, valeurs => {
      valeurs[5] = `${valeurs[5]} (retirée le ${dateDuJour(maintenant)})`;
      return valeurs;
    });
  }

  function lireActives(contenu) {
    const corps = fichiersVocauxTableau.corpsSection(contenu, SECTION);
    if (corps === null) return [];
    return fichiersVocauxTableau.lignesDonnees(corps)
      .map(ligne => fichiersVocauxTableau.cellules(ligne))
      .filter(c => !estCochee(c[0]) && !estRetiree(c[5]))
      .map(c => ({ tache: c[5], priorite: c[6], joursRestants: c[8] === '' ? Infinity : Number(c[8]) }))
      .sort((a, b) => {
        if ((a.priorite === 'Haute') !== (b.priorite === 'Haute')) return a.priorite === 'Haute' ? -1 : 1;
        return a.joursRestants - b.joursRestants;
      });
  }

  return { detecterCommande, ajouter, coche, retirer, lireActives, SECTION, COLONNES };
})();
