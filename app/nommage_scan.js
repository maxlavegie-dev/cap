'use strict';

// Nom proposé pour un scan à partir du texte lu sur le téléphone (étape 3, 05/11/2026), sans DOM.
// Cherche un mot-clé du tableur de classement dans le texte (sans accents ni majuscules) et prépare
// le nom avec le « Modèle de titre » : « [date] » remplacé par la date lue sur le document
// (AAAA-MM-JJ), ou « DATE A PRECISER » ; le reste du modèle n'est pas touché.
// Verrous : ce module PROPOSE seulement (rien n'est renommé sans le « Oui » de Max) ; aucun mot-clé,
// ou des mots-clés qui mènent à des modèles différents : pas de proposition, le nom SCAN-… reste.
// Il ne garde ni ne recopie le texte lu.
const nommageScan = (() => {
  const dateAPreciser = 'DATE A PRECISER';
  const longueurMax = 150;
  const mois = Object.freeze({ janvier: 1, fevrier: 2, mars: 3, avril: 4, mai: 5, juin: 6, juillet: 7,
    aout: 8, septembre: 9, octobre: 10, novembre: 11, decembre: 12 });

  // Sans accents ni majuscules, ponctuation remplacée par des espaces (comparaison mot à mot).
  function cle(texte) {
    return String(texte || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
      .replace(/[^a-z0-9]+/g, ' ').trim();
  }

  function dateValide(annee, mois_, jour) {
    if (annee < 1900 || annee > 2100 || mois_ < 1 || mois_ > 12 || jour < 1) return '';
    const date = new Date(Date.UTC(annee, mois_ - 1, jour));
    if (date.getUTCMonth() !== mois_ - 1 || date.getUTCDate() !== jour) return '';
    return `${annee}-${String(mois_).padStart(2, '0')}-${String(jour).padStart(2, '0')}`;
  }

  // Première date valide écrite dans le texte (12/03/2026, 12.03.2026, 12-03-2026, 2026-03-12,
  // 12 mars 2026, 1er mars 2026). Aucune : chaîne vide (jamais une date inventée).
  // ----- Lecture de la date (06/11/2026, après l'essai c17) -----
  // Formes acceptées : 17/03/2025, 17.03.2025, 17-03-2025 (espaces permis autour des séparateurs),
  // 2025-03-17, « 17 mars 2025 », « 1er mars 2025 », « 17mars 2025 », mois abrégés (janv., févr., avr.,
  // juil., sept., oct., nov., déc.). Dans une date SEULEMENT, confusions de lecture évidentes corrigées :
  // O → 0, l ou I → 1, « mal » → « mai ». Année sur 2 chiffres : jamais acceptée (comptée « non acceptée »).
  // Jamais une date inventée ; la date retenue est toujours montrée à Max dans le nom proposé.
  const MOIS_ABREGES = Object.freeze({ janvier: 1, janv: 1, fevrier: 2, fevr: 2, fev: 2, mars: 3, avril: 4, avr: 4, mai: 5, mal: 5,
    juin: 6, juillet: 7, juil: 7, aout: 8, septembre: 9, sept: 9, octobre: 10, oct: 10, novembre: 11, nov: 11, decembre: 12, dec: 12 });
  const NOMS_MOIS = Object.keys(MOIS_ABREGES).sort((a, b) => b.length - a.length).join('|');
  const CHIFFRE = '[0-9oil]';

  // Groupe de « chiffres » lu par la reconnaissance : O → 0, l ou i → 1 ; au moins `minimum` vrais chiffres.
  function chiffres(groupe, minimum) {
    const vrais = (groupe.match(/\d/g) || []).length;
    if (vrais < minimum) return null;
    const propre = groupe.replace(/o/g, '0').replace(/[il]/g, '1');
    return { valeur: Number(propre), corrige: propre !== groupe };
  }

  // { date, mois, corrigee, diagnostic } ; diagnostic : des NOMBRES seulement (jamais la date).
  function analyserDates(texte) {
    const plat = String(texte || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    const diagnostic = { candidates: { chiffres: 0, lettres: 0, iso: 0 }, rejetees: { impossible: 0, naissance: 0 },
      non_acceptees: 0, corrections: 0, choisie: 'aucune' };
    const trouvees = [];
    const ajouter = (sorte, position, annee, moisNum, jour, corrige) => {
      if (!annee || !moisNum || !jour) return;
      diagnostic.candidates[sorte]++;
      if (corrige) diagnostic.corrections++;
      trouvees.push({ sorte, position, date: dateValide(annee.valeur, moisNum, jour.valeur), corrige });
    };
    const avant = `(?<![0-9a-z])`;
    const apres = `(?![0-9a-z])`;
    const sep = `\\s*[/.\\-]\\s*`;
    for (const m of plat.matchAll(new RegExp(`${avant}(${CHIFFRE}{1,2})${sep}(${CHIFFRE}{1,2})${sep}(${CHIFFRE}{4})${apres}`, 'g'))) {
      const j = chiffres(m[1], 1), mo = chiffres(m[2], 1), a = chiffres(m[3], 2);
      if (j && mo && a) ajouter('chiffres', m.index, a, mo.valeur, j, j.corrige || mo.corrige || a.corrige);
    }
    for (const m of plat.matchAll(new RegExp(`${avant}(\\d{4})\\s*-\\s*(\\d{2})\\s*-\\s*(\\d{2})${apres}`, 'g'))) {
      ajouter('iso', m.index, { valeur: Number(m[1]) }, Number(m[2]), { valeur: Number(m[3]) }, false);
    }
    for (const m of plat.matchAll(new RegExp(`${avant}(${CHIFFRE}{1,2})(?:er)?\\s*(${NOMS_MOIS})(?![a-z])\\.?\\s*(${CHIFFRE}{4})${apres}`, 'g'))) {
      const j = chiffres(m[1], 1), a = chiffres(m[3], 2);
      if (j && a) ajouter('lettres', m.index, a, MOIS_ABREGES[m[2]], j, j.corrige || a.corrige || m[2] === 'mal');
    }
    // Année sur 2 chiffres (« 17/03/25 ») : jamais acceptée, seulement comptée.
    diagnostic.non_acceptees = [...plat.matchAll(new RegExp(`${avant}\\d{1,2}${sep}\\d{1,2}${sep}\\d{2}${apres}`, 'g'))].length;
    // Une date de naissance (« né le », « née le », « naissance », « DDN ») n'est jamais la date du document.
    const naissance = position => /(?:\bnee?\s*(?:\(e\))?\s*le|naissance|\bddn)\W*$/.test(plat.slice(Math.max(0, position - 30), position));
    const valides = [];
    for (const t of trouvees) {
      if (!t.date) { diagnostic.rejetees.impossible++; continue; }
      if (naissance(t.position)) { diagnostic.rejetees.naissance++; continue; }
      valides.push(t);
    }
    const bonne = valides.sort((a, b) => a.position - b.position)[0];
    if (bonne) {
      diagnostic.choisie = bonne.sorte;
      return { date: bonne.date, mois: '', corrigee: bonne.corrige, diagnostic };
    }
    const moisSeul = moisDuTexte(texte);
    if (moisSeul) diagnostic.choisie = 'mois seul';
    return { date: '', mois: moisSeul, corrigee: false, diagnostic };
  }

  // Première date valide écrite dans le texte ; aucune : chaîne vide (jamais une date inventée).
  function dateDuTexte(texte) {
    return analyserDates(texte).date;
  }

  // Lignes du tableur dont le mot-clé apparaît, mot pour mot, dans le texte.
  function motsClesTrouves(texte, lignes) {
    const contenu = ` ${cle(texte)} `;
    return (lignes || []).filter(ligne => {
      const mot = cle(ligne.mot_cle);
      return mot && contenu.includes(` ${mot} `);
    });
  }

  // { nom (sans .pdf) ou '', mot_cle, raison : 'trouve' | 'aucun' | 'contradictoire' | 'sans_texte', date }
  function proposer(texte, lignes) {
    if (!cle(texte)) return { nom: '', mot_cle: '', raison: 'sans_texte', date: '' };
    const trouvees = motsClesTrouves(texte, lignes);
    if (!trouvees.length) return { nom: '', mot_cle: '', raison: 'aucun', date: '' };
    const modeles = new Set(trouvees.map(ligne => cle(ligne.modele)));
    if (modeles.size > 1) {
      return { nom: '', mot_cle: trouvees.map(ligne => ligne.mot_cle).join(' / '), raison: 'contradictoire', date: '' };
    }
    const ligne = trouvees[0];
    const date = dateDuTexte(texte);
    const nom = ligne.modele.includes('[date]')
      ? ligne.modele.replace('[date]', date || dateAPreciser) : ligne.modele;
    return { nom: nom.replace(/\s+/g, ' ').trim(), mot_cle: ligne.mot_cle, raison: 'trouve', date };
  }

  // Vérifie un nom proposé ou modifié par Max : jamais vide, jamais de caractère interdit dans un
  // nom de fichier. Le nom est gardé tel quel (accents et majuscules compris), sans « .pdf ».
  // 06/11/2026 (règle de nommage) : les caractères interdits sont REMPLACÉS, plus refusés ; « change »
  // dit si le nom a été modifié, pour que Cap montre le résultat à Max avant son « Oui ».
  function verifierNom(saisie) {
    const brut = String(saisie || '').replace(/\.pdf$/i, '').replace(/\s+/g, ' ').trim();
    const base = nettoyerNom(brut);
    if (!base) return { ok: false, base: '', raison: 'Le nom est vide.', change: false };
    if (base.length > longueurMax) return { ok: false, base: '', raison: `Le nom est trop long (plus de ${longueurMax} caractères).`, change: false };
    return { ok: true, base, raison: '', change: base !== brut };
  }

  // ----- Règle de nommage validée par Max le 06/11/2026 -----
  // « AAAA-MM-JJ Type - Émetteur - Personne.pdf » ; émetteur seulement s'il est certain ; sans date
  // lisible : « DATE-A-PRECISER » (jamais la date du scan sans l'accord de Max) ; mois et année
  // seuls : « AAAA-MM » ; caractères interdits remplacés ; même nom : « (2) », « (3) »…
  const dateAPreciserRegle = 'DATE-A-PRECISER';

  // Caractères interdits ou gênants remplacés (jamais refusés) : / et \ → « - » ; « : » → « - » ;
  // ? * < > | et les guillemets supprimés ; espaces doublés réduits ; point ou espace aux bouts retirés.
  function nettoyerNom(saisie) {
    return String(saisie || '').replace(/\.pdf$/i, '')
      .replace(/[\/\\]/g, '-')
      .replace(/\s*:\s*/g, ' - ')
      .replace(/[?*<>|"«»“”\u0000-\u001f]/g, '')
      .replace(/\s+/g, ' ').trim()
      .replace(/^[.\s]+|[.\s]+$/g, '');
  }

  // Mois et année seuls (« mars 2026 », « 03/2026 »), si aucune date complète : « AAAA-MM », sinon ''.
  function moisDuTexte(texte) {
    const plat = String(texte || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    const noms = Object.keys(mois).join('|');
    const trouvees = [];
    for (const m of plat.matchAll(new RegExp(`(?<![\\d])(${noms})\\s+(\\d{4})(?!\\d)`, 'g'))) {
      trouvees.push({ position: m.index, annee: Number(m[2]), mois: mois[m[1]] });
    }
    for (const m of plat.matchAll(/(?<![\d/.-])(\d{1,2})[/.-](\d{4})(?!\d)/g)) {
      trouvees.push({ position: m.index, annee: Number(m[2]), mois: Number(m[1]) });
    }
    const bonne = trouvees.filter(t => t.annee >= 1900 && t.annee <= 2100 && t.mois >= 1 && t.mois <= 12)
      .sort((a, b) => a.position - b.position)[0];
    return bonne ? `${bonne.annee}-${String(bonne.mois).padStart(2, '0')}` : '';
  }

  function composerNom({ date = '', type = '', emetteur = '', personne = '' } = {}) {
    const suite = [emetteur, personne].map(p => String(p || '').trim()).filter(Boolean).map(p => ` - ${p}`).join('');
    return nettoyerNom(`${date || dateAPreciserRegle} ${String(type || '').trim()}${suite}`).slice(0, longueurMax).trim();
  }

  // Même nom déjà pris (sans tenir compte des majuscules) : « Nom (2).pdf », « Nom (3).pdf »…
  function nomUnique(base, existants = []) {
    const pris = new Set(existants.map(nom => String(nom).toLowerCase()));
    let nom = `${base}.pdf`;
    for (let n = 2; pris.has(nom.toLowerCase()); n++) nom = `${base} (${n}).pdf`;
    return nom;
  }

  return { cle, dateDuTexte, analyserDates, motsClesTrouves, proposer, verifierNom, dateAPreciser,
    dateAPreciserRegle, nettoyerNom, moisDuTexte, composerNom, nomUnique };
})();
