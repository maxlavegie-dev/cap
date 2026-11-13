'use strict';

// Commandes vocales, étape 1 (08/11/2026, accord de Max) : Cap lit lui-même le tableur « Commandes vocales » de Max.
// Depuis 13h (option 4) : avec le compte Cap, à qui Max l'a partagé (voir lireAvecCompteCap, en bas).
// Avant (gardé) : choisi une fois dans Chrome, droit drive.file, comme le tableur de classement.
// Une copie RÉDUITE est gardée sur le téléphone, et seulement là :
// - seules les lignes qui ont un « Code commande » (ex. NAV-05, COMMUN) ;
// - jamais les lignes marquées « RETIRER » (colonne des remarques) ;
// - jamais les lignes de noms de personnes (blocs « Cible » et « Nom d'appel ») : les vrais prénoms restent dans le Drive ;
// - quatre champs par ligne : code, commande, bloc, formulation.
// Ce fichier n'appelle aucune IA et rien ici n'est jamais envoyé à l'IA (vérifié par les tests).
// Les résumés affichés ne contiennent que des NOMBRES.
const commandesVocales = (() => {
  const CLE_COPIE = 'cap_commandes_vocales_v1';
  const BLOCS_EXCLUS = ['cible', 'nom d appel'];
  // 08/11/2026 (étape 0, question 39) : « œ » et « æ » comptent comme « oe » et « ae » (« l'œil » = « l'oeil »).
  const plier = texte => String(texte || '').replace(/œ/g, 'oe').replace(/Œ/g, 'OE').replace(/æ/g, 'ae').replace(/Æ/g, 'AE')
    .normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ').trim();

  // Colonnes retrouvées par leur titre (première ligne), quel que soit leur ordre.
  function colonnes(entete) {
    const titres = (entete || []).map(plier);
    const trouver = (...motifs) => titres.findIndex(t => motifs.some(m => t.startsWith(m)));
    return {
      commande: trouver('commande'),
      bloc: trouver('bloc'),
      formulation: trouver('formulation'),
      code: trouver('code commande', 'code'),
      remarque: trouver('remarque')
    };
  }

  // valeurs : lignes du tableur (la première = les titres). Renvoie la copie réduite et un compte en nombres.
  function analyser(valeurs) {
    const lignesBrutes = Array.isArray(valeurs) ? valeurs : [];
    const col = colonnes(lignesBrutes[0]);
    if (col.code < 0 || col.formulation < 0) throw new Error('Le tableur « Commandes vocales » n’a pas les colonnes « Formulation » et « Code commande ».');
    const cellule = (ligne, i) => (i >= 0 && Array.isArray(ligne) ? String(ligne[i] ?? '').trim() : '');
    const compte = { lues: 0, gardees: 0, retirees: 0, noms_exclus: 0, sans_code: 0, codes: 0 };
    const lignes = [];
    const codes = new Set();
    for (const ligne of lignesBrutes.slice(1)) {
      const formulation = cellule(ligne, col.formulation);
      const code = cellule(ligne, col.code).toUpperCase();
      if (!formulation && !code) continue;
      compte.lues++;
      if (/^retirer/i.test(cellule(ligne, col.remarque))) { compte.retirees++; continue; }
      const bloc = cellule(ligne, col.bloc);
      if (BLOCS_EXCLUS.includes(plier(bloc))) { compte.noms_exclus++; continue; }
      // 08/11/2026 (étape 0) : les blocs « Cible de titre / de personne / de document / de dossier » (écrits avec des
      // espaces réservés comme [PRÉNOM]) sont gardés, SAUF si une majuscule y reste hors des crochets : un vrai nom
      // pourrait s'y être glissé ; la ligne reste alors dans le Drive.
      if (/^cible/.test(plier(bloc)) && /[A-ZÀ-Þ]/.test(formulation.replace(/\[[^\]]*\]/g, ''))) { compte.noms_exclus++; continue; }
      if (!code || !formulation) { compte.sans_code++; continue; }
      // 08/11/2026 (étape 2) : les lignes « CONFLIT » sont gardées, marquées (Max tranchera ; aucune action d'ici là).
      const garde = { code, commande: cellule(ligne, col.commande), bloc, formulation };
      if (/^conflit/i.test(cellule(ligne, col.remarque))) garde.conflit = true;
      lignes.push(garde);
      codes.add(code);
    }
    compte.gardees = lignes.length;
    compte.codes = codes.size;
    return { lignes, compte };
  }

  function texteResume(compte, quand = '') {
    return [
      `Commandes vocales : ${compte.gardees} formulation(s) gardée(s) sur ce téléphone, ${compte.codes} code(s) de commande.`,
      `Écartées : ${compte.retirees} « à retirer », ${compte.noms_exclus} ligne(s) de noms (restées dans le Drive), ${compte.sans_code} sans code.`,
      quand ? `Lu le ${quand}.` : ''
    ].filter(Boolean).join('\n');
  }

  // Copie gardée sur le téléphone (localStorage seulement).
  function garder(stockage, analyse, maintenant) {
    const copie = { lu_le: new Date(maintenant).toISOString(), compte: analyse.compte, lignes: analyse.lignes };
    try { stockage.setItem(CLE_COPIE, JSON.stringify(copie)); } catch (erreur) {
      throw new Error('La copie des commandes vocales n’a pas pu être gardée sur ce téléphone (mémoire pleine ?).');
    }
    return copie;
  }

  function copie(stockage = (typeof localStorage !== 'undefined' ? localStorage : null)) {
    try {
      const c = JSON.parse(stockage.getItem(CLE_COPIE));
      return c && Array.isArray(c.lignes) ? c : null;
    } catch (erreur) { return null; }
  }

  function oublier(stockage = (typeof localStorage !== 'undefined' ? localStorage : null)) {
    try { stockage.removeItem(CLE_COPIE); } catch (erreur) { /* rien */ }
  }

  // Lecture du tableur choisi (première feuille, colonnes A à F), puis copie réduite sur le téléphone.
  async function lireEtGarder({
    fichier = async () => googlePicker.dossierChoisi('commandes_vocales') || await googlePicker.retrouverDepuisDrive('commandes_vocales'),
    appeler = url => googleConnexion.appeler(url),
    stockage = (typeof localStorage !== 'undefined' ? localStorage : null),
    maintenant = Date.now()
  } = {}) {
    const choisi = await fichier();
    if (!choisi) throw new Error('Choisis d’abord le tableur « Commandes vocales » dans « Réglages du Drive », avec Cap ouvert dans Chrome.');
    const base = `https://sheets.googleapis.com/v4/spreadsheets/${encodeURIComponent(choisi.id)}`;
    const infos = await (await appeler(`${base}?fields=sheets.properties.title`)).json();
    const titre = infos.sheets?.[0]?.properties?.title;
    if (!titre) throw new Error('Le tableur « Commandes vocales » n’a aucune feuille lisible.');
    const plage = `'${titre.replace(/'/g, "''")}'!A:F`;
    const donnees = await (await appeler(`${base}/values/${encodeURIComponent(plage)}?valueRenderOption=FORMATTED_VALUE`)).json();
    return garder(stockage, analyser(donnees.values || []), maintenant);
  }

  // ----- 08/11/2026, 13h (option 4, accord de Max) : lecture avec le COMPTE CAP -----
  // Max a partagé le tableur avec le compte Cap, en lecture seule. Le compte Cap (droit drive.readonly, déjà accordé)
  // le retrouve par son nom exact et l'exporte en CSV (première feuille) par l'API Drive, en lecture seule : aucune
  // publication, aucune nouvelle autorisation, et ça marche dans l'application du téléphone (pas de fenêtre de choix).
  // La lecture par la fenêtre de choix (lireEtGarder) est gardée pour plus tard, après une publication.
  const NOM_TABLEUR = 'Commandes vocales';

  // CSV (export Google) → lignes de cellules : guillemets, virgules et retours à la ligne dans les cellules.
  function lireCsv(texte) {
    const lignes = [];
    let ligne = [];
    let cellule = '';
    let entreGuillemets = false;
    const s = String(texte || '').replace(/^\uFEFF/, '');
    for (let i = 0; i < s.length; i++) {
      const c = s[i];
      if (entreGuillemets) {
        if (c === '"' && s[i + 1] === '"') { cellule += '"'; i++; }
        else if (c === '"') entreGuillemets = false;
        else cellule += c;
      } else if (c === '"') entreGuillemets = true;
      else if (c === ',') { ligne.push(cellule); cellule = ''; }
      else if (c === '\n' || c === '\r') {
        if (c === '\r' && s[i + 1] === '\n') i++;
        ligne.push(cellule); lignes.push(ligne); ligne = []; cellule = '';
      } else cellule += c;
    }
    if (cellule || ligne.length) { ligne.push(cellule); lignes.push(ligne); }
    return lignes;
  }

  async function lireAvecCompteCap({
    compte = (typeof googleCompteRelations !== 'undefined' ? googleCompteRelations : null),
    stockage = (typeof localStorage !== 'undefined' ? localStorage : null),
    maintenant = Date.now(),
    // 11/11/2026 (c146) : le téléphone a-t-il du réseau ? (remplaçable dans les tests)
    enLigne = () => (typeof navigator === 'undefined' || navigator.onLine !== false)
  } = {}) {
    if (!compte) throw new Error('Le compte Cap n’est pas disponible dans cette version.');
    if (typeof compte.adresse === 'function' && !compte.adresse()) {
      throw new Error('Identifiant du compte Cap absent : écris-le d’abord dans « Réglages du Drive ».');
    }
    // 11/11/2026 (accord de Max, c146, ligne 120) : SANS RÉSEAU, la vraie cause, sans « Autoriser… » ; la copie gardée reste utilisée.
    if (!enLigne()) throw new Error('Pas de réseau : je ne peux pas relire les commandes vocales. Reconnecte le téléphone, puis « Lire les commandes vocales ». Les commandes déjà gardées restent utilisées.');
    if (typeof compte.connecte === 'function' && !compte.connecte()) {
      throw new Error('Le compte Cap n’est pas connecté (ou la connexion a expiré, au bout d’environ 1 h). Touche « Autoriser la lecture du compte Cap », puis « Lire les commandes vocales ».');
    }
    const q = `name='${NOM_TABLEUR}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false`;
    const liste = await (await compte.appeler(`https://www.googleapis.com/drive/v3/files?q=${encodeURIComponent(q)}&fields=files(id)&pageSize=10`)).json();
    const trouves = Array.isArray(liste.files) ? liste.files : [];
    if (!trouves.length) {
      throw new Error('Le compte Cap ne voit aucun tableur « Commandes vocales » : partage-le avec le compte Cap (lecture seule) depuis ton Drive.');
    }
    if (trouves.length > 1) {
      throw new Error(`Le compte Cap voit ${trouves.length} tableurs « Commandes vocales » : garde-en un seul partagé avec lui.`);
    }
    const reponse = await compte.appeler(`https://www.googleapis.com/drive/v3/files/${encodeURIComponent(trouves[0].id)}/export?mimeType=${encodeURIComponent('text/csv')}`);
    return garder(stockage, analyser(lireCsv(await reponse.text())), maintenant);
  }

  // ----- 08/11/2026 (étape 2, accord de Max) : reconnaître la commande dans une phrase (code pur, sans IA) -----
  // Pour chaque code, les formulations du tableur sont rangées selon leur bloc :
  // - « action » : verbes et tournures (« Verbe… », « Tournure… ») ;
  // - « cible » : ce qui est visé (« Mot-clé », « Écran cible ») ;
  // - « l'un ou l'autre » : « Variante de transcription » et « Début de phrase » ;
  // - ignorés : compléments (« dans Cap », « tout de suite »…) et déterminants.
  // Les lignes « COMMUN » d'une commande (ex. « Navigation ») servent à tous les codes qui ont cette commande.
  // Une phrase vise un code si elle contient (mots entiers, sans accents ni ponctuation) une action ET une cible du
  // code (deux formulations différentes) ; un code sans cible (ex. arrêter la dictée) se contente d'une action.
  // Le meilleur code est celui dont les mots reconnus sont les plus longs ; une égalité est signalée, jamais tranchée.
  // Rien n'est fait ici : seulement « quelle commande ? » (les actions viendront à l'étape 4, avec l'accord de Max).
  const motsDe = texte => ` ${plier(texte)} `;
  // 08/11/2026 (étape 0) : ancien moteur de l'étape 2 GARDÉ tel quel ci-dessous (sorteEtape2, preparerEtape2,
  // reconnaitreEtape2), plus utilisé ; le nouveau moteur (plus bas) le remplace sous le nom « reconnaitre ».
  function sorteEtape2(bloc) {
    const b = plier(bloc);
    if (/^(complement|determinant)/.test(b)) return '';
    if (/^(verbe|tournure)/.test(b)) return 'action';
    if (/^(mot cle|ecran cible)/.test(b)) return 'cible';
    if (/^(variante|debut)/.test(b)) return 'les_deux';
    return '';
  }
  function preparerEtape2(lignes) {
    const sorte = sorteEtape2;
    const codes = new Map();
    const communs = new Map();
    for (const l of lignes || []) {
      const s = sorte(l.bloc);
      const terme = plier(l.formulation);
      if (!s || !terme) continue;
      if (l.code === 'COMMUN') {
        if (!communs.has(l.commande)) communs.set(l.commande, []);
        communs.get(l.commande).push({ terme, sorte: s, conflit: Boolean(l.conflit) });
        continue;
      }
      if (!codes.has(l.code)) codes.set(l.code, { code: l.code, commandes: new Set(), termes: [] });
      const c = codes.get(l.code);
      if (l.commande) c.commandes.add(l.commande);
      c.termes.push({ terme, sorte: s, conflit: Boolean(l.conflit) });
    }
    for (const c of codes.values()) {
      for (const commande of c.commandes) for (const t of communs.get(commande) || []) c.termes.push(t);
      c.aDesCibles = c.termes.some(t => t.sorte === 'cible');
      // Libellé : la commande la plus précise (pas « Navigation »).
      c.libelle = [...c.commandes].sort((x, y) => (x === 'Navigation') - (y === 'Navigation'))[0] || c.code;
    }
    return codes;
  }
  let indexEtape2 = null;
  let indexDeEtape2 = null;
  function reconnaitreEtape2(phrase, lignes = (copie() || {}).lignes) {
    if (!lignes || !lignes.length) return { statut: 'pas_de_tableur' };
    if (indexDeEtape2 !== lignes) { indexEtape2 = preparerEtape2(lignes); indexDeEtape2 = lignes; }
    const index = indexEtape2;
    const p = motsDe(phrase);
    if (!p.trim()) return { statut: 'rien' };
    const resultats = [];
    for (const c of index.values()) {
      const trouves = c.termes.filter(t => p.includes(` ${t.terme} `));
      const plusLong = sortes => trouves.filter(t => sortes.includes(t.sorte)).sort((x, y) => y.terme.length - x.terme.length)[0] || null;
      const cible = plusLong(['cible', 'les_deux']);
      const dedans = (grand, petit) => ` ${grand} `.includes(` ${petit} `);
      const action = trouves.filter(t => ['action', 'les_deux'].includes(t.sorte) && t !== cible && !(cible && dedans(cible.terme, t.terme)))
        .sort((x, y) => y.terme.length - x.terme.length)[0] || null;
      let retenus = null;
      if (c.aDesCibles) {
        if (cible && action && cible.terme !== action.terme) retenus = [action, cible];
        else {
          // Une variante entière qui contient déjà un verbe du code (ex. « ouvre l'autre ») suffit seule.
          const entiere = trouves.filter(t => t.sorte === 'les_deux' && c.termes.some(v => v.sorte === 'action' && v.terme !== t.terme && dedans(t.terme, v.terme)))
            .sort((x, y) => y.terme.length - x.terme.length)[0];
          if (entiere) retenus = [entiere];
        }
      } else if (plusLong(['action', 'les_deux'])) retenus = [plusLong(['action', 'les_deux'])];
      if (!retenus) continue;
      resultats.push({ code: c.code, commande: c.libelle, mots: retenus.map(t => t.terme), score: retenus.reduce((s, t) => s + t.terme.length, 0),
        conflit: retenus.some(t => t.conflit) });
    }
    if (!resultats.length) return { statut: 'rien' };
    resultats.sort((x, y) => y.score - x.score);
    const egaux = resultats.filter(r => r.score === resultats[0].score);
    if (egaux.length > 1) return { statut: 'ambigu', codes: egaux.map(r => r.code), commandes: egaux.map(r => r.commande) };
    return { statut: 'reconnu', ...resultats[0] };
  }


  // ===== 08/11/2026 (accord de Max, étape 0 du codage) : NOUVEAU MOTEUR (code pur, sans IA) =====
  // Mêmes règles que l'étape 2 (une action ET une cible du même code, le plus long gagne, égalité signalée), plus :
  // - « Expression … » (expression complète, de pause, de silence…) : la formulation seule suffit ;
  // - « Cible de titre / de personne / de document / de dossier » : des cibles ;
  // - espaces réservés : [NOMBRE] (0 à 100, en chiffres ou en lettres, « pour cent » permis), [DURÉE] (« 10 secondes »,
  //   « 2 minutes 40 »), [TITRE], [PRÉNOM], [DOSSIER], [SUJET] (quelques mots) : leur valeur est rendue dans « valeurs » ;
  // - hésitations : « euh », « heu »… retirés, mots ou groupes répétés gardés une fois (« mets le, mets le volume à, à 75 ») ;
  //   pour un chiffre, c'est le dernier dit qui compte ;
  // - codes où le verbe seul suffit (décision de Max : pause MUS-05, reprise MUS-06) ;
  // - la fenêtre ouverte départage une égalité (questions 37 et 25) : lecteur → MUS, visionneuse → VIS ;
  // - phrase qui commence comme une commande sans être complète (« ouvre », « mets-moi ») : statut « incomplet ».
  // 08/11/2026 (correction A, accord de Max) : + NAV-09 (« ferme » seul ferme l'écran en cours, question 12). Le verbe
  // seul ne compte QUE si la phrase n'a rien d'autre que ce verbe et de petits mots (« ferme », « ferme-le », « je veux
  // que tu fermes ») : « rappelle-moi de fermer le gaz » reste une tâche. Avant : new Set(['MUS-05', 'MUS-06']), verbe
  // seul accepté n'importe où dans la phrase.
  const VERBE_SEUL = new Set(['MUS-05', 'MUS-06', 'NAV-09', 'MUS-14', 'MUS-15']); // 08/11/2026 (étape 2a) : + « rejoue », « recommence » (question 17) seuls
  // 08/11/2026 (étape 2a) : pour ces deux-là, SEULEMENT ces verbes (le bloc a aussi « reviens », « retourne », trop larges seuls).
  const VERBE_SEUL_LIMITE = { 'MUS-14': /^rejou/, 'MUS-15': /^recommen/ };
  // 08/11/2026 (étape 2a, question 37) : « le suivant », « le précédent » seuls (phrase entière) : la fenêtre ouverte décide.
  // 09/11/2026 (essai de Max sur le Pixel) : + NAV-13. Dans le vrai tableur, « mes tâches », « ma to-do »… sont des « Écran
  // cible » (verbe d'ouverture COMMUN devant) : dit SEUL, c'était incomplet, donc rangé dans « À trier ». Maintenant la
  // cible seule (phrase entière, rien d'autre) ouvre l'écran des tâches. Avant : new Set(['MUS-12', 'MUS-13', 'VIS-04', 'VIS-05']).
  const CIBLE_SEULE = new Set(['MUS-12', 'MUS-13', 'VIS-04', 'VIS-05', 'NAV-13']);
  const NOMBRES = { zero: 0, un: 1, une: 1, deux: 2, trois: 3, quatre: 4, cinq: 5, six: 6, sept: 7, huit: 8, neuf: 9, dix: 10,
    onze: 11, douze: 12, treize: 13, quatorze: 14, quinze: 15, seize: 16, vingt: 20, trente: 30, quarante: 40, cinquante: 50,
    soixante: 60, cent: 100 };
  const MOT_NOMBRE = `(?:${Object.keys(NOMBRES).join('|')}|et)`;
  const NOMBRE = `(?:\\d{1,3}|${MOT_NOMBRE}(?: ${MOT_NOMBRE}){0,3})`;
  const UNITE_MIN = '(?:minutes?|mn|min)';
  const UNITE_SEC = '(?:secondes?|sec|s)';
  const DUREE = `(?:${NOMBRE} ${UNITE_MIN}(?: (?:et )?${NOMBRE}(?: ${UNITE_SEC})?)?|${NOMBRE} ${UNITE_SEC})`;
  const LIBRE = '[a-z0-9]+(?: [a-z0-9]+){0,7}';
  const RESERVES = { nombre: NOMBRE, duree: DUREE, titre: LIBRE, prenom: LIBRE, dossier: LIBRE, sujet: LIBRE };
  // 08/11/2026 (étape 3a) : petits mots retirés au début et à la fin d'un titre dit (« mets-moi le … s'il te plaît »).
  const DEBUT_VIDE = new Set(['moi', 'le', 'la', 'les', 'l', 'un', 'une', 'du', 'de', 'd']);
  const FIN_VIDE = new Set(['stp', 'svp', 'plait', 'il', 'te', 's', 'maintenant', 'merci']);
  const MOTS_VIDES = new Set(['le', 'la', 'les', 'l', 'moi', 'toi', 'ca', 'un', 'une', 'des', 'du', 'de', 'd', 'en', 'y', 'nous',
    's', 'il', 'te', 'plait', 'vous', 'stp', 'svp', 'donc', 'alors', 'maintenant', 'vite']);

  // « soixante quinze » → 75 ; « 75 » → 75 ; hors 0 à 100 → null.
  function lireNombre(texte) {
    const t = plier(texte);
    if (/^\d+$/.test(t)) { const n = Number(t); return n <= 100 ? n : null; }
    let total = 0;
    for (const mot of t.split(' ')) {
      if (mot === 'et') continue;
      if (!(mot in NOMBRES)) return null;
      const v = NOMBRES[mot];
      if (v === 100) total = (total || 1) * 100;
      else if (v === 20 && total % 100 === 4) total += 76; // quatre vingt(s) = 80
      else if (v >= 1 && v <= 16 && total % 10 === 0 && total % 100 >= 60) total += v; // soixante dix, quatre vingt quinze
      else total += v;
    }
    return total <= 100 ? total : null;
  }
  // « 2 minutes 40 » → 160 ; « 30 secondes » → 30.
  function lireDuree(texte) {
    const t = plier(texte);
    const m = new RegExp(`^(${NOMBRE}) ${UNITE_MIN}(?: (?:et )?(${NOMBRE})(?: ${UNITE_SEC})?)?$`).exec(t);
    if (m) { const min = lireNombre(m[1]); const sec = m[2] ? lireNombre(m[2]) : 0; return min === null || sec === null ? null : min * 60 + sec; }
    const s = new RegExp(`^(${NOMBRE}) ${UNITE_SEC}$`).exec(t);
    return s ? lireNombre(s[1]) : null;
  }

  // Hésitations : « euh »… retirés ; groupes de 1 à 4 mots répétés à la suite gardés une fois.
  function sansHesitations(plie) {
    let mots = plie.split(' ').filter(m => m && !/^(euh+|heu+|hum+|bah|ben|hein)$/.test(m));
    for (let n = 4; n >= 1; n--) {
      const garde = [];
      for (let i = 0; i < mots.length; i++) {
        const avant = garde.slice(-n).join(' ');
        const groupe = mots.slice(i, i + n).join(' ');
        if (garde.length >= n && groupe === avant && i + n <= mots.length) { i += n - 1; continue; }
        garde.push(mots[i]);
      }
      mots = garde;
    }
    return mots.join(' ');
  }

  function sorte(bloc) {
    const b = plier(bloc);
    if (/^(complement|determinant)/.test(b)) return '';
    if (/^expression seule/.test(b)) return 'seule'; // 08/11/2026 (étape 2a) : compléments de Cap, phrase entière seulement
    if (/avec un mot cle seulement/.test(b)) return 'action_cible'; // 08/11/2026 : verbe jamais seul (toujours avec un mot-clé)
    if (/^expression/.test(b)) return 'complete';
    if (/^(verbe|tournure)/.test(b)) return 'action';
    if (/^(mot cle|ecran cible|cible)/.test(b)) return 'cible';
    if (/^(variante|debut)/.test(b)) return 'les_deux';
    return '';
  }

  // Une formulation → terme : texte plié, et motif si elle a des espaces réservés.
  // 08/11/2026 (correction B, accord de Max) : dans un mot-clé (cible ou variante), le petit mot est libre :
  // « mon eau », « ton eau » comptent comme « l'eau ». Un mot-clé fait d'un seul petit mot (« sa ») reste exact.
  const DETERMINANTS = ['le', 'la', 'l', 'les', 'un', 'une', 'des', 'du', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa',
    'ses', 'notre', 'votre', 'nos', 'vos', 'ce', 'cet', 'cette', 'ces', 'au', 'aux']; // 08/11/2026 (étape 3c) : + « au », « aux » (« reviens au précédent »)
  const GROUPE_DETERMINANTS = `(?:${DETERMINANTS.join('|')})`;
  // 08/11/2026 (correction C, accord de Max) : « ne » et « n' » sont ignorés (« je ne veux voir que l'eau »).
  const sansNe = plie => plie.split(' ').filter(m => m !== 'ne' && m !== 'n').join(' ');
  function terme(formulation, s, conflit) {
    const morceaux = String(formulation).split(/\[([^\]]+)\]/);
    // Avant le 08/11/2026 (corrections B et C) : if (morceaux.length === 1) return { terme: plier(formulation), sorte: s, conflit };
    if (morceaux.length === 1) {
      const plie = sansNe(plier(formulation));
      const mots = plie.split(' ');
      // Seulement un petit mot SUIVI d'un autre mot (« ouvre notre », variante de « ouvre autre », reste exact).
      const libre = (m, i) => DETERMINANTS.includes(m) && i < mots.length - 1;
      if ((s === 'cible' || s === 'les_deux') && mots.some(libre)) {
        let motif = mots.map((m, i) => (libre(m, i) ? GROUPE_DETERMINANTS : m)).join(' ');
        // 09/11/2026 (défauts 4 et 6 vus par Max : « document suivant », « morceau suivant » dits SANS « le ») : le petit
        // mot du DÉBUT devient facultatif quand il reste au moins deux mots après lui (« le document suivant »). Un
        // mot-clé court (« le suivant ») le garde obligatoire : « suivant » tout seul dans une phrase ne déclenche rien.
        if (libre(mots[0], 0) && mots.length >= 3) motif = `(?:${GROUPE_DETERMINANTS} )?${mots.slice(1).map((m, i) => (libre(m, i + 1) ? GROUPE_DETERMINANTS : m)).join(' ')}`;
        return { terme: plie, sorte: s, conflit, motif: new RegExp(` ${motif} `, 'g'), noms: [], longueur: plie.length };
      }
      return { terme: plie, sorte: s, conflit };
    }
    let motif = '';
    const noms = [];
    let longueur = 0;
    morceaux.forEach((m, i) => {
      if (i % 2 === 0) { const p = sansNe(plier(m)); if (p) { motif += ` ${p.replace(/ /g, ' ')}`; longueur += p.length; } return; }
      const nom = plier(m).replace(/ /g, '');
      const reserve = RESERVES[nom];
      if (!reserve) { motif += ` ${plier(m)}`; return; } // crochets inconnus : gardés comme des mots
      noms.push(nom);
      longueur += 5;
      const dernier = i === morceaux.length - 2 && !plier(morceaux[i + 1]);
      const groupe = reserve === LIBRE && !dernier ? '[a-z0-9]+(?: [a-z0-9]+){0,7}?' : reserve;
      motif += ` (${groupe})${nom === 'nombre' ? '(?: pour cent)?' : ''}`;
    });
    const plie = plier(formulation.replace(/\[[^\]]+\]/g, ' '));
    // 08/11/2026 (étape 3a) : « [TITRE] » tout seul : sa valeur sera le reste de la phrase après le verbe (voir reconnaitre).
    const libreSeul = !plie && noms.length === 1 && RESERVES[noms[0]] === LIBRE;
    return { terme: plie || noms.join(' '), sorte: s, conflit, motif: new RegExp(`${motif} `, 'g'), noms, longueur, libreSeul };
  }

  // 08/11/2026 (étape 2a) : décisions de Max (questions 10 et 16) pas écrites dans le tableur, ajoutées par Cap.
  // « Expression seule » : seulement si la phrase n'a rien d'autre (« silence », « un autre »).
  const SUPPLEMENTS = [
    // 09/11/2026 (décision de Max, bloc c74) : « mets la musique / la zik / la zic » = le lecteur s'allume avec la playlist
    // par défaut (« Afficher le lecteur » ; si une musique joue déjà : le lecteur seulement). Phrase entière seulement.
    { code: 'MUS-19', commande: 'Afficher le lecteur', bloc: 'Expression seule (Cap)', formulation: 'mets la musique' },
    { code: 'MUS-19', commande: 'Afficher le lecteur', bloc: 'Expression seule (Cap)', formulation: 'mets la zik' },
    { code: 'MUS-19', commande: 'Afficher le lecteur', bloc: 'Expression seule (Cap)', formulation: 'mets la zic' },
    // 09/11/2026 (accord de Max, chantiers, séance 1) : l'écran « Chantiers » (code de Cap NAV-CH), phrase entière seulement.
    { code: 'NAV-CH', commande: 'Ouvrir les chantiers', bloc: 'Expression seule (Cap)', formulation: 'ouvre les chantiers' },
    { code: 'NAV-CH', commande: 'Ouvrir les chantiers', bloc: 'Expression seule (Cap)', formulation: 'ouvre mes chantiers' },
    { code: 'NAV-CH', commande: 'Ouvrir les chantiers', bloc: 'Expression seule (Cap)', formulation: 'affiche les chantiers' },
    { code: 'NAV-CH', commande: 'Ouvrir les chantiers', bloc: 'Expression seule (Cap)', formulation: 'montre les chantiers' },
    { code: 'NAV-CH', commande: 'Ouvrir les chantiers', bloc: 'Expression seule (Cap)', formulation: 'montre-moi les chantiers' },
    { code: 'NAV-CH', commande: 'Ouvrir les chantiers', bloc: 'Expression seule (Cap)', formulation: 'les chantiers' },
    { code: 'NAV-CH', commande: 'Ouvrir les chantiers', bloc: 'Expression seule (Cap)', formulation: 'mes chantiers' },
    { code: 'MUS-10', commande: 'Couper le son', bloc: 'Expression seule (Cap)', formulation: 'tais-toi' },
    { code: 'MUS-10', commande: 'Couper le son', bloc: 'Expression seule (Cap)', formulation: 'silence' },
    { code: 'MUS-12', commande: 'Passer au morceau suivant', bloc: 'Expression seule (Cap)', formulation: 'un autre' },
    { code: 'MUS-12', commande: 'Passer au morceau suivant', bloc: 'Expression complète (Cap)', formulation: 'un autre morceau' },
    { code: 'MUS-12', commande: 'Passer au morceau suivant', bloc: 'Expression complète (Cap)', formulation: 'une autre chanson' },
    // 08/11/2026 (correction, règle de Max) : « arrête / stop / coupe / éteins… » + un mot-clé (la musique, le morceau,
    // le player… ; le son, le volume) arrêtent la musique ou coupent le son. Dans le tableur, ces verbes sont tous marqués
    // RETIRER (« garder seulement avec une cible ») : Cap ignore les lignes RETIRER, donc « arrête la musique » donnait
    // « Dictée arrêtée. » (défaut constaté par Max sur c50). Remis ici comme VERBES : jamais seuls (MUS-07 et MUS-10 ont
    // des mots-clés et ne sont pas des codes « verbe seul ») ; « arrête » ou « stop » seuls restent la dictée (DIC-02).
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'arrête' },
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'arrête-moi' },
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'arrêtes' },
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'arrete' },
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'stop' },
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'stoppe' },
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'stope' },
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'coupe' },
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'coupe-moi' },
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'éteins' },
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'eteins' },
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'termine' },
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'finis' },
    { code: 'MUS-07', commande: 'Arrêter la musique', bloc: 'Verbe d’arrêt, avec un mot-clé seulement (Cap)', formulation: 'fais taire' },
    { code: 'MUS-10', commande: 'Couper le son', bloc: 'Verbe de coupure, avec un mot-clé seulement (Cap)', formulation: 'coupe' },
    { code: 'MUS-10', commande: 'Couper le son', bloc: 'Verbe de coupure, avec un mot-clé seulement (Cap)', formulation: 'coupe-moi' },
    { code: 'MUS-10', commande: 'Couper le son', bloc: 'Verbe de coupure, avec un mot-clé seulement (Cap)', formulation: 'éteins' },
    { code: 'MUS-10', commande: 'Couper le son', bloc: 'Verbe de coupure, avec un mot-clé seulement (Cap)', formulation: 'eteins' },
    { code: 'MUS-10', commande: 'Couper le son', bloc: 'Verbe de coupure, avec un mot-clé seulement (Cap)', formulation: 'fais taire' },
  ];
  function preparer(lignes) {
    const codes = new Map();
    const communs = new Map();
    for (const l of [...(lignes || []), ...((lignes || []).length ? SUPPLEMENTS : [])]) {
      const s = sorte(l.bloc);
      if (!s || !plier(l.formulation)) continue;
      const t = terme(l.formulation, s, Boolean(l.conflit));
      // 09/11/2026 (accord de Max, partie C) : une formulation du bloc « Écran cible » d'une commande de navigation peut se
      // dire SEULE (phrase entière) : « l'agenda », « mes notes »… Avant : seulement NAV-13 (« mes tâches »).
      if (/^ecran cible/.test(plier(l.bloc || '')) && /^NAV-/.test(l.code || '')) t.ecranSeul = true;
      if (l.apprise) t.apprise = true; // 09/11/2026 (petit tableur) : phrase apprise (choix de Max)
      if (l.code === 'COMMUN') {
        if (!communs.has(l.commande)) communs.set(l.commande, []);
        communs.get(l.commande).push(t);
        continue;
      }
      if (!codes.has(l.code)) codes.set(l.code, { code: l.code, commandes: new Set(), termes: [] });
      const c = codes.get(l.code);
      if (l.commande) c.commandes.add(l.commande);
      c.termes.push(t);
    }
    for (const c of codes.values()) {
      for (const commande of c.commandes) for (const t of communs.get(commande) || []) c.termes.push(t);
      c.aDesCibles = c.termes.some(t => t.sorte === 'cible');
      c.libelle = [...c.commandes].sort((x, y) => (x === 'Navigation') - (y === 'Navigation'))[0] || c.code;
    }
    return codes;
  }

  // Cherche un terme dans la phrase (« p » : phrase pliée entourée d'espaces). Renvoie la trouvaille ou null.
  function chercher(t, p) {
    if (!t.motif) return p.includes(` ${t.terme} `) ? { t, longueur: t.terme.length, valeurs: {} } : null;
    t.motif.lastIndex = 0;
    let m;
    let dernier = null;
    while ((m = t.motif.exec(p)) !== null) { dernier = m; t.motif.lastIndex = m.index + 1; }
    if (!dernier) return null;
    // 08/11/2026 (étape 3a) : « [TITRE] » seul : sa valeur est calculée ensuite (reste de la phrase), pas ici.
    if (t.libreSeul) return { t, longueur: t.longueur, valeurs: {} };
    const valeurs = {};
    t.noms.forEach((nom, i) => {
      const brut = dernier[i + 1];
      if (nom === 'nombre') { const n = lireNombre(brut); if (n !== null) valeurs.nombre = n; }
      else if (nom === 'duree') { const d = lireDuree(brut); if (d !== null) valeurs.duree = d; }
      else if (brut.split(' ').every(m => MOTS_VIDES.has(m))) valeurs.vide = true; // « mets-moi s'il te plaît » : pas un titre
      else valeurs[nom] = brut;
    });
    if (t.noms.includes('nombre') && !('nombre' in valeurs)) return null;
    if (t.noms.includes('duree') && !('duree' in valeurs)) return null;
    if (valeurs.vide) return null;
    return { t, longueur: t.longueur, valeurs };
  }

  let index = null;
  let indexDe = null;
  // contexte : { ouvert: 'lecteur' | 'visionneuse' | '' } (la fenêtre affichée).
  function reconnaitre(phrase, lignes = (copie() || {}).lignes, contexte = {}) {
    if (!lignes || !lignes.length) return { statut: 'pas_de_tableur' };
    if (indexDe !== lignes) { index = preparer(lignes); indexDe = lignes; }
    // Avant le 08/11/2026 (correction C) : const propre = sansHesitations(plier(phrase));
    const brut = sansHesitations(plier(phrase));
    if (!brut) return { statut: 'rien' };
    // « ne … pas / jamais / point / rien » : une vraie négation (« ne ferme pas ça ») n'est jamais une commande.
    if (/(^| )(ne|n)( |$)/.test(brut) && /(^| )(pas|jamais|point|rien)( |$)/.test(brut)) return { statut: 'rien' };
    const propre = sansNe(brut);
    if (!propre) return { statut: 'rien' };
    const p = ` ${propre} `;
    const dedans = (grand, petit) => ` ${grand} `.includes(` ${petit} `);
    const resultats = [];
    for (const c of index.values()) {
      const trouves = [];
      for (const t of c.termes) { const r = chercher(t, p); if (r) trouves.push(r); }
      if (!trouves.length) continue;
      const meilleur = sortes => trouves.filter(r => sortes.includes(r.t.sorte)).sort((x, y) => y.longueur - x.longueur)[0] || null;
      const options = [];
      const complete = meilleur(['complete']);
      if (complete) options.push([complete]);
      // 08/11/2026 (étape 3a) : une expression complète peut aussi avoir sa cible (« ouvre le pdf » + [TITRE]).
      if (complete) {
        const cibleHors = trouves.filter(r => r.t.sorte === 'cible' && r !== complete && !dedans(complete.t.terme, r.t.terme))
          .sort((x, y) => y.longueur - x.longueur)[0];
        if (cibleHors) options.push([complete, cibleHors]);
      }
      const seule = trouves.filter(r => r.t.sorte === 'seule' && rienDAutre(propre, r.t.terme))[0]; // 08/11/2026 (étape 2a)
      if (seule) options.push([seule]);
      const cible = meilleur(['cible', 'les_deux']);
      // 08/11/2026 : + 'action_cible' (verbe qui n'agit qu'avec un mot-clé ; jamais seul, voir plus bas).
      // 09/11/2026 (défaut 1 vu par Max : « mes notes de cours » = « Ouvrir Notes ») : le verbe ne peut pas être le MÊME
      // bout de phrase que le mot-clé (« les notes » et « mes notes » tombaient tous deux sur « mes notes »).
      const simple = r => !r.t.libreSeul && !(r.t.noms || []).length; // pas de [TITRE], [NOMBRE]… (09/11/2026)
      const bout = r => { if (!r.t.motif) return r.t.terme; const m = ` ${propre} `.match(new RegExp(r.t.motif.source)); return m ? m[0].trim() : r.t.terme; };
      const action = trouves.filter(r => ['action', 'les_deux', 'action_cible'].includes(r.t.sorte) && r !== cible && !(cible && dedans(cible.t.terme, r.t.terme))
        && !(cible && simple(cible) && simple(r) && (dedans(bout(cible), bout(r)) || dedans(bout(r), bout(cible)))))
        .sort((x, y) => y.longueur - x.longueur)[0] || null;
      if (c.aDesCibles) {
        if (cible && action && cible.t.terme !== action.t.terme) options.push([action, cible]);
        const entiere = trouves.filter(r => r.t.sorte === 'les_deux' && c.termes.some(v => v.sorte === 'action' && v.terme !== r.t.terme && dedans(r.t.terme, v.terme)))
          .sort((x, y) => y.longueur - x.longueur)[0];
        if (entiere) options.push([entiere]);
        // Avant le 08/11/2026 (correction A) : if (VERBE_SEUL.has(c.code)) { const seul = meilleur(['action', 'les_deux']); if (seul) options.push([seul]); }
        if (VERBE_SEUL.has(c.code)) {
          const cibles = new Set(c.termes.filter(v => v.sorte === 'cible').map(v => v.terme));
          const limite = VERBE_SEUL_LIMITE[c.code];
          const seul = trouves.filter(r => (r.t.sorte === 'action' || (r.t.sorte === 'les_deux' && !cibles.has(r.t.terme))) && !r.t.motif && rienDAutre(propre, r.t.terme)
            && (!limite || limite.test(r.t.terme)))
            .sort((x, y) => y.longueur - x.longueur)[0];
          if (seul) options.push([seul]);
        }
        // 09/11/2026 (partie C) : + tout écran de navigation dit seul (bloc « Écran cible »). Avant : if (CIBLE_SEULE.has(c.code)) {
        if (CIBLE_SEULE.has(c.code) || c.termes.some(v => v.ecranSeul)) { // 08/11/2026 (étape 2a)
          // 09/11/2026 : avec le petit mot libre (« la to-do » pour « ma to-do »), on compare le texte VRAIMENT trouvé dans
          // la phrase. Avant : trouves.filter(r => r.t.sorte === 'cible' && rienDAutre(propre, r.t.terme))…
          const texteTrouve = r => { if (!r.t.motif) return r.t.terme; const m = ` ${propre} `.match(new RegExp(r.t.motif.source)); return m ? m[0].trim() : r.t.terme; };
          // 09/11/2026 (partie C) : pour un écran, seulement ses formulations « Écran cible » (pas ses mots-clés) ; CIBLE_SEULE inchangé.
          const seuleCible = trouves.filter(r => r.t.sorte === 'cible' && (CIBLE_SEULE.has(c.code) || r.t.ecranSeul) && rienDAutre(propre, texteTrouve(r))).sort((x, y) => y.longueur - x.longueur)[0];
          if (seuleCible) options.push([seuleCible]);
        }
      } else {
        const seul = meilleur(['action', 'les_deux']);
        if (seul) options.push([seul]);
      }
      if (!options.length) continue;
      const score = o => o.reduce((s, r) => s + r.longueur, 0);
      let retenus = options.sort((x, y) => score(y) - score(x))[0];
      // 08/11/2026 (étape 3a) : « [TITRE] » seul = tout ce qui suit le verbe ou l'expression (« mets-moi bohemian
      // rhapsody » → « bohemian rhapsody », et non le dernier mot) ; rien après (« mets-moi s'il te plaît ») : cette
      // possibilité ne compte pas (on garde la meilleure des autres, s'il y en a).
      const libre = retenus.find(r => r.t.libreSeul);
      const autre = retenus.find(r => !r.t.libreSeul && !r.t.motif);
      if (libre) {
        const i = autre ? p.indexOf(` ${autre.t.terme} `) : -1;
        const reste = i < 0 ? [] : p.slice(i + autre.t.terme.length + 2).trim().split(' ').filter(Boolean);
        while (reste.length && DEBUT_VIDE.has(reste[0])) reste.shift();
        while (reste.length && FIN_VIDE.has(reste[reste.length - 1])) reste.pop();
        if (reste.length) libre.valeurs = { [libre.t.noms[0]]: reste.join(' ') };
        else {
          const autres = options.filter(o => !o.includes(libre));
          if (!autres.length) continue;
          retenus = autres[0]; // déjà triées, la meilleure d'abord
        }
      }
      resultats.push({ code: c.code, commande: c.libelle, mots: retenus.map(r => r.t.terme), score: score(retenus),
        conflit: retenus.some(r => r.t.conflit), valeurs: Object.assign({}, ...retenus.map(r => r.valeurs)),
        apprise: retenus.some(r => r.t.apprise) }); // 09/11/2026 (petit tableur)
    }
    if (!resultats.length) {
      const incomplet = commenceCommeUneCommande(propre);
      return incomplet ? { statut: 'incomplet', mot: incomplet } : { statut: 'rien' };
    }
    resultats.sort((x, y) => y.score - x.score);
    let egaux = resultats.filter(r => r.score === resultats[0].score);
    // 09/11/2026 (petit tableur) : à égalité, la phrase que Max a apprise à Cap (une seule) tranche.
    if (egaux.length > 1 && egaux.filter(r => r.apprise).length === 1) egaux = egaux.filter(r => r.apprise);
    if (egaux.length > 1 && contexte.ouvert) {
      const prefixe = { lecteur: 'MUS-', visionneuse: 'VIS-' }[contexte.ouvert];
      const prefere = egaux.filter(r => prefixe && r.code.startsWith(prefixe));
      if (prefere.length === 1) egaux = prefere;
    }
    // 09/11/2026 (mission D) : + « options » : chaque possibilité complète (comme un résultat « reconnu »), pour la
    // fenêtre de gros choix. Avant : { statut: 'ambigu', codes, commandes } seulement.
    const enReconnu = x => { const o = { statut: 'reconnu', code: x.code, commande: x.commande, mots: x.mots, score: x.score, conflit: x.conflit }; if (Object.keys(x.valeurs).length) o.valeurs = x.valeurs; return o; };
    if (egaux.length > 1) return { statut: 'ambigu', codes: egaux.map(r => r.code), commandes: egaux.map(r => r.commande), options: egaux.map(enReconnu) };
    const r = egaux[0];
    const sortie = { statut: 'reconnu', code: r.code, commande: r.commande, mots: r.mots, score: r.score, conflit: r.conflit };
    if (Object.keys(r.valeurs).length) sortie.valeurs = r.valeurs;
    return sortie;
  }

  // 08/11/2026 (correction A) : la phrase n'a rien d'autre que « terme » (en tête) et de petits mots.
  function rienDAutre(propre, terme) {
    if (propre !== terme && !propre.startsWith(`${terme} `)) return false;
    return propre.slice(terme.length).trim().split(' ').filter(Boolean).every(m => MOTS_VIDES.has(m));
  }

  // Phrase qui commence comme une commande sans être complète : un verbe (ou tournure) d'une commande en tête,
  // suivi de rien ou de petits mots seulement (« ouvre », « mets-moi », « affiche-le s'il te plaît »).
  // Prudent : « mets du sel FICTIF » n'est PAS incomplet (il y a d'autres mots) : la phrase part dans « À trier ».
  function commenceCommeUneCommande(propre) {
    let meilleur = '';
    for (const c of index.values()) {
      if (!PREFIXES_COMMANDES.test(c.code)) continue;
      // 08/11/2026 (correction A) : une variante qui est aussi un mot-clé (« ça ») n'est pas un début de commande.
      const cibles = new Set(c.termes.filter(v => v.sorte === 'cible').map(v => v.terme));
      for (const t of c.termes) {
        if (t.motif || !['action', 'les_deux'].includes(t.sorte) || (t.sorte === 'les_deux' && cibles.has(t.terme))) continue;
        if ((propre === t.terme || propre.startsWith(`${t.terme} `)) && t.terme.length > meilleur.length) meilleur = t.terme;
      }
    }
    if (!meilleur) return '';
    const reste = propre.slice(meilleur.length).trim().split(' ').filter(Boolean);
    return reste.every(m => MOTS_VIDES.has(m)) ? meilleur : '';
  }

  // ----- 08/11/2026 (étape 0) : décision pour le MICRO DU MILIEU (accord de Max) -----
  // Codes que le micro fait lui-même (plan accepté : navigation et dictée, musique, visionneuse, documents).
  // Les autres codes du tableur (appel, liste de courses…) suivent le chemin d'avant.
  const PREFIXES_COMMANDES = /^(NAV|DIC|MUS|VIS|DOC)-/;
  const PAS_UNE_IA = 'Je ne suis pas une IA, dis-moi ce que tu veux.';
  const actions = new Map(); // code → fonction (branchées étape par étape)
  function brancherAction(code, fonction) { if (typeof fonction === 'function') actions.set(code, fonction); else actions.delete(code); }
  function actionBranchee(code) { return actions.has(code); }
  // Renvoie null (la phrase suit le chemin d'avant : tâche « À trier »…) ou { code?, message } (déjà traité ici).
  // ----- 09/11/2026 (accord de Max, petit tableur, étape 2) : les PHRASES APPRISES s'ajoutent aux lignes du tableur
  // principal pour le micro. D'où elles viennent : la liste du téléphone (phrasesApprendre) et la copie du petit tableur
  // « Phrases apprises » (tableurPhrases.lireEtGarder) : Cap les reconnaît même sans réseau.
  // Règles de Max : reconnues seulement DITES EN ENTIER (bloc « Expression seule ») ; « Aucune ne convient » (pas de code)
  // ignorée ; lignes « retirée » ou « remplacée » ignorées ; LE PRINCIPAL GAGNE : une phrase que le tableur principal
  // reconnaît déjà est ignorée ici (elle reste écrite dans le petit tableur, marquée « déjà dans le principal »).
  const CLE_PHRASES_TELEPHONE = 'cap_phrases_a_apprendre_v1';
  const CLE_PHRASES_TABLEUR = 'cap_phrases_apprises_copie_v1';
  const CLE_PHRASES_TAMPON = 'cap_phrases_tampon_v1';
  function dejaDansPrincipal(phrase, principal = (copie() || {}).lignes) {
    if (!principal || !principal.length) return false;
    // « Reconnaît » = une réponse NETTE. Quand le principal HÉSITE (fenêtre de gros choix), le choix de Max sert justement
    // à trancher : la phrase apprise compte alors (déduit de la règle de Max, à confirmer).
    const r = reconnaitre(phrase, principal);
    return r.statut === 'reconnu';
  }
  function lireListe(stockage, cle) { try { const v = JSON.parse(stockage.getItem(cle)); return v; } catch (erreur) { return null; } }
  function phrasesApprises(stockage) {
    const tampon = lireListe(stockage, CLE_PHRASES_TAMPON);
    const ecartes = new Set((Array.isArray(tampon) ? tampon : []).filter(o => o && o.type === 'etat').map(o => o.id)); // retrait pas encore écrit
    const telephone = lireListe(stockage, CLE_PHRASES_TELEPHONE);
    const tableur = lireListe(stockage, CLE_PHRASES_TABLEUR);
    const vues = new Set();
    const sortie = [];
    const garder = (e, etat = '') => {
      if (!e || typeof e.phrase !== 'string' || !e.code || (e.id && ecartes.has(e.id))) return;
      if (/^(retir|rempla)/.test(plier(etat))) return;
      const cle = plier(e.phrase);
      if (!cle || vues.has(cle)) return;
      vues.add(cle);
      sortie.push({ phrase: e.phrase, code: e.code });
    };
    for (const e of Array.isArray(telephone) ? telephone : []) garder(e); // le téléphone d'abord (le plus récent)
    for (const e of (tableur && Array.isArray(tableur.lignes)) ? tableur.lignes : []) garder(e, e.etat);
    return sortie;
  }
  let fusion = null;
  let fusionDe = '';
  function lignesMicro(stockage = (typeof localStorage !== 'undefined' ? localStorage : null)) {
    if (!stockage) return undefined;
    const principal = (copie(stockage) || {}).lignes;
    if (!principal || !principal.length) return principal;
    let brut = '';
    try { brut = [CLE_COPIE, CLE_PHRASES_TELEPHONE, CLE_PHRASES_TABLEUR, CLE_PHRASES_TAMPON].map(c => stockage.getItem(c) || '').join('|'); } catch (erreur) { return principal; }
    if (fusion && brut === fusionDe) return fusion;
    const commandeDe = new Map();
    for (const l of principal) if (l.code && !commandeDe.has(l.code)) commandeDe.set(l.code, l.commande);
    const ajout = [];
    for (const a of phrasesApprises(stockage)) {
      if (!commandeDe.has(a.code) || dejaDansPrincipal(a.phrase, principal)) continue;
      ajout.push({ code: a.code, commande: commandeDe.get(a.code), bloc: 'Expression seule (Cap)', formulation: a.phrase.replace(/[[\]]/g, ' '), apprise: true });
    }
    fusion = ajout.length ? [...principal, ...ajout] : principal;
    fusionDe = brut;
    return fusion;
  }
  // ----- 09/11/2026 (décision de Max, séance 2) : LES DEUX TABLEURS -----
  // Le tableur « Commandes vocales » (Drive de Max, lecture seule) et « Commandes vocales (Cap) » (Drive du compte Cap :
  // les phrases apprises). Les phrases apprises viennent : de la liste du téléphone (pas encore écrites), de la copie du
  // tableur de Cap, et (avant la reprise) de la copie de « Phrases apprises ». Une phrase apprise ne compte que DITE EN
  // ENTIER. Règles de Max (remplacent « le principal gagne » et « la phrase apprise tranche ») :
  //  - même commande dans les deux (ou le principal ne connaît pas la phrase, ou il hésite et la commande apprise est
  //    l'une de ses possibilités) : Cap la fait directement ;
  //  - commandes différentes : la fenêtre de gros choix, une case par commande (+ « Aucun de ces choix ») ;
  //  - une phrase « choisie par Max » (dans cette fenêtre) est retenue : Cap la fait directement ensuite.
  // Écartées : « Aucune ne convient » (pas de code), « retirée », « remplacée » (et celles qui attendent de l'être).
  const CLE_CAP_COPIE = 'cap_tableur_cap_copie_v1';
  const CLE_CAP_TAMPON = 'cap_tableur_cap_tampon_v1';
  function apprisesDeuxTableurs(stockage) {
    const ecartes = new Set();
    const choisies = new Set();
    for (const cle of [CLE_PHRASES_TAMPON, CLE_CAP_TAMPON]) {
      const t = lireListe(stockage, cle);
      for (const o of Array.isArray(t) ? t : []) {
        if (!o || o.type !== 'etat') continue;
        const texte = plier(o.texte || o.etat || '');
        if (/^(retir|remplac)/.test(texte)) ecartes.add(o.id);
        else if (/^choisie/.test(texte)) choisies.add(o.id);
      }
    }
    const vues = new Set();
    const sortie = [];
    const garder = (e, ecartee = false, choisie = false) => {
      if (!e || typeof e.phrase !== 'string' || !e.code || ecartee || (e.id && ecartes.has(e.id))) return;
      const cle = plier(e.phrase);
      if (!cle || vues.has(cle)) return;
      vues.add(cle);
      sortie.push({ phrase: e.phrase, cle, code: String(e.code).trim(), commande: e.commande || '', id: e.id || '', choisie: Boolean(choisie || e.choisie || (e.id && choisies.has(e.id))) });
    };
    const telephone = lireListe(stockage, CLE_PHRASES_TELEPHONE);
    for (const e of Array.isArray(telephone) ? telephone : []) garder(e); // le téléphone d'abord (le plus récent)
    const cap = lireListe(stockage, CLE_CAP_COPIE);
    for (const e of (cap && Array.isArray(cap.lignes)) ? cap.lignes : []) garder(e, e.ecartee, e.choisie);
    const ancien = lireListe(stockage, CLE_PHRASES_TABLEUR);
    for (const e of (ancien && Array.isArray(ancien.lignes)) ? ancien.lignes : []) garder(e, /^(retir|remplac)/.test(plier(e.etat || '')));
    return sortie;
  }
  // La phrase apprise dite EN ENTIER (petits mots en plus tolérés à la fin), la plus longue d'abord.
  function trouverApprise(phrase, liste) {
    const propre = sansNe(sansHesitations(plier(phrase)));
    if (!propre) return null;
    return (liste || []).filter(a => a.cle && rienDAutre(propre, a.cle)).sort((x, y) => y.cle.length - x.cle.length)[0] || null;
  }
  function nomCommande(code, lignes) {
    try { const c = codesConnus(lignes).find(x => x.code === code); return c ? c.commande : ''; } catch (erreur) { return ''; }
  }

  // Avant le 09/11/2026 (petit tableur) : function deciderMicro(phrase, { lignes = (copie() || {}).lignes, contexte = {} } = {}) {
  // Avant la séance 2 (09/11/2026) : function deciderMicro(phrase, { lignes = lignesMicro(), contexte = {} } = {}) {
  // (lignesMicro, « le principal gagne », reste dans le code mais le micro ne s'en sert plus.)
  function deciderMicro(phrase, { lignes = (copie() || {}).lignes, contexte = {}, apprises = null } = {}) {
    const liste = apprises || (typeof localStorage !== 'undefined' ? apprisesDeuxTableurs(localStorage) : []);
    const a = trouverApprise(phrase, liste);
    if (a && PREFIXES_COMMANDES.test(a.code)) {
      const rp = lignes && lignes.length ? reconnaitre(phrase, lignes, contexte) : { statut: 'rien' };
      const optionApprise = { statut: 'reconnu', code: a.code, commande: nomCommande(a.code, lignes) || a.commande || a.code, mots: [a.cle], score: a.cle.length, conflit: false, apprise: true };
      if (rp.statut === 'reconnu' && rp.code === a.code) return faireReconnu(rp, contexte); // même commande : directement
      if (rp.statut === 'ambigu' && rp.codes.includes(a.code)) return faireReconnu((rp.options || []).find(o => o.code === a.code) || optionApprise, contexte);
      if (!['reconnu', 'ambigu'].includes(rp.statut) || a.choisie) return faireReconnu(optionApprise, contexte);
      const options = [...(rp.statut === 'reconnu' ? [rp] : (rp.options || [])), optionApprise].filter(o => PREFIXES_COMMANDES.test(o.code));
      if (options.length < 2) return faireReconnu(optionApprise, contexte);
      return { statut: 'ambigu', deuxTableurs: true, codes: options.map(o => o.code), options,
        message: `J’hésite entre ${options.map(o => `« ${o.commande} »`).join(' et ')} : touche ou dis le bon numéro.` };
    }
    const r = reconnaitre(phrase, lignes, contexte);
    if (r.statut === 'incomplet') return { statut: 'incomplet', message: PAS_UNE_IA };
    if (r.statut === 'ambigu') {
      if (!r.codes.every(c => PREFIXES_COMMANDES.test(c))) return null;
      // 09/11/2026 (accord de Max, mission D) : Cap ne devine pas : il montre les choix en gros, numérotés (fenêtre de Cap).
      // Avant : message: `J’hésite entre … . Redis-le autrement.` (sans choix).
      return { statut: 'ambigu', codes: r.codes, options: r.options || [], message: `J’hésite entre ${r.commandes.map(c => `« ${c} »`).join(' et ')} : touche ou dis le bon numéro.` };
    }
    if (r.statut !== 'reconnu' || !PREFIXES_COMMANDES.test(r.code)) return null;
    return faireReconnu(r, contexte); // 09/11/2026 (mission D) : la suite d'avant, devenue une fonction (même contenu)
  }
  // 09/11/2026 (mission D) : fait une commande reconnue (ou CHOISIE par Max dans la fenêtre de gros choix). Même contenu que
  // la fin de deciderMicro d'avant.
  function faireReconnu(r, contexte = {}) {
    const action = actions.get(r.code);
    if (!action) return { statut: 'pas_encore', code: r.code, message: `J’ai compris « ${r.commande} », mais je ne sais pas encore le faire.` };
    // 08/11/2026 (étape 1) : une action peut rendre { message, parler: false } (ne pas parler : ex. relancer la dictée).
    const sortie = action(r, contexte);
    const message = (sortie && typeof sortie === 'object' ? sortie.message : sortie) || `C’est fait : ${r.commande}.`;
    const fait = { statut: 'fait', code: r.code, message };
    if (sortie && typeof sortie === 'object' && sortie.parler === false) fait.parler = false;
    if (sortie && typeof sortie === 'object' && sortie.suite) fait.suite = sortie.suite; // 08/11/2026 (étape 2b) : réponse qui vient après (recherche)
    return fait;
  }

  // ----- 09/11/2026 (accord de Max) : machine « phrase à apprendre » : les commandes PROCHES d'une phrase, choisies par
  // le CODE (mots en commun avec les formulations du tableur), jamais par l'IA ; et les commandes rangées par famille.
  const FAMILLES = { NAV: 'Navigation', MUS: 'Musique', VIS: 'Visionneuse', DOC: 'Documents', DIC: 'Dictée' };
  function codesConnus(lignes = (copie() || {}).lignes) {
    if (!lignes || !lignes.length) return [];
    if (indexDe !== lignes) { index = preparer(lignes); indexDe = lignes; }
    return [...index.values()].filter(c => PREFIXES_COMMANDES.test(c.code))
      .map(c => ({ code: c.code, commande: c.libelle, termes: c.termes })).sort((a, b) => a.code.localeCompare(b.code));
  }
  function familles(lignes = (copie() || {}).lignes) {
    const par = new Map();
    for (const c of codesConnus(lignes)) {
      const f = c.code.slice(0, 3);
      if (!par.has(f)) par.set(f, { famille: f, nom: FAMILLES[f] || f, codes: [] });
      par.get(f).codes.push({ code: c.code, commande: c.commande });
    }
    return [...par.values()];
  }
  function proches(phrase, lignes = (copie() || {}).lignes, n = 5) {
    const propre = sansHesitations(plier(phrase));
    const mots = propre.split(' ').filter(m => m.length > 1 && !MOTS_VIDES.has(m) && !DETERMINANTS.includes(m));
    if (!mots.length) return [];
    const p = ` ${propre} `;
    return codesConnus(lignes).map(c => {
      const motsCode = new Set(c.termes.flatMap(x => String(x.terme || '').split(' ')));
      let score = mots.filter(m => motsCode.has(m)).length * 2;
      for (const x of c.termes) if (!x.motif && String(x.terme || '').length > 2 && p.includes(` ${x.terme} `)) score += 1;
      return { code: c.code, commande: c.commande, score };
    }).filter(x => x.score > 0).sort((a, b) => b.score - a.score || a.code.localeCompare(b.code)).slice(0, n);
  }

  // ----- 08/11/2026 (correction D, accord de Max) : les 10 dernières phrases entendues par le micro du milieu, avec la
  // réponse de Cap. Gardées sur le téléphone seulement (localStorage), pour les essais ; jamais envoyées à l'IA.
  const CLE_ENTENDUES = 'cap_phrases_entendues_v1';
  function noterEntendue(stockage, phrase, reponse, maintenant = Date.now()) {
    if (!stockage) return;
    const liste = entendues(stockage);
    liste.unshift({ quand: new Date(maintenant).toISOString(), phrase: String(phrase || ''), reponse: String(reponse || '') });
    try { stockage.setItem(CLE_ENTENDUES, JSON.stringify(liste.slice(0, 10))); } catch (erreur) { /* mémoire pleine : tant pis pour l'historique */ }
  }
  function entendues(stockage) {
    try { const l = JSON.parse(stockage.getItem(CLE_ENTENDUES)); return Array.isArray(l) ? l : []; } catch (erreur) { return []; }
  }

  function texteReconnaissance(r) {
    if (r.statut === 'pas_de_tableur') return 'Lis d’abord les commandes vocales (bouton « Lire les commandes vocales »).';
    if (r.statut === 'rien') return 'Aucune commande reconnue dans cette phrase.';
    if (r.statut === 'incomplet') return `Phrase incomplète (« ${r.mot} ») : ${PAS_UNE_IA}`; // 08/11/2026 (étape 0)
    if (r.statut === 'ambigu') return `Phrase ambiguë : ${r.codes.map((c, i) => `${c} (${r.commandes[i]})`).join(' ou ')}. Rien n’est choisi.`;
    return `Commande reconnue : ${r.code} (${r.commande}). Mots reconnus : ${r.mots.map(m => `« ${m} »`).join(', ')}.`
      + (r.valeurs ? ` Valeurs : ${Object.entries(r.valeurs).map(([k, v]) => `${k} = ${v}`).join(', ')}.` : '') // 08/11/2026 (étape 0)
      + (r.conflit ? ' Attention : formulation marquée « CONFLIT » dans le tableur, à trancher par Max.' : '');
  }

  // 08/11/2026 (étape 0) : + deciderMicro, brancherAction, actionBranchee, lireNombre, lireDuree, PAS_UNE_IA, PREFIXES_COMMANDES.
  return { CLE_COPIE, NOM_TABLEUR, analyser, texteResume, lireEtGarder, lireAvecCompteCap, lireCsv, copie, oublier, reconnaitre, texteReconnaissance,
    deciderMicro, brancherAction, actionBranchee, lireNombre, lireDuree, PAS_UNE_IA, PREFIXES_COMMANDES, faireReconnu, // 09/11/2026 : + faireReconnu
    codesConnus, familles, proches, FAMILLES, // 09/11/2026 : machine « phrase à apprendre »
    lignesMicro, dejaDansPrincipal, // 09/11/2026 : petit tableur (étape 2)
    apprisesDeuxTableurs, trouverApprise, // 09/11/2026 : séance 2 (les deux tableurs)
    CLE_ENTENDUES, noterEntendue, entendues }; // 08/11/2026 (correction D) : + CLE_ENTENDUES, noterEntendue, entendues
})();
