'use strict';

const comprendreDemande = (() => {
  const nombres = {
    un: 1, une: 1, deux: 2, trois: 3, quatre: 4, cinq: 5, six: 6, sept: 7, huit: 8, neuf: 9, dix: 10,
    onze: 11, douze: 12, quinze: 15, vingt: 20, 'vingt-cinq': 25, trente: 30, quarante: 40,
    'quarante-cinq': 45, cinquante: 50
  };
  const jours = ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'];
  const mois = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
  const motsNombres = Object.keys(nombres).sort((a, b) => b.length - a.length).join('|');
  const motRendezVous = /\b(?:rendez[- ]vous|rdv)\b/i;
  const motReport = /\b(?:report(?:e|er|es)?|repouss(?:e|er|es)?|décal(?:e|er|es)?)\b/i;

  function deuxChiffres(valeur) {
    return String(valeur).padStart(2, '0');
  }

  function texteDate(date) {
    return `${date.getFullYear()}-${deuxChiffres(date.getMonth() + 1)}-${deuxChiffres(date.getDate())}`;
  }

  function dansJours(maintenant, nombre) {
    const date = new Date(maintenant.getFullYear(), maintenant.getMonth(), maintenant.getDate() + nombre, 12);
    return texteDate(date);
  }

  function dateValide(annee, moisIndex, jour) {
    const date = new Date(annee, moisIndex, jour, 12);
    return date.getMonth() === moisIndex && date.getDate() === jour ? date : null;
  }

  function lireNombre(mot) {
    const texte = mot.toLowerCase();
    return /^\d+$/.test(texte) ? Number(texte) : nombres[texte];
  }

  function trouverRappels(texte) {
    const rappels = [];
    const morceaux = [];
    const expression = new RegExp(`\\b(?:avec\\s+)?(?:un\\s+|une\\s+|des\\s+)?rappels?\\b[^.;]*?(?:(\\d+|${motsNombres})\\s*(minutes?|min|heures?|h|jours?)|(une\\s+demi-heure|un\\s+quart\\s+d'heure|la\\s+veille))(?:\\s+(?:avant|plus\\s+tôt))?`, 'gi');
    for (const trouve of texte.matchAll(expression)) {
      let minutes;
      if (trouve[3]) {
        const special = trouve[3].toLowerCase().replace(/\s+/g, ' ');
        minutes = special === 'la veille' ? 1440 : special.startsWith('une demi') ? 30 : 15;
      } else {
        const nombre = lireNombre(trouve[1]);
        const unite = trouve[2].toLowerCase();
        minutes = unite.startsWith('j') ? nombre * 1440 : unite.startsWith('h') ? nombre * 60 : nombre;
      }
      if (Number.isInteger(minutes) && minutes >= 0 && minutes <= 40320 && !rappels.includes(minutes)) rappels.push(minutes);
      morceaux.push(trouve[0]);
    }
    return { rappels: rappels.slice(0, 5), morceaux };
  }

  function trouverDate(texte, maintenant) {
    let trouve = /\baprès[- ]demain\b/i.exec(texte);
    if (trouve) return { date: dansJours(maintenant, 2), morceau: trouve[0] };
    trouve = /\bdemain\b/i.exec(texte);
    if (trouve) return { date: dansJours(maintenant, 1), morceau: trouve[0] };
    trouve = /\baujourd'hui\b|\bce\s+(?:matin|midi|soir|après-midi)\b/i.exec(texte);
    if (trouve) return { date: dansJours(maintenant, 0), morceau: trouve[0] };
    trouve = /\b(?:ce\s+)?week[- ]?end\b/i.exec(texte);
    if (trouve) return { date: dansJours(maintenant, maintenant.getDay() === 0 ? 0 : 6 - maintenant.getDay()), morceau: trouve[0] };
    trouve = /\b(?:la\s+)?semaine\s+prochaine\b/i.exec(texte);
    if (trouve) return { date: dansJours(maintenant, (8 - maintenant.getDay()) % 7 || 7), morceau: trouve[0] };
    trouve = new RegExp(`\\b(?:le\\s+)?(1er|premier|\\d{1,2})\\s+(${mois.join('|')})(?:\\s+(\\d{4}))?\\b`, 'i').exec(texte);
    if (trouve) {
      const jour = /^\d+$/.test(trouve[1]) ? Number(trouve[1]) : 1;
      const moisIndex = mois.indexOf(trouve[2].toLowerCase());
      let annee = trouve[3] ? Number(trouve[3]) : maintenant.getFullYear();
      let date = dateValide(annee, moisIndex, jour);
      if (date && !trouve[3] && texteDate(date) < dansJours(maintenant, 0)) date = dateValide(++annee, moisIndex, jour);
      if (date) return { date: texteDate(date), morceau: trouve[0] };
    }
    trouve = /\b(?:le\s+)?(\d{1,2})\/(\d{1,2})(?:\/(\d{4}))?\b/.exec(texte);
    if (trouve) {
      let annee = trouve[3] ? Number(trouve[3]) : maintenant.getFullYear();
      let date = dateValide(annee, Number(trouve[2]) - 1, Number(trouve[1]));
      if (date && !trouve[3] && texteDate(date) < dansJours(maintenant, 0)) date = dateValide(++annee, Number(trouve[2]) - 1, Number(trouve[1]));
      if (date) return { date: texteDate(date), morceau: trouve[0] };
    }
    trouve = new RegExp(`\\b(?:ce\\s+|le\\s+)?(${jours.join('|')})(?:\\s+prochain)?\\b`, 'i').exec(texte);
    if (trouve) {
      const ecart = (jours.indexOf(trouve[1].toLowerCase()) - maintenant.getDay() + 7) % 7 || 7;
      return { date: dansJours(maintenant, ecart), morceau: trouve[0] };
    }
    return { date: '', morceau: '' };
  }

  function trouverHeure(texte) {
    let trouve = /(?:(?<!\S)à\s+)?\bmidi\b/i.exec(texte);
    const numerique = /(?:(?<!\S)à\s+)?(?<![\d/])(\d{1,2})\s*(?:heures?|h(?![a-zà-ÿ])|:)(?:\s*(\d{2}))?(?:\s+et\s+(demie|quart))?(?![\d/])/i.exec(texte);
    if (numerique) trouve = numerique;
    if (!trouve) return { heure: '', morceau: '' };
    if (!numerique) return { heure: '12:00', morceau: trouve[0] };
    const heures = Number(trouve[1]);
    const minutes = trouve[2] ? Number(trouve[2]) : trouve[3] === 'demie' ? 30 : trouve[3] === 'quart' ? 15 : 0;
    if (heures > 23 || minutes > 59) return { heure: '', morceau: '' };
    return { heure: `${deuxChiffres(heures)}:${deuxChiffres(minutes)}`, morceau: trouve[0] };
  }

  function uneHeurePlusTard(heure) {
    if (!heure) return '';
    const [heures, minutes] = heure.split(':').map(Number);
    const total = Math.min(heures * 60 + minutes + 60, 23 * 60 + 59);
    return `${deuxChiffres(Math.floor(total / 60))}:${deuxChiffres(total % 60)}`;
  }

  function nettoyer(texte) {
    return texte.replace(/\s+/g, ' ').replace(/^[\s,.;:–-]+|[\s,.;:–-]+$/g, '')
      .replace(/^(?:et|avec|à|pour|qui\s+s'appelle)\s+/i, '').replace(/\s+(?:et|avec|à)$/i, '').trim();
  }

  function trouverTitre(texte, morceaux) {
    const intitule = /\b(?:intitulée?s?|appelée?s?|nommée?s?|titre)\s*:?\s*(.+?)(?=,|;|\.(?:\s|$)|\bavec\b|\b(?:un|une)\s+rappel|$)/i.exec(texte);
    if (intitule && nettoyer(intitule[1])) return nettoyer(intitule[1]);
    let reste = texte;
    for (const morceau of morceaux.filter(Boolean)) reste = reste.replace(morceau, ' ');
    reste = reste.replace(/^.*?\b(?:rendez[- ]vous|rdv)\b/i, ' ');
    reste = nettoyer(reste.replace(/(?<!\S)(?:à|pour|le)\s*(?=,|$)/gi, ' '));
    for (let i = 0; i < 3; i++) reste = nettoyer(reste);
    return reste ? reste.charAt(0).toUpperCase() + reste.slice(1) : '';
  }

  function rendezVous(texte, maintenant = new Date()) {
    const source = String(texte || '').replace(/[’`]/g, "'");
    if (!motRendezVous.test(source) || motReport.test(source)) return null;
    const rappels = trouverRappels(source);
    let sansRappels = source;
    for (const morceau of rappels.morceaux) sansRappels = sansRappels.replace(morceau, ' ');
    const date = trouverDate(sansRappels, maintenant);
    const heure = trouverHeure(sansRappels.replace(date.morceau, ' '));
    const titre = trouverTitre(sansRappels, [date.morceau, heure.morceau]);
    return {
      titre, date: date.date, heure: heure.heure, heure_fin: uneHeurePlusTard(heure.heure),
      journee_entiere: false, lieu: '', telephone: '', mail: '', notes: '', rappels: rappels.rappels
    };
  }

  function report(texte) {
    const source = String(texte || '');
    if (!motReport.test(source) || !/\bdemain\b/i.test(source) || /\baprès[- ]demain\b/i.test(source)) return null;
    return { cible: motRendezVous.test(source) ? 'rendez-vous' : 'tache' };
  }

  function date(texte, maintenant = new Date()) {
    return trouverDate(String(texte || '').replace(/[’`]/g, "'"), maintenant).date;
  }

  return { rendezVous, report, date };
})();
