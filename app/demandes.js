'use strict';

function composerTexte(phrase, complement) {
  const debut = phrase.debut.replace(/(?:\.\.\.|…)$/, '').trimEnd();
  return `${debut} ${complement.trim()}`.trim();
}

function noterEnTache(intitule, source) {
  const date = comprendreDemande.trouverDate(intitule);
  const tache = creerTache({
    intitule,
    categorie: 'À trier',
    sous_categorie: '',
    echeance: date.date,
    origine: source === 'micro' ? 'dictée' : 'ajout à la main',
    fictif: false
  });
  return { tache, choix: date.choix };
}

function traiterDemande({ texte = '', source, id_phrase = '', complement = '', agenda_disponible = false }) {
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
    const libre = phrase?.action !== 'ajouter_tache';
    const report = libre ? comprendreDemande.report(texteComplet) : null;
    const brouillon = libre && !report ? comprendreDemande.rendezVous(texteComplet) : null;
    if (report?.cible === 'tache') {
      resultat = { type: 'report', message: '' };
    } else if (report) {
      resultat = {
        type: 'pas_compris',
        message: 'Je ne sais pas encore déplacer un rendez-vous à la voix. Cherche-le en bas, puis touche « Modifier ».'
      };
    } else if (brouillon && agenda_disponible) {
      resultat = { type: 'rendez-vous', brouillon, message: 'Vérifie le rendez-vous avant que je l’ajoute à l’agenda.' };
    } else if (brouillon) {
      const { tache, choix } = noterEnTache(intitule, source);
      resultat = {
        type: 'tache', tache, choix_echeance: choix,
        message: `Pas de connexion à Google : ce n'est PAS dans l'agenda. Je l'ai notée comme tâche dans À trier : « ${intitule} »`
      };
    } else {
      const { tache, choix } = noterEnTache(intitule, source);
      resultat = { type: 'tache', tache, choix_echeance: choix, message: `Ajoutée dans À trier : « ${intitule} »` };
    }
  }
  if (id_phrase) preferencesClavier.compterUtilisation(id_phrase);
  preferencesClavier.ajouterHistorique({ texte, source, id_phrase, complement });
  return resultat;
}
