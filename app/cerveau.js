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
  let actif = 'auto';
  const DUREE_PROPOSITION_MS = 5 * 60 * 1000;
  let question = null;
  let enAttente = null;
  const MOTS_OUI = 'oui|ouais|ok|okay|d accord|daccord|vas y|va y|c est ca|c est bien ca|c est bon|parfait|exact|exactement|ca me va|ca marche|tres bien|bien sur|yes|go|top|valide|je valide|confirme|je confirme|absolument|tout a fait|impeccable|nickel|super';
  const OUI = new RegExp(`^(?:(?:cap|max) )?(?:${MOTS_OUI})(?: (?:${MOTS_OUI}|merci|cap|max))*$`);
  const NON = /^(?:(?:cap|max) )?(?:non|nan|non merci|pas du tout|surtout pas|pas la peine|laisse tomber|oublie|oublie ca|annule|annuler|annule ca|ne range rien|rien du tout)(?: (?:merci|cap|max|laisse tomber|oublie|ca ira))*$/;

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

  // « auto » : l'IA payante si elle est prête (clé tapée par Max), sinon les réponses préparées.
  function choisirFournisseur(nom) {
    if (nom !== 'auto' && !fournisseurs.has(nom)) throw new Error('Ce fournisseur d’IA n’est pas installé.');
    actif = nom;
  }

  function fournisseurActif() {
    if (actif !== 'auto') return fournisseurs.has(actif) ? actif : 'prepare';
    for (const [nom, fournisseur] of fournisseurs) {
      if (fournisseur.payant && typeof fournisseur.pret === 'function' && fournisseur.pret()) return nom;
    }
    return 'prepare';
  }

  const PAS_COMPRIS = { type: 'question', question: 'Je n’ai pas compris. Tu peux redire ta demande autrement ?', choix: [] };

  function parole(texte) {
    return typeof texte === 'string' ? texte.trim().slice(0, 400) : '';
  }

  // Une action « confirmation » devient une proposition : Cap la dit à Max et attend son oui.
  function proposition(nom, parametres) {
    let prete;
    try {
      prete = actionsCap.preparerProposition(nom, parametres);
    } catch (erreur) {
      if (nom !== 'proposer_rangement') return { type: 'reponse', texte: parole(erreur.message) || PAS_COMPRIS.question };
      prete = actionsCap.preparerProposition(nom, { ...parametres, categorie: '', sous_categorie: '' });
    }
    return { type: 'proposition', action: nom, parametres: prete.parametres, texte: prete.texte, manque: prete.manque || '', choix: prete.choix || [] };
  }

  function valider(decision) {
    if (decision?.type === 'action' && actionsCap.demandeConfirmation(decision.action)) {
      return proposition(decision.action, { ...(decision.parametres || {}) });
    }
    if (decision?.type === 'action' && actionsCap.CATALOGUE.some(action => action.nom === decision.action && !action.lecture)) {
      return { type: 'action', action: decision.action, parametres: { ...(decision.parametres || {}) }, parole: parole(decision.parole) };
    }
    if (decision?.type === 'reponse' && parole(decision.texte)) {
      return { type: 'reponse', texte: parole(decision.texte) };
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
    enAttente = decision.type === 'proposition' ? { ...decision, jusqua: Date.now() + DUREE_PROPOSITION_MS } : null;
    return decision;
  }

  // Une décision préparée par Cap lui-même (ex. rendez-vous dicté), soumise aux mêmes règles.
  function proposer(brut) {
    question = null;
    return retenir(valider(brut));
  }

  // demande : { texte, source }. Renvoie une décision, ou une promesse de décision (IA en ligne).
  // Un échange payant n'est compté que s'il a vraiment eu lieu. En cas d'échec, Cap repasse aux réponses préparées et le dit.
  function comprendre(demande) {
    question = null;
    const entree = { texte: String(demande?.texte || ''), source: demande?.source || '' };
    const prepare = fournisseurs.get('prepare');
    const fournisseur = fournisseurs.get(fournisseurActif());
    const finir = (brut, alerte = '') => {
      const decision = retenir(valider(brut));
      if (alerte) decision.alerte = alerte;
      return decision;
    };
    if (!fournisseur.payant) return finir(fournisseur.comprendre(entree, contexte()));
    if (!limiteIA.peutEchanger()) {
      return finir(prepare.comprendre(entree, contexte()), limiteIA.raisonArret());
    }
    let brut;
    try {
      brut = Promise.resolve(fournisseur.comprendre(entree, contexte()));
    } catch (erreur) {
      brut = Promise.reject(erreur);
    }
    return brut.then(
      resultat => finir(resultat, limiteIA.compter().alerte),
      erreur => finir(prepare.comprendre(entree, contexte()),
        `${erreur instanceof Error && erreur.message ? erreur.message : 'L’IA n’a pas répondu.'} Réponse préparée à la place.`)
    );
  }

  // Réponse à une proposition : « oui » → l'action ; « non » → rien ; détail manquant → nouvelle proposition ;
  // autre chose (une correction) → null, et la phrase repart vers le cerveau, qui repropose.
  function repondreProposition(texte) {
    const proposee = enAttente;
    enAttente = null;
    if (!proposee || Date.now() > proposee.jusqua) return null;
    const plat = plier(texte).replace(/ +/g, ' ').trim();
    const prevenir = reponse => fournisseurs.get(fournisseurActif())?.suiteProposition?.(texte, reponse);
    if (!proposee.manque && OUI.test(plat)) {
      prevenir('Max a dit oui : Cap l’a fait.');
      return { type: 'action', action: proposee.action, parametres: { ...proposee.parametres }, parole: '' };
    }
    if (NON.test(plat)) {
      prevenir('Max a dit non : rien n’a été fait.');
      return { type: 'reponse', texte: proposee.action === 'proposer_rendez_vous' ? 'D’accord, je n’inscris rien dans l’agenda.' : 'D’accord, je ne range rien.' };
    }
    if (proposee.action === 'proposer_rendez_vous' && comprendreDemande.rendezVous(texte)) return null;
    if (proposee.manque) {
      const complets = actionsCap.completerProposition(proposee, texte);
      if (complets) return retenir(proposition(proposee.action, complets));
    }
    if (proposee.action === 'proposer_rendez_vous') {
      // Correction d'un rendez-vous (« non, à 16 h », « non, mardi ») : Cap reformule avec la correction.
      const heure = actionsCap.heureDite(texte);
      const date = comprendreDemande.trouverDate(texte).date;
      if (heure || date) {
        const corriges = { ...proposee.parametres, choix_date: [] };
        if (heure) Object.assign(corriges, { heure, heure_fin: '' });
        if (date) corriges.date = date;
        return retenir(proposition(proposee.action, corriges));
      }
      return { type: 'reponse', texte: 'Je n’ai pas saisi la correction. Redis-moi le rendez-vous en entier.' };
    }
    return null;
  }

  // Réponse à la question (ou proposition) en attente. Renvoie la décision complétée, ou null (elle est alors oubliée).
  function repondre(texte) {
    if (enAttente) return repondreProposition(texte);
    const posee = question;
    question = null;
    if (!posee || Date.now() > posee.jusqua) return null;
    const plie = ` ${plier(texte).replace(/ +/g, ' ').trim()} `;
    if (/ (?:a trier|aucune?|nulle part|ni l un ni l autre) /.test(plie)) {
      return { type: 'action', action: posee.action, parametres: { ...posee.base, categorie: '', sous_categorie: '' } };
    }
    const retenus = posee.choix.filter(choix => {
      const motif = motifNom(choix.libelle);
      return motif && new RegExp(motif).test(plie);
    });
    if (retenus.length !== 1) return null;
    const { categorie = '', sous_categorie = '' } = retenus[0];
    return { type: 'action', action: posee.action, parametres: { ...posee.base, categorie, sous_categorie } };
  }

  function questionEnAttente() {
    return Boolean(question) && Date.now() <= question.jusqua;
  }

  function propositionEnAttente() {
    return Boolean(enAttente) && Date.now() <= enAttente.jusqua;
  }

  function oublierProposition() {
    enAttente = null;
  }

  return {
    comprendre, repondre, questionEnAttente, propositionEnAttente, oublierProposition, proposer,
    enregistrerFournisseur, choisirFournisseur, fournisseurActif,
    texte: { plier, motifNom }
  };
})();
