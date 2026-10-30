'use strict';

// La frontière entre le cerveau et Cap : le cerveau (quel que soit le modèle d'IA) ne touche jamais
// aux tâches lui-même. Il demande une action de ce catalogue, et c'est ici que tout est vérifié.
const actionsCap = (() => {
  const CATALOGUE = [{
    nom: 'ajouter_tache',
    description: 'Ajoute une seule tâche, mot pour mot, dans une catégorie et une sous-catégorie qui existent déjà.',
    parametres: {
      intitule: 'le texte exact de la tâche, sans reformulation',
      categorie: 'une catégorie existante, ou vide pour À trier',
      sous_categorie: 'une sous-catégorie existante de cette catégorie, « À classer », ou vide pour laisser Cap choisir',
      date_dite: 'la phrase où chercher l’échéance (par défaut, l’intitulé)'
    }
  }];

  const cle = valeur => String(valeur || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('fr').replace(/\s+/g, ' ').trim();

  function categorieExistante(nom, parente = '') {
    const cherche = cle(nom);
    return listesChoix.categories(parente).find(categorie => cle(categorie) === cherche) || '';
  }

  function ajouterTache({ intitule, categorie = '', sous_categorie = '', date_dite = '', source = '' } = {}) {
    const texte = typeof intitule === 'string' ? intitule.trim() : '';
    if (!texte) throw new Error('Écris un intitulé pour cette tâche.');
    const nomCategorie = categorie ? categorieExistante(categorie) : listesChoix.A_TRIER;
    if (!nomCategorie) throw new Error(`La catégorie « ${categorie} » n’existe pas. Rien n’a été ajouté.`);
    let sous = '';
    if (nomCategorie !== listesChoix.A_TRIER) {
      const disponibles = listesChoix.categories(nomCategorie);
      if (sous_categorie && sousCategories.estAClasser(sous_categorie)) {
        sous = disponibles.length ? sousCategories.A_CLASSER : '';
      } else if (sous_categorie) {
        sous = categorieExistante(sous_categorie, nomCategorie);
        if (!sous) throw new Error(`La sous-catégorie « ${sous_categorie} » n’existe pas dans ${nomCategorie}. Rien n’a été ajouté.`);
      } else {
        sous = sousCategories.trouver(texte, nomCategorie, disponibles, TACHES).sous_categorie;
      }
    }
    const date = comprendreDemande.trouverDate(typeof date_dite === 'string' && date_dite.trim() ? date_dite : texte);
    const tache = creerTache({
      intitule: texte,
      categorie: nomCategorie,
      sous_categorie: sous,
      echeance: date.date,
      origine: source === 'micro' ? 'dictée' : 'ajout à la main',
      fictif: false
    });
    return { tache, choix: date.choix };
  }

  const EXECUTANTS = { ajouter_tache: ajouterTache };

  function executer(nom, parametres) {
    if (!Object.prototype.hasOwnProperty.call(EXECUTANTS, nom)) {
      throw new Error('Cap ne sait pas encore faire cette action. Rien n’a été fait.');
    }
    return EXECUTANTS[nom](parametres && typeof parametres === 'object' ? parametres : {});
  }

  return { CATALOGUE, executer, categorieExistante };
})();
