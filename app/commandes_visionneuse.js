'use strict';

// 08/11/2026 (accord de Max, étape 3a du codage des commandes vocales) : la VISIONNEUSE à la voix, depuis l'écran Micro.
// - VIS-01 « ouvre la visionneuse / l'œil » : le même chemin que l'œil de « Autre ».
// - VIS-02 « affiche le pdf [nom] », VIS-03 « montre la photo [nom] » : Cap cherche lui-même (code, jamais l'IA) dans le
//   Drive du compte Cap (« Relations » et « Documents ») ; un seul trouvé = il s'ouvre dans la visionneuse ; plusieurs, ou
//   pas de nom (« affiche le pdf ») = Cap ne devine jamais : il montre les choix en très gros, avec de gros numéros.
// - Compte Cap pas connecté ou expiré : la visionneuse le dit, avec « Autoriser la lecture du compte Cap ».
// Le CONTENU des documents n'est jamais lu ici et jamais envoyé à l'IA (seulement leurs noms, pour les comparer).
// 08/11/2026 (étape 3c) : suivant / précédent, pages d'un PDF et fermer ajoutés (actions3c, plus bas).
// Pas encore (3d, avec l'accord de Max) : photos d'une personne, dossier entier.
const commandesVisionneuse = (() => {
  const PROFONDEUR_MAX = 8;
  const MAX_CHOIX = 9;
  const plierTexte = s => String(s || '').replace(/œ/g, 'oe').replace(/æ/g, 'ae').normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  const MOTS_VIDES = new Set(['le', 'la', 'les', 'l', 'un', 'une', 'des', 'du', 'de', 'd', 'mon', 'ma', 'mes', 'ce', 'cet', 'cette',
    'pdf', 'document', 'fichier', 'image', 'photo', 'et', 'jpg', 'jpeg', 'png']);
  const motsUtiles = s => plierTexte(s).split(' ').filter(m => m && !MOTS_VIDES.has(m));
  const sansExtension = nom => String(nom || '').replace(/\.[a-z0-9]{2,5}$/i, '');
  // 3 : même nom ; 2 : tous les mots dits sont dans le nom ; 0 : non.
  function score(nom, requete) {
    const mots = motsUtiles(requete);
    if (!mots.length) return 0;
    if (plierTexte(sansExtension(nom)) === plierTexte(requete)) return 3;
    const dans = ` ${plierTexte(nom)} `;
    return mots.every(m => dans.includes(` ${m} `)) ? 2 : 0;
  }

  // Tous les PDF et images de « Relations » et « Documents » (à la racine du compte Cap), avec le chemin des dossiers.
  function documentsDe(arbre, sorte) {
    const trouves = [];
    const vus = new Set();
    const parcourir = (id, chemin, niveau) => {
      if (vus.has(id) || niveau > PROFONDEUR_MAX) return;
      vus.add(id);
      for (const f of arbre.enfants(id)) {
        if (f.mimeType === 'application/vnd.google-apps.folder') { parcourir(f.id, `${chemin} ${f.name}`, niveau + 1); continue; }
        const s = sorte(f);
        if (s === 'pdf' || s === 'images') trouves.push({ id: f.id, nom: sansExtension(f.name), sorte: s === 'pdf' ? 'pdf' : 'image', chemin });
      }
    };
    for (const racine of arbre.enfants(arbre.racine)) {
      if (racine.mimeType === 'application/vnd.google-apps.folder' && (racine.name === 'Relations' || racine.name === 'Documents')) parcourir(racine.id, racine.name, 1);
    }
    return trouves.sort((a, b) => a.nom.localeCompare(b.nom, 'fr', { numeric: true }));
  }

  function brancher(doc, { commandes = (typeof commandesVocales !== 'undefined' ? commandesVocales : null),
    compte = (typeof googleCompteRelations !== 'undefined' ? googleCompteRelations : null),
    lireArbre = c => relationsCompte.lireArbre(c), sorte = f => relationsCompte.sorte(f),
    visionneuse = () => (typeof visionneuseCap !== 'undefined' ? visionneuseCap.instance : null),
    transition = (typeof choixSurEau !== 'undefined' ? choixSurEau : null) } = {}) {
    if (!commandes) return null;
    const el = id => doc.getElementById(id);
    const fenetre = el('choix-voix');
    const liste = el('liste-choix-voix');
    const fermer = el('fermer-choix-voix');
    const ouvrirFenetre = () => { if (transition) transition.ouvrir(fenetre); else if (!fenetre.open) fenetre.showModal(); };
    const fermerFenetre = () => { if (!fenetre.open) return; if (transition) transition.fermer(fenetre); else fenetre.close(); };
    if (fermer) fermer.addEventListener('click', fermerFenetre);
    const noeud = (balise, classe, texte) => { const n = doc.createElement(balise); if (classe) n.className = classe; if (texte !== undefined) n.textContent = texte; return n; };

    function montrer(document) {
      const v = visionneuse();
      if (!v) return 'La visionneuse n’est pas disponible ici.';
      fermerFenetre();
      void v.ouvrir([{ id: document.id, sorte: document.sorte }]);
      return `J’ouvre « ${document.nom} ».`;
    }
    // Choix en très gros, gros numéros (au plus 9) ; un toucher ouvre le document dans la visionneuse.
    function montrerChoix(documents, quoi, question) {
      if (!fenetre || !liste) return 'Je ne peux pas montrer les choix ici.';
      const montres = documents.slice(0, MAX_CHOIX);
      liste.replaceChildren(...montres.map((d, i) => {
        const bouton = noeud('button', 'ligne-morceau ligne-choix-voix');
        bouton.type = 'button';
        bouton.append(noeud('span', 'numero-morceau', String(i + 1)), noeud('span', 'nom-morceau', d.nom));
        bouton.addEventListener('click', () => { montrer(d); });
        return bouton;
      }));
      ouvrirFenetre();
      const plus = documents.length > montres.length ? ` (je montre les ${montres.length} premiers ; dis son nom pour un autre)` : '';
      return `${question || `J’ai trouvé ${documents.length} ${quoi}`}${plus} : touche le bon numéro.`;
    }
    async function documents() {
      if (!compte) return { message: 'Le compte Cap n’est pas disponible ici.' };
      const v = visionneuse();
      if (typeof compte.adresse === 'function' && !compte.adresse()) return { message: 'Identifiant du compte Cap absent : écris-le d’abord dans « Réglages du Drive ».' };
      if (typeof compte.connecte === 'function' && !compte.connecte()) {
        if (v) v.annoncer('Le compte Cap n’est pas connecté (ou la connexion a expiré, au bout d’environ 1 h). Touche « Autoriser la lecture du compte Cap » : tu reviendras ici.', { autorisation: true });
        return { message: 'Le compte Cap n’est pas connecté (ou la connexion a expiré) : touche « Autoriser la lecture du compte Cap ».' };
      }
      try { return { liste: documentsDe(await lireArbre(compte), sorte) }; } catch (erreur) {
        if (/expir|pas connecté/i.test(String(erreur && erreur.message))) {
          if (v) v.annoncer('La connexion du compte Cap a expiré : touche « Autoriser la lecture du compte Cap », tu reviendras ici.', { autorisation: true });
          return { message: 'La connexion du compte Cap a expiré : touche « Autoriser la lecture du compte Cap ».' };
        }
        return { message: `Je n’ai pas pu lire le Drive du compte Cap : ${String(erreur && erreur.message || '').slice(0, 160)}` };
      }
    }
    // sorteVoulue : 'pdf' ou 'image' ; nom et dossier : ce que Max a dit (ou rien).
    async function chercher(sorteVoulue, nom, dossier) {
      const r = await documents();
      if (!r.liste) return r.message;
      const mot = sorteVoulue === 'pdf' ? 'PDF' : 'image';
      let candidats = r.liste.filter(d => d.sorte === sorteVoulue);
      if (dossier) candidats = candidats.filter(d => score(d.chemin, dossier) > 0);
      if (!candidats.length) return dossier ? `Je ne trouve aucun ${mot} dans « ${dossier} ».` : `Il n’y a aucun ${mot} dans le compte Cap.`;
      if (!nom) {
        if (candidats.length === 1) return montrer(candidats[0]);
        return montrerChoix(candidats, '', sorteVoulue === 'pdf' ? 'Quel PDF ?' : 'Quelle image ?');
      }
      const notes = candidats.map(d => ({ d, n: score(d.nom, nom) })).filter(x => x.n > 0);
      if (!notes.length) return `Je ne trouve pas ${sorteVoulue === 'pdf' ? 'de PDF' : 'd’image'} « ${nom} ».`;
      const max = Math.max(...notes.map(x => x.n));
      const meilleurs = notes.filter(x => x.n === max).map(x => x.d);
      if (meilleurs.length === 1) return montrer(meilleurs[0]);
      return montrerChoix(meilleurs, sorteVoulue === 'pdf' ? 'PDF' : 'images');
    }
    const v = r => r.valeurs || {};
    const avecRecherche = (sorteVoulue) => r => ({ message: 'Je cherche…', parler: false, suite: chercher(sorteVoulue, v(r).titre, v(r).dossier) });
    // ----- 08/11/2026 (accord de Max, étape 3c) : suivant / précédent, fermer, pages d'un PDF -----
    const avecVisionneuse = fonction => r => { const vi = visionneuse(); return vi && vi.documentVoisin ? fonction(vi, r) : 'La visionneuse n’est pas disponible ici.'; };
    const motsDe = r => (r.mots || []).join(' ');
    const actions3c = {
      'VIS-04': avecVisionneuse(vi => vi.documentVoisin(1)),
      'VIS-05': avecVisionneuse(vi => vi.documentVoisin(-1)),
      'VIS-06': avecVisionneuse(vi => vi.fermerParVoix()),
      // Le mot dit décide : suivante / précédente, première / dernière, ou un numéro (le dernier dit).
      'VIS-08': avecVisionneuse((vi, r) => {
        const m = motsDe(r);
        if (r.valeurs && Number.isFinite(r.valeurs.nombre)) return vi.page({ numero: r.valeurs.nombre });
        if (/(premiere|debut)/.test(m)) return vi.page({ premiere: true });
        if (/(derniere|fin du)/.test(m)) return vi.page({ derniere: true });
        if (/(precedent|d avant|qui precede|retourne la page)/.test(m)) return vi.page({ delta: -1 });
        return vi.page({ delta: 1 }); // suivante, prochaine, d'après, qui suit, « tourne la page »
      })
    };
    const actions = {
      ...actions3c,
      'VIS-01': () => { const oeil = el('ouvrir-oeil'); if (!oeil) return 'La visionneuse n’est pas disponible ici.'; oeil.click(); return 'J’ouvre la visionneuse.'; },
      'VIS-02': avecRecherche('pdf'),
      'VIS-03': avecRecherche('image')
    };
    for (const [code, action] of Object.entries(actions)) commandes.brancherAction(code, action);
    return { actions, chercher, documentsDe };
  }
  return { brancher, documentsDe, score };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  commandesVisionneuse.instance = commandesVisionneuse.brancher(document);
}
