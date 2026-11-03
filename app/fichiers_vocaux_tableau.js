'use strict';

// Petits outils pour lire et écrire des tableaux Markdown rangés sous des titres "# Section"
// (utilisé par l'Échéancier et la liste À faire). Ne connaît aucune règle métier : seulement la
// mise en forme du texte. Jamais d'effacement : on ajoute, on déplace, on marque, jamais on retire
// une ligne sans la remettre ailleurs dans le même fichier.
const fichiersVocauxTableau = (() => {
  function echapperCellule(valeur) {
    return String(valeur ?? '').replace(/\|/g, '\\|').replace(/\r?\n/g, ' ').trim();
  }

  function ligneTableau(valeurs) {
    return `| ${valeurs.map(echapperCellule).join(' | ')} |`;
  }

  function enTete(colonnes) {
    return `${ligneTableau(colonnes)}\n${ligneTableau(colonnes.map(() => '---'))}`;
  }

  function sectionVide(titre, colonnes) {
    return `# ${titre}\n\n${enTete(colonnes)}\n`;
  }

  function construireFichier(sectionsSpec) {
    return sectionsSpec.map(section => sectionVide(section.titre, section.colonnes)).join('\n');
  }

  // Découpe le contenu en blocs { titre, debut, finEntete, fin } pour chaque "# Titre".
  function analyser(contenuBrut) {
    const texte = String(contenuBrut || '');
    const regex = /^#\s+(.+?)\s*$/gm;
    const matches = [...texte.matchAll(regex)];
    const blocs = matches.map((m, i) => ({
      titre: m[1],
      debut: m.index,
      finEntete: m.index + m[0].length,
      fin: i + 1 < matches.length ? matches[i + 1].index : texte.length
    }));
    return { texte, blocs };
  }

  function corpsSection(contenu, titre) {
    const { texte, blocs } = analyser(contenu);
    const bloc = blocs.find(b => b.titre === titre);
    return bloc ? texte.slice(bloc.finEntete, bloc.fin) : null;
  }

  function remplacerSection(contenu, titre, nouveauCorps) {
    const { texte, blocs } = analyser(contenu);
    const bloc = blocs.find(b => b.titre === titre);
    if (!bloc) {
      const base = texte && !texte.endsWith('\n') ? `${texte}\n` : texte;
      return `${base}\n# ${titre}\n${nouveauCorps}`;
    }
    return texte.slice(0, bloc.finEntete) + nouveauCorps + texte.slice(bloc.fin);
  }

  function estSeparateur(ligne) {
    const sansBarres = ligne.replace(/\|/g, '').trim();
    return sansBarres.length > 0 && /^[:\- ]+$/.test(sansBarres);
  }

  // Lignes de données d'une section (sans l'en-tête ni la ligne de tirets, qui sont les deux
  // premières lignes à commencer par "|").
  function lignesDonnees(corpsBrut) {
    const pipes = String(corpsBrut || '').split(/\r?\n/)
      .map(ligne => ligne.trim())
      .filter(ligne => ligne.startsWith('|'));
    const debutDonnees = pipes.length > 1 && estSeparateur(pipes[1]) ? 2 : pipes.length > 0 ? 1 : 0;
    return pipes.slice(debutDonnees);
  }

  function cellules(ligne) {
    const sansBords = ligne.trim().replace(/^\|/, '').replace(/\|$/, '');
    return sansBords.split('|').map(c => c.trim().replace(/\\\|/g, '|'));
  }

  // Ajoute une ligne à la fin des données d'une section (la crée si elle n'existe pas encore).
  function ajouterLigne(contenu, titre, colonnes, valeurs) {
    let corps = corpsSection(contenu, titre);
    if (corps === null) corps = `\n${enTete(colonnes)}\n`;
    const propre = corps.endsWith('\n') ? corps : `${corps}\n`;
    const nouveauCorps = `${propre}${ligneTableau(valeurs)}\n`;
    return remplacerSection(contenu, titre, nouveauCorps);
  }

  // Retire une ligne de données (par index parmi lignesDonnees) sans toucher à l'en-tête.
  function retirerLigneParIndex(corpsBrut, index) {
    const corps = String(corpsBrut || '');
    const lignesBrutes = corps.split(/\r?\n/);
    let comptePipe = -1;
    let compteDonnees = -1;
    const resultat = lignesBrutes.filter(ligne => {
      const propre = ligne.trim();
      if (!propre.startsWith('|')) return true;
      comptePipe += 1;
      if (comptePipe === 0) return true;
      if (comptePipe === 1 && estSeparateur(propre)) return true;
      compteDonnees += 1;
      return compteDonnees !== index;
    });
    return `${resultat.join('\n')}\n`;
  }

  return {
    ligneTableau, enTete, sectionVide, construireFichier,
    corpsSection, remplacerSection, lignesDonnees, cellules,
    ajouterLigne, retirerLigneParIndex
  };
})();
