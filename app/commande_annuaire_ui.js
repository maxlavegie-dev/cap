'use strict';

// Affiche à l'écran les commandes vocales de l'annuaire (fiche, appel, mail), une fois comprises
// par commandes_annuaire.js. Zéro envoi automatique : un appel ou un mail n'est jamais déclenché
// sans que Max touche le bouton « Oui ». L'IA ne voit rien de ce fichier ni de l'annuaire.
const commandeAnnuaireUI = (() => {
  const parId = id => document.getElementById(id);
  const dialogue = parId('commande-annuaire');
  const corps = parId('commande-annuaire-corps');
  let origine = null;

  function noeud(balise, classe, texte) {
    const element = document.createElement(balise);
    if (classe) element.className = classe;
    if (texte !== undefined) element.textContent = texte;
    return element;
  }

  function ouvrir() {
    if (!dialogue.open) {
      origine = document.activeElement;
      dialogue.showModal();
    }
  }

  function fermer() {
    if (dialogue.open) dialogue.close();
  }

  dialogue.addEventListener('close', () => {
    corps.replaceChildren();
    origine?.focus?.({ preventScroll: true });
  });

  function direSiPossible(texte) {
    if (typeof voix !== 'undefined' && voix.dire) voix.dire(texte);
  }

  // Remplaçable par les tests automatiques, pour ne jamais vraiment naviguer pendant un test.
  let naviguer = url => { window.location.href = url; };

  function afficherMessage(texte) {
    const bouton = noeud('button', 'commande-annuaire-fermer', 'Fermer');
    bouton.type = 'button';
    bouton.addEventListener('click', fermer);
    corps.replaceChildren(noeud('p', 'commande-annuaire-message', texte), bouton);
    ouvrir();
    direSiPossible(texte);
    bouton.focus({ preventScroll: true });
  }

  function afficherChoixContacts(contacts, suite) {
    const boutons = contacts.map(contact => {
      const bouton = noeud('button', 'choix-grand-affichage', annuaire.nomAffichage(contact));
      bouton.type = 'button';
      bouton.addEventListener('click', () => suite(contact));
      return bouton;
    });
    corps.replaceChildren(
      noeud('p', 'choix-grand-affichage-titre', 'Plusieurs personnes correspondent. Touche la bonne :'),
      ...boutons
    );
    ouvrir();
    boutons[0]?.focus({ preventScroll: true });
  }

  function afficherConfirmation(nomAffiche, sousTexte, surOui) {
    const oui = noeud('button', '', 'Oui');
    const non = noeud('button', '', 'Non');
    oui.type = 'button';
    non.type = 'button';
    oui.addEventListener('click', () => { fermer(); surOui(); });
    non.addEventListener('click', fermer);
    const boutons = noeud('div', 'commande-annuaire-boutons');
    boutons.append(oui, non);
    corps.replaceChildren(
      noeud('p', 'commande-annuaire-texte', nomAffiche),
      noeud('p', 'commande-annuaire-sous-texte', sousTexte),
      boutons
    );
    ouvrir();
    oui.focus({ preventScroll: true });
  }

  function traiterAppel(contact) {
    const numero = String(contact.telephone || '').trim();
    if (!numero) {
      afficherMessage(`${annuaire.nomAffichage(contact)} n’a pas de numéro de téléphone enregistré.`);
      return;
    }
    const chiffres = numero.replace(/[^\d+]/g, '');
    afficherConfirmation(annuaire.nomAffichage(contact), numero, () => {
      naviguer(`tel:${chiffres}`);
    });
  }

  function traiterMail(contact, message) {
    const mail = String(contact.mail || '').trim();
    if (!mail) {
      afficherMessage(`${annuaire.nomAffichage(contact)} n’a pas d’adresse mail enregistrée.`);
      return;
    }
    afficherConfirmation(annuaire.nomAffichage(contact), mail, () => {
      // Le paramètre body est toujours présent, même vide : certains téléphones Android
      // affichent sinon le mot « undefined » dans le corps du brouillon quand il est absent.
      naviguer(`mailto:${encodeURIComponent(mail)}?body=${encodeURIComponent(message || '')}`);
    });
  }

  function traiterFiche(contact) {
    fermer();
    ficheContact.ouvrirFiche(contact);
  }

  function traiter(detection) {
    const resolu = commandesAnnuaire.resoudreContact(detection.nom);
    if (resolu.statut === 'aucun') {
      afficherMessage(`Je ne trouve personne qui s’appelle « ${detection.nom} ».`);
      return;
    }
    const action = { fiche: traiterFiche, appel: traiterAppel, mail: traiterMail }[detection.action];
    if (!action) return;
    const parametresSupplementaires = detection.action === 'mail' ? [detection.message] : [];
    if (resolu.statut === 'un') {
      action(resolu.contact, ...parametresSupplementaires);
      return;
    }
    afficherChoixContacts(resolu.contacts, contact => action(contact, ...parametresSupplementaires));
  }

  fermetureFenetres.installer(dialogue, { retour: fermer, cle: () => 'commande-annuaire' });

  // _definirNaviguer : réservé aux tests automatiques, pour ne jamais vraiment appeler ou mailer.
  return { traiter, _definirNaviguer: fonction => { naviguer = fonction; } };
})();
