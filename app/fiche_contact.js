'use strict';

const ficheContact = (() => {
  const parId = id => document.getElementById(id);
  const dialogue = parId('annuaire');
  const formulaire = parId('formulaire-contact');
  const erreur = parId('erreur-annuaire');
  const statut = parId('statut-annuaire');
  const champsLisibles = {
    nom: 'Nom', surnom: 'Surnom', telephone: 'Téléphone', adresse: 'Adresse',
    mail: 'Mail', anniversaire: 'Anniversaire', note: 'Note'
  };
  const touchesPave = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '+', '0', 'espace'];
  let contact = null;
  let creation = false;
  let origine = null;
  let champVocal = '';

  function noeud(balise, classe, texte) {
    const element = document.createElement(balise);
    if (classe) element.className = classe;
    if (texte !== undefined) element.textContent = texte;
    return element;
  }

  function champ(cle) { return formulaire.elements.namedItem(cle); }
  function texte(valeur) { return valeur === undefined || valeur === null ? '' : String(valeur); }

  function messageErreur(message) {
    erreur.textContent = message;
    erreur.hidden = !message;
    if (message) erreur.scrollIntoView({ block: 'nearest' });
  }

  function afficherVue(vue, focus) {
    for (const [nom, id] of Object.entries({
      liste: 'liste-contacts-vue', consultation: 'consultation-contact', edition: 'formulaire-contact',
      recapitulatif: 'recapitulatif-contact', suppression: 'confirmation-suppression-contact'
    })) parId(id).hidden = nom !== vue;
    messageErreur('');
    statut.hidden = true;
    statut.textContent = '';
    parId('contenu-annuaire').scrollTop = 0;
    focus?.focus({ preventScroll: true });
  }

  function carte(titre, valeur, lien) {
    const section = noeud('section', 'carte-contact');
    section.append(noeud('h3', '', titre), noeud('p', '', valeur));
    if (lien) {
      const ancre = noeud('a', 'lien-fiche-contact', lien.texte);
      ancre.href = lien.href;
      section.append(ancre);
    }
    return section;
  }

  function valeurLisible(cle, valeur) {
    return texte(valeur).trim() || '—';
  }

  // --- Liste ---

  function ligneContact(item) {
    const li = noeud('li');
    const bouton = noeud('button', 'ouvrir-contact', item.surnom ? `${item.nom} (${item.surnom})` : item.nom);
    bouton.type = 'button';
    bouton.addEventListener('click', () => ouvrirConsultation(item, bouton));
    li.append(bouton);
    return li;
  }

  function ligneSupprime(item) {
    const li = noeud('li', 'ligne-contact-supprime');
    li.append(noeud('span', '', `${item.nom} (supprimé le ${item.supprime_le})`));
    const restaurer = noeud('button', '', 'Restaurer');
    restaurer.type = 'button';
    restaurer.addEventListener('click', () => {
      annuaire.restaurerContact(item.id);
      renduListe();
      statut.textContent = `« ${item.nom} » est restauré dans l’annuaire.`;
      statut.hidden = false;
    });
    li.append(restaurer);
    return li;
  }

  function renduListe() {
    const recherche = parId('recherche-contacts').value.trim();
    const items = recherche ? annuaire.correspondances(recherche) : annuaire.tous();
    parId('liste-contacts').replaceChildren(...items.map(ligneContact));
    const supprimes = annuaire.supprimes();
    parId('basculer-contacts-supprimes').textContent = `Contacts supprimés (${supprimes.length})`;
    parId('basculer-contacts-supprimes').hidden = supprimes.length === 0;
    parId('liste-contacts-supprimes').replaceChildren(...supprimes.map(ligneSupprime));
  }

  parId('recherche-contacts').addEventListener('input', renduListe);
  parId('basculer-contacts-supprimes').addEventListener('click', () => {
    const ouverte = !parId('liste-contacts-supprimes').hidden;
    parId('liste-contacts-supprimes').hidden = ouverte;
    parId('basculer-contacts-supprimes').setAttribute('aria-expanded', String(!ouverte));
  });
  parId('nouveau-contact').addEventListener('click', bouton => ouvrirEdition(null, bouton.currentTarget));

  // --- Consultation ---

  function afficherConsultation() {
    parId('titre-annuaire').textContent = contact.nom;
    const telephone = texte(contact.telephone).trim();
    const numero = telephone.replace(/[^\d+]/g, '');
    const mail = texte(contact.mail).trim();
    const adresse = texte(contact.adresse).trim();
    const historique = contact.historique.slice().reverse()
      .map(entree => `${entree.date.slice(0, 10)} — ${entree.champ}${entree.ancienne ? ` : « ${entree.ancienne} » → « ${entree.nouvelle} »` : entree.nouvelle ? ` : ${entree.nouvelle}` : ''}`)
      .join('\n');
    parId('cartes-contact').replaceChildren(
      carte('Surnom', valeurLisible('surnom', contact.surnom)),
      carte('Téléphone', telephone || '—', /\d/.test(numero) ? { texte: 'Appeler', href: `tel:${numero}` } : null),
      carte('Adresse', adresse || '—', adresse ? { texte: 'Itinéraire', href: `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(adresse)}` } : null),
      carte('Mail', mail || '—', mail ? { texte: 'Écrire', href: `mailto:${encodeURIComponent(mail)}` } : null),
      carte('Anniversaire', valeurLisible('anniversaire', contact.anniversaire)),
      carte('Note', valeurLisible('note', contact.note)),
      carte('Historique', historique || 'Aucun changement enregistré.')
    );
    afficherVue('consultation', parId('modifier-contact'));
  }

  function ouvrirConsultation(item, boutonOrigine) {
    if (dialogue.open && !parId('liste-contacts-vue').hidden) {
      contact = item;
      origine = boutonOrigine || document.activeElement;
      afficherConsultation();
      return;
    }
  }

  parId('modifier-contact').addEventListener('click', () => ouvrirEdition(contact, parId('modifier-contact')));
  parId('supprimer-contact').addEventListener('click', () => {
    parId('intitule-suppression-contact').textContent = contact.nom;
    afficherVue('suppression', parId('annuler-suppression-contact'));
  });
  parId('annuler-suppression-contact').addEventListener('click', () => afficherConsultation());
  parId('confirmer-suppression-contact').addEventListener('click', () => {
    const nom = contact.nom;
    annuaire.supprimerContact(contact.id);
    renduListe();
    afficherVue('liste', parId('nouveau-contact'));
    statut.textContent = `« ${nom} » a été supprimé. Tu peux le restaurer depuis « Contacts supprimés ».`;
    statut.hidden = false;
  });

  // --- Clavier numérique ---

  function remplirPave() {
    const zone = parId('pave-telephone').querySelector('.touches-pave');
    zone.replaceChildren(...touchesPave.map(touche => {
      const bouton = noeud('button', 'touche-pave', touche === 'espace' ? ' ' : touche);
      bouton.type = 'button';
      bouton.setAttribute('aria-label', touche === 'espace' ? 'Espace' : touche);
      bouton.addEventListener('click', () => {
        champ('telephone').value += touche === 'espace' ? ' ' : touche;
      });
      return bouton;
    }));
  }

  parId('clavier-telephone').addEventListener('click', () => {
    parId('pave-telephone').hidden = false;
  });
  parId('pave-effacer').addEventListener('click', () => {
    champ('telephone').value = champ('telephone').value.slice(0, -1);
  });
  parId('pave-fermer').addEventListener('click', () => {
    parId('pave-telephone').hidden = true;
  });

  // --- Dictée vocale ---

  function ecouterChamp(nomChamp, bouton) {
    if (!dictee.disponible()) return;
    if (dictee.enCours() && champVocal === nomChamp) {
      dictee.arreter();
      return;
    }
    champVocal = nomChamp;
    bouton.setAttribute('aria-pressed', 'true');
    messageErreur('');
    statut.textContent = 'Je t’écoute…';
    statut.hidden = false;
    let recu = false;
    dictee.demarrer({
      surProvisoire(texteRecu) {
        if (recu) return;
        statut.textContent = `J’entends : « ${texteRecu.trim()} »`;
      },
      surFinal(texteRecu) {
        if (recu) return;
        recu = true;
        champ(nomChamp).value = texteRecu.trim();
        statut.hidden = true;
      },
      surErreur() {},
      surFin() {
        bouton.setAttribute('aria-pressed', 'false');
        if (!recu) {
          statut.textContent = 'Je n’ai rien entendu. Réessaie ou écris directement.';
        }
      }
    });
  }

  parId('dire-telephone').addEventListener('click', event => ecouterChamp('telephone', event.currentTarget));
  parId('dire-adresse').addEventListener('click', event => ecouterChamp('adresse', event.currentTarget));

  // --- Édition ---

  function remplirFormulaire() {
    for (const cle of Object.keys(champsLisibles)) champ(cle).value = texte(contact?.[cle]);
    parId('dire-telephone').hidden = !dictee.disponible();
    parId('dire-adresse').hidden = !dictee.disponible();
    parId('pave-telephone').hidden = true;
    parId('enregistrer-contact').textContent = creation ? 'Vérifier' : 'Enregistrer';
    parId('titre-recapitulatif-contact').textContent = creation ? 'Contact à ajouter' : 'Ce qui va changer';
  }

  function ouvrirEdition(item, boutonOrigine) {
    creation = !item;
    contact = item || { nom: '', surnom: '', telephone: '', adresse: '', mail: '', anniversaire: '', note: '' };
    if (!dialogue.open) {
      origine = boutonOrigine || document.activeElement;
      dialogue.showModal();
    }
    remplirFormulaire();
    parId('titre-annuaire').textContent = creation ? 'Nouveau contact' : `Modifier ${contact.nom}`;
    afficherVue('edition', champ('nom'));
  }

  parId('annuler-edition-contact').addEventListener('click', () => {
    if (creation) { afficherVue('liste', parId('nouveau-contact')); }
    else afficherConsultation();
  });
  parId('revenir-contact').addEventListener('click', () => afficherVue('edition', parId('enregistrer-contact')));

  let proposes = null;

  formulaire.addEventListener('submit', event => {
    event.preventDefault();
    messageErreur('');
    const brut = {};
    for (const cle of Object.keys(champsLisibles)) brut[cle] = champ(cle).value;
    let valides;
    try {
      valides = annuaire.validerChamps(brut);
    } catch (echec) {
      messageErreur(echec instanceof Error ? echec.message : 'Vérifie les champs du contact.');
      return;
    }
    const changements = {};
    for (const cle of Object.keys(champsLisibles)) {
      if (creation || valides[cle] !== texte(contact[cle])) changements[cle] = valides[cle];
    }
    proposes = valides;
    const lignes = Object.entries(changements).map(([cle, valeur]) => {
      const section = noeud('section', 'carte-contact');
      section.append(noeud('h4', '', champsLisibles[cle]), noeud('p', '',
        creation ? valeurLisible(cle, valeur) : `${valeurLisible(cle, contact[cle])} → ${valeurLisible(cle, valeur)}`));
      return section;
    });
    parId('changements-contact').replaceChildren(...(lignes.length ? lignes : [noeud('p', '', 'Aucun changement.')]));
    parId('confirmer-contact').hidden = lignes.length === 0;
    afficherVue('recapitulatif', parId('titre-recapitulatif-contact'));
  });

  parId('confirmer-contact').addEventListener('click', () => {
    try {
      if (creation) {
        contact = annuaire.creerContact(proposes);
        creation = false;
      } else {
        contact = annuaire.modifierContact(contact.id, proposes);
      }
    } catch (echec) {
      afficherVue('edition', parId('enregistrer-contact'));
      messageErreur(echec instanceof Error ? echec.message : 'Le contact n’a pas pu être enregistré. Réessaie.');
      return;
    }
    renduListe();
    afficherConsultation();
    statut.textContent = 'Contact enregistré dans l’annuaire.';
    statut.hidden = false;
  });

  // --- Ouverture / fermeture du dialogue ---

  function navenir() {
    if (!parId('liste-contacts-vue').hidden) { dialogue.close(); return; }
    if (!parId('consultation-contact').hidden) { afficherVue('liste', parId('nouveau-contact')); return; }
    if (!formulaire.hidden) {
      if (creation) afficherVue('liste', parId('nouveau-contact'));
      else afficherConsultation();
      return;
    }
    if (!parId('recapitulatif-contact').hidden) { afficherVue('edition', parId('enregistrer-contact')); return; }
    if (!parId('confirmation-suppression-contact').hidden) { afficherConsultation(); return; }
    dialogue.close();
  }
  parId('retour-annuaire').addEventListener('click', navenir);
  fermetureFenetres.installer(dialogue, { retour: navenir, cle: () => 'annuaire' });

  dialogue.addEventListener('close', () => {
    creation = false;
    formulaire.reset();
    origine?.focus?.({ preventScroll: true });
  });

  function ouvrirListe() {
    if (dialogue.open) return;
    parId('titre-annuaire').textContent = 'Annuaire';
    origine = document.activeElement;
    parId('recherche-contacts').value = '';
    renduListe();
    dialogue.showModal();
    afficherVue('liste', parId('nouveau-contact'));
  }

  remplirPave();
  return { ouvrirListe };
})();
