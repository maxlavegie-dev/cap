'use strict';

// Trouve la sous-catégorie d'une phrase dictée dans une catégorie, sans jamais deviner.
// Si rien n'est clair, la tâche va dans « À classer » de cette catégorie.
const sousCategories = (() => {
  const A_CLASSER = 'À classer';
  const MOTS_COMMUNS_MINIMUM = 2;
  const motsVides = new Set([
    'pour', 'dans', 'avec', 'sans', 'sous', 'chez', 'entre', 'vers', 'mais', 'plus', 'moins', 'tout', 'toute', 'tous',
    'toutes', 'cette', 'celui', 'celle', 'ceux', 'sont', 'avoir', 'etre', 'elle', 'elles', 'nous', 'vous', 'leur',
    'quoi', 'quand', 'comme', 'aussi', 'encore', 'tres', 'bien', 'alors', 'donc', 'aide', 'aider', 'faire', 'penser',
    'commencer', 'finir', 'continuer', 'nouveau', 'nouvelle', 'nouvel', 'autre', 'autres', 'idee', 'chose', 'truc',
    'demain', 'aujourd', 'semaine', 'prochain', 'prochaine', 'jour', 'jours', 'mois', 'avant', 'apres', 'depuis'
  ]);

  function normaliser(valeur) {
    return String(valeur || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr')
      .replace(/[^a-z0-9]+/g, ' ').trim();
  }

  function racine(mot) {
    return mot.length > 4 ? mot.replace(/[sx]$/, '') : mot;
  }

  function mots(valeur) {
    return normaliser(valeur).split(' ').filter(Boolean).map(racine);
  }

  function motsSignificatifs(valeur) {
    return new Set(normaliser(valeur).split(' ').filter(mot => mot.length >= 4 && !motsVides.has(mot)).map(racine));
  }

  function estAClasser(nom) {
    return normaliser(nom) === normaliser(A_CLASSER);
  }

  function nommee(texte, disponibles) {
    const phrase = ` ${mots(texte).join(' ')} `;
    return disponibles.filter(nom => {
      const suite = mots(nom).join(' ');
      return suite && phrase.includes(` ${suite} `);
    });
  }

  // Indices évidents (réglages INDICES_RANGEMENT) : « scène » pour Scénarios, « chapitre » pour Roman…
  function parIndices(texte, disponibles) {
    const reglages = typeof INDICES_RANGEMENT === 'object' && INDICES_RANGEMENT ? INDICES_RANGEMENT : {};
    const phrase = ` ${mots(texte).join(' ')} `;
    return (Array.isArray(disponibles) ? disponibles : []).filter(nom => {
      const cle = Object.keys(reglages).find(item => mots(item).join(' ') === mots(nom).join(' '));
      const indices = cle && Array.isArray(reglages[cle]) ? reglages[cle] : [];
      return indices.some(indice => {
        const suite = mots(indice);
        if (suite.length > 1 && ['le', 'la', 'les', 'l', 'un', 'une', 'des', 'de', 'du'].includes(suite[0])) suite.shift();
        return suite.length && phrase.includes(` ${suite.join(' ')} `);
      });
    });
  }

  function parContenu(texte, categorie, disponibles, taches) {
    const motsPhrase = motsSignificatifs(texte);
    if (!motsPhrase.size) return '';
    const scores = disponibles.map(nom => {
      const communs = new Set();
      for (const tache of taches) {
        if (tache.parente || tache.abandonnee_le) continue;
        if (normaliser(tache.categorie) !== normaliser(categorie) || normaliser(tache.sous_categorie) !== normaliser(nom)) continue;
        for (const mot of motsSignificatifs(tache.intitule)) if (motsPhrase.has(mot)) communs.add(mot);
      }
      return { nom, score: communs.size };
    }).sort((a, b) => b.score - a.score);
    const [premier, second] = scores;
    if (!premier || premier.score < MOTS_COMMUNS_MINIMUM) return '';
    if (second && second.score === premier.score) return '';
    return premier.nom;
  }

  // disponibles : sous-catégories actives de la catégorie ; taches : la liste complète.
  function trouver(texte, categorie, disponibles, taches = []) {
    const liste = (Array.isArray(disponibles) ? disponibles : []).filter(nom => normaliser(nom) && !estAClasser(nom));
    if (!liste.length) return { sous_categorie: '', raison: 'aucune sous-catégorie' };
    const nommees = nommee(texte, liste);
    if (nommees.length === 1) return { sous_categorie: nommees[0], raison: 'nommée' };
    if (nommees.length > 1) return { sous_categorie: A_CLASSER, raison: 'plusieurs nommées' };
    const indiquees = parIndices(texte, liste);
    if (indiquees.length === 1) return { sous_categorie: indiquees[0], raison: 'indice' };
    if (indiquees.length > 1) return { sous_categorie: A_CLASSER, raison: 'plusieurs indices' };
    const proche = parContenu(texte, categorie, liste, Array.isArray(taches) ? taches : []);
    if (proche) return { sous_categorie: proche, raison: 'contenu proche' };
    return { sous_categorie: A_CLASSER, raison: 'pas clair' };
  }

  return { A_CLASSER, trouver, estAClasser, parIndices };
})();
