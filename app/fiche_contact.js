'use strict';

const ficheContact = (() => {
  const parId = id => document.getElementById(id);
  const dialogue = parId('annuaire');
  const formulaire = parId('formulaire-contact');
  const erreur = parId('erreur-annuaire');
  const statut = parId('statut-annuaire');
  const champsLisibles = {
    prenom: 'Prénom', nom: 'Nom', surnoms: 'Appellations et surnoms', type: 'Type', role: 'Rôle',
    lien: 'Lien avec Max', telephone: 'Téléphone', telephone2: 'Deuxième téléphone', mail: 'Mail',
    mail2: 'Deuxième mail', adresse: 'Adresse postale', coordonnees: 'Coordonnées',
    anniversaire: 'Date de naissance / anniversaire', domaine: 'Domaine', fonction: 'Fonction / titre',
    site_web: 'Site web', note_ia: 'Note pour IA', note: 'Note'
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
    parId('retour-annuaire').hidden = vue === 'liste';
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
    const surnoms = annuaire.listeSurnoms(item.surnoms);
    const intitule = annuaire.nomAffichage(item);
    const bouton = noeud('button', 'ouvrir-contact', surnoms.length ? `${intitule} (${surnoms.join(', ')})` : intitule);
    bouton.type = 'button';
    bouton.addEventListener('click', () => ouvrirConsultation(item, bouton));
    li.append(bouton);
    return li;
  }

  function ligneSupprime(item) {
    const li = noeud('li', 'ligne-contact-supprime');
    const intitule = annuaire.nomAffichage(item);
    li.append(noeud('span', '', `${intitule} (supprimé le ${item.supprime_le})`));
    const restaurer = noeud('button', '', 'Restaurer');
    restaurer.type = 'button';
    restaurer.addEventListener('click', () => {
      annuaire.restaurerContact(item.id);
      renduListe();
      statut.textContent = `« ${intitule} » est restauré dans l’annuaire.`;
      statut.hidden = false;
    });
    li.append(restaurer);
    return li;
  }

  function renduListe() {
    const recherche = parId('recherche-contacts').value.trim();
    const items = recherche ? annuaire.correspondances(recherche) : annuaire.tous();
    parId('liste-contacts').replaceChildren(...items.map(ligneContact));
    const compteur = parId('compteur-resultats-contacts');
    if (!recherche) {
      compteur.textContent = '';
    } else {
      compteur.textContent = items.length === 0 ? 'Aucun résultat'
        : items.length === 1 ? '1 résultat' : `${items.length} résultats`;
    }
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

  function carteTelephone(titre, valeur) {
    const telephone = texte(valeur).trim();
    const numero = telephone.replace(/[^\d+]/g, '');
    return carte(titre, telephone || '—', /\d/.test(numero) ? { texte: 'Appeler', href: `tel:${numero}` } : null);
  }

  function carteMail(titre, valeur) {
    const mail = texte(valeur).trim();
    return carte(titre, mail || '—', mail ? { texte: 'Écrire', href: `mailto:${encodeURIComponent(mail)}` } : null);
  }

  function afficherConsultation() {
    parId('titre-annuaire').textContent = annuaire.nomAffichage(contact);
    const adresse = texte(contact.adresse).trim();
    const siteWeb = texte(contact.site_web).trim();
    const historique = contact.historique.slice().reverse()
      .map(entree => `${entree.date.slice(0, 10)} — ${entree.champ}${entree.ancienne ? ` : « ${entree.ancienne} » → « ${entree.nouvelle} »` : entree.nouvelle ? ` : ${entree.nouvelle}` : ''}`)
      .join('\n');
    parId('cartes-contact').replaceChildren(
      carte('Appellations et surnoms', valeurLisible('surnoms', contact.surnoms)),
      carte('Type', valeurLisible('type', contact.type)),
      carte('Rôle', valeurLisible('role', contact.role)),
      carte('Lien avec Max', valeurLisible('lien', contact.lien)),
      carteTelephone('Téléphone', contact.telephone),
      carteTelephone('Deuxième téléphone', contact.telephone2),
      carteMail('Mail', contact.mail),
      carteMail('Deuxième mail', contact.mail2),
      carte('Adresse postale', adresse || '—', adresse ? { texte: 'Itinéraire', href: `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(adresse)}` } : null),
      carte('Coordonnées', valeurLisible('coordonnees', contact.coordonnees)),
      carte('Date de naissance / anniversaire', annuaire.anniversaireLisible(contact.anniversaire) || '—'),
      carte('Domaine', valeurLisible('domaine', contact.domaine)),
      carte('Fonction / titre', valeurLisible('fonction', contact.fonction)),
      carte('Site web', siteWeb || '—', siteWeb ? { texte: 'Ouvrir', href: /^https?:\/\//.test(siteWeb) ? siteWeb : `https://${siteWeb}` } : null),
      carte('Note pour IA', valeurLisible('note_ia', contact.note_ia)),
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
    parId('intitule-suppression-contact').textContent = annuaire.nomAffichage(contact);
    afficherVue('suppression', parId('annuler-suppression-contact'));
  });
  parId('annuler-suppression-contact').addEventListener('click', () => afficherConsultation());
  parId('confirmer-suppression-contact').addEventListener('click', () => {
    const intitule = annuaire.nomAffichage(contact);
    annuaire.supprimerContact(contact.id);
    renduListe();
    afficherVue('liste', parId('nouveau-contact'));
    statut.textContent = `« ${intitule} » a été supprimé. Tu peux le restaurer depuis « Contacts supprimés ».`;
    statut.hidden = false;
  });

  // --- Clavier numérique ---

  function installerPave(idPave, idEffacer, idFermer, idClavier, nomChamp) {
    const zone = parId(idPave).querySelector('.touches-pave');
    zone.replaceChildren(...touchesPave.map(touche => {
      const bouton = noeud('button', 'touche-pave', touche === 'espace' ? ' ' : touche);
      bouton.type = 'button';
      bouton.setAttribute('aria-label', touche === 'espace' ? 'Espace' : touche);
      bouton.addEventListener('click', () => {
        champ(nomChamp).value += touche === 'espace' ? ' ' : touche;
      });
      return bouton;
    }));
    parId(idClavier).addEventListener('click', () => { parId(idPave).hidden = false; });
    parId(idEffacer).addEventListener('click', () => {
      champ(nomChamp).value = champ(nomChamp).value.slice(0, -1);
    });
    parId(idFermer).addEventListener('click', () => {
      parId(idPave).hidden = true;
      grandAffichageDepuisChamp(nomChamp);
    });
  }

  // --- Fenêtre très gros pendant 8 secondes ---

  const dialogueGrand = parId('grand-affichage');
  const texteGrand = parId('grand-affichage-texte');
  let delaiGrand;

  function fermerGrandAffichage() {
    clearTimeout(delaiGrand);
    if (dialogueGrand.open) dialogueGrand.close();
  }

  function ajusterTailleUneLigne(element) {
    const tailleMax = 96;
    const tailleMin = 22;
    let taille = tailleMax;
    element.style.fontSize = taille + 'px';
    while (taille > tailleMin && element.scrollWidth > element.clientWidth) {
      taille -= 2;
      element.style.fontSize = taille + 'px';
    }
  }

  function afficherGrandAffichage(valeur, options) {
    const propre = texte(valeur).trim();
    if (!propre) return;
    clearTimeout(delaiGrand);
    texteGrand.textContent = propre;
    const uneLigne = Boolean(options && options.uneLigne) || propre.length <= 20;
    if (uneLigne) {
      texteGrand.removeAttribute('data-long');
    } else {
      texteGrand.setAttribute('data-long', '1');
      texteGrand.style.fontSize = '';
    }
    if (!dialogueGrand.open) dialogueGrand.showModal();
    if (uneLigne) ajusterTailleUneLigne(texteGrand);
    delaiGrand = setTimeout(fermerGrandAffichage, 8000);
  }

  function estChampTelephone(nomChamp) {
    return nomChamp === 'telephone' || nomChamp === 'telephone2';
  }

  function grandAffichageDepuisChamp(nomChamp) {
    if (nomChamp === 'anniversaire') { gererAnniversaireSaisie(champ(nomChamp).value); return; }
    afficherGrandAffichage(champ(nomChamp).value, { uneLigne: estChampTelephone(nomChamp) });
  }

  dialogueGrand.addEventListener('click', fermerGrandAffichage);
  dialogueGrand.addEventListener('close', () => clearTimeout(delaiGrand));

  function afficherChoixAnniversaire(options) {
    clearTimeout(delaiGrand);
    texteGrand.removeAttribute('data-long');
    texteGrand.replaceChildren(
      noeud('p', 'choix-grand-affichage-titre', 'Je ne suis pas sûr. Touche la bonne date :'),
      ...options.map(option => {
        const bouton = noeud('button', 'choix-grand-affichage', option.lisible);
        bouton.type = 'button';
        bouton.addEventListener('click', event => {
          event.stopPropagation();
          champ('anniversaire').value = option.valeur;
          fermerGrandAffichage();
          afficherGrandAffichage(option.lisible);
        });
        return bouton;
      })
    );
    if (!dialogueGrand.open) dialogueGrand.showModal();
  }

  function gererAnniversaireSaisie(valeurBrute) {
    if (!texte(valeurBrute).trim()) return;
    let resultat;
    try {
      resultat = annuaire.analyserAnniversaire(valeurBrute);
    } catch (echec) {
      return;
    }
    if (!resultat.ok) { afficherChoixAnniversaire(resultat.options); return; }
    if (resultat.valeur) {
      champ('anniversaire').value = resultat.valeur;
      afficherGrandAffichage(resultat.lisible);
    }
  }

  champ('anniversaire').addEventListener('blur', () => gererAnniversaireSaisie(champ('anniversaire').value));

  // --- Dictée vocale ---

  const CHAMPS_MAIL = new Set(['mail', 'mail2']);

  function normaliserMailDicte(valeur) {
    let propre = ` ${valeur.toLocaleLowerCase('fr').trim()} `;
    propre = propre.replace(/\s+arobase\s+/g, '@');
    propre = propre.replace(/\s+point\s+/g, '.');
    propre = propre.replace(/\s+tiret\s+/g, '-');
    propre = propre.replace(/\s+underscore\s+/g, '_');
    return propre.replace(/\s+/g, '').trim();
  }

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
        statut.hidden = true;
        if (nomChamp === 'anniversaire') {
          champ(nomChamp).value = texteRecu.trim();
          gererAnniversaireSaisie(texteRecu);
          return;
        }
        const valeur = CHAMPS_MAIL.has(nomChamp) ? normaliserMailDicte(texteRecu) : texteRecu.trim();
        champ(nomChamp).value = valeur;
        afficherGrandAffichage(valeur, { uneLigne: estChampTelephone(nomChamp) });
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

  for (const bouton of document.querySelectorAll('.micro-champ')) {
    bouton.addEventListener('click', event => ecouterChamp(bouton.dataset.champ, event.currentTarget));
  }

  // --- Édition ---

  function remplirChampType() {
    const selecteur = champ('type');
    const valeur = texte(contact?.type);
    const option = Array.from(selecteur.options).find(item => item.value === valeur);
    Array.from(selecteur.querySelectorAll('.option-type-ancienne')).forEach(item => item.remove());
    if (!option && valeur) {
      const ancienne = noeud('option', 'option-type-ancienne', valeur);
      ancienne.value = valeur;
      selecteur.append(ancienne);
    }
    selecteur.value = valeur;
  }

  function remplirFormulaire() {
    for (const cle of Object.keys(champsLisibles)) {
      if (cle === 'type') continue;
      champ(cle).value = texte(contact?.[cle]);
    }
    remplirChampType();
    for (const bouton of document.querySelectorAll('.micro-champ')) bouton.hidden = !dictee.disponible();
    parId('pave-telephone').hidden = true;
    parId('pave-telephone2').hidden = true;
    parId('enregistrer-contact').textContent = creation ? 'Vérifier' : 'Enregistrer';
    parId('titre-recapitulatif-contact').textContent = creation ? 'Contact à ajouter' : 'Ce qui va changer';
  }

  function ouvrirEdition(item, boutonOrigine) {
    creation = !item;
    contact = item || Object.fromEntries(annuaire.CHAMPS.map(cle => [cle, '']));
    if (creation) contact.type = 'Personne';
    if (!dialogue.open) {
      origine = boutonOrigine || document.activeElement;
      dialogue.showModal();
    }
    remplirFormulaire();
    parId('titre-annuaire').textContent = creation ? 'Nouveau contact' : `Modifier ${annuaire.nomAffichage(contact)}`;
    afficherVue('edition', champ('prenom'));
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

  function ajusterHauteurClavier() {
    if (!window.visualViewport) return;
    document.documentElement.style.setProperty('--hauteur-annuaire-clavier', `${window.visualViewport.height}px`);
  }
  if (window.visualViewport) window.visualViewport.addEventListener('resize', ajusterHauteurClavier);

  function ouvrirListe() {
    if (dialogue.open) return;
    parId('titre-annuaire').textContent = 'Annuaire';
    origine = document.activeElement;
    parId('recherche-contacts').value = '';
    renduListe();
    dialogue.showModal();
    afficherVue('liste', parId('nouveau-contact'));
    ajusterHauteurClavier();
  }

  installerPave('pave-telephone', 'pave-effacer', 'pave-fermer', 'clavier-telephone', 'telephone');
  installerPave('pave-telephone2', 'pave-effacer2', 'pave-fermer2', 'clavier-telephone2', 'telephone2');
  return { ouvrirListe };
})();
