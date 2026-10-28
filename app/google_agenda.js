'use strict';

const googleAgenda = (() => {
  const cleStockage = 'cap_google_agenda_v1';
  const cleCache = 'cap_google_rendezvous_v1';
  const racine = 'https://www.googleapis.com/calendar/v3';
  const fuseau = 'Europe/Paris';
  let ouverture = null;

  function erreurAvecStatut(message, statut) {
    const erreur = new Error(message);
    erreur.statut = statut;
    return erreur;
  }

  function statutDe(erreur) {
    return erreur.statut ?? erreur.status;
  }

  async function requete(url, options = {}) {
    if (!googleConnexion.connecte()) throw erreurAvecStatut('Connecte-toi à Google pour accéder à l’agenda.', 0);
    const reponse = await googleConnexion.appeler(url, options);
    if (!reponse.ok) throw erreurAvecStatut(`Google a répondu ${reponse.status}.`, reponse.status);
    return reponse;
  }

  function lireStockage(cle) {
    try {
      return localStorage.getItem(cle);
    } catch (erreur) {
      return null;
    }
  }

  function ecrireStockage(cle, valeur) {
    try {
      localStorage.setItem(cle, valeur);
    } catch (erreur) {
      return;
    }
  }

  function idValide(id) {
    return typeof id === 'string' && id !== '' && id !== 'primary';
  }

  function ajouterJours(texte, nombre) {
    const date = new Date(`${texte}T12:00:00Z`);
    date.setUTCDate(date.getUTCDate() + nombre);
    return date.toISOString().slice(0, 10);
  }

  function partsParis(date) {
    const parties = new Intl.DateTimeFormat('en-GB', {
      timeZone: fuseau,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hourCycle: 'h23'
    }).formatToParts(date);
    const valeur = type => parties.find(partie => partie.type === type).value;
    return {
      date: `${valeur('year')}-${valeur('month')}-${valeur('day')}`,
      heure: `${valeur('hour')}:${valeur('minute')}`
    };
  }

  function horaireDescription(description) {
    const trouve = /^\s*(\d{1,2})(?:h(\d{2})?|:(\d{2}))(?!\d)/i.exec(description || '');
    if (!trouve) return '';
    const heures = Number(trouve[1]);
    const minutes = Number(trouve[2] || trouve[3] || 0);
    if (heures > 23 || minutes > 59) return '';
    return `${String(heures).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
  }

  function lireDescription(texte = '') {
    let notes = String(texte);
    const heure_journee = horaireDescription(notes);
    if (heure_journee) notes = notes.replace(/^\s*\d{1,2}(?:h\d{2}|h|:\d{2})(?!\d)(?:[ \t]*[–—-][ \t]*|[ \t]*)/i, '');
    const lignes = notes.split('\n');
    const resultat = { heure_journee, notes: '', telephone: '', mail: '' };
    const extraits = new Set();
    for (let i = lignes.length - 1; i >= 0; i--) {
      const trouve = /^\s*(t[ée]l[ée]phone|mail)\s*:\s*(.*)$/i.exec(lignes[i]);
      if (!trouve || !trouve[2]) continue;
      const champ = trouve[1].toLowerCase() === 'mail' ? 'mail' : 'telephone';
      if (extraits.has(champ)) continue;
      resultat[champ] = trouve[2];
      extraits.add(champ);
      lignes.splice(i, 1);
    }
    resultat.notes = lignes.join('\n');
    return resultat;
  }

  function ecrireDescription({ heure_journee = '', notes = '', telephone = '', mail = '' } = {}) {
    let texte = String(notes);
    if (heure_journee) texte = `${heure_journee.replace(':', 'h')} – ${texte}`;
    for (const [libelle, valeur] of [['Téléphone', telephone], ['Mail', mail]]) {
      if (valeur) texte += `${texte ? '\n' : ''}${libelle} : ${valeur}`;
    }
    return texte;
  }

  function versRendezVous(evenement) {
    const description = evenement.description || '';
    const informations = lireDescription(description);
    const journee = Boolean(evenement.start.date && !evenement.start.dateTime);
    const debut = journee ? { date: evenement.start.date, heure: informations.heure_journee }
      : partsParis(new Date(evenement.start.dateTime));
    return {
      id: evenement.id || '',
      titre: evenement.summary || '',
      date: debut.date,
      heure: debut.heure,
      heure_fin: !journee && evenement.end?.dateTime ? partsParis(new Date(evenement.end.dateTime)).heure : '',
      journee_entiere: journee,
      lieu: evenement.location || '',
      notes: informations.notes,
      telephone: informations.telephone,
      mail: informations.mail,
      rappels: evenement.reminders?.useDefault ? [] : (evenement.reminders?.overrides || [])
        .filter(rappel => rappel.method === 'popup').map(rappel => rappel.minutes),
      description
    };
  }

  async function agendaExiste(id) {
    try {
      await requete(`${racine}/calendars/${encodeURIComponent(id)}`);
      return true;
    } catch (erreur) {
      if (statutDe(erreur) === 404) return false;
      throw erreur;
    }
  }

  async function chercherAgendaExistant() {
    let jeton = '';
    do {
      const url = `${racine}/users/me/calendarList?maxResults=250${jeton ? `&pageToken=${encodeURIComponent(jeton)}` : ''}`;
      let donnees;
      try {
        donnees = await (await requete(url)).json();
      } catch (erreur) {
        if (statutDe(erreur) === 403) return '';
        throw erreur;
      }
      const trouve = (donnees.items || []).find(agenda => agenda.summary === REGLAGES_GOOGLE.nom_agenda && !agenda.primary && idValide(agenda.id));
      if (trouve) return trouve.id;
      jeton = donnees.nextPageToken || '';
    } while (jeton);
    return '';
  }

  async function creerAgenda() {
    const reponse = await requete(`${racine}/calendars`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ summary: REGLAGES_GOOGLE.nom_agenda, timeZone: fuseau })
    });
    const agenda = await reponse.json();
    if (!idValide(agenda.id)) throw new Error('Google n’a pas renvoyé d’agenda valide.');
    return agenda.id;
  }

  async function creerEvenementsFictifs(id) {
    const aujourdhui = partsParis(new Date()).date;
    const modeles = [
      { jours: 1, titre: 'FICTIF – Dentiste', journee: true, description: '14h30 – Cabinet fictif' },
      { jours: 2, titre: 'FICTIF – Répétition studio', debut: '10:00', fin: '10:30' },
      { jours: 4, titre: 'FICTIF – Rendez-vous éditeur', debut: '16:15', fin: '17:00' },
      { jours: 6, titre: 'FICTIF – Kiné', debut: '09:05', fin: '09:35' }
    ];
    const url = `${racine}/calendars/${encodeURIComponent(id)}/events`;
    for (const modele of modeles) {
      const date = ajouterJours(aujourdhui, modele.jours);
      const corps = modele.journee
        ? {
          summary: modele.titre,
          description: modele.description,
          start: { date },
          end: { date: ajouterJours(date, 1) }
        }
        : {
          summary: modele.titre,
          start: { dateTime: `${date}T${modele.debut}:00`, timeZone: fuseau },
          end: { dateTime: `${date}T${modele.fin}:00`, timeZone: fuseau }
        };
      corps.location = '12 rue Fictive, 75000 Paris';
      corps.description = ecrireDescription({
        heure_journee: modele.journee ? '14:30' : '',
        notes: modele.description ? 'Cabinet fictif' : 'Préparation du rendez-vous FICTIF.',
        telephone: modele.jours === 2 ? '' : '01 00 00 00 00',
        mail: modele.jours === 2 ? '' : 'cabinet.fictif@example.com'
      });
      corps.reminders = { useDefault: false, overrides: [60, 1440].map(minutes => ({ method: 'popup', minutes })) };
      await requete(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(corps)
      });
    }
  }

  async function ouvrir() {
    const stocke = lireStockage(cleStockage);
    if (idValide(stocke) && await agendaExiste(stocke)) return stocke;

    const existant = await chercherAgendaExistant();
    if (existant) {
      ecrireStockage(cleStockage, existant);
      return existant;
    }

    const id = await creerAgenda();
    ecrireStockage(cleStockage, id);
    await creerEvenementsFictifs(id);
    return id;
  }

  function trouverOuCreer() {
    if (!ouverture) ouverture = ouvrir().finally(() => { ouverture = null; });
    return ouverture;
  }

  function lireCache() {
    const brut = lireStockage(cleCache);
    if (!brut) return null;
    try {
      const donnees = JSON.parse(brut);
      return Array.isArray(donnees?.rendezvous) ? donnees.rendezvous.filter(rendezVous =>
        rendezVous && typeof rendezVous.titre === 'string' && typeof rendezVous.date === 'string') : null;
    } catch (erreur) {
      return null;
    }
  }

  async function prochainsRendezVous(n = 5) {
    const demande = Math.floor(Number(n));
    const nombre = Number.isFinite(demande) ? Math.min(2500, Math.max(1, demande)) : 5;
    try {
      const id = await trouverOuCreer();
      const url = `${racine}/calendars/${encodeURIComponent(id)}/events?timeMin=${encodeURIComponent(new Date().toISOString())}&singleEvents=true&orderBy=startTime&maxResults=${nombre}`;
      const donnees = await (await requete(url)).json();
      const evenements = (donnees.items || [])
        .filter(evenement => evenement.status !== 'cancelled' && evenement.start && (evenement.start.date || evenement.start.dateTime));
      const liste = evenements.map(versRendezVous);
      ecrireStockage(cleCache, JSON.stringify({ enregistre_le: new Date().toISOString(), rendezvous: liste }));
      return liste;
    } catch (erreur) {
      const cache = lireCache();
      if (cache) return cache.slice(0, nombre);
      throw erreur;
    }
  }

  const cleHistorique = 'cap_rdv_historique_v1';

  function lireHistorique() {
    try {
      const historique = JSON.parse(localStorage.getItem(cleHistorique) || '[]');
      return Array.isArray(historique) ? historique : [];
    } catch (erreur) {
      return [];
    }
  }

  function sauvegarderAncien(id, evenement) {
    try {
      const historique = JSON.parse(localStorage.getItem(cleHistorique) || '[]');
      if (!Array.isArray(historique)) throw new Error();
      const ancien = {};
      for (const champ of ['summary', 'location', 'description', 'start', 'end', 'reminders']) {
        ancien[champ] = evenement[champ] ?? null;
      }
      historique.unshift({ enregistre_le: new Date().toISOString(), id, ancien });
      const texte = JSON.stringify(historique.slice(0, 100));
      localStorage.setItem(cleHistorique, texte);
      if (localStorage.getItem(cleHistorique) !== texte) throw new Error();
    } catch (erreur) {
      throw new Error('Impossible de sauvegarder l’ancienne version sur ce téléphone. Le rendez-vous n’a pas été modifié.');
    }
  }

  function verifierChangements(changements) {
    const champs = ['titre', 'date', 'heure', 'heure_fin', 'lieu', 'notes', 'telephone', 'mail', 'rappels'];
    if (!changements || typeof changements !== 'object' || Array.isArray(changements)
      || Object.keys(changements).some(champ => !champs.includes(champ))) {
      throw new Error('Modification de rendez-vous non autorisée.');
    }
    for (const [champ, valeur] of Object.entries(changements)) {
      if (champ !== 'rappels' && typeof valeur !== 'string') throw new Error('Valeur de rendez-vous invalide.');
    }
    if ('titre' in changements && !changements.titre.trim()) throw new Error('Le titre est obligatoire.');
    if (changements.mail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(changements.mail)) throw new Error('L’adresse mail n’est pas valide.');
    if (['telephone', 'mail'].some(champ => /[\r\n]/.test(changements[champ] || ''))) throw new Error('Les coordonnées doivent tenir sur une ligne.');
    if ('date' in changements && (!/^\d{4}-\d{2}-\d{2}$/.test(changements.date)
      || !Number.isFinite(Date.parse(`${changements.date}T12:00:00Z`))
      || new Date(`${changements.date}T12:00:00Z`).toISOString().slice(0, 10) !== changements.date)) throw new Error('La date n’est pas valide.');
    for (const champ of ['heure', 'heure_fin']) {
      if (changements[champ] && !/^([01]\d|2[0-3]):[0-5]\d$/.test(changements[champ])) throw new Error('L’heure n’est pas valide.');
    }
    if ('rappels' in changements && (!Array.isArray(changements.rappels) || changements.rappels.length > 5
      || changements.rappels.some(minutes => !Number.isInteger(minutes) || minutes < 0 || minutes > 40320))) {
      throw new Error('Choisis au maximum cinq rappels entre 0 et 40320 minutes.');
    }
  }

  async function modifierRendezVous(id, changements) {
    const verifierConnexion = () => {
      if (!navigator.onLine || !googleConnexion.connecte()) throw new Error('Il faut être connecté à Google pour modifier un rendez-vous.');
    };
    verifierConnexion();
    if (typeof id !== 'string' || !id.trim()) throw new Error('Ce rendez-vous n’a pas d’identifiant. Actualise la liste une fois connecté.');
    verifierChangements(changements);
    const idAgenda = await trouverOuCreer();
    if (!idValide(idAgenda)) throw new Error('Modification de cet agenda interdite.');
    const base = `${racine}/calendars/${encodeURIComponent(idAgenda)}`;
    const agenda = await (await requete(base)).json();
    if (agenda.primary || agenda.summary !== REGLAGES_GOOGLE.nom_agenda || !REGLAGES_GOOGLE.nom_agenda.includes('FICTIF')) {
      throw new Error('Seul l’agenda Cap – FICTIF peut être modifié.');
    }
    const url = `${base}/events/${encodeURIComponent(id)}`;
    const ancien = await (await requete(url)).json();
    if (!ancien.start || !ancien.end || ancien.status === 'cancelled') throw new Error('Ce rendez-vous n’est plus modifiable.');
    const actuel = versRendezVous(ancien);
    const nouveau = { ...actuel, ...changements };
    const corps = {};
    if ('titre' in changements) corps.summary = nouveau.titre;
    if ('lieu' in changements) corps.location = nouveau.lieu;
    if (['notes', 'telephone', 'mail'].some(champ => champ in changements)
      || (actuel.journee_entiere && 'heure' in changements)) {
      corps.description = ecrireDescription({
        ...lireDescription(ancien.description || ''),
        notes: nouveau.notes, telephone: nouveau.telephone, mail: nouveau.mail,
        heure_journee: actuel.journee_entiere ? nouveau.heure : lireDescription(ancien.description || '').heure_journee
      });
    }
    if (actuel.journee_entiere) {
      if ('heure_fin' in changements) throw new Error('Une journée entière n’a pas d’heure de fin.');
      if ('date' in changements) {
        const duree = Math.max(1, Math.round((Date.parse(ancien.end.date) - Date.parse(ancien.start.date)) / 86400000));
        corps.start = { date: nouveau.date };
        corps.end = { date: ajouterJours(nouveau.date, duree) };
      }
    } else if (['date', 'heure', 'heure_fin'].some(champ => champ in changements)) {
      if (!nouveau.heure || !nouveau.heure_fin || nouveau.heure_fin <= nouveau.heure) throw new Error('L’heure de fin doit être après l’heure de début.');
      corps.start = { dateTime: `${nouveau.date}T${nouveau.heure}:00`, timeZone: fuseau };
      corps.end = { dateTime: `${nouveau.date}T${nouveau.heure_fin}:00`, timeZone: fuseau };
    }
    if ('rappels' in changements) corps.reminders = {
      useDefault: false, overrides: nouveau.rappels.map(minutes => ({ method: 'popup', minutes }))
    };
    if (!Object.keys(corps).length) return actuel;
    verifierConnexion();
    sauvegarderAncien(id, ancien);
    const headers = { 'Content-Type': 'application/json' };
    if (ancien.etag) headers['If-Match'] = ancien.etag;
    const reponse = await (await requete(url, { method: 'PATCH', headers, body: JSON.stringify(corps) })).json();
    const resultat = versRendezVous({ ...ancien, ...corps, ...reponse, id });
    const cache = lireCache() || [];
    const index = cache.findIndex(rendezVous => rendezVous.id === id);
    if (index < 0) cache.push(resultat);
    else cache[index] = resultat;
    cache.sort((a, b) => `${a.date} ${a.heure}`.localeCompare(`${b.date} ${b.heure}`));
    ecrireStockage(cleCache, JSON.stringify({ enregistre_le: new Date().toISOString(), rendezvous: cache }));
    return resultat;
  }

  return { trouverOuCreer, prochainsRendezVous, lireCache, lireDescription, ecrireDescription, modifierRendezVous, lireHistorique };
})();
