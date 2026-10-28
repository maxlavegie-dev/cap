'use strict';

// Tout est INVENTÉ ; ce fichier sera supprimé d’un coup avant les vraies données.
const TACHES_FICTIVES = (() => {
  function dateRelative(jours) {
    const date = new Date();
    date.setDate(date.getDate() + jours);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  }

  const liste = [];
  function ajouter(intitule, categorie, sousCategorie, champs = {}) {
    const tache = {
      id: `FICTIF-${String(liste.length + 1).padStart(3, '0')}`,
      intitule,
      categorie,
      sous_categorie: sousCategorie,
      fait: false,
      date_entree: dateRelative(-5),
      echeance: '',
      date_realisation: '',
      priorite: 'normale',
      parente: '',
      note: '',
      avant_le: '',
      abandonnee_le: '',
      origine: 'fictif',
      fictif: true,
      ...champs
    };
    liste.push(tache);
    return tache;
  }

  function titre(intitule, album, nombreFaites, supplement = false) {
    const parent = ajouter(intitule, 'Musique', album);
    const etapes = ['Réenregistrer les voix', 'Mixer', 'Masteriser'];
    if (supplement) etapes.push('Terminer la production');
    etapes.forEach((etape, index) => {
      const fait = index < nombreFaites;
      ajouter(etape, 'Musique', album, {
        parente: parent.id,
        fait,
        date_realisation: fait ? dateRelative(-1) : ''
      });
    });
    return parent;
  }

  titre('Les lucioles du large', 'Album A', 2, true).note = 'FICTIF — Essayer une fin plus douce.';
  titre('Un matin de papier', 'Album A', 1);
  titre('La lune en chaussettes', 'Album A', 0);
  titre('Soleil de poche', 'Album B', 2);
  titre('Les nuages à roulettes', 'Album B', 1);

  const roman = ajouter('Les jardins suspendus de minuit', 'Écriture', 'Roman', {
    echeance: dateRelative(7)
  });
  ['Relire', 'Corriger', 'Envoyer'].forEach((intitule, index) => {
    ajouter(intitule, 'Écriture', 'Roman', {
      parente: roman.id,
      fait: index === 0,
      date_realisation: index === 0 ? dateRelative(-2) : ''
    });
  });
  ajouter('Noter l’idée du train qui ne s’arrête jamais', 'Écriture', 'Scénarios', {
    note: 'FICTIF — Les voyageurs découvrent une gare dans les nuages.'
  });
  ajouter('Acheter du pain et des pommes', 'Quotidien', 'Courses', {
    echeance: dateRelative(1),
    priorite: 'haute'
  });
  ajouter('Arroser les plantes du balcon', 'Quotidien', 'Maison', {
    avant_le: dateRelative(-2)
  });
  return liste;
})();
