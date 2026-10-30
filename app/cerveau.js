'use strict';

// Le cerveau de Cap : comprend ce que Max dit ou écrit, et répond par une DÉCISION, sans rien faire lui-même.
// Décisions possibles :
//   { type: 'action', action: 'ajouter_tache', parametres: {...} }  → exécutée ensuite par actionsCap ;
//   { type: 'question', question, action, base, choix: [{ libelle, categorie, sous_categorie }] } → une seule question courte.
// Le modèle d'IA est interchangeable : chaque « fournisseur » a la même forme
//   { nom, payant, comprendre(demande, contexte) } et renvoie une décision (ou une promesse de décision).
// Sans clé, seul le fournisseur « prepare » (réponses préparées, gratuit, sur le téléphone) est utilisé.
const cerveau = (() => {
  const DUREE_QUESTION_MS = 2 * 60 * 1000;
  const fournisseurs = new Map();
  let actif = 'prepare';
  let question = null;

  // Même longueur que le texte d'origine : les positions trouvées servent à recopier l'intitulé mot pour mot.
  function plier(texte) {
    return String(texte || '').split('').map(caractere => {
      const base = caractere.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr');
      return base.length === 1 && /[a-z0-9]/.test(base) ? base : ' ';
    }).join('');
  }

  // Motif d'un nom de catégorie, sans accents ni majuscules, singulier ou pluriel.
  function motifNom(nom) {
    const mots = plier(nom).split(' ').filter(Boolean)
      .map(mot => `${mot.length > 4 ? mot.replace(/[sx]$/, '') : mot}[sx]?`);
    return mots.length ? `(?<![a-z0-9])${mots.join(' +')}(?![a-z0-9])` : '';
  }

  function contexte() {
    return {
      categories: listesChoix.categories().map(nom => ({ nom, sous_categories: listesChoix.categories(nom) })),
      a_trier: listesChoix.A_TRIER,
      actions: actionsCap.CATALOGUE.map(action => action.nom)
    };
  }

  function enregistrerFournisseur(nom, fournisseur) {
    if (!nom || !fournisseur || typeof fournisseur.comprendre !== 'function') throw new Error('Fournisseur d’IA invalide.');
    fournisseurs.set(nom, fournisseur);
  }

  function choisirFournisseur(nom) {
    if (!fournisseurs.has(nom)) throw new Error('Ce fournisseur d’IA n’est pas installé.');
    actif = nom;
  }

  function fournisseurActif() {
    return fournisseurs.has(actif) ? actif : 'prepare';
  }

  const PAS_COMPRIS = { type: 'question', question: 'Je n’ai pas compris. Tu peux redire ta demande autrement ?', choix: [] };

  function valider(decision) {
    if (decision?.type === 'action' && actionsCap.CATALOGUE.some(action => action.nom === decision.action)) {
      return { type: 'action', action: decision.action, parametres: { ...(decision.parametres || {}) } };
    }
    if (decision?.type === 'question' && typeof decision.question === 'string' && decision.question.trim()) {
      const choix = Array.isArray(decision.choix) ? decision.choix.filter(item => item && typeof item.libelle === 'string').slice(0, 3) : [];
      return { type: 'question', question: decision.question.trim(), action: decision.action || '', base: { ...(decision.base || {}) }, choix };
    }
    return { ...PAS_COMPRIS };
  }

  function retenir(decision) {
    question = decision.type === 'question' && decision.choix.length
      ? { ...decision, jusqua: Date.now() + DUREE_QUESTION_MS } : null;
    return decision;
  }

  // demande : { texte, source }. Renvoie une décision, ou une promesse de décision (IA en ligne).
  function comprendre(demande) {
    question = null;
    let fournisseur = fournisseurs.get(fournisseurActif());
    let alerte = '';
    if (fournisseur.payant) {
      if (limiteIA.peutEchanger()) {
        alerte = limiteIA.compter().alerte;
      } else {
        fournisseur = fournisseurs.get('prepare');
        alerte = `Limite de ${limiteIA.MAXIMUM} échanges avec l’IA atteinte aujourd’hui : j’utilise les réponses préparées.`;
      }
    }
    const finir = brut => {
      const decision = retenir(valider(brut));
      if (alerte) decision.alerte = alerte;
      return decision;
    };
    const brut = fournisseur.comprendre({ texte: String(demande?.texte || ''), source: demande?.source || '' }, contexte());
    return brut && typeof brut.then === 'function' ? brut.then(finir, () => finir(null)) : finir(brut);
  }

  // Réponse à la question en attente. Renvoie la décision complétée, ou null (la question est alors oubliée).
  function repondre(texte) {
    const enAttente = question;
    question = null;
    if (!enAttente || Date.now() > enAttente.jusqua) return null;
    const plie = ` ${plier(texte).replace(/ +/g, ' ').trim()} `;
    if (/ (?:a trier|aucune?|nulle part|ni l un ni l autre) /.test(plie)) {
      return { type: 'action', action: enAttente.action, parametres: { ...enAttente.base, categorie: '', sous_categorie: '' } };
    }
    const retenus = enAttente.choix.filter(choix => {
      const motif = motifNom(choix.libelle);
      return motif && new RegExp(motif).test(plie);
    });
    if (retenus.length !== 1) return null;
    const { categorie = '', sous_categorie = '' } = retenus[0];
    return { type: 'action', action: enAttente.action, parametres: { ...enAttente.base, categorie, sous_categorie } };
  }

  function questionEnAttente() {
    return Boolean(question) && Date.now() <= question.jusqua;
  }

  return {
    comprendre, repondre, questionEnAttente, enregistrerFournisseur, choisirFournisseur, fournisseurActif,
    texte: { plier, motifNom }
  };
})();
