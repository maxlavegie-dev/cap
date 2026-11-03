'use strict';

const annuaire = (() => {
  const cle = 'cap_annuaire_v1';
  const cleEnvoi = 'cap_annuaire_a_envoyer_v1';
  const texte = valeur => (typeof valeur === 'string' ? valeur : '');
  const normaliser = valeur => texte(valeur).toLocaleLowerCase('fr').normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();

  const CHAMPS = [
    'prenom', 'nom', 'type', 'role', 'lien', 'surnoms', 'coordonnees', 'telephone', 'mail',
    'domaine', 'note_ia', 'anniversaire', 'adresse', 'telephone2', 'mail2', 'fonction', 'site_web', 'note'
  ];
  const CHAMPS_TEXTE = CHAMPS;
  const CHAMPS_MODIFIABLES = CHAMPS;

  let donnees = { contacts: [] };

  function maintenant() { return new Date().toISOString(); }
  function dateDuJour() {
    const date = new Date();
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  }

  function listeSurnoms(valeur) {
    const vus = new Set();
    const liste = [];
    for (const item of texte(valeur).split(',').map(morceau => morceau.trim()).filter(Boolean)) {
      const cle = normaliser(item);
      if (vus.has(cle)) continue;
      vus.add(cle);
      liste.push(item);
    }
    return liste;
  }

  function validerTelephone(valeur) {
    const propre = texte(valeur).trim();
    if (!propre) return '';
    if (!/^[0-9+().\s-]{3,30}$/.test(propre) || !/\d/.test(propre)) throw new Error('Vérifie le numéro de téléphone.');
    return propre;
  }

  function validerMail(valeur) {
    const propre = texte(valeur).trim();
    if (!propre) return '';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(propre)) throw new Error('Vérifie l’adresse mail.');
    return propre;
  }

  function validerAnniversaire(valeur) {
    const propre = texte(valeur).trim();
    if (!propre) return '';
    const correspondance = /^(\d{2})-(\d{2})(?:-(\d{4}))?$/.exec(propre);
    if (!correspondance) throw new Error('La date de naissance / anniversaire doit être au format JJ-MM ou JJ-MM-AAAA.');
    const jour = Number(correspondance[1]);
    const mois = Number(correspondance[2]);
    const annee = correspondance[3] ? Number(correspondance[3]) : 2024;
    const date = new Date(annee, mois - 1, jour);
    if (date.getMonth() !== mois - 1 || date.getDate() !== jour) throw new Error('Cette date n’existe pas.');
    return propre;
  }

  function validerSiteWeb(valeur) {
    const propre = texte(valeur).trim();
    if (!propre) return '';
    if (/\s/.test(propre) || !propre.includes('.')) throw new Error('Vérifie le site web.');
    return propre.slice(0, 200);
  }

  function auMoinsUnNomOuSurnom(champs) {
    return Boolean(texte(champs.prenom).trim()) || listeSurnoms(champs.surnoms).length > 0;
  }

  function contactValide(contact) {
    if (!contact || typeof contact !== 'object' || Array.isArray(contact)) return false;
    if (typeof contact.id !== 'string' || !contact.id) return false;
    if (CHAMPS_TEXTE.some(champ => typeof contact[champ] !== 'string')) return false;
    if (!auMoinsUnNomOuSurnom(contact)) return false;
    if (typeof contact.supprime_le !== 'string' || typeof contact.modifie_le !== 'string') return false;
    if (!Array.isArray(contact.historique)) return false;
    return contact.historique.every(entree => entree && typeof entree === 'object'
      && typeof entree.champ === 'string' && typeof entree.ancienne === 'string'
      && typeof entree.nouvelle === 'string' && typeof entree.date === 'string');
  }

  function copierContact(contact) {
    const copie = { id: contact.id };
    for (const champ of CHAMPS) copie[champ] = texte(contact[champ]);
    copie.supprime_le = texte(contact.supprime_le);
    copie.modifie_le = texte(contact.modifie_le);
    copie.historique = contact.historique.map(entree => ({ ...entree }));
    return copie;
  }

  function migrerContactAncien(ancien) {
    const contact = { id: ancien.id };
    for (const champ of CHAMPS) contact[champ] = '';
    contact.nom = texte(ancien.nom);
    contact.surnoms = texte(ancien.surnom);
    contact.telephone = texte(ancien.telephone);
    contact.adresse = texte(ancien.adresse);
    contact.mail = texte(ancien.mail);
    contact.anniversaire = texte(ancien.anniversaire);
    contact.note = texte(ancien.note);
    contact.supprime_le = texte(ancien.supprime_le);
    contact.modifie_le = texte(ancien.modifie_le);
    contact.historique = (Array.isArray(ancien.historique) ? ancien.historique : []).map(entree => ({
      ...entree,
      champ: entree && entree.champ === 'surnom' ? 'surnoms' : entree?.champ
    }));
    return contact;
  }

  function estAncienFormat(brut) {
    return brut && typeof brut === 'object' && !Array.isArray(brut)
      && typeof brut.prenom !== 'string' && typeof brut.surnom === 'string';
  }

  function lireMemoire() {
    try {
      const brut = JSON.parse(localStorage.getItem(cle));
      if (!brut || typeof brut !== 'object' || !Array.isArray(brut.contacts)) return { contacts: [] };
      const contacts = brut.contacts
        .map(item => (estAncienFormat(item) ? migrerContactAncien(item) : item))
        .filter(contactValide)
        .map(copierContact);
      return { contacts };
    } catch (erreur) {
      return { contacts: [] };
    }
  }

  function enregistrer(aEnvoyer = true) {
    localStorage.setItem(cle, JSON.stringify(donnees));
    if (aEnvoyer) {
      localStorage.setItem(cleEnvoi, '1');
      if (typeof vibration !== 'undefined') vibration.courte();
    }
    window.dispatchEvent(new Event('cap-annuaire-changee'));
  }

  function genererId() {
    let id;
    do {
      const aleatoire = Math.floor(Math.random() * 1679616).toString(36).padStart(4, '0');
      id = `C-${Date.now().toString(36)}${aleatoire}`;
    } while (donnees.contacts.some(contact => contact.id === id));
    return id;
  }

  function nomAffichage(contact) {
    const complet = `${texte(contact.prenom)} ${texte(contact.nom)}`.trim();
    if (complet) return complet;
    const premier = listeSurnoms(contact.surnoms)[0];
    return premier || '(sans nom)';
  }

  function tri(liste) {
    return [...liste].sort((a, b) => normaliser(nomAffichage(a)).localeCompare(normaliser(nomAffichage(b)), 'fr'));
  }

  function tous() {
    return tri(donnees.contacts.filter(contact => !contact.supprime_le));
  }

  function supprimes() {
    return tri(donnees.contacts.filter(contact => contact.supprime_le));
  }

  function trouver(id) {
    const contact = donnees.contacts.find(item => item.id === id);
    if (!contact) throw new Error('Ce contact est introuvable.');
    return contact;
  }

  function correspondances(texteRecherche) {
    const recherche = normaliser(texteRecherche);
    if (!recherche) return [];
    const actifs = tous();
    const correspond = (contact, exact) => {
      const prenom = normaliser(contact.prenom);
      const nom = normaliser(contact.nom);
      const surnoms = listeSurnoms(contact.surnoms).map(normaliser);
      if (exact) {
        return prenom === recherche || nom === recherche || surnoms.includes(recherche);
      }
      return prenom.includes(recherche) || nom.includes(recherche) || surnoms.some(surnom => surnom.includes(recherche));
    };
    const exacts = actifs.filter(contact => correspond(contact, true));
    if (exacts.length) return exacts;
    return actifs.filter(contact => correspond(contact, false));
  }

  function validerChamps(champs = {}) {
    const propres = {
      prenom: texte(champs.prenom).replace(/\s+/g, ' ').trim().slice(0, 80),
      nom: texte(champs.nom).replace(/\s+/g, ' ').trim().slice(0, 80),
      type: texte(champs.type).trim().slice(0, 40),
      role: texte(champs.role).trim().slice(0, 60),
      lien: texte(champs.lien).trim().slice(0, 60),
      surnoms: listeSurnoms(champs.surnoms).join(', ').slice(0, 200),
      coordonnees: texte(champs.coordonnees).trim().slice(0, 300),
      telephone: validerTelephone(champs.telephone),
      mail: validerMail(champs.mail),
      domaine: texte(champs.domaine).trim().slice(0, 60),
      note_ia: texte(champs.note_ia).trim().slice(0, 500),
      anniversaire: validerAnniversaire(champs.anniversaire),
      adresse: texte(champs.adresse).trim().slice(0, 300),
      telephone2: validerTelephone(champs.telephone2),
      mail2: validerMail(champs.mail2),
      fonction: texte(champs.fonction).trim().slice(0, 80),
      site_web: validerSiteWeb(champs.site_web),
      note: texte(champs.note).trim().slice(0, 500)
    };
    if (!auMoinsUnNomOuSurnom(propres)) throw new Error('Donne au moins un prénom ou un surnom à ce contact.');
    return propres;
  }

  function creerContact(champs) {
    const propres = validerChamps(champs);
    const contact = {
      id: genererId(),
      ...propres,
      supprime_le: '',
      modifie_le: maintenant(),
      historique: [{ champ: 'créé', ancienne: '', nouvelle: nomAffichage(propres), date: maintenant() }]
    };
    donnees.contacts.push(contact);
    enregistrer();
    return contact;
  }

  function modifierContact(id, champs) {
    const contact = trouver(id);
    const propres = validerChamps({ ...contact, ...champs });
    const date = maintenant();
    let change = false;
    for (const champ of CHAMPS_MODIFIABLES) {
      if (contact[champ] !== propres[champ]) {
        contact.historique.push({ champ, ancienne: contact[champ], nouvelle: propres[champ], date });
        contact[champ] = propres[champ];
        change = true;
      }
    }
    if (change) {
      contact.modifie_le = date;
      enregistrer();
    }
    return contact;
  }

  function supprimerContact(id) {
    const contact = trouver(id);
    if (contact.supprime_le) return contact;
    contact.supprime_le = dateDuJour();
    contact.modifie_le = maintenant();
    contact.historique.push({ champ: 'supprimé', ancienne: '', nouvelle: contact.supprime_le, date: contact.modifie_le });
    enregistrer();
    return contact;
  }

  function restaurerContact(id) {
    const contact = trouver(id);
    if (!contact.supprime_le) return contact;
    const ancienne = contact.supprime_le;
    contact.supprime_le = '';
    contact.modifie_le = maintenant();
    contact.historique.push({ champ: 'restauré', ancienne, nouvelle: '', date: contact.modifie_le });
    enregistrer();
    return contact;
  }

  function fusionnerHistoriques(local, distant) {
    const cle = entree => `${entree.champ}\u0000${entree.date}`;
    const vues = new Set(local.map(cle));
    const ajouts = distant.filter(entree => !vues.has(cle(entree)));
    return [...local, ...ajouts].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
  }

  function fusionner(distant) {
    for (const brut of (distant?.contacts || [])) {
      const contact = estAncienFormat(brut) ? migrerContactAncien(brut) : brut;
      if (!contactValide(contact)) continue;
      const propre = copierContact(contact);
      const local = donnees.contacts.find(item => item.id === propre.id);
      if (!local) {
        donnees.contacts.push(propre);
      } else {
        local.historique = fusionnerHistoriques(local.historique, propre.historique);
        if (propre.modifie_le > local.modifie_le) {
          for (const champ of [...CHAMPS_MODIFIABLES, 'supprime_le', 'modifie_le']) local[champ] = propre[champ];
        }
      }
    }
    enregistrer(false);
  }

  function exporter() {
    return JSON.parse(JSON.stringify(donnees));
  }

  function aEnvoyer() {
    try { return localStorage.getItem(cleEnvoi) === '1'; } catch (erreur) { return false; }
  }

  function marquerEnvoye() {
    try { localStorage.removeItem(cleEnvoi); } catch (erreur) {}
  }

  function recharger() {
    donnees = lireMemoire();
    try { localStorage.setItem(cle, JSON.stringify(donnees)); } catch (erreur) {}
  }

  recharger();
  return {
    tous, supprimes, trouver, correspondances, creerContact, modifierContact, supprimerContact, restaurerContact,
    fusionner, exporter, aEnvoyer, marquerEnvoye, recharger, nomAffichage, listeSurnoms,
    validerTelephone, validerMail, validerAnniversaire, validerSiteWeb, validerChamps, CHAMPS
  };
})();
