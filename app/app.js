(() => {
  'use strict';

  const parId = id => document.getElementById(id);
  const dateElement = parId('date');
  const listeElement = parId('liste-taches');
  const statutElement = parId('statut');
  const archiveElement = parId('basculer-archive');
  const listeArchiveElement = parId('liste-archive');
  const menu = parId('menu-tache');
  const confirmation = parId('confirmation');
  const ajout = parId('ajout-tache');
  const formulaire = parId('formulaire-ajout');
  const clavier = parId('clavier');
  const saisieDemande = parId('saisie-demande');
  const reponseSilencieuse = parId('reponse-silencieuse');
  const zoneRecherche = parId('zone-recherche');
  const sourceRecherche = parId('source-recherche');
  const saisieRecherche = parId('saisie-recherche');
  const resultatsRecherche = parId('resultats-recherche');
  let cibleRecherche = null;
  let delaiSurbrillance;
  let phraseSelectionnee = null;
  const formatDate = new Intl.DateTimeFormat('fr-FR', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  });
  const formatHeure = new Intl.DateTimeFormat('fr-FR', {
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23'
  });
  const formatDateCourte = new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric', month: 'long', year: 'numeric'
  });
  let archiveOuverte = false;
  let tacheSelectionnee = null;
  let parenteAjout = null;
  let retourDialogue = null;
  let delaiStatut;
  let dernierJour;

  function element(balise, classe, texte) {
    const noeud = document.createElement(balise);
    if (classe) noeud.className = classe;
    if (texte !== undefined) noeud.textContent = texte;
    return noeud;
  }

  function surlignerResultat(cible) {
    if (!cible) return;
    clearTimeout(delaiSurbrillance);
    cibleRecherche?.classList.remove('surbrillance-recherche');
    cibleRecherche = cible;
    cible.tabIndex = -1;
    cible.focus({ preventScroll: true });
    cible.scrollIntoView({ block: 'center' });
    cible.classList.add('surbrillance-recherche');
    delaiSurbrillance = setTimeout(() => {
      cible.classList.remove('surbrillance-recherche');
      cibleRecherche = null;
    }, 2000);
  }

  function identiteRendezVous(rendezVous) {
    return JSON.stringify([rendezVous.date, rendezVous.heure, rendezVous.titre]);
  }

  function texteRendezVous(rendezVous) {
    const valeur = new Date(`${rendezVous.date}T12:00:00`);
    const date = Number.isNaN(valeur.getTime()) ? rendezVous.date : formatRendezVous.format(valeur);
    return [date, rendezVous.heure, rendezVous.titre].filter(Boolean).join(' – ');
  }

  function ouvrirResultatTache(tache) {
    if (tache.abandonnee_le) {
      archiveOuverte = true;
      afficher();
    }
    changerVue(true);
    const liste = tache.abandonnee_le ? listeArchiveElement : listeElement;
    const ligne = Array.from(liste.querySelectorAll('[data-tache]'))
      .find(noeud => noeud.dataset.tache === String(tache.id));
    surlignerResultat(ligne);
  }

  function ouvrirResultatRendezVous(rendezVous, origine) {
    ficheRendezVous.ouvrir(rendezVous, origine, () => {
      erreurAgenda = '';
      remplirRendezVous(googleAgenda.lireCache() || []);
      afficherRecherche();
    });
  }

  function afficherRecherche() {
    parId('libelle-source').textContent = sourceRecherche.selectedOptions[0]?.textContent || '';
    const texte = saisieRecherche.value.trim();
    resultatsRecherche.replaceChildren();
    resultatsRecherche.hidden = true;
    if (!texte) return;
    const agenda = sourceRecherche.value === 'rendez-vous';
    const resultats = agenda
      ? recherche.chercherRendezVous(googleAgenda.lireCache() || [], texte)
      : recherche.chercherTaches(TACHES, texte);
    for (const resultat of resultats.slice(0, 30)) {
      const ligne = element('li');
      const bouton = element('button', 'resultat-recherche', agenda ? texteRendezVous(resultat) : resultat.intitule);
      bouton.type = 'button';
      if (agenda) {
        bouton.dataset.rdvFocus = `recherche-${resultat.id || identiteRendezVous(resultat)}`;
        bouton.setAttribute('aria-haspopup', 'dialog');
        bouton.setAttribute('aria-controls', 'fiche-rendez-vous');
      }
      if (!agenda && resultat.fait) bouton.append(element('span', 'etat-resultat', 'fait'));
      bouton.addEventListener('click', () => {
        if (agenda) ouvrirResultatRendezVous(resultat, bouton);
        else ouvrirResultatTache(resultat);
      });
      ligne.append(bouton);
      resultatsRecherche.append(ligne);
    }
    if (resultats.length > 30) {
      resultatsRecherche.append(element('li', 'autres-resultats', `et ${resultats.length - 30} autres…`));
    }
    if (resultats.length === 0) {
      const message = element('li', 'message-recherche', agenda ? 'Rien trouvé dans Rendez-vous' : 'Rien trouvé dans Tâches');
      message.setAttribute('role', 'status');
      resultatsRecherche.append(message);
    }
    resultatsRecherche.hidden = false;
  }

  function afficherJournal() {
    const libelles = {
      ajout: 'Ajouté', fait: 'Fait', 'remise à faire': 'Remis à faire',
      abandon: 'Abandonné', remise: 'Remis'
    };
    const actions = journalActions.lire().slice(0, 5);
    const maintenant = new Date();
    const hier = new Date(maintenant);
    hier.setDate(hier.getDate() - 1);
    parId('liste-actions').replaceChildren(...actions.map(action => {
      const ligne = element('li');
      const date = new Date(action.heure);
      if (!Number.isNaN(date.getTime())) {
        const prefixe = date.toDateString() === maintenant.toDateString() ? ''
          : date.toDateString() === hier.toDateString() ? 'hier '
            : `${String(date.getDate()).padStart(2, '0')}/${String(date.getMonth() + 1).padStart(2, '0')} `;
        const heure = element('time', 'heure-action', `${prefixe}${formatHeure.format(date)}`);
        heure.dateTime = date.toISOString();
        ligne.append(heure, document.createTextNode(' · '));
      }
      ligne.append(element('span', '', `${libelles[action.type]} : ${action.texte}`));
      return ligne;
    }));
    parId('dernieres-actions').hidden = actions.length === 0;
  }

  saisieRecherche.addEventListener('input', afficherRecherche);
  saisieRecherche.addEventListener('search', afficherRecherche);
  sourceRecherche.addEventListener('change', afficherRecherche);
  saisieRecherche.addEventListener('keydown', event => {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    afficherRecherche();
    saisieRecherche.blur();
  });

  function annoncer(message, temporaire = false) {
    clearTimeout(delaiStatut);
    statutElement.textContent = message;
    if (temporaire) {
      delaiStatut = setTimeout(() => { statutElement.textContent = ''; }, 2600);
    }
  }

  function signalerErreur(erreur, dialogue) {
    const message = erreur instanceof Error ? erreur.message : 'L’action n’a pas pu être enregistrée.';
    annoncer(message);
    if (dialogue) {
      const zone = dialogue.querySelector('.erreur');
      if (zone) {
        zone.textContent = message;
        zone.hidden = false;
      }
    }
  }

  function repereFocus(noeud) {
    return { noeud, cle: noeud?.dataset.focus };
  }

  function restaurerFocus(repere) {
    let cible = repere?.noeud;
    if (!cible?.isConnected && repere?.cle) {
      cible = Array.from(document.querySelectorAll('#liste-taches [data-focus], #liste-archive [data-focus]'))
        .find(noeud => noeud.dataset.focus === repere.cle);
    }
    if (!cible?.isConnected || cible.closest('[hidden], [inert]')) cible = parId('basculer-vue');
    cible.focus({ preventScroll: true });
  }

  function ouvrir(dialogue, cible, origine) {
    if (origine) retourDialogue = repereFocus(origine);
    const erreur = dialogue.querySelector('.erreur');
    if (erreur) {
      erreur.textContent = '';
      erreur.hidden = true;
    }
    dialogue.showModal();
    dialogue.scrollTop = 0;
    cible.focus({ preventScroll: true });
  }

  for (const dialogue of [menu, confirmation, ajout, clavier]) {
    dialogue.querySelectorAll('[data-fermer]').forEach(bouton => {
      bouton.addEventListener('click', () => dialogue.close());
    });
    dialogue.addEventListener('close', () => {
      if (!document.querySelector('dialog[open]')) restaurerFocus(retourDialogue);
    });
  }

  function dateLisible(valeur) {
    if (!valeur) return '';
    const texte = String(valeur);
    const date = /^\d{4}-\d{2}-\d{2}$/.test(texte)
      ? new Date(`${texte}T12:00:00`) : new Date(texte);
    return Number.isNaN(date.getTime()) ? texte : formatDateCourte.format(date);
  }

  function dateRelative(valeur) {
    const jours = joursRestants(valeur);
    if (!Number.isFinite(jours)) return dateLisible(valeur);
    if (jours === 0) return 'aujourd’hui';
    if (jours === 1) return 'demain';
    return jours < 0 ? `en retard de ${-jours} j` : `dans ${jours} j`;
  }

  function details(tache, texte, contexte) {
    texte.append(element('span', 'intitule', tache.intitule));
    if (contexte && tache.parente) {
      const parent = TACHES.find(item => item.id === tache.parente);
      if (parent) texte.append(element('span', 'contexte-parent', `Tâche parente : ${parent.intitule}`));
    }
    if (!tache.parente) {
      const progression = avancementTache(tache.id);
      if (progression.total > 0) {
        texte.append(element('span', 'details-tache', `${progression.faites}/${progression.total} étapes`));
      }
    }
    if (tache.priorite === 'haute') {
      texte.append(element('span', 'details-tache priorite-haute', 'Priorité haute'));
    }
    if (tache.note) texte.append(element('span', 'details-tache', tache.note));
    if (tache.echeance) {
      texte.append(element('span', 'details-tache', `Échéance : ${dateRelative(tache.echeance)}`));
    }
    if (tache.avant_le) {
      texte.append(element('span', 'details-tache', `Avant le : ${dateRelative(tache.avant_le)}`));
    }
    if (tache.fait && tache.date_realisation) {
      texte.append(element('span', 'details-tache', `Réalisée le ${dateLisible(tache.date_realisation)}`));
    }
  }

  function creerLigne(tache, contexte = false, estArchive = false) {
    const ligne = element('li', tache.parente ? 'tache etape' : 'tache');
    ligne.dataset.tache = tache.id;
    const texte = element('span', estArchive ? 'texte-tache texte-archive' : 'texte-tache');
    details(tache, texte, contexte || estArchive);
    if (estArchive) {
      texte.append(element('span', 'classement', `${tache.categorie || 'Sans catégorie'} > ${tache.sous_categorie || 'Sans sous-catégorie'}`));
      texte.append(element('span', 'details-tache', `Abandonnée le ${dateLisible(tache.abandonnee_le)}`));
      const bouton = element('button', 'remettre', 'Remettre');
      bouton.type = 'button';
      bouton.dataset.focus = JSON.stringify(['remettre', tache.id]);
      bouton.setAttribute('aria-label', `Remettre : ${tache.intitule}`);
      bouton.addEventListener('click', () => {
        try {
          remettre(tache.id);
        } catch (erreur) {
          signalerErreur(erreur);
          return;
        }
        afficher();
        annoncer(`Tâche remise : ${tache.intitule}`);
      });
      ligne.append(texte, bouton);
      return ligne;
    }
    const etiquette = element('label');
    const caseACocher = element('input');
    caseACocher.type = 'checkbox';
    caseACocher.id = `tache-${tache.id}`;
    caseACocher.dataset.focus = JSON.stringify(['cocher', tache.id]);
    caseACocher.checked = Boolean(tache.fait);
    etiquette.htmlFor = caseACocher.id;
    caseACocher.addEventListener('change', () => {
      const ancienEtat = !caseACocher.checked;
      try {
        cocher(tache.id, caseACocher.checked);
      } catch (erreur) {
        caseACocher.checked = ancienEtat;
        signalerErreur(erreur);
        return;
      }
      afficher();
    });
    etiquette.append(caseACocher, texte);
    const options = element('button', 'options-tache', '…');
    options.type = 'button';
    options.dataset.focus = JSON.stringify(['options', tache.id]);
    options.setAttribute('aria-label', `Actions : ${tache.intitule}`);
    options.setAttribute('aria-haspopup', 'dialog');
    options.addEventListener('click', () => {
      tacheSelectionnee = tache.id;
      parId('intitule-menu').textContent = tache.intitule;
      parId('ajouter-etape').hidden = Boolean(tache.parente);
      ouvrir(menu, tache.parente ? parId('abandonner-tache') : parId('ajouter-etape'), options);
    });
    ligne.append(etiquette, options);
    return ligne;
  }

  function afficher() {
    const actif = document.activeElement;
    const repere = listeElement.contains(actif) || listeArchiveElement.contains(actif) ? repereFocus(actif) : null;
    const fragment = document.createDocumentFragment();
    const parIdTache = new Map(TACHES.map(tache => [tache.id, tache]));
    const visibles = TACHES.filter(tache => !tache.abandonnee_le);
    const racines = visibles.filter(tache => {
      const parent = parIdTache.get(tache.parente);
      return !tache.parente || !parent || parent.abandonnee_le;
    });
    const groupes = new Map();
    for (const tache of racines) {
      if (!groupes.has(tache.categorie)) groupes.set(tache.categorie, new Map());
      const sousGroupes = groupes.get(tache.categorie);
      if (!sousGroupes.has(tache.sous_categorie)) sousGroupes.set(tache.sous_categorie, []);
      sousGroupes.get(tache.sous_categorie).push(tache);
    }
    const categoriesTriees = [...groupes].sort(([a], [b]) =>
      Number(b === 'À trier') - Number(a === 'À trier'));
    for (const [categorie, sousGroupes] of categoriesTriees) {
      const section = element('section', 'categorie');
      section.append(element('h2', '', categorie || 'Sans catégorie'));
      for (const [sousCategorie, taches] of sousGroupes) {
        const sousSection = element('section', 'sous-categorie');
        if (sousCategorie) {
          const titre = element('h3');
          titre.append(element('span', '', sousCategorie));
          const pourcentage = avancementSousCategorie(categorie, sousCategorie);
          titre.append(element('span', 'pourcentage', `${pourcentage} %`));
          sousSection.append(titre);
        }
        const liste = element('ul', 'liste-groupe');
        for (const tache of taches) {
          liste.append(creerLigne(tache, Boolean(tache.parente)));
          if (!tache.parente) {
            for (const etape of visibles.filter(item => item.parente === tache.id)) {
              liste.append(creerLigne(etape));
            }
          }
        }
        sousSection.append(liste);
        section.append(sousSection);
      }
      fragment.append(section);
    }
    if (visibles.length === 0) {
      fragment.append(element('p', 'etat-vide', 'Aucune tâche pour le moment. Le bouton + permet d’en ajouter une.'));
    }
    listeElement.replaceChildren(fragment);
    const abandonnees = TACHES.filter(tache => tache.abandonnee_le);
    archiveElement.textContent = `${archiveOuverte ? 'Masquer' : 'Voir'} les tâches abandonnées (${abandonnees.length})`;
    archiveElement.setAttribute('aria-expanded', String(archiveOuverte));
    parId('archive-taches').hidden = !archiveOuverte;
    listeArchiveElement.replaceChildren();
    if (archiveOuverte) {
      for (const tache of abandonnees) {
        listeArchiveElement.append(creerLigne(tache, true, true));
      }
      if (abandonnees.length === 0) {
        listeArchiveElement.append(element('li', 'etat-vide', 'Aucune tâche abandonnée.'));
      }
    }
    if (repere) restaurerFocus(repere);
    afficherJournal();
    afficherRecherche();
  }

  function suggestions() {
    const categories = [...new Set(TACHES.map(tache => tache.categorie).filter(Boolean))];
    const categorie = parId('categorie').value;
    const sousCategories = [...new Set(TACHES
      .filter(tache => !categorie || tache.categorie === categorie)
      .map(tache => tache.sous_categorie).filter(Boolean))];
    for (const [id, valeurs] of [['categories', categories], ['sous-categories', sousCategories]]) {
      parId(id).replaceChildren(...valeurs.map(valeur => {
        const option = element('option');
        option.value = valeur;
        return option;
      }));
    }
  }

  function preparerAjout(parente, origine) {
    parenteAjout = parente;
    formulaire.reset();
    const estEtape = parente !== null;
    parId('titre-ajout').textContent = estEtape ? 'Ajouter une étape' : 'Ajouter une tâche';
    const contexte = parId('contexte-etape');
    const parent = TACHES.find(tache => tache.id === parente);
    contexte.textContent = parent ? `Tâche parente : ${parent.intitule}` : '';
    contexte.hidden = !estEtape;
    parId('champs-tache').hidden = estEtape;
    parId('champs-tache').disabled = estEtape;
    const aucune = element('option', '', 'Aucune');
    aucune.value = '';
    parId('modele').replaceChildren(aucune, ...Object.keys(ETAPES_PAR_DEFAUT).map(nom => {
      const option = element('option', '', nom);
      option.value = nom;
      return option;
    }));
    suggestions();
    ouvrir(ajout, parId('intitule'), origine);
  }

  parId('ajouter').addEventListener('click', event => preparerAjout(null, event.currentTarget));
  parId('categorie').addEventListener('input', suggestions);
  parId('ajouter-etape').addEventListener('click', () => {
    const parent = TACHES.find(tache => tache.id === tacheSelectionnee);
    if (!parent || parent.parente) return;
    menu.close();
    preparerAjout(parent.id);
  });
  parId('abandonner-tache').addEventListener('click', () => {
    const tache = TACHES.find(item => item.id === tacheSelectionnee);
    if (!tache) return;
    parId('intitule-confirmation').textContent = tache.intitule;
    menu.close();
    ouvrir(confirmation, confirmation.querySelector('[data-fermer]'));
  });
  parId('confirmer-abandon').addEventListener('click', () => {
    try {
      abandonner(tacheSelectionnee);
    } catch (erreur) {
      signalerErreur(erreur, confirmation);
      return;
    }
    afficher();
    confirmation.close();
    annoncer('Tâche conservée dans les tâches abandonnées.');
  });

  formulaire.addEventListener('invalid', event => {
    signalerErreur(new Error(event.target.validationMessage), ajout);
  }, true);

  formulaire.addEventListener('submit', event => {
    event.preventDefault();
    const intitule = parId('intitule').value;
    if (!intitule.trim()) {
      signalerErreur(new Error('Indique un intitulé pour continuer.'), ajout);
      parId('intitule').focus();
      return;
    }
    try {
      if (parenteAjout !== null) {
        ajouterEtape(parenteAjout, intitule);
      } else {
        const champs = {
          intitule,
          categorie: parId('categorie').value.trim(),
          sous_categorie: parId('sous-categorie').value.trim(),
          echeance: parId('echeance').value || '',
          avant_le: parId('avant-le').value || '',
          priorite: parId('priorite').value,
          note: parId('note').value,
          origine: 'ajout à la main',
          fictif: false
        };
        const modele = parId('modele').value;
        if (modele) creerAvecEtapesParDefaut(champs, modele);
        else creerTache(champs);
      }
    } catch (erreur) {
      signalerErreur(erreur, ajout);
      return;
    }
    afficher();
    ajout.close();
    annoncer(`Tâche ajoutée : ${intitule}`);
  });

  archiveElement.addEventListener('click', () => {
    archiveOuverte = !archiveOuverte;
    afficher();
  });
  function afficherResultatDemande(resultat, origine) {
    if (resultat.type === 'tache') afficher();
    annoncer(resultat.message);
    if (resultat.type !== 'tache') return;
    const annuler = element('button', 'annuler-dictee', 'Annuler');
    annuler.type = 'button';
    annuler.addEventListener('click', () => {
      try {
        abandonner(resultat.tache.id);
      } catch (erreur) {
        const rendreFocus = document.activeElement === annuler;
        signalerErreur(erreur);
        if (rendreFocus) origine.focus({ preventScroll: true });
        return;
      }
      afficher();
      if (document.activeElement === annuler) origine.focus({ preventScroll: true });
      annoncer('Tâche abandonnée : tu la retrouves dans les tâches abandonnées.');
    });
    statutElement.append(annuler);
    delaiStatut = setTimeout(() => {
      if (document.activeElement === annuler) origine.focus({ preventScroll: true });
      annuler.remove();
    }, 8000);
  }

  function selectionnerPhrase(phrase) {
    phraseSelectionnee = phrase;
    parId('debut-phrase').textContent = phrase ? phrase.debut : '';
    parId('phrase-selectionnee').hidden = !phrase;
    if (phrase) saisieDemande.setAttribute('aria-describedby', 'debut-phrase');
    else saisieDemande.removeAttribute('aria-describedby');
    saisieDemande.focus();
  }

  function envoyerDemandeClavier(demande) {
    const erreur = clavier.querySelector('.erreur');
    erreur.hidden = true;
    erreur.textContent = '';
    let resultat;
    try {
      resultat = traiterDemande(demande);
    } catch (erreur) {
      signalerErreur(erreur, clavier);
      return;
    }
    if (resultat.type === 'vide') {
      signalerErreur(new Error(resultat.message), clavier);
      return;
    }
    saisieDemande.value = '';
    phraseSelectionnee = null;
    parId('debut-phrase').textContent = '';
    parId('phrase-selectionnee').hidden = true;
    saisieDemande.removeAttribute('aria-describedby');
    clavier.close();
    afficherResultatDemande(resultat, parId('ouvrir-clavier'));
  }

  function choisirPhrase(phrase) {
    if (phrase.a_completer) {
      selectionnerPhrase(phrase);
      return;
    }
    try {
      envoyerDemandeClavier({
        texte: composerTexte(phrase, ''), source: 'clavier', id_phrase: phrase.id, complement: ''
      });
    } catch (erreur) {
      signalerErreur(erreur, clavier);
    }
  }

  function boutonPhrase(phrase) {
    const bouton = element('button', 'phrase-clavier', phrase.debut);
    bouton.type = 'button';
    bouton.addEventListener('click', () => choisirPhrase(phrase));
    return bouton;
  }

  function reconstruireClavier() {
    reponseSilencieuse.setAttribute('aria-checked', String(preferencesClavier.silencieux()));
    const plusUtilisees = preferencesClavier.plusUtilisees(4).slice(0, 4);
    parId('plus-utilisees').replaceChildren(...plusUtilisees.map(boutonPhrase));
    parId('section-plus-utilisees').hidden = plusUtilisees.length === 0;
    const categories = new Map();
    for (const phrase of PHRASES_CLAVIER) {
      if (!categories.has(phrase.categorie)) categories.set(phrase.categorie, []);
      categories.get(phrase.categorie).push(phrase);
    }
    const sections = [];
    for (const [categorie, phrases] of categories) {
      const section = element('section', 'categorie-clavier');
      const titre = element('h3', '', categorie);
      const liste = element('div', 'liste-phrases');
      liste.append(...phrases.map(boutonPhrase));
      section.append(titre, liste);
      sections.push(section);
    }
    parId('categories-clavier').replaceChildren(...sections);
    const historique = preferencesClavier.historique().slice(0, 10);
    parId('historique-demandes').replaceChildren(...historique.map(demande => {
      const bouton = element('button', 'demande-historique', demande.texte);
      bouton.type = 'button';
      bouton.addEventListener('click', () => envoyerDemandeClavier({
        texte: demande.texte,
        source: demande.source,
        id_phrase: demande.id_phrase,
        complement: demande.complement
      }));
      return bouton;
    }));
    parId('section-historique').hidden = historique.length === 0;
  }

  parId('ouvrir-clavier').addEventListener('click', event => {
    ouvrir(clavier, clavier.querySelector('[data-fermer]'), event.currentTarget);
    try {
      reconstruireClavier();
    } catch (erreur) {
      signalerErreur(erreur, clavier);
    }
  });

  parId('enlever-phrase').addEventListener('click', () => selectionnerPhrase(null));

  reponseSilencieuse.addEventListener('click', () => {
    try {
      preferencesClavier.definirSilencieux(!preferencesClavier.silencieux());
      reponseSilencieuse.setAttribute('aria-checked', String(preferencesClavier.silencieux()));
    } catch (erreur) {
      signalerErreur(erreur, clavier);
    }
  });

  parId('formulaire-demande').addEventListener('submit', event => {
    event.preventDefault();
    const complement = saisieDemande.value;
    try {
      if (phraseSelectionnee?.a_completer && !complement.trim()) {
        signalerErreur(new Error('Complète la phrase pour continuer.'), clavier);
        saisieDemande.focus();
        return;
      }
      envoyerDemandeClavier({
        texte: phraseSelectionnee ? composerTexte(phraseSelectionnee, complement) : complement,
        source: phraseSelectionnee ? 'clavier' : 'saisie',
        id_phrase: phraseSelectionnee ? phraseSelectionnee.id : '',
        complement: phraseSelectionnee ? complement : ''
      });
    } catch (erreur) {
      signalerErreur(erreur, clavier);
    }
  });

  function ajouterDictee(texte) {
    const intitule = texte.trim();
    try {
      const resultat = traiterDemande({ texte: intitule, source: 'micro' });
      afficherResultatDemande(resultat, parId('microphone'));
    } catch (erreur) {
      const message = erreur instanceof Error ? erreur.message : 'L’action n’a pas pu être enregistrée.';
      annoncer(`${message} Texte dicté à recopier : « ${intitule} »`);
    }
  }

  parId('microphone').addEventListener('click', () => {
    if (dictee.enCours()) {
      dictee.arreter();
      return;
    }
    if (!dictee.disponible()) {
      annoncer("La dictée n'est pas disponible dans ce navigateur. Utilise le bouton +.");
      return;
    }
    const micro = parId('microphone');
    let resultatRecu = false;
    let finalRecu = false;
    micro.setAttribute('aria-pressed', 'true');
    micro.setAttribute('aria-label', 'Arrêter la dictée');
    annoncer("Je t'écoute…");
    dictee.demarrer({
      surProvisoire(texte) {
        if (!finalRecu) annoncer(texte || "Je t'écoute…");
      },
      surFinal(texte) {
        if (finalRecu) return;
        resultatRecu = true;
        finalRecu = true;
        ajouterDictee(texte);
      },
      surErreur(code) {
        resultatRecu = true;
        if (finalRecu) return;
        const messages = {
          'not-allowed': 'Le micro est bloqué. Autorise-le pour cette page dans le navigateur.',
          'service-not-allowed': 'Le micro est bloqué. Autorise-le pour cette page dans le navigateur.',
          'no-speech': "Je n'ai rien entendu, réessaie.",
          network: "La dictée a besoin d'internet pour l'instant.",
          'audio-capture': 'Aucun micro trouvé.'
        };
        annoncer(code === 'aborted' ? '' : (messages[code] || "La dictée n'a pas marché, réessaie."));
      },
      surFin() {
        micro.setAttribute('aria-pressed', 'false');
        micro.setAttribute('aria-label', 'Dicter une tâche');
        if (!resultatRecu) annoncer("Je n'ai rien entendu, réessaie.");
      }
    });
  });

  function actualiserHorloge() {
    const maintenant = new Date();
    const dateTexte = formatDate.format(maintenant).toLocaleLowerCase('fr-FR');
    if (dateElement.textContent !== dateTexte) {
      dateElement.textContent = dateTexte;
      const annee = maintenant.getFullYear();
      const mois = String(maintenant.getMonth() + 1).padStart(2, '0');
      const jour = String(maintenant.getDate()).padStart(2, '0');
      dateElement.dateTime = `${annee}-${mois}-${jour}`;
    }
    if (dernierJour && dernierJour !== dateTexte) {
      try {
        afficher();
      } catch (erreur) {
        signalerErreur(erreur);
      }
    }
    dernierJour = dateTexte;
  }

  let erreurAgenda = '';
  const formatRendezVous = new Intl.DateTimeFormat('fr-FR', {
    weekday: 'short', day: 'numeric', month: 'short'
  });

  let minuteurExpiration;

  function afficherEtatGoogle() {
    const connecte = googleConnexion.connecte();
    const info = synchronisation.informations();
    const nombre = info.nombre;
    const resume = nombre === null ? 'Nombre de modifications en attente inconnu'
      : !navigator.onLine ? `Hors connexion : ${nombre} en attente`
        : nombre ? `${nombre} modifications en attente`
          : !connecte ? 'Non connecté à Google' : !info.pret ? 'Préparation de l’envoi…' : 'Tout est envoyé';
    parId('texte-etat-google').textContent = [resume, info.erreur, erreurAgenda,
      info.illisibles ? `${info.illisibles} lignes du tableau sont illisibles, je n’y touche pas` : '']
      .filter(Boolean).join(' — ');
    const dernier = parId('dernier-envoi');
    dernier.textContent = info.dernierEnvoi
      ? `Dernier envoi réussi : ${formatHeure.format(new Date(info.dernierEnvoi))}` : 'Aucun envoi réussi pour le moment';
    const synchroniser = parId('synchroniser-maintenant');
    synchroniser.hidden = !connecte;
    synchroniser.disabled = info.enCours;
    synchroniser.textContent = info.enCours ? 'Envoi…' : 'Synchroniser maintenant';
    parId('connexion-google').hidden = connecte || googleConnexion.reconnexion();
    const alerte = parId('alerte-google');
    const visible = (googleConnexion.reconnexion() && !connecte)
      || googleConnexion.besoinGeste() || Boolean(googleConnexion.message());
    const apparait = alerte.hidden && visible;
    alerte.hidden = !visible;
    if (visible) {
      const attente = nombre === null ? 'Les tâches sont gardées sur ton téléphone ; la file est illisible.'
        : nombre ? `${nombre} tâches attendent : elles sont gardées sur ton téléphone.` : 'Rien n’est perdu.';
      parId('texte-alerte-google').textContent = [googleConnexion.besoinGeste()
        ? 'Google demande ton accord pour continuer.' : 'Google a coupé l’accès.', attente,
      googleConnexion.besoinGeste() ? '' : googleConnexion.message()].filter(Boolean).join(' ');
    }
    if (apparait) {
      try { navigator.vibrate?.(200); } catch (erreur) {}
    }
    if (!connecte) remplirRendezVous(googleAgenda.lireCache() || []);
    clearTimeout(minuteurExpiration);
    const delai = googleConnexion.expiration() - Date.now() - 60000;
    if (connecte && delai > 0) minuteurExpiration = setTimeout(afficherEtatGoogle, Math.min(delai + 1, 2147483647));
  }

  function tenterReconnexionSilencieuse() {
    const texteSaisi = Array.from(document.querySelectorAll('input:not([type="checkbox"]):not([type="button"]):not([type="submit"]), textarea, [contenteditable="true"]'))
      .some(champ => (champ.value ?? champ.textContent).trim());
    const conditionsOk = !document.hidden && !document.querySelector('dialog[open]')
      && !dictee.enCours() && !texteSaisi;
    try { googleConnexion.tenterSilencieux(conditionsOk); } catch (erreur) { signalerErreur(erreur); }
  }

  const ecranComplet = parId('ecran-complet');
  const accueil = parId('accueil');
  const basculerVue = parId('basculer-vue');

  function changerVue(complete) {
    document.body.classList.toggle('vue-complete', complete);
    ecranComplet.hidden = !complete;
    ecranComplet.inert = !complete;
    accueil.hidden = complete;
    accueil.inert = complete;
    zoneRecherche.hidden = complete;
    zoneRecherche.inert = complete;
    basculerVue.textContent = complete ? 'Revenir à l’accueil' : 'Afficher tout';
    basculerVue.setAttribute('aria-expanded', String(complete));
    if (complete) ecranComplet.focus({ preventScroll: true });
    else parId('ajouter').focus({ preventScroll: true });
  }

  basculerVue.addEventListener('click', () => changerVue(ecranComplet.hidden));
  let debutGlissement = null;
  const surface = document.querySelector('.ecran');
  surface.addEventListener('touchstart', event => {
    debutGlissement = null;
    if (event.touches.length !== 1 || document.querySelector('dialog[open]')
      || event.target.closest('button, input, textarea, select, a, #alerte-google, #zone-recherche')) return;
    const touche = event.touches[0];
    debutGlissement = { x: touche.clientX, y: touche.clientY,
      complete: !ecranComplet.hidden, enHaut: ecranComplet.scrollTop === 0 };
  }, { passive: true });
  surface.addEventListener('touchend', event => {
    const debut = debutGlissement;
    debutGlissement = null;
    if (!debut || document.querySelector('dialog[open]')
      || event.changedTouches.length !== 1 || event.touches.length) return;
    const touche = event.changedTouches[0];
    const vertical = touche.clientY - debut.y;
    if (Math.abs(vertical) <= 60 || Math.abs(vertical) <= Math.abs(touche.clientX - debut.x)) return;
    if (!debut.complete && vertical < 0) changerVue(true);
    else if (debut.complete && vertical > 0 && debut.enHaut && ecranComplet.scrollTop === 0) changerVue(false);
  }, { passive: true });
  surface.addEventListener('touchcancel', () => { debutGlissement = null; }, { passive: true });

  function remplirRendezVous(rendezVous) {
    parId('liste-rendez-vous').replaceChildren(...rendezVous.map(rendezVous => {
      const ligne = element('li');
      ligne.dataset.rendezVous = identiteRendezVous(rendezVous);
      const bouton = element('button', 'ouvrir-rdv', texteRendezVous(rendezVous));
      bouton.type = 'button';
      bouton.dataset.rdvFocus = `liste-${rendezVous.id || identiteRendezVous(rendezVous)}`;
      bouton.setAttribute('aria-haspopup', 'dialog');
      bouton.setAttribute('aria-controls', 'fiche-rendez-vous');
      bouton.addEventListener('click', () => ouvrirResultatRendezVous(rendezVous, bouton));
      ligne.append(bouton);
      return ligne;
    }));
    parId('rendez-vous').hidden = rendezVous.length === 0;
  }

  async function afficherRendezVous() {
    remplirRendezVous(googleAgenda.lireCache() || []);
    if (!googleConnexion.connecte()) return;
    try {
      const rendezVous = await googleAgenda.prochainsRendezVous();
      remplirRendezVous(googleConnexion.connecte() ? rendezVous : googleAgenda.lireCache() || []);
      erreurAgenda = '';
    } catch (erreur) {
      erreurAgenda = 'Les rendez-vous ne sont pas disponibles pour le moment.';
    }
    afficherRecherche();
    afficherEtatGoogle();
  }

  for (const id of ['connexion-google', 'redonner-acces-google']) {
    parId(id).addEventListener('click', () => {
      try { googleConnexion.seConnecter(); } catch (erreur) { signalerErreur(erreur); }
    });
  }
  parId('synchroniser-maintenant').addEventListener('click', () => {
    void (synchronisation.informations().pret ? synchronisation.envoyer() : synchronisation.demarrer());
  });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) return;
    afficherEtatGoogle();
    tenterReconnexionSilencieuse();
    synchronisation.reprendre();
  });
  window.addEventListener('cap-google-etat', afficherEtatGoogle);
  window.addEventListener('cap-google-deconnecte', afficherEtatGoogle);
  window.addEventListener('cap-google-fusion', afficher);
  window.addEventListener('online', () => { void afficherRendezVous(); });
  afficherEtatGoogle();
  tenterReconnexionSilencieuse();
  if (googleConnexion.connecte()) {
    void synchronisation.demarrer().then(() => {
      afficher();
      return afficherRendezVous();
    }).catch(erreur => signalerErreur(erreur));
  }
  setInterval(afficherEtatGoogle, 30000);
  actualiserHorloge();
  setInterval(actualiserHorloge, 1000);
  try {
    const info = parId('info-chargement');
    info.textContent = INFO_CHARGEMENT;
    info.hidden = !INFO_CHARGEMENT;
    if (INFO_CHARGEMENT) annoncer(INFO_CHARGEMENT);
    afficher();
    afficherRecherche();
  } catch (erreur) {
    signalerErreur(erreur);
  }
})();
