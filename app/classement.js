'use strict';

// Classement des scans, étape 1 (05/11/2026) : lecture du tableur « Classement documents
// administratifs » et de la STRUCTURE du Doc « Architecture officielle des archives », sans DOM.
// Ces deux fichiers sont choisis une fois par Max (sélecteur Google, droit drive.file) et lus à
// chaque besoin, sur le téléphone. Ils contiennent de vrais noms : rien n'en est copié ailleurs
// (ni journal, ni console). Ce module ne crée, ne nomme et ne range RIEN : il lit et vérifie.
const classement = (() => {
  const separateurChemin = /\s+\/\s+/;

  // Comparaison sans accents ni majuscules ; le nom exact du Doc est toujours gardé à part.
  function cle(texte) {
    return String(texte || '').normalize('NFD').replace(/[̀-ͯ]/g, '')
      .toLowerCase().replace(/\s+/g, ' ').trim();
  }

  // « Prenom_fictif (aucun sous-dossier pour l'instant) » → « Prenom_fictif ».
  function nomDossier(texte) {
    return String(texte || '').replace(/\u000b/g, ' ').split('(')[0].replace(/\s+/g, ' ').trim();
  }

  function texteParagraphe(paragraphe) {
    return (paragraphe.elements || []).map(element => element.textRun?.content || '').join('')
      .replace(/\n$/, '');
  }

  // Sections jamais lues comme des dossiers : les règles pour Cap, et les archives faites à la
  // main (« 00_A_CLASSER (le premier) »), que Cap ne crée jamais.
  function sectionIgnoree(titre) {
    const texte = cle(titre);
    return texte.startsWith('regles pour cap') || texte.startsWith('00_a_classer');
  }

  // Structure du Doc (API Docs) → arbre : un titre de niveau 2 = un dossier principal ; dessous,
  // une puce par sous-dossier, un retrait (nestingLevel) par niveau. Tout le reste est ignoré.
  function analyserArchitecture(document) {
    const racine = { nom: '', enfants: [] };
    const doutes = [];
    let principal = null;
    let pile = [];
    let ignorees = 0;
    for (const bloc of document?.body?.content || []) {
      const paragraphe = bloc.paragraph;
      if (!paragraphe) continue;
      const style = paragraphe.paragraphStyle?.namedStyleType || 'NORMAL_TEXT';
      const texte = texteParagraphe(paragraphe);
      if (/^(HEADING_\d|TITLE|SUBTITLE)$/.test(style)) {
        principal = null;
        pile = [];
        if (style !== 'HEADING_2') continue;
        if (sectionIgnoree(texte)) { ignorees++; continue; }
        const nom = nomDossier(texte);
        if (!nom) continue;
        principal = ajouterEnfant(racine, nom, doutes);
        continue;
      }
      if (!paragraphe.bullet || !principal) continue;
      const nom = nomDossier(texte);
      if (!nom) continue;
      const niveau = Number(paragraphe.bullet.nestingLevel || 0);
      const parent = niveau === 0 ? principal : pile[niveau - 1];
      if (!parent) {
        doutes.push({ type: 'niveau_saute', nom });
        continue;
      }
      pile[niveau] = ajouterEnfant(parent, nom, doutes);
      pile.length = niveau + 1;
    }
    return { racine, doutes, sections_ignorees: ignorees };
  }

  // Deux noms identiques sans accents ni majuscules au même endroit : doute, jamais de choix.
  function ajouterEnfant(parent, nom, doutes) {
    const existant = parent.enfants.find(enfant => cle(enfant.nom) === cle(nom));
    if (existant) {
      existant.double = true;
      doutes.push({ type: 'double', nom });
      return existant;
    }
    const enfant = { nom, enfants: [] };
    parent.enfants.push(enfant);
    return enfant;
  }

  function compterDossiers(noeud) {
    return noeud.enfants.reduce((total, enfant) => total + 1 + compterDossiers(enfant), 0);
  }

  // Valeurs de la première feuille → lignes du tableur. Première ligne = en-têtes ; colonnes dans
  // l'ordre : Mot-clé repéré, Organisme, Chemin de destination, Type de document, Modèle de titre.
  function analyserTableur(valeurs) {
    const lignes = [];
    const ignorees = [];
    (valeurs || []).slice(1).forEach((brute, indice) => {
      const [mot_cle, organisme, chemin, type, modele] = Array.from({ length: 5 },
        (_, colonne) => String(brute?.[colonne] ?? '').trim());
      const numero = indice + 2;
      if (!mot_cle && !chemin && !modele) return;
      if (!mot_cle || !chemin || !modele) { ignorees.push({ numero, raison: 'incomplete' }); return; }
      const morceaux = chemin.split(separateurChemin).map(morceau => morceau.trim()).filter(Boolean);
      lignes.push({ numero, mot_cle, organisme, chemin: morceaux, type, modele });
    });
    return { lignes, ignorees };
  }

  // Le chemin du tableur existe-t-il dans le Doc ? Renvoie les noms EXACTS du Doc (accents
  // compris) pour chaque niveau, ou la raison du refus. Dans le doute, on refuse.
  function verifierChemin(morceaux, architecture) {
    let noeud = architecture.racine;
    const noms = [];
    for (const morceau of morceaux) {
      const trouves = noeud.enfants.filter(enfant => cle(enfant.nom) === cle(morceau));
      if (!trouves.length) return { ok: false, raison: 'absent_du_doc', niveau: noms.length };
      if (trouves.length > 1 || trouves[0].double) return { ok: false, raison: 'double_dans_le_doc', niveau: noms.length };
      noeud = trouves[0];
      noms.push(noeud.nom);
    }
    return noms.length ? { ok: true, noms } : { ok: false, raison: 'vide', niveau: 0 };
  }

  // Résumé de contrôle : des NOMBRES seulement (jamais un nom du Doc ni du tableur).
  function resumer(tableur, architecture) {
    const verifications = tableur.lignes.map(ligne => verifierChemin(ligne.chemin, architecture));
    return {
      lignes: tableur.lignes.length,
      lignes_ignorees: tableur.ignorees.length,
      dossiers_principaux: architecture.racine.enfants.length,
      dossiers: compterDossiers(architecture.racine),
      sections_ignorees: architecture.sections_ignorees,
      doutes_doc: architecture.doutes.length,
      chemins_trouves: verifications.filter(v => v.ok).length,
      chemins_absents: verifications.filter(v => !v.ok && v.raison === 'absent_du_doc').length,
      chemins_douteux: verifications.filter(v => !v.ok && v.raison !== 'absent_du_doc').length
    };
  }

  function texteResume(resume) {
    return [
      `Tableur : ${resume.lignes} ligne(s) lue(s)${resume.lignes_ignorees ? `, ${resume.lignes_ignorees} incomplète(s) ignorée(s)` : ''}.`,
      `Doc : ${resume.dossiers_principaux} dossier(s) principal(aux), ${resume.dossiers} dossier(s) en tout.`,
      `Parties écartées (règles pour Cap, 00_A_CLASSER le premier) : ${resume.sections_ignorees}.`,
      `Chemins du tableur trouvés dans le Doc : ${resume.chemins_trouves} sur ${resume.lignes}`
        + ` (absents : ${resume.chemins_absents}, douteux : ${resume.chemins_douteux}).`,
      resume.doutes_doc ? `Doutes dans le Doc (noms en double, niveaux sautés) : ${resume.doutes_doc}.` : 'Aucun doute dans le Doc.'
    ].join('\n');
  }

  // ----- Lecture dans le Drive (fichiers choisis par Max) -----

  async function lireJson(url) {
    return (await googleConnexion.appeler(url)).json();
  }

  async function lireTableur(id) {
    const base = `https://sheets.googleapis.com/v4/spreadsheets/${encodeURIComponent(id)}`;
    const infos = await lireJson(`${base}?fields=sheets.properties.title`);
    const titre = infos.sheets?.[0]?.properties?.title;
    if (!titre) throw new Error('Le tableur de classement n’a aucune feuille lisible.');
    // Première feuille, quel que soit son nom.
    const plage = `'${titre.replace(/'/g, "''")}'!A:E`;
    const donnees = await lireJson(`${base}/values/${encodeURIComponent(plage)}?valueRenderOption=FORMATTED_VALUE`);
    return analyserTableur(donnees.values || []);
  }

  async function lireArchitecture(id) {
    const champs = 'body.content(paragraph(paragraphStyle.namedStyleType,bullet.nestingLevel,elements.textRun.content))';
    const document = await lireJson(`https://docs.googleapis.com/v1/documents/${encodeURIComponent(id)}?fields=${encodeURIComponent(champs)}`);
    return analyserArchitecture(document);
  }

  async function fichierChoisi(role) {
    return googlePicker.dossierChoisi(role) || await googlePicker.retrouverDepuisDrive(role);
  }

  // Lit les deux fichiers, à chaque appel (jamais de copie gardée).
  async function lire() {
    const architecture = await fichierChoisi('architecture');
    const tableur = await fichierChoisi('tableur_classement');
    if (!architecture || !tableur) {
      throw new Error('Choisis d’abord le Doc d’architecture et le tableur de classement dans « Réglages du Drive », '
        + 'avec Cap ouvert dans Chrome.');
    }
    const [lignes, arbre] = await Promise.all([lireTableur(tableur.id), lireArchitecture(architecture.id)]);
    return { tableur: lignes, architecture: arbre, resume: resumer(lignes, arbre) };
  }

  return { cle, nomDossier, analyserArchitecture, analyserTableur, verifierChemin, resumer, texteResume, lire };
})();
