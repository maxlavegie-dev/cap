'use strict';

// Recherche par mots-clés courts et par score (06/11/2026), sans DOM.
// Le tableur « Cap – Mots-clés courts – à valider » (dans le Drive de Max, choisi une fois par lui)
// découpe chaque ligne du tableur de classement en trois recherches : le type (1 à 3 mots), la
// personne (prénom seul, plusieurs formes possibles) et l'organisme. Le tableur de classement
// reste la BASE : modèles de titre et chemins viennent toujours de lui.
// Règles de lecture du tableur à valider : une « Correction de Max » prime sur la proposition
// (seul ce qui précède la parenthèse compte ; plusieurs formes séparées par « | ») ; « Refusé »
// sans correction : la proposition n'est pas utilisée.
// Verrous : ce module PROPOSE seulement (rien n'est renommé sans le « Oui » de Max) ; il ne garde
// ni ne recopie le texte lu ; aucun nom n'est écrit dans le code (tout vient du Drive).
const motsCourts = (() => {
  const cle = nommageScan.cle;
  const VIDES = new Set('de d du la le l les des a au aux et en un une sur pour par ou avec sans s'.split(' '));
  const BONUS_PERSONNE = 3;
  const BONUS_ORGANISME = 1;
  const POIDS_COURANT = 0.25;
  const BONUS_PHRASE = 1.3; // mots du type côte à côte, dans l'ordre
  const BONUS_HAUT = 1.3; // mots du type dans le haut du document
  const PROCHE = 0.85; // une autre ligne à 85 % du meilleur score ou plus : elle est « proche »
  const CHOIX_MAX = 3;

  // ----- Lecture du tableur à valider (valeurs brutes des onglets) -----

  function colonne(entetes, debut) {
    const cherche = cle(debut);
    return entetes.findIndex(entete => cle(entete).startsWith(cherche));
  }

  // Correction de Max d'abord (avant la parenthèse), sinon la proposition ; « Refusé » seul : rien.
  function valeurRetenue(proposition, statut, correction) {
    const corrige = String(correction || '').split('(')[0].trim();
    if (corrige) return corrige;
    if (cle(statut).startsWith('refuse')) return '';
    return String(proposition || '').trim();
  }

  function lignesOnglet(valeurs, champs) {
    const [entetes = [], ...lignes] = valeurs || [];
    const index = Object.fromEntries(Object.entries(champs).map(([nom, debut]) => [nom, colonne(entetes, debut)]));
    return lignes.map(ligne => Object.fromEntries(Object.entries(index)
      .map(([nom, i]) => [nom, i >= 0 ? String(ligne[i] ?? '').trim() : ''])));
  }

  function formes(valeur) {
    return String(valeur || '').split('|').map(forme => cle(forme)).filter(Boolean);
  }

  // onglets : { types, organismes, personnes, courants } = valeurs brutes (1re ligne = en-têtes).
  function analyser(onglets) {
    const types = new Map();
    for (const l of lignesOnglet(onglets.types, { expression: 'Expression', mots: 'Mots courts', seul: 'Suffit seul',
      statut: 'Statut', correction: 'Correction' })) {
      const expression = cle(l.expression);
      if (!expression) continue;
      const alternatives = formes(valeurRetenue(l.mots, l.statut, l.correction))
        .map(forme => forme.split(' ').filter(mot => mot && !VIDES.has(mot)))
        .filter(mots => mots.length);
      types.set(expression, { alternatives, seul: !cle(l.seul).startsWith('non') });
    }
    const organismes = new Map();
    for (const l of lignesOnglet(onglets.organismes, { organisme: 'Organisme', mots: 'Mots courts', statut: 'Statut', correction: 'Correction' })) {
      const organisme = cle(l.organisme);
      if (organisme) organismes.set(organisme, formes(valeurRetenue(l.mots, l.statut, l.correction)));
    }
    const personnes = [];
    for (const l of lignesOnglet(onglets.personnes, { nom: 'Nom', prenom: 'Prenom', statut: 'Statut', correction: 'Correction' })) {
      const nom = cle(l.nom);
      const prenoms = formes(valeurRetenue(l.prenom, l.statut, l.correction));
      // affichage : le nom tel qu'il est écrit dans le tableur (pour le nom du fichier).
      if (nom && prenoms.length) personnes.push({ nom, prenoms, affichage: String(l.nom).replace(/\s+/g, ' ').trim() });
    }
    // Les noms les plus longs d'abord (un nom ne doit pas en cacher un autre qui le contient).
    personnes.sort((a, b) => b.nom.length - a.nom.length);
    const courants = new Set();
    for (const l of lignesOnglet(onglets.courants, { mot: 'Mot', jamais: 'Jamais seul', statut: 'Statut', correction: 'Correction' })) {
      const mot = cle(l.mot);
      if (mot && cle(valeurRetenue(l.jamais, l.statut, l.correction)).startsWith('oui')) courants.add(mot);
    }
    return { types, organismes, personnes, courants };
  }

  // ----- Recherche dans le texte lu -----

  function chercheur(texte) {
    const contenu = ` ${cle(texte)} `;
    const jetons = contenu.trim() ? contenu.trim().split(' ') : [];
    const egal = (jeton, m) => jeton === m || jeton === `${m}s` || jeton === `${m}x`;
    // Même début (06/11/2026, après l'essai c14) : pour les mots du TYPE seulement, deux mots de
    // 8 lettres ou plus qui ont le même début comptent comme le même mot (le début commun fait au
    // moins 8 lettres, et tout le mot du tableur sauf ses 3 dernières lettres). Ex. : un nom de
    // spécialité et le nom du métier qui va avec. Peut se tromper (ex. « certificat » et
    // « certification ») : le « Oui » de Max protège. Jamais pour les prénoms ni les organismes.
    function memeDebut(jeton, m) {
      if (m.length < 8 || jeton.length < 8) return false;
      let commun = 0;
      while (commun < m.length && commun < jeton.length && m[commun] === jeton[commun]) commun++;
      return commun >= Math.max(8, m.length - 3);
    }
    const egalType = (jeton, m) => egal(jeton, m) || memeDebut(jeton, m);
    // Mot entier, n'importe où ; le pluriel simple (s, x) compte aussi.
    const mot = m => contenu.includes(` ${m} `) || contenu.includes(` ${m}s `) || contenu.includes(` ${m}x `);
    const motType = m => (m.includes(' ') ? mot(m) : jetons.some(jeton => egalType(jeton, m)));
    const expression = e => contenu.includes(` ${e} `);
    const positions = m => jetons.reduce((liste, jeton, i) => (egalType(jeton, m) ? [...liste, i] : liste), []);
    // Le titre d'un courrier est en haut : le premier quart du texte (au moins 120 mots).
    const finDebut = Math.max(120, Math.ceil(jetons.length / 4));
    // Mots côte à côte, dans l'ordre (au plus 3 mots entre deux, ex. « avis de taxe foncière »).
    function enPhrase(mots) {
      if (mots.length < 2) return false;
      const listes = mots.map(positions);
      return listes[0].some(depart => {
        let courant = depart;
        return listes.slice(1).every(liste => {
          const suivant = liste.find(p => p > courant && p - courant <= 4);
          if (suivant === undefined) return false;
          courant = suivant;
          return true;
        });
      });
    }
    const enHaut = mots => mots.every(m => positions(m).some(p => p < finDebut));
    return { mot, motType, expression, enPhrase, enHaut, vide: !jetons.length };
  }

  // Une règle par ligne du tableur de classement : sa personne, son expression, ses mots courts.
  function regles(lignes, mots) {
    return (lignes || []).map(ligne => {
      const motCle = cle(ligne.mot_cle);
      const personneMotCle = mots.personnes.find(p => motCle === p.nom || motCle.endsWith(` ${p.nom}`)) || null;
      const expression = personneMotCle ? motCle.slice(0, motCle.length - personneMotCle.nom.length).trim() : motCle;
      // 06/11/2026 : sans personne dans le mot-clé, celle du « Modèle de titre » (s'il en nomme une).
      const modele = ` ${cle(ligne.modele)} `;
      const personne = personneMotCle || mots.personnes.find(p => modele.includes(` ${p.nom} `)) || null;
      const type = mots.types.get(expression);
      // Ligne absente du tableur à valider (ajoutée depuis) : ses propres mots, sans les petits mots.
      const alternatives = type ? type.alternatives
        : [expression.split(' ').filter(m => m && !VIDES.has(m))].filter(m => m.length);
      return { ligne, personne, expression, alternatives, seul: type ? type.seul : true,
        organisme: mots.organismes.get(cle(ligne.organisme)) || [] };
    }).filter(r => r.alternatives.length);
  }

  // Rareté : un mot présent dans peu d'expressions compte beaucoup ; un mot trop courant, peu.
  function poids(liste, mots) {
    const parExpression = new Map();
    for (const r of liste) if (!parExpression.has(r.expression)) parExpression.set(r.expression, new Set(r.alternatives.flat()));
    const frequence = new Map();
    for (const ensemble of parExpression.values()) for (const m of ensemble) frequence.set(m, (frequence.get(m) || 0) + 1);
    const total = Math.max(parExpression.size, 1);
    return m => Math.log(1 + total / (frequence.get(m) || 1)) * (mots.courants.has(m) ? POIDS_COURANT : 1);
  }

  const arrondi = n => Math.round(n * 10) / 10;

  // Règle de nommage validée par Max (06/11/2026) : « AAAA-MM-JJ Type - Émetteur - Personne ».
  // Type : la colonne « Type de document » du tableur de classement ; vide : le « Modèle de titre »
  // sans « [date] » ni la personne. Émetteur : vide tant qu'il n'est pas reconnu avec certitude.
  function typeDe(r) {
    const type = String(r.ligne.type || '').trim();
    if (type) return type;
    let modele = String(r.ligne.modele || '').replace('[date]', ' ');
    if (r.personne && r.personne.affichage) modele = modele.split(r.personne.affichage).join(' ');
    return modele.replace(/\s+/g, ' ').trim();
  }
  function nomSelonRegle(r, date, emetteur = '') {
    return nommageScan.composerNom({ date, type: typeDe(r), emetteur, personne: r.personne ? r.personne.affichage : '' });
  }

  // { nom, mot_cle, raison : 'trouve' | 'choix' | 'trop_proches' | 'aucun' | 'sans_texte', date, score,
  //   choix : [{ nom, mot_cle, score }], personne_incertaine, meilleurs : 3 meilleurs [{ nom, mot_cle, score }] }
  // options.emetteur : forme complète de l'émetteur (déjà certain, ou choisi par Max), ou ''.
  function proposer(texte, lignes, mots, options = {}) {
    const emetteurNom = String(options.emetteur || '').trim();
    const vide = { nom: '', mot_cle: '', raison: 'aucun', date: '', score: 0, choix: [], personne_incertaine: false, meilleurs: [] };
    const trouve = chercheur(texte);
    if (trouve.vide) return { ...vide, raison: 'sans_texte' };
    const liste = regles(lignes, mots);
    const poidsDe = poids(liste, mots);
    const candidats = [];
    for (const r of liste) {
      // Bonus du titre (06/11/2026, après un essai sur un faux courrier) : un mot cité en passant
      // (« photographie » dans le corps du texte ; 09/11/2026 : exemple neutre, avant un exemple de santé) ne doit pas l'emporter sur le titre écrit en haut.
      const alternative = r.alternatives
        .filter(a => a.every(trouve.motType))
        .map(a => ({ mots: a, score: a.reduce((s, m) => s + poidsDe(m), 0)
          * (trouve.enPhrase(a) ? BONUS_PHRASE : 1) * (trouve.enHaut(a) ? BONUS_HAUT : 1) }))
        .sort((a, b) => b.score - a.score)[0];
      if (!alternative) continue;
      const organisme = r.organisme.find(trouve.expression) || '';
      // Mots trop courants (ou ligne marquée « jamais seul ») : jamais suffisants seuls.
      const suffit = r.seul && alternative.mots.some(m => !mots.courants.has(m));
      if (!suffit && !organisme) continue;
      let personneTrouvee = false;
      let incertaine = false;
      if (r.personne) {
        personneTrouvee = r.personne.prenoms.some(trouve.mot);
        const autre = mots.personnes.some(p => p !== r.personne && p.prenoms.some(trouve.mot));
        if (!personneTrouvee && autre) continue; // le texte parle de quelqu'un d'autre
        incertaine = !personneTrouvee;
      }
      const score = alternative.score + (personneTrouvee ? BONUS_PERSONNE : 0) + (organisme ? BONUS_ORGANISME : 0);
      const motCle = [alternative.mots.join(' '), personneTrouvee ? 'prénom' : '', organisme ? `organisme « ${organisme} »` : '']
        .filter(Boolean).join(' + ');
      candidats.push({ regle: r, cle: cle(r.ligne.modele), mot_cle: motCle, score, incertaine });
    }
    // Une seule fois chaque modèle de titre (son meilleur score).
    const meilleurs = new Map();
    for (const c of candidats) if (!meilleurs.has(c.cle) || meilleurs.get(c.cle).score < c.score) meilleurs.set(c.cle, c);
    const tries = [...meilleurs.values()].sort((a, b) => b.score - a.score);
    if (!tries.length) return vide;
    // Date complète, sinon mois et année seuls ; aucune : « DATE-A-PRECISER » (jamais inventée).
    const lectureDate = nommageScan.analyserDates(texte);
    const date = lectureDate.date || lectureDate.mois;
    vide.date_diagnostic = lectureDate.diagnostic;
    vide.date_corrigee = Boolean(lectureDate.date && lectureDate.corrigee);
    // Pour le Journal Numérisation : les 3 meilleurs candidats et leur score (jamais le texte lu).
    vide.meilleurs = tries.slice(0, 3).map(c => ({ nom: nomSelonRegle(c.regle, date, emetteurNom), mot_cle: c.mot_cle, score: arrondi(c.score) }));
    const proches = tries.filter(c => c.score >= tries[0].score * PROCHE);
    const choix = proches.map(c => ({ nom: nomSelonRegle(c.regle, date, emetteurNom), mot_cle: c.mot_cle, score: arrondi(c.score),
      personne: c.regle.personne ? c.regle.personne.affichage : '' }));
    // proches : tous les titres proches (pour choisir d'abord la personne, s'ils en nomment plusieurs).
    vide.proches = choix;
    const incertaine = proches.some(c => c.incertaine);
    if (proches.length === 1) {
      return { ...vide, nom: choix[0].nom, mot_cle: choix[0].mot_cle, raison: 'trouve', date, score: choix[0].score, personne_incertaine: incertaine };
    }
    if (proches.length <= CHOIX_MAX) return { ...vide, raison: 'choix', date, choix, personne_incertaine: incertaine };
    return { ...vide, raison: 'trop_proches', date, choix: choix.slice(0, CHOIX_MAX), personne_incertaine: incertaine };
  }

  return { analyser, valeurRetenue, proposer };
})();
