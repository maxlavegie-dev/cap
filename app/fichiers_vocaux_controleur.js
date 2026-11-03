'use strict';

// Relie fichiersVocaux (comprendre la phrase, sans IA), fichiersVocauxDrive (lire/écrire le
// fichier Markdown) et le journal des actions. N'efface jamais une ligne existante.
const fichiersVocauxControleur = (() => {
  function pret() {
    return typeof navigator === 'undefined' || navigator.onLine !== false
      ? googleConnexion.connecte() : false;
  }

  function consigner(texte, compris, fait) {
    if (typeof journalActions === 'undefined') return;
    try { journalActions.consigner({ source: 'Cap', entree: texte, compris, fait }); } catch (erreur) {}
  }

  async function traiterAjout(commande) {
    const nomFichier = REGLAGES_GOOGLE.fichiers_vocaux.liste_courses;
    const resultat = await fichiersVocauxDrive.modifier('liste_courses', nomFichier,
      contenu => fichiersVocaux.ajouterElements(contenu, commande.produits));
    const liste = resultat.ajoutes.join(', ');
    const message = resultat.ajoutes.length
      ? `C'est noté. Ajouté à la liste de courses : ${liste}.`
      : 'Déjà dans la liste de courses, rien ajouté.';
    consigner(commande.produits.join(', '), 'ajouter à la liste de courses', message);
    return { type: 'reponse', message, parole: "C'est noté." };
  }

  async function traiterRetrait(commande) {
    const nomFichier = REGLAGES_GOOGLE.fichiers_vocaux.liste_courses;
    const resultat = await fichiersVocauxDrive.modifier('liste_courses', nomFichier,
      contenu => fichiersVocaux.retirerElement(contenu, commande.produit));
    const message = resultat.retire
      ? `C'est noté. Retiré de la liste de courses : ${resultat.nom}.`
      : `Je ne trouve pas « ${commande.produit} » dans la liste de courses.`;
    consigner(commande.produit, 'retirer de la liste de courses', message);
    return { type: 'reponse', message, parole: "C'est noté." };
  }

  async function traiterLecture() {
    const nomFichier = REGLAGES_GOOGLE.fichiers_vocaux.liste_courses;
    const id = await fichiersVocauxDrive.trouverOuCreerFichier('liste_courses', nomFichier);
    const contenu = await fichiersVocauxDrive.lireTexte(id);
    const elements = fichiersVocaux.elementsActifs(contenu);
    const message = elements.length
      ? `Dans ta liste de courses : ${elements.join(', ')}.`
      : 'Ta liste de courses est vide.';
    consigner('', 'lire la liste de courses', message);
    return { type: 'reponse', message, parole: message };
  }

  async function traiter(commande, source) {
    if (!pret()) {
      const message = navigator.onLine === false
        ? "Pas de connexion : je ne peux pas encore toucher à ta liste de courses hors connexion."
        : "Connecte-toi à Google pour que je touche à ta liste de courses.";
      return { type: 'reponse', message, parole: message };
    }
    try {
      if (commande.type === 'ajouter') return await traiterAjout(commande);
      if (commande.type === 'retirer') return await traiterRetrait(commande);
      if (commande.type === 'lire') return await traiterLecture();
    } catch (erreur) {
      const message = erreur instanceof Error ? erreur.message : "Je n'ai pas pu toucher à ta liste de courses.";
      return { type: 'reponse', message, parole: message };
    }
    return { type: 'reponse', message: "Je n'ai pas compris la commande pour la liste de courses.",
      parole: "Je n'ai pas compris." };
  }

  return { traiter, pret };
})();
