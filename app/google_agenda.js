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

  function versRendezVous(evenement) {
    const titre = evenement.summary || '';
    if (evenement.start.date && !evenement.start.dateTime) {
      return {
        titre,
        date: evenement.start.date,
        heure: horaireDescription(evenement.description),
        journee_entiere: true
      };
    }
    const debut = partsParis(new Date(evenement.start.dateTime));
    return {
      titre,
      date: debut.date,
      heure: debut.heure,
      journee_entiere: false
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
      const cache = liste.map((rendezVous, index) => ({
        ...rendezVous,
        lieu: evenements[index].location || '',
        description: evenements[index].description || ''
      }));
      ecrireStockage(cleCache, JSON.stringify({ enregistre_le: new Date().toISOString(), rendezvous: cache }));
      return liste;
    } catch (erreur) {
      const cache = lireCache();
      if (cache) return cache.slice(0, nombre);
      throw erreur;
    }
  }

  return { trouverOuCreer, prochainsRendezVous, lireCache };
})();
