'use strict';

const preferencesClavier = (() => {
  const cleUsage = 'cap_usage_phrases_v1';
  const cleHistorique = 'cap_historique_demandes_v1';
  const cleSilence = 'cap_reponse_silencieuse_v1';

  function lire(cle, valeurVide, valide) {
    let valeur;
    try {
      const brut = localStorage.getItem(cle);
      valeur = brut === null ? valeurVide : JSON.parse(brut);
    } catch (erreur) {
      valeur = valeurVide;
    }
    return valide(valeur) ? valeur : valeurVide;
  }

  function ecrire(cle, valeur) {
    try {
      localStorage.setItem(cle, JSON.stringify(valeur));
    } catch (erreur) {
    }
  }

  function usages() {
    return lire(cleUsage, {}, valeur => valeur !== null && typeof valeur === 'object'
      && !Array.isArray(valeur) && Object.values(valeur).every(compteur => Number.isSafeInteger(compteur) && compteur >= 0));
  }

  function historique() {
    return lire(cleHistorique, [], valeur => Array.isArray(valeur) && valeur.every(entree =>
      entree !== null && typeof entree === 'object'
      && typeof entree.texte === 'string' && typeof entree.id_phrase === 'string'
      && typeof entree.complement === 'string' && ['micro', 'clavier', 'saisie'].includes(entree.source)
      && typeof entree.date === 'string' && Number.isFinite(Date.parse(entree.date))))
      .slice(0, 20).map(entree => ({ ...entree }));
  }

  return {
    compterUtilisation(id) {
      if (!PHRASES_CLAVIER.some(phrase => phrase.id === id)) return;
      const compteurs = usages();
      compteurs[id] = Math.min((compteurs[id] || 0) + 1, Number.MAX_SAFE_INTEGER);
      ecrire(cleUsage, compteurs);
    },
    plusUtilisees(n) {
      const compteurs = usages();
      return PHRASES_CLAVIER.filter(phrase => (compteurs[phrase.id] || 0) > 0)
        .sort((a, b) => compteurs[b.id] - compteurs[a.id])
        .slice(0, Math.max(0, Math.floor(n) || 0));
    },
    ajouterHistorique(entree) {
      ecrire(cleHistorique, [{
        texte: entree.texte,
        id_phrase: entree.id_phrase || '',
        complement: entree.complement || '',
        source: entree.source,
        date: new Date().toISOString()
      }, ...historique()].slice(0, 20));
    },
    historique,
    silencieux() {
      return lire(cleSilence, true, valeur => typeof valeur === 'boolean');
    },
    definirSilencieux(valeur) {
      if (typeof valeur === 'boolean') ecrire(cleSilence, valeur);
    }
  };
})();
