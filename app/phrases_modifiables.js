'use strict';

// MODULE DE CLAUDE POUR CAP : phrases de demande modifiables (code pur, sans IA).
//
// Rôle : garder, pour chaque commande vocale, la liste des phrases que Cap reconnaît, et laisser
// Max les ajouter, modifier ou retirer SANS toucher au code. Ce fichier ne fait que transformer des
// données : aucun DOM, aucun appel réseau, aucune écriture Drive ni localStorage. Zencoder branche
// le stockage (exporterJSON / chargerJSON) et l'écran des réglages.
//
// Règles respectées :
//  - Zéro perte : une phrase retirée ou remplacée est MARQUÉE (retiree_le), jamais effacée.
//  - Aucune phrase n'est envoyée à l'IA. Aucun nom de proche, aucune donnée réelle.
//  - Fonctions pures : chaque fonction qui modifie renvoie un NOUVEL état, l'ancien reste intact.
//  - Il reste toujours au moins une phrase active par rubrique.
//
// Deux sortes de rubriques :
//  - type 'commande' : la phrase qui OUVRE une demande (ex. « liste », « à faire »).
//  - type 'action'   : le mot qui suit (ex. « lis-moi », « retire », « coche », « note », « terminé »).
//
// Utilisation côté Cap (exemple, à adapter par Zencoder) :
//   const trouve = phrasesModifiables.detecterCommande(etat, 'liste pommes, pain et lait');
//   // -> { rubrique: 'liste_courses', phrase: 'liste', reste: 'pommes, pain et lait' }
//   const action = phrasesModifiables.detecterAction(etat, 'lis-moi');
//   // -> { rubrique: 'action_lire', phrase: 'lis-moi', reste: '' }

const phrasesModifiables = (() => {
  const VERSION = 1;
  const LONGUEUR_MAX = 60;

  // Phrases d'origine, reprises du code actuel de Zencoder (fichiers_vocaux*.js).
  const PAR_DEFAUT = {
    liste_courses: { type: 'commande', libelle: 'Liste de courses', phrases: ['liste', 'listes'] },
    choses_a_acheter: { type: 'commande', libelle: 'Choses à acheter', phrases: ['achat', 'achats'] },
    films_a_voir: { type: 'commande', libelle: 'Films à voir', phrases: ['film', 'films'] },
    livres_a_lire: { type: 'commande', libelle: 'Livres à lire', phrases: ['livre', 'livres'] },
    bloc_notes: { type: 'commande', libelle: 'Bloc-notes', phrases: ['bloc-notes', 'bloc note'] },
    brouillon_vocal: { type: 'commande', libelle: 'Brouillon vocal', phrases: ['brouillon vocal', 'brouillon'] },
    echeancier: { type: 'commande', libelle: 'Échéancier', phrases: ['échéance'] },
    a_faire: {
      type: 'commande', libelle: 'À faire',
      phrases: ['à faire', 'affaire', 'mets dans ma to-do', 'ma to-do', 'rappelle-moi de', 'il faut que je']
    },
    action_lire: { type: 'action', libelle: 'Action : lire', phrases: ['lis-moi'] },
    action_retirer: { type: 'action', libelle: 'Action : retirer', phrases: ['retire'] },
    action_cocher: { type: 'action', libelle: 'Action : cocher', phrases: ['coche'] },
    action_note: { type: 'action', libelle: 'Action : commencer une dictée', phrases: ['note'] },
    action_terminer: { type: 'action', libelle: 'Action : terminer', phrases: ['terminé', 'terminée'] }
  };

  function deuxChiffres(valeur) {
    return String(valeur).padStart(2, '0');
  }

  function dateDuJour(maintenant = new Date()) {
    return `${deuxChiffres(maintenant.getDate())}/${deuxChiffres(maintenant.getMonth() + 1)}/${maintenant.getFullYear()}`;
  }

  function cloner(objet) {
    return JSON.parse(JSON.stringify(objet));
  }

  // "À faire" -> "a faire" ; "rappelle-moi" -> deux mots "rappelle", "moi".
  function normaliserMot(mot) {
    return mot.toLowerCase().normalize('NFD').replace(/\p{M}/gu, '');
  }

  // Découpe en mots en gardant leur position dans le texte d'origine.
  function jetons(texte) {
    const resultat = [];
    const motif = /[\p{L}\p{N}]+/gu;
    const source = String(texte || '');
    let trouve;
    while ((trouve = motif.exec(source)) !== null) {
      resultat.push({ mot: normaliserMot(trouve[0]), debut: trouve.index, fin: trouve.index + trouve[0].length });
    }
    return resultat;
  }

  function cleNormalisee(texte) {
    return jetons(texte).map(j => j.mot).join(' ');
  }

  function nouvelleEntree(texte, origine, maintenant) {
    return { texte: String(texte).trim().replace(/\s+/g, ' '), origine, ajoutee_le: dateDuJour(maintenant), retiree_le: null };
  }

  function estActive(entree) {
    return entree.retiree_le === null;
  }

  function creerEtat(maintenant = new Date()) {
    const rubriques = {};
    for (const [id, def] of Object.entries(PAR_DEFAUT)) {
      rubriques[id] = {
        type: def.type,
        libelle: def.libelle,
        phrases: def.phrases.map(texte => nouvelleEntree(texte, true, maintenant))
      };
    }
    return { version: VERSION, rubriques };
  }

  function phrasesActives(etat, rubrique) {
    const element = etat.rubriques[rubrique];
    return element ? element.phrases.filter(estActive).map(entree => entree.texte) : [];
  }

  // Cherche une phrase active identique (une fois normalisée) dans les rubriques du même type.
  function chercherConflit(etat, rubrique, texte) {
    const cle = cleNormalisee(texte);
    const type = etat.rubriques[rubrique].type;
    for (const [id, element] of Object.entries(etat.rubriques)) {
      if (element.type !== type) continue;
      if (element.phrases.some(entree => estActive(entree) && cleNormalisee(entree.texte) === cle)) return id;
    }
    return null;
  }

  function verifierTexte(etat, rubrique, texte) {
    if (!etat.rubriques[rubrique]) return `Rubrique inconnue : ${rubrique}.`;
    const propre = String(texte || '').trim();
    if (!cleNormalisee(propre)) return 'La phrase est vide.';
    if (propre.length > LONGUEUR_MAX) return `La phrase est trop longue (${LONGUEUR_MAX} caractères au maximum).`;
    const conflit = chercherConflit(etat, rubrique, propre);
    if (conflit === rubrique) return 'Cette phrase existe déjà pour cette commande.';
    if (conflit) return `Cette phrase est déjà utilisée par : ${etat.rubriques[conflit].libelle}.`;
    return null;
  }

  function ajouterPhrase(etat, rubrique, texte, maintenant = new Date()) {
    const erreur = verifierTexte(etat, rubrique, texte);
    if (erreur) return { ok: false, etat, erreur };
    const suivant = cloner(etat);
    suivant.rubriques[rubrique].phrases.push(nouvelleEntree(texte, false, maintenant));
    return { ok: true, etat: suivant };
  }

  // Marque la phrase comme retirée (jamais effacée). Refuse de retirer la dernière phrase active.
  function retirerPhrase(etat, rubrique, texte, maintenant = new Date()) {
    const element = etat.rubriques[rubrique];
    if (!element) return { ok: false, etat, erreur: `Rubrique inconnue : ${rubrique}.` };
    const cle = cleNormalisee(texte);
    const index = element.phrases.findIndex(entree => estActive(entree) && cleNormalisee(entree.texte) === cle);
    if (index === -1) return { ok: false, etat, erreur: 'Phrase introuvable.' };
    if (element.phrases.filter(estActive).length <= 1) {
      return { ok: false, etat, erreur: 'Il doit rester au moins une phrase pour cette commande.' };
    }
    const suivant = cloner(etat);
    suivant.rubriques[rubrique].phrases[index].retiree_le = dateDuJour(maintenant);
    return { ok: true, etat: suivant };
  }

  // Modifier = marquer l'ancienne comme retirée, puis ajouter la nouvelle. L'ancienne reste visible
  // dans l'historique. Si la nouvelle est refusée, rien ne change.
  function modifierPhrase(etat, rubrique, ancienne, nouvelle, maintenant = new Date()) {
    const element = etat.rubriques[rubrique];
    if (!element) return { ok: false, etat, erreur: `Rubrique inconnue : ${rubrique}.` };
    const cle = cleNormalisee(ancienne);
    const index = element.phrases.findIndex(entree => estActive(entree) && cleNormalisee(entree.texte) === cle);
    if (index === -1) return { ok: false, etat, erreur: 'Phrase introuvable.' };
    const brouillon = cloner(etat);
    brouillon.rubriques[rubrique].phrases[index].retiree_le = dateDuJour(maintenant);
    const erreur = verifierTexte(brouillon, rubrique, nouvelle);
    if (erreur) return { ok: false, etat, erreur };
    brouillon.rubriques[rubrique].phrases.push(nouvelleEntree(nouvelle, false, maintenant));
    return { ok: true, etat: brouillon };
  }

  // Retour aux phrases d'origine : les phrases ajoutées par Max sont marquées retirées, les phrases
  // d'origine redeviennent actives (nouvelle entrée datée). Rien n'est effacé.
  // Si une phrase d'origine est déjà prise par une autre commande, elle est ignorée et signalée.
  function reinitialiser(etat, rubrique, maintenant = new Date()) {
    const element = etat.rubriques[rubrique];
    if (!element || !PAR_DEFAUT[rubrique]) return { ok: false, etat, erreur: `Rubrique inconnue : ${rubrique}.` };
    const suivant = cloner(etat);
    const cible = suivant.rubriques[rubrique];
    const dateRetrait = dateDuJour(maintenant);
    for (const entree of cible.phrases) {
      if (estActive(entree) && !entree.origine) entree.retiree_le = dateRetrait;
    }
    const ignorees = [];
    for (const texte of PAR_DEFAUT[rubrique].phrases) {
      const cle = cleNormalisee(texte);
      if (cible.phrases.some(entree => estActive(entree) && cleNormalisee(entree.texte) === cle)) continue;
      const conflit = chercherConflit(suivant, rubrique, texte);
      if (conflit) { ignorees.push(texte); continue; }
      cible.phrases.push(nouvelleEntree(texte, true, maintenant));
    }
    return { ok: true, etat: suivant, ignorees };
  }

  // Trouve la plus longue phrase active qui ouvre le texte, mot entier par mot entier.
  function correspondance(etat, texte, type) {
    const mots = jetons(texte);
    let meilleur = null;
    for (const [id, element] of Object.entries(etat.rubriques)) {
      if (element.type !== type) continue;
      for (const entree of element.phrases) {
        if (!estActive(entree)) continue;
        const motsPhrase = jetons(entree.texte);
        if (!motsPhrase.length || motsPhrase.length > mots.length) continue;
        if (!motsPhrase.every((jeton, i) => jeton.mot === mots[i].mot)) continue;
        if (!meilleur || motsPhrase.length > meilleur.longueur) {
          meilleur = { rubrique: id, phrase: entree.texte, longueur: motsPhrase.length };
        }
      }
    }
    if (!meilleur) return null;
    const fin = mots[meilleur.longueur - 1].fin;
    const reste = String(texte).slice(fin).replace(/^[\s,;:.!?\-–—]+/u, '').trim();
    return { rubrique: meilleur.rubrique, phrase: meilleur.phrase, reste };
  }

  function detecterCommande(etat, texte) {
    return correspondance(etat, texte, 'commande');
  }

  function detecterAction(etat, texte) {
    return correspondance(etat, texte, 'action');
  }

  // Vrai si tout le texte est exactement une des phrases actives de la rubrique (ex. « terminé »).
  function estExactement(etat, rubrique, texte) {
    const element = etat.rubriques[rubrique];
    if (!element) return false;
    const cle = cleNormalisee(texte);
    return Boolean(cle) && element.phrases.some(entree => estActive(entree) && cleNormalisee(entree.texte) === cle);
  }

  function exporterJSON(etat) {
    return JSON.stringify(etat);
  }

  // Relit un état sauvegardé. Si le texte est absent ou abîmé, renvoie l'état d'origine sans rien
  // effacer côté stockage (c'est à l'appelant de ne pas écraser avant d'avoir lu `ok`).
  // Les rubriques ajoutées plus tard au code sont complétées avec leurs phrases d'origine.
  function chargerJSON(texte, maintenant = new Date()) {
    let lu;
    try {
      lu = JSON.parse(texte);
    } catch (erreur) {
      return { ok: false, etat: creerEtat(maintenant), erreur: 'Données illisibles.' };
    }
    const valide = lu && lu.version === VERSION && lu.rubriques && typeof lu.rubriques === 'object'
      && Object.values(lu.rubriques).every(element => element && Array.isArray(element.phrases)
        && element.phrases.every(entree => entree && typeof entree.texte === 'string' && 'retiree_le' in entree));
    if (!valide) return { ok: false, etat: creerEtat(maintenant), erreur: 'Données non reconnues.' };
    const initial = creerEtat(maintenant);
    for (const [id, element] of Object.entries(initial.rubriques)) {
      if (!lu.rubriques[id]) lu.rubriques[id] = element;
    }
    return { ok: true, etat: lu };
  }

  return {
    VERSION, PAR_DEFAUT, creerEtat, phrasesActives,
    ajouterPhrase, retirerPhrase, modifierPhrase, reinitialiser,
    detecterCommande, detecterAction, estExactement, exporterJSON, chargerJSON
  };
})();
if (typeof module !== 'undefined' && module.exports) module.exports = phrasesModifiables;
