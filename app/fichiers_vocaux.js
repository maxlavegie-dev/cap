'use strict';

// Comprend, en code pur (sans IA), les phrases qui visent un des "fichiers vocaux" du Drive
// (liste de courses, etc.) et transforme leur contenu Markdown. Aucune écriture Google ici :
// ce fichier ne fait que lire/transformer du texte, zéro perte (jamais d'effacement, seulement
// des marquages datés).

const fichiersVocaux = (() => {
  function deuxChiffres(valeur) {
    return String(valeur).padStart(2, '0');
  }

  function dateDuJour(maintenant = new Date()) {
    return `${deuxChiffres(maintenant.getDate())}/${deuxChiffres(maintenant.getMonth() + 1)}/${maintenant.getFullYear()}`;
  }

  function normaliser(texte) {
    return recherche.normaliser(texte).replace(/\s+/g, ' ').trim();
  }

  // "liste pommes, pain et lait" -> ["pommes", "pain", "lait"]
  function decouperProduits(texte) {
    return texte
      .split(/\s*,\s*|\s+et\s+/i)
      .map(mot => mot.trim())
      .filter(Boolean);
  }

  // Un mot déclencheur par fichier-liste : chacun est indépendant, pas de collision entre eux.
  const LISTES_SIMPLES = [
    { fichier: 'liste_courses', motif: /^liste\b/i, debut: /^liste\s*,?\s*/i },
    { fichier: 'choses_a_acheter', motif: /^achats\b/i, debut: /^achats\s*,?\s*/i },
    { fichier: 'films_a_voir', motif: /^films\b/i, debut: /^films\s*,?\s*/i },
    { fichier: 'livres_a_lire', motif: /^livres\b/i, debut: /^livres\s*,?\s*/i }
  ];

  function detecterCommande(texteBrut) {
    const texte = String(texteBrut || '').trim();
    const entree = LISTES_SIMPLES.find(item => item.motif.test(texte));
    if (!entree) return null;
    const reste = texte.replace(entree.debut, '').trim();
    if (/^lis[- ]?moi\b/i.test(reste)) return { type: 'lire', fichier: entree.fichier };
    const retire = /^retir[eé]\w*\s+(.+)/i.exec(reste);
    if (retire) return { type: 'retirer', fichier: entree.fichier, produit: retire[1].trim() };
    if (!reste) return null;
    const produits = decouperProduits(reste);
    return produits.length ? { type: 'ajouter', fichier: entree.fichier, produits } : null;
  }

  function ligneProduit(nom) {
    return `- ${nom}`;
  }

  function estLigneActive(ligne) {
    return /^-\s+\S/.test(ligne) && !/\(retiré le \d{2}\/\d{2}\/\d{4}\)\s*$/.test(ligne);
  }

  function nomLigne(ligne) {
    return ligne.replace(/^-\s+/, '').replace(/\s*\(retiré le \d{2}\/\d{2}\/\d{4}\)\s*$/, '').trim();
  }

  function elementsActifs(contenu) {
    return String(contenu || '').split(/\r?\n/).filter(estLigneActive).map(nomLigne);
  }

  function assurerFinLigne(contenu) {
    const propre = String(contenu || '');
    return propre && !propre.endsWith('\n') ? `${propre}\n` : propre;
  }

  // Ajoute chaque produit à la fin, sans jamais créer de doublon avec un élément déjà actif.
  function ajouterElements(contenu, produitsBruts) {
    const actifs = elementsActifs(contenu).map(normaliser);
    const ajoutes = [];
    const doublons = [];
    let texte = assurerFinLigne(contenu);
    for (const produit of produitsBruts) {
      const cle = normaliser(produit);
      if (!cle || actifs.includes(cle) || ajoutes.some(a => normaliser(a) === cle)) {
        if (cle) doublons.push(produit);
        continue;
      }
      texte += `${ligneProduit(produit)}\n`;
      ajoutes.push(produit);
    }
    return { contenu: texte, ajoutes, doublons };
  }

  // Ne supprime jamais la ligne : la marque comme retirée avec la date du jour (zéro perte).
  function retirerElement(contenu, produitBrut, maintenant = new Date()) {
    const cible = normaliser(produitBrut);
    const lignes = String(contenu || '').split(/\r?\n/);
    let trouve = '';
    const resultat = lignes.map(ligne => {
      if (trouve || !estLigneActive(ligne) || normaliser(nomLigne(ligne)) !== cible) return ligne;
      trouve = nomLigne(ligne);
      return `${ligne} (retiré le ${dateDuJour(maintenant)})`;
    });
    return { contenu: resultat.join('\n'), retire: Boolean(trouve), nom: trouve };
  }

  return {
    detecterCommande, ajouterElements, retirerElement, elementsActifs,
    ligneProduit, estLigneActive, nomLigne, dateDuJour, normaliser
  };
})();
