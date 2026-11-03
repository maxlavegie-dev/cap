'use strict';

// Relie fichiersVocaux / fichiersVocauxEcheancier / fichiersVocauxAFaire / fichiersVocauxNotes
// (comprendre la phrase, sans IA) à fichiersVocauxDrive (lire/écrire le fichier Markdown) et au
// journal des actions. N'efface jamais une ligne existante.
const fichiersVocauxControleur = (() => {
  const NOMS_LISIBLES = {
    liste_courses: 'ta liste de courses',
    choses_a_acheter: 'tes choses à acheter',
    films_a_voir: 'tes films à voir',
    livres_a_lire: 'tes livres à lire'
  };

  let session = null; // { fichier, morceaux: [] } — dictée libre en cours (Bloc-notes, Brouillon vocal)

  function pret() {
    return typeof navigator === 'undefined' || navigator.onLine !== false
      ? googleConnexion.connecte() : false;
  }

  function messagePasPret() {
    return navigator.onLine === false
      ? "Pas de connexion : je ne peux pas encore toucher à tes fichiers hors connexion."
      : "Connecte-toi à Google pour que je touche à tes fichiers.";
  }

  function consigner(texte, compris, fait) {
    if (typeof journalActions === 'undefined') return;
    try { journalActions.consigner({ source: 'Cap', entree: texte, compris, fait }); } catch (erreur) {}
  }

  // ---------- Listes simples (courses, achats, films, livres) ----------

  async function traiterListe(commande) {
    const nomFichier = REGLAGES_GOOGLE.fichiers_vocaux[commande.fichier];
    const libelle = NOMS_LISIBLES[commande.fichier];
    if (commande.type === 'ajouter') {
      const resultat = await fichiersVocauxDrive.modifier(commande.fichier, nomFichier,
        contenu => fichiersVocaux.ajouterElements(contenu, commande.produits));
      const message = resultat.ajoutes.length
        ? `C'est noté. Ajouté à ${libelle} : ${resultat.ajoutes.join(', ')}.`
        : `Déjà dans ${libelle}, rien ajouté.`;
      consigner(commande.produits.join(', '), `ajouter à ${libelle}`, message);
      return { type: 'reponse', message, parole: "C'est noté." };
    }
    if (commande.type === 'retirer') {
      const resultat = await fichiersVocauxDrive.modifier(commande.fichier, nomFichier,
        contenu => fichiersVocaux.retirerElement(contenu, commande.produit));
      const message = resultat.retire
        ? `C'est noté. Retiré de ${libelle} : ${resultat.nom}.`
        : `Je ne trouve pas « ${commande.produit} » dans ${libelle}.`;
      consigner(commande.produit, `retirer de ${libelle}`, message);
      return { type: 'reponse', message, parole: "C'est noté." };
    }
    const id = await fichiersVocauxDrive.trouverOuCreerFichier(commande.fichier, nomFichier);
    const contenu = await fichiersVocauxDrive.lireTexte(id);
    const elements = fichiersVocaux.elementsActifs(contenu);
    const message = elements.length ? `Dans ${libelle} : ${elements.join(', ')}.` : `${libelle} est vide.`;
    consigner('', `lire ${libelle}`, message);
    return { type: 'reponse', message, parole: message };
  }

  // ---------- Échéancier ----------

  async function traiterEcheancier(commande) {
    const nomFichier = REGLAGES_GOOGLE.fichiers_vocaux.echeancier;
    if (commande.type === 'ajouter') {
      await fichiersVocauxDrive.modifier('echeancier', nomFichier,
        contenu => fichiersVocauxEcheancier.ajouter(contenu, commande));
      const delaiTexte = commande.delaiJours === null ? 'sans rappel' : `rappel ${commande.delaiJours} jours avant`;
      const message = `C'est noté. Échéance ajoutée : ${commande.element} (${commande.dateLisible}), ${delaiTexte}.`;
      consigner(commande.element, 'ajouter une échéance', message);
      return { type: 'reponse', message, parole: "C'est noté." };
    }
    if (commande.type === 'terminer') {
      const resultat = await fichiersVocauxDrive.modifier('echeancier', nomFichier,
        contenu => fichiersVocauxEcheancier.terminer(contenu, commande.element));
      const message = resultat.trouve
        ? `C'est noté. Échéance terminée : ${resultat.element}.`
        : `Je ne trouve pas « ${commande.element} » dans tes échéances à venir.`;
      consigner(commande.element, 'terminer une échéance', message);
      return { type: 'reponse', message, parole: "C'est noté." };
    }
    const id = await fichiersVocauxDrive.trouverOuCreerFichier('echeancier', nomFichier);
    const contenu = await fichiersVocauxDrive.lireTexte(id);
    const lignes = fichiersVocauxEcheancier.lireAVenir(contenu);
    const message = lignes.length
      ? `Tes échéances à venir, les plus proches d'abord : ${lignes.map(l => `${l.element} (${l.dateLisible})`).join(', ')}.`
      : 'Tu n’as aucune échéance à venir.';
    consigner('', 'lire les échéances', message);
    return { type: 'reponse', message, parole: message };
  }

  // ---------- À faire ----------

  async function traiterAFaire(commande) {
    const nomFichier = REGLAGES_GOOGLE.fichiers_vocaux.a_faire;
    if (commande.type === 'ajouter') {
      await fichiersVocauxDrive.modifier('a_faire', nomFichier,
        contenu => fichiersVocauxAFaire.ajouter(contenu, commande));
      const message = `C'est noté dans ta to-do : ${commande.tache}.`;
      consigner(commande.tache, 'ajouter une tâche (à faire)', message);
      return { type: 'reponse', message, parole: "C'est noté." };
    }
    if (commande.type === 'coche') {
      const resultat = await fichiersVocauxDrive.modifier('a_faire', nomFichier,
        contenu => fichiersVocauxAFaire.coche(contenu, commande.element));
      const message = resultat.trouve
        ? `C'est noté. Cochée : ${resultat.element}.`
        : `Je ne trouve pas « ${commande.element} » dans ta to-do.`;
      consigner(commande.element, 'cocher une tâche (à faire)', message);
      return { type: 'reponse', message, parole: "C'est noté." };
    }
    if (commande.type === 'retirer') {
      const resultat = await fichiersVocauxDrive.modifier('a_faire', nomFichier,
        contenu => fichiersVocauxAFaire.retirer(contenu, commande.element));
      const message = resultat.trouve
        ? `C'est noté. Retirée de ta to-do : ${resultat.element}.`
        : `Je ne trouve pas « ${commande.element} » dans ta to-do.`;
      consigner(commande.element, 'retirer une tâche (à faire)', message);
      return { type: 'reponse', message, parole: "C'est noté." };
    }
    const id = await fichiersVocauxDrive.trouverOuCreerFichier('a_faire', nomFichier);
    const contenu = await fichiersVocauxDrive.lireTexte(id);
    const lignes = fichiersVocauxAFaire.lireActives(contenu);
    const message = lignes.length
      ? `Dans ta to-do, les plus urgentes d'abord : ${lignes.map(l => l.tache).join(', ')}.`
      : 'Ta to-do est vide.';
    consigner('', 'lire la to-do (à faire)', message);
    return { type: 'reponse', message, parole: message };
  }

  // ---------- Dictée libre (Bloc-notes, Brouillon vocal) ----------

  function sessionActive() { return Boolean(session); }

  function ouvrirSession(fichier) { session = { fichier, morceaux: [] }; }

  function accumuler(texte) {
    if (session && texte) session.morceaux.push(texte);
  }

  async function fermerSession() {
    if (!session) return null;
    if (!pret()) {
      const message = messagePasPret();
      return { type: 'reponse', message, parole: message };
    }
    const { fichier, morceaux } = session;
    const contenu = morceaux.join(' ').trim();
    if (!contenu) {
      session = null;
      return { type: 'reponse', message: "Je n'ai rien noté, rien à enregistrer.", parole: 'Rien noté.' };
    }
    const nomFichier = REGLAGES_GOOGLE.fichiers_vocaux[fichier];
    const libelle = fichier === 'bloc_notes' ? 'ton bloc-notes' : 'ton brouillon vocal';
    const titre = fichiersVocauxNotes.titreCourt(contenu);
    try {
      await fichiersVocauxDrive.modifier(fichier, nomFichier,
        avant => ({ contenu: fichiersVocauxNotes.ajouterEntree(avant, titre, contenu) }));
      session = null;
      const message = `C'est noté. Ajouté à ${libelle} : ${titre}.`;
      consigner(contenu, `note dans ${libelle}`, message);
      return { type: 'reponse', message, parole: "C'est noté." };
    } catch (erreur) {
      const message = erreur instanceof Error
        ? `${erreur.message} Dis « terminé » pour réessayer.`
        : `Je n'ai pas pu enregistrer dans ${libelle}. Dis « terminé » pour réessayer.`;
      return { type: 'reponse', message, parole: message };
    }
  }

  function detecterOuvertureNote(texte) {
    return fichiersVocauxNotes.detecterOuverture(texte);
  }

  // ---------- Détection générale (listes, échéancier, à faire) ----------

  function detecterCommande(texte) {
    const liste = fichiersVocaux.detecterCommande(texte);
    if (liste) return { systeme: 'liste', commande: liste };
    const afaire = fichiersVocauxAFaire.detecterCommande(texte);
    if (afaire) return { systeme: 'a_faire', commande: afaire };
    const echeance = fichiersVocauxEcheancier.detecterCommande(texte);
    if (echeance) return { systeme: 'echeancier', commande: echeance };
    return null;
  }

  async function traiter(detection, source) {
    if (!pret()) {
      const message = messagePasPret();
      return { type: 'reponse', message, parole: message };
    }
    try {
      if (detection.systeme === 'liste') return await traiterListe(detection.commande);
      if (detection.systeme === 'echeancier') return await traiterEcheancier(detection.commande);
      if (detection.systeme === 'a_faire') return await traiterAFaire(detection.commande);
    } catch (erreur) {
      const message = erreur instanceof Error ? erreur.message : "Je n'ai pas pu terminer cette action.";
      return { type: 'reponse', message, parole: message };
    }
    return { type: 'reponse', message: "Je n'ai pas compris cette commande.", parole: "Je n'ai pas compris." };
  }

  return {
    pret, detecterCommande, traiter,
    sessionActive, ouvrirSession, accumuler, fermerSession, detecterOuvertureNote
  };
})();
