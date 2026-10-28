'use strict';

function composerTexte(phrase, complement) {
  const debut = phrase.debut.replace(/(?:\.\.\.|…)$/, '').trimEnd();
  return `${debut} ${complement.trim()}`.trim();
}

function traiterDemande({ texte = '', source, id_phrase = '', complement = '' }) {
  if (!['micro', 'clavier', 'saisie'].includes(source)) throw new Error('Origine de demande invalide.');
  const phrase = PHRASES_CLAVIER.find(item => item.id === id_phrase);
  const texteComplet = texte.trim();
  const intitule = phrase?.action === 'ajouter_tache' ? complement.trim() : texteComplet;
  if (!texteComplet || !intitule) {
    return {
      type: 'vide',
      message: source === 'micro' ? "Je n'ai rien entendu, réessaie." : "Je n'ai rien reçu, réessaie."
    };
  }
  let resultat;
  if (phrase && !phrase.a_completer) {
    resultat = {
      type: 'attente_cerveau',
      message: `« ${phrase.debut} » marchera quand le cerveau de Cap sera branché.`
    };
  } else {
    const tache = creerTache({
      intitule,
      categorie: 'À trier',
      sous_categorie: '',
      origine: source === 'micro' ? 'dictée' : 'ajout à la main',
      fictif: false
    });
    resultat = { type: 'tache', tache, message: `Ajoutée dans À trier : « ${intitule} »` };
  }
  if (id_phrase) preferencesClavier.compterUtilisation(id_phrase);
  preferencesClavier.ajouterHistorique({ texte, source, id_phrase, complement });
  return resultat;
}
