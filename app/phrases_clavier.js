'use strict';

const PHRASES_CLAVIER = [
  { id: 'retrouver', categorie: 'Retrouver', debut: 'Retrouve-moi...', a_completer: true, action: '' },
  { id: 'dictionnaire', categorie: 'Retrouver', debut: 'Cherche dans mon dictionnaire...', a_completer: true, action: '' },
  { id: 'dernier-mail', categorie: 'Retrouver', debut: 'Retrouve le dernier mail de...', a_completer: true, action: '' },
  { id: 'agenda', categorie: 'Agenda et to-do', debut: "Qu'est-ce que j'ai le...", a_completer: true, action: '' },
  { id: 'ajouter-tache', categorie: 'Agenda et to-do', debut: 'Ajoute à ma to-do...', a_completer: true, action: 'ajouter_tache' },
  { id: 'rappel', categorie: 'Agenda et to-do', debut: 'Rappelle-moi de...', a_completer: true, action: '' },
  { id: 'resumer-mails', categorie: 'Mails', debut: 'Résume mes mails de...', a_completer: true, action: '' },
  { id: 'brouillon', categorie: 'Mails', debut: 'Prépare un brouillon de réponse à...', a_completer: true, action: '' },
  { id: 'reformuler', categorie: 'Général', debut: 'Reformule en plus...', a_completer: true, action: '' },
  { id: 'continuer', categorie: 'Général', debut: 'Continue.', a_completer: false, action: '' },
  { id: 'annuler', categorie: 'Général', debut: 'Annule.', a_completer: false, action: '' }
];
