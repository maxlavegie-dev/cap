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

// Exécute la décision du cerveau par la frontière actionsCap, et prépare ce que Cap affiche et dit.
function executerDecision(decision, source) {
  if (decision.type === 'question') {
    const message = [decision.alerte, decision.question].filter(Boolean).join(' ');
    return { type: 'question', message, parole: decision.question };
  }
  if (decision.type === 'reponse') {
    return { type: 'reponse', message: [decision.alerte, decision.texte].filter(Boolean).join(' '), parole: decision.texte };
  }
  if (decision.type === 'proposition') {
    return { type: 'proposition', message: [decision.alerte, decision.texte].filter(Boolean).join(' '), parole: decision.texte };
  }
  if (decision.action === 'proposer_rendez_vous') {
    const suite = actionsCap.executer(decision.action, decision.parametres).then(rendezVous => ({
      type: 'rendez_vous_ajoute', rendezVous,
      message: `Rendez-vous ajouté dans l'agenda Cap – FICTIF : ${rendezVous.titre}`,
      parole: 'C’est inscrit dans l’agenda.'
    }));
    return { type: 'reflexion', message: 'J’inscris le rendez-vous…', suite };
  }
  const { tache, choix } = actionsCap.executer(decision.action, { ...decision.parametres, source });
  const lieu = [tache.categorie, tache.sous_categorie].filter(Boolean);
  const message = `Ajoutée dans ${lieu.join(' › ')} : « ${tache.intitule} »`;
  return {
    type: 'tache', tache, choix_echeance: choix,
    message: decision.alerte ? `${message}. ${decision.alerte}` : message,
    parole: decision.parole || `C’est noté dans ${lieu.join(', ')}.`
  };
}

function demanderAuCerveau(texte, source) {
  const decision = cerveau.comprendre({ texte, source });
  if (decision && typeof decision.then === 'function') {
    return { type: 'reflexion', message: 'Je réfléchis…', suite: decision.then(fini => executerDecision(fini, source)) };
  }
  return executerDecision(decision, source);
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
  const suiteQuestion = !phrase && (cerveau.propositionEnAttente() || !annulation.estDemande(texteComplet))
    ? cerveau.repondre(texteComplet) : null;
  if (phrase) cerveau.oublierProposition();
  if (suiteQuestion) {
    resultat = executerDecision(suiteQuestion, source);
  } else if (phrase?.id === 'annuler' || (!phrase && annulation.estDemande(texteComplet))) {
    resultat = { type: 'annuler', message: '' };
  } else if (phrase && !phrase.a_completer && cerveau.fournisseurActif() !== 'prepare') {
    resultat = demanderAuCerveau(texteComplet, source);
  } else if (phrase && !phrase.a_completer) {
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
      // Rendez-vous dicté : Cap redit tous les détails et attend le oui de Max (la fiche ne s'ouvre que sur le bouton +).
      resultat = executerDecision(cerveau.proposer({ type: 'action', action: 'proposer_rendez_vous', parametres: brouillon }), source);
    } else if (brouillon) {
      const { tache, choix } = noterEnTache(intitule, source);
      resultat = {
        type: 'tache', tache, choix_echeance: choix,
        message: `Pas de connexion à Google : ce n'est PAS dans l'agenda. Je l'ai notée comme tâche dans À trier : « ${intitule} »`
      };
    } else {
      resultat = demanderAuCerveau(intitule, source);
    }
  }
  if (id_phrase) preferencesClavier.compterUtilisation(id_phrase);
  preferencesClavier.ajouterHistorique({ texte, source, id_phrase, complement });
  return resultat;
}
