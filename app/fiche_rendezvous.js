'use strict';

const ficheRendezVous = (() => {
  const parId = id => document.getElementById(id);
  const dialogue = parId('fiche-rendez-vous');
  const contenu = parId('contenu-fiche-rdv');
  const formulaire = parId('formulaire-rdv');
  const retour = parId('retour-fiche-rdv');
  const erreur = parId('erreur-fiche-rdv');
  const statut = parId('statut-fiche-rdv');
  const confirmer = parId('confirmer-rdv');
  const champs = {
    titre: 'Titre', date: 'Date', heure: 'Heure', heure_fin: 'Heure de fin',
    lieu: 'Adresse', telephone: 'Téléphone', mail: 'Mail', notes: 'Notes', rappels: 'Rappel'
  };
  const standards = [10, 30, 60, 1440, 2880];
  const casesRappels = Array.from(formulaire.querySelectorAll('[name="rappels"]'));
  const formatDate = new Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  let rendezVous;
  let origine;
  let cleOrigine;
  let surModification;
  let changements = {};
  let enCours = false;

  function element(balise, classe, texte) {
    const noeud = document.createElement(balise);
    if (classe) noeud.className = classe;
    if (texte !== undefined) noeud.textContent = texte;
    return noeud;
  }

  function champ(cle) {
    return formulaire.elements.namedItem(cle);
  }

  function texte(valeur) {
    return valeur === undefined || valeur === null ? '' : String(valeur);
  }

  function duree(minutes) {
    if (minutes >= 1440 && minutes % 1440 === 0) return `${minutes / 1440} jour${minutes === 1440 ? '' : 's'}`;
    if (minutes >= 60 && minutes % 60 === 0) return `${minutes / 60} h`;
    return `${minutes} min`;
  }

  function valeurLisible(cle, valeur) {
    if (cle === 'rappels') return valeur?.length ? valeur.map(minutes => `Rappel ${duree(minutes)} avant`).join('\n') : 'Aucun rappel';
    if (cle === 'date' && valeur) {
      const date = new Date(`${valeur}T12:00:00`);
      if (!Number.isNaN(date.getTime())) return formatDate.format(date);
    }
    return texte(valeur).trim() || '—';
  }

  function messageErreur(message) {
    erreur.textContent = message;
    erreur.hidden = !message;
    if (message) erreur.scrollIntoView({ block: 'nearest' });
  }

  function autorise() {
    if (navigator.onLine && googleConnexion.connecte()) return true;
    messageErreur('Il faut être connecté à Google pour modifier un rendez-vous.');
    return false;
  }

  function afficherVue(vue, focus) {
    parId('consultation-rdv').hidden = vue !== 'consultation';
    formulaire.hidden = vue !== 'edition';
    parId('recapitulatif-rdv').hidden = vue !== 'recapitulatif';
    messageErreur('');
    statut.hidden = true;
    statut.textContent = '';
    contenu.scrollTop = 0;
    focus?.focus({ preventScroll: true });
  }

  function carte(titre, valeur, lien) {
    const section = element('section', 'carte-rdv');
    section.append(element('h3', '', titre), element('p', '', valeur));
    if (lien) {
      const ancre = element('a', 'lien-fiche-rdv', lien.texte);
      ancre.href = lien.href;
      if (lien.externe) {
        ancre.target = '_blank';
        ancre.rel = 'noopener';
      }
      section.append(ancre);
    }
    return section;
  }

  function afficherConsultation() {
    const lieu = texte(rendezVous.lieu).trim();
    const telephone = texte(rendezVous.telephone).trim();
    const numero = telephone.replace(/[^\d+]/g, '');
    const mail = texte(rendezVous.mail).trim();
    const horaire = rendezVous.journee_entiere ? rendezVous.heure || 'Toute la journée'
      : [rendezVous.heure, rendezVous.heure_fin].filter(Boolean).join(' – ') || '—';
    const rappel = carte('Rappel', valeurLisible('rappels', rendezVous.rappels));
    rappel.append(element('p', 'info-rappel-rdv', 'La notification vient de Google Agenda sur ton téléphone.'));
    parId('cartes-rdv').replaceChildren(
      carte('Titre', valeurLisible('titre', rendezVous.titre)),
      carte('Date et heure', `${valeurLisible('date', rendezVous.date)} · ${horaire}`),
      carte('Adresse', lieu || '—', lieu ? { texte: 'Itinéraire', href: `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(lieu)}`, externe: true } : null),
      carte('Téléphone', telephone || '—', /\d/.test(numero) ? { texte: 'Appeler', href: `tel:${numero}` } : null),
      carte('Mail', mail || '—', mail ? { texte: 'Écrire', href: `mailto:${encodeURIComponent(mail)}` } : null),
      carte('Notes', valeurLisible('notes', rendezVous.notes)),
      rappel
    );
    afficherVue('consultation', parId('modifier-rdv'));
  }

  function ouvrir(rdv, boutonOrigine, apresModification) {
    if (enCours || dialogue.open) return;
    rendezVous = { ...rdv, rappels: [...(rdv.rappels || [])] };
    origine = boutonOrigine || document.activeElement;
    cleOrigine = origine?.dataset.rdvFocus;
    surModification = apresModification;
    changements = {};
    afficherConsultation();
    dialogue.showModal();
    retour.focus({ preventScroll: true });
  }

  parId('modifier-rdv').addEventListener('click', () => {
    messageErreur('');
    if (!autorise()) return;
    for (const cle of Object.keys(champs).filter(cle => cle !== 'rappels')) champ(cle).value = texte(rendezVous[cle]);
    const journee = Boolean(rendezVous.journee_entiere);
    parId('horaires-rdv').hidden = false;
    champ('heure').disabled = false;
    champ('heure').required = !journee;
    champ('heure_fin').closest('div').hidden = journee;
    champ('heure_fin').disabled = journee;
    for (const caseRappel of casesRappels) caseRappel.checked = rendezVous.rappels.includes(Number(caseRappel.value));
    const autres = rendezVous.rappels.filter(minutes => !standards.includes(minutes));
    parId('autres-rappels-rdv').textContent = autres.length ? `Rappels conservés : ${autres.map(duree).join(', ')} avant.` : '';
    parId('autres-rappels-rdv').hidden = autres.length === 0;
    afficherVue('edition', champ('titre'));
  });

  parId('annuler-edition-rdv').addEventListener('click', afficherConsultation);
  parId('revenir-rdv').addEventListener('click', () => afficherVue('edition', parId('enregistrer-rdv')));
  retour.addEventListener('click', () => { if (!enCours) dialogue.close(); });
  dialogue.addEventListener('cancel', event => { if (enCours) event.preventDefault(); });
  dialogue.addEventListener('close', () => {
    let cible = origine;
    if ((!cible?.isConnected || cible.closest('[hidden], [inert]')) && cleOrigine) {
      cible = Array.from(document.querySelectorAll('[data-rdv-focus]')).find(noeud => noeud.dataset.rdvFocus === cleOrigine);
    }
    if (!cible?.isConnected || cible.closest('[hidden], [inert]')) cible = parId('basculer-vue');
    cible.focus({ preventScroll: true });
    formulaire.reset();
  });

  formulaire.addEventListener('submit', event => {
    event.preventDefault();
    if (enCours) return;
    messageErreur('');
    if (!autorise()) return;
    if (!champ('titre').value.trim()) {
      messageErreur('Donne un titre à ton rendez-vous.');
      champ('titre').focus();
      return;
    }
    if (!champ('date').value || !champ('date').validity.valid) {
      messageErreur('Choisis une date valide.');
      champ('date').focus();
      return;
    }
    const mail = champ('mail').value.trim();
    if (mail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(mail)) {
      messageErreur('Vérifie l’adresse mail.');
      champ('mail').focus();
      return;
    }
    if (!rendezVous.journee_entiere && (!champ('heure').value || !champ('heure_fin').value || champ('heure_fin').value <= champ('heure').value)) {
      messageErreur('L’heure de fin doit être après l’heure de début.');
      champ('heure_fin').focus();
      return;
    }
    changements = {};
    for (const cle of Object.keys(champs).filter(cle => cle !== 'rappels')) {
      if (rendezVous.journee_entiere && (cle === 'heure' || cle === 'heure_fin')) continue;
      const valeur = champ(cle).value;
      if (valeur !== texte(rendezVous[cle])) changements[cle] = valeur;
    }
    const rappels = [...rendezVous.rappels.filter(minutes => !standards.includes(minutes)),
      ...casesRappels.filter(caseRappel => caseRappel.checked).map(caseRappel => Number(caseRappel.value))];
    const trier = valeurs => [...valeurs].sort((a, b) => a - b);
    if (JSON.stringify(trier(rappels)) !== JSON.stringify(trier(rendezVous.rappels))) changements.rappels = rappels;
    const lignes = Object.entries(changements).map(([cle, valeur]) => {
      const section = element('section', 'carte-rdv');
      section.append(element('h4', '', champs[cle]), element('p', '', `${valeurLisible(cle, rendezVous[cle])} → ${valeurLisible(cle, valeur)}`));
      return section;
    });
    parId('changements-rdv').replaceChildren(...(lignes.length ? lignes : [element('p', '', 'Aucun changement.')]));
    confirmer.hidden = lignes.length === 0;
    afficherVue('recapitulatif', parId('titre-recapitulatif-rdv'));
  });

  confirmer.addEventListener('click', async () => {
    if (enCours || !Object.keys(changements).length || !autorise()) return;
    enCours = true;
    dialogue.setAttribute('aria-busy', 'true');
    confirmer.disabled = true;
    parId('revenir-rdv').disabled = true;
    retour.disabled = true;
    confirmer.textContent = 'Enregistrement…';
    messageErreur('');
    try {
      const resultat = await googleAgenda.modifierRendezVous(rendezVous.id, changements);
      rendezVous = { ...resultat, rappels: [...(resultat.rappels || [])] };
    } catch (echec) {
      afficherVue('edition', parId('enregistrer-rdv'));
      messageErreur(echec instanceof Error ? echec.message : 'Le rendez-vous n’a pas pu être modifié. Réessaie.');
      return;
    } finally {
      enCours = false;
      dialogue.removeAttribute('aria-busy');
      confirmer.disabled = false;
      parId('revenir-rdv').disabled = false;
      retour.disabled = false;
      confirmer.textContent = 'Confirmer';
    }
    afficherConsultation();
    statut.textContent = "Rendez-vous mis à jour dans l'agenda Cap – FICTIF.";
    statut.hidden = false;
    contenu.scrollTop = 0;
    try { surModification?.(rendezVous); } catch (echec) {}
  });

  return { ouvrir };
})();
