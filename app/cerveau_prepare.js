'use strict';

// Fournisseur « réponses préparées » : gratuit, sans clé, tout se passe sur le téléphone.
// Il range une tâche seulement si la catégorie ou la sous-catégorie est NOMMÉE ; sinon elle va dans À trier.
// Si plusieurs catégories sont nommées, il pose une seule question au lieu de deviner.
const cerveauPrepare = (() => {
  const { plier, motifNom } = cerveau.texte;
  const VERBE = /^ *(?:cap +)?(?:ajoute|rajoute|inscris|ecris|note(?! +(?:de|des|du|d) ))(?: +moi)?(?: +(?:une|la|cette) +tache)? +/;
  const DANS = '(?:dans|en|a|au|pour)(?: +(?:la|ma|les|mes) +(?:categorie|liste|rubrique)s?)?';
  const LISTE = '(?:(?:a|dans) +(?:ma +(?:to +do|todo|liste)|a +trier))';
  const LIAISON_SOUS = '(?: *(?:sous +categorie|rubrique|dans))?';

  function cibles(contexte) {
    const liste = [];
    for (const { nom, sous_categories: sous = [] } of contexte.categories) {
      if (plier(nom).trim() === plier(contexte.a_trier).trim()) continue;
      const motifCategorie = motifNom(nom);
      if (motifCategorie) liste.push({ categorie: nom, sous_categorie: '', motif: motifCategorie });
      for (const nomSous of sous) {
        const motifSous = motifNom(nomSous);
        if (motifSous && !sousCategories.estAClasser(nomSous)) liste.push({ categorie: nom, sous_categorie: nomSous, motif: motifSous });
      }
    }
    return liste;
  }

  // Formes reconnues pour chaque cible : « Musique », « Musique Album A », « Album A ».
  function formes(cible, toutes) {
    if (cible.sous_categorie) return [{ ...cible, motif: cible.motif }];
    const resultat = [{ ...cible }];
    for (const sous of toutes.filter(item => item.sous_categorie && item.categorie === cible.categorie)) {
      resultat.push({ ...sous, motif: `${cible.motif}${LIAISON_SOUS} +${sous.motif}` });
    }
    return resultat;
  }

  function meilleure(trouvees) {
    if (!trouvees.length) return null;
    const longueur = Math.max(...trouvees.map(item => item.longueur));
    const longues = trouvees.filter(item => item.longueur === longueur);
    const categories = new Set(longues.map(item => item.categorie));
    return categories.size === 1 ? { ...longues[0], ambigues: [] } : { ambigues: longues };
  }

  // Désignation après le verbe : au début (« Ajoute dans Musique : … ») ou à la fin (« Ajoute … dans Musique »).
  function designation(plie, debut, toutes) {
    const reste = plie.slice(debut);
    const liste = new RegExp(`^${LISTE} +`).exec(reste);
    if (liste) return { categorie: '', sous_categorie: '', de: debut + liste[0].length, a: plie.length };
    const listeFin = new RegExp(` +${LISTE} *$`).exec(reste);
    if (listeFin) return { categorie: '', sous_categorie: '', de: debut, a: debut + listeFin.index };
    const auDebut = [];
    const aLaFin = [];
    for (const cible of toutes) {
      for (const forme of formes(cible, toutes)) {
        const tete = new RegExp(`^${DANS} +${forme.motif} +`).exec(reste);
        if (tete) auDebut.push({ ...forme, longueur: tete[0].trimEnd().length, de: debut + tete[0].length, a: plie.length });
        const queue = new RegExp(` +${DANS} +${forme.motif} *$`).exec(reste);
        if (queue) aLaFin.push({ ...forme, longueur: queue[0].trim().length, de: debut, a: debut + queue.index });
      }
    }
    return meilleure(auDebut) || meilleure(aLaFin);
  }

  // Sans désignation claire : les noms cités n'importe où dans la phrase.
  function nommees(plie, toutes) {
    const parCategorie = new Map();
    for (const cible of toutes) {
      if (!new RegExp(cible.motif).test(plie)) continue;
      if (!parCategorie.has(cible.categorie)) parCategorie.set(cible.categorie, new Set());
      if (cible.sous_categorie) parCategorie.get(cible.categorie).add(cible.sous_categorie);
    }
    return [...parCategorie].map(([categorie, sous]) => ({ categorie, sous_categorie: sous.size === 1 ? [...sous][0] : '' }));
  }

  function question(intitule, texte, candidats) {
    const parCategorie = new Map();
    for (const item of candidats) if (!parCategorie.has(item.categorie)) parCategorie.set(item.categorie, item);
    const choix = [...parCategorie.values()].slice(0, 3).map(item => ({
      libelle: item.categorie, categorie: item.categorie, sous_categorie: item.sous_categorie || ''
    }));
    return {
      type: 'question',
      question: `Je la range dans ${choix.map(item => item.libelle).join(' ou dans ')} ?`,
      action: 'ajouter_tache',
      base: { intitule, date_dite: texte },
      choix
    };
  }

  function nettoyer(intitule) {
    return intitule.replace(/^[\s:;,.\-–—›>]+/, '').replace(/[\s:;,\-–—›>]+$/, '');
  }

  function comprendre({ texte }, contexte) {
    const original = String(texte || '').trim();
    const plie = plier(original);
    const toutes = cibles(contexte);
    const verbe = VERBE.exec(plie);
    const action = (intitule, categorie = '', sousCategorie = '') => ({
      type: 'action',
      action: 'ajouter_tache',
      parametres: { intitule, categorie, sous_categorie: sousCategorie, date_dite: original }
    });
    if (verbe) {
      const trouvee = designation(plie, verbe[0].length, toutes);
      if (trouvee?.ambigues?.length) {
        return question(original, original, trouvee.ambigues);
      }
      if (trouvee) {
        const intitule = nettoyer(original.slice(trouvee.de, trouvee.a));
        if (intitule) return action(intitule, trouvee.categorie, trouvee.sous_categorie);
      }
    }
    const candidats = nommees(plie, toutes);
    if (candidats.length > 1) return question(original, original, candidats);
    if (candidats.length === 1) return action(original, candidats[0].categorie, candidats[0].sous_categorie);
    const indiques = parIndices(original, contexte);
    if (indiques.length > 1) return question(original, original, indiques);
    if (indiques.length === 1) return action(original, indiques[0].categorie, indiques[0].sous_categorie);
    return action(original);
  }

  // Rien de nommé : indices évidents (« scène » → Scénarios, « chapitre » → Roman). Plusieurs dans une catégorie : À classer.
  function parIndices(original, contexte) {
    const resultat = [];
    for (const { nom, sous_categories: sous = [] } of contexte.categories) {
      if (plier(nom).trim() === plier(contexte.a_trier).trim()) continue;
      const trouvees = sousCategories.parIndices(original, sous.filter(item => !sousCategories.estAClasser(item)));
      if (trouvees.length) resultat.push({ categorie: nom, sous_categorie: trouvees.length === 1 ? trouvees[0] : sousCategories.A_CLASSER });
    }
    return resultat;
  }

  const fournisseur = { nom: 'réponses préparées', payant: false, comprendre };
  cerveau.enregistrerFournisseur('prepare', fournisseur);
  return fournisseur;
})();
