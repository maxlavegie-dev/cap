(() => {
  'use strict';

  const parId = id => document.getElementById(id);
  const dateElement = parId('date');
  const heureElement = parId('heure');
  const listeElement = parId('liste-taches');
  const statutElement = parId('statut');
  const archiveElement = parId('basculer-archive');
  const listeArchiveElement = parId('liste-archive');
  const menu = parId('menu-tache');
  const confirmation = parId('confirmation');
  const ajout = parId('ajout-tache');
  const formulaire = parId('formulaire-ajout');
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
    if (!cible?.isConnected) cible = archiveElement;
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

  for (const dialogue of [menu, confirmation, ajout]) {
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
  function ajouterDictee(texte) {
    const intitule = texte.trim();
    if (!intitule) {
      annoncer("Je n'ai rien entendu, réessaie.");
      return;
    }
    let tache;
    try {
      tache = creerTache({
        intitule, categorie: 'À trier', sous_categorie: '', origine: 'dictée', fictif: false
      });
    } catch (erreur) {
      const message = erreur instanceof Error ? erreur.message : 'L’action n’a pas pu être enregistrée.';
      annoncer(`${message} Texte dicté à recopier : « ${intitule} »`);
      return;
    }
    afficher();
    annoncer(`Ajoutée dans À trier : « ${intitule} »`);
    const annuler = element('button', 'annuler-dictee', 'Annuler');
    annuler.type = 'button';
    annuler.addEventListener('click', () => {
      try {
        abandonner(tache.id);
      } catch (erreur) {
        signalerErreur(erreur);
        return;
      }
      afficher();
      if (document.activeElement === annuler) parId('microphone').focus({ preventScroll: true });
      annoncer('Tâche abandonnée : tu la retrouves dans les tâches abandonnées.');
    });
    statutElement.append(annuler);
    delaiStatut = setTimeout(() => {
      if (document.activeElement === annuler) parId('microphone').focus({ preventScroll: true });
      annuler.remove();
    }, 8000);
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
    const heureTexte = formatHeure.format(maintenant);
    if (dateElement.textContent !== dateTexte) {
      dateElement.textContent = dateTexte;
      const annee = maintenant.getFullYear();
      const mois = String(maintenant.getMonth() + 1).padStart(2, '0');
      const jour = String(maintenant.getDate()).padStart(2, '0');
      dateElement.dateTime = `${annee}-${mois}-${jour}`;
    }
    if (heureElement.textContent !== heureTexte) {
      heureElement.textContent = heureTexte;
      heureElement.dateTime = heureTexte;
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

  actualiserHorloge();
  setInterval(actualiserHorloge, 1000);
  try {
    const info = parId('info-chargement');
    info.textContent = INFO_CHARGEMENT;
    info.hidden = !INFO_CHARGEMENT;
    if (INFO_CHARGEMENT) annoncer(INFO_CHARGEMENT);
    afficher();
  } catch (erreur) {
    signalerErreur(erreur);
  }
})();
