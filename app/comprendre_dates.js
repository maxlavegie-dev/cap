'use strict';

const comprendreDates = (() => {
  const nombres = {
    un: 1, une: 1, deux: 2, trois: 3, quatre: 4, cinq: 5, six: 6, sept: 7, huit: 8, neuf: 9, dix: 10,
    onze: 11, douze: 12, treize: 13, quatorze: 14, quinze: 15, seize: 16, 'dix-sept': 17, 'dix-huit': 18,
    'dix-neuf': 19, vingt: 20, 'vingt et un': 21, 'vingt-et-un': 21, trente: 30, 'trente et un': 31, 'trente-et-un': 31
  };
  const jours = ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'];
  const motifsMois = ['janvier', 'f[ée]vrier', 'mars', 'avril', 'mai', 'juin', 'juillet', 'ao[uû]t', 'septembre', 'octobre', 'novembre', 'd[ée]cembre'];
  const N = `(\\d{1,3}|${Object.keys(nombres).sort((a, b) => b.length - a.length).join('|')})`;
  const J = `(${jours.join('|')})`;
  const M = `(${motifsMois.join('|')})`;
  const ORDINAL = '(premier|premi[eè]re|1er|1re|deuxi[eè]me|second|seconde|troisi[eè]me|quatri[eè]me|dernier|derni[eè]re)';

  const deux = valeur => String(valeur).padStart(2, '0');
  const iso = date => `${date.getFullYear()}-${deux(date.getMonth() + 1)}-${deux(date.getDate())}`;
  const jourDe = date => new Date(date.getFullYear(), date.getMonth(), date.getDate(), 12);
  const plus = (date, nombre) => new Date(date.getFullYear(), date.getMonth(), date.getDate() + nombre, 12);
  const finDuMois = (annee, mois) => new Date(annee, mois + 1, 0, 12);
  const lundiDe = date => plus(date, -((date.getDay() + 6) % 7));
  const dansSemaine = (date, jour) => plus(lundiDe(date), (jour + 6) % 7);
  const prochain = (date, jour) => plus(date, ((jour - date.getDay() + 7) % 7) || 7);
  const indexJour = mot => jours.indexOf(mot.toLowerCase());
  const indexMois = mot => motifsMois.findIndex(motif => new RegExp(`^${motif}$`, 'i').test(mot));

  function nombre(mot) {
    const texte = String(mot || '').toLowerCase().replace(/\s+/g, ' ');
    if (/^\d+$/.test(texte)) return Number(texte);
    if (/^(?:1er|1re|premier|premi[eè]re)$/.test(texte)) return 1;
    return nombres[texte];
  }

  function ordinal(mot) {
    const texte = mot.toLowerCase();
    if (texte.startsWith('dern')) return -1;
    if (/^(?:premi|1)/.test(texte)) return 1;
    if (/^(?:deux|second)/.test(texte)) return 2;
    if (texte.startsWith('trois')) return 3;
    return 4;
  }

  function plusMois(date, nombreMois) {
    const fin = finDuMois(date.getFullYear(), date.getMonth() + nombreMois);
    return new Date(fin.getFullYear(), fin.getMonth(), Math.min(date.getDate(), fin.getDate()), 12);
  }

  function dateValide(annee, mois, jour) {
    const date = new Date(annee, mois, jour, 12);
    return date.getMonth() === mois && date.getDate() === jour ? date : null;
  }

  function aVenir(annee, mois, jour, anneeDonnee, aujourdHui) {
    let date = dateValide(annee, mois, jour);
    if (date && !anneeDonnee && date < aujourdHui) date = dateValide(annee + 1, mois, jour);
    return date;
  }

  function nemeJour(annee, mois, jour, rang) {
    if (rang === -1) {
      const fin = finDuMois(annee, mois);
      return plus(fin, -((fin.getDay() - jour + 7) % 7));
    }
    const premier = new Date(annee, mois, 1, 12);
    const date = plus(premier, ((jour - premier.getDay() + 7) % 7) + 7 * (rang - 1));
    return date.getMonth() === mois ? date : null;
  }

  function choix(...dates) {
    return { choix: dates };
  }

  const regles = [
    {
      motif: new RegExp(`\\b(?:le\\s+)?${ORDINAL}\\s+${J}\\s+(du\\s+mois\\s+prochain|du\\s+mois(?:\\s+en\\s+cours)?|de\\s+ce\\s+mois|(?:du\\s+mois\\s+)?(?:de\\s+|d'|en\\s+)${M}(?:\\s+(\\d{4}))?)`, 'i'),
      calcul(t, a) {
        const rang = ordinal(t[1]);
        const jour = indexJour(t[2]);
        if (/prochain/i.test(t[3])) {
          const suivant = finDuMois(a.getFullYear(), a.getMonth() + 1);
          return nemeJour(suivant.getFullYear(), suivant.getMonth(), jour, rang);
        }
        if (t[4]) {
          const mois = indexMois(t[4]);
          let annee = t[5] ? Number(t[5]) : a.getFullYear();
          let date = nemeJour(annee, mois, jour, rang);
          if (date && !t[5] && date < a) date = nemeJour(++annee, mois, jour, rang);
          return date;
        }
        const date = nemeJour(a.getFullYear(), a.getMonth(), jour, rang);
        if (date && date >= a) return date;
        const suivant = finDuMois(a.getFullYear(), a.getMonth() + 1);
        return nemeJour(suivant.getFullYear(), suivant.getMonth(), jour, rang);
      }
    },
    {
      motif: new RegExp(`\\b${J}\\s+en\\s+(huit|quinze|8|15)\\b`, 'i'),
      calcul: (t, a) => plus(prochain(a, indexJour(t[1])), /huit|8/i.test(t[2]) ? 7 : 14)
    },
    {
      motif: new RegExp(`\\b${J}\\s*,?\\s+dans\\s+${N}\\s+semaines?\\b`, 'i'),
      calcul: (t, a) => nombre(t[2]) ? dansSemaine(plus(a, 7 * nombre(t[2])), indexJour(t[1])) : null
    },
    {
      motif: new RegExp(`\\bdans\\s+${N}\\s+semaines?\\s*,?\\s+(?:le\\s+)?${J}\\b`, 'i'),
      calcul: (t, a) => nombre(t[1]) ? dansSemaine(plus(a, 7 * nombre(t[1])), indexJour(t[2])) : null
    },
    {
      motif: new RegExp(`\\b${J}\\s*,?\\s+(?:de\\s+)?(?:la\\s+)?semaine\\s+prochaine\\b`, 'i'),
      calcul: (t, a) => dansSemaine(plus(a, 7), indexJour(t[1]))
    },
    {
      motif: new RegExp(`\\b(?:la\\s+)?semaine\\s+prochaine\\s*,?\\s+(?:le\\s+)?${J}\\b`, 'i'),
      calcul: (t, a) => dansSemaine(plus(a, 7), indexJour(t[1]))
    },
    {
      motif: /\bdans\s+(?:une\s+)?quinzaine(?:\s+de\s+jours)?\b/i,
      calcul: (t, a) => plus(a, 14)
    },
    {
      motif: new RegExp(`\\bdans\\s+${N}\\s+(jours?|semaines?|mois|ans?|ann[ée]es?)\\b`, 'i'),
      calcul(t, a) {
        const n = nombre(t[1]);
        if (!n) return null;
        const unite = t[2].toLowerCase();
        if (unite.startsWith('j')) return n === 8 ? choix(plus(a, 7), plus(a, 8)) : plus(a, n);
        if (unite.startsWith('s')) return plus(a, 7 * n);
        if (unite === 'mois') return plusMois(a, n);
        return plusMois(a, 12 * n);
      }
    },
    {
      motif: /\b(?:à\s+la\s+)?fin\s+(?:du\s+)?mois\s+prochain\b/i,
      calcul: (t, a) => finDuMois(a.getFullYear(), a.getMonth() + 1)
    },
    {
      motif: /\b(?:à\s+la\s+)?fin\s+(?:du|de\s+ce)\s+mois\b/i,
      calcul: (t, a) => finDuMois(a.getFullYear(), a.getMonth())
    },
    {
      motif: /\b(?:à\s+la\s+)?fin\s+(?:de\s+(?:l'|cette\s+)|d'\s*)ann[ée]e\b/i,
      calcul: (t, a) => new Date(a.getFullYear(), 11, 31, 12)
    },
    {
      motif: /\b(?:à\s+la\s+)?fin\s+de\s+(?:la\s+|cette\s+)?semaine\b/i,
      calcul: (t, a) => a.getDay() === 0 ? a : a.getDay() === 6 ? choix(plus(a, 6), plus(a, 1)) : choix(dansSemaine(a, 5), dansSemaine(a, 0))
    },
    {
      motif: new RegExp(`\\b(?:à\\s+la\\s+)?fin\\s+(?:de\\s+|d')?${M}(?:\\s+(\\d{4}))?`, 'i'),
      calcul(t, a) {
        const mois = indexMois(t[1]);
        let annee = t[2] ? Number(t[2]) : a.getFullYear();
        if (!t[2] && finDuMois(annee, mois) < a) annee++;
        return finDuMois(annee, mois);
      }
    },
    { motif: /\bapr[eè]s[- ]demain\b/i, calcul: (t, a) => plus(a, 2) },
    { motif: /\bdemain\b/i, calcul: (t, a) => plus(a, 1) },
    { motif: /\baujourd'hui\b|\bce\s+(?:matin|midi|soir|après-midi)\b/i, calcul: (t, a) => a },
    {
      motif: /\b(?:le\s+)?week[- ]?end\s+prochain\b|\ble\s+prochain\s+week[- ]?end\b/i,
      calcul: (t, a) => dansSemaine(plus(a, 7), 6)
    },
    { motif: /\b(?:ce\s+)?week[- ]?end\b/i, calcul: (t, a) => plus(a, a.getDay() === 0 ? 0 : 6 - a.getDay()) },
    { motif: /\b(?:la\s+)?semaine\s+prochaine\b/i, calcul: (t, a) => dansSemaine(plus(a, 7), 1) },
    {
      motif: new RegExp(`\\b(?:le\\s+)?(?:${J}\\s+)?(1er|1re|premier|${N.slice(1, -1)})\\s+${M}(?:\\s+(\\d{4}))?`, 'i'),
      calcul(t, a) {
        const jour = nombre(t[2]);
        if (!jour) return null;
        return aVenir(t[4] ? Number(t[4]) : a.getFullYear(), indexMois(t[3]), jour, Boolean(t[4]), a);
      }
    },
    {
      motif: /\b(?:le\s+)?(\d{1,2})\/(\d{1,2})(?:\/(\d{4}))?\b/,
      calcul: (t, a) => aVenir(t[3] ? Number(t[3]) : a.getFullYear(), Number(t[2]) - 1, Number(t[1]), Boolean(t[3]), a)
    },
    {
      motif: new RegExp(`\\b(?:(ce)\\s+|le\\s+)?${J}(?:\\s+(prochain))?\\b`, 'i'),
      calcul(t, a) {
        const jour = indexJour(t[2]);
        if (t[3]) {
          const date = prochain(a, jour);
          return date < plus(lundiDe(a), 7) ? choix(date, plus(date, 7)) : date;
        }
        if (jour === a.getDay()) return t[1] ? a : choix(a, plus(a, 7));
        return prochain(a, jour);
      }
    }
  ];

  const regleJourSeul = {
    motif: new RegExp(`^\\s*(?:le\\s+)?(1er|premier|${N.slice(1, -1)})\\s*$`, 'i'),
    calcul(t, a) {
      const jour = nombre(t[1]);
      if (!jour || jour > 31) return null;
      const date = dateValide(a.getFullYear(), a.getMonth(), jour);
      if (date && date >= a) return date;
      for (let decalage = 1; decalage <= 2; decalage++) {
        const fin = finDuMois(a.getFullYear(), a.getMonth() + decalage);
        const suivante = dateValide(fin.getFullYear(), fin.getMonth(), jour);
        if (suivante) return suivante;
      }
      return null;
    }
  };

  function trouver(texte, maintenant = new Date(), { seul = false } = {}) {
    const source = String(texte || '').replace(/[’`]/g, "'");
    const aujourdHui = jourDe(maintenant);
    for (const regle of seul ? [...regles, regleJourSeul] : regles) {
      const trouve = regle.motif.exec(source);
      if (!trouve) continue;
      const resultat = regle.calcul(trouve, aujourdHui);
      if (!resultat) continue;
      if (resultat.choix) {
        const dates = [...new Set(resultat.choix.map(iso))];
        if (dates.length > 1) return { date: '', choix: dates, morceau: trouve[0] };
        return { date: dates[0], choix: [], morceau: trouve[0] };
      }
      return { date: iso(resultat), choix: [], morceau: trouve[0] };
    }
    return { date: '', choix: [], morceau: '' };
  }

  return { trouver };
})();
