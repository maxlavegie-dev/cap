'use strict';

// 13/11/2026 (accord de Max, marche P2 de la copie des échanges du téléphone) : CLÉ DE CHAQUE EXPÉDITEUR.
// Une clé unique par expéditeur, sans doublon, qui décidera plus tard de son dossier. La clé est une EMPREINTE : jamais le
// numéro (ni le nom) en clair. Sortes :
//   - 'numero' : un même numéro écrit de plusieurs façons (+33, 06, espaces, tirets…) donne UNE seule clé (numeros.js) ;
//   - 'lettres' : expéditeur en lettres (banque, publicité), nom écrit de façon uniforme (majuscules, sans accents, espaces
//     simples) ; deux noms différents ne fusionnent jamais ;
//   - 'court' : numéro court (3 à 6 chiffres) ;
//   - 'masque' : numéro masqué ou absent : UNE seule clé « masque » ;
//   - 'nom' : un nom sans numéro ;
//   - 'groupe' : une clé par ENSEMBLE de participants (l'ordre ne compte pas) ;
//   - 'a-trier' : numéro présent sur deux fiches (ou plus), ou adresse illisible : « À trier ».
// L'empreinte est DONNÉE par l'appelant (dans Cap : celle de l'index des relations, clé secrète du téléphone ; dans les tests :
// une empreinte FICTIVE). Fonction PURE : pas de page, pas de réseau, pas de stockage, aucune sortie. Un message d'erreur ne
// contient jamais l'expéditeur.
const clesExpediteurs = (() => {
  const plier = t => String(t).normalize('NFD').replace(/[̀-ͯ]/g, '');
  const MASQUES = /^(?:|-1|-2|-3|0|null|undefined|unknown|inconnu|masque|masqué|private|prive|privé|insert-address-token)$/i;

  // Forme uniforme d'un expéditeur en lettres ou d'un nom : sans accents, majuscules, espaces simples, sans espace autour.
  function uniforme(texte) {
    return plier(texte).toUpperCase().replace(/[\s  ]+/g, ' ').trim();
  }

  // Classe une adresse SANS rien calculer : { sorte, valeur } (valeur = forme normalisée, gardée en mémoire seulement).
  function classer(adresse) {
    const brut = adresse === null || adresse === undefined ? '' : String(adresse).trim();
    if (MASQUES.test(brut)) return { sorte: 'masque', valeur: '' };
    if (/[A-Za-zÀ-ÿ]/.test(brut)) return { sorte: 'lettres', valeur: uniforme(brut) };
    const chiffres = brut.replace(/[\s.\-()  ]/g, '');
    if (/^\d{3,6}$/.test(chiffres)) return { sorte: 'court', valeur: chiffres };
    const n = typeof numeros !== 'undefined' ? numeros.normaliserNumero(brut) : null;
    if (n) return { sorte: 'numero', valeur: n };
    return { sorte: 'a-trier', valeur: '' };
  }

  async function empreinteSure(empreinte, texte) {
    if (typeof empreinte !== 'function') throw new Error('Clé d’expéditeur impossible : aucune fonction d’empreinte donnée.');
    let e;
    try { e = await empreinte(texte); } catch (erreur) { throw new Error('Clé d’expéditeur impossible : l’empreinte a échoué.'); }
    if (typeof e !== 'string' || !/^[0-9a-f]{16,}$/.test(e)) throw new Error('Clé d’expéditeur impossible : empreinte invalide.');
    return e;
  }

  // expediteur : { adresse } ou { nom } ; options : { empreinte(texte) → hex, personnesPour(numeroNormalise) → [identifiants] }.
  // Rend { sorte, cle } (cle = 'sorte:empreinte', ou 'masque', ou 'a-trier').
  async function cle(expediteur, { empreinte, personnesPour = null } = {}) {
    const ex = expediteur || {};
    if ((ex.adresse === undefined || ex.adresse === null || String(ex.adresse).trim() === '') && typeof ex.nom === 'string' && ex.nom.trim()) {
      return { sorte: 'nom', cle: `nom:${await empreinteSure(empreinte, `nom:${uniforme(ex.nom)}`)}` };
    }
    const c = classer(ex.adresse);
    if (c.sorte === 'masque') return { sorte: 'masque', cle: 'masque' };
    if (c.sorte === 'a-trier') return { sorte: 'a-trier', cle: 'a-trier' };
    if (c.sorte === 'numero' && typeof personnesPour === 'function') {
      let p = [];
      try { p = (await personnesPour(c.valeur)) || []; } catch (erreur) { p = []; } // 13/11/2026 (P3) : peut être asynchrone
      if (new Set(p).size > 1) return { sorte: 'a-trier', cle: 'a-trier' };
    }
    return { sorte: c.sorte, cle: `${c.sorte}:${await empreinteSure(empreinte, `${c.sorte}:${c.valeur}`)}` };
  }

  // participants : [{ adresse } ou { nom }] ; un seul participant distinct : sa clé ; plusieurs : une clé de groupe.
  async function cleGroupe(participants, options = {}) {
    const cles = [];
    for (const p of participants || []) {
      const r = await cle(p, options);
      if (r.sorte === 'masque' || r.sorte === 'a-trier') return { sorte: 'a-trier', cle: 'a-trier' };
      cles.push(r.cle);
    }
    const uniques = [...new Set(cles)].sort();
    if (!uniques.length) return { sorte: 'a-trier', cle: 'a-trier' };
    if (uniques.length === 1) return { sorte: cles.length ? (await cle(participants[0], options)).sorte : 'a-trier', cle: uniques[0] };
    return { sorte: 'groupe', cle: `groupe:${await empreinteSure(options.empreinte, `groupe:${uniques.join('|')}`)}` };
  }

  return Object.freeze({ cle, cleGroupe, uniforme });
})();
