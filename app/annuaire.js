'use strict';

const annuaire = (() => {
  const cle = 'cap_annuaire_v1';
  const cleEnvoi = 'cap_annuaire_a_envoyer_v1';
  const texte = valeur => (typeof valeur === 'string' ? valeur : '');
  const normaliser = valeur => texte(valeur).toLocaleLowerCase('fr').normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
  const CHAMPS_TEXTE = ['nom', 'surnom', 'telephone', 'adresse', 'mail', 'anniversaire', 'note'];
  const CHAMPS_MODIFIABLES = ['nom', 'surnom', 'telephone', 'adresse', 'mail', 'anniversaire', 'note'];
  let donnees = { contacts: [] };

  function maintenant() { return new Date().toISOString(); }
  function dateDuJour() {
    const date = new Date();
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
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
    if (!/^\d{2}-\d{2}$/.test(propre)) throw new Error('L’anniversaire doit être au format JJ-MM.');
    const [jour, mois] = propre.split('-').map(Number);
    const date = new Date(2024, mois - 1, jour);
    if (date.getMonth() !== mois - 1 || date.getDate() !== jour) throw new Error('Cette date d’anniversaire n’existe pas.');
    return propre;
  }

  function contactValide(contact) {
    if (!contact || typeof contact !== 'object' || Array.isArray(contact)) return false;
    if (typeof contact.id !== 'string' || !contact.id) return false;
    if (CHAMPS_TEXTE.some(champ => typeof contact[champ] !== 'string')) return false;
    if (!contact.nom.trim()) return false;
    if (typeof contact.supprime_le !== 'string' || typeof contact.modifie_le !== 'string') return false;
    if (!Array.isArray(contact.historique)) return false;
    return contact.historique.every(entree => entree && typeof entree === 'object'
      && typeof entree.champ === 'string' && typeof entree.ancienne === 'string'
      && typeof entree.nouvelle === 'string' && typeof entree.date === 'string');
  }

  function copierContact(contact) {
    return {
      id: contact.id,
      nom: contact.nom.trim(),
      surnom: texte(contact.surnom),
      telephone: texte(contact.telephone),
      adresse: texte(contact.adresse),
      mail: texte(contact.mail),
      anniversaire: texte(contact.anniversaire),
      note: texte(contact.note),
      supprime_le: texte(contact.supprime_le),
      modifie_le: texte(contact.modifie_le),
      historique: contact.historique.map(entree => ({ ...entree }))
    };
  }

  function lireMemoire() {
    try {
      const brut = JSON.parse(localStorage.getItem(cle));
      if (!brut || typeof brut !== 'object' || !Array.isArray(brut.contacts)) return { contacts: [] };
      return { contacts: brut.contacts.filter(contactValide).map(copierContact) };
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

  function tri(liste) {
    return [...liste].sort((a, b) => normaliser(a.nom).localeCompare(normaliser(b.nom), 'fr'));
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
    const exacts = actifs.filter(contact => normaliser(contact.nom) === recherche || normaliser(contact.surnom) === recherche);
    if (exacts.length) return exacts;
    return actifs.filter(contact => normaliser(contact.nom).includes(recherche) || normaliser(contact.surnom).includes(recherche));
  }

  function validerChamps(champs = {}) {
    const nom = texte(champs.nom).replace(/\s+/g, ' ').trim();
    if (!nom) throw new Error('Donne un nom à ce contact.');
    if (nom.length > 80) throw new Error('Le nom est trop long.');
    return {
      nom,
      surnom: texte(champs.surnom).replace(/\s+/g, ' ').trim().slice(0, 60),
      telephone: validerTelephone(champs.telephone),
      adresse: texte(champs.adresse).trim().slice(0, 300),
      mail: validerMail(champs.mail),
      anniversaire: validerAnniversaire(champs.anniversaire),
      note: texte(champs.note).trim().slice(0, 500)
    };
  }

  function creerContact(champs) {
    const propres = validerChamps(champs);
    const contact = {
      id: genererId(),
      ...propres,
      supprime_le: '',
      modifie_le: maintenant(),
      historique: [{ champ: 'créé', ancienne: '', nouvelle: propres.nom, date: maintenant() }]
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
    for (const contact of (distant?.contacts || []).filter(contactValide).map(copierContact)) {
      const local = donnees.contacts.find(item => item.id === contact.id);
      if (!local) {
        donnees.contacts.push(contact);
      } else {
        local.historique = fusionnerHistoriques(local.historique, contact.historique);
        if (contact.modifie_le > local.modifie_le) {
          for (const champ of [...CHAMPS_MODIFIABLES, 'supprime_le', 'modifie_le']) local[champ] = contact[champ];
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
    fusionner, exporter, aEnvoyer, marquerEnvoye, recharger,
    validerTelephone, validerMail, validerAnniversaire, validerChamps
  };
})();
