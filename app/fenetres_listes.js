'use strict';

const fenetresListes = (() => {
  const fenetre = document.getElementById('fenetre-liste');
  const titre = document.getElementById('titre-fenetre-liste');
  const contenu = document.getElementById('contenu-fenetre-liste');
  const zoneErreur = fenetre.querySelector('.erreur');
  const bandeau = document.getElementById('annulation-liste');
  let delaiAnnulation;
  let rappels = {};

  function noeud(balise, classe, texte) {
    const element = document.createElement(balise);
    if (classe) element.className = classe;
    if (texte !== undefined) element.textContent = texte;
    return element;
  }

  function bouton(texte, classe, action) {
    const element = noeud('button', classe, texte);
    element.type = 'button';
    element.addEventListener('click', () => {
      try {
        action();
      } catch (erreur) {
        erreurVisible(erreur instanceof Error ? erreur.message : 'Action impossible.');
      }
    });
    return element;
  }

  function erreurVisible(texte) {
    zoneErreur.textContent = texte;
    zoneErreur.hidden = !texte;
  }

  function afficherVue(texteTitre, enfants, focus) {
    erreurVisible('');
    titre.textContent = texteTitre;
    contenu.replaceChildren(...enfants);
    if (!fenetre.open) fenetre.showModal();
    fenetre.scrollTop = 0;
    (focus || contenu.querySelector('button, input, textarea'))?.focus({ preventScroll: true });
  }

  function fermer() {
    if (fenetre.open) fenetre.close();
  }

  function proposerAnnulation(texte, annuler) {
    clearTimeout(delaiAnnulation);
    const retour = bouton('Annuler', 'bouton-annuler-liste', () => {
      clearTimeout(delaiAnnulation);
      bandeau.hidden = true;
      bandeau.replaceChildren();
      annuler();
    });
    bandeau.replaceChildren(noeud('span', '', texte), retour);
    bandeau.hidden = false;
    delaiAnnulation = setTimeout(() => {
      bandeau.hidden = true;
      bandeau.replaceChildren();
    }, 8000);
  }

  function grille(enfants) {
    const zone = noeud('div', 'grille-choix');
    zone.append(...enfants);
    return zone;
  }

  function boutonCouleur(texte, couleur, action, choisi) {
    const element = bouton(texte, 'bouton-choix', action);
    element.style.setProperty('--couleur-choix', couleur);
    if (choisi) element.setAttribute('aria-current', 'true');
    return element;
  }

  function vueCategories() {
    const actuelle = rappels.categorie || '';
    const boutons = listesChoix.categories().map(nom =>
      boutonCouleur(nom, listesChoix.couleur(nom), () => vueSousCategories(nom), nom === actuelle));
    afficherVue('Catégorie', [
      grille(boutons),
      grille([
        bouton('Sans catégorie', 'bouton-choix bouton-neutre', () => choisir('', '')),
        bouton('Ajouter', 'bouton-choix bouton-outil', () => vueAjout('categorie', '')),
        bouton('Modifier', 'bouton-choix bouton-outil', () => vueModifier('categorie', ''))
      ]),
      actionsBas([bouton('Fermer', '', fermer)])
    ], boutons.find(element => element.hasAttribute('aria-current')) || boutons[0]);
  }

  function vueSousCategories(categorie) {
    const couleur = listesChoix.couleur(categorie);
    const actuelle = rappels.categorie === categorie ? rappels.sousCategorie || '' : '';
    const boutons = listesChoix.categories(categorie).map(nom =>
      boutonCouleur(nom, couleur, () => choisir(categorie, nom), nom === actuelle));
    const sans = boutonCouleur(`${categorie}, sans sous-catégorie`, couleur, () => choisir(categorie, ''), false);
    sans.classList.add('bouton-sans-sous');
    afficherVue(`${categorie} : sous-catégorie`, [
      grille([sans, ...boutons]),
      grille([
        bouton('Ajouter', 'bouton-choix bouton-outil', () => vueAjout('categorie', categorie)),
        bouton('Modifier', 'bouton-choix bouton-outil', () => vueModifier('categorie', categorie))
      ]),
      actionsBas([bouton('Retour', '', vueCategories)])
    ], boutons.find(element => element.hasAttribute('aria-current')) || sans);
  }

  function choisir(categorie, sousCategorie) {
    const surChoix = rappels.surChoix;
    fermer();
    surChoix?.(categorie, sousCategorie);
  }

  function actionsBas(enfants) {
    const zone = noeud('div', 'actions-dialogue');
    zone.append(...enfants);
    return zone;
  }

  function retourDepuis(type, parente) {
    if (type === 'modele') return rappels.vueDepart === 'modifier' ? () => vueModifier('modele', '') : fermer;
    return parente ? () => vueSousCategories(parente) : vueCategories;
  }

  function vueAjout(type, parente) {
    const formulaire = noeud('form', 'formulaire-liste');
    const idNom = 'nom-nouvel-element';
    const etiquette = noeud('label', '', type === 'modele' ? 'Nom des étapes par défaut' : parente ? `Nouvelle sous-catégorie de ${parente}` : 'Nouvelle catégorie');
    etiquette.htmlFor = idNom;
    const nom = noeud('input');
    nom.id = idNom;
    nom.type = 'text';
    nom.maxLength = 60;
    nom.autocomplete = 'off';
    nom.required = true;
    formulaire.append(etiquette, nom);
    let etapes = null;
    if (type === 'modele') {
      const etiquetteEtapes = noeud('label', '', 'Étapes, une par ligne (20 au maximum)');
      etiquetteEtapes.htmlFor = 'etapes-nouveau-modele';
      etapes = noeud('textarea');
      etapes.id = 'etapes-nouveau-modele';
      etapes.rows = 5;
      formulaire.append(etiquetteEtapes, etapes);
    }
    const retour = retourDepuis(type, parente);
    const enregistrer = noeud('button', '', 'Enregistrer');
    enregistrer.type = 'submit';
    formulaire.append(actionsBas([bouton('Retour', '', retour), enregistrer]));
    formulaire.addEventListener('submit', event => {
      event.preventDefault();
      try {
        if (type === 'modele') {
          const ajoute = listesChoix.ajouterModele(nom.value, etapes.value.split('\n'));
          const surFin = rappels.surFin;
          fermer();
          surFin?.(ajoute);
        } else {
          listesChoix.ajouterCategorie(nom.value, parente);
          retour();
        }
      } catch (erreur) {
        erreurVisible(erreur instanceof Error ? erreur.message : 'Ajout impossible.');
      }
    });
    afficherVue(type === 'modele' ? 'Ajouter des étapes par défaut' : parente ? 'Ajouter une sous-catégorie' : 'Ajouter une catégorie', [formulaire], nom);
  }

  function vueModifier(type, parente) {
    const actifs = type === 'modele' ? listesChoix.modeles() : listesChoix.categories(parente);
    const retirees = type === 'modele' ? listesChoix.modelesRetires() : listesChoix.categoriesRetirees(parente);
    const liste = noeud('ul', 'liste-cases');
    const retirer = bouton('Retirer', 'bouton-retirer', () => {
      const noms = Array.from(liste.querySelectorAll('input:checked'), caseACocher => caseACocher.value);
      const faits = listesChoix.retirer(type, noms, parente);
      vueModifier(type, parente);
      if (faits.length) {
        proposerAnnulation(`${faits.length} retiré${faits.length > 1 ? 's' : ''} (gardé${faits.length > 1 ? 's' : ''} dans le tableau).`, () => {
          listesChoix.remettre(type, faits, parente);
          if (fenetre.open) vueModifier(type, parente);
        });
      }
    });
    retirer.hidden = true;
    actifs.forEach((nom, indice) => {
      const ligne = noeud('li');
      const caseACocher = noeud('input');
      caseACocher.type = 'checkbox';
      caseACocher.value = nom;
      caseACocher.id = `case-liste-${indice}`;
      const etiquette = noeud('label', '', nom);
      etiquette.htmlFor = caseACocher.id;
      if (type !== 'modele') ligne.style.setProperty('--couleur-choix', listesChoix.couleur(parente || nom));
      caseACocher.addEventListener('change', () => {
        const nombre = liste.querySelectorAll('input:checked').length;
        retirer.hidden = nombre === 0;
        retirer.textContent = `Retirer (${nombre})`;
      });
      ligne.append(caseACocher, etiquette);
      liste.append(ligne);
    });
    const enfants = [];
    enfants.push(actifs.length ? liste : noeud('p', 'etat-vide', 'La liste est vide.'));
    enfants.push(noeud('p', 'aide-liste', 'Retirer n’efface rien : l’élément est gardé dans le tableau avec la date, et tu peux le remettre.'));
    if (retirees.length) {
      const section = noeud('section', 'section-retirees');
      section.append(noeud('h3', '', 'Retirées'));
      const listeRetirees = noeud('ul', 'liste-retirees');
      for (const element of retirees) {
        const ligne = noeud('li');
        ligne.append(noeud('span', '', `${element.nom} (retirée le ${element.retiree_le})`),
          bouton('Remettre', 'bouton-remettre', () => {
            listesChoix.remettre(type, [element.nom], parente);
            vueModifier(type, parente);
          }));
        listeRetirees.append(ligne);
      }
      section.append(listeRetirees);
      enfants.push(section);
    }
    const retour = type === 'modele' ? fermer : parente ? () => vueSousCategories(parente) : vueCategories;
    const ajouter = type === 'modele' ? [bouton('Ajouter', '', () => vueAjout('modele', ''))] : [];
    enfants.push(actionsBas([bouton(type === 'modele' ? 'Fermer' : 'Retour', '', retour), ...ajouter, retirer]));
    const titreVue = type === 'modele' ? 'Modifier la liste des étapes par défaut'
      : parente ? `Modifier les sous-catégories de ${parente}` : 'Modifier les catégories';
    afficherVue(titreVue, enfants);
  }

  function choisirCategorie({ categorie = '', sousCategorie = '', surChoix } = {}) {
    rappels = { categorie, sousCategorie, surChoix };
    vueCategories();
  }

  function gererModeles({ action = 'modifier', surFin } = {}) {
    rappels = { surFin, vueDepart: action };
    if (action === 'ajouter') vueAjout('modele', '');
    else vueModifier('modele', '');
  }

  fenetre.addEventListener('close', () => {
    if (fenetre.open) return;
    clearTimeout(delaiAnnulation);
    bandeau.hidden = true;
    bandeau.replaceChildren();
  });

  return { choisirCategorie, gererModeles, fermer };
})();
