'use strict';

const modeTrier = (() => {
  let dialogue = null;
  let rappels = {};
  let passees = new Set();
  let enTete = '';
  let delaiAnnuler;

  function noeud(balise, classe, texte) {
    const element = document.createElement(balise);
    if (classe) element.className = classe;
    if (texte !== undefined) element.textContent = texte;
    return element;
  }

  function bouton(texte, classe, action) {
    const element = noeud('button', classe, texte);
    element.type = 'button';
    element.addEventListener('click', action);
    return element;
  }

  function normaliser(valeur) {
    return String(valeur || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr')
      .replace(/[^a-z0-9]+/g, ' ').trim();
  }

  function categoriesCibles() {
    return listesChoix.categories().filter(nom => normaliser(nom) !== normaliser(listesChoix.A_TRIER));
  }

  function reconnaitre(texte) {
    const entendu = ` ${normaliser(texte)} `;
    const trouvees = categoriesCibles().filter(nom => normaliser(nom) && entendu.includes(` ${normaliser(nom)} `));
    trouvees.sort((a, b) => normaliser(b).length - normaliser(a).length);
    return trouvees[0] || '';
  }

  function aTrier() {
    const actives = TACHES.filter(tache => !tache.parente && !tache.fait && !tache.abandonnee_le
      && normaliser(tache.categorie) === normaliser(listesChoix.A_TRIER));
    const restantes = actives.filter(tache => !passees.has(tache.id));
    const premiere = restantes.find(tache => tache.id === enTete);
    return { total: actives.length, restantes: premiere ? [premiere, ...restantes.filter(tache => tache !== premiere)] : restantes };
  }

  function message(texte) {
    const zone = dialogue.querySelector('.message-tri');
    if (zone) zone.textContent = texte;
  }

  function proposerAnnulation(texte, annuler) {
    clearTimeout(delaiAnnuler);
    const zone = dialogue.querySelector('.annulation-tri');
    if (!zone) return;
    zone.replaceChildren(noeud('span', '', texte), bouton('Annuler', 'annuler-tri', () => {
      clearTimeout(delaiAnnuler);
      zone.replaceChildren();
      annuler();
    }));
    delaiAnnuler = setTimeout(() => zone.replaceChildren(), 8000);
  }

  function ranger(tache, categorie, contexte) {
    let ancienne;
    let sous = '';
    try {
      sous = sousCategories.trouver(tache.intitule, categorie, listesChoix.categories(categorie), TACHES).sous_categorie;
      ancienne = journalActions.pendant(contexte, () => classer(tache.id, categorie, sous));
    } catch (erreur) {
      message(erreur instanceof Error ? erreur.message : 'Je n’ai pas pu ranger cette tâche.');
      return;
    }
    enTete = '';
    rappels.surChangement?.();
    construire();
    const texte = `« ${tache.intitule} » rangée dans ${[categorie, sous].filter(Boolean).join(' › ')}.`;
    message(texte);
    proposerAnnulation(texte, () => {
      try {
        journalActions.pendant({ source: 'bouton Annuler (Trier)', entree: 'Annuler', compris: 'remettre dans À trier' },
          () => classer(tache.id, ancienne.categorie, ancienne.sous_categorie));
      } catch (erreur) {
        message(erreur instanceof Error ? erreur.message : 'Je n’ai pas pu annuler.');
        return;
      }
      passees.delete(tache.id);
      enTete = tache.id;
      rappels.surChangement?.();
      construire();
      message(`« ${tache.intitule} » est revenue dans À trier.`);
    });
  }

  function ecouter(tache, micro) {
    if (dictee.enCours()) {
      dictee.arreter();
      return;
    }
    if (!dictee.disponible()) {
      message('La dictée n’est pas disponible ici. Touche une catégorie.');
      return;
    }
    let recu = false;
    micro.setAttribute('aria-pressed', 'true');
    message('Je t’écoute… dis le nom de la catégorie.');
    let provisoire = '';
    const traiter = texte => {
      if (recu) return;
      recu = true;
      const categorie = reconnaitre(texte);
      if (!categorie) {
        message(`Je n’ai pas reconnu de catégorie dans « ${texte} ». Touche-la plutôt.`);
        journalActions.consigner({ source: 'micro (Trier)', entree: texte, compris: 'aucune catégorie reconnue', fait: 'rien' });
        return;
      }
      ranger(tache, categorie, { source: 'micro (Trier)', entree: texte, compris: `catégorie ${categorie}` });
    };
    dictee.demarrer({
      surProvisoire(texte) { provisoire = texte || provisoire; if (texte) message(texte); },
      surFinal(texte) { traiter(texte); },
      surErreur(code) {
        if (recu || code === 'aborted') return;
        recu = true;
        message(code === 'not-allowed' || code === 'service-not-allowed'
          ? 'Le micro est bloqué. Autorise-le pour cette page.' : 'Je n’ai rien entendu. Touche une catégorie ou réessaie.');
      },
      surFin() {
        micro.setAttribute('aria-pressed', 'false');
        if (!recu && provisoire) traiter(provisoire);
        else if (!recu) message('Je n’ai rien entendu. Touche une catégorie ou réessaie.');
      }
    });
  }

  function construire() {
    if (!dialogue) return;
    const { total, restantes } = aTrier();
    const contenu = dialogue.querySelector('.contenu-tri');
    const tache = restantes[0];
    const elements = [noeud('h2', '', 'Trier')];
    elements[0].id = 'titre-mode-trier';
    if (!tache) {
      elements.push(noeud('p', 'tache-a-trier', total ? 'Tu as passé les tâches restantes.' : 'Tout est trié. Bravo !'));
      if (total) elements.push(bouton('Revoir les tâches passées', 'revoir-passees', () => { passees = new Set(); construire(); }));
    } else {
      elements.push(noeud('p', 'compte-tri', `Encore ${restantes.length} à trier`));
      const carte = noeud('p', 'tache-a-trier', tache.intitule);
      carte.dataset.tache = tache.id;
      elements.push(carte);
      const grille = noeud('div', 'grille-tri');
      for (const categorie of categoriesCibles()) {
        const choix = bouton(categorie, 'choix-tri', () => ranger(tache, categorie,
          { source: 'tuile touchée (Trier)', entree: categorie, compris: `catégorie ${categorie}` }));
        choix.style.setProperty('--couleur-categorie', listesChoix.couleur(categorie));
        grille.append(choix);
      }
      const actions = noeud('div', 'actions-tri');
      const micro = bouton('Dire la catégorie', 'micro-tri', () => ecouter(tache, micro));
      micro.setAttribute('aria-pressed', 'false');
      actions.append(micro, bouton('Passer', 'passer-tri', () => {
        passees.add(tache.id);
        enTete = '';
        construire();
        message('Tâche passée : elle reste dans À trier.');
      }));
      elements.push(grille, actions);
    }
    const statut = noeud('p', 'message-tri');
    statut.setAttribute('role', 'status');
    const annulation = noeud('div', 'annulation-tri');
    const ancienMessage = contenu.querySelector('.message-tri')?.textContent || '';
    const ancienneAnnulation = contenu.querySelector('.annulation-tri');
    if (ancienneAnnulation) annulation.replaceChildren(...ancienneAnnulation.childNodes);
    statut.textContent = ancienMessage;
    elements.push(statut, annulation);
    contenu.replaceChildren(...elements);
  }

  function ouvrir(element, options = {}) {
    dialogue = element;
    rappels = options;
    passees = new Set();
    enTete = '';
    clearTimeout(delaiAnnuler);
    dialogue.querySelector('.contenu-tri').replaceChildren();
    construire();
    if (!dialogue.open) dialogue.showModal();
    dialogue.querySelector('.choix-tri, .revoir-passees, h2')?.focus({ preventScroll: true });
  }

  return { ouvrir, reconnaitre, construire };
})();
