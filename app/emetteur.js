'use strict';

// Reconnaissance de l'émetteur d'un scan (06/11/2026), sans DOM.
// Source : le « Dictionnaire général » du Drive de Max (choisi une fois par lui), trois onglets lus
// dans cet ordre : « Ancienne liste », « Tri contacts », « Dictionnaire ». Seules les colonnes utiles
// sont lues (noms, organisation, fonction, téléphones, mails, adresse) : JAMAIS les notes ni les
// dates de naissance. Rien n'est écrit sur le téléphone ; l'IA ne voit rien de ce module.
// Trois niveaux d'indices trouvés dans le texte lu :
//   fort   : un téléphone (9 derniers chiffres) ou un mail retrouvé tel quel → l'entrée devient un choix ;
//   moyen  : un nom entier, ou un nom de famille avec prénom ou titre (Dr, Docteur…) → un choix ;
//   faible : ville, code postal, rue, fonction → départage seulement, ne crée jamais de choix.
// Verrous : un indice ne décide jamais seul ; seul un nom écrit EXACTEMENT, avec une seule entrée
// possible, est proposé directement (Max valide ensuite le nom avec Oui / Modifier / Non) ; sinon
// les cases s'affichent. La famille et Max sont écartés sur le nom COMPLET, et leurs téléphones,
// mails et adresses ne comptent jamais. Les indices ne s'affichent jamais.
const emetteur = (() => {
  const ONGLETS = Object.freeze(['Ancienne liste', 'Tri contacts', 'Dictionnaire']);
  const COURT = Object.freeze({ 'Ancienne liste': 'ancienne liste', 'Tri contacts': 'tri contacts', Dictionnaire: 'dictionnaire' });
  const TITRES = new Set(['dr', 'docteur', 'pr', 'professeur', 'maitre', 'me']);
  // Mots qui ne désignent personne à eux seuls (jamais reconnus par le nom).
  const GENERIQUES = new Set(('banque banquiere docteur dr service services madame monsieur mme mr m maman papa mairie ecole college '
    + 'creche hopital notaire taxi station boutique client clinique cabinet centre agence assurance credit lyon paris france '
    + 'secretariat accueil urgences pharmacie laboratoire association societe entreprise rue avenue boulevard chemin place '
    + 'allee route impasse quai cours cedex bis de du des la le les et').split(' '));
  const POINTS = Object.freeze({ fort: 10, moyen: 6, souple: 4, faible: 1, faibleMax: 3 });
  const CHOIX_MAX = 4;

  // Sans accents ni majuscules, ponctuation remplacée par des espaces.
  function cle(texte) {
    return String(texte || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
      .replace(/[^a-z0-9@.]+/g, ' ').replace(/(^|\s)[.@]+|[.@]+(\s|$)/g, ' ').replace(/\s+/g, ' ').trim();
  }
  const mots = texte => cle(texte).replace(/[.@]/g, ' ').split(' ').filter(Boolean);
  const chiffres9 = texte => {
    const tout = String(texte || '').replace(/\D/g, '');
    return tout.length >= 9 ? tout.slice(-9) : '';
  };

  // ----- Lecture des onglets (valeurs des seules colonnes autorisées, 1re ligne = en-têtes) -----

  // Colonnes autorisées, par onglet (comparées sans accents ni majuscules). Tout le reste est ignoré,
  // et les colonnes de notes ou de naissance sont refusées même si leur nom ressemble.
  const AUTORISEES = Object.freeze({
    'Ancienne liste': [/^first name$/, /^middle name$/, /^last name$/, /^name prefix$/, /^nickname$/, /^organization name$/,
      /^organization title$/, /^organization department$/, /^e mail \d+ value$/, /^phone \d+ value$/,
      /^address \d+ (street|city|postal code)$/, /^appellations et surnoms$/],
    'Tri contacts': [/^nom dans les contacts$/, /^organisation etiquette$/, /^telephone$/, /^mail$/, /^categorie$/,
      /^nom propre pour le dictionnaire$/, /^role lien avec max$/, /^appellations et surnoms$/],
    Dictionnaire: [/^prenom$/, /^nom$/, /^type$/, /^role$/, /^lien avec max$/, /^appellations et surnoms$/, /^coordonnees$/,
      /^telephone$/, /^mail$/, /^domaine$/, /^adresse postale$/, /^deuxieme telephone$/, /^deuxieme mail$/, /^fonction titre$/]
  });
  const INTERDITES = /note|naissance|anniversaire|birthday|photo|remarque|decision|site/;

  function enteteCle(entete) { return cle(entete).replace(/[.@]/g, ' ').replace(/\s+/g, ' ').trim(); }
  function colonneAutorisee(onglet, entete) {
    const c = enteteCle(entete);
    return Boolean(c) && !INTERDITES.test(c) && (AUTORISEES[onglet] || []).some(motif => motif.test(c));
  }

  // { colonnes: [index…] } des colonnes à demander au Drive pour un onglet, d'après ses en-têtes.
  function colonnesALire(onglet, entetes) {
    return (entetes || []).map((entete, i) => (colonneAutorisee(onglet, entete) ? i : -1)).filter(i => i >= 0);
  }

  // Un nom → { mots, titre, personne } ; les titres en tête (« Dr ») sont retirés et notés.
  function nomDe(texte, personne, familleTexte = '') {
    let liste = mots(texte);
    let titre = false;
    while (liste.length && TITRES.has(liste[0])) { liste = liste.slice(1); titre = true; }
    // famille : le nom de famille (colonne « Nom » ou « Last Name » quand on la connaît, sinon le dernier mot).
    // familleSure : le nom de famille vient d'une colonne connue ; sinon (nom brut d'un contact, ordre
    // inconnu), la règle « titre + nom de famille » ne s'applique pas.
    const famille = mots(familleTexte);
    return liste.length ? { mots: liste, titre, personne, famille: famille.length ? famille : liste.slice(-1), familleSure: famille.length > 0,
      affichage: String(texte || '').replace(/\s+/g, ' ').trim() } : null;
  }

  function entree(onglet, numero, champs) {
    const valeur = nom => Object.entries(champs).filter(([c]) => c === nom).map(([, v]) => v).join(' ').trim();
    const commence = debut => Object.entries(champs).filter(([c]) => c.startsWith(debut)).map(([, v]) => v).filter(Boolean);
    const e = { onglet, numero, noms: [], telephones: [], mails: [], faibles: [], famille: false, affichage: '' };
    const ajouterTel = t => { for (const morceau of String(t).split(/[,;/|\n]+/)) { const n = chiffres9(morceau); if (n) e.telephones.push(n); } };
    const ajouterMails = t => { for (const m of String(t).toLowerCase().match(/[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/g) || []) e.mails.push(m); };
    // Appellations et surnoms (06/11/2026) : chaque forme (séparée par « , » « ; » « | » ou un retour à la
    // ligne) est cherchée TELLE QUELLE dans le texte, titre compris ; trouvée exactement, elle fait
    // reconnaître la fiche. Un seul mot trop court ou courant ne compte pas.
    const ajouterAppellations = t => {
      for (const a of String(t || '').split(/[,;|\n]+/)) {
        const n = nomDe(a, false);
        if (!n) continue;
        n.appellation = mots(a);
        e.noms.push(n);
      }
    };
    const ajouterFaibles = t => { for (const m of mots(t)) if ((m.length >= 4 || /^\d{5}$/.test(m)) && !GENERIQUES.has(m)) e.faibles.push(m); };
    if (onglet === 'Ancienne liste') {
      const personne = [valeur('first name'), valeur('middle name'), valeur('last name')].filter(Boolean).join(' ');
      const organisation = valeur('organization name');
      if (valeur('last name')) e.noms.push(nomDe(`${valeur('name prefix')} ${personne}`, true, valeur('last name')));
      else if (personne) e.noms.push(nomDe(personne, false));
      if (valeur('nickname')) e.noms.push(nomDe(valeur('nickname'), false));
      if (organisation) e.noms.push(nomDe(organisation, false));
      ajouterAppellations(valeur('appellations et surnoms'));
      e.affichage = (valeur('last name') ? personne : '') || organisation || personne;
      commence('phone').forEach(ajouterTel);
      commence('e mail').forEach(ajouterMails);
      [...commence('address'), valeur('organization title'), valeur('organization department')].forEach(ajouterFaibles);
    } else if (onglet === 'Tri contacts') {
      const propre = valeur('nom propre pour le dictionnaire');
      const brut = valeur('nom dans les contacts');
      if (propre) e.noms.push(nomDe(propre, mots(propre).length >= 2, mots(propre).length >= 2 ? mots(propre).slice(-1).join(' ') : ''));
      if (brut) e.noms.push(nomDe(brut, mots(brut).length >= 2));
      if (valeur('organisation etiquette')) e.noms.push(nomDe(valeur('organisation etiquette'), false));
      ajouterAppellations(valeur('appellations et surnoms'));
      e.affichage = propre || brut || valeur('organisation etiquette');
      ajouterTel(valeur('telephone'));
      ajouterMails(valeur('mail'));
      [valeur('role lien avec max'), valeur('categorie')].forEach(ajouterFaibles);
    } else {
      const type = cle(valeur('type'));
      const personne = type ? type.startsWith('personne') : Boolean(valeur('prenom'));
      const complet = [valeur('prenom'), valeur('nom')].filter(Boolean).join(' ');
      if (complet) e.noms.push(nomDe(complet, personne && Boolean(valeur('nom')) && Boolean(valeur('prenom')), valeur('nom')));
      ajouterAppellations(valeur('appellations et surnoms'));
      e.affichage = complet;
      const domaine = cle(valeur('domaine'));
      e.famille = domaine.startsWith('famille') || domaine === 'moi';
      [valeur('telephone'), valeur('deuxieme telephone'), valeur('coordonnees')].forEach(ajouterTel);
      [valeur('mail'), valeur('deuxieme mail'), valeur('coordonnees')].forEach(ajouterMails);
      [valeur('adresse postale'), valeur('fonction titre'), valeur('role')].forEach(ajouterFaibles);
    }
    e.noms = e.noms.filter(Boolean);
    return e;
  }

  // onglets : { 'Ancienne liste': valeurs, 'Tri contacts': valeurs, Dictionnaire: valeurs }, chaque
  // valeur = lignes des SEULES colonnes autorisées, la 1re ligne étant leurs en-têtes ; numero = ligne
  // dans l'onglet (pour le journal : onglet et numéro seulement).
  function analyser(onglets) {
    const entrees = [];
    for (const onglet of ONGLETS) {
      const [entetes = [], ...lignes] = onglets[onglet] || [];
      const noms = entetes.map(enteteCle);
      lignes.forEach((ligne, i) => {
        const champs = {};
        noms.forEach((nom, j) => {
          if (!colonneAutorisee(onglet, entetes[j])) return;
          const v = String(ligne[j] ?? '').trim();
          if (v) champs[nom] = champs[nom] ? `${champs[nom]} ${v}` : v;
        });
        if (Object.keys(champs).length) entrees.push(entree(onglet, i + 2, champs));
      });
    }
    return entrees;
  }

  // ----- Recherche dans le texte lu -----

  // Une lettre d'écart au plus (mots de 5 lettres ou plus).
  function presque(a, b) {
    if (a === b) return true;
    if (a.length < 5 || b.length < 5 || Math.abs(a.length - b.length) > 1) return false;
    let i = 0, j = 0, ecarts = 0;
    while (i < a.length && j < b.length) {
      if (a[i] === b[j]) { i++; j++; continue; }
      if (++ecarts > 1) return false;
      if (a.length > b.length) i++; else if (b.length > a.length) j++; else { i++; j++; }
    }
    return ecarts + (a.length - i) + (b.length - j) <= 1;
  }

  function nomUtilisable(nom) {
    const utiles = nom.mots.filter(m => !GENERIQUES.has(m) && m.length >= 2);
    return utiles.length > 0;
  }

  // Le nom apparaît-il ? → 'exact' | 'souple' | ''. Plusieurs mots : côte à côte, dans l'ordre.
  // Un seul mot : seulement précédé d'un titre (Dr, Docteur…), et jamais un mot générique.
  // Titre juste avant la position i (ou séparé par une initiale) → 'colle' ; séparé par 1 ou 2 mots
  // (le prénom, 06/11/2026) → 'ecarte' ; sinon ''.
  function titreAvant(jetons, i) {
    if (i >= 1 && TITRES.has(jetons[i - 1])) return 'colle';
    if (i >= 2 && TITRES.has(jetons[i - 2]) && jetons[i - 1].length === 1) return 'colle';
    for (const ecart of [2, 3]) {
      if (i - ecart < 0 || !TITRES.has(jetons[i - ecart])) continue;
      const milieu = jetons.slice(i - ecart + 1, i);
      if (milieu.every(m => m.length >= 1 && !TITRES.has(m) && !GENERIQUES.has(m))) return 'ecarte';
    }
    return '';
  }

  // Appellation écrite par Max, cherchée telle quelle (titre compris), mots côte à côte.
  function appellationDansTexte(nom, jetons) {
    const a = nom.appellation;
    if (!a || !a.length) return false;
    if (a.length === 1 && (a[0].length < 4 || GENERIQUES.has(a[0]) || TITRES.has(a[0]))) return false;
    if (a.every(m => GENERIQUES.has(m) || TITRES.has(m))) return false;
    for (let i = 0; i + a.length <= jetons.length; i++) {
      if (a.every((m, k) => jetons[i + k] === m)) return true;
    }
    return false;
  }

  function nomDansTexte(nom, jetons) {
    if (appellationDansTexte(nom, jetons)) return 'appellation';
    if (!nomUtilisable(nom)) return '';
    const n = nom.mots;
    if (n.length >= 2) {
      let meilleur = '';
      for (let i = 0; i + n.length <= jetons.length; i++) {
        let souple = false;
        let ok = true;
        for (let k = 0; k < n.length && ok; k++) {
          if (jetons[i + k] === n[k]) continue;
          if (presque(jetons[i + k], n[k])) souple = true; else ok = false;
        }
        if (ok) { if (!souple) return 'exact'; meilleur = 'souple'; }
      }
      // Nom de famille précédé d'un titre (« Dr Fictif » pour « Jean Fictif »), personnes seulement ;
      // un nom de famille en plusieurs mots (avec trait d'union) doit être là en entier.
      if (nom.personne && nom.familleSure) {
        const famille = nom.famille;
        if (famille.join('').length >= 3 && !famille.every(m => GENERIQUES.has(m))) {
          for (let i = 1; i + famille.length <= jetons.length; i++) {
            // Fiche avec un prénom connu : le titre doit être juste avant le nom de famille (sinon le mot
            // du milieu est un autre prénom, ex. « Dr Jean Fictif » n'est pas « Jeanne Fictif »).
            if (titreAvant(jetons, i) !== 'colle') continue;
            const morceau = jetons.slice(i, i + famille.length);
            if (morceau.every((m, k) => m === famille[k])) return 'exact';
            if (morceau.every((m, k) => presque(m, famille[k]))) meilleur = meilleur || 'souple';
          }
        }
      }
      return meilleur;
    }
    const seul = n[0];
    if (seul.length < 3 || GENERIQUES.has(seul) || !(nom.titre || nom.personne)) return '';
    // Fiche « Dr Nom » : le titre juste avant le nom → exact ; un prénom entre les deux (« Docteur
    // Prénom NOM ») → souple, donc les cases s'affichent (06/11/2026).
    let meilleur = '';
    for (let i = 1; i < jetons.length; i++) {
      const titre = titreAvant(jetons, i);
      if (!titre) continue;
      if (jetons[i] === seul) { if (titre === 'colle') return 'exact'; meilleur = 'souple'; }
      else if (presque(jetons[i], seul)) meilleur = 'souple';
    }
    return meilleur;
  }

  const nomComplet = e => (e.noms.find(n => n.personne) || e.noms[0] || { mots: [] }).mots.join(' ');

  // exclusions : { noms: [noms complets, sans accents] } (personnes de l'onglet « Personnes » du
  // tableur des mots-clés courts). Les entrées « Famille » / « Moi » du Dictionnaire s'y ajoutent.
  // Retour : { etat : 'certain' | 'choix' | 'aucun', candidats : [{ onglet, numero, complet, court,
  //   score, exact }] } ; candidats triés, au plus CHOIX_MAX ; jamais d'indice dans le retour.
  function reconnaitre(texte, entrees, exclusions = {}) {
    // Les adresses mail sont retirées avant de chercher les noms (« jean.fictif@… » n'est pas « Jean Fictif »).
    const jetons = mots(String(texte || '').replace(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g, ' '));
    const contenu = ` ${jetons.join(' ')} `;
    const telephones = new Set();
    for (const m of String(texte || '').match(/(?:\+?\d[\d .\-/]{7,}\d)/g) || []) { const n = chiffres9(m); if (n) telephones.add(n); }
    const mailsTexte = new Set((String(texte || '').toLowerCase().match(/[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/g) || []));
    // Famille et Max : nom complet, et leurs coordonnées ne comptent jamais.
    const nomsExclus = new Set((exclusions.noms || []).map(n => mots(n).join(' ')).filter(Boolean));
    const telExclus = new Set();
    const mailsExclus = new Set();
    for (const e of entrees || []) {
      if (!e.famille) continue;
      const complet = nomComplet(e);
      if (complet) nomsExclus.add(complet);
      e.telephones.forEach(t => telExclus.add(t));
      e.mails.forEach(m => mailsExclus.add(m));
    }
    // Diagnostic (06/11/2026) : des NOMBRES seulement, jamais un nom ni un indice.
    const diagnostic = {
      lues: Object.fromEntries(ONGLETS.map(o => [o, (entrees || []).filter(e => e.onglet === o).length])),
      titres: jetons.filter(m => TITRES.has(m)).length, telephones: telephones.size,
      candidats: { telephone_mail: 0, exact: 0, appellation: 0, souple: 0 }, famille_ecartee: 0
    };
    const groupes = new Map();
    for (const e of entrees || []) {
      if (e.famille || e.noms.some(n => nomsExclus.has(n.mots.join(' ')))) { diagnostic.famille_ecartee++; continue; }
      let score = 0;
      let cree = false;
      let exact = false;
      const forts = e.telephones.filter(t => telephones.has(t) && !telExclus.has(t)).length
        + e.mails.filter(m => mailsTexte.has(m) && !mailsExclus.has(m)).length;
      if (forts) { score += POINTS.fort; cree = true; diagnostic.candidats.telephone_mail++; }
      let meilleurNom = '';
      for (const n of e.noms) {
        const r = nomDansTexte(n, jetons);
        if (r === 'appellation') { meilleurNom = 'exact'; diagnostic.candidats.appellation++; break; }
        if (r === 'exact') { meilleurNom = 'exact'; diagnostic.candidats.exact++; break; }
        if (r === 'souple') meilleurNom = 'souple';
      }
      if (meilleurNom === 'souple') diagnostic.candidats.souple++;
      if (meilleurNom) { score += meilleurNom === 'exact' ? POINTS.moyen : POINTS.souple; cree = true; exact = meilleurNom === 'exact'; }
      if (!cree) continue;
      const faibles = new Set(e.faibles.filter(m => contenu.includes(` ${m} `)));
      score += Math.min(faibles.size, POINTS.faibleMax) * POINTS.faible;
      // Une même personne dans plusieurs onglets : une seule case ; le Dictionnaire gagne toujours.
      const cleGroupe = nomComplet(e) || `${e.onglet}#${e.numero}`;
      const avant = groupes.get(cleGroupe);
      const rang = ONGLETS.indexOf(e.onglet);
      const candidat = { onglet: e.onglet, numero: e.numero, complet: e.affichage || nomComplet(e), score, exact, rang, forts };
      if (!avant) groupes.set(cleGroupe, candidat);
      else if (rang > avant.rang) groupes.set(cleGroupe, { ...candidat, score: Math.max(score, avant.score), exact: exact || avant.exact });
      else { avant.score = Math.max(score, avant.score); avant.exact = avant.exact || exact; }
    }
    const tries = [...groupes.values()].sort((a, b) => b.score - a.score || b.rang - a.rang);
    if (!tries.length) return { etat: 'aucun', candidats: [], diagnostic };
    const candidats = formesCourtes(tries.slice(0, CHOIX_MAX)).map(({ rang, forts, ...c }) => c);
    // Proposé directement seulement si : une seule entrée possible, trouvée par son nom écrit exactement.
    if (tries.length === 1 && tries[0].exact) return { etat: 'certain', candidats, diagnostic };
    return { etat: 'choix', candidats, diagnostic };
  }

  // Forme courte pour les cases (« J. Fictif », sigle d'un organisme long) ; deux formes courtes
  // identiques sont allongées (forme complète, puis onglet et numéro) jusqu'à se distinguer.
  function formeCourte(complet) {
    const liste = String(complet || '').replace(/\s+/g, ' ').trim().split(' ').filter(Boolean);
    if (liste.length >= 2 && liste.length <= 3 && /^[A-ZÀ-Ý]/.test(liste[0]) && liste.join(' ').length > 18) {
      return `${liste[0][0]}. ${liste.slice(1).join(' ')}`;
    }
    if (liste.length >= 4) return liste.filter(m => m.length > 3).map(m => m[0].toUpperCase()).join('');
    return liste.join(' ');
  }
  function formesCourtes(candidats) {
    const avec = candidats.map(c => ({ ...c, court: formeCourte(c.complet) }));
    const doublons = () => {
      const vus = new Map();
      for (const c of avec) vus.set(c.court.toLowerCase(), (vus.get(c.court.toLowerCase()) || 0) + 1);
      return new Set([...vus].filter(([, n]) => n > 1).map(([cle_]) => cle_));
    };
    let deux = doublons();
    for (const c of avec) if (deux.has(c.court.toLowerCase())) c.court = c.complet;
    deux = doublons();
    for (const c of avec) if (deux.has(c.court.toLowerCase())) c.court = `${c.complet} (${COURT[c.onglet]} n° ${c.numero})`;
    return avec;
  }

  return { ONGLETS, colonnesALire, colonneAutorisee, analyser, reconnaitre, formeCourte, presque };
})();
