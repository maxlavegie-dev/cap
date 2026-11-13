'use strict';

// 12/11/2026 (accord de Max, c154, marche A3a de la « carte complète ») : COORDONNÉES DES RELATIONS, sur le téléphone seulement.
// CHANGEMENT DE RÈGLE VOULU PAR MAX : jusqu'ici, rien du Dictionnaire général n'était écrit sur le téléphone. Maintenant, pour
// chaque dossier « r_… » de « Relations » (compte Cap) dont la fiche est retrouvée dans l'onglet « Dictionnaire » (compte
// PERSONNEL de Max, lecture seule), TOUTES les cases remplies de sa ligne sont gardées dans une copie à part, famille comprise :
// les colonnes ajoutées plus tard au Dictionnaire y entrent seules, sans nouveau code. Seulement les personnes qui ont un
// dossier « r_… » (pas tout le Dictionnaire).
// - Lien ligne ↔ dossier : la MÊME règle que la création des dossiers (relations.calculer : « r_Prénom Nom », diminutif entre
//   parenthèses, sans accents ni majuscules) ; en secours, le prénom complet (sans la parenthèse). Deux fiches au même nom :
//   « homonymes », AUCUNE case gardée (Cap ne devine pas). Fiche introuvable (diminutif changé…) : « absente ».
// - Remplie par « Tout synchroniser » (synchro_tout.js) ; une lecture ratée garde l'ancienne copie.
// - Sans DOM. Jamais envoyé à l'IA, jamais écrit dans le Drive, jamais dans un journal : deux tests verrous le prouvent (liste des
//   seuls fichiers qui ont le droit de nommer ce module ; envois espionnés avec des données FICTIVES dans toutes les colonnes).
//   Aucun vrai nom dans le dépôt : les tests n'utilisent que des données FICTIVES.
const coordonneesRelations = (() => {
  const CLE = 'cap_coordonnees_relations_v1';
  const PREFIXE = 'r_';
  const cle = texte => String(texte || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
  const propre = texte => String(texte ?? '').replace(/\r\n?/g, '\n').trim();
  const enTete = texte => cle(texte).replace(/[^a-z ]/g, '').trim();
  function lettre(index) {
    let n = index + 1; let l = '';
    while (n) { const r = (n - 1) % 26; l = String.fromCharCode(65 + r) + l; n = Math.floor((n - 1) / 26); }
    return l;
  }

  // valeurs : toutes les lignes de l'onglet « Dictionnaire » (1re ligne = en-têtes) ; nomsDossiers : ['r_…'] ;
  // regle : relations.js (calculer). Retour : { version, quand, personnes: [{ cle, nomDossier, etat, champs | nombre }] }.
  function construire(valeurs, nomsDossiers, regle, maintenant = Date.now()) {
    const [entetes = [], ...lignes] = Array.isArray(valeurs) ? valeurs : [];
    const r = regle.calculer(valeurs);
    const parCle = new Map();
    for (const f of r.aCreer) parCle.set(f.cle, [f.numero]);
    for (const h of r.homonymesNoms || []) parCle.set(cle(h.nomDossier.slice(PREFIXE.length)), h.numeros.slice());
    // Secours : le prénom complet, sans la parenthèse du diminutif (« Prénom (Diminutif) » → « Prénom »).
    const col = nom => entetes.findIndex(e => enTete(e) === nom);
    const iPrenom = col('prenom'); const iNom = col('nom'); const iType = col('type');
    const secours = new Map();
    lignes.forEach((ligne, i) => {
      const type = cle(iType >= 0 ? ligne[iType] : '');
      const prenom = propre(iPrenom >= 0 ? ligne[iPrenom] : '').replace(/\s*\([^()]*\)\s*$/, '');
      const nom = propre(iNom >= 0 ? ligne[iNom] : '');
      if (!prenom || !nom || !type.startsWith('personne')) return;
      const c = cle(`${prenom} ${nom}`);
      if (!secours.has(c)) secours.set(c, []);
      secours.get(c).push(i + 2);
    });
    const largeur = Math.max(entetes.length, ...lignes.map(l => (Array.isArray(l) ? l.length : 0)));
    const champsDe = numero => {
      const ligne = lignes[numero - 2] || [];
      const champs = [];
      for (let j = 0; j < largeur; j++) {
        const valeur = propre(ligne[j]);
        if (valeur) champs.push({ titre: propre(entetes[j]) || `Colonne ${lettre(j)}`, valeur });
      }
      return champs;
    };
    const vus = new Set();
    const personnes = [];
    for (const nomDossier of Array.isArray(nomsDossiers) ? nomsDossiers : []) {
      if (!String(nomDossier || '').startsWith(PREFIXE)) continue;
      const c = cle(String(nomDossier).slice(PREFIXE.length));
      if (!c || vus.has(c)) continue;
      vus.add(c);
      const numeros = parCle.get(c) || secours.get(c) || [];
      if (numeros.length === 1) personnes.push({ cle: c, nomDossier: String(nomDossier), etat: 'trouve', champs: champsDe(numeros[0]) });
      else if (numeros.length > 1) personnes.push({ cle: c, nomDossier: String(nomDossier), etat: 'homonymes', nombre: numeros.length });
      else personnes.push({ cle: c, nomDossier: String(nomDossier), etat: 'absente' });
    }
    return { version: 1, quand: maintenant, personnes };
  }

  // Remplace la copie par une lecture complète réussie. Rend la copie gardée (ou null : rien de changé).
  function garder(stockage, valeurs, nomsDossiers, regle, maintenant = Date.now()) {
    if (!stockage || !regle || typeof regle.calculer !== 'function' || !Array.isArray(valeurs) || !Array.isArray(valeurs[0])) return null;
    const copie = construire(valeurs, nomsDossiers, regle, maintenant);
    try { stockage.setItem(CLE, JSON.stringify(copie)); } catch (erreur) { return null; } // mémoire pleine : l'ancienne reste
    return copie;
  }

  function lire(stockage) {
    if (!stockage) return null;
    try {
      const c = JSON.parse(stockage.getItem(CLE));
      return c && Array.isArray(c.personnes) ? c : null;
    } catch (erreur) { return null; }
  }

  // La fiche d'un dossier (« r_Prénom Nom » ou « Prénom Nom ») dans la copie, ou null.
  function pour(stockage, nom) {
    const copie = lire(stockage);
    if (!copie) return null;
    const n = String(nom || '');
    const c = cle(n.startsWith(PREFIXE) ? n.slice(PREFIXE.length) : n);
    return copie.personnes.find(p => p.cle === c) || null;
  }

  // Pour l'écran de « Tout synchroniser » : des NOMBRES seulement.
  function compter(copie) {
    const p = copie && Array.isArray(copie.personnes) ? copie.personnes : [];
    return { trouvees: p.filter(x => x.etat === 'trouve').length, homonymes: p.filter(x => x.etat === 'homonymes').length, absentes: p.filter(x => x.etat === 'absente').length };
  }

  return { CLE, construire, garder, lire, pour, compter };
})();
