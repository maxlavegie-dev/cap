'use strict';

// Musique de « Relations » (07/11/2026, accord de Max) : liste des MP3 d'un dossier « r_ » du compte
// Cap (lecture seule), puis lancement d'un morceau dans le lecteur de Zencoder, repris tel quel
// (lecteur_mp3/index.html, une seule ligne ajoutée : window.lecteurMp3Zencoder).
// - Un morceau par ligne : un gros numéro, le nom du morceau sur une seule ligne.
// - Un sous-dossier dont le nom contient « album » (ou « playlist ») devient une liste de lecture :
//   numéro au début du nom (01, 02…), sinon ordre alphabétique.
// - Le MP3 est lu par le compte Cap, puis donné au lecteur sous forme d'adresse locale temporaire
//   (comme le prévoyait Zencoder) ; un seul morceau en mémoire à la fois.
// - Les noms restent sur ce téléphone, à l'écran : jamais gardés, jamais envoyés, jamais donnés à l'IA.
const relationsMp3 = (() => {
  const drive = 'https://www.googleapis.com/drive/v3/files';
  const DOSSIER = 'application/vnd.google-apps.folder';
  const PROFONDEUR_MAX = 20;
  // Au-delà, le morceau n'est pas chargé (mémoire du téléphone).
  const TAILLE_MAX = 60 * 1000 * 1000;
  const estAlbum = nom => /album|playlist/i.test(String(nom || ''));

  // Nom affiché : sans « .mp3 » ni numéro de tête (le gros numéro est déjà à gauche).
  function nomMorceau(nomFichier) {
    // 10/11/2026 (séance 3) : toute extension de musique retirée (types_fichiers.js). Avant : seulement « .mp3 ».
    const sansExtension = typesFichiers.sansExtensionMusique(nomFichier);
    const sansNumero = sansExtension.replace(/^\d+\s*[-._)]*\s*/, '').trim();
    return sansNumero || sansExtension || 'morceau sans nom';
  }

  // Numéro au début du nom d'abord (01, 02, 10…), puis les autres par ordre alphabétique.
  function trier(morceaux) {
    const numero = m => { const t = /^\s*(\d+)/.exec(m.nomFichier); return t ? Number(t[1]) : Infinity; };
    return [...morceaux].sort((a, b) => (numero(a) - numero(b))
      || a.nomFichier.localeCompare(b.nomFichier, 'fr', { numeric: true, sensitivity: 'base' }));
  }

  // MP3 d'un dossier « r_ » : les morceaux libres, puis les albums (sous-dossiers à toute profondeur).
  // 10/11/2026 (séance 4 du lecteur) : + les VIDÉOS reconnues (MP4, WEBM) du dossier, à toute profondeur, dans une liste à
  // part « Vidéos », numérotées après la musique. « total » reste le nombre de morceaux de musique (un dossier n'est proposé
  // que s'il a de la musique, règle de la séance 3) ; « nbVideos » le nombre de vidéos.
  function morceauxDe(arbre, sorte, idDossier) {
    const libres = [];
    const albums = [];
    const videos = [];
    const vus = new Set();
    const parcourir = (id, album, niveau) => {
      if (vus.has(id) || niveau > PROFONDEUR_MAX) return;
      vus.add(id);
      for (const fichier of arbre.enfants(id)) {
        if (fichier.mimeType === DOSSIER) {
          if (!album && estAlbum(fichier.name)) {
            const nouveau = { nom: String(fichier.name), morceaux: [] };
            albums.push(nouveau);
            parcourir(fichier.id, nouveau, niveau + 1);
          } else parcourir(fichier.id, album, niveau + 1);
        } else if (sorte(fichier) === 'musique') { // 10/11/2026 (séance 3) : toute la musique ; avant : seulement le MP3
          (album ? album.morceaux : libres).push({
            id: fichier.id, nomFichier: String(fichier.name || ''), nom: nomMorceau(fichier.name), taille: Number(fichier.size) || 0
          });
        } else if (sorte(fichier) === 'video') {
          const nomFichier = String(fichier.name || '');
          videos.push({ id: fichier.id, nomFichier, nom: typesFichiers.sansExtensionVideo(nomFichier) || 'vidéo sans nom', taille: Number(fichier.size) || 0, video: true });
        }
      }
    };
    parcourir(idDossier, null, 1);
    const listes = albums.filter(a => a.morceaux.length)
      .sort((a, b) => a.nom.localeCompare(b.nom, 'fr', { numeric: true }))
      .map(a => ({ nom: a.nom, morceaux: trier(a.morceaux) }));
    // Numéros continus dans tout le dossier (pour toucher ou, plus tard, dire « le 3 »).
    let n = 0;
    const numeroter = m => ({ ...m, numero: ++n });
    const resultat = { libres: trier(libres).map(numeroter), albums: listes.map(a => ({ nom: a.nom, morceaux: a.morceaux.map(numeroter) })) };
    resultat.total = n;
    resultat.videos = trier(videos).map(numeroter);
    resultat.nbVideos = resultat.videos.length;
    return resultat;
  }

  // Dossiers « r_ » de « Relations » (racine du compte Cap) qui contiennent au moins un fichier LISIBLE par le lecteur :
  // musique (MP3, FLAC, M4A, WAV, OGG, OPUS) OU vidéo (MP4, WEBM), même dans un sous-dossier. Nom de fonction gardé.
  // 10/11/2026 (décision de Max, après la séance 4 du lecteur) : une vidéo seule suffit. Avant (séance 3) : musique seulement.
  function dossiersAvecMp3(arbre, sorte) {
    const racines = arbre.enfants(arbre.racine).filter(x => x.name === 'Relations' && x.mimeType === DOSSIER);
    if (racines.length !== 1) return { racines: racines.length, dossiers: [] };
    const dossiers = arbre.enfants(racines[0].id)
      .filter(x => x.mimeType === DOSSIER && String(x.name).startsWith('r_'))
      .map(x => ({ id: x.id, nom: String(x.name), musique: morceauxDe(arbre, sorte, x.id) }))
      .filter(x => x.musique.total + (x.musique.nbVideos || 0) > 0) // avant : .filter(x => x.musique.total > 0)
      .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));
    return { racines: 1, dossiers };
  }

  // Lecteur de Zencoder dans un cadre de la page.
  // 07/11/2026 (accord de Max) : rechargé à chaque ouverture (la sortie du sable se rejoue) et vidé
  // à la fermeture (son animation s'arrête) : « vider » remet le cadre sur une page blanche.
  // 08/11/2026 (décisions de Max) : retouches d'AFFICHAGE du lecteur de Zencoder, posées par Cap dans la page chargée
  // (le fichier de Zencoder n'est pas modifié ; ses textes et ses fonctions restent) :
  // 1. l'étiquette « FICTIF — essai lecteur » (affichage seul, aucune fonction) est cachée ;
  // 2. et 3. lecture, pause, début, fin : les caractères ▶ ⏸ ⏮ ⏭ (que le téléphone dessine en noir ou en émoji orange)
  //    sont cachés et remplacés par des dessins centrés, de la couleur des textes du lecteur ; le triangle de lecture est
  //    décalé un peu à droite (centrage optique) ; pas de surbrillance ni de focus qui reste après le toucher ;
  // 4. « Choisir un MP3 » devient « Choisir » (même bouton, même place, même fonction ; texte d'origine gardé).
  const ICONES_LECTEUR = { '▶': 'lecture', '⏸': 'pause', '⏮': 'debut', '⏭': 'fin' };
  const dessin = chemin => `url("data:image/svg+xml,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path fill='#3a3a38' d='${chemin}'/></svg>`)}")`;
  const STYLE_RETOUCHES_LECTEUR = [
    '#lecteur .etiquette-fictif { display: none; }',
    // 10/11/2026 (séance 4 du lecteur) : l'image d'une vidéo, au-dessus du titre, à la largeur du lecteur ; cachée pour la musique.
    '#image-video { display: block; width: 100%; max-height: 42vh; margin: 0 auto 12px; border-radius: 12px; background: #000; object-fit: contain; }',
    '#image-video[hidden] { display: none; }',
    '#controles button { color: transparent; -webkit-tap-highlight-color: transparent; outline: none;',
    '  background-repeat: no-repeat; background-position: center; background-size: 46%; }',
    '#controles button:focus, #controles button:focus-visible, #controles button:active { outline: none; }',
    '#bouton-choisir { -webkit-tap-highlight-color: transparent; outline: none; }',
    // Triangle : boîte décalée d'une unité à droite sur 24 (environ 4 %), centrage optique.
    `#controles button[data-icone="lecture"] { background-image: ${dessin('M7.5 5v14l11-7z')}; }`,
    `#controles button[data-icone="pause"] { background-image: ${dessin('M7 5h3.5v14H7zM13.5 5H17v14h-3.5z')}; }`,
    `#controles button[data-icone="debut"] { background-image: ${dessin('M6 5h2v14H6zM18 5v14L9 12z')}; }`,
    `#controles button[data-icone="fin"] { background-image: ${dessin('M16 5h2v14h-2zM6 5v14l9-7z')}; }`
  ].join('\n');
  function retoucherLecteur(docLecteur) {
    if (!docLecteur || !docLecteur.head || docLecteur.getElementById('retouches-cap')) return;
    const style = docLecteur.createElement('style');
    style.id = 'retouches-cap';
    style.textContent = STYLE_RETOUCHES_LECTEUR;
    docLecteur.head.appendChild(style);
    const choisir = docLecteur.getElementById('bouton-choisir');
    if (choisir) { choisir.dataset.texteZencoder = choisir.textContent; choisir.textContent = 'Choisir'; }
    const controles = docLecteur.getElementById('controles');
    if (!controles) return;
    const boutons = [...controles.querySelectorAll('button')];
    const marquer = () => { for (const b of boutons) b.dataset.icone = ICONES_LECTEUR[b.textContent.trim()] || ''; };
    marquer();
    // Le lecteur change lui-même ▶ ⏸ : le dessin suit.
    const vue = docLecteur.defaultView;
    if (vue && vue.MutationObserver) new vue.MutationObserver(marquer).observe(controles, { subtree: true, childList: true, characterData: true });
    // Aucun état qui reste après le toucher (focus) : le bouton reprend son aspect dès que le doigt est levé.
    const lacher = e => { const b = e.target && e.target.closest ? e.target.closest('button') : null; if (b) vue.setTimeout(() => b.blur(), 0); };
    controles.addEventListener('pointerup', lacher);
    controles.addEventListener('click', lacher);
    if (choisir) { choisir.addEventListener('pointerup', lacher); choisir.addEventListener('click', lacher); }
  }

  function chargeurLecteur(cadre) {
    let promesse = null;
    const charger = () => {
      if (!promesse) {
        promesse = new Promise((ok, refus) => {
          const surChargement = () => {
            let adresse = '';
            try { adresse = String(cadre.contentWindow.location.href); } catch (erreur) { /* pas encore lisible */ }
            // La page blanche de la fermeture précédente peut finir de charger ici : ce n'est pas le lecteur.
            if (!/lecteur_mp3\/index\.html/.test(adresse)) return;
            cadre.removeEventListener('load', surChargement);
            const lecteur = cadre.contentWindow.lecteurMp3Zencoder;
            if (lecteur && typeof lecteur.jouerFichier === 'function' && typeof lecteur.arreter === 'function') {
              try { retoucherLecteur(cadre.contentWindow.document); } catch (erreur) { /* affichage seulement : le lecteur marche sans */ }
              ok(lecteur);
            }
            else { promesse = null; refus(new Error('Le lecteur MP3 n’a pas pu démarrer.')); }
          };
          cadre.addEventListener('load', surChargement);
          cadre.src = 'lecteur_mp3/index.html';
        });
      }
      return promesse;
    };
    charger.vider = () => { promesse = null; cadre.src = 'about:blank'; };
    return charger;
  }

  // Étape 3 (07/11/2026, accord de Max) : morceau suivant et connexion qui expire.
  // - À la fin d'un morceau, le suivant de la MÊME liste (morceaux libres, ou album) se lance tout seul ;
  //   il est chargé à l'avance pendant l'écoute (pas de blanc, et un morceau de marge).
  // - Avant une liste, si la connexion du compte Cap finit dans moins de 30 minutes : proposition de
  //   l'autoriser à nouveau d'abord.
  // - Si elle expire quand même : la place (dossier, morceau, numéro ; jamais un nom) est gardée sur ce
  //   téléphone, puis « Reprendre la musique au morceau N » relance au bon endroit, en un appui.
  const CLE_REPRISE = 'cap_musique_reprise_v1';
  const MINUTES_AVANT_LISTE = 30;
  const estExpiration = erreur => /expir|pas connecté/i.test(String(erreur && erreur.message || ''));

  // 08/11/2026 : marque du retour direct dans la musique (la même que visionneuseCap.CLE_RETOUR_MUSIQUE, vérifié par un test).
  const CLE_RETOUR_MUSIQUE = 'cap_retour_musique_v1';
  // 08/11/2026 (étape 2b) : + « hasard » (tirage au sort, remplaçable dans les tests).
  // 11/11/2026 (c139) : + enLigne (le téléphone a-t-il du réseau ? remplaçable dans les tests).
  function brancher(doc, { compte, arbre, sorte, lecteur, urls = URL, stockage = localStorage, maintenant = () => Date.now(), hasard = Math.random,
    enLigne = () => (typeof navigator === 'undefined' || navigator.onLine !== false) }) {
    const el = id => doc.getElementById(id);
    const ouvrir = el('musique-compte-relations');
    const reprendre = el('reprendre-musique-relations');
    const fenetre = el('musique-relations');
    const etat = el('etat-musique-relations');
    const avertissement = el('avertissement-musique-relations');
    const liste = el('liste-musique-relations');
    const retour = el('retour-musique-relations');
    const fermer = el('fermer-musique-relations');
    const fenetreLecteur = el('lecteur-mp3-relations');
    const etatLecteur = el('etat-lecteur-mp3');
    const reconnecter = el('reconnecter-lecteur-mp3');
    const fermerLecteur = el('fermer-lecteur-mp3');
    if (![ouvrir, reprendre, fenetre, etat, avertissement, liste, retour, fermer, fenetreLecteur, etatLecteur, reconnecter, fermerLecteur].every(Boolean)) return;
    const raison = erreur => String(erreur && erreur.message || 'raison inconnue').slice(0, 220);
    // 08/11/2026 (règle générale de Max) : écran de choix sur l'eau : l'écran d'avant disparaît dans le rien, puis les
    // boutons sortent de sous le sable ; la fermeture fait l'inverse (choix_sur_eau.js ; sinon, d'un coup comme avant).
    const transition = typeof choixSurEau !== 'undefined' ? choixSurEau : null;
    const ouvrirFenetre = () => { if (transition) transition.ouvrir(fenetre); else if (!fenetre.open) fenetre.showModal(); };
    const fermerFenetre = () => { if (transition) transition.fermer(fenetre); else fenetre.close(); };
    const changerEcran = miseAJour => { if (transition) transition.changer(fenetre, miseAJour); else miseAJour(); };
    const noeud = (balise, classe, texte) => {
      const n = doc.createElement(balise);
      if (classe) n.className = classe;
      if (texte !== undefined) n.textContent = texte;
      return n;
    };
    let dossiers = [];
    let dossierEnCours = null;
    const dossierDuMorceau = new WeakMap(); // 09/11/2026 (playlist par défaut) : le dossier de chaque morceau de la liste
    let adresseEnCours = null;
    // Lecteur de Zencoder, une fois chargé (fermer ne le charge jamais pour rien).
    let zencoderPret = null;
    let demande = 0;
    // Liste en cours de lecture et place dans cette liste ; morceau suivant chargé à l'avance.
    let file = [];
    let position = -1;
    let avance = null;
    const fins = new WeakSet();
    // Vrai quand le lecteur est fermé et déjà nettoyé (pour ne nettoyer qu'une fois par ouverture).
    let nettoye = true;
    // 08/11/2026 (décision de Max) : musique en arrière-plan (lecteur caché, musique qui continue, indicateur).
    let enArrierePlan = false;
    let pauseVoulue = false; // 08/11/2026 (reprise automatique) : vraie seulement après « pause » dit ou demandé par Max
    let fermetureLecteur = null;
    const indicateur = el('indicateur-musique');

    // ----- Place gardée sur le téléphone (identifiants et numéro seulement) -----
    const lireReprise = () => {
      try {
        const r = JSON.parse(stockage.getItem(CLE_REPRISE));
        return r && typeof r.dossier === 'string' && typeof r.morceau === 'string' && Number.isFinite(r.numero) ? r : null;
      } catch (erreur) { return null; }
    };
    const montrerReprise = () => {
      const r = lireReprise();
      reprendre.hidden = !r;
      if (r) reprendre.textContent = `Reprendre la musique au morceau ${r.numero}`;
    };
    const garderPlace = (d, morceau) => {
      try { stockage.setItem(CLE_REPRISE, JSON.stringify({ dossier: d.id, morceau: morceau.id, numero: morceau.numero })); } catch (erreur) { /* rien */ }
      montrerReprise();
    };
    const oublierPlace = () => {
      try { stockage.removeItem(CLE_REPRISE); } catch (erreur) { /* rien */ }
      montrerReprise();
    };

    const autoriserDeNouveau = () => {
      try { compte.seConnecter(); } catch (erreur) { message(raison(erreur)); }
    };

    const montrerDossiers = () => {
      retour.hidden = true;
      avertissement.hidden = true;
      // 08/11/2026 (demande de Max) : plus de texte d'aide (« N dossier(s) avec de la musique. Touche un dossier. »).
      etat.textContent = '';
      liste.replaceChildren(...dossiers.map(d => {
        // 10/11/2026 (séance 3) : « (N morceaux) ». Avant : `${d.nom} (${d.musique.total} MP3)`.
        // 10/11/2026 (séance 4 du lecteur) : + « , N vidéo(s) » s'il y en a.
        const nv = d.musique.nbVideos || 0;
        // 10/11/2026 (décision de Max) : sans musique, seulement « (1 vidéo) ».
        const nm = d.musique.total;
        const parties = [nm && `${nm} morceau${nm > 1 ? 'x' : ''}`, nv && `${nv} vidéo${nv > 1 ? 's' : ''}`].filter(Boolean);
        const bouton = noeud('button', 'choix-grand-affichage', `${d.nom} (${parties.join(', ')})`);
        bouton.type = 'button';
        // 08/11/2026 (demande de Max) : les dossiers disparaissent dans le rien, puis les morceaux sortent du sable.
        bouton.addEventListener('click', () => changerEcran(() => montrerMorceaux(d)));
        return bouton;
      }));
    };

    // La liste (morceaux libres, ou album) qui contient ce morceau.
    const listeDe = (d, morceau) => [d.musique.libres, ...d.musique.albums.map(a => a.morceaux), d.musique.videos || []].find(l => l.includes(morceau)) || [morceau]; // 10/11/2026 : + vidéos

    const ligne = (d, morceau) => {
      const bouton = noeud('button', 'ligne-morceau');
      bouton.type = 'button';
      bouton.append(noeud('span', 'numero-morceau', String(morceau.numero)), noeud('span', 'nom-morceau', morceau.nom));
      // 10/11/2026 (séance 4 du lecteur) : marques visibles « vidéo » et « trop gros pour être lu ici » (plus de 60 Mo).
      const marques = [morceau.video && 'vidéo', morceau.taille > TAILLE_MAX && 'trop gros pour être lu ici'].filter(Boolean);
      if (marques.length) bouton.append(noeud('span', 'marque-morceau', ` (${marques.join(', ')})`));
      bouton.addEventListener('click', () => choisir(d, morceau));
      return bouton;
    };

    const montrerMorceaux = (d, { sansLancement = false } = {}) => {
      dossierEnCours = d;
      retour.hidden = dossiers.length < 2;
      avertissement.hidden = true;
      // 08/11/2026 (règle générale) : plus de texte d'aide (« nom : N MP3. Touche un morceau. »).
      etat.textContent = '';
      const blocs = [];
      if (d.musique.libres.length) blocs.push(noeud('h3', 'titre-liste-morceaux', 'Morceaux'), ...d.musique.libres.map(m => ligne(d, m)));
      for (const album of d.musique.albums) {
        blocs.push(noeud('h3', 'titre-liste-morceaux', `${album.nom} (liste de lecture, ${album.morceaux.length})`), ...album.morceaux.map(m => ligne(d, m)));
      }
      // 10/11/2026 (séance 4 du lecteur) : les vidéos du dossier, après la musique.
      if ((d.musique.videos || []).length) blocs.push(noeud('h3', 'titre-liste-morceaux', 'Vidéos'), ...d.musique.videos.map(m => ligne(d, m)));
      liste.replaceChildren(...blocs);
      // Un seul morceau (et aucune vidéo) : lancement direct.
      if (d.musique.total === 1 && !d.musique.nbVideos && !sansLancement) lancer(d, d.musique.libres[0] || d.musique.albums[0].morceaux[0]);
    };

    // Avant une liste de plusieurs morceaux : la connexion tiendra-t-elle ?
    const choisir = (d, morceau) => {
      const l = listeDe(d, morceau);
      const restants = l.length - l.indexOf(morceau) - 1;
      const minutes = typeof compte.minutesRestantes === 'function' ? compte.minutesRestantes() : Infinity;
      if (restants < 1 || minutes >= MINUTES_AVANT_LISTE) { lancer(d, morceau); return; }
      const autoriser = noeud('button', 'choix-grand-affichage', 'Autoriser la lecture du compte Cap');
      autoriser.type = 'button';
      autoriser.addEventListener('click', () => { garderPlace(d, morceau); autoriserDeNouveau(); });
      const quandMeme = noeud('button', 'choix-grand-affichage', 'Jouer quand même');
      quandMeme.type = 'button';
      quandMeme.addEventListener('click', () => { avertissement.hidden = true; lancer(d, morceau); });
      avertissement.replaceChildren(
        noeud('p', '', `La connexion du compte Cap finit dans ${Math.max(0, minutes)} minute(s) : la musique s’arrêterait avant la fin de la liste. `
          + 'Autorise-la à nouveau d’abord ; ensuite, « Reprendre la musique au morceau ' + morceau.numero + ' » relancera ce morceau.'),
        autoriser, quandMeme);
      avertissement.hidden = false;
      try { avertissement.scrollIntoView({ block: 'center' }); } catch (erreur) { /* rien */ }
    };

    const lancer = (d, morceau) => {
      // 08/11/2026 : un nouveau morceau choisi pendant la musique en arrière-plan : le lecteur revient au premier plan.
      enArrierePlan = false;
      montrerIndicateur(false);
      dossierEnCours = d;
      file = listeDe(d, morceau);
      position = file.indexOf(morceau);
      avance = null;
      oublierPlace();
      void jouer(morceau);
    };

    // Message posé sur le lecteur, seulement pendant le chargement ou en cas de problème.
    // 07/11/2026 (demande de Max) : le titre « Morceau N : nom » au-dessus du lecteur est désactivé
    // (il répétait le titre affiché par le lecteur) : une fois le morceau lancé, le message est caché.
    const message = texte => { etatLecteur.hidden = false; etatLecteur.textContent = texte; };

    const lire = morceau => compte.appeler(`${drive}/${encodeURIComponent(morceau.id)}?alt=media`).then(r => r.blob());

    // Morceau suivant chargé pendant l'écoute (une erreur ici n'arrête rien : il sera redemandé à la fin).
    const preparerSuivant = numeroDemande => {
      const suivant = file[position + 1];
      if (!suivant || suivant.taille > TAILLE_MAX) return;
      lire(suivant).then(contenu => { if (numeroDemande === demande) avance = { id: suivant.id, contenu }; }).catch(() => {});
    };

    // Fin d'un morceau (y compris le bouton « fin » du lecteur) : le suivant de la liste.
    const surveillerFin = zencoder => {
      const audio = zencoder.audio;
      if (!audio || typeof audio.addEventListener !== 'function' || fins.has(audio)) return;
      fins.add(audio);
      audio.addEventListener('ended', () => {
        if ((!fenetreLecteur.open && !enArrierePlan) || zencoderPret !== zencoder) return; // 08/11/2026 : continue en arrière-plan
        const suivant = file[position + 1];
        if (!suivant) {
          // 08/11/2026 : fin de la liste en arrière-plan : tout s'arrête, l'indicateur s'en va.
          if (enArrierePlan) { enArrierePlan = false; nettoyer(); montrerIndicateur(false); }
          return;
        }
        position++;
        void jouer(suivant);
      });
    };

    // Connexion expirée : la place est gardée, puis « Autoriser » (la page de Google, puis le retour dans Cap).
    const expiree = morceau => {
      if (dossierEnCours) garderPlace(dossierEnCours, morceau);
      message(`La connexion du compte Cap a expiré. Touche « Autoriser la lecture du compte Cap » : ensuite, « Reprendre la musique au morceau ${morceau.numero} » relancera ce morceau.`);
      reconnecter.hidden = false;
      if (enArrierePlan && indicateur) indicateur.classList.add('indicateur-probleme'); // 08/11/2026 : visible depuis l'indicateur
    };

    async function jouer(morceau) {
      const numeroDemande = ++demande;
      if (dossierDuMorceau.has(morceau)) dossierEnCours = dossierDuMorceau.get(morceau); // 09/11/2026 (playlist : plusieurs dossiers)
      pauseVoulue = false; // 08/11/2026
      reconnecter.hidden = true;
      if (!fenetreLecteur.open && !enArrierePlan) fenetreLecteur.showModal(); // 08/11/2026 : pas de retour au premier plan en arrière-plan
      nettoye = false;
      montrerIndicateur(); // 08/11/2026, 11h45 : la note discrète sur le lecteur
      if (morceau.taille > TAILLE_MAX) {
        // 10/11/2026 (demande de Max) : dit clairement. Avant : « « nom » est trop gros (N Mo, plus de 60 Mo) : pas chargé. »
        message(`« ${morceau.nom} » : trop gros pour être lu ici (${Math.round(morceau.taille / 1e6)} Mo ; limite : 60 Mo). Rien n’a été chargé.`);
        return;
      }
      message(`Lecture en cours… (chargement de « ${morceau.nom} »)`);
      etatLecteur.classList.add('en-lecture');
      try {
        const deja = avance && avance.id === morceau.id ? avance.contenu : null;
        avance = null;
        const [zencoder, contenu] = await Promise.all([lecteur(), deja ? Promise.resolve(deja) : lire(morceau)]);
        zencoderPret = zencoder;
        // Un autre morceau a été demandé entre-temps, ou le lecteur a été fermé : celui-ci est abandonné.
        if (numeroDemande !== demande || (!fenetreLecteur.open && !enArrierePlan)) return;
        const adresse = urls.createObjectURL(contenu);
        zencoder.jouerFichier(adresse, `${morceau.numero}. ${morceau.nom}`, Boolean(morceau.video)); // 10/11/2026 : vidéo = image montrée
        if (adresseEnCours) urls.revokeObjectURL(adresseEnCours);
        adresseEnCours = adresse;
        // Ancien titre en double, désactivé le 07/11/2026 :
        // etatLecteur.textContent = `Morceau ${morceau.numero} : ${morceau.nom}`;
        etatLecteur.textContent = '';
        etatLecteur.hidden = true;
        surveillerFin(zencoder);
        preparerSuivant(numeroDemande);
      } catch (erreur) {
        if (numeroDemande !== demande) return;
        if (estExpiration(erreur)) expiree(morceau);
        else message(`Morceau non lu : ${raison(erreur)}`);
      } finally {
        if (numeroDemande === demande) etatLecteur.classList.remove('en-lecture');
      }
    }

    // Lecture du Drive puis la fenêtre « Musique » (dossiers, ou la liste d'un seul dossier).
    const chargerDossiers = async () => {
      ouvrirFenetre();
      liste.replaceChildren();
      retour.hidden = true;
      avertissement.hidden = true;
      etat.textContent = 'Lecture du Drive du compte Cap… (rien n’est modifié)';
      const r = dossiersAvecMp3(await arbre(), sorte);
      dossiers = r.dossiers;
      if (r.racines !== 1) { etat.textContent = r.racines ? 'Plusieurs dossiers « Relations » à la racine du compte Cap : garde-en un seul.' : 'Aucun dossier « Relations » à la racine du compte Cap.'; return false; }
      if (!dossiers.length) { etat.textContent = 'Aucune musique ni vidéo dans les dossiers « r_ » de « Relations ».'; return false; } // 10/11/2026 ; avant : « Aucun MP3… », puis « Aucune musique… »
      return true;
    };

    ouvrir.addEventListener('click', () => attenteLecture.pendant(ouvrir, async () => {
      try {
        if (!await chargerDossiers()) return;
        // Un seul dossier avec de la musique : sa liste directement.
        if (dossiers.length === 1) montrerMorceaux(dossiers[0]); else montrerDossiers();
      } catch (erreur) { etat.textContent = `${raison(erreur)} Rien n’a été modifié.`; }
    }));

    // « Reprendre la musique au morceau N » : la liste du bon dossier, puis ce morceau.
    reprendre.addEventListener('click', () => attenteLecture.pendant(reprendre, async () => {
      const r = lireReprise();
      if (!r) { montrerReprise(); return; }
      try {
        if (!await chargerDossiers()) return;
        const d = dossiers.find(x => x.id === r.dossier);
        const tous = d ? [...d.musique.libres, ...d.musique.albums.flatMap(a => a.morceaux)] : [];
        const morceau = tous.find(x => x.id === r.morceau);
        if (!d || !morceau) { etat.textContent = 'Ce morceau n’est plus dans « Relations ». Choisis-en un autre.'; oublierPlace(); montrerDossiers(); return; }
        montrerMorceaux(d, { sansLancement: true });
        lancer(d, morceau);
      } catch (erreur) { etat.textContent = `${raison(erreur)} Rien n’a été modifié.`; }
    }));

    reconnecter.addEventListener('click', autoriserDeNouveau);
    // Étape A (07/11/2026, accord de Max) : « Redonner l'accès à Google » recharge Cap (page de Google) et
    // coupe la musique : la place du morceau en cours est gardée avant (dossier et numéro, jamais un nom).
    const redonner = el('redonner-acces-google');
    if (redonner) {
      redonner.addEventListener('click', () => {
        if (fenetreLecteur.open && dossierEnCours && file[position]) garderPlace(dossierEnCours, file[position]);
      }, true);
    }
    // 08/11/2026 (demande de Max) : icône « Lecteur » de l'écran Autre : la musique du compte Cap directement,
    // comme l'œil ouvre la visionneuse. Jamais une fenêtre vide : identifiant absent, pas connecté, connexion
    // expirée, aucun « Relations » ou aucun MP3 = un message clair (et « Autoriser… » quand il le faut).
    // « Fermer » ramène à Autre (resté ouvert dessous).
    const boutonLecteur = el('ouvrir-lecteur');
    const autoriserMusique = el('autoriser-musique-relations');
    const proposerAutorisation = oui => { if (autoriserMusique) autoriserMusique.hidden = !oui; };
    let dejaOuvert = false;
    // 11/11/2026 (accord de Max, c139, ligne 1 de la liste ; défaut 6 de c72) : téléphone SANS RÉSEAU (mode avion…) : Cap
    // dit « Pas de réseau », la vraie cause, au lieu de « compte Cap pas connecté » ; pas de bouton « Autoriser… » (il ne
    // marcherait pas sans réseau). Rien n'est modifié. Avant : seul l'état de la connexion du compte était regardé.
    const PAS_DE_RESEAU = 'Pas de réseau : la musique du compte Cap se lit par Internet. Reconnecte le téléphone (mode avion ?), puis réessaie. Rien n’a été modifié.';
    async function ouvrirLecteur() {
      const premiereOuverture = !dejaOuvert;
      dejaOuvert = true;
      ouvrirFenetre();
      liste.replaceChildren();
      retour.hidden = true;
      avertissement.hidden = true;
      proposerAutorisation(false);
      if (typeof compte.adresse === 'function' && !compte.adresse()) {
        etat.textContent = 'Identifiant du compte Cap absent : écris-le d’abord dans « Réglages du Drive » (Autre, puis Réglages).';
        return;
      }
      if (!enLigne()) { etat.textContent = PAS_DE_RESEAU; return; } // c139
      if (typeof compte.connecte === 'function' && !compte.connecte()) {
        // 08/11/2026 : au retour de Google (refus, mauvais compte…), la raison donnée par le compte d'abord.
        // (seulement à la première ouverture de la page : ensuite, ce message serait périmé).
        const retour = premiereOuverture && typeof compte.retourRecent === 'function' && compte.retourRecent() && typeof compte.message === 'function' ? compte.message() : '';
        etat.textContent = retour || ('Le compte Cap n’est pas connecté (ou la connexion a expiré, au bout d’environ 1 h). '
          + 'Touche « Autoriser la lecture du compte Cap » : tu reviendras ici.');
        proposerAutorisation(true);
        return;
      }
      try {
        if (!await chargerDossiers()) return;
        if (dossiers.length === 1) montrerMorceaux(dossiers[0]); else montrerDossiers();
      } catch (erreur) {
        if (!enLigne()) { etat.textContent = PAS_DE_RESEAU; return; } // c139 : réseau perdu pendant la lecture
        const expire = estExpiration(erreur);
        etat.textContent = expire
          ? 'La connexion du compte Cap a expiré : touche « Autoriser la lecture du compte Cap », tu reviendras ici.'
          : `${raison(erreur)} Rien n’a été modifié.`;
        proposerAutorisation(expire);
      }
    }
    // Pas d'attenteLecture ici : elle remplacerait le dessin de l'icône par du texte ; la fenêtre s'ouvre tout de suite
    // et dit « Lecture du Drive… ». Un second appui pendant la lecture est ignoré.
    let lecteurEnCours = false;
    if (boutonLecteur) boutonLecteur.addEventListener('click', () => {
      if (lecteurEnCours) return;
      lecteurEnCours = true;
      ouvrirLecteur().finally(() => { lecteurEnCours = false; });
    });
    // 08/11/2026 (accord de Max) : retour direct dans la musique après la page de Google (marque de 10 min, sans identifiant).
    if (autoriserMusique) autoriserMusique.addEventListener('click', () => {
      try { if (stockage) stockage.setItem(CLE_RETOUR_MUSIQUE, String(maintenant())); } catch (erreur) { /* rien : retour habituel */ }
      try { compte.seConnecter(); } catch (erreur) {
        try { if (stockage) stockage.removeItem(CLE_RETOUR_MUSIQUE); } catch (e) { /* rien */ }
        etat.textContent = raison(erreur);
      }
    });
    fenetre.addEventListener('close', () => { if (!fenetre.open) proposerAutorisation(false); }); // « close » peut arriver après une réouverture
    ouvrir.addEventListener('click', () => proposerAutorisation(false), true);
    fermer.addEventListener('click', () => proposerAutorisation(false));
    reprendre.addEventListener('click', () => proposerAutorisation(false), true);

    retour.addEventListener('click', () => changerEcran(montrerDossiers)); // 08/11/2026 : même transition
    fermer.addEventListener('click', fermerFenetre);
    // « Arrêter et fermer » (posé sur le lecteur), ou fenêtre fermée autrement (retour du téléphone) :
    // la musique s'arrête, la mémoire est libérée, le lecteur est vidé (il se rechargera à la prochaine ouverture).
    // Le nettoyage se fait tout de suite (bouton, ou « cancel » du retour du téléphone), et l'événement
    // « close », qui peut arriver plus tard, ne nettoie que si le lecteur n'a pas été rouvert entre-temps.
    const nettoyer = () => {
      if (nettoye) return;
      nettoye = true;
      demande++;
      avance = null;
      etatLecteur.classList.remove('en-lecture');
      if (zencoderPret) zencoderPret.arreter();
      zencoderPret = null;
      if (typeof lecteur.vider === 'function') lecteur.vider();
      if (adresseEnCours) { urls.revokeObjectURL(adresseEnCours); adresseEnCours = null; }
      enArrierePlan = false; // 08/11/2026
      montrerIndicateur(false);
    };
    fenetreLecteur.addEventListener('cancel', nettoyer);
    // 08/11/2026 : « close » ne nettoie pas quand la musique passe en arrière-plan.
    fenetreLecteur.addEventListener('close', () => { if (!fenetreLecteur.open && !enArrierePlan) nettoyer(); });
    // « Arrêter et fermer » : bouton caché le 08/11/2026 (décision de Max, remplacé par le geste de haut en bas) ; code gardé.
    fermerLecteur.addEventListener('click', () => { nettoyer(); if (fenetreLecteur.open) fenetreLecteur.close(); });

    // ----- 08/11/2026 (décisions de Max) : deux sorties du lecteur -----
    // GESTE de haut en bas (bande du bord droit) : la musique s'ARRÊTE (fondu du son très court), le lecteur s'en va
    // en vapeur, puis la liste des morceaux ressort du sable derrière. BOUTON « Musique en arrière-plan » : la musique
    // CONTINUE, même disparition, et un petit indicateur (note de musique, en haut à droite) ramène au lecteur.
    const geste = el('geste-fermer-lecteur');
    const arrierePlan = el('arriere-plan-lecteur');
    const DUREE_FONDU_SON_MS = 300;
    const DUREE_VAPEUR_MS = transition ? transition.REGLAGES.sortieMs : 450;
    const animationsReduites = () => {
      const v = doc.defaultView;
      return Boolean(v && v.matchMedia && v.matchMedia('(prefers-reduced-motion: reduce)').matches);
    };
    // L'indicateur se pose dans la fenêtre ouverte du dessus (sinon il serait inerte sous elle), ou sur la page ;
    // en arrière-plan, jamais dans le lecteur qui s'en va (il passe tout de suite sur l'écran d'en dessous).
    function placerIndicateur() {
      if (!indicateur || indicateur.hidden) return;
      const ouvertes = [...doc.querySelectorAll('dialog[open]')].filter(d => !(enArrierePlan && d === fenetreLecteur));
      const cible = ouvertes.length ? ouvertes[ouvertes.length - 1] : doc.body;
      if (indicateur.parentNode !== cible) cible.appendChild(indicateur);
    }
    // 08/11/2026, 11h45 (décision de Max) : la note ronde est TOUJOURS là quand le lecteur est ouvert (discrète, un peu
    // transparente : la toucher = arrière-plan) et pleinement visible quand la musique joue en arrière-plan (la toucher =
    // retour au lecteur). Ni lecteur ni arrière-plan : cachée. (L'argument d'avant est ignoré : l'état décide.)
    function montrerIndicateur() {
      if (!indicateur) return;
      const visible = enArrierePlan || (fenetreLecteur.open && fermetureLecteur === null);
      indicateur.hidden = !visible;
      indicateur.classList.toggle('indicateur-discret', visible && !enArrierePlan);
      if (!visible) indicateur.classList.remove('indicateur-probleme');
      placerIndicateur();
    }
    if (indicateur && doc.defaultView && doc.defaultView.MutationObserver) {
      new doc.defaultView.MutationObserver(montrerIndicateur).observe(doc.body, { subtree: true, attributes: true, attributeFilter: ['open'] });
    }
    // Fondu du son : le volume descend à zéro en 0,3 s (pas de coupure nette).
    function attenuerSon() {
      const audio = zencoderPret && zencoderPret.audio;
      if (!audio || typeof audio.volume !== 'number') return;
      const depart = audio.volume;
      const debut = maintenant();
      const pas = setInterval(() => {
        const t = Math.min(1, (maintenant() - debut) / DUREE_FONDU_SON_MS);
        try { audio.volume = Math.max(0, depart * (1 - t)); } catch (erreur) { /* rien */ }
        if (t >= 1) clearInterval(pas);
      }, 25);
    }
    function quitterLecteur(arreter) {
      if (!fenetreLecteur.open || fermetureLecteur !== null) return;
      enArrierePlan = !arreter && Boolean(zencoderPret);
      if (arreter) attenuerSon();
      if (enArrierePlan) montrerIndicateur(); // la note devient pleinement visible tout de suite
      const reduit = animationsReduites();
      if (transition && fenetre.open) transition.reapparaitre(fenetre);
      const finir = () => {
        fermetureLecteur = null;
        fenetreLecteur.classList.remove('lecteur-vapeur');
        if (!enArrierePlan) nettoyer();
        if (fenetreLecteur.open) fenetreLecteur.close();
        montrerIndicateur();
      };
      const duree = reduit ? (arreter ? DUREE_FONDU_SON_MS : 0) : Math.max(DUREE_VAPEUR_MS, arreter ? DUREE_FONDU_SON_MS : 0);
      if (!reduit) fenetreLecteur.classList.add('lecteur-vapeur');
      if (!duree) { finir(); return; }
      fermetureLecteur = setTimeout(finir, duree);
      if (!enArrierePlan) montrerIndicateur(); // geste : la note s'en va avec le lecteur
    }
    if (geste) {
      let depart = null;
      geste.addEventListener('pointerdown', e => {
        depart = { id: e.pointerId, x: e.clientX, y: e.clientY, quand: maintenant() };
        try { geste.setPointerCapture(e.pointerId); } catch (erreur) { /* rien */ }
      });
      geste.addEventListener('pointerup', e => {
        const d = depart;
        depart = null;
        if (!d || d.id !== e.pointerId) return;
        const hauteur = (doc.defaultView && doc.defaultView.innerHeight) || 1;
        const bas = e.clientY - d.y;
        const cote = Math.abs(e.clientX - d.x);
        // Net, vers le bas : au moins 20 % de la hauteur, deux fois plus vertical que de côté, en moins de 1,5 s.
        if (bas >= 0.2 * hauteur && bas >= 2 * cote && maintenant() - d.quand <= 1500) quitterLecteur(true);
      });
      geste.addEventListener('pointercancel', () => { depart = null; });
    }
    // « Musique en arrière-plan » : bouton caché le 08/11/2026, 11h45 (la note le remplace) ; code gardé.
    if (arrierePlan) arrierePlan.addEventListener('click', () => quitterLecteur(false));
    if (indicateur) {
      indicateur.addEventListener('click', () => {
        // Lecteur ouvert : la musique passe en arrière-plan. En arrière-plan : retour au lecteur.
        if (!enArrierePlan) { if (fenetreLecteur.open) quitterLecteur(false); else montrerIndicateur(); return; }
        enArrierePlan = false;
        if (!fenetreLecteur.open) fenetreLecteur.showModal();
        montrerIndicateur();
      });
    }
    montrerReprise();

    // ----- 08/11/2026 (accord de Max, étape 2a des commandes vocales) : TÉLÉCOMMANDE du lecteur, pour la voix -----
    // Elle passe par les MÊMES boutons que le doigt quand le lecteur de Zencoder est chargé (lecture / pause, début,
    // volume) ; sinon (tests), directement par son lecteur audio. Chaque fonction rend la phrase que Cap dit.
    // Rien n'est envoyé à l'IA ; aucun nom n'est gardé.
    const PAS_DE_MUSIQUE = 'Aucune musique en cours.';
    const actif = () => Boolean(zencoderPret && (fenetreLecteur.open || enArrierePlan) && fermetureLecteur === null);
    const audio = () => (zencoderPret && zencoderPret.audio) || null;
    const boutonZencoder = id => {
      try { const d = el('cadre-lecteur-mp3') && el('cadre-lecteur-mp3').contentDocument; return d ? d.getElementById(id) : null; } catch (erreur) { return null; }
    };
    const enPause = () => { const a = audio(); return Boolean(a && a.paused); };
    const lireVolume = () => { const a = audio(); return a && typeof a.volume === 'number' ? Math.round(a.volume * 100) : null; };
    function ecrireVolume(n) {
      const v = Math.max(0, Math.min(100, Math.round(n)));
      const curseur = boutonZencoder('curseur-volume');
      if (curseur) { curseur.value = String(v); curseur.dispatchEvent(new curseur.ownerDocument.defaultView.Event('input', { bubbles: true })); }
      const a = audio();
      if (a) { try { a.volume = v / 100; } catch (erreur) { /* rien */ } }
      return v;
    }
    let volumeAvantCoupure = null;
    function basculer(vouluEnPause) {
      const a = audio();
      if (!a || enPause() === vouluEnPause) return;
      const bouton = boutonZencoder('bouton-lecture');
      if (bouton) { bouton.click(); return; }
      if (vouluEnPause) { if (typeof a.pause === 'function') a.pause(); else zencoderPret.arreter(); } else if (typeof a.play === 'function') a.play();
    }
    function positionner(secondes) {
      const a = audio();
      if (!a) return null;
      const duree = Number.isFinite(a.duration) ? a.duration : Infinity;
      const s = Math.max(0, Math.min(duree, secondes));
      try { a.currentTime = s; } catch (erreur) { /* rien */ }
      return s;
    }
    const enMinutes = s => { const m = Math.floor(s / 60); const r = Math.round(s % 60); return m ? `${m} minute${m > 1 ? 's' : ''}${r ? ` ${r}` : ''}` : `${r} seconde${r > 1 ? 's' : ''}`; };
    const telecommande = {
      etat: () => ({ actif: actif(), arrierePlan: enArrierePlan, enPause: enPause(), volume: lireVolume(), titre: actif() && file[position] ? file[position].nom : '',
        pauseVoulue: pauseVoulue && enPause() }), // 08/11/2026 : + pauseVoulue
      pause() { if (!actif()) return PAS_DE_MUSIQUE; pauseVoulue = true; if (enPause()) return 'La musique est déjà en pause.'; basculer(true); return 'Pause.'; },
      reprendre() { if (!actif()) return PAS_DE_MUSIQUE; pauseVoulue = false; if (!enPause()) return 'La musique joue déjà.'; basculer(false); return 'Je reprends la musique.'; },
      arreter() {
        if (!actif()) return PAS_DE_MUSIQUE;
        if (fenetreLecteur.open && !enArrierePlan) { quitterLecteur(true); return 'Musique arrêtée.'; }
        attenuerSon();
        setTimeout(() => { enArrierePlan = false; nettoyer(); if (fenetreLecteur.open) fenetreLecteur.close(); montrerIndicateur(); }, DUREE_FONDU_SON_MS);
        return 'Musique arrêtée.';
      },
      suivant() {
        // 09/11/2026 (accord de Max, proposition B) : sans musique en cours, si une liste a été jouée depuis l'ouverture de
        // Cap (gardée en mémoire après l'arrêt), le morceau d'après se lance EN ARRIÈRE-PLAN (la note apparaît) ; sinon Cap
        // le dit. Le lecteur ne s'ouvre pas tout seul. Avant : if (!actif()) return PAS_DE_MUSIQUE;
        if (!actif()) {
          if (!dossierEnCours || !file.length || position < 0) return 'Il n’y a pas de morceau suivant : aucune musique n’a été lancée.';
          const apres = file[position + 1];
          if (!apres) return 'C’est le dernier morceau de la liste.';
          lancerEnArrierePlan(dossierEnCours, apres, file);
          return `Je mets le morceau suivant : « ${apres.nom} ».`;
        }
        const s = file[position + 1];
        if (!s) return 'C’est le dernier morceau de la liste.';
        position++;
        void jouer(s);
        return 'Morceau suivant.';
      },
      precedent() {
        if (!actif()) return PAS_DE_MUSIQUE;
        if (position < 1) return 'C’est le premier morceau de la liste.';
        position--;
        void jouer(file[position]);
        return 'Morceau précédent.';
      },
      debut() {
        if (!actif()) return PAS_DE_MUSIQUE;
        const bouton = boutonZencoder('bouton-debut');
        if (bouton) bouton.click(); else positionner(0);
        return 'Je reprends le morceau au début.';
      },
      rejouer() { if (!actif()) return PAS_DE_MUSIQUE; telecommande.debut(); basculer(false); return 'Je rejoue ce morceau.'; },
      volume(n) {
        if (!actif()) return PAS_DE_MUSIQUE;
        if (n <= 0) return telecommande.couper();
        volumeAvantCoupure = null;
        return `Volume à ${ecrireVolume(n)}.`;
      },
      plusFort(jusquAuBout = false) {
        if (!actif()) return PAS_DE_MUSIQUE;
        const v = lireVolume() ?? 80;
        if (v >= 100) return 'Le volume est déjà au maximum.';
        volumeAvantCoupure = null;
        return `Je monte le volume (${ecrireVolume(jusquAuBout ? 100 : v + 15)}).`;
      },
      moinsFort() {
        if (!actif()) return PAS_DE_MUSIQUE;
        const v = lireVolume() ?? 80;
        if (v <= 0) return 'Le son est déjà coupé.';
        return `Je baisse le volume (${ecrireVolume(Math.max(5, v - 15))}).`;
      },
      couper() {
        if (!actif()) return PAS_DE_MUSIQUE;
        const v = lireVolume();
        if (!v) return 'Le son est déjà coupé.';
        volumeAvantCoupure = v;
        ecrireVolume(0);
        return 'Son coupé.';
      },
      remettre() {
        if (!actif()) return PAS_DE_MUSIQUE;
        if (lireVolume()) return 'Le son est déjà là.';
        ecrireVolume(volumeAvantCoupure || 80);
        volumeAvantCoupure = null;
        return 'Son remis.';
      },
      titre() { if (!actif() || !file[position]) return PAS_DE_MUSIQUE; return `Ce morceau s’appelle « ${file[position].nom} ».`; },
      // secondes : déplacement (relatif, positif ou négatif) ou position précise (absolu).
      deplacer(secondes, absolu) {
        if (!actif()) return PAS_DE_MUSIQUE;
        const a = audio();
        const depart = a && Number.isFinite(a.currentTime) ? a.currentTime : 0;
        const s = positionner(absolu ? secondes : depart + secondes);
        if (s === null) return PAS_DE_MUSIQUE;
        return absolu ? `Je vais à ${enMinutes(s)}.` : (secondes < 0 ? `Je recule de ${enMinutes(-secondes)}.` : `J’avance de ${enMinutes(secondes)}.`);
      },
      arrierePlan() {
        if (!actif()) return PAS_DE_MUSIQUE;
        if (enArrierePlan) return 'La musique est déjà en arrière-plan.';
        quitterLecteur(false);
        return 'La musique continue en arrière-plan.';
      },
      // Afficher le lecteur (ou le ramener devant) ; sans musique : la musique du compte Cap (icône « Lecteur »).
      afficher() {
        if (actif() && enArrierePlan) {
          enArrierePlan = false;
          if (!fenetreLecteur.open) fenetreLecteur.showModal();
          montrerIndicateur();
          return 'Voici le lecteur.';
        }
        // 09/11/2026 (défaut 1 vu par Max : jamais un pouce sans effet) : déjà affiché : Cap le DIT (croix).
        // Avant : if (actif()) return ''; // déjà affiché : rien (question 32)
        if (actif()) return 'Le lecteur est déjà affiché.';
        if (boutonLecteur) { boutonLecteur.click(); return 'J’ouvre la musique.'; }
        return 'Le lecteur n’est pas disponible ici.';
      },
      // Masquer : déjà caché en arrière-plan = rien d'arrêté ; lecteur affiché = arrêté (règle de Max, question 24).
      masquer() {
        if (!actif()) return 'Le lecteur n’est pas affiché.';
        if (enArrierePlan) return 'Le lecteur est déjà caché ; la musique continue. Dis « arrête la musique » pour l’arrêter.';
        quitterLecteur(true);
        return 'Lecteur fermé, musique arrêtée.';
      }
    };
    // ----- 08/11/2026 (accord de Max, étape 2b) : LANCER la musique à la voix -----
    // Cap cherche lui-même (code, jamais l'IA) dans la musique du compte Cap : un morceau par son titre, la musique
    // d'une personne (dossier « r_Prénom Nom… » de « Relations » qui a de la musique), un album, ou au hasard
    // (seulement si Max a dit « au hasard »). Une seule réponse : elle se lance EN ARRIÈRE-PLAN (la note ronde),
    // pour que l'écran Micro reste là (le lecteur affiché le couvrirait ; « montre-moi le player » le ramène).
    // Plusieurs réponses : Cap ne devine jamais : il montre les choix en très gros, avec de gros numéros.
    // Pas connecté ou connexion expirée : la fenêtre « Musique » le dit, avec « Autoriser la lecture du compte Cap ».
    const MOTS_VIDES_MUSIQUE = new Set(['le', 'la', 'les', 'l', 'un', 'une', 'des', 'du', 'de', 'd', 'mon', 'ma', 'mes', 'ce', 'cet', 'cette',
      'morceau', 'morceaux', 'chanson', 'chansons', 'titre', 'musique', 'son', 'album', 'mp3', 'et']);
    const plierTexte = s => String(s || '').replace(/œ/g, 'oe').replace(/æ/g, 'ae').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
    const motsUtiles = s => plierTexte(s).split(' ').filter(m => m && !MOTS_VIDES_MUSIQUE.has(m));
    const personneDe = d => String(d.nom).replace(/^r_/, '').split('-')[0].trim();
    const tousLesMorceaux = d => [...d.musique.libres, ...d.musique.albums.flatMap(a => a.morceaux)];
    // 3 : même nom ; 2 : tous les mots dits sont dans le nom ; 0 : non.
    const score = (nom, requete) => {
      const mots = motsUtiles(requete);
      if (!mots.length) return 0;
      if (plierTexte(nom) === plierTexte(requete)) return 3; // vraiment le même nom (« un fictif » n'est pas « fictif »)
      const dans = ` ${plierTexte(nom)} `;
      return mots.every(m => dans.includes(` ${m} `)) ? 2 : 0;
    };
    const meilleurs = (elements, nomDe, requete) => {
      const notes = elements.map(e => ({ e, n: score(nomDe(e), requete) })).filter(x => x.n > 0);
      const max = Math.max(0, ...notes.map(x => x.n));
      return notes.filter(x => x.n === max).map(x => x.e);
    };
    let dernierePersonne = '';
    function lancerEnArrierePlan(d, morceau, liste) {
      if (fenetre.open) fermerFenetre();
      if (fenetreLecteur.open) fenetreLecteur.close();
      enArrierePlan = true;
      dossierEnCours = d;
      file = liste || listeDe(d, morceau);
      position = Math.max(0, file.indexOf(morceau));
      avance = null;
      oublierPlace();
      montrerIndicateur();
      void jouer(morceau);
    }
    const lancerTexte = (d, morceau) => `Je mets « ${morceau.nom} ».`;
    // Choix en très gros, gros numéros (au plus 9) ; un toucher lance (en arrière-plan, comme à la voix).
    function montrerChoix(choix, quoi) {
      const montres = choix.slice(0, 9);
      ouvrirFenetre();
      proposerAutorisation(false);
      retour.hidden = true;
      avertissement.hidden = true;
      etat.textContent = '';
      liste.replaceChildren(...montres.map((c, i) => {
        const bouton = noeud('button', 'ligne-morceau ligne-choix-voix');
        bouton.type = 'button';
        bouton.append(noeud('span', 'numero-morceau', String(i + 1)), noeud('span', 'nom-morceau', c.texte));
        bouton.addEventListener('click', c.lancer);
        return bouton;
      }));
      return `J’ai trouvé ${choix.length} ${quoi}${choix.length > montres.length ? ` (je montre les ${montres.length} premiers)` : ''} : touche le bon numéro.`;
    }
    async function bibliotheque() {
      if (typeof compte.adresse === 'function' && !compte.adresse()) return { message: 'Identifiant du compte Cap absent : écris-le d’abord dans « Réglages du Drive ».' };
      if (!enLigne()) { if (boutonLecteur) boutonLecteur.click(); return { message: 'Pas de réseau : je ne peux pas lire la musique du compte Cap. Reconnecte le téléphone, puis redemande.' }; } // c139
      if (typeof compte.connecte === 'function' && !compte.connecte()) {
        if (boutonLecteur) boutonLecteur.click(); // la fenêtre « Musique » dit pourquoi et montre « Autoriser… »
        return { message: 'Le compte Cap n’est pas connecté (ou la connexion a expiré) : touche « Autoriser la lecture du compte Cap ».' };
      }
      try {
        const r = dossiersAvecMp3(await arbre(), sorte);
        if (r.racines !== 1) return { message: r.racines ? 'Plusieurs dossiers « Relations » dans le compte Cap : garde-en un seul.' : 'Aucun dossier « Relations » dans le compte Cap.' };
        // 10/11/2026 (décision de Max) : les commandes vocales de MUSIQUE ne prennent que les dossiers qui ont de la musique
        // (un dossier avec seulement des vidéos n'y entre pas). Avant : tous les dossiers de la liste (qui avaient tous de la musique).
        const avecMusique = r.dossiers.filter(d => d.musique.total > 0);
        if (!avecMusique.length) return { message: 'Aucune musique dans les dossiers « Relations » du compte Cap.' };
        dossiers = r.dossiers;
        return { dossiers: avecMusique };
      } catch (erreur) {
        if (estExpiration(erreur)) { if (boutonLecteur) boutonLecteur.click(); return { message: 'La connexion du compte Cap a expiré : touche « Autoriser la lecture du compte Cap ».' }; }
        return { message: `Je n’ai pas pu lire la musique du compte Cap : ${raison(erreur)}` };
      }
    }
    // demande : { titre, prenom, album, tout, auHasard }
    telecommande.lancerVoix = async function lancerVoix(demande = {}) {
      const b = await bibliotheque();
      if (!b.dossiers) return b.message;
      let ds = b.dossiers;
      let prenom = demande.prenom ? String(demande.prenom) : '';
      if (/^(lui|elle)$/.test(plierTexte(prenom))) prenom = dernierePersonne; // question 41 : la dernière personne citée
      if (prenom) {
        ds = ds.filter(d => score(personneDe(d), prenom) > 0);
        if (!ds.length) return `Je ne trouve pas de musique de « ${prenom} » dans Cap.`;
        if (ds.length > 1) {
          return montrerChoix(ds.map(d => ({ texte: personneDe(d), lancer: () => { const t = tousLesMorceaux(d); lancerEnArrierePlan(d, t[0], t); } })), 'personnes');
        }
        dernierePersonne = personneDe(ds[0]);
      }
      const morceaux = ds.flatMap(d => tousLesMorceaux(d).map(m => ({ d, m })));
      const jouables = morceaux.filter(x => x.m.taille <= TAILLE_MAX);
      if (demande.auHasard) {
        if (!jouables.length) return 'Aucun morceau jouable.';
        const x = jouables[Math.min(jouables.length - 1, Math.floor(hasard() * jouables.length))];
        lancerEnArrierePlan(x.d, x.m);
        return lancerTexte(x.d, x.m);
      }
      const albums = ds.flatMap(d => d.musique.albums.map(a => ({ d, a })));
      const lancerAlbum = x => lancerEnArrierePlan(x.d, x.a.morceaux[0], x.a.morceaux);
      if (demande.album) {
        const trouves = meilleurs(albums, x => x.a.nom, demande.album);
        if (!trouves.length) return `Je ne trouve pas d’album « ${demande.album} ».`;
        if (trouves.length > 1) return montrerChoix(trouves.map(x => ({ texte: `${x.a.nom} · ${personneDe(x.d)}`, lancer: () => lancerAlbum(x) })), 'albums');
        lancerAlbum(trouves[0]);
        return `Je mets l’album « ${trouves[0].a.nom} ».`;
      }
      if (demande.titre) {
        const trouves = meilleurs(morceaux, x => x.m.nom, demande.titre);
        if (trouves.length === 1) { lancerEnArrierePlan(trouves[0].d, trouves[0].m); return lancerTexte(trouves[0].d, trouves[0].m); }
        if (trouves.length > 1) return montrerChoix(trouves.map(x => ({ texte: `${x.m.nom} · ${personneDe(x.d)}`, lancer: () => lancerEnArrierePlan(x.d, x.m) })), 'morceaux');
        const parAlbum = meilleurs(albums, x => x.a.nom, demande.titre);
        if (parAlbum.length === 1) { lancerAlbum(parAlbum[0]); return `Je mets l’album « ${parAlbum[0].a.nom} ».`; }
        return `Je ne trouve pas de morceau « ${demande.titre} ».`;
      }
      if (prenom) {
        const d = ds[0];
        const t = tousLesMorceaux(d);
        lancerEnArrierePlan(d, t[0], t);
        return demande.tout ? `Je mets toute la musique de ${personneDe(d)}.` : lancerTexte(d, t[0]);
      }
      // Rien de précis : la fenêtre « Musique » (dossiers), pour toucher le morceau.
      if (boutonLecteur) boutonLecteur.click();
      return 'Quel morceau ? Touche-le dans la liste.';
    };
    // ----- 09/11/2026 (décision de Max, bloc c74) : la PLAYLIST PAR DÉFAUT -----
    // Rien n'est gardé : la liste est refaite à chaque fois depuis le Drive du compte Cap (un MP3 ajouté y entre tout seul) :
    // tous les MP3 jouables (60 Mo au plus) des dossiers « r_ » de « Relations », dossier par dossier (ordre des noms),
    // puis dans l'ordre des morceaux. Elle part TOUJOURS du premier morceau, lecteur affiché (il « s'allume »).
    telecommande.lancerPlaylist = async function lancerPlaylist() {
      const b = await bibliotheque();
      if (!b.dossiers) return b.message;
      const tous = [];
      for (const d of b.dossiers) for (const m of tousLesMorceaux(d)) if (m.taille <= TAILLE_MAX) { tous.push(m); dossierDuMorceau.set(m, d); }
      if (!tous.length) return 'Aucun morceau jouable dans les dossiers « Relations » du compte Cap.';
      if (fenetre.open) fermerFenetre();
      enArrierePlan = false;
      montrerIndicateur(false);
      dossierEnCours = dossierDuMorceau.get(tous[0]);
      file = tous;
      position = 0;
      avance = null;
      oublierPlace();
      void jouer(tous[0]);
      return `Je mets la musique : ${tous.length} morceau${tous.length > 1 ? 'x' : ''}, en commençant par le premier.`;
    };
    // « Choisir » (un MP3 du téléphone) : le lecteur s'affiche ; c'est Max qui touche « Choisir » (Android n'ouvre
    // le choix des fichiers qu'après un vrai toucher).
    telecommande.choisirFichier = function choisirFichier() {
      if (actif() && enArrierePlan) telecommande.afficher();
      else if (!fenetreLecteur.open) {
        fenetreLecteur.showModal();
        nettoye = false;
        montrerIndicateur();
        Promise.resolve(lecteur()).then(z => { if (fenetreLecteur.open) { zencoderPret = z; surveillerFin(z); } }).catch(erreur => message(`Le lecteur n’a pas pu démarrer : ${raison(erreur)}`));
      }
      return 'Touche « Choisir » dans le lecteur pour prendre un morceau du téléphone.'; // 10/11/2026 ; avant : « un MP3 »
    };
    return telecommande;
  }

  return { nomMorceau, trier, morceauxDe, dossiersAvecMp3, chargeurLecteur, retoucherLecteur, brancher, TAILLE_MAX, CLE_RETOUR_MUSIQUE };
})();

if (!(typeof window !== 'undefined' && window.CAP_TESTS)) {
  // 08/11/2026 (étape 2a) : la télécommande est gardée (commandes vocales). Avant : relationsMp3.brancher(document, {…}) sans garder.
  relationsMp3.instance = relationsMp3.brancher(document, {
    compte: googleCompteRelations,
    arbre: () => relationsCompte.lireArbre(googleCompteRelations),
    sorte: relationsCompte.sorte,
    lecteur: relationsMp3.chargeurLecteur(document.getElementById('cadre-lecteur-mp3'))
  });
}
