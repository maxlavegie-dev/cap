'use strict';

const chargementTaches = stockage.charger();
const TACHES = chargementTaches.taches;
const INFO_CHARGEMENT = chargementTaches.message;

function dateDuJour() {
  const date = new Date();
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function joursRestants(dateTexte) {
  if (typeof dateTexte !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(dateTexte)) {
    throw new Error('Choisis une date valide.');
  }
  const date = new Date(`${dateTexte}T00:00:00Z`);
  if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== dateTexte) {
    throw new Error('Choisis une date valide.');
  }
  // Des jours civils, même lors d’un changement d’heure.
  const aujourdHui = new Date(`${dateDuJour()}T00:00:00Z`);
  return Math.round((date - aujourdHui) / 86400000);
}

function trouverTache(id) {
  const tache = TACHES.find(element => element.id === id);
  if (!tache) throw new Error('Cette tâche est introuvable.');
  return tache;
}

function enregistrerModification(modifier) {
  const avant = TACHES.map(tache => ({ ...tache }));
  try {
    const resultat = modifier();
    stockage.enregistrer(TACHES);
    const precedentes = new Map(avant.map(tache => [tache.id, JSON.stringify(tache)]));
    const ids = TACHES.filter(tache => precedentes.get(tache.id) !== JSON.stringify(tache)).map(tache => tache.id);
    if (typeof synchronisation !== 'undefined') synchronisation.signaler(ids);
    if (ids.length && typeof vibration !== 'undefined') vibration.courte();
    if (typeof journalActions !== 'undefined') {
      const anciennes = new Map(avant.map(tache => [tache.id, tache]));
      for (const tache of TACHES) {
        const ancienne = anciennes.get(tache.id);
        if (!ancienne) journalActions.noter('ajout', tache.intitule);
        else {
          if (ancienne.fait !== tache.fait) journalActions.noter(tache.fait ? 'fait' : 'remise à faire', tache.intitule);
          if (ancienne.echeance !== tache.echeance) journalActions.noter('échéance', tache.intitule);
          if (!tache.parente && (ancienne.categorie !== tache.categorie || ancienne.sous_categorie !== tache.sous_categorie)) {
            journalActions.noter('classement', `${tache.intitule} → ${[tache.categorie || 'Sans catégorie', tache.sous_categorie].filter(Boolean).join(' › ')}`);
          }
          if (ancienne.abandonnee_le !== tache.abandonnee_le) {
            journalActions.noter(tache.abandonnee_le ? 'abandon' : 'remise', tache.intitule);
          }
        }
      }
    }
    return resultat;
  } catch (erreur) {
    TACHES.splice(0, TACHES.length, ...avant);
    throw erreur;
  }
}

function preparerTache(champs = {}) {
  if (typeof champs.intitule !== 'string' || !champs.intitule.trim()) {
    throw new Error('Écris un intitulé pour cette tâche.');
  }
  for (const champ of ['categorie', 'sous_categorie', 'note']) {
    if (champs[champ] !== undefined && typeof champs[champ] !== 'string') {
      throw new Error('Vérifie les champs de la tâche.');
    }
  }
  for (const champ of ['echeance', 'avant_le']) {
    if (champs[champ] !== undefined && champs[champ] !== '') joursRestants(champs[champ]);
  }
  const priorite = champs.priorite === undefined ? 'normale' : champs.priorite;
  if (!['haute', 'normale', 'basse'].includes(priorite)) throw new Error('Choisis une priorité valide.');
  const origine = champs.origine === undefined ? 'ajout à la main' : champs.origine;
  if (!['ajout à la main', 'dictée', 'fictif'].includes(origine)) throw new Error('Origine invalide.');
  if (champs.fictif !== undefined && typeof champs.fictif !== 'boolean') throw new Error('Indicateur fictif invalide.');
  let id;
  do {
    const aleatoire = Math.floor(Math.random() * 1679616).toString(36).padStart(4, '0');
    id = `T-${Date.now().toString(36)}${aleatoire}`;
  } while (TACHES.some(tache => tache.id === id));
  const parente = champs.parente === undefined ? '' : champs.parente;
  let parent;
  if (parente !== '') {
    parent = trouverTache(parente);
    if (parent.parente) throw new Error('Une étape ne peut pas avoir ses propres étapes.');
    if (parent.abandonnee_le) throw new Error('Remets d’abord la tâche parente pour lui ajouter une étape.');
  }
  return {
    id,
    intitule: champs.intitule,
    categorie: parent ? parent.categorie : (champs.categorie || ''),
    sous_categorie: parent ? parent.sous_categorie : (champs.sous_categorie || ''),
    fait: false,
    date_entree: dateDuJour(),
    echeance: champs.echeance || '',
    date_realisation: '',
    priorite,
    parente,
    note: champs.note || '',
    avant_le: champs.avant_le || '',
    abandonnee_le: '',
    origine,
    fictif: champs.fictif === true
  };
}

function creerTache(champs) {
  return enregistrerModification(() => {
    const tache = preparerTache(champs);
    TACHES.push(tache);
    return tache;
  });
}

function creerAvecEtapesParDefaut(champs, nomModele) {
  if (!Object.prototype.hasOwnProperty.call(ETAPES_PAR_DEFAUT, nomModele)) {
    throw new Error('Ce modèle d’étapes est introuvable.');
  }
  if (champs.parente) throw new Error('Les étapes par défaut sont réservées aux tâches principales.');
  return enregistrerModification(() => {
    const parent = preparerTache(champs);
    TACHES.push(parent);
    for (const intitule of ETAPES_PAR_DEFAUT[nomModele]) {
      TACHES.push(preparerTache({
        intitule,
        parente: parent.id,
        origine: parent.origine,
        fictif: parent.fictif
      }));
    }
    return parent;
  });
}

function ajouterEtape(idParente, intitule) {
  return creerTache({ intitule, parente: idParente, origine: 'ajout à la main', fictif: false });
}

function cocher(id, valeur) {
  if (typeof valeur !== 'boolean') throw new Error('La case doit être cochée ou décochée.');
  return enregistrerModification(() => {
    const tache = trouverTache(id);
    tache.fait = valeur;
    tache.date_realisation = valeur ? dateDuJour() : '';
    return tache;
  });
}

function changerEcheance(id, valeur) {
  if (typeof valeur !== 'string') throw new Error('Choisis une date valide.');
  if (valeur !== '') joursRestants(valeur);
  return enregistrerModification(() => {
    const tache = trouverTache(id);
    const ancienne = tache.echeance;
    tache.echeance = valeur;
    return ancienne;
  });
}

function reporterADemain(id) {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  const demain = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  return changerEcheance(id, demain);
}

function classer(id, categorie, sousCategorie = '') {
  if (typeof categorie !== 'string' || typeof sousCategorie !== 'string') throw new Error('Choisis une catégorie valide.');
  return enregistrerModification(() => {
    const tache = trouverTache(id);
    if (tache.parente) throw new Error('Une étape suit la catégorie de sa tâche.');
    const ancienne = { categorie: tache.categorie, sous_categorie: tache.sous_categorie };
    for (const cible of TACHES.filter(item => item.id === id || item.parente === id)) {
      cible.categorie = categorie;
      cible.sous_categorie = sousCategorie;
    }
    return ancienne;
  });
}

function abandonner(id) {
  return enregistrerModification(() => {
    const tache = trouverTache(id);
    if (!tache.abandonnee_le) tache.abandonnee_le = dateDuJour();
    return tache;
  });
}

function remettre(id) {
  return enregistrerModification(() => {
    const tache = trouverTache(id);
    tache.abandonnee_le = '';
    return tache;
  });
}

function avancementTache(id) {
  trouverTache(id);
  const etapes = TACHES.filter(tache => tache.parente === id && !tache.abandonnee_le);
  return { faites: etapes.filter(tache => tache.fait).length, total: etapes.length };
}

function avancementSousCategorie(categorie, sousCategorie) {
  const actives = TACHES.filter(tache => tache.categorie === categorie
    && tache.sous_categorie === sousCategorie && !tache.abandonnee_le);
  const etapes = actives.filter(tache => tache.parente);
  const elements = etapes.length ? etapes : actives.filter(tache => !tache.parente);
  return elements.length ? Math.round(elements.filter(tache => tache.fait).length * 100 / elements.length) : 0;
}
