(() => {
  'use strict';

  const parId = id => document.getElementById(id);
  const dateElement = parId('date');
  const listeElement = parId('liste-taches');
  const statutElement = parId('statut');
  const texteEntenduElement = parId('texte-entendu');
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

  // ----- 09/11/2026 (accord de Max, partie 2 A) : CHERCHER PARTOUT -----
  // « Tout » : tâches, rendez-vous et personnes de l'annuaire (ce que Cap peut déjà lire sur le téléphone, sans rien
  // envoyer et sans autorisation nouvelle). Chaque résultat dit ce qu'il est (Tâche, Rendez-vous, Personne) et mène
  // directement à lui. Les sources « (plus tard) » ne sont pas encore lues.
  function trouverPartout(texte, source) {
    const resultats = [];
    if (!String(texte || '').trim()) return resultats;
    if (source === 'tout' || source === 'taches') {
      for (const tache of recherche.chercherTaches(TACHES, texte)) resultats.push({ sorte: 'Tâche', libelle: tache.intitule, fait: tache.fait, ouvrir: () => ouvrirResultatTache(tache), tache });
    }
    if (source === 'tout' || source === 'rendez-vous') {
      for (const rdv of recherche.chercherRendezVous(googleAgenda.lireCache() || [], texte)) resultats.push({ sorte: 'Rendez-vous', libelle: texteRendezVous(rdv), ouvrir: origine => ouvrirResultatRendezVous(rdv, origine), rdv });
    }
    if ((source === 'tout' || source === 'personnes') && typeof annuaire !== 'undefined') {
      let personnes = [];
      try { personnes = annuaire.correspondances(texte); } catch (erreur) { personnes = []; }
      for (const p of personnes) resultats.push({ sorte: 'Personne', libelle: annuaire.nomAffichage(p), ouvrir: () => { if (typeof ficheContact !== 'undefined') ficheContact.ouvrirFiche(p); }, personne: p });
    }
    // 12/11/2026 (accord de Max, c151, A2) : les CARTES (carte_cap.js) : aujourd'hui les relations gardées sur le téléphone
    // (« Relation · Nom ») ; le toucher ouvre la carte. Les sources de la carte s'ajoutent dans carte_cap.js, pas ici.
    if ((source === 'tout' || source === 'personnes') && typeof carteCap !== 'undefined') {
      let cartes = [];
      try { cartes = carteCap.trouver(texte); } catch (erreur) { cartes = []; }
      for (const e of cartes) resultats.push({ sorte: e.sorte, libelle: e.titre, ouvrir: origine => carteCap.ouvrir(e, origine), carte: e });
    }
    return resultats;
  }
  const NOMS_SOURCES = { tout: 'partout', taches: 'Tâches', 'rendez-vous': 'Rendez-vous', personnes: 'Personnes' };

  function afficherRecherche() {
    parId('libelle-source').textContent = sourceRecherche.selectedOptions[0]?.textContent || '';
    const texte = saisieRecherche.value.trim();
    resultatsRecherche.replaceChildren();
    resultatsRecherche.hidden = true;
    if (!texte) return;
    // 09/11/2026 (partie 2 A) : « Tout » et « Personnes » passent par trouverPartout. Tâches et Rendez-vous : le code
    // d'avant, inchangé (ci-dessous).
    if (sourceRecherche.value === 'tout' || sourceRecherche.value === 'personnes') {
      const trouves = trouverPartout(texte, sourceRecherche.value);
      for (const r of trouves.slice(0, 30)) {
        const ligne = element('li');
        const bouton = element('button', 'resultat-recherche', r.libelle);
        bouton.type = 'button';
        bouton.prepend(element('span', 'sorte-resultat', `${r.sorte} · `));
        if (r.fait) bouton.append(element('span', 'etat-resultat', 'fait'));
        bouton.addEventListener('click', () => r.ouvrir(bouton));
        ligne.append(bouton);
        resultatsRecherche.append(ligne);
      }
      if (trouves.length > 30) resultatsRecherche.append(element('li', 'autres-resultats', `et ${trouves.length - 30} autres…`));
      if (!trouves.length) {
        const message = element('li', 'message-recherche', `Rien trouvé ${sourceRecherche.value === 'tout' ? 'nulle part' : 'dans Personnes'}`);
        message.setAttribute('role', 'status');
        resultatsRecherche.append(message);
      }
      resultatsRecherche.hidden = false;
      return;
    }
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

  // 09/11/2026 (partie 2 A) : la barre de Chercher : même menu, propositions dès la première lettre (6 au plus).
  const chercherSource = parId('chercher-source');
  const chercherChamp = parId('chercher-champ');
  const propositionsChercher = parId('propositions-chercher');
  if (chercherSource && chercherSource.options.length === 0) for (const o of sourceRecherche.options) chercherSource.append(o.cloneNode(true));
  // ----- 11/11/2026 (accord de Max, c135) : « Chantier » dans le menu de la recherche (index.html) et dans les propositions
  // de Chercher. Le choisir (menu) ou le toucher (proposition) ouvre l'écran des chantiers (chantiers_ecran.js écoute
  // « cap-ouvrir-chantiers », comme l'icône « Chantiers ») ; le menu revient aussitôt à son choix d'avant (on ne cherche
  // jamais « dans » les chantiers ici). Proposition : les lettres tapées se trouvent n'importe où dans « Chantier », sans
  // majuscules ni accents. La recherche elle-même (trouverPartout) n'est pas changée.
  const SOURCE_CHANTIERS = 'chantiers';
  const ouvrirLesChantiers = () => document.dispatchEvent(new CustomEvent('cap-ouvrir-chantiers'));
  const plierMot = x => String(x || '').normalize('NFD').replace(/\p{M}/gu, '').toLocaleLowerCase('fr-FR').trim();
  const choixAvant = new Map(); // menu → son dernier vrai choix
  function choixChantiers(menu) {
    if (!menu || menu.value !== SOURCE_CHANTIERS) { if (menu) choixAvant.set(menu, menu.value); return false; }
    menu.value = choixAvant.get(menu) || 'tout';
    ouvrirLesChantiers();
    return true;
  }
  for (const menu of [sourceRecherche, chercherSource]) if (menu) choixAvant.set(menu, menu.value);
  // 11/11/2026 (c136) : « valider » (touche Entrée) : la MÊME liste, mais jusqu'à 30 résultats, et « Rien trouvé » quand il
  // n'y a rien ; tout reste dans Chercher. Avant : 6 propositions seulement, Entrée partait vers l'écran des tâches.
  function proposerDansChercher(valider = false) {
    if (!chercherChamp || !propositionsChercher) return;
    const texte = chercherChamp.value.trim();
    const source = chercherSource ? chercherSource.value : 'tout';
    const maximum = valider === true ? 30 : 6;
    const tousTrouves = texte ? trouverPartout(texte, source) : [];
    const trouves = tousTrouves.slice(0, maximum);
    // c135 : « Chantier » en tête quand les lettres tapées sont dans le mot (6 propositions au plus, comme avant).
    if (texte && (source === 'tout') && plierMot('Chantier').includes(plierMot(texte))) {
      trouves.unshift({ sorte: 'Écran', libelle: 'Chantier', ouvrir: ouvrirLesChantiers });
      trouves.length = Math.min(trouves.length, maximum);
    }
    propositionsChercher.replaceChildren(...trouves.map(r => {
      const ligne = element('li');
      const bouton = element('button', 'proposition-chercher', r.libelle);
      bouton.type = 'button';
      bouton.prepend(element('span', 'sorte-resultat', `${r.sorte} · `));
      bouton.addEventListener('click', () => {
        propositionsChercher.replaceChildren();
        propositionsChercher.hidden = true;
        if (r.tache) {
          // Une tâche : l'écran des tâches (même chemin que Entrée, donc « Fermer » revient à Chercher), la tâche surlignée.
          // c136 : par « cap-chercher-vers-taches » (accueil_cap.js). Avant : la touche Entrée simulée (keydown Enter).
          chercherChamp.dispatchEvent(new CustomEvent('cap-chercher-vers-taches', { detail: r.tache.intitule, bubbles: true }));
          ouvrirResultatTache(r.tache);
        } else r.ouvrir(bouton); // un rendez-vous ou une personne : sa fiche, par-dessus Chercher
      });
      ligne.append(bouton);
      return ligne;
    }));
    if (valider === true && tousTrouves.length > maximum) propositionsChercher.append(element('li', 'proposition-chercher info-chercher', `et ${tousTrouves.length - maximum} autres…`));
    if (valider === true && texte && !trouves.length) {
      // Même allure que les propositions (lisible sur l'eau) ; pas un bouton.
      const message = element('li', 'proposition-chercher info-chercher', `Rien trouvé ${source === 'tout' ? 'nulle part' : `dans ${NOMS_SOURCES[source] || 'cette source'}`}`);
      message.setAttribute('role', 'status');
      propositionsChercher.append(message);
    }
    propositionsChercher.hidden = propositionsChercher.children.length === 0;
  }
  if (chercherChamp) chercherChamp.addEventListener('input', () => proposerDansChercher());
  if (chercherChamp) chercherChamp.addEventListener('cap-chercher-valider', () => proposerDansChercher(true)); // c136
  if (chercherSource) chercherSource.addEventListener('change', () => { if (choixChantiers(chercherSource)) return; if (sourceRecherche.querySelector(`option[value="${chercherSource.value}"]`)) sourceRecherche.value = chercherSource.value; proposerDansChercher(); });

  saisieRecherche.addEventListener('input', afficherRecherche);
  saisieRecherche.addEventListener('search', afficherRecherche);
  sourceRecherche.addEventListener('change', () => { if (choixChantiers(sourceRecherche)) return; afficherRecherche(); }); // c135 ; avant : addEventListener('change', afficherRecherche)
  saisieRecherche.addEventListener('keydown', event => {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    afficherRecherche();
    saisieRecherche.blur();
  });

  let dernierMessage = ''; // 09/11/2026 : pour la bulle du petit micro (sous-titres)
  function annoncer(message, temporaire = false) {
    clearTimeout(delaiStatut);
    dernierMessage = message;
    statutElement.textContent = message;
    if (temporaire) {
      delaiStatut = setTimeout(() => { statutElement.textContent = ''; }, 2600);
    }
  }

  let delaiTexteEntendu = null;

  // Affiche brièvement le texte exact compris par la dictée, pour preuve en cas de commande mal reconnue.
  function afficherTexteEntendu(texte) {
    if (!texteEntenduElement) return;
    clearTimeout(delaiTexteEntendu);
    const propre = texte.trim();
    texteEntenduElement.textContent = propre ? `Entendu : « ${propre} »` : '';
    if (propre) {
      delaiTexteEntendu = setTimeout(() => { texteEntenduElement.textContent = ''; }, 4000);
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
        // 09/11/2026 (mission C) : ouverte par l'icône « À trier » de Chercher : la plus récente EN HAUT (ordre d'ajout
        // inversé), seulement dans cette vue. Ailleurs, l'ordre ne change pas.
        if (vueActuelle.recentEnHaut) taches.reverse();
        for (const tache of taches) {
          liste.append(creerLigne(tache, Boolean(tache.parente)));
          if (vueActuelle.recentEnHaut && tache.id === vueActuelle.derniereId) liste.lastElementChild.classList.add('derniere-ajoutee'); // 09/11/2026 (mission C)
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
    // c173 (décision de Max) : dans une vue ouverte depuis une tuile, pas de « Fermer » : on sort en glissant (vers les tuiles).
    // Le bouton reste dans la page (caché) : la voix et le glissement depuis les tuiles s'en servent.
    parId('fermer-chercher').hidden = vueActuelle.type !== 'tuiles' && Boolean(vueActuelle.depuisTuiles);
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

  // 12/11/2026 (accord de Max, c173) : « depuisTuiles » : la vue a été ouverte en touchant une tuile de « Tout voir » : le
  // glissement vers le bas y RAMÈNE AUX TUILES (avant : il fermait tout, retour à l'accueil) et son « Fermer » est caché.
  function ouvrirVue(type, categorie = '', { depuisTuiles = false } = {}) {
    vueActuelle = { type, categorie, depuisTuiles };
    termineesOuvertes = false;
    afficher();
    const ecran = parId('ecran-complet');
    ecran.scrollTop = 0;
    const cible = type === 'tuiles' ? parId('tuiles').querySelector('.ouvrir-tuile') : parId('retour-tuiles');
    (cible || ecran).focus({ preventScroll: true });
  }

  // 09/11/2026 (accord de Max, mission C) : l'icône « À trier » de Chercher ouvre la liste « À trier », la dernière phrase
  // ajoutée en haut et surlignée (marque qui reste tant que la vue est ouverte, en plus de la surbrillance habituelle).
  document.addEventListener('cap-ouvrir-a-trier', () => {
    ouvrirVue('categorie', listesChoix.A_TRIER);
    const derniere = [...TACHES].reverse().find(t => !t.abandonnee_le && !t.fait && !t.parente && (t.categorie || '') === listesChoix.A_TRIER);
    vueActuelle.recentEnHaut = true;
    vueActuelle.derniereId = derniere ? derniere.id : null;
    afficher();
    if (!derniere) return;
    const ligne = Array.from(listeElement.querySelectorAll('[data-tache]')).find(n => n.dataset.tache === String(derniere.id));
    if (!ligne) return;
    surlignerResultat(ligne);
    parId('ecran-complet').scrollTop = 0;
  });

  function afficherTuiles() {
    const actives = racinesActives();
    const compte = new Map();
    for (const tache of actives) compte.set(tache.categorie || '', (compte.get(tache.categorie || '') || 0) + 1);
    const noms = listesChoix.categories();
    const autres = [...compte.keys()].filter(nom => !noms.some(item => item.toLocaleLowerCase('fr') === nom.toLocaleLowerCase('fr')));
    const aTrier = compte.get(listesChoix.A_TRIER) || 0;
    // 12/11/2026 (accord de Max, c172) : noms, ordre et contenu des tuiles fixes : tuiles_config.js (un seul endroit) ; ici,
    // seulement les CALCULS des compteurs. Avant : les tuiles écrites ici, titre et compteur en dur.
    const COMPTEURS_TUILES = {
      actions: () => journalActions.lire().length,
      'rendez-vous': () => (googleAgenda.lireCache() || []).length,
      aujourdhui: () => actives.filter(estPourAujourdhui).length + rendezVousDuJour().length,
      annuaire: () => annuaire.tous().length,
      'a-trier': () => aTrier,
      tout: () => actives.length
    };
    const depuisConfig = liste => liste.map(t => (t.compteur ? { id: t.id, titre: t.titre, compteur: COMPTEURS_TUILES[t.compteur]() } : { id: t.id, titre: t.titre }));
    tuiles.afficher(parId('tuiles'), {
      fixes: depuisConfig(TUILES_CONFIG.fixes),
      categories: [...noms, ...autres].map(nom => ({
        titre: nom || 'Sans catégorie', categorie: nom, compteur: compte.get(nom) || 0,
        couleur: nom ? listesChoix.couleur(nom) : '', deplacable: nom !== '' && noms.includes(nom) && nom !== listesChoix.A_TRIER
      })),
      finales: depuisConfig(TUILES_CONFIG.finales)
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

  // 12/11/2026 (c172) : ce que les tuiles fixes OUVRENT, par le nom donné dans tuiles_config.js (« ouvre ») ; « vue » (ou une
  // tuile hors du tableau) : la vue du même nom ; une catégorie : sa liste. Avant : une suite de « if » sur l'identifiant.
  const OUVERTURES_TUILES = {
    annuaire: () => ficheContact.ouvrirListe(),
    trier: () => modeTrier.ouvrir(parId('mode-trier'), { surChangement: afficher, gererCategories: fenetresListes.gererCategories }),
    'ajouter-categorie': () => fenetresListes.gererCategories({ action: 'ajouter' }),
    'modifier-categories': () => fenetresListes.gererCategories({ action: 'modifier' })
  };
  function ouvrirTuile(id, categorie) {
    const config = [...TUILES_CONFIG.fixes, ...TUILES_CONFIG.finales].find(t => t.id === id);
    if (config && OUVERTURES_TUILES[config.ouvre]) { OUVERTURES_TUILES[config.ouvre](); return; }
    if (categorie !== undefined) ouvrirVue('categorie', categorie, { depuisTuiles: true }); // c173
    else ouvrirVue(id, '', { depuisTuiles: true });
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
      afficherTexteEntendu(intitule);
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
    if (resultat.type === 'tache' || resultat.type === 'silence') return;
    const compris = { annuler: 'annuler la dernière action', report: 'reporter la tâche ouverte à demain',
      proposition: 'proposition faite à Max', rendez_vous_ajoute: 'rendez-vous inscrit après le oui de Max',
      vide: 'rien reçu', pas_compris: 'pas compris', attente_cerveau: 'demande pour plus tard',
      question: 'question posée à Max', reflexion: 'demande envoyée au cerveau', reponse: 'conversation',
      commande_annuaire: 'commande annuaire (fiche/appel/mail)' };
    journalActions.consigner({ source, entree: texte, compris: compris[resultat.type] || resultat.type,
      fait: resultat.message || ({ report: 'report demandé', annuler: 'annulation demandée' }[resultat.type] || 'rien') });
  }

  let reflexionsEnCours = 0;

  function afficherResultatDemande(resultat, origine) {
    if (origine && origine.id === 'microphone') signePourResultat(resultat); // 09/11/2026 (étape 4) : micro des commandes seulement
    if (resultat.type === 'silence') return;
    if (resultat.type === 'annuler') {
      annulerParLaParole(origine);
      return;
    }
    if (resultat.type === 'commande_annuaire') {
      commandeAnnuaireUI.traiter(resultat.detection);
      return;
    }
    if (resultat.type === 'reflexion') {
      annoncer(resultat.message);
      reflexionsEnCours += 1;
      resultat.suite.then(suite => afficherResultatDemande(suite, origine)).catch(erreur => signalerErreur(erreur))
        .finally(() => {
          reflexionsEnCours -= 1;
          afficherCerveau();
        });
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

  // 08/11/2026 (accord de Max, étape 0 des commandes vocales) : le MICRO DU MILIEU essaie d'abord les commandes
  // (code de Cap, sans IA, copie du tableur sur le téléphone). Commande reconnue : Cap la fait (ou dit qu'il ne sait pas
  // encore) et AUCUNE tâche n'est créée. Phrase qui commence comme une commande sans être complète : « Je ne suis pas
  // une IA, dis-moi ce que tu veux. » Sinon : chemin d'avant (tâche « À trier »…, choix B). Pas pendant une session de
  // fichier vocal (notes…). La conversation continue et le clavier gardent le chemin d'avant.
  function fenetreAffichee() {
    if (parId('lecteur-mp3-relations')?.open) return 'lecteur';
    // 08/11/2026 (étape 2a) : musique en arrière-plan = « le suivant » vise le morceau.
    try { if (typeof relationsMp3 !== 'undefined' && relationsMp3.instance && relationsMp3.instance.etat().actif) return 'lecteur'; } catch (erreur) { /* rien */ }
    if (parId('visionneuse-cap')?.open || parId('lecteur-pdf-relations')?.open || parId('vignettes-cap')?.open) return 'visionneuse'; // 08/11/2026 : + vignettes
    return '';
  }
  // 08/11/2026 (accord de Max) : pendant l'écoute, Android met la musique en pause (le service de reconnaissance
  // de Google prend le son). Filet de sécurité : si la musique jouait avant l'écoute et qu'elle est encore en pause
  // 1,5 s après la fin, Cap la relance (jamais si Max a demandé la pause). Aucune autorisation de plus.
  const REPRISE_MUSIQUE_MS = 1500;
  function musique() {
    try { return typeof relationsMp3 !== 'undefined' && relationsMp3.instance ? relationsMp3.instance : null; } catch (erreur) { return null; }
  }
  function musiqueJoue() {
    const m = musique();
    if (!m) return false;
    try { const e = m.etat(); return Boolean(e.actif && !e.enPause); } catch (erreur) { return false; }
  }
  function reprendreMusiqueSiCoupee(jouaitAvant) {
    if (!jouaitAvant) return;
    setTimeout(() => {
      const m = musique();
      if (!m) return;
      try { const e = m.etat(); if (e.actif && e.enPause && !e.pauseVoulue) m.reprendre(); } catch (erreur) { /* rien */ }
    }, REPRISE_MUSIQUE_MS);
  }

  // ----- 09/11/2026 (accord de Max, mission D) : FENÊTRE DE GROS CHOIX quand Cap hésite entre deux commandes ou plus -----
  // Une ligne par choix, avec son numéro. Toucher la case, ou dire seulement « un », « deux »… (le code lit le nombre :
  // aucune IA, aucun coût). « Aucun de ces choix » ferme sans rien faire. Pendant la fenêtre : ni pouce ni croix ; après
  // le choix : la commande, puis le pouce (ou la croix si elle n'a pas pu se faire). Rien n'est envoyé à personne.
  const fenetreChoixCommande = parId('choix-commande');
  const listeChoixCommande = parId('liste-choix-commande');
  let choixCommandeEnCours = null; // { phrase, options }
  const ouvrirChoixCommande = () => { if (typeof choixSurEau !== 'undefined') choixSurEau.ouvrir(fenetreChoixCommande); else if (!fenetreChoixCommande.open) fenetreChoixCommande.showModal(); };
  const fermerChoixCommande = () => { if (!fenetreChoixCommande.open) return; if (typeof choixSurEau !== 'undefined') choixSurEau.fermer(fenetreChoixCommande); else fenetreChoixCommande.close(); };
  // Après la fermeture (fondu compris) : le signe (il n'apparaît jamais tant que la fenêtre est là).
  const signeApresChoix = sorte => {
    if (!fenetreChoixCommande.open) { montrerSigne(sorte); return; }
    fenetreChoixCommande.addEventListener('close', () => montrerSigne(sorte), { once: true });
  };
  function montrerChoixCommande(decision, phrase) {
    if (!fenetreChoixCommande || !listeChoixCommande || !(decision.options || []).length) return false;
    choixCommandeEnCours = { phrase, options: decision.options.slice(0, 9) };
    preparerFenetreChoix('', 'Aucun de ces choix'); // 09/11/2026 : sans question ni champ (la fenêtre d'hésitation)
    listeChoixCommande.replaceChildren(...choixCommandeEnCours.options.map((option, i) => {
      const bouton = element('button', 'ligne-morceau ligne-choix-voix ligne-choix-commande');
      bouton.type = 'button';
      bouton.append(element('span', 'numero-morceau', String(i + 1)), element('span', 'nom-morceau', option.commande));
      bouton.addEventListener('click', () => choisirCommande(i));
      return bouton;
    }));
    ouvrirChoixCommande();
    return true;
  }
  function choisirCommande(i) {
    const choix = choixCommandeEnCours;
    if (!choix || !choix.options[i]) return;
    if (choix.surChoix) { choix.surChoix(i); return; } // 09/11/2026 : une étape de la machine « phrase à apprendre »
    choixCommandeEnCours = null;
    fermerChoixCommande();
    const option = choix.options[i];
    let fait = null;
    try { fait = commandesVocales.faireReconnu(option, { ouvert: fenetreAffichee() }); } catch (erreur) { fait = { statut: 'erreur', message: 'La commande n’a pas pu se faire.' }; }
    journalActions.consigner({ source: 'micro', entree: choix.phrase, compris: `choix de Max : ${option.code}`, fait: fait.message });
    noterPhraseEntendue(choix.phrase, `${fait.message} (choix ${i + 1})`);
    // 09/11/2026 (décision de Max, séance 2) : le choix est RETENU, daté (« choisie par Max le … »). Avant :
    // rangerPhraseApprise({ phrase: choix.phrase, code: option.code, commande: option.commande, origine: 'hesitation' }, { discret: true });
    retenirChoix(choix.phrase, option);
    annoncer(fait.message);
    if (fait.parler !== false) voix.dire(fait.message);
    const echec = fait.statut !== 'fait' || ECHEC_COMMANDE.test(fait.message);
    montrerBulle(fait.message, { erreur: echec });
    if (fait.suite) {
      Promise.resolve(fait.suite).then(texte => {
        if (!texte) return;
        annoncer(texte); voix.dire(texte); noterPhraseEntendue(choix.phrase, texte);
        montrerBulle(texte, { erreur: ECHEC_COMMANDE.test(texte) });
        signeApresChoix(ECHEC_COMMANDE.test(texte) ? 'croix' : 'pouce');
      }).catch(() => signeApresChoix('croix'));
    } else signeApresChoix(echec ? 'croix' : 'pouce');
  }
  // 09/11/2026 (séance 2) : retenir le choix de Max (fenêtre de gros choix). Même commande déjà apprise : elle est marquée
  // « choisie par Max le … ». Autre commande apprise (téléphone ou tableur de Cap) : l'ancienne est « remplacée le … » et
  // la nouvelle ajoutée, « choisie par Max ». Rien d'effacé. Corrigeable ensuite avec « Modifier ».
  function retenirChoix(phrase, option) {
    if (typeof phrasesApprendre === 'undefined' || !option || !option.code) return;
    const cle = phrasesApprendre.plier(phrase);
    try {
      const surTelephone = phrasesApprendre.lire(localStorage).find(e => phrasesApprendre.plier(e.phrase) === cle);
      if (surTelephone && (surTelephone.code || '') === option.code) {
        phrasesApprendre.marquerChoisie(localStorage, surTelephone.id);
        versPetitTableur(t => t.noterChoix(surTelephone.id));
        return;
      }
      const dansCap = destinationPhrases() ? destinationPhrases().copie().filter(l => !l.ecartee && l.id && phrasesApprendre.plier(l.phrase) === cle) : [];
      const memeCode = dansCap.find(l => l.code === option.code);
      if (!surTelephone && memeCode) { versPetitTableur(t => t.noterChoix(memeCode.id)); return; }
      const entree = { phrase, code: option.code, commande: option.commande, origine: 'hesitation', choisie: true };
      const g = surTelephone ? phrasesApprendre.garderNouvelle(localStorage, entree) : phrasesApprendre.ajouter(localStorage, entree);
      versPetitTableur(t => {
        for (const v of g.remplacees || []) t.noterRemplacement(v.id);
        for (const l of dansCap) if (l.code !== option.code && !(g.remplacees || []).some(v => v.id === l.id)) t.noterRemplacement(l.id);
        if (g.statut === 'ajoutee') t.noterAjout(g.entree);
      });
      majCompteApprendre();
    } catch (erreur) { montrerBulle('Le choix n’a pas pu être retenu (mémoire du téléphone pleine ?).', { erreur: true }); }
  }
  function aucunChoixCommande() {
    if (choixCommandeEnCours && choixCommandeEnCours.surAucun) { choixCommandeEnCours.surAucun(); return; } // 09/11/2026 : « Annuler » de la machine
    choixCommandeEnCours = null;
    fermerChoixCommande(); // ferme sans rien faire (ni commande, ni signe)
  }
  if (parId('aucun-choix-commande')) parId('aucun-choix-commande').addEventListener('click', aucunChoixCommande);
  if (fenetreChoixCommande) fenetreChoixCommande.addEventListener('close', () => { if (!fenetreChoixCommande.open) choixCommandeEnCours = null; });
  // À la voix, pendant la fenêtre : « un », « le deux », « numéro trois », « 2 »… ; « aucun » ferme. Autre phrase : la
  // fenêtre se ferme et la phrase suit son chemin habituel.
  const PETITS_MOTS_CHOIX = new Set(['le', 'la', 'l', 'numero', 'choix', 'case', 'c', 'est', 'ce', 'sera', 'prends', 'je', 'veux', 'plutot']);
  function reponseAuChoix(phrase) {
    if (!choixCommandeEnCours || !fenetreChoixCommande.open) return false;
    const mots = String(phrase).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, ' ').trim().split(' ').filter(Boolean);
    // 09/11/2026 (décision de Max, bloc c75) : L'ORDRE GAGNE. Un rang dit seul (« deux », « la deuxième ») choisit la case
    // à cette place, même si une autre case commence par ce nombre (« Deux … ») : celle-là se touche, ou se dit en entier.
    // 09/11/2026 (bloc c74, décision de Max) : le rang (« numéro 1 », « le premier », « la deuxième », « le 3e »…) par
    // numero_choix.js, le même pour toutes les fenêtres de choix. Le code d'avant reste en secours (fichier absent).
    if (typeof numeroChoix !== 'undefined') {
      const r = numeroChoix.rang(phrase);
      if (Number.isInteger(r) && r >= 1 && r <= choixCommandeEnCours.options.length) { choisirCommande(r - 1); return true; }
    }
    // 09/11/2026 (machine « phrase à apprendre ») : un mot d'une case (« oui », « redire », « changer »…) la choisit aussi.
    if (choixCommandeEnCours.surChoix && mots.length <= 3) {
      const premier = s => String(s).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, ' ').trim().split(' ')[0];
      const j = choixCommandeEnCours.options.findIndex(o => premier(o.texte) && premier(o.texte) === mots[0]);
      if (j >= 0) { choisirCommande(j); return true; }
    }
    if (mots.includes('aucun') || mots.includes('aucune')) { noterPhraseEntendue(phrase, 'Aucun de ces choix.'); aucunChoixCommande(); return true; }
    // 09/11/2026 (bloc c74) : le rang était essayé ici, APRÈS le mot de la case (déplacé plus haut, bloc c75).
    // 09/11/2026 (défaut 3) : ce que la reconnaissance écrit souvent pour un numéro dit seul (SEULEMENT dans cette fenêtre).
    const SONS_NUMEROS = { de: 'deux', deu: 'deux', eux: 'deux', d: 'deux', hein: 'un', in: 'un', trois: 'trois', toit: 'trois', quatres: 'quatre', sinq: 'cinq', sank: 'cinq' };
    let restes = mots.filter(m => !PETITS_MOTS_CHOIX.has(m) || (mots.length === 1 && SONS_NUMEROS[m])).map(m => SONS_NUMEROS[m] || m);
    if (restes.length > 1 && restes.every(m => m === restes[0])) restes = [restes[0]]; // « d'eux » → « deux », pas « deux deux »
    const reste = restes.join(' ');
    const n = reste ? commandesVocales.lireNombre(reste) : null;
    if (Number.isInteger(n) && n >= 1 && n <= choixCommandeEnCours.options.length) { choisirCommande(n - 1); return true; }
    aucunChoixCommande(); // une autre phrase : la fenêtre s'en va, la phrase suit son chemin
    return false;
  }

  // ----- 09/11/2026 (accord de Max) : MACHINE « PHRASE À APPRENDRE » -----
  // Le bouton rond (à gauche du petit micro) : Max redit la phrase refusée (ou reprend la dernière, gardée 2 minutes),
  // confirme (« Oui », « Redire », « Écrire »), choisit une commande proposée par le CODE (les plus proches en haut,
  // « Autres commandes » par famille, « Aucune ne convient »), confirme encore (« Oui », « Changer ») ; Cap range la
  // phrase dans la liste du téléphone : le pouce 3 s, le nombre monte. Toujours la fenêtre de gros choix numérotée
  // (toucher, ou « numéro deux », ou le mot de la case). Rien n'est écrit dans le tableur, rien n'est envoyé, rien à l'IA.
  const boutonApprendre = parId('bouton-apprendre');
  const compteApprendre = parId('compte-apprendre');
  const questionChoix = parId('question-choix-commande');
  const saisieApprendre = parId('saisie-apprendre');
  const boutonAucunChoix = parId('aucun-choix-commande');
  const DUREE_REFUSEE_MS = 2 * 60 * 1000;
  let derniereRefusee = null; // { phrase, quand } : la dernière phrase que Cap n'a pas comprise
  let apprendre = null; // { phrase, commande?, code? } pendant la machine
  let attenteEcouteApprendre = null;
  const listeApprendre = () => (typeof phrasesApprendre !== 'undefined' ? phrasesApprendre.lire(localStorage) : []);
  function noterRefusee(phrase) { if (phrase && phrase.trim()) derniereRefusee = { phrase: phrase.trim(), quand: Date.now() }; }
  function preparerFenetreChoix(question, bas, avecSaisie = false) {
    if (questionChoix) { questionChoix.textContent = question || ''; questionChoix.hidden = !question; }
    if (saisieApprendre) saisieApprendre.hidden = !avecSaisie;
    if (boutonAucunChoix) boutonAucunChoix.textContent = bas;
  }
  // Une étape : la question (courte) et des cases numérotées ; « Annuler » en bas ferme sans rien garder.
  function etapeApprendre(question, cases, { avecSaisie = false } = {}) {
    if (!fenetreChoixCommande || !listeChoixCommande) return;
    preparerFenetreChoix(question, 'Annuler', avecSaisie);
    listeChoixCommande.replaceChildren(...cases.map((c, i) => {
      const bouton = element('button', 'ligne-morceau ligne-choix-voix ligne-choix-commande');
      bouton.type = 'button';
      bouton.append(element('span', 'numero-morceau', String(i + 1)), element('span', 'nom-morceau', c.texte));
      bouton.addEventListener('click', () => choisirCommande(i));
      return bouton;
    }));
    choixCommandeEnCours = { phrase: apprendre ? apprendre.phrase : '', options: cases, surChoix: i => cases[i].faire(), surAucun: annulerApprendre };
    ouvrirChoixCommande();
  }
  function annulerApprendre() {
    clearTimeout(attenteEcouteApprendre); // une écoute prévue ne démarre plus
    if (apprendre && micro.getAttribute('aria-pressed') === 'true' && dictee.enCours()) dictee.arreter();
    apprendre = null;
    choixCommandeEnCours = null;
    preparerFenetreChoix('', 'Aucun de ces choix');
    fermerChoixCommande();
  }
  function majCompteApprendre() {
    const n = listeApprendre().length;
    if (compteApprendre) { compteApprendre.textContent = String(n); compteApprendre.hidden = n === 0; }
    if (boutonApprendre) boutonApprendre.setAttribute('aria-label', `Phrase à apprendre (${n} en attente)`);
    const ouvrir = parId('ouvrir-phrases-apprendre');
    if (ouvrir) ouvrir.textContent = `Phrases à apprendre (${n})`;
    afficherPhrasesApprendre();
  }
  // Écoute d'UNE phrase pour la machine (elle ne passe PAS par les commandes : rien n'est fait, rien n'est rangé).
  function ecouterPourApprendre(fin) {
    if (!dictee.disponible()) { montrerBulle("La dictée n'est pas disponible ici.", { erreur: true }); montrerSigne('croix'); return; }
    if (live.actif) arreterLive();
    if (dictee.enCours()) dictee.arreter();
    let recu = false;
    let provisoire = '';
    const finir = texte => { if (recu) return; recu = true; micro.setAttribute('aria-pressed', 'false'); fin(String(texte || '').trim()); };
    micro.setAttribute('aria-pressed', 'true');
    annoncer('Redis la phrase…');
    // 0,4 s d'attente : si Max a répondu à la voix, la reconnaissance précédente doit d'abord se terminer.
    clearTimeout(attenteEcouteApprendre);
    attenteEcouteApprendre = setTimeout(() => dictee.demarrer({
      surProvisoire(texte) { if (texte) provisoire = texte; },
      surFinal(texte) { finir(texte); },
      surErreur(code) { if (code !== 'aborted') finir(provisoire); },
      surFin() { finir(provisoire); }
    }), 400);
  }
  function demarrerApprendre() {
    if (apprendre) return;
    apprendre = { phrase: '' };
    const recente = derniereRefusee && Date.now() - derniereRefusee.quand <= DUREE_REFUSEE_MS ? derniereRefusee.phrase : '';
    if (recente) {
      apprendre.phrase = recente;
      // 09/11/2026 (décision de Max, après c72) : + « Écrire » (champ déjà rempli avec la phrase refusée), si Android a
      // mal entendu. Cette question EST la confirmation (pas de « J'ai compris » en plus). Avant : Oui, Redire seulement.
      etapeApprendre(`Reprendre « ${recente} » ?`, [
        { texte: 'Oui', faire: () => etapeCommandes() },
        { texte: 'Redire', faire: () => redireApprendre() },
        { texte: 'Écrire', faire: () => ecrireApprendre(recente) }
      ]);
    } else redireApprendre();
  }
  function redireApprendre() {
    etapeApprendre('Redis la phrase…', []); // la fenêtre dit ce qu'on attend ; « Annuler » reste possible
    ecouterPourApprendre(texte => {
      if (!apprendre) return;
      if (!texte) {
        montrerBulle("Je n'ai rien entendu.", { erreur: true });
        etapeApprendre('Je n’ai rien entendu.', [{ texte: 'Redire', faire: () => redireApprendre() }, { texte: 'Écrire', faire: () => ecrireApprendre('') }]);
        return;
      }
      apprendre.phrase = texte;
      confirmerPhrase();
    });
  }
  function confirmerPhrase() {
    etapeApprendre(`J’ai compris : « ${apprendre.phrase} »`, [
      { texte: 'Oui', faire: () => etapeCommandes() },
      { texte: 'Redire', faire: () => redireApprendre() },
      { texte: 'Écrire', faire: () => ecrireApprendre(apprendre.phrase) }
    ]);
  }
  function ecrireApprendre(texte) {
    etapeApprendre('Écris la phrase :', [
      { texte: 'Valider', faire: () => { const t = (saisieApprendre ? saisieApprendre.value : '').trim(); if (!t) return; apprendre.phrase = t; if (saisieApprendre) saisieApprendre.blur(); confirmerPhrase(); } },
      { texte: 'Redire', faire: () => redireApprendre() }
    ], { avecSaisie: true });
    if (saisieApprendre) { saisieApprendre.value = texte || ''; try { saisieApprendre.focus(); } catch (erreur) { /* rien */ } }
  }
  function etapeCommandes() {
    let proches = [];
    try { proches = commandesVocales.proches(apprendre.phrase, undefined, 5); } catch (erreur) { proches = []; }
    etapeApprendre(`« ${apprendre.phrase} » : quelle commande ?`, [
      ...proches.map(c => ({ texte: c.commande, faire: () => confirmerCommande(c.code, c.commande) })),
      { texte: 'Autres commandes', faire: () => etapeFamilles() },
      { texte: 'Aucune ne convient', faire: () => confirmerCommande('', 'Aucune ne convient') }
    ]);
  }
  function etapeFamilles() {
    let fs = [];
    try { fs = commandesVocales.familles(); } catch (erreur) { fs = []; }
    etapeApprendre('Quelle famille ?', [
      ...fs.map(f => ({ texte: f.nom, faire: () => etapeFamille(f, 0) })),
      { texte: 'Retour', faire: () => etapeCommandes() }
    ]);
  }
  function etapeFamille(f, debut) {
    const PAGE = 6;
    const montres = f.codes.slice(debut, debut + PAGE);
    etapeApprendre(`${f.nom} : quelle commande ?`, [
      ...montres.map(c => ({ texte: c.commande, faire: () => confirmerCommande(c.code, c.commande) })),
      ...(f.codes.length > debut + PAGE ? [{ texte: 'Suivantes', faire: () => etapeFamille(f, debut + PAGE) }] : []),
      { texte: 'Retour', faire: () => etapeFamilles() }
    ]);
  }
  function confirmerCommande(code, commande) {
    apprendre.code = code;
    apprendre.commande = commande;
    etapeApprendre(`« ${apprendre.phrase} » → ${code ? commande : 'aucune commande'} : c’est bien ça ?`, [
      // 09/11/2026 : + « Modifier » (Réglages) : la phrase reçoit la nouvelle commande (voir modifierPhraseApprise).
      { texte: 'Oui', faire: () => { const a = apprendre; if (a.modifier) { modifierPhraseApprise(a); return; } rangerPhraseApprise({ phrase: a.phrase, code: a.code, commande: a.commande, origine: 'bouton' }); } },
      { texte: 'Changer', faire: () => etapeCommandes() }
    ]);
  }
  // ----- 09/11/2026 (décision de Max, après c72) : « Modifier » dans Réglages > « Phrases à apprendre » -----
  // Change la COMMANDE d'une phrase sans la retirer : la phrase garde ses mots et son origine ; dans le tableur « Phrases
  // apprises », l'ancienne ligne est marquée « remplacée le … » et une ligne avec la nouvelle commande est ajoutée.
  // Rien n'est effacé.
  function modifierPhrase(entree) {
    if (apprendre || !entree) return;
    apprendre = { phrase: entree.phrase, modifier: entree };
    etapeCommandes();
  }
  function modifierPhraseApprise(a) {
    const ancienne = a.modifier;
    if ((ancienne.code || '') === (a.code || '')) { annulerApprendre(); montrerBulle('C’est déjà cette commande : rien n’a changé.', { erreur: true }); signeApresChoix('croix'); return; }
    const g = phrasesApprendre.garderNouvelle(localStorage, { phrase: ancienne.phrase, code: a.code, commande: a.commande, origine: ancienne.origine === 'hésitation' ? 'hesitation' : 'bouton' });
    versPetitTableur(t => { for (const v of g.remplacees || []) t.noterRemplacement(v.id); if (g.statut === 'ajoutee') t.noterAjout(g.entree, { etat: etatPrincipal(g.entree.phrase) }); });
    majCompteApprendre();
    annulerApprendre();
    montrerBulle(`Modifié : « ${ancienne.phrase} » → ${a.code ? a.commande : 'aucune commande'}.`);
    signeApresChoix('pouce');
  }

  // Range la phrase (bouton ou fenêtre d'hésitation) ; doublon : le dit ; autre commande : demande laquelle garder.
  // discret : depuis la fenêtre d'hésitation (Max vient d'agir) : pas de question, pas de pouce en plus.
  function rangerPhraseApprise(entree, { discret = false } = {}) {
    if (typeof phrasesApprendre === 'undefined') return;
    const r = phrasesApprendre.ajouter(localStorage, entree);
    if (r.statut === 'ajoutee') versPetitTableur(t => t.noterAjout(r.entree, { etat: etatPrincipal(r.entree.phrase) })); // 09/11/2026 (petit tableur)
    if (r.statut === 'ajoutee') {
      if (derniereRefusee && phrasesApprendre.plier(derniereRefusee.phrase) === phrasesApprendre.plier(entree.phrase)) derniereRefusee = null; // rangée : plus à reprendre
      majCompteApprendre();
      if (!discret) { annulerApprendre(); montrerBulle(`Noté : « ${entree.phrase} ».`); signeApresChoix('pouce'); }
      return;
    }
    if (r.statut === 'deja') {
      if (!discret) { annulerApprendre(); montrerBulle('Cette phrase est déjà dans la liste.', { erreur: true }); signeApresChoix('croix'); }
      return;
    }
    if (r.statut === 'conflit') {
      if (discret) { montrerBulle('Cette phrase est déjà dans la liste avec une autre commande : à revoir dans Réglages.', { erreur: true }); return; }
      const ancienne = r.existante.code ? r.existante.commande : 'aucune commande';
      const nouvelle = entree.code ? entree.commande : 'aucune commande';
      etapeApprendre(`Déjà notée avec « ${ancienne} ». Laquelle garder ?`, [
        { texte: ancienne, faire: () => { annulerApprendre(); montrerBulle('Gardée comme avant.'); signeApresChoix('pouce'); } },
        // 09/11/2026 (petit tableur) : l'ancienne ligne est marquée « remplacée le … », la nouvelle est ajoutée. Avant :
        // { texte: nouvelle, faire: () => { phrasesApprendre.garderNouvelle(localStorage, entree); majCompteApprendre(); …
        { texte: nouvelle, faire: () => { const g = phrasesApprendre.garderNouvelle(localStorage, entree);
          versPetitTableur(t => { for (const v of g.remplacees || []) t.noterRemplacement(v.id); if (g.statut === 'ajoutee') t.noterAjout(g.entree, { etat: etatPrincipal(g.entree.phrase) }); }); majCompteApprendre(); annulerApprendre(); montrerBulle(`Noté : « ${entree.phrase} ».`); signeApresChoix('pouce'); } }
      ]);
      return;
    }
    if (!discret) { annulerApprendre(); montrerBulle('La liste est pleine : retire des phrases dans Réglages.', { erreur: true }); signeApresChoix('croix'); }
  }
  // ----- 09/11/2026 (accord de Max) : le PETIT TABLEUR « Phrases apprises » (tableur_phrases.js). Chaque changement va
  // d'abord dans le tampon du téléphone, puis Cap essaie de l'écrire (sans bloquer Max ; s'il n'y arrive pas, ça attend).
  // 09/11/2026 (décision de Max, séance 2) : les changements vont maintenant dans « Commandes vocales (Cap) » (tableurCap,
  // même façon de faire). « Phrases apprises » n'est plus écrit (il reste intact). Avant : noter(tableurPhrases).
  const destinationPhrases = () => (typeof tableurCap !== 'undefined' ? tableurCap : null);
  function versPetitTableur(noter) {
    if (!destinationPhrases()) return;
    try { noter(destinationPhrases()); } catch (erreur) { montrerBulle('La phrase n’a pas pu être mise en attente (mémoire du téléphone pleine ?).', { erreur: true }); return; }
    envoyerPetitTableur();
  }
  // Le principal gagne : une phrase qu'il reconnaît déjà est écrite quand même, marquée « déjà dans le principal ».
  function etatPrincipal(phrase) {
    try { return typeof commandesVocales !== 'undefined' && commandesVocales.dejaDansPrincipal(phrase) ? 'déjà dans le principal' : ''; } catch (erreur) { return ''; }
  }
  // Écrit ce qui attend, puis (tout est écrit) relit le petit tableur pour en garder la copie sur le téléphone (étape 2).
  // 09/11/2026 (séance 2) : vers « Commandes vocales (Cap) ». Avant : tableurPhrases.envoyer() puis tableurPhrases.lireEtGarder().
  function envoyerPetitTableur() {
    const d = destinationPhrases();
    if (!d) return Promise.resolve(null);
    return d.envoyer()
      .then(async r => { if (r && r.attente === 0 && !r.raison) { try { await d.lireEtGarder(); } catch (erreur) { /* on relira plus tard */ } } return r; })
      .then(r => { majTamponTableur(); return r; }, () => { majTamponTableur(); return null; });
  }
  function majTamponTableur() {
    const n = destinationPhrases() ? destinationPhrases().enAttente() : 0; // 09/11/2026 (séance 2) : avant, tableurPhrases.enAttente()
    // « Ouvrir le tableur » : seulement quand Cap connaît le tableur (créé ou retrouvé au moins une fois).
    const lien = parId('ouvrir-tableur-phrases');
    const adresseTableur = typeof tableurPhrases === 'undefined' ? '' : tableurPhrases.adresse();
    if (lien) { lien.hidden = !adresseTableur; if (adresseTableur) lien.href = adresseTableur; else lien.removeAttribute('href'); }
    const etat = parId('tampon-phrases-apprendre');
    // 09/11/2026 (séance 2) : avant, « … écrites dans le tableur « Phrases apprises ». »
    if (etat) etat.textContent = n === 0 ? 'Toutes les phrases sont écrites dans le tableur « Commandes vocales (Cap) ».'
      : `${n} ${n > 1 ? 'changements attendent' : 'changement attend'} d’être écrit${n > 1 ? 's' : ''} dans le tableur (réseau ou connexion Google).`;
  }
  // ----- 09/11/2026 (décision de Max, séance 1) : le tableur « Commandes vocales (Cap) » du COMPTE CAP -----
  // À l'ouverture de Cap (compte Cap connecté) et en ouvrant « Phrases à apprendre » : Cap le retrouve, ou le crée vide
  // avec les titres du tableur « Commandes vocales ». Sans bloquer : en cas d'échec, Réglages le dit, rien d'autre.
  let etatTableurCap = '';
  function majTableurCap() {
    const etat = parId('etat-tableur-cap');
    const lien = parId('ouvrir-tableur-cap');
    const adresseCap = typeof tableurCap === 'undefined' ? '' : tableurCap.adresse();
    if (etat) etat.textContent = etatTableurCap;
    if (lien) { lien.hidden = !adresseCap; if (adresseCap) lien.href = adresseCap; else lien.removeAttribute('href'); }
  }
  function preparerTableurCap() {
    if (typeof tableurCap === 'undefined') return Promise.resolve(null);
    return tableurCap.trouverOuCreer().then(r => {
      if (r && r.raison === 'pas_connecte') etatTableurCap = 'Tableur « Commandes vocales (Cap) » : le compte Cap n’est pas connecté.';
      else if (r && r.id) etatTableurCap = r.cree ? 'Tableur « Commandes vocales (Cap) » créé dans le Drive du compte Cap.' : 'Tableur « Commandes vocales (Cap) » prêt.';
      majTableurCap();
      if (r && r.id) void reprendrePhrasesApprises().then(() => envoyerPetitTableur()); // 09/11/2026 (séance 2)
      return r;
    }, erreur => { etatTableurCap = `Tableur « Commandes vocales (Cap) » : ${erreur && erreur.message ? erreur.message : 'pas prêt.'}`; majTableurCap(); return null; });
  }
  // ----- 09/11/2026 (décision de Max, séance 2) : REPRISE de « Phrases apprises » dans « Commandes vocales (Cap) » -----
  // Une seule fois : chaque ligne du petit tableur (relu SANS y toucher) est recopiée, avec son identifiant, marquée
  // « reprise le … » (et son état d'origine). Les phrases du téléphone pas encore dans le petit tableur sont ajoutées.
  // Le petit tableur reste intact. Sans réseau : on réessaiera au prochain démarrage.
  const CLE_REPRISE_CAP = 'cap_tableur_cap_reprise_v1';
  async function reprendrePhrasesApprises() {
    if (typeof tableurCap === 'undefined' || typeof tableurPhrases === 'undefined' || typeof phrasesApprendre === 'undefined') return;
    try { if (localStorage.getItem(CLE_REPRISE_CAP)) return; } catch (erreur) { return; }
    let lu = false;
    try { lu = (await tableurPhrases.lireSansToucher()).lu; } catch (erreur) { lu = false; }
    let copieConnue = lu;
    try { copieConnue = lu || localStorage.getItem(tableurPhrases.CLE_COPIE) !== null || !localStorage.getItem(tableurPhrases.CLE_ID); } catch (erreur) { return; }
    if (!copieConnue) return; // le petit tableur existe mais n'a pas pu être lu : plus tard
    try {
      if (localStorage.getItem(CLE_REPRISE_CAP)) return;
      const copiePetit = tableurPhrases.copie();
      for (const l of copiePetit) tableurCap.noterReprise(l);
      const dejaLa = new Set(copiePetit.map(l => l.id));
      for (const e of phrasesApprendre.lire(localStorage).slice().reverse()) if (!dejaLa.has(e.id)) tableurCap.noterAjout(e);
      localStorage.setItem(CLE_REPRISE_CAP, new Date().toISOString());
    } catch (erreur) { /* mémoire pleine : plus tard */ }
  }
  void preparerTableurCap();

  // Reprise (une seule fois) : les phrases déjà sur le téléphone avant le petit tableur y sont écrites aussi.
  if (typeof tableurPhrases !== 'undefined' && typeof phrasesApprendre !== 'undefined') {
    try {
      // 09/11/2026 (séance 2) : plus de nouvelle écriture dans « Phrases apprises » (intact) : la reprise d'avant n'est
      // plus faite (la reprise vers « Commandes vocales (Cap) » la remplace). Avant : if (!localStorage.getItem('cap_phrases_tableur_reprise_v1')) {
      if (false && !localStorage.getItem('cap_phrases_tableur_reprise_v1')) {
        for (const e of phrasesApprendre.lire(localStorage).slice().reverse()) tableurPhrases.noterAjout(e);
        localStorage.setItem('cap_phrases_tableur_reprise_v1', new Date().toISOString());
      }
    } catch (erreur) { /* mémoire pleine : on réessaiera au prochain démarrage */ }
    window.addEventListener('online', () => { void envoyerPetitTableur(); });
    window.addEventListener('cap-google-etat', () => { if (destinationPhrases() && destinationPhrases().enAttente()) void envoyerPetitTableur(); }); // 09/11/2026 : avant, tableurPhrases.enAttente()
    void envoyerPetitTableur();
  }

  // ----- 09/11/2026 (décision de Max, bloc c74) : « mets la musique / la zik / la zic » sont maintenant compris par le CODE
  // (le lecteur s'allume avec la playlist par défaut). Une phrase apprise avant avec une autre commande (« Lancer un
  // morceau ») gênerait (à égalité, la phrase apprise gagne) : elle est passée à « Afficher le lecteur » comme avec
  // « Modifier » : l'ancienne ligne du petit tableur est marquée « remplacée le … », rien n'est effacé.
  function rangerPhrasesMusique() {
    if (typeof phrasesApprendre === 'undefined' || typeof tableurPhrases === 'undefined') return;
    const PHRASES_MUSIQUE = ['mets la musique', 'mets la zik', 'mets la zic'];
    const vise = phrase => PHRASES_MUSIQUE.includes(phrasesApprendre.plier(phrase));
    try {
      const liste = phrasesApprendre.lire(localStorage);
      for (const e of liste) {
        if (!vise(e.phrase) || e.code === 'MUS-19') continue;
        const g = phrasesApprendre.garderNouvelle(localStorage, { phrase: e.phrase, code: 'MUS-19', commande: 'Afficher le lecteur', origine: e.origine === 'hésitation' ? 'hesitation' : 'bouton' });
        versPetitTableur(tp => { for (const v of g.remplacees || []) tp.noterRemplacement(v.id); if (g.statut === 'ajoutee') tp.noterAjout(g.entree, { etat: etatPrincipal(g.entree.phrase) }); });
      }
      // Ligne venue d'un autre appareil (copie du petit tableur seulement) : marquée « remplacée » (une seule fois).
      const surTelephone = new Set(phrasesApprendre.lire(localStorage).map(e => e.id));
      // 09/11/2026 (séance 2) : le tampon du nouveau tableur. Avant : tableurPhrases.tampon()
      const enAttente = new Set((destinationPhrases() ? destinationPhrases().tampon() : []).filter(o => o.type === 'etat').map(o => o.id));
      for (const l of tableurPhrases.copie()) {
        if (!vise(l.phrase) || !l.code || l.code === 'MUS-19' || !l.id || surTelephone.has(l.id) || enAttente.has(l.id)) continue;
        if (/^(retir|rempla)/.test(phrasesApprendre.plier(l.etat))) continue;
        versPetitTableur(tp => tp.noterRemplacement(l.id));
      }
    } catch (erreur) { /* mémoire du téléphone : on réessaiera au prochain démarrage */ }
  }
  rangerPhrasesMusique();

  // Réglages > « Phrases à apprendre (N) » : la liste, « Retirer » par ligne, « Copier tout ».
  function afficherPhrasesApprendre() {
    const ul = parId('liste-phrases-apprendre');
    if (!ul) return;
    const liste = listeApprendre();
    ul.replaceChildren(...liste.map((e, rang) => {
      const li = element('li', 'ligne-phrase-apprendre');
      const d = new Date(e.quand);
      li.append(element('span', 'texte-phrase-apprendre', `« ${e.phrase} » → ${e.code ? e.commande : 'aucune commande'} · ${Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString('fr-FR')} · ${e.origine}`));
      const retirer = element('button', 'retirer-phrase-apprendre', 'Retirer');
      retirer.type = 'button';
      // 09/11/2026 (petit tableur) : la ligne du tableur est MARQUÉE « retirée le … », jamais effacée. Avant :
      // retirer.addEventListener('click', () => { phrasesApprendre.retirer(localStorage, rang); majCompteApprendre(); });
      retirer.addEventListener('click', () => {
        const partie = phrasesApprendre.retirerEntree(localStorage, rang);
        if (partie) versPetitTableur(t => t.noterRetrait(partie.id));
        majCompteApprendre();
      });
      // 09/11/2026 (décision de Max) : « Modifier » à côté de « Retirer » (changer la commande sans retirer la phrase).
      const modifier = element('button', 'modifier-phrase-apprendre', 'Modifier');
      modifier.type = 'button';
      modifier.addEventListener('click', () => modifierPhrase(e));
      li.append(modifier, retirer);
      return li;
    }));
    const vide = parId('vide-phrases-apprendre');
    if (vide) vide.hidden = liste.length > 0;
    const copier = parId('copier-phrases-apprendre');
    if (copier) copier.hidden = liste.length === 0;
  }
  if (boutonApprendre) boutonApprendre.addEventListener('click', demarrerApprendre);
  if (parId('ouvrir-phrases-apprendre')) parId('ouvrir-phrases-apprendre').addEventListener('click', event => {
    const contenu = parId('contenu-phrases-apprendre');
    contenu.hidden = !contenu.hidden;
    event.currentTarget.setAttribute('aria-expanded', String(!contenu.hidden));
    afficherPhrasesApprendre();
    majTamponTableur();
    if (!contenu.hidden) void envoyerPetitTableur(); // 09/11/2026 (petit tableur)
    if (!contenu.hidden) void preparerTableurCap(); // 09/11/2026 (séance 1, tableur du compte Cap)
  });
  if (parId('copier-phrases-apprendre')) parId('copier-phrases-apprendre').addEventListener('click', async () => {
    const etat = parId('etat-copie-apprendre');
    const texte = phrasesApprendre.texteACopier(listeApprendre());
    let ok = false;
    try { if (navigator.clipboard && navigator.clipboard.writeText) { await navigator.clipboard.writeText(texte); ok = true; } } catch (erreur) { ok = false; }
    if (!ok) {
      try { const zone = element('textarea'); zone.value = texte; document.body.append(zone); zone.select(); ok = document.execCommand('copy'); zone.remove(); } catch (erreur) { ok = false; }
    }
    if (etat) { etat.hidden = false; etat.textContent = ok ? 'Copié : colle-le toi-même dans le tableur « Commandes vocales ».' : 'La copie n’a pas marché.'; }
  });
  majCompteApprendre();

  // ----- 09/11/2026 (décision de Max, bloc c74) : RÉPONDRE PAR LE RANG dans les AUTRES fenêtres de choix -----
  // La fenêtre du dessus (celle qui porte le petit micro) a deux propositions ou plus : « numéro 2 », « la deuxième »…
  // touche la 2e proposition AFFICHÉE (même bouton que le doigt). « Annuler » / « Fermer » ne comptent pas. Une autre
  // phrase suit son chemin habituel. La fenêtre de gros choix des commandes a sa propre règle (reponseAuChoix).
  const PROPOSITIONS_CHOIX = {
    'choix-voix': '#liste-choix-voix button',
    'musique-relations': '#liste-musique-relations button',
    'chantiers-cap': '#liste-chantiers button', // 09/11/2026 (chantiers, séance 1)
    'journaux-relations': '#liste-journaux-relations button', // 10/11/2026 (c90) : « numéro 2 » touche la 2e relation
    'vignettes-cap': '#grille-vignettes .vignette',
    'question-date': '#choix-question-date button',
    'scanner-choix-emetteur': '#scanner-choix-emetteur-cases button',
    'commande-annuaire': '#commande-annuaire-corps button:not(.commande-annuaire-fermer)'
  };
  function reponseParRang(phrase) {
    if (typeof numeroChoix === 'undefined') return false;
    const micro = parId('petit-micro');
    const fenetre = micro && micro.closest('dialog[open]');
    if (!fenetre || !PROPOSITIONS_CHOIX[fenetre.id]) return false;
    const n = numeroChoix.rang(phrase);
    if (!Number.isInteger(n)) return false;
    // 11/11/2026 (c132) : la liste des chantiers filtrée par la recherche : le numéro vaut pour la liste COMPLÈTE.
    // Hors question en cours (mode confirmation), on passe par le choix de la liste complète.
    if (fenetre.id === 'chantiers-cap' && /\bnum[ée]ro\b|\bnum\b|\bno\b/i.test(phrase) && !fenetre.classList.contains('mode-confirmation') && typeof chantiersEcran !== 'undefined' && chantiersEcran.choisirRang && chantiersEcran.nombreChantiers) {
      const total = chantiersEcran.nombreChantiers();
      if (total >= 2) {
        if (n > total) {
          const texte = `Il n’y a que ${total} chantiers : dis un numéro de 1 à ${total}.`;
          noterPhraseEntendue(phrase, texte); annoncer(texte); montrerBulle(texte, { erreur: true }); montrerSigne('croix');
          return true;
        }
        if (chantiersEcran.choisirRang(n)) { noterPhraseEntendue(phrase, `Choix ${n}.`); montrerSigne('pouce'); return true; }
      }
    }
    // 11/11/2026 (c130) : fiche d'un chantier ouverte (écran à part) : la liste est cachée mais la voix y choisit toujours
    // (« le deuxième ») ; jamais pendant une question (mode confirmation).
    const listeCachee = fenetre.id === 'chantiers-cap' && fenetre.classList.contains('fiche-ouverte') && !fenetre.classList.contains('mode-confirmation');
    const cases = [...fenetre.querySelectorAll(PROPOSITIONS_CHOIX[fenetre.id])].filter(b => !b.disabled && !b.closest('[hidden]') && (listeCachee || b.getClientRects().length > 0));
    if (cases.length < 2) return false;
    noterPhraseEntendue(phrase, n <= cases.length ? `Choix ${n}.` : `Il n’y a que ${cases.length} choix.`);
    if (n > cases.length) {
      const texte = `Il n’y a que ${cases.length} choix : dis un numéro de 1 à ${cases.length}.`;
      annoncer(texte); montrerBulle(texte, { erreur: true }); montrerSigne('croix');
      return true;
    }
    cases[n - 1].click();
    montrerSigne('pouce');
    return true;
  }

  function essayerCommande(intitule) {
    if (typeof commandesVocales === 'undefined' || fichiersVocauxControleur.sessionActive()) return false;
    if (reponseAuChoix(intitule)) return true; // 09/11/2026 (mission D)
    if (reponseParRang(intitule)) return true; // 09/11/2026 (bloc c74)
    let decision = null;
    try { decision = commandesVocales.deciderMicro(intitule, { contexte: { ouvert: fenetreAffichee() } }); } catch (erreur) { return false; }
    if (!decision) return false;
    journalActions.consigner({ source: 'micro', entree: intitule, compris: decision.code ? `commande ${decision.code}` : 'commande incomplète', fait: decision.message });
    noterPhraseEntendue(intitule, decision.message); // 08/11/2026 (correction D)
    if (decision.statut === 'incomplet' || decision.statut === 'pas_encore') noterRefusee(intitule); // 09/11/2026 (phrase à apprendre)
    // 09/11/2026 (mission D) : hésitation = la fenêtre de gros choix s'ouvre AVANT le signe (donc ni pouce ni croix).
    if (decision.statut === 'ambigu') montrerChoixCommande(decision, intitule);
    annoncer(decision.message);
    // 09/11/2026 : pas comprise, hésitation, « pas encore » ou réponse qui dit que rien ne s'est passé = échec (toujours).
    montrerBulle(decision.message, { erreur: decision.statut !== 'fait' || ECHEC_COMMANDE.test(decision.message) });
    if (!decision.suite) montrerSigne(decision.statut !== 'fait' || ECHEC_COMMANDE.test(decision.message) ? 'croix' : 'pouce'); // 09/11/2026 (étape 4)
    if (decision.parler !== false) voix.dire(decision.message); // 08/11/2026 (étape 1) : avant, toujours dit
    // 08/11/2026 (étape 2b) : réponse qui arrive après une recherche (musique du compte Cap).
    if (decision.suite) Promise.resolve(decision.suite).then(texte => {
      if (!texte) return;
      annoncer(texte);
      voix.dire(texte);
      noterPhraseEntendue(intitule, texte);
      montrerBulle(texte, { erreur: ECHEC_COMMANDE.test(texte) }); // 09/11/2026
      montrerSigne(ECHEC_COMMANDE.test(texte) ? 'croix' : 'pouce'); // 09/11/2026 (étape 4)
    }).catch(erreur => { annoncer(erreur instanceof Error ? erreur.message : 'La commande n’a pas pu se faire.'); montrerSigne('croix'); }); // 09/11/2026 : + croix
    return true;
  }

  // 08/11/2026 (correction D, accord de Max) : les 10 dernières phrases du micro du milieu et la réponse de Cap,
  // sur le téléphone seulement, affichées dans « Réglages du Drive » pour les essais.
  function noterPhraseEntendue(phrase, reponse) {
    if (typeof commandesVocales === 'undefined') return;
    try { commandesVocales.noterEntendue(localStorage, phrase, reponse); } catch (erreur) { /* rien */ }
    afficherPhrasesEntendues();
  }
  function afficherPhrasesEntendues() {
    const liste = parId('liste-phrases-entendues');
    if (!liste || typeof commandesVocales === 'undefined') return;
    let entendues = [];
    try { entendues = commandesVocales.entendues(localStorage); } catch (erreur) { entendues = []; }
    liste.replaceChildren(...entendues.map(e => {
      const ligne = element('li');
      const heure = new Date(e.quand);
      ligne.textContent = `${Number.isNaN(heure.getTime()) ? '' : heure.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) + ' — '}« ${e.phrase} » → ${e.reponse}`;
      return ligne;
    }));
    parId('vide-phrases-entendues').hidden = entendues.length > 0;
  }

  // 11/11/2026 (accord de Max, c107) : témoin du micro dans la fiche d'un chantier (chantiers_ecran.js) : « Entendu … » ou
  // « Rien entendu ». Fiche fermée : rien. Une panne du témoin ne gêne jamais la dictée.
  function temoinMicroChantier(texte) {
    try { if (typeof chantiersEcran !== 'undefined' && typeof chantiersEcran.temoinMicro === 'function') chantiersEcran.temoinMicro(texte); } catch (erreur) { /* rien */ }
  }
  // Le témoin est posé AVANT (visible même si la suite échoue) et APRÈS (la phrase a pu ouvrir ou changer la fiche).
  function ajouterDictee(texte, options = {}) {
    const intitule = String(texte || '').trim();
    temoinMicroChantier(intitule);
    try { return ajouterDicteeSansTemoin(texte, options); } finally { temoinMicroChantier(intitule); }
  }
  function ajouterDicteeSansTemoin(texte, { commandes = false } = {}) {
    const intitule = texte.trim();
    afficherTexteEntendu(intitule);
    // 10/11/2026 (accord de Max, c104) : une note de chantier est ATTENDUE (« ajoute au journal » dit seul) : la phrase va
    // d'abord là (même « annuler », qui arrête l'attente), avant les fenêtres de confirmation.
    if (intitule && typeof chantiersEcran !== 'undefined' && typeof chantiersEcran.noteEnAttente === 'function' && chantiersEcran.noteEnAttente()) {
      const r = chantiersEcran.noteParLaVoix(intitule);
      if (r && r.message) {
        noterPhraseEntendue(intitule, r.message);
        annoncer(r.message);
        montrerBulle(r.message, { erreur: r.echec });
        montrerSigne(r.echec ? 'croix' : 'pouce');
        return;
      }
    }
    // 10/11/2026 (accord de Max, c87) : « oui », « non », « annuler » répondent d'abord à une fenêtre de confirmation
    // ouverte (confirmations_fenetres.js, phrase entière seulement ; doute : rien n'est fait) ; dits SEULS sans rien à
    // confirmer, ils ne sont plus rangés dans « À trier ». Avant : ils devenaient une tâche.
    if (intitule && typeof confirmationsFenetres !== 'undefined') {
      const r = confirmationsFenetres.repondreVoix(document, intitule);
      const iaEnAttente = typeof cerveau !== 'undefined' && Boolean((cerveau.propositionEnAttente && cerveau.propositionEnAttente()) || (cerveau.questionEnAttente && cerveau.questionEnAttente()));
      const message = r ? r.message : (confirmationsFenetres.rienAConfirmer(document, intitule, { iaEnAttente }) ? 'Il n’y a rien à confirmer en ce moment.' : '');
      if (message) {
        const echec = !r || r.resultat === 'doute' || r.resultat === 'refus';
        noterPhraseEntendue(intitule, message);
        annoncer(message);
        montrerBulle(message, { erreur: echec });
        montrerSigne(echec ? 'croix' : 'pouce');
        return;
      }
    }
    // 10/11/2026 (accord de Max, c95) : « ajoute au journal, … » dans la fiche d'un chantier qui a un dossier (chantiers_ecran.js) :
    // le texte va dans le champ de note et la question s'affiche (rien n'est écrit sans le Oui) ; sinon la phrase continue.
    if (intitule && typeof chantiersEcran !== 'undefined' && typeof chantiersEcran.noteParLaVoix === 'function') {
      const r = chantiersEcran.noteParLaVoix(intitule);
      if (r && r.message) {
        noterPhraseEntendue(intitule, r.message);
        annoncer(r.message);
        montrerBulle(r.message, { erreur: r.echec });
        montrerSigne(r.echec ? 'croix' : 'pouce');
        return;
      }
    }
    if (commandes && intitule && essayerCommande(intitule)) return; // 08/11/2026 (étape 0)
    if (commandes && intitule) noterRefusee(intitule); // 09/11/2026 : pas une commande : peut être une phrase à apprendre
    try {
      const resultat = journalActions.pendant({ source: 'micro', entree: intitule, compris: 'noter une tâche dans À trier' },
        () => traiterDemande({ texte: intitule, source: 'micro', agenda_disponible: agendaDisponible() }));
      if (commandes) noterPhraseEntendue(intitule, resultat.message || (resultat.type === 'tache' ? 'tâche notée' : resultat.type)); // 08/11/2026 (correction D)
      noterDemande('micro', intitule, resultat);
      afficherResultatDemande(resultat, parId('microphone'));
      if (commandes) montrerBulle(dernierMessage); // 09/11/2026 : ce que Cap vient d'écrire en bas (sous-titres seulement)
    } catch (erreur) {
      const message = erreur instanceof Error ? erreur.message : 'L’action n’a pas pu être enregistrée.';
      if (commandes) montrerSigne('croix'); // 09/11/2026 (étape 4)
      annoncer(`${message} Texte dicté à recopier : « ${intitule} »`);
    }
  }

  // Mode conversation (« live ») : un appui long de 2 secondes sur le micro. Cap écoute, répond, puis réécoute tout seul.
  // Il s'arrête sur un appui sur le micro, sur « Arrêter », sur « stop », après une minute de silence, ou si la limite du jour est atteinte.
  const APPUI_LONG_MS = 2000;
  const SILENCE_LIVE_MS = 60 * 1000;
  // Après « bloc-notes, note » (ou brouillon vocal), Cap attend en silence. Si Max ne dit rien
  // pendant ce délai, Cap arrête d'écouter et enregistre ce qui a déjà été dicté, sans rien effacer ;
  // s'il n'avait encore rien dit, aucune entrée vide n'est créée. Délai réglable ici.
  const SILENCE_NOTE_MS = 40 * 1000;
  const live = { actif: false, dernierSon: 0, verrou: null, attente: null };
  let minuteurAppui = null;
  let appuiLong = false;

  function bip(aigu) {
    try {
      const Contexte = window.AudioContext || window.webkitAudioContext;
      if (!Contexte) return;
      const contexte = new Contexte();
      const oscillateur = contexte.createOscillator();
      const volume = contexte.createGain();
      oscillateur.frequency.value = aigu ? 880 : 520;
      volume.gain.value = 0.15;
      oscillateur.connect(volume);
      volume.connect(contexte.destination);
      oscillateur.start();
      oscillateur.stop(contexte.currentTime + 0.15);
      oscillateur.onended = () => contexte.close();
    } catch (erreur) {
      return;
    }
  }

  function limiteLiveAtteinte() {
    return cerveau.fournisseurActif() !== 'prepare' && !limiteIA.peutEchanger();
  }

  function demarrerLive() {
    if (live.actif) return;
    if (!dictee.disponible()) {
      annoncer("La dictée n'est pas disponible dans ce navigateur.");
      return;
    }
    if (limiteLiveAtteinte()) {
      annoncer(limiteIA.raisonArret() || 'J’ai atteint ma limite pour aujourd’hui.');
      return;
    }
    Object.assign(live, { actif: true, dernierSon: Date.now() });
    // 08/11/2026 (décision de Max) : bandeau « Arrêter » retiré : « continu » suffit (un toucher lance, un autre arrête),
    // et le micro de l'accueil porte un léger halo. Code gardé : remettre BANDEAU_LIVE à true pour le rétablir.
    if (BANDEAU_LIVE) parId('bandeau-live').hidden = false;
    parId('microphone').classList.add('live');
    parId('microphone').setAttribute('aria-label', 'Arrêter le mode conversation');
    majContinu(); // 08/11/2026 (étape 3)
    bip(true);
    navigator.wakeLock?.request?.('screen').then(verrou => {
      if (live.actif) live.verrou = verrou;
      else verrou.release();
    }).catch(() => {});
    // 08/11/2026 (accord de Max) : la musique se met en pause pendant la conversation : Cap le dit une fois.
    live.musiqueAvant = musiqueJoue();
    annoncer('Mode conversation : parle quand tu veux, je réponds à chaque pause.'
      + (live.musiqueAvant ? ' La musique est en pause pendant la conversation, elle reprendra à l’arrêt.' : ''));
    ecouterLive();
  }

  // 08/11/2026 (accord de Max, étape 3) : bouton « continu » de l'écran Micro : il lance ou arrête la conversation
  // continue (même code que l'appui long du micro, qui ne la lance plus). État actif très visible (aria-pressed).
  const BANDEAU_LIVE = false; // 08/11/2026 : bandeau « Arrêter » désactivé (voir demarrerLive)
  function majContinu() {
    // 09/11/2026 : le gros micro de l'accueil porte l'état de la conversation (surbrillance par le style « live »).
    micro.setAttribute('aria-label', live.actif ? 'Arrêter la conversation continue' : (micro.getAttribute('aria-pressed') === 'true' ? 'Arrêter la dictée' : 'Dicter une tâche'));
    // 08/11/2026 (accord de Max) : léger halo fixe sur le micro de l'accueil pendant la conversation.
    const accueil = parId('ouvrir-micro');
    if (accueil) {
      accueil.classList.toggle('conversation-en-cours', live.actif);
      accueil.setAttribute('aria-label', live.actif ? 'Micro (conversation en cours)' : 'Micro');
    }
    const bouton = parId('micro-continu');
    if (!bouton) return;
    bouton.setAttribute('aria-pressed', String(live.actif));
    bouton.setAttribute('aria-label', live.actif ? 'Arrêter la conversation continue' : 'Conversation continue');
  }

  function arreterLive(message = 'Mode conversation arrêté.') {
    if (!live.actif) return;
    live.actif = false;
    reprendreMusiqueSiCoupee(live.musiqueAvant); // 08/11/2026 : la musique reprend à l'arrêt
    live.musiqueAvant = false;
    clearTimeout(live.attente);
    live.verrou?.release?.().catch?.(() => {});
    live.verrou = null;
    parId('bandeau-live').hidden = true;
    parId('microphone').classList.remove('live');
    parId('microphone').setAttribute('aria-label', 'Dicter une tâche');
    majContinu(); // 08/11/2026 (étape 3)
    if (dictee.enCours()) dictee.arreter();
    bip(false);
    annoncer(message);
  }

  // Attend que Cap ait fini de réfléchir et de parler avant de réécouter (pour ne pas s'écouter lui-même).
  function relancerLive() {
    clearTimeout(live.attente);
    if (!live.actif) return;
    if (Date.now() - live.dernierSon > SILENCE_LIVE_MS) {
      arreterLive('Mode conversation arrêté après une minute de silence.');
      return;
    }
    if (limiteLiveAtteinte()) {
      arreterLive(`${limiteIA.raisonArret() || 'J’ai atteint ma limite pour aujourd’hui.'} Mode conversation arrêté.`);
      return;
    }
    if (reflexionsEnCours > 0 || voix.parle() || dictee.enCours()) {
      live.attente = setTimeout(relancerLive, 300);
      return;
    }
    ecouterLive();
  }

  function ecouterLive() {
    if (!live.actif) return;
    let entendu = '';
    dictee.demarrer({
      surProvisoire(texte) {
        if (texte) annoncer(texte);
      },
      surFinal(texte) {
        if (!entendu) entendu = texte.trim();
      },
      surErreur(code) {
        if (['not-allowed', 'service-not-allowed', 'audio-capture'].includes(code)) {
          arreterLive('Le micro est bloqué ou introuvable : mode conversation arrêté.');
        }
      },
      surFin() {
        if (!live.actif) return;
        if (entendu) {
          live.dernierSon = Date.now();
          if (!fichiersVocauxControleur.sessionActive()
            && /^(?:stop|stoppe|arrete|arrete toi|fin|termine|c est fini|au revoir)(?: (?:le mode|la conversation|cap|merci))*$/.test(cerveau.texte.plier(entendu).replace(/ +/g, ' ').trim())) {
            arreterLive('Mode conversation arrêté. À plus tard, Max.');
            return;
          }
          ajouterDictee(entendu);
        }
        live.attente = setTimeout(relancerLive, 300);
      }
    });
  }

  const micro = parId('microphone');
  micro.addEventListener('contextmenu', event => event.preventDefault());
  // ----- 09/11/2026 (accord de Max, étape 2) : GROS MICRO de l'accueil, « + » et nouvelle icône -----
  // Premier toucher : il n'écoute pas, il fait apparaître « + » (à gauche) et la nouvelle icône (à droite). Ensuite, un
  // toucher = une phrase (deux touchers rapides marchent donc d'eux-mêmes). Déjà en écoute : le toucher garde son effet
  // (arrêter). Ils restent jusqu'à ce que Max touche l'un d'eux ou quitte l'accueil : aucune minuterie.
  const outilsMicro = ['micro-ajouter', 'micro-ecrire'].map(id => parId(id)).filter(Boolean);
  const outilsVisibles = () => outilsMicro.length > 0 && outilsMicro.every(b => !b.hidden);
  function montrerOutilsMicro(oui) {
    for (const b of outilsMicro) {
      if (b.hidden === !oui) continue;
      b.hidden = !oui;
      b.classList.toggle('outil-apparait', oui);
    }
  }
  micro.addEventListener('click', event => {
    if (!outilsMicro.length || appuiLong || !micro.closest('#accueil-boutons') || outilsVisibles()) return;
    montrerOutilsMicro(true);
    if (micro.getAttribute('aria-pressed') === 'true' || live.actif) return; // déjà en écoute : ce toucher l'arrête
    event.stopImmediatePropagation(); // premier toucher : rien d'autre
  }, true);
  for (const b of outilsMicro) b.addEventListener('click', () => montrerOutilsMicro(false));
  // Quitter l'accueil (Chercher, Autre, Réglages, tâches, eau) : ils s'en vont.
  const surAccueil = () => !document.documentElement.classList.contains('ecran-cap-ouvert')
    && !document.body.classList.contains('vue-complete') && !document.documentElement.classList.contains('eau-ouverte');
  if (typeof MutationObserver !== 'undefined') {
    const suivre = () => { if (!surAccueil()) montrerOutilsMicro(false); };
    new MutationObserver(suivre).observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    new MutationObserver(suivre).observe(document.body, { attributes: true, attributeFilter: ['class'] });
  }
  // « le micro » à la voix (NAV-22) : les fait apparaître, sans écouter.
  document.addEventListener('cap-montrer-outils-micro', () => montrerOutilsMicro(true));
  // 08/11/2026 (accord de Max, étape 3) : l'appui long du micro ne lance plus la conversation : c'est le bouton
  // « continu » de l'écran Micro. Code gardé ; remettre true pour le rétablir.
  // 09/11/2026 (accord de Max, étape 2) : l'appui long du GROS MICRO de l'accueil relance la conversation (surbrillance) ;
  // « continu » est caché. Avant : false.
  const APPUI_LONG_CONVERSATION = true;
  micro.addEventListener('pointerdown', () => {
    appuiLong = false;
    clearTimeout(minuteurAppui);
    if (!APPUI_LONG_CONVERSATION) return;
    if (live.actif || dictee.enCours()) return;
    minuteurAppui = setTimeout(() => {
      appuiLong = true;
      montrerOutilsMicro(true); // 09/11/2026 : « + » et l'icône apparaissent en même temps
      demarrerLive();
    }, APPUI_LONG_MS);
  });
  ['pointerup', 'pointerleave', 'pointercancel'].forEach(nom => micro.addEventListener(nom, () => clearTimeout(minuteurAppui)));
  parId('arreter-live').addEventListener('click', () => arreterLive());
  // 08/11/2026 (accord de Max, étape 3b) : petit micro de la VISIONNEUSE (elle couvre l'écran Micro).
  // Appui simple : une phrase (le même chemin que le micro du milieu : commandes d'abord, sinon « À trier »).
  // Appui long (2 s) : conversation continue, bouton en surbrillance ; un toucher l'arrête.
  // 08/11/2026 (accord de Max) : même petit micro sur l'écran des vignettes : le bloc ci-dessous (écrit pour la
  // visionneuse) devient une fonction, branchée sur les deux boutons. Avant : const microVision = parId('micro-visionneuse');
  // if (microVision) { … } (même contenu).
  function brancherPetitMicro(microVision) {
    if (!microVision) return;
    let appuiLongVision = false;
    let minuteurVision = null;
    microVision.addEventListener('contextmenu', event => event.preventDefault());
    microVision.addEventListener('pointerdown', () => {
      appuiLongVision = false;
      clearTimeout(minuteurVision);
      if (live.actif || dictee.enCours()) return;
      minuteurVision = setTimeout(() => { appuiLongVision = true; demarrerLive(); }, APPUI_LONG_MS);
    });
    ['pointerup', 'pointerleave', 'pointercancel'].forEach(nom => microVision.addEventListener(nom, () => clearTimeout(minuteurVision)));
    microVision.addEventListener('click', () => {
      if (appuiLongVision) { appuiLongVision = false; return; }
      if (live.actif) { arreterLive(); return; }
      if (dictee.enCours()) { dictee.arreter(); return; }
      if (!dictee.disponible()) { annoncer("La dictée n'est pas disponible dans ce navigateur."); montrerBulle("La dictée n'est pas disponible ici.", { erreur: true }); montrerSigne('croix'); return; } // 09/11/2026 : + bulle, + croix
      ecouterDemandeMicro();
    });
    // L'état suit le micro du milieu : écoute d'une phrase (« en-ecoute »), conversation (surbrillance, aria-pressed).
    const suivreMicro = () => {
      microVision.classList.toggle('en-ecoute', micro.getAttribute('aria-pressed') === 'true' && !live.actif);
      microVision.setAttribute('aria-pressed', String(live.actif));
    };
    if (typeof MutationObserver !== 'undefined') new MutationObserver(suivreMicro).observe(micro, { attributes: true, attributeFilter: ['aria-pressed', 'class'] });
  }
  brancherPetitMicro(parId('micro-visionneuse'));
  brancherPetitMicro(parId('micro-vignettes')); // 08/11/2026
  brancherPetitMicro(parId('petit-micro')); // 09/11/2026 : le petit micro de tous les écrans (mêmes règles)
  brancherPetitMicro(parId('micro-depart-visionneuse')); // 12/11/2026 (c161) : sous « Oui » et « Non » de « ↺ »
  // 08/11/2026 (accord de Max, étape 1 des commandes vocales) : dictée dite au micro du milieu.
  // DIC-02 « arrête », « stop »… : arrête la dictée (et la conversation continue si elle tourne).
  // DIC-01 « lance la dictée »… : Cap réécoute tout de suite, sans parler (sinon le micro entendrait sa voix).
  if (typeof commandesVocales !== 'undefined') {
    commandesVocales.brancherAction('DIC-02', () => {
      if (live.actif) arreterLive('Dictée arrêtée.');
      else if (dictee.enCours()) dictee.arreter();
      return 'Dictée arrêtée.';
    });
    commandesVocales.brancherAction('DIC-01', () => {
      setTimeout(() => { if (!dictee.enCours() && !live.actif) ecouterDemandeMicro(); }, 400);
      return { message: 'Je t’écoute.', parler: false };
    });
  }
  const boutonContinu = parId('micro-continu'); // 08/11/2026 (étape 3)
  if (boutonContinu) boutonContinu.addEventListener('click', () => {
    if (live.actif) { arreterLive(); return; }
    if (dictee.enCours()) dictee.arreter(); // une dictée simple en cours laisse la place à la conversation
    demarrerLive();
  });
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') arreterLive();
  });

  micro.addEventListener('click', () => {
    if (appuiLong) {
      appuiLong = false;
      return;
    }
    if (live.actif) {
      arreterLive();
      return;
    }
    if (dictee.enCours()) {
      dictee.arreter();
      return;
    }
    if (!dictee.disponible()) {
      annoncer("La dictée n'est pas disponible dans ce navigateur. Utilise le bouton +.");
      return;
    }
    ecouterDemandeMicro();
  });

  // Horodatage du dernier mot entendu pendant une dictée libre (bloc-notes, brouillon vocal) en cours ;
  // sert à mesurer le silence sans jamais effacer ce qui a déjà été dicté.
  let dernierSonNote = 0;

  // Ferme la session de dictée libre après un silence, sans rien effacer : enregistre ce qui a déjà
  // été dicté, ou ne crée aucune entrée si rien n'avait encore été dit (fermerSession gère les deux cas).
  function fermerSessionNotePourSilence() {
    const resultat = { type: 'reflexion', message: '', suite: fichiersVocauxControleur.fermerSession() };
    noterDemande('micro', '', resultat);
    afficherResultatDemande(resultat, micro);
  }

  // Une écoute du micro (appui simple). Si une dictée libre (bloc-notes, brouillon vocal) vient de
  // s'ouvrir, Cap réécoute tout seul sans que Max ait besoin de retoucher le micro, jusqu'à « terminé »
  // ou jusqu'à SILENCE_NOTE_MS de silence.
  // ----- 09/11/2026 (accord de Max) : BULLE sous le petit micro et interrupteur « Sous-titres » -----
  // Erreurs et échecs du micro (rien entendu, micro bloqué, phrase pas comprise, « pas encore prêt »…) : toujours.
  // Confirmations (« Ajoutée dans À trier », « J'ouvre Autre »…) : seulement si « Sous-titres » est allumé.
  // Le message du bas (#statut) ne change pas. Rien n'est envoyé à l'IA.
  const CLE_SOUS_TITRES = 'cap_sous_titres_v1';
  const BULLE_MS = 4500;
  const bulleMicro = parId('bulle-micro');
  let delaiBulle = null;
  const sousTitres = () => { try { return localStorage.getItem(CLE_SOUS_TITRES) === 'oui'; } catch (erreur) { return false; } };
  // Réponses d'une commande « faite » qui disent en fait que rien ne s'est passé : traitées comme des échecs.
  // 09/11/2026 : + « C'est le dernier / premier … », « C'est déjà … » (rien n'a été fait : la croix, pas le pouce).
  // 09/11/2026 (défaut 1 vu par Max sur c72 : jamais un pouce sans effet) : + toute réponse « … déjà … » (« Le lecteur est
  // déjà affiché », « La musique joue déjà »…) : rien n'a été fait, donc la croix avec la phrase.
  // Avant : /pas encore pr[eê]t|n[’']est pas (disponible|ouvert)|…|^c[’']est (le |la )?(dernier|…|d[eé]j[aà])/i
  const ECHEC_COMMANDE = /(^|\s)d[eé]j[aà](\s|[.,;:!]|$)|pas encore pr[eê]t|n[’']est pas (disponible|ouvert)|n[’']y a (rien|pas)|je ne (peux|sais|trouve)|impossible|^aucun|d[’']abord|a expir|^c[’']est (le |la )?(dernier|derni[eè]re|premier|premi[eè]re|d[eé]j[aà])/i;
  function montrerBulle(texte, { erreur = false } = {}) {
    if (!bulleMicro || !texte) return;
    if (!erreur && !sousTitres()) return;
    clearTimeout(delaiBulle);
    bulleMicro.textContent = texte;
    bulleMicro.classList.toggle('bulle-erreur', erreur);
    bulleMicro.hidden = false;
    delaiBulle = setTimeout(() => { bulleMicro.hidden = true; bulleMicro.textContent = ''; }, BULLE_MS);
  }
  const boutonSousTitres = parId('bouton-sous-titres');
  if (boutonSousTitres) {
    const montrerEtat = () => boutonSousTitres.setAttribute('aria-checked', String(sousTitres()));
    montrerEtat();
    boutonSousTitres.addEventListener('click', () => {
      try { localStorage.setItem(CLE_SOUS_TITRES, sousTitres() ? 'non' : 'oui'); } catch (erreur) { /* réglage pas gardé */ }
      montrerEtat();
    });
  }

  // ----- 09/11/2026 (accord de Max, étape 4) : POUCE ou CROIX ROUGE à côté du petit micro -----
  // Pouce : compris, certain, fait ou rangé. Croix : pas compris ou pas fait. Fenêtre de choix ouverte (Cap hésite) :
  // rien, tant que Max n'a pas choisi. Jamais le contenu de la phrase, rien de lu à voix haute, rien envoyé à l'IA.
  // Indépendant de « Sous-titres » (la bulle garde sa règle).
  const signeMicro = parId('signe-micro');
  const SIGNE_MS = { pouce: 3000, croix: 2600 }; // 09/11/2026 (accord de Max) : pouce 3 s (avant : 1800 ms)
  let delaiSigne = null;
  // 09/11/2026 (défauts 4 et 5 vus par Max sur c72 : Cap muet dans la visionneuse) : la fenêtre des VIGNETTES de documents et
  // la fenêtre « Musique » ont l'allure des fenêtres de choix (classe fenetre-choix), mais ce ne sont pas des questions :
  // elles restaient ouvertes (même sous la visionneuse) et Cap ne montrait plus ni pouce ni croix. Seules les vraies
  // questions comptent maintenant : la fenêtre de gros choix des commandes, les choix de la musique, la date, l'émetteur.
  // Avant : document.querySelector('dialog.fenetre-choix[open], #choix-voix[open], #question-date[open], #scanner-choix-emetteur[open]')
  const choixOuvert = () => Boolean(document.querySelector('#choix-commande[open], #choix-voix[open], #question-date[open], #scanner-choix-emetteur[open]'));
  function montrerSigne(sorte) {
    if (!signeMicro) return;
    clearTimeout(delaiSigne);
    signeMicro.hidden = true;
    signeMicro.classList.remove('signe-pouce-visible', 'signe-croix-visible');
    if (!sorte || choixOuvert()) return; // Cap hésite (gros choix) ou attend : pas de signe
    void signeMicro.offsetWidth; // l'animation repart du début
    signeMicro.classList.add(sorte === 'pouce' ? 'signe-pouce-visible' : 'signe-croix-visible');
    signeMicro.setAttribute('aria-label', sorte === 'pouce' ? 'Compris' : 'Pas compris ou pas fait');
    signeMicro.hidden = false;
    delaiSigne = setTimeout(() => { signeMicro.hidden = true; signeMicro.classList.remove('signe-pouce-visible', 'signe-croix-visible'); }, SIGNE_MS[sorte]);
  }
  // Le résultat d'une phrase rangée ou traitée (micro des commandes) : pouce, croix, ou rien (question, réflexion en cours).
  function signePourResultat(resultat) {
    if (!resultat) return;
    if (['tache', 'rendez_vous_ajoute', 'report', 'annuler', 'reponse'].includes(resultat.type)) montrerSigne('pouce');
    else if (['pas_compris', 'vide'].includes(resultat.type)) montrerSigne('croix');
    // question, proposition (Cap demande), reflexion (la suite décidera), commande_annuaire (fenêtre), silence : rien
  }

  function ecouterDemandeMicro() {
    let resultatRecu = false;
    let finalRecu = false;
    const musiqueAvant = musiqueJoue(); // 08/11/2026 (reprise automatique)
    const sessionActiveAuDepart = fichiersVocauxControleur.sessionActive();
    if (sessionActiveAuDepart && dernierSonNote === 0) dernierSonNote = Date.now();
    micro.setAttribute('aria-pressed', 'true');
    micro.setAttribute('aria-label', 'Arrêter la dictée');
    annulation.garderPendantEcoute();
    if (!sessionActiveAuDepart) annoncer("Je t'écoute…");
    // 09/11/2026 (défaut 3 vu par Max : « deux » dans la fenêtre de choix = « je n'ai rien entendu ») : pour un mot COURT,
    // Android donne souvent le mot pendant l'écoute (provisoire), puis « pas trouvé » à la fin : le mot était perdu.
    // Maintenant le dernier mot provisoire est gardé et sert de phrase (comme le micro des tuiles le faisait déjà).
    let provisoireMicro = '';
    const garderProvisoire = () => {
      if (finalRecu || !provisoireMicro.trim() || fichiersVocauxControleur.sessionActive()) return false;
      finalRecu = true;
      resultatRecu = true;
      ajouterDictee(provisoireMicro, { commandes: true });
      return true;
    };
    dictee.demarrer({
      surProvisoire(texte) {
        if (texte) provisoireMicro = texte; // 09/11/2026 (défaut 3)
        if (!finalRecu && !fichiersVocauxControleur.sessionActive()) annoncer(texte || "Je t'écoute…");
      },
      surFinal(texte) {
        if (finalRecu) return;
        resultatRecu = true;
        finalRecu = true;
        if (texte && texte.trim()) dernierSonNote = Date.now();
        ajouterDictee(texte, { commandes: true }); // 08/11/2026 (étape 0) : micro du milieu ; avant : ajouterDictee(texte)
      },
      surErreur(code) {
        if (code === 'no-speech' && garderProvisoire()) return; // 09/11/2026 (défaut 3) : le mot court entendu compte
        resultatRecu = true;
        if (finalRecu) return;
        if (code !== 'aborted' && !fichiersVocauxControleur.sessionActive()) temoinMicroChantier(''); // c107 : Android n'a rien rendu
        const messages = {
          'not-allowed': 'Le micro est bloqué. Autorise-le pour cette page dans le navigateur.',
          'service-not-allowed': 'Le micro est bloqué. Autorise-le pour cette page dans le navigateur.',
          'no-speech': "Je n'ai rien entendu, réessaie.",
          network: "La dictée a besoin d'internet pour l'instant.",
          'audio-capture': 'Aucun micro trouvé.'
        };
        // 09/11/2026 (défaut 2) : pendant la fenêtre de gros choix, « rien entendu » dit comment répondre.
        if (code === 'no-speech' && choixCommandeEnCours && fenetreChoixCommande && fenetreChoixCommande.open) messages['no-speech'] = "Je n'ai rien entendu. Dis « numéro deux », ou touche la case.";
        if (!fichiersVocauxControleur.sessionActive()) {
          annoncer(code === 'aborted' ? '' : (messages[code] || "La dictée n'a pas marché, réessaie."));
          if (code !== 'aborted') montrerBulle(messages[code] || "La dictée n'a pas marché, réessaie.", { erreur: true }); // 09/11/2026
          if (code !== 'aborted') montrerSigne('croix'); // 09/11/2026 (étape 4)
        }
      },
      surFin() {
        // Après "terminé", fermerSession() écrit dans Drive (asynchrone) : le micro ne doit pas
        // se relancer pendant ce court instant, sinon il entend du silence et annonce une fausse erreur.
        if (fichiersVocauxControleur.sessionEnCoursDeFermeture()) {
          dernierSonNote = 0;
          micro.setAttribute('aria-pressed', 'false');
          micro.setAttribute('aria-label', 'Dicter une tâche');
          return;
        }
        if (fichiersVocauxControleur.sessionActive()) {
          if (Date.now() - dernierSonNote > SILENCE_NOTE_MS) {
            dernierSonNote = 0;
            micro.setAttribute('aria-pressed', 'false');
            micro.setAttribute('aria-label', 'Dicter une tâche');
            fermerSessionNotePourSilence();
            return;
          }
          ecouterDemandeMicro();
          return;
        }
        dernierSonNote = 0;
        micro.setAttribute('aria-pressed', 'false');
        micro.setAttribute('aria-label', 'Dicter une tâche');
        if (!resultatRecu) garderProvisoire(); // 09/11/2026 (défaut 3)
        if (!resultatRecu) {
          temoinMicroChantier(''); // c107 : fin d'écoute sans aucune phrase
          // 09/11/2026 (défaut 2) : pendant la fenêtre de gros choix, Cap dit comment répondre (un mot seul comme « deux »
          // n'arrive souvent pas jusqu'à Cap : rien n'est transmis par Android).
          const aide = choixCommandeEnCours && fenetreChoixCommande && fenetreChoixCommande.open
            ? "Je n'ai rien entendu. Dis « numéro deux », ou touche la case." : "Je n'ai rien entendu, réessaie.";
          annoncer(aide);
          montrerBulle(aide, { erreur: true }); // 09/11/2026 : visible même sur la visionneuse
          montrerSigne('croix'); // 09/11/2026 (étape 4)
        }
        reprendreMusiqueSiCoupee(musiqueAvant); // 08/11/2026
      }
    });
  }

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
    // 10/11/2026 (c101) : le garde-fou ajouté en c100 (« if (!parId('texte-etat-google')) return; ») est RETIRÉ : il cachait
    // le vrai défaut (identifiant en double qui vidait cette zone) ; une erreur de ce genre doit se voir.
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
    // 11/11/2026 (accord de Max, c140 ; même idée que c139) : téléphone SANS RÉSEAU : l'alerte dit la vraie cause, « Pas de
    // réseau », et cache « Redonner l'accès à Google » (sans réseau, il ouvrait la page d'erreur de Chrome). Le réseau
    // revient : l'alerte redevient comme avant (événements « online » / « offline », plus bas). Avant : toujours
    // « Google a coupé l'accès » et le bouton.
    const horsLigne = navigator.onLine === false;
    parId('redonner-acces-google').hidden = visible && horsLigne;
    if (visible) {
      const attente = nombre === null ? 'Les tâches sont gardées sur ton téléphone ; la file est illisible.'
        : nombre ? `${nombre} tâches attendent : elles sont gardées sur ton téléphone.` : 'Rien n’est perdu.';
      parId('texte-alerte-google').textContent = horsLigne
        ? ['Pas de réseau : Google ne peut pas être joint pour l’instant.', attente, 'Quand le réseau revient, Cap te le redira s’il faut redonner l’accès.'].join(' ')
        : [googleConnexion.besoinGeste()
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
    // Étape A (07/11/2026) : un curseur, ou un champ qui garde un RÉGLAGE (attribut data-reglage, par exemple
    // l'identifiant du compte Cap), n'est pas un texte en cours : il ne bloque plus le renouvellement.
    const texteSaisi = Array.from(document.querySelectorAll('input:not([type="checkbox"]):not([type="button"]):not([type="submit"]):not([type="hidden"]):not([type="range"]):not([data-reglage]), textarea, [contenteditable="true"]'))
      .some(champ => (champ.value ?? champ.textContent).trim());
    const conditionsOk = !document.hidden && !document.querySelector('dialog[open]')
      && !dictee.enCours() && !texteSaisi;
    try { googleConnexion.tenterSilencieux(conditionsOk); } catch (erreur) { signalerErreur(erreur); }
  }

  const ecranComplet = parId('ecran-complet');
  const accueil = parId('accueil');
  const basculerVue = parId('basculer-vue');

  // 08/11/2026 (accord de Max, étape 1) : ouverture et fermeture DOUCES de « Chercher » (transition_ecrans.js) :
  // l'écran d'avant disparaît dans le rien, puis le nouveau sort de sous le sable. Avant : changerVue faisait
  // directement le travail de changerVueDirect (gardé tel quel ci-dessous).
  function changerVue(complete) {
    if (typeof transitionEcrans !== 'undefined') transitionEcrans.changer(document, () => changerVueDirect(complete));
    else changerVueDirect(complete);
  }

  function changerVueDirect(complete) {
    document.body.classList.toggle('vue-complete', complete);
    ecranComplet.hidden = !complete;
    ecranComplet.inert = !complete;
    accueil.hidden = complete;
    accueil.inert = complete;
    // Étape A (07/11/2026) : la barre de recherche est maintenant dans « Chercher » (l'écran des tâches),
    // plus sur l'accueil (avant : zoneRecherche.hidden = complete).
    zoneRecherche.hidden = !complete;
    zoneRecherche.inert = !complete;
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
    const groupes = journalIA.conversations().slice(0, 15);
    parId('liste-journal-ia').replaceChildren(...groupes.map((groupe, rang) => {
      const debut = new Date(groupe.debut);
      const titre = `Conversation du ${String(debut.getDate()).padStart(2, '0')}/${String(debut.getMonth() + 1).padStart(2, '0')}`
        + ` à ${debut.getHours()} h ${String(debut.getMinutes()).padStart(2, '0')}`
        + ` (${groupe.echanges.length} échange${groupe.echanges.length > 1 ? 's' : ''})`;
      const bloc = element('details', 'conversation-ia');
      bloc.open = rang === 0;
      const echanges = element('ol');
      echanges.append(...groupe.echanges.map(entree => {
        const ligne = element('li');
        ligne.append(element('span', 'heure-action', dateCourte(entree.heure)), document.createTextNode(` · Max : ${entree.dit}`));
        if (entree.repondu) ligne.append(element('br'), document.createTextNode(`Cap : ${entree.repondu}`));
        if (entree.action) ligne.append(element('br'), document.createTextNode(`Action demandée : ${entree.action}`));
        return ligne;
      }));
      bloc.append(element('summary', '', titre), echanges);
      const ligne = element('li');
      ligne.append(bloc);
      return ligne;
    }));
    if (!groupes.length) parId('liste-journal-ia').append(element('li', '', 'Aucun échange avec l’IA pour l’instant.'));
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
  // Une conversation par ouverture : revenir dans Cap après plus de 15 minutes compte comme une nouvelle ouverture.
  const PAUSE_NOUVELLE_CONVERSATION_MS = 15 * 60 * 1000;
  let cacheLe = 0;
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      cacheLe = Date.now();
      return;
    }
    if (cacheLe && Date.now() - cacheLe > PAUSE_NOUVELLE_CONVERSATION_MS) {
      cerveauClaude.nouvelleConversation();
      cerveau.oublierProposition();
    }
    cacheLe = 0;
    prechargerFiche();
  });

  function erreurReglagesIA(message) {
    const zone = reglagesIA.querySelector('.erreur');
    zone.textContent = message;
    zone.hidden = !message;
  }

  const reglagesDrive = parId('reglages-drive');
  fermetureFenetres.installer(reglagesDrive);

  function erreurReglagesDrive(message) {
    const zone = reglagesDrive.querySelector('.erreur');
    zone.textContent = message;
    zone.hidden = !message;
  }

  function afficherDrive() {
    const cle = clePicker.presente();
    parId('etat-picker').textContent = cle
      ? 'Clé enregistrée sur ce téléphone.'
      : 'Aucune clé : le sélecteur de dossier Google n’est pas encore réglé.';
    parId('retirer-cle-picker').hidden = !cle;
    const dossier = googlePicker.dossierAppCap();
    parId('etat-dossier-drive').textContent = dossier
      ? `Dossier choisi : « ${dossier.nom || dossier.id} ».`
      : 'Aucun dossier choisi pour l’instant.';
    parId('choisir-dossier-drive').disabled = !cle;
    parId('oublier-dossier-drive').hidden = !dossier;
    // Dossier des scans (05/11/2026) : Cap y crée lui-même 00_A_CLASSER.
    const documents = googlePicker.dossierDocumentsPersonnels();
    parId('etat-dossier-documents').textContent = documents
      ? `Scans déposés dans « ${documents.nom || documents.id} › ${REGLAGES_GOOGLE.dossier_a_classer} ».`
      : window.PontMicroAndroid
        // Dans la coque Android, la fenêtre de Google ne s'ouvre pas : le choix se fait dans Chrome.
        ? `Scans : aucun dossier choisi. Choisis « ${REGLAGES_GOOGLE.dossier_documents_personnels} » dans Cap ouvert avec Chrome.`
        : `Scans : aucun dossier choisi. Choisis « ${REGLAGES_GOOGLE.dossier_documents_personnels} ».`;
    parId('choisir-dossier-documents').disabled = !cle;
    parId('oublier-dossier-documents').hidden = !documents;
    // Classement des scans (05/11/2026) : Doc d'architecture et tableur, choisis dans Chrome.
    const architecture = googlePicker.dossierChoisi('architecture');
    const tableur = googlePicker.dossierChoisi('tableur_classement');
    const motsCourtsChoisis = googlePicker.dossierChoisi('mots_cles_courts');
    const dictionnaireChoisi = googlePicker.dossierChoisi('dictionnaire');
    // Jamais d'identifiant ni de nom de fichier à l'écran : seulement choisi ou pas.
    parId('etat-classement').textContent = `Classement : ${architecture ? 'Doc choisi' : 'Doc pas encore choisi'}, `
      + `${tableur ? 'tableur choisi' : 'tableur pas encore choisi'}, `
      + `${motsCourtsChoisis ? 'mots-clés courts choisis' : 'mots-clés courts pas encore choisis (recherche stricte)'}, `
      + `${dictionnaireChoisi ? 'Dictionnaire choisi' : 'Dictionnaire pas encore choisi (émetteur non cherché)'}.`
      + (!(architecture && tableur && motsCourtsChoisis && dictionnaireChoisi) && window.PontMicroAndroid ? ' Choisis-les dans Cap ouvert avec Chrome.' : '');
    parId('choisir-architecture').disabled = !cle;
    parId('choisir-tableur-classement').disabled = !cle;
    parId('choisir-mots-courts').disabled = !cle;
    parId('choisir-dictionnaire').disabled = !cle;
    parId('verifier-classement').disabled = !(architecture && tableur);
    // 08/11/2026 : tableur « Commandes vocales » (choisi ou pas, et la copie du téléphone en nombres seulement).
    // 08/11/2026, 13h (option 4) : lu avec le compte Cap, à qui Max a partagé le tableur (lecture seule).
    const copieCommandes = commandesVocales.copie();
    parId('etat-commandes-vocales').textContent = 'Commandes vocales (lues avec le compte Cap) : '
      + (copieCommandes ? `${copieCommandes.compte.gardees} formulation(s) gardée(s) sur ce téléphone.` : 'rien de lu pour l’instant.');
    parId('choisir-commandes-vocales').disabled = !cle;
    if (parId('choisir-chantiers')) parId('choisir-chantiers').disabled = !cle; // 09/11/2026 (chantiers, séance 1)
  }

  parId('ouvrir-reglages-drive').addEventListener('click', event => {
    ouvrir(reglagesDrive, parId('titre-reglages-drive'), event.currentTarget);
    afficherDrive();
    afficherPhrasesEntendues(); // 08/11/2026 (correction D)
    // Coque Android : le dossier des scans, choisi dans Chrome, est relu dans le Drive.
    if (googleConnexion.connecte()) {
      for (const role of ['documents_personnels', 'architecture', 'tableur_classement', 'mots_cles_courts', 'dictionnaire', 'commandes_vocales']) {
        if (googlePicker.dossierChoisi(role)) continue;
        googlePicker.retrouverDepuisDrive(role)
          .then(dossier => { if (dossier) afficherDrive(); })
          .catch(() => {});
      }
    }
  });
  parId('formulaire-cle-picker').addEventListener('submit', event => {
    event.preventDefault();
    const champ = parId('cle-picker');
    try {
      clePicker.enregistrer(champ.value);
      champ.value = '';
      erreurReglagesDrive('');
      annoncer('Clé du sélecteur Google enregistrée sur ce téléphone.');
    } catch (erreur) {
      erreurReglagesDrive(erreur.message);
    }
    afficherDrive();
  });
  parId('retirer-cle-picker').addEventListener('click', () => {
    clePicker.retirer();
    erreurReglagesDrive('');
    annoncer('Clé du sélecteur Google retirée de ce téléphone.');
    afficherDrive();
  });
  // Diagnostic du sélecteur (05/11/2026) : étapes franchies, affichées dans « Réglages du Drive ».
  // Jamais la clé ni le jeton (google_picker.js ne les met jamais dans ces textes).
  function diagnosticPicker(lignes) {
    const zone = parId('diagnostic-picker');
    zone.textContent = lignes.length ? `Diagnostic :\n${lignes.join('\n')}` : '';
    zone.hidden = !lignes.length;
  }

  // « Réglages du Drive » est une fenêtre modale, toujours au-dessus de tout : la fenêtre de Google
  // s'ouvrait derrière, invisible. On ferme donc les réglages pendant le choix, puis on les rouvre
  // (aussi si Google ne répond pas du tout, pour que Max voie le diagnostic).
  async function choisirDossierDrive(role, apres) {
    return choisirDansGoogle(options => googlePicker.choisir(role, options), apres);
  }

  // Ouvre une fenêtre du sélecteur Google (`lancer`), réglages fermés, puis les rouvre avec le diagnostic.
  async function choisirDansGoogle(lancer, apres) {
    const lignes = [];
    const rouvrir = () => {
      if (!reglagesDrive.open) reglagesDrive.showModal();
      afficherDrive();
      diagnosticPicker(lignes);
    };
    const noter = texte => {
      lignes.push(texte);
      if (reglagesDrive.open) diagnosticPicker(lignes);
    };
    erreurReglagesDrive('');
    diagnosticPicker([]);
    try {
      if (!clePicker.presente() || !googleConnexion.connecte()) {
        await lancer({ noter });
      }
      if (reglagesDrive.open) reglagesDrive.close();
      const dossier = await lancer({ noter, surSilence: rouvrir });
      rouvrir();
      if (dossier) await apres(dossier);
    } catch (erreur) {
      noter(`Arrêt : ${erreur.message}`);
      rouvrir();
      erreurReglagesDrive(erreur.message);
    }
  }

  parId('choisir-dossier-drive').addEventListener('click', () => {
    void choisirDossierDrive('app_cap', async () => {
      annoncer('Dossier « App Cap » enregistré.');
    });
  });
  parId('oublier-dossier-drive').addEventListener('click', () => {
    googlePicker.oublierDossier();
    erreurReglagesDrive('');
    annoncer('Dossier oublié : choisis-en un à nouveau quand tu veux.');
    afficherDrive();
  });

  parId('choisir-dossier-documents').addEventListener('click', () => {
    void choisirDossierDrive('documents_personnels', async dossier => {
      // Rangé aussi dans le Drive, pour que la coque Android le retrouve toute seule.
      try {
        await googlePicker.rangerDansDrive('documents_personnels');
        annoncer(`Dossier « ${dossier.nom || REGLAGES_GOOGLE.dossier_documents_personnels} » enregistré pour les scans, `
          + 'aussi pour l’application Cap du téléphone.', true);
      } catch (erreur) {
        erreurReglagesDrive('Dossier choisi ici, mais pas encore rangé dans le Drive : l’application Cap du téléphone '
          + 'ne le retrouvera pas. Réessaie quand Google répond.');
      }
    });
  });
  // Chaque fichier est choisi à part (la fenêtre de Google ne permet pas d'en cocher deux sur le téléphone).
  for (const [bouton, role, libelle] of [['choisir-architecture', 'architecture', 'Doc d’architecture'],
    ['choisir-tableur-classement', 'tableur_classement', 'Tableur de classement'],
    ['choisir-mots-courts', 'mots_cles_courts', 'Tableur des mots-clés courts'],
    ['choisir-dictionnaire', 'dictionnaire', 'Dictionnaire général'],
    ['choisir-commandes-vocales', 'commandes_vocales', 'Tableur « Commandes vocales »'],
    ['choisir-chantiers', 'chantiers', 'Tableur « Liste des chantiers »']]) { // 09/11/2026 : + Liste des chantiers
    parId(bouton).addEventListener('click', () => {
      parId('resume-classement').hidden = true;
      void choisirDansGoogle(options => googlePicker.choisirFichier(role, options), async () => {
        // Rangé aussi dans le Drive, pour que la coque Android le retrouve toute seule.
        try {
          await googlePicker.rangerDansDrive(role);
          annoncer(`${libelle} enregistré, aussi pour l’application Cap du téléphone.`);
        } catch (erreur) {
          erreurReglagesDrive(`${libelle} choisi ici, mais pas encore rangé dans le Drive : l’application Cap du téléphone `
            + 'ne le retrouvera pas. Réessaie quand Google répond.');
        }
      });
    });
  }
  // 08/11/2026 (accord de Max) : lecture du tableur « Commandes vocales », copie réduite sur ce téléphone,
  // résumé en nombres seulement (aucune formulation ni aucun nom affiché).
  parId('lire-commandes-vocales').addEventListener('click', () => attenteLecture.pendant(parId('lire-commandes-vocales'), async () => {
    const zone = parId('resume-commandes-vocales');
    zone.hidden = false;
    zone.textContent = 'Lecture du tableur « Commandes vocales »… (rien n’est modifié)';
    erreurReglagesDrive('');
    try {
      parId('autoriser-commandes-vocales').hidden = true;
      // 08/11/2026, 13h : avec le compte Cap (ancienne lecture par la fenêtre de choix : commandesVocales.lireEtGarder()).
      const copie = await commandesVocales.lireAvecCompteCap();
      zone.textContent = commandesVocales.texteResume(copie.compte, new Date(copie.lu_le).toLocaleString('fr-FR'));
    } catch (erreur) {
      // Connexion du compte Cap absente ou expirée : message clair et « Autoriser la lecture du compte Cap ».
      zone.textContent = erreur.message;
      parId('autoriser-commandes-vocales').hidden = !/expir|pas connecté/i.test(erreur.message);
    }
    afficherDrive();
  }));
  // 08/11/2026 (étape 2) : essai de la reconnaissance (aucune action lancée, rien n'est gardé, rien ne part).
  parId('reconnaitre-commandes-vocales').addEventListener('click', () => {
    const zone = parId('resultat-commandes-vocales');
    zone.hidden = false;
    zone.textContent = commandesVocales.texteReconnaissance(commandesVocales.reconnaitre(parId('phrase-commandes-vocales').value));
  });
  parId('autoriser-commandes-vocales').addEventListener('click', () => {
    try { googleCompteRelations.seConnecter(); } catch (erreur) { erreurReglagesDrive(erreur.message); }
  });
  // Étape 1 : lecture seule des deux fichiers, résumé en nombres seulement (aucun nom affiché).
  parId('verifier-classement').addEventListener('click', async () => {
    const zone = parId('resume-classement');
    zone.hidden = false;
    zone.textContent = 'Lecture du Doc et du tableur…';
    erreurReglagesDrive('');
    try {
      const lecture = await classement.lire();
      zone.textContent = [...lecture.etats, classement.texteResume(lecture.resume)].join('\n');
      noterLecture('réussie', lecture.etats);
    } catch (erreur) {
      zone.textContent = '';
      zone.hidden = true;
      erreurReglagesDrive(erreur.message);
      noterLecture('échouée', String(erreur.message).split('\n'));
    }
  });
  // Journal Numérisation : une ligne par lecture (états seulement, jamais un nom ni un identifiant).
  function noterLecture(resultat, etats) {
    try {
      journaux.ajouter('numerisation', { action: 'Lecture du classement', resultat, details: etats.join(' ; ') });
    } catch (erreur) {
      erreurReglagesDrive(`La ligne du Journal Numérisation n’a pas pu être gardée : ${erreur.message}`);
    }
  }
  parId('oublier-dossier-documents').addEventListener('click', async () => {
    try {
      await googlePicker.oublierDossier('documents_personnels');
      erreurReglagesDrive('');
      annoncer('Dossier des scans oublié : choisis-en un à nouveau quand tu veux.');
    } catch (erreur) {
      erreurReglagesDrive('Dossier oublié ici, mais pas dans le Drive : réessaie quand Google répond.');
    }
    afficherDrive();
  });

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

  // ---------- Mes phrases (réglages des phrases vocales, module phrases_modifiables.js) ----------

  const reglagesPhrases = parId('reglages-phrases');
  fermetureFenetres.installer(reglagesPhrases);
  let rubriqueCourantePhrases = null;
  let modifPhraseCourante = null;
  let champVocalPhrase = false;

  function etatPhrases() { return phrasesModifiablesEtat.obtenir(); }

  function statutPhrases(message) {
    const zone = parId('statut-phrases');
    zone.textContent = message;
    zone.hidden = !message;
  }

  function erreurPhrases(message) {
    const zone = parId('erreur-phrases');
    zone.textContent = message;
    zone.hidden = !message;
  }

  function ligneRubriquePhrases(id, rubrique) {
    const li = element('li');
    const bouton = element('button', '', rubrique.libelle);
    bouton.type = 'button';
    bouton.addEventListener('click', () => ouvrirRubriquePhrases(id));
    li.append(bouton);
    return li;
  }

  function renduListeRubriquesPhrases() {
    const rubriques = Object.entries(etatPhrases().rubriques);
    parId('liste-rubriques-commande').replaceChildren(
      ...rubriques.filter(([, r]) => r.type === 'commande').map(([id, r]) => ligneRubriquePhrases(id, r)));
    parId('liste-rubriques-action').replaceChildren(
      ...rubriques.filter(([, r]) => r.type === 'action').map(([id, r]) => ligneRubriquePhrases(id, r)));
  }

  function ligneActivePhrase(texte) {
    const li = element('li');
    li.append(document.createTextNode(`${texte} `));
    const modifier = element('button', '', 'Modifier');
    modifier.type = 'button';
    modifier.addEventListener('click', () => demarrerModificationPhrase(texte));
    const retirer = element('button', '', 'Retirer');
    retirer.type = 'button';
    retirer.addEventListener('click', () => retirerPhraseEcran(texte));
    li.append(modifier, retirer);
    return li;
  }

  function renduDetailPhrases() {
    const rubrique = etatPhrases().rubriques[rubriqueCourantePhrases];
    if (!rubrique) return;
    parId('titre-rubrique-phrases').textContent = rubrique.libelle;
    const actives = rubrique.phrases.filter(entree => entree.retiree_le === null).map(entree => entree.texte);
    parId('liste-phrases-actives').replaceChildren(...actives.map(ligneActivePhrase));
  }

  function annulerModificationPhrase() {
    modifPhraseCourante = null;
    parId('saisie-phrase').value = '';
    parId('bouton-phrase-valider').textContent = 'Ajouter';
    parId('annuler-modif-phrase').hidden = true;
  }

  function demarrerModificationPhrase(texte) {
    modifPhraseCourante = texte;
    parId('saisie-phrase').value = texte;
    parId('bouton-phrase-valider').textContent = 'Enregistrer';
    parId('annuler-modif-phrase').hidden = false;
    erreurPhrases('');
    parId('saisie-phrase').focus({ preventScroll: true });
  }

  function retirerPhraseEcran(texte) {
    const resultat = phrasesModifiables.retirerPhrase(etatPhrases(), rubriqueCourantePhrases, texte);
    if (!resultat.ok) { erreurPhrases(resultat.erreur); return; }
    phrasesModifiablesEtat.enregistrer(resultat.etat);
    erreurPhrases('');
    if (modifPhraseCourante === texte) annulerModificationPhrase();
    renduDetailPhrases();
    statutPhrases(`Phrase retirée : « ${texte} ».`);
  }

  parId('formulaire-phrase').addEventListener('submit', event => {
    event.preventDefault();
    const valeur = parId('saisie-phrase').value;
    const resultat = modifPhraseCourante
      ? phrasesModifiables.modifierPhrase(etatPhrases(), rubriqueCourantePhrases, modifPhraseCourante, valeur)
      : phrasesModifiables.ajouterPhrase(etatPhrases(), rubriqueCourantePhrases, valeur);
    if (!resultat.ok) { erreurPhrases(resultat.erreur); return; }
    phrasesModifiablesEtat.enregistrer(resultat.etat);
    erreurPhrases('');
    statutPhrases(modifPhraseCourante ? 'Phrase modifiée.' : 'Phrase ajoutée.');
    annulerModificationPhrase();
    renduDetailPhrases();
  });

  parId('annuler-modif-phrase').addEventListener('click', () => {
    annulerModificationPhrase();
    erreurPhrases('');
  });

  parId('reinitialiser-rubrique-phrases').addEventListener('click', () => {
    parId('confirmation-reinit-phrases').hidden = false;
    parId('annuler-reinit-phrases').focus({ preventScroll: true });
  });

  parId('annuler-reinit-phrases').addEventListener('click', () => {
    parId('confirmation-reinit-phrases').hidden = true;
    parId('reinitialiser-rubrique-phrases').focus({ preventScroll: true });
  });

  parId('confirmer-reinit-phrases').addEventListener('click', () => {
    parId('confirmation-reinit-phrases').hidden = true;
    const resultat = phrasesModifiables.reinitialiser(etatPhrases(), rubriqueCourantePhrases);
    if (!resultat.ok) { erreurPhrases(resultat.erreur); return; }
    phrasesModifiablesEtat.enregistrer(resultat.etat);
    erreurPhrases('');
    annulerModificationPhrase();
    renduDetailPhrases();
    statutPhrases(resultat.ignorees && resultat.ignorees.length
      ? `Phrases d’origine restaurées (sauf : ${resultat.ignorees.join(', ')}, déjà utilisées ailleurs).`
      : 'Phrases d’origine restaurées.');
  });

  function ouvrirRubriquePhrases(id) {
    rubriqueCourantePhrases = id;
    annulerModificationPhrase();
    statutPhrases('');
    erreurPhrases('');
    parId('confirmation-reinit-phrases').hidden = true;
    renduDetailPhrases();
    parId('liste-rubriques-phrases-vue').hidden = true;
    parId('detail-rubrique-phrases').hidden = false;
    parId('saisie-phrase').focus({ preventScroll: true });
  }

  parId('retour-liste-phrases').addEventListener('click', () => {
    parId('detail-rubrique-phrases').hidden = true;
    parId('liste-rubriques-phrases-vue').hidden = false;
    parId('liste-rubriques-commande').querySelector('button')?.focus({ preventScroll: true });
  });

  parId('ouvrir-reglages-phrases').addEventListener('click', event => {
    parId('liste-rubriques-phrases-vue').hidden = false;
    parId('detail-rubrique-phrases').hidden = true;
    renduListeRubriquesPhrases();
    for (const bouton of reglagesPhrases.querySelectorAll('.micro-champ')) bouton.hidden = !dictee.disponible();
    ouvrir(reglagesPhrases, parId('titre-reglages-phrases'), event.currentTarget);
  });

  parId('reglages-phrases').querySelector('.micro-champ').addEventListener('click', event => {
    const bouton = event.currentTarget;
    if (!dictee.disponible()) return;
    if (dictee.enCours() && champVocalPhrase) {
      dictee.arreter();
      return;
    }
    champVocalPhrase = true;
    bouton.setAttribute('aria-pressed', 'true');
    statutPhrases('Je t’écoute…');
    let recu = false;
    dictee.demarrer({
      surProvisoire(texteRecu) {
        if (!recu) statutPhrases(`J’entends : « ${texteRecu.trim()} »`);
      },
      surFinal(texteRecu) {
        if (recu) return;
        recu = true;
        parId('saisie-phrase').value = texteRecu.trim();
      },
      surErreur() {},
      surFin() {
        champVocalPhrase = false;
        bouton.setAttribute('aria-pressed', 'false');
        statutPhrases(recu ? '' : 'Je n’ai rien entendu. Réessaie ou écris directement.');
      }
    });
  });

  reglagesPhrases.addEventListener('close', () => {
    rubriqueCourantePhrases = null;
    annulerModificationPhrase();
    statutPhrases('');
    erreurPhrases('');
    parId('confirmation-reinit-phrases').hidden = true;
  });

  basculerVue.addEventListener('click', () => changerVue(ecranComplet.hidden));
  let debutGlissement = null;
  const surface = document.querySelector('.ecran');
  surface.addEventListener('touchstart', event => {
    debutGlissement = null;
    // Étape A (07/11/2026) : pas de glissement vers les tâches quand « Autre » ou « Réglages » est ouvert.
    if (event.touches.length !== 1 || document.querySelector('dialog[open]') || document.documentElement.classList.contains('ecran-cap-ouvert')
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
    // 09/11/2026 (étape 3) : par le « Fermer » des tâches (règle du retour). Avant : changerVue(false).
    else if (debut.complete && vertical > 0 && debut.enHaut && ecranComplet.scrollTop === 0) {
      // c173 : vue ouverte depuis une tuile : retour aux TUILES (avant : toujours « Fermer », donc l'accueil).
      if (vueActuelle.type !== 'tuiles' && vueActuelle.depuisTuiles) { ouvrirVue('tuiles'); return; }
      const f = parId('fermer-chercher'); if (f) f.click(); if (!ecranComplet.hidden) changerVue(false);
    }
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

  // 11/11/2026 (accord de Max, c145, ligne 120 ; même idée que c139 à c144) : SANS RÉSEAU, la page de Google ne s'ouvre pas
  // (elle montrait la page d'erreur de Chrome) : Cap dit « Pas de réseau ». Avec réseau : comme avant.
  const PAS_DE_RESEAU_GOOGLE = 'Pas de réseau : la page de Google ne peut pas s’ouvrir. Reconnecte le téléphone, puis touche de nouveau le bouton. Rien n’a été changé.';
  for (const id of ['connexion-google', 'redonner-acces-google']) {
    parId(id).addEventListener('click', () => {
      if (navigator.onLine === false) { annoncer(PAS_DE_RESEAU_GOOGLE); montrerBulle(PAS_DE_RESEAU_GOOGLE, { erreur: true }); return; } // c145
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
  // c140 : l'alerte Google suit le réseau (« Pas de réseau » hors ligne, comme avant quand il revient).
  window.addEventListener('offline', () => afficherEtatGoogle());
  window.addEventListener('online', () => {
    afficherEtatGoogle(); // c140
    void afficherRendezVous();
    void journalActions.envoyer();
    void journaux.envoyer().catch(() => {});
  });
  // Lignes des journaux de chantier restées sur le téléphone : nouvel essai au démarrage.
  if (journaux.enAttente()) setTimeout(() => { void journaux.envoyer().catch(() => {}); }, 3000);
  try {
    scanEcran.initialiser({ annoncer });
  } catch (erreur) {
    signalerErreur(erreur);
  }
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
