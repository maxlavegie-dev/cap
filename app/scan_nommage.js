'use strict';

// Nommage des documents scannés (lot 3.3), sans DOM.
// Format : DATE - TYPE - ORGANISME - PERSONNE (si utile) - DESCRIPTION.pdf, sans accent, en majuscules.
// Verrous : la date est celle écrite sur le document (jamais celle du scan) ; sans date lisible, Cap le dit au lieu d'en inventer une ;
// ce module ne renomme rien : il propose un nom, et c'est Max qui le valide.
const scanNommage = (() => {
  const longueur_morceau = 40;
  const longueur_description = 60;
  const longueur_totale = 150;
  const date_a_preciser = 'DATE A PRECISER';

  // Majuscules, sans accent ni caractère spécial, mots séparés par une seule espace.
  function normaliser(texte) {
    return String(texte || '')
      .replace(/œ/gi, 'oe').replace(/æ/gi, 'ae').replace(/ß/g, 'ss')
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .toUpperCase().replace(/[^A-Z0-9]+/g, ' ').trim();
  }

  function couper(texte, maximum) {
    if (texte.length <= maximum) return texte;
    const coupe = texte.slice(0, maximum);
    const dernier = coupe.lastIndexOf(' ');
    return (dernier > maximum / 2 ? coupe.slice(0, dernier) : coupe).trim();
  }

  // AAAA-MM-JJ ou AAAA-MM, calendrier réel. Retourne la date propre ou '' si elle n'est pas valide.
  function dateValide(texte) {
    const m = String(texte || '').trim().match(/^(\d{4})-(\d{2})(?:-(\d{2}))?$/);
    if (!m) return '';
    const annee = Number(m[1]);
    const mois = Number(m[2]);
    if (annee < 1900 || annee > 2100 || mois < 1 || mois > 12) return '';
    if (m[3] !== undefined) {
      const jour = Number(m[3]);
      const dernier = new Date(annee, mois, 0).getDate();
      if (jour < 1 || jour > dernier) return '';
    }
    return m[0];
  }

  function assembler(morceaux) {
    let base = morceaux.join(' - ');
    if (base.length <= longueur_totale) return base;
    const sansDescription = morceaux.slice(0, -1).join(' - ');
    const place = longueur_totale - sansDescription.length - 3;
    if (place >= 5) return `${sansDescription} - ${couper(morceaux[morceaux.length - 1], place)}`;
    return couper(base, longueur_totale);
  }

  function pris(existants) { return new Set((existants || []).map(nom => String(nom).toLowerCase())); }

  // Ajoute .pdf, et -2, -3… si le nom existe déjà : jamais deux fichiers du même nom.
  function uniqueAvecExtension(base, existants) {
    const dejaPris = pris(existants);
    let nom = `${base}.pdf`;
    for (let n = 2; dejaPris.has(nom.toLowerCase()); n++) nom = `${base}-${n}.pdf`;
    return nom;
  }

  // identification : { type, organisme, personne, date, description } (champs vides si inconnus), ou null.
  // Retourne { base, nom, dateValide, manques } ; manques liste, en français, ce que Cap n'a pas pu lire.
  function proposer(identification, existants = []) {
    const id = identification || {};
    const manques = [];
    const date = dateValide(id.date);
    if (!date) manques.push(String(id.date || '').trim() ? 'une date valide' : 'la date');
    const type = couper(normaliser(id.type), longueur_morceau);
    if (!type) manques.push('le type de document');
    const organisme = couper(normaliser(id.organisme), longueur_morceau);
    if (!organisme) manques.push('l’organisme');
    const personne = couper(normaliser(id.personne), longueur_morceau);
    const description = couper(normaliser(id.description), longueur_description);
    const morceaux = [date || date_a_preciser, type || 'DOCUMENT', organisme, personne, description].filter(Boolean);
    const base = assembler(morceaux);
    return { base, nom: uniqueAvecExtension(base, existants), dateValide: !!date, manques };
  }

  // Vérifie le nom tapé ou gardé par Max (sans .pdf). Retourne { ok, base, raison }. Rien n'est accepté sans date valide en tête.
  function verifier(saisie) {
    const texte = String(saisie || '').trim().replace(/\.pdf$/i, '').trim();
    const m = texte.match(/^(\d{4}-\d{2}(?:-\d{2})?)(?:\s*-\s*(.*))?$/);
    const date = m ? dateValide(m[1]) : '';
    if (!date) return { ok: false, base: '', raison: 'Le nom doit commencer par une date valide écrite sur le document, par exemple 2026-05-14 ou 2026-05.' };
    const morceaux = (m[2] || '').split(/\s*-\s*/).map(normaliser).filter(Boolean);
    if (!morceaux.length) return { ok: false, base: '', raison: 'Ajoute au moins le type de document après la date.' };
    return { ok: true, base: assembler([date, ...morceaux]), raison: '' };
  }

  return { normaliser, dateValide, proposer, verifier, uniqueAvecExtension, date_a_preciser };
})();
