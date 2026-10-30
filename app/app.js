(() => {
  'use strict';

  const parId = id => document.getElementById(id);
  const dateElement = parId('date');
  const listeElement = parId('liste-taches');
  const statutElement = parId('statut');
  const archiveElement = parId('basculer-archive');
  const listeArchiveElement = parId('liste-archive');
  const termineesElement = parId('basculer-terminees');
  const listeTermineesElement = parId('liste-terminees');
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
  let termineesOuvertes = false;
  let vueActuelle = { type: 'tuiles', categorie: '' };
  let derniereTache = null;
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

  function retenirTache(id) {
    derniereTache = { id, heure: Date.now() };
  }

  function racineDe(tache) {
    const parent = TACHES.find(item => item.id === tache.parente);
    return tache.parente && parent && !parent.abandonnee_le ? parent : tache;
  }

  function estTerminee(tache) {
    const racine = racineDe(tache);
    return !tache.abandonnee_le && Boolean(racine.fait) && !racine.abandonnee_le;
  }

  function ouvrirResultatTache(tache) {
    retenirTache(tache.id);
    if (vueActuelle.type !== 'tout') {
      vueActuelle = { type: 'tout', categorie: '' };
      afficher();
    }
    if (tache.abandonnee_le) {
      archiveOuverte = true;
      afficher();
    } else if (estTerminee(tache) && !termineesOuvertes) {
      termineesOuvertes = true;
      afficher();
    }
    changerVue(true);
    const liste = tache.abandonnee_le ? listeArchiveElement : estTerminee(tache) ? listeTermineesElement : listeElement;
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
      abandon: 'Abandonné', remise: 'Remis', 'échéance': 'Échéance changée', classement: 'Classé'
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
      const texte = `${libelles[action.type]} : ${action.texte}`;
      const memeTexte = TACHES.filter(tache => tache.intitule === action.texte);
      const tache = action.id !== undefined ? TACHES.find(item => item.id === action.id)
        : memeTexte.length === 1 ? memeTexte[0] : null;
      if (tache) {
        const bouton = element('button', 'lien-action', texte);
        bouton.type = 'button';
        bouton.addEventListener('click', () => ouvrirResultatTache(tache));
        ligne.append(bouton);
      } else {
        ligne.append(element('span', '', texte));
      }
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
      cible = Array.from(document.querySelectorAll('#liste-taches [data-focus], #liste-terminees [data-focus], #liste-archive [data-focus]'))
        .find(noeud => noeud.dataset.focus === repere.cle);
    }
    if ((!cible?.isConnected || cible.closest('[hidden], [inert]')) && repere?.cle && !termineesElement.closest('[hidden], [inert]')) {
      cible = termineesElement;
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

  const questionDate = parId('question-date');
  fermetureFenetres.installer(questionDate);
  let questionEnCours = null;
  questionDate.addEventListener('close', () => {
    if (questionDate.open) return;
    const question = questionEnCours;
    questionEnCours = null;
    question?.surRefus?.();
  });

  function demanderDate(choix, texte, surChoix, surRefus) {
    if (questionDate.open) {
      const ancienne = questionEnCours;
      questionEnCours = null;
      questionDate.close();
      ancienne?.surRefus?.();
    }
    const question = { surRefus };
    parId('texte-question-date').textContent = texte;
    parId('choix-question-date').replaceChildren(...choix.map(valeur => {
      const bouton = element('button', 'choix-date-possible', choixDates.dateEnLettres(valeur));
      bouton.type = 'button';
      bouton.addEventListener('click', () => {
        if (questionEnCours === question) questionEnCours = null;
        questionDate.close();
        surChoix(valeur);
      });
      return bouton;
    }));
    questionEnCours = question;
    questionDate.showModal();
    parId('choix-question-date').querySelector('button').focus({ preventScroll: true });
  }

  function proposerEcheance(tache, choix) {
    if (!choix?.length) return;
    demanderDate(choix, `Pour « ${tache.intitule} », je ne suis pas sûr de la date. Laquelle ?`, valeur => {
      try {
        journalActions.pendant({ source: 'question sur la date', entree: valeur, compris: 'échéance choisie' },
          () => changerEcheance(tache.id, valeur));
      } catch (erreur) {
        signalerErreur(erreur);
        return;
      }
      afficher();
      annoncer(`Échéance : ${choixDates.dateEnLettres(valeur)}.`);
    }, () => annoncer('Pas d’échéance pour cette tâche : choisis-la plus tard si besoin.'));
  }

  function texteEcheance(tache) {
    return tache.echeance ? ` Échéance : ${choixDates.dateEnLettres(tache.echeance)}.` : '';
  }

  fermetureFenetres.installer(menu);
  fermetureFenetres.installer(confirmation);
  fermetureFenetres.installer(clavier);
  fermetureFenetres.installer(ajout, {
    cle: () => `ajout:${parenteAjout ?? 'tache'}`,
    rouvrir: () => {
      const parente = parenteAjout;
      return () => preparerAjout(parente, null);
    }
  });

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

  function creerLigne(tache, contexte = false, estArchive = false, termine = false) {
    const ligne = element('li', tache.parente ? 'tache etape' : 'tache');
    ligne.dataset.tache = tache.id;
    const texte = element('span', estArchive ? 'texte-tache texte-archive' : 'texte-tache');
    details(tache, texte, contexte || estArchive);
    if (termine && !tache.parente) {
      texte.append(element('span', 'classement', [tache.categorie || 'Sans catégorie', tache.sous_categorie].filter(Boolean).join(' > ')));
    }
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
        proposerAnnulation(`Tâche remise : ${tache.intitule}`, () => abandonner(tache.id),
          `De nouveau dans les tâches abandonnées : ${tache.intitule}`, parId('basculer-vue'));
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
      const nouvelEtat = caseACocher.checked;
      try {
        cocher(tache.id, nouvelEtat);
      } catch (erreur) {
        caseACocher.checked = !nouvelEtat;
        signalerErreur(erreur);
        return;
      }
      afficher();
      proposerAnnulation(`${nouvelEtat ? 'Terminée' : 'Remise à faire'} : ${tache.intitule}`, () => cocher(tache.id, !nouvelEtat),
        `${nouvelEtat ? 'Remise à faire' : 'De nouveau terminée'} : ${tache.intitule}`, parId('basculer-vue'));
    });
    etiquette.append(caseACocher, texte);
    const options = element('button', 'options-tache', '…');
    options.type = 'button';
    options.dataset.focus = JSON.stringify(['options', tache.id]);
    options.setAttribute('aria-label', `Actions : ${tache.intitule}`);
    options.setAttribute('aria-haspopup', 'dialog');
    options.addEventListener('click', () => {
      tacheSelectionnee = tache.id;
      retenirTache(tache.id);
      parId('intitule-menu').textContent = tache.intitule;
      parId('ajouter-etape').hidden = Boolean(tache.parente);
      ouvrir(menu, tache.parente ? parId('abandonner-tache') : parId('ajouter-etape'), options);
    });
    ligne.append(etiquette, options);
    activerGlissement(ligne, tache);
    return ligne;
  }

  function proposerAnnulation(message, action, messageApres, origine) {
    annoncer(message);
    const annuler = element('button', 'annuler-dictee', 'Annuler');
    annuler.type = 'button';
    const rendreFocus = () => {
      const cible = origine?.isConnected && !origine.closest('[hidden], [inert]') ? origine : parId('basculer-vue');
      cible.focus({ preventScroll: true });
    };
    const retirer = () => {
      if (document.activeElement === annuler) rendreFocus();
      annuler.remove();
    };
    const entree = annulation.proposer({
      annuler: () => {
        journalActions.pendant({ source: 'Annuler', entree: 'Annuler', compris: 'annuler la dernière action' }, action);
        afficher();
      },
      messageApres,
      retirer
    });
    annuler.addEventListener('click', () => {
      const avaitFocus = document.activeElement === annuler;
      try {
        annulation.executer(entree);
      } catch (erreur) {
        signalerErreur(erreur);
        if (avaitFocus) rendreFocus();
        return;
      }
      if (avaitFocus) rendreFocus();
      annoncer(messageApres);
    });
    statutElement.append(annuler);
    delaiStatut = setTimeout(() => {
      annulation.expirer(entree);
      retirer();
    }, annulation.DUREE_MS);
  }

  function annulerParLaParole(origine) {
    let message;
    try {
      message = annulation.annulerDerniere();
    } catch (erreur) {
      signalerErreur(erreur);
      return;
    }
    if (!message) {
      annoncer('Il n’y a plus rien à annuler : le délai de 8 secondes est passé, ou rien n’a été fait.');
      return;
    }
    annoncer(message);
    const cible = origine?.isConnected && !origine.closest('[hidden], [inert]') ? origine : null;
    cible?.focus({ preventScroll: true });
  }

  function terminerParGlissement(tache) {
    if (tache.fait) {
      annoncer('Cette tâche est déjà terminée.', true);
      return;
    }
    try {
      cocher(tache.id, true);
    } catch (erreur) {
      signalerErreur(erreur);
      return;
    }
    afficher();
    proposerAnnulation(`Terminée : ${tache.intitule}`, () => cocher(tache.id, false),
      `Remise à faire : ${tache.intitule}`, parId('ecran-complet'));
  }

  function reporterTache(id, origine) {
    const tache = TACHES.find(item => item.id === id);
    if (!tache || tache.abandonnee_le) {
      annoncer('Je ne trouve pas cette tâche.');
      return;
    }
    let ancienne;
    try {
      ancienne = reporterADemain(tache.id);
    } catch (erreur) {
      signalerErreur(erreur);
      return;
    }
    retenirTache(tache.id);
    afficher();
    proposerAnnulation(`Reportée à demain : ${tache.intitule}`, () => changerEcheance(tache.id, ancienne),
      `Report annulé : ${tache.intitule}`, origine);
  }

  function activerGlissement(ligne, tache) {
    let depart = null;
    const remettreEnPlace = () => {
      ligne.style.transform = '';
      ligne.classList.remove('glisse');
      delete ligne.dataset.sens;
    };
    ligne.addEventListener('pointerdown', event => {
      if (event.pointerType === 'mouse' && event.button !== 0) return;
      if (event.target.closest('.options-tache')) return;
      depart = { x: event.clientX, y: event.clientY, id: event.pointerId, actif: false };
    });
    ligne.addEventListener('pointermove', event => {
      if (!depart || event.pointerId !== depart.id) return;
      const ecartX = event.clientX - depart.x;
      const ecartY = event.clientY - depart.y;
      if (!depart.actif) {
        if (Math.abs(ecartY) > 12 && Math.abs(ecartY) > Math.abs(ecartX)) {
          depart = null;
          return;
        }
        if (Math.abs(ecartX) < 12) return;
        depart.actif = true;
        try { ligne.setPointerCapture(event.pointerId); } catch (erreur) {}
        ligne.classList.add('glisse');
      }
      ligne.style.transform = `translateX(${ecartX}px)`;
      ligne.dataset.sens = ecartX > 0 ? 'droite' : 'gauche';
    });
    const finir = event => {
      if (!depart || event.pointerId !== depart.id) return;
      const etat = depart;
      depart = null;
      if (!etat.actif) return;
      remettreEnPlace();
      const bloquer = clic => {
        clic.preventDefault();
        clic.stopPropagation();
      };
      ligne.addEventListener('click', bloquer, { capture: true, once: true });
      setTimeout(() => ligne.removeEventListener('click', bloquer, true), 400);
      if (event.type === 'pointercancel') return;
      const ecartX = event.clientX - etat.x;
      const seuil = Math.min(90, ligne.offsetWidth * 0.3);
      if (ecartX >= seuil) terminerParGlissement(tache);
      else if (ecartX <= -seuil) reporterTache(tache.id, parId('ecran-complet'));
    };
    ligne.addEventListener('pointerup', finir);
    ligne.addEventListener('pointercancel', finir);
  }

  function afficher() {
    const actif = document.activeElement;
    const repere = listeElement.contains(actif) || listeArchiveElement.contains(actif)
      || listeTermineesElement.contains(actif) ? repereFocus(actif) : null;
    const fragment = document.createDocumentFragment();
    const parIdTache = new Map(TACHES.map(tache => [tache.id, tache]));
    const visibles = TACHES.filter(tache => !tache.abandonnee_le);
    const toutesRacines = visibles.filter(tache => {
      const parent = parIdTache.get(tache.parente);
      return !tache.parente || !parent || parent.abandonnee_le;
    });
    const dansVue = vueActuelle.type === 'categorie'
      ? tache => (tache.categorie || '') === vueActuelle.categorie
      : vueActuelle.type === 'aujourdhui' ? estPourAujourdhui : () => true;
    const racines = toutesRacines.filter(tache => !tache.fait && dansVue(tache));
    const terminees = toutesRacines.filter(tache => tache.fait && dansVue(tache));
    const groupes = new Map();
    for (const tache of racines) {
      if (!groupes.has(tache.categorie)) groupes.set(tache.categorie, new Map());
      const sousGroupes = groupes.get(tache.categorie);
      const avecSous = tache.categorie && tache.categorie !== listesChoix.A_TRIER && listesChoix.categories(tache.categorie).length > 0;
      const cleSous = !tache.sous_categorie && avecSous ? sousCategories.A_CLASSER : tache.sous_categorie;
      if (!sousGroupes.has(cleSous)) sousGroupes.set(cleSous, []);
      sousGroupes.get(cleSous).push(tache);
    }
    const categoriesTriees = [...groupes].sort(([a], [b]) =>
      Number(b === 'À trier') - Number(a === 'À trier'));
    for (const [categorie, sousGroupes] of categoriesTriees) {
      const section = element('section', 'categorie');
      if (categorie) section.style.setProperty('--couleur-categorie', listesChoix.couleur(categorie));
      section.append(element('h2', '', categorie || 'Sans catégorie'));
      const rangSous = nom => (!nom ? 0 : sousCategories.estAClasser(nom) ? 1 : 2);
      const sousTries = [...sousGroupes].sort(([a], [b]) => rangSous(a) - rangSous(b));
      for (const [sousCategorie, taches] of sousTries) {
        const sousSection = element('section', 'sous-categorie');
        if (sousCategorie) {
          const titre = element('h3');
          titre.append(element('span', '', sousCategorie));
          if (!sousCategories.estAClasser(sousCategorie)) {
            titre.append(element('span', 'pourcentage', `${avancementSousCategorie(categorie, sousCategorie)} %`));
          }
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
    } else if (racines.length === 0) {
      fragment.append(element('p', 'etat-vide', vueActuelle.type === 'aujourdhui'
        ? 'Rien de dû aujourd’hui, rien en retard.' : vueActuelle.type === 'categorie' && terminees.length === 0
          ? 'Aucune tâche dans cette catégorie. Le micro de la tuile permet d’en dicter une.' : 'Tout est terminé. Bravo !'));
    }
    listeElement.replaceChildren(fragment);
    termineesElement.hidden = terminees.length === 0;
    termineesElement.textContent = `Terminées (${terminees.length})`;
    termineesElement.setAttribute('aria-expanded', String(termineesOuvertes && terminees.length > 0));
    listeTermineesElement.hidden = !termineesOuvertes || terminees.length === 0;
    listeTermineesElement.replaceChildren();
    if (termineesOuvertes) {
      for (const tache of [...terminees].reverse()) {
        listeTermineesElement.append(creerLigne(tache, Boolean(tache.parente), false, true));
        if (!tache.parente) {
          for (const etape of visibles.filter(item => item.parente === tache.id)) {
            listeTermineesElement.append(creerLigne(etape));
          }
        }
      }
    }
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
    afficherTuiles();
    appliquerVue();
  }

  function estPourAujourdhui(tache) {
    const jour = dateDuJour();
    return Boolean((tache.echeance && tache.echeance <= jour) || (tache.avant_le && tache.avant_le <= jour));
  }

  function racinesActives() {
    const parIdTache = new Map(TACHES.map(tache => [tache.id, tache]));
    return TACHES.filter(tache => {
      if (tache.abandonnee_le || tache.fait) return false;
      const parent = parIdTache.get(tache.parente);
      return !tache.parente || !parent || parent.abandonnee_le;
    });
  }

  function rendezVousDuJour() {
    const jour = dateDuJour();
    return (googleAgenda.lireCache() || []).filter(rendezVous => rendezVous.date === jour);
  }

  function titreDeVue() {
    const titres = { tuiles: 'Tout voir', tout: 'Tout', actions: 'Dernières actions',
      'rendez-vous': 'Prochains rendez-vous', aujourdhui: 'Aujourd’hui' };
    return vueActuelle.type === 'categorie' ? vueActuelle.categorie || 'Sans catégorie' : titres[vueActuelle.type];
  }

  function appliquerVue() {
    const ecran = parId('ecran-complet');
    ecran.dataset.vue = vueActuelle.type;
    parId('titre-vue').textContent = titreDeVue();
    parId('retour-tuiles').hidden = vueActuelle.type === 'tuiles';
    for (const bloc of ecran.querySelectorAll('[data-vues]')) {
      bloc.classList.toggle('hors-vue', !bloc.dataset.vues.split(' ').includes(vueActuelle.type));
    }
    const rdvJour = rendezVousDuJour();
    parId('liste-rdv-jour').replaceChildren(...rdvJour.map(rendezVous => {
      const ligne = element('li');
      const bouton = element('button', 'ouvrir-rdv', texteRendezVous(rendezVous));
      bouton.type = 'button';
      bouton.addEventListener('click', () => ouvrirResultatRendezVous(rendezVous, bouton));
      ligne.append(bouton);
      return ligne;
    }));
    parId('rendez-vous-du-jour').hidden = rdvJour.length === 0;
    const vide = parId('vide-vue');
    const messages = {
      actions: parId('dernieres-actions').hidden ? 'Aucune action pour le moment.' : '',
      'rendez-vous': parId('rendez-vous').hidden ? 'Aucun rendez-vous à venir (ou agenda pas encore lu).' : ''
    };
    vide.textContent = messages[vueActuelle.type] || '';
    vide.hidden = !vide.textContent;
  }

  function ouvrirVue(type, categorie = '') {
    vueActuelle = { type, categorie };
    termineesOuvertes = false;
    afficher();
    const ecran = parId('ecran-complet');
    ecran.scrollTop = 0;
    const cible = type === 'tuiles' ? parId('tuiles').querySelector('.ouvrir-tuile') : parId('retour-tuiles');
    (cible || ecran).focus({ preventScroll: true });
  }

  function afficherTuiles() {
    const actives = racinesActives();
    const compte = new Map();
    for (const tache of actives) compte.set(tache.categorie || '', (compte.get(tache.categorie || '') || 0) + 1);
    const noms = listesChoix.categories();
    const autres = [...compte.keys()].filter(nom => !noms.some(item => item.toLocaleLowerCase('fr') === nom.toLocaleLowerCase('fr')));
    const aTrier = compte.get(listesChoix.A_TRIER) || 0;
    tuiles.afficher(parId('tuiles'), {
      fixes: [
        { id: 'actions', titre: 'Dernières actions', compteur: journalActions.lire().length },
        { id: 'rendez-vous', titre: 'Prochains rendez-vous', compteur: (googleAgenda.lireCache() || []).length },
        { id: 'aujourdhui', titre: 'Aujourd’hui', compteur: actives.filter(estPourAujourdhui).length + rendezVousDuJour().length },
        { id: 'trier', titre: 'Trier', compteur: aTrier }
      ],
      categories: [...noms, ...autres].map(nom => ({
        titre: nom || 'Sans catégorie', categorie: nom, compteur: compte.get(nom) || 0,
        couleur: nom ? listesChoix.couleur(nom) : '', deplacable: nom !== '' && noms.includes(nom) && nom !== listesChoix.A_TRIER
      })),
      finales: [
        { id: 'tout', titre: 'Tout', compteur: actives.length },
        { id: 'ajouter-categorie', titre: '+ Ajouter' },
        { id: 'modifier-categories', titre: 'Modifier' }
      ]
    }, {
      surOuvrir: ouvrirTuile,
      surMicro: dicterDansCategorie,
      surOrdre(ordre) {
        listesChoix.ordonner(ordre);
        annoncer('Ordre des tuiles enregistré.', true);
      },
      surDebutDeplacement(nom) { annoncer(`Glisse « ${nom} » à sa nouvelle place.`, true); }
    });
  }

  function ouvrirTuile(id, categorie) {
    if (id === 'trier') {
      modeTrier.ouvrir(parId('mode-trier'), { surChangement: afficher, gererCategories: fenetresListes.gererCategories });
      return;
    }
    if (id === 'ajouter-categorie') {
      fenetresListes.gererCategories({ action: 'ajouter' });
      return;
    }
    if (id === 'modifier-categories') {
      fenetresListes.gererCategories({ action: 'modifier' });
      return;
    }
    if (categorie !== undefined) ouvrirVue('categorie', categorie);
    else ouvrirVue(id);
  }

  function dicterDansCategorie(categorie, bouton) {
    if (dictee.enCours()) {
      dictee.arreter();
      return;
    }
    if (!dictee.disponible()) {
      annoncer("La dictée n'est pas disponible dans ce navigateur. Utilise le bouton +.");
      return;
    }
    const nom = categorie || 'Sans catégorie';
    let recu = false;
    let provisoire = '';
    bouton.setAttribute('aria-pressed', 'true');
    bouton.classList.add('ecoute');
    annulation.garderPendantEcoute();
    annoncer(`Je t'écoute… (tâche pour ${nom})`);
    const ajouterDans = texte => {
      if (recu) return;
      recu = true;
      const intitule = texte.trim();
      if (!intitule) {
        annoncer("Je n'ai rien entendu, réessaie.");
        return;
      }
      if (annulation.estDemande(intitule)) {
        journalActions.consigner({ source: `micro de la tuile ${nom}`, entree: intitule, compris: 'annuler la dernière action', fait: 'annulation demandée' });
        annulerParLaParole(bouton);
        return;
      }
      let tache;
      const date = comprendreDemande.trouverDate(intitule);
      const sous = categorie
        ? sousCategories.trouver(intitule, categorie, listesChoix.categories(categorie), TACHES).sous_categorie : '';
      const destination = [nom, sous].filter(Boolean).join(' › ');
      try {
        tache = journalActions.pendant({ source: `micro de la tuile ${nom}`, entree: intitule, compris: `ajouter une tâche dans ${destination}` },
          () => creerTache({ intitule, categorie, sous_categorie: sous, echeance: date.date, origine: 'dictée' }));
      } catch (erreur) {
        annoncer(`${erreur instanceof Error ? erreur.message : 'Ajout impossible.'} Texte dicté : « ${intitule} »`);
        return;
      }
      retenirTache(tache.id);
      afficher();
      proposerAnnulation(`Ajoutée dans ${destination} : « ${intitule} »${texteEcheance(tache)}`, () => abandonner(tache.id),
        'Tâche abandonnée : tu la retrouves dans les tâches abandonnées.', bouton);
      proposerEcheance(tache, date.choix);
    };
    dictee.demarrer({
      surProvisoire(texte) {
        if (texte) provisoire = texte;
        if (!recu) annoncer(texte || `Je t'écoute… (tâche pour ${nom})`);
      },
      surFinal: ajouterDans,
      surErreur(code) {
        if (recu || code === 'aborted') return;
        recu = true;
        annoncer(code === 'not-allowed' || code === 'service-not-allowed'
          ? 'Le micro est bloqué. Autorise-le pour cette page dans le navigateur.' : "Je n'ai rien entendu, réessaie.");
      },
      surFin() {
        bouton.setAttribute('aria-pressed', 'false');
        bouton.classList.remove('ecoute');
        if (!recu && provisoire) ajouterDans(provisoire);
        else if (!recu) annoncer("Je n'ai rien entendu, réessaie.");
      }
    });
  }

  function afficherCategorieChoisie() {
    const categorie = parId('categorie').value;
    const sousCategorie = parId('sous-categorie').value;
    parId('texte-categorie').textContent = categorie ? (sousCategorie ? `${categorie} › ${sousCategorie}` : categorie) : 'Aucune';
    parId('choisir-categorie').style.setProperty('--couleur-categorie', categorie ? listesChoix.couleur(categorie) : 'transparent');
  }

  function remplirModeles(valeur = parId('modele').value) {
    const aucune = element('option', '', 'Aucune');
    aucune.value = '';
    const ajouterModele = element('option', '', 'Ajouter…');
    ajouterModele.value = '__ajouter';
    const modifierModeles = element('option', '', 'Modifier la liste…');
    modifierModeles.value = '__modifier';
    const noms = listesChoix.modeles();
    parId('modele').replaceChildren(aucune, ...noms.map(nom => {
      const option = element('option', '', nom);
      option.value = nom;
      return option;
    }), ajouterModele, modifierModeles);
    parId('modele').value = noms.includes(valeur) ? valeur : '';
    parId('modele').dataset.precedent = parId('modele').value;
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
    parId('categorie').value = '';
    parId('sous-categorie').value = '';
    remplirModeles('');
    ouvrir(ajout, parId('intitule'), origine);
    fermetureFenetres.restaurer(ajout);
    afficherCategorieChoisie();
  }

  parId('ajouter').addEventListener('click', event => preparerAjout(null, event.currentTarget));
  parId('choisir-categorie').addEventListener('click', () => {
    fenetresListes.choisirCategorie({
      categorie: parId('categorie').value,
      sousCategorie: parId('sous-categorie').value,
      surChoix(categorie, sousCategorie) {
        parId('categorie').value = categorie;
        parId('sous-categorie').value = sousCategorie;
        afficherCategorieChoisie();
        parId('choisir-categorie').focus({ preventScroll: true });
      }
    });
  });
  parId('modele').addEventListener('change', () => {
    const selection = parId('modele');
    const action = selection.value;
    if (action !== '__ajouter' && action !== '__modifier') {
      selection.dataset.precedent = action;
      return;
    }
    selection.value = selection.dataset.precedent || '';
    fenetresListes.gererModeles({
      action: action === '__ajouter' ? 'ajouter' : 'modifier',
      surFin(nom) {
        remplirModeles(nom);
        selection.focus({ preventScroll: true });
      }
    });
  });
  document.querySelectorAll('#formulaire-ajout .champ-date').forEach(champ => choixDates.installer(champ));
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
    const id = tacheSelectionnee;
    const tache = TACHES.find(item => item.id === id);
    const dejaAbandonnee = Boolean(tache?.abandonnee_le);
    try {
      abandonner(id);
    } catch (erreur) {
      signalerErreur(erreur, confirmation);
      return;
    }
    afficher();
    confirmation.close();
    if (dejaAbandonnee) {
      annoncer('Tâche conservée dans les tâches abandonnées.');
      return;
    }
    proposerAnnulation('Tâche conservée dans les tâches abandonnées.', () => remettre(id),
      `Tâche remise : ${tache.intitule}`, parId('basculer-vue'));
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
    let creee;
    try {
      if (parenteAjout !== null) {
        creee = ajouterEtape(parenteAjout, intitule);
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
        creee = modele ? creerAvecEtapesParDefaut(champs, modele) : creerTache(champs);
      }
    } catch (erreur) {
      signalerErreur(erreur, ajout);
      return;
    }
    afficher();
    ajout.close();
    proposerAnnulation(`Tâche ajoutée : ${intitule}`, () => abandonner(creee.id),
      'Tâche abandonnée : tu la retrouves dans les tâches abandonnées.', parId('basculer-vue'));
  });

  archiveElement.addEventListener('click', () => {
    archiveOuverte = !archiveOuverte;
    afficher();
  });
  termineesElement.addEventListener('click', () => {
    termineesOuvertes = !termineesOuvertes;
    afficher();
  });
  parId('reporter-tache').addEventListener('click', () => {
    const id = tacheSelectionnee;
    menu.close();
    reporterTache(id, parId('ecran-complet'));
  });
  function agendaDisponible() {
    return navigator.onLine && googleConnexion.connecte();
  }

  function noterDemande(source, texte, resultat) {
    if (resultat.type === 'tache') return;
    const compris = { annuler: 'annuler la dernière action', report: 'reporter la tâche ouverte à demain',
      proposition: 'proposition faite à Max', rendez_vous_ajoute: 'rendez-vous inscrit après le oui de Max',
      vide: 'rien reçu', pas_compris: 'pas compris', attente_cerveau: 'demande pour plus tard',
      question: 'question posée à Max', reflexion: 'demande envoyée au cerveau', reponse: 'conversation' };
    journalActions.consigner({ source, entree: texte, compris: compris[resultat.type] || resultat.type,
      fait: resultat.message || ({ report: 'report demandé', annuler: 'annulation demandée' }[resultat.type] || 'rien') });
  }

  function afficherResultatDemande(resultat, origine) {
    if (resultat.type === 'annuler') {
      annulerParLaParole(origine);
      return;
    }
    if (resultat.type === 'reflexion') {
      annoncer(resultat.message);
      resultat.suite.then(suite => afficherResultatDemande(suite, origine)).catch(erreur => signalerErreur(erreur))
        .finally(() => afficherCerveau());
      return;
    }
    if (resultat.type === 'question' || resultat.type === 'reponse' || resultat.type === 'proposition') {
      annoncer(resultat.message);
      voix.dire(resultat.parole);
      return;
    }
    if (resultat.type === 'report') {
      const recente = derniereTache && Date.now() - derniereTache.heure < 15 * 60 * 1000
        && TACHES.some(tache => tache.id === derniereTache.id && !tache.abandonnee_le);
      if (recente) reporterTache(derniereTache.id, origine);
      else annoncer('Je ne sais pas quelle tâche reporter. Ouvre-la d’abord (bouton …), ou glisse-la vers la gauche.');
      return;
    }
    if (resultat.type === 'rendez_vous_ajoute') {
      const rendezVous = resultat.rendezVous;
      const rafraichir = () => {
        erreurAgenda = '';
        remplirRendezVous(googleAgenda.lireCache() || []);
        afficherRecherche();
      };
      rafraichir();
      // Annuler n'efface rien chez Google : le rendez-vous est gardé, marqué « ANNULÉ » dans son titre.
      proposerAnnulation(resultat.message, () => {
        googleAgenda.modifierRendezVous(rendezVous.id, { titre: `ANNULÉ – ${rendezVous.titre}` })
          .then(rafraichir)
          .catch(erreur => signalerErreur(erreur));
      }, 'Rendez-vous annulé : il reste dans l’agenda Cap – FICTIF, marqué « ANNULÉ », car Cap n’efface jamais rien.', origine);
      voix.dire(resultat.parole);
      return;
    }
    if (resultat.type === 'tache') afficher();
    if (resultat.type !== 'tache') {
      annoncer(resultat.message);
      return;
    }
    proposerAnnulation(resultat.message + texteEcheance(resultat.tache), () => abandonner(resultat.tache.id),
      'Tâche abandonnée : tu la retrouves dans les tâches abandonnées.', origine);
    voix.dire(resultat.parole);
    proposerEcheance(resultat.tache, resultat.choix_echeance);
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
      resultat = journalActions.pendant({ source: 'clavier', entree: demande.texte, compris: 'noter une tâche dans À trier' },
        () => traiterDemande({ ...demande, agenda_disponible: agendaDisponible() }));
    } catch (erreur) {
      signalerErreur(erreur, clavier);
      return;
    }
    noterDemande('clavier', demande.texte, resultat);
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
    annulation.garderPendantEcoute();
    ouvrir(clavier, parId('titre-clavier'), event.currentTarget);
    try {
      reconstruireClavier();
    } catch (erreur) {
      signalerErreur(erreur, clavier);
    }
    fermetureFenetres.restaurer(clavier);
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
      const resultat = journalActions.pendant({ source: 'micro', entree: intitule, compris: 'noter une tâche dans À trier' },
        () => traiterDemande({ texte: intitule, source: 'micro', agenda_disponible: agendaDisponible() }));
      noterDemande('micro', intitule, resultat);
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
    annulation.garderPendantEcoute();
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
    const texteSaisi = Array.from(document.querySelectorAll('input:not([type="checkbox"]):not([type="button"]):not([type="submit"]):not([type="hidden"]), textarea, [contenteditable="true"]'))
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
    else {
      if (vueActuelle.type !== 'tuiles') {
        vueActuelle = { type: 'tuiles', categorie: '' };
        afficher();
      }
      parId('ajouter').focus({ preventScroll: true });
    }
  }

  parId('retour-tuiles').addEventListener('click', () => ouvrirVue('tuiles'));
  const aide = parId('aide');
  const fenetreTri = parId('mode-trier');
  fermetureFenetres.installer(aide);
  fermetureFenetres.installer(fenetreTri);
  fenetreTri.addEventListener('close', () => {
    if (dictee.enCours()) dictee.arreter();
    afficher();
  });
  parId('ouvrir-aide').addEventListener('click', event => {
    ouvrir(aide, parId('titre-aide'), event.currentTarget);
  });

  function afficherSauvegarde() {
    const etat = sauvegardeDrive.etat();
    const date = Date.parse(etat.derniere);
    const texte = Number.isFinite(date)
      ? `Dernière sauvegarde du tableau : ${formatDateCourte.format(new Date(date))}. Prochaine copie automatique une semaine après.`
      : 'Aucune sauvegarde du tableau pour le moment. La copie automatique chaque semaine commencera après la première.';
    const enTrop = etat.nombre > REGLAGES_GOOGLE.sauvegardes_a_garder
      ? ` Tu as ${etat.nombre} copies : Cap n’en supprime aucune sans ton accord.` : '';
    parId('texte-sauvegarde').textContent = texte + enTrop;
    parId('sauvegarder-maintenant').disabled = !googleConnexion.connecte();
  }

  parId('sauvegarder-maintenant').addEventListener('click', async event => {
    const bouton = event.currentTarget;
    bouton.disabled = true;
    annoncer('Sauvegarde du tableau en cours…');
    try {
      const resultat = await sauvegardeDrive.sauvegarder();
      annoncer(`Sauvegarde faite : « ${resultat.nom} », rangée dans le dossier ${REGLAGES_GOOGLE.dossier_sauvegardes}.`);
    } catch (erreur) {
      annoncer(`La sauvegarde n’a pas marché : ${erreur instanceof Error ? erreur.message : 'erreur inconnue'}. Rien n’a été perdu.`);
    }
    afficherSauvegarde();
  });
  window.addEventListener('cap-sauvegarde-etat', afficherSauvegarde);

  const reglagesIA = parId('reglages-ia');
  fermetureFenetres.installer(reglagesIA);
  const formatEuros = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', minimumFractionDigits: 2, maximumFractionDigits: 2 });

  async function afficherCerveau() {
    const cle = cleIA.presente();
    const usage = `Aujourd’hui : ${limiteIA.utilises()} échange(s) sur ${limiteIA.maximum()}. Dépensé ce mois-ci : environ ${formatEuros.format(limiteIA.depenseDuMois())}.`;
    parId('texte-cerveau').textContent = cle
      ? `Cerveau : ${REGLAGES_IA.nom}. ${usage}`
      : 'Cerveau : réponses préparées (gratuites). Aucune clé d’IA enregistrée.';
    parId('usage-ia').textContent = `${usage} Plafond du mois : ${formatEuros.format(limiteIA.plafondMensuel())}.`;
    parId('retirer-cle-ia').hidden = !cle;
    parId('retirer-fiche-ia').hidden = !cerveauClaude.ficheTelephone();
    if (reglagesIA.open && document.activeElement !== parId('limite-ia')) parId('limite-ia').value = String(limiteIA.maximum());
    if (reglagesIA.open && document.activeElement !== parId('plafond-ia')) parId('plafond-ia').value = String(limiteIA.plafondMensuel()).replace('.', ',');
    afficherJournalIA();
    let etat = cle ? `Clé enregistrée sur ce téléphone (${cleIA.apercu()}).` : 'Aucune clé : Cap utilise les réponses préparées, gratuites.';
    if (cle) {
      const consignes = await cerveauClaude.etatConsignes();
      etat += consignes === 'pret' ? ` Cap parle avec ${REGLAGES_IA.nom}.` : ` ${consignes} En attendant, Cap utilise les réponses préparées.`;
    }
    parId('etat-ia').textContent = etat;
    parId('fiche-ia').textContent = texteFiche();
  }

  function dateCourte(iso) {
    const date = new Date(iso);
    return Number.isNaN(date.getTime()) ? '' : `${date.toLocaleDateString('fr-FR')} à ${formatHeure.format(date)}`;
  }

  function texteFiche() {
    const info = cerveauClaude.infoConsignes();
    const quelle = cerveauClaude.origineFiche() === 'telephone' ? 'ta fiche, gardée sur ce téléphone' : 'la fiche de secours (aucune fiche collée)';
    return info ? `Fiche suivie : ${quelle}. Lue le ${dateCourte(info.lue_le)}, version du ${dateCourte(info.version_du)} (repère ${info.empreinte}).`
      : `Fiche suivie : ${quelle}. Pas encore lue.`;
  }

  parId('formulaire-fiche-ia').addEventListener('submit', async event => {
    event.preventDefault();
    try {
      await cerveauClaude.enregistrerFiche(parId('texte-fiche-ia').value);
      erreurReglagesIA('');
      annoncer('Ta fiche est enregistrée sur ce téléphone : je la suis à partir de maintenant.', true);
    } catch (erreur) {
      erreurReglagesIA(erreur.message);
    }
    afficherCerveau();
  });
  parId('retirer-fiche-ia').addEventListener('click', async () => {
    await cerveauClaude.retirerFiche();
    parId('texte-fiche-ia').value = '';
    erreurReglagesIA('');
    annoncer('Ta fiche est retirée de ce téléphone : je suis la fiche de secours.', true);
    afficherCerveau();
  });

  function afficherJournalIA() {
    const entrees = journalIA.lire().slice(0, 20);
    parId('liste-journal-ia').replaceChildren(...entrees.map(entree => {
      const ligne = element('li');
      ligne.append(element('span', 'heure-action', dateCourte(entree.heure)), document.createTextNode(` · Max : ${entree.dit}`));
      if (entree.repondu) ligne.append(element('br'), document.createTextNode(`Cap : ${entree.repondu}`));
      if (entree.action) ligne.append(element('br'), document.createTextNode(`Action demandée : ${entree.action}`));
      return ligne;
    }));
    if (!entrees.length) parId('liste-journal-ia').append(element('li', '', 'Aucun échange avec l’IA pour l’instant.'));
  }

  parId('effacer-journal-ia').addEventListener('click', () => {
    journalIA.effacer();
    annoncer('Historique de l’IA effacé.', true);
    afficherJournalIA();
  });
  parId('formulaire-plafond-ia').addEventListener('submit', event => {
    event.preventDefault();
    try {
      const plafond = limiteIA.definirPlafond(parId('plafond-ia').value);
      erreurReglagesIA('');
      annoncer(`Plafond enregistré : ${formatEuros.format(plafond)} par mois.`, true);
    } catch (erreur) {
      erreurReglagesIA(erreur.message);
    }
    afficherCerveau();
  });
  window.addEventListener('cap-consignes-changees', () => {
    annoncer(`Ma fiche de consignes a changé : je suis maintenant la version du ${dateCourte(cerveauClaude.infoConsignes()?.version_du)}.`, true);
  });
  // La fiche est relue à chaque ouverture (et au retour dans l'appli), en tâche de fond, pour que les premiers mots de Max soient compris.
  const prechargerFiche = () => { if (cleIA.presente()) cerveauClaude.precharger(); };
  prechargerFiche();
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') prechargerFiche(); });

  function erreurReglagesIA(message) {
    const zone = reglagesIA.querySelector('.erreur');
    zone.textContent = message;
    zone.hidden = !message;
  }

  parId('ouvrir-reglages-ia').addEventListener('click', event => {
    ouvrir(reglagesIA, parId('titre-reglages-ia'), event.currentTarget);
    parId('texte-fiche-ia').value = cerveauClaude.ficheTelephone();
    afficherCerveau();
  });
  parId('formulaire-cle-ia').addEventListener('submit', event => {
    event.preventDefault();
    const champ = parId('cle-ia');
    try {
      cleIA.enregistrer(champ.value);
      champ.value = '';
      erreurReglagesIA('');
      cerveauClaude.oublier();
      annoncer('Clé enregistrée sur ce téléphone.', true);
    } catch (erreur) {
      erreurReglagesIA(erreur.message);
    }
    afficherCerveau();
  });
  parId('retirer-cle-ia').addEventListener('click', () => {
    cleIA.retirer();
    cerveauClaude.oublier();
    erreurReglagesIA('');
    annoncer('Clé retirée de ce téléphone : Cap reprend les réponses préparées.', true);
    afficherCerveau();
  });
  parId('formulaire-limite-ia').addEventListener('submit', event => {
    event.preventDefault();
    try {
      const limite = limiteIA.definirMaximum(parId('limite-ia').value);
      erreurReglagesIA('');
      annoncer(`Limite enregistrée : ${limite} échanges par jour.`, true);
    } catch (erreur) {
      erreurReglagesIA(erreur.message);
    }
    afficherCerveau();
  });
  reglagesIA.addEventListener('close', () => {
    parId('cle-ia').value = '';
    parId('limite-ia').value = '';
    parId('plafond-ia').value = '';
    parId('texte-fiche-ia').value = '';
  });

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
    parId('rendez-vous').hidden = rendezVous.length === 0 && !agendaDisponible();
  }

  // La fiche d'un nouveau rendez-vous ne s'ouvre que sur ce bouton, jamais toute seule après une phrase dite.
  parId('nouveau-rdv').addEventListener('click', event => {
    const bouton = event.currentTarget;
    if (!agendaDisponible()) {
      annoncer('Connecte-toi à Google pour ajouter un rendez-vous.');
      return;
    }
    ficheRendezVous.nouveau({}, bouton, rendezVous => {
      erreurAgenda = '';
      remplirRendezVous(googleAgenda.lireCache() || []);
      afficherRecherche();
      annoncer(`Rendez-vous ajouté dans l'agenda Cap – FICTIF : ${rendezVous.titre}`);
    }, () => annoncer("Rendez-vous pas ajouté : rien n'a été mis dans l'agenda."));
  });

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
    void journalActions.envoyer();
  });
  window.addEventListener('cap-google-etat', afficherEtatGoogle);
  window.addEventListener('cap-google-etat', afficherSauvegarde);
  window.addEventListener('cap-google-deconnecte', afficherEtatGoogle);
  window.addEventListener('cap-google-deconnecte', afficherSauvegarde);
  window.addEventListener('cap-google-fusion', () => {
    listesChoix.recharger();
    afficher();
  });
  window.addEventListener('cap-listes-changees', () => {
    afficher();
    if (ajout.open && !parId('champs-tache').disabled) {
      remplirModeles();
      afficherCategorieChoisie();
    }
  });
  window.addEventListener('online', () => {
    void afficherRendezVous();
    void journalActions.envoyer();
  });
  afficherEtatGoogle();
  afficherSauvegarde();
  afficherCerveau();
  tenterReconnexionSilencieuse();
  if (googleConnexion.connecte()) {
    void synchronisation.demarrer().then(() => {
      afficher();
      void journalActions.envoyer();
      void sauvegardeDrive.verifierAutomatique().then(resultat => {
        if (resultat) annoncer(`Sauvegarde de la semaine faite : « ${resultat.nom} ».`, true);
      });
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
