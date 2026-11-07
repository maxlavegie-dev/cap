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
    const sansExtension = String(nomFichier || '').replace(/\.mp3$/i, '').trim();
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
  function morceauxDe(arbre, sorte, idDossier) {
    const libres = [];
    const albums = [];
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
        } else if (sorte(fichier) === 'mp3') {
          (album ? album.morceaux : libres).push({
            id: fichier.id, nomFichier: String(fichier.name || ''), nom: nomMorceau(fichier.name), taille: Number(fichier.size) || 0
          });
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
    return resultat;
  }

  // Dossiers « r_ » de « Relations » (racine du compte Cap) qui contiennent au moins un MP3.
  function dossiersAvecMp3(arbre, sorte) {
    const racines = arbre.enfants(arbre.racine).filter(x => x.name === 'Relations' && x.mimeType === DOSSIER);
    if (racines.length !== 1) return { racines: racines.length, dossiers: [] };
    const dossiers = arbre.enfants(racines[0].id)
      .filter(x => x.mimeType === DOSSIER && String(x.name).startsWith('r_'))
      .map(x => ({ id: x.id, nom: String(x.name), musique: morceauxDe(arbre, sorte, x.id) }))
      .filter(x => x.musique.total > 0)
      .sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));
    return { racines: 1, dossiers };
  }

  // Lecteur de Zencoder dans un cadre de la page.
  // 07/11/2026 (accord de Max) : rechargé à chaque ouverture (la sortie du sable se rejoue) et vidé
  // à la fermeture (son animation s'arrête) : « vider » remet le cadre sur une page blanche.
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
            if (lecteur && typeof lecteur.jouerFichier === 'function' && typeof lecteur.arreter === 'function') ok(lecteur);
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

  function brancher(doc, { compte, arbre, sorte, lecteur, urls = URL, stockage = localStorage }) {
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
    const noeud = (balise, classe, texte) => {
      const n = doc.createElement(balise);
      if (classe) n.className = classe;
      if (texte !== undefined) n.textContent = texte;
      return n;
    };
    let dossiers = [];
    let dossierEnCours = null;
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
      etat.textContent = `${dossiers.length} dossier(s) avec de la musique. Touche un dossier.`;
      liste.replaceChildren(...dossiers.map(d => {
        const bouton = noeud('button', 'choix-grand-affichage', `${d.nom} (${d.musique.total} MP3)`);
        bouton.type = 'button';
        bouton.addEventListener('click', () => montrerMorceaux(d));
        return bouton;
      }));
    };

    // La liste (morceaux libres, ou album) qui contient ce morceau.
    const listeDe = (d, morceau) => [d.musique.libres, ...d.musique.albums.map(a => a.morceaux)].find(l => l.includes(morceau)) || [morceau];

    const ligne = (d, morceau) => {
      const bouton = noeud('button', 'ligne-morceau');
      bouton.type = 'button';
      bouton.append(noeud('span', 'numero-morceau', String(morceau.numero)), noeud('span', 'nom-morceau', morceau.nom));
      bouton.addEventListener('click', () => choisir(d, morceau));
      return bouton;
    };

    const montrerMorceaux = (d, { sansLancement = false } = {}) => {
      dossierEnCours = d;
      retour.hidden = dossiers.length < 2;
      avertissement.hidden = true;
      etat.textContent = `${d.nom} : ${d.musique.total} MP3. Touche un morceau.`;
      const blocs = [];
      if (d.musique.libres.length) blocs.push(noeud('h3', 'titre-liste-morceaux', 'Morceaux'), ...d.musique.libres.map(m => ligne(d, m)));
      for (const album of d.musique.albums) {
        blocs.push(noeud('h3', 'titre-liste-morceaux', `${album.nom} (liste de lecture, ${album.morceaux.length})`), ...album.morceaux.map(m => ligne(d, m)));
      }
      liste.replaceChildren(...blocs);
      // Un seul morceau : lancement direct.
      if (d.musique.total === 1 && !sansLancement) lancer(d, d.musique.libres[0] || d.musique.albums[0].morceaux[0]);
    };

    // Avant une liste de plusieurs morceaux : la connexion tiendra-t-elle ?
    const choisir = (d, morceau) => {
      const l = listeDe(d, morceau);
      const restants = l.length - l.indexOf(morceau) - 1;
      const minutes = typeof compte.minutesRestantes === 'function' ? compte.minutesRestantes() : Infinity;
      if (restants < 1 || minutes >= MINUTES_AVANT_LISTE) { lancer(d, morceau); return; }
      const autoriser = noeud('button', 'relations-gros-bouton', 'Autoriser la lecture du compte Cap');
      autoriser.type = 'button';
      autoriser.addEventListener('click', () => { garderPlace(d, morceau); autoriserDeNouveau(); });
      const quandMeme = noeud('button', 'relations-gros-bouton', 'Jouer quand même');
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
        if (!fenetreLecteur.open || zencoderPret !== zencoder) return;
        const suivant = file[position + 1];
        if (!suivant) return;
        position++;
        void jouer(suivant);
      });
    };

    // Connexion expirée : la place est gardée, puis « Autoriser » (la page de Google, puis le retour dans Cap).
    const expiree = morceau => {
      if (dossierEnCours) garderPlace(dossierEnCours, morceau);
      message(`La connexion du compte Cap a expiré. Touche « Autoriser la lecture du compte Cap » : ensuite, « Reprendre la musique au morceau ${morceau.numero} » relancera ce morceau.`);
      reconnecter.hidden = false;
    };

    async function jouer(morceau) {
      const numeroDemande = ++demande;
      reconnecter.hidden = true;
      if (!fenetreLecteur.open) fenetreLecteur.showModal();
      nettoye = false;
      if (morceau.taille > TAILLE_MAX) {
        message(`« ${morceau.nom} » est trop gros (${Math.round(morceau.taille / 1e6)} Mo, plus de 60 Mo) : pas chargé.`);
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
        if (numeroDemande !== demande || !fenetreLecteur.open) return;
        const adresse = urls.createObjectURL(contenu);
        zencoder.jouerFichier(adresse, `${morceau.numero}. ${morceau.nom}`);
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
      if (!fenetre.open) fenetre.showModal();
      liste.replaceChildren();
      retour.hidden = true;
      avertissement.hidden = true;
      etat.textContent = 'Lecture du Drive du compte Cap… (rien n’est modifié)';
      const r = dossiersAvecMp3(await arbre(), sorte);
      dossiers = r.dossiers;
      if (r.racines !== 1) { etat.textContent = r.racines ? 'Plusieurs dossiers « Relations » à la racine du compte Cap : garde-en un seul.' : 'Aucun dossier « Relations » à la racine du compte Cap.'; return false; }
      if (!dossiers.length) { etat.textContent = 'Aucun MP3 dans les dossiers « r_ » de « Relations ».'; return false; }
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
    retour.addEventListener('click', montrerDossiers);
    fermer.addEventListener('click', () => fenetre.close());
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
    };
    fenetreLecteur.addEventListener('cancel', nettoyer);
    fenetreLecteur.addEventListener('close', () => { if (!fenetreLecteur.open) nettoyer(); });
    fermerLecteur.addEventListener('click', () => { nettoyer(); if (fenetreLecteur.open) fenetreLecteur.close(); });
    montrerReprise();
  }

  return { nomMorceau, trier, morceauxDe, dossiersAvecMp3, chargeurLecteur, brancher, TAILLE_MAX };
})();

if (!(typeof window !== 'undefined' && window.CAP_TESTS)) {
  relationsMp3.brancher(document, {
    compte: googleCompteRelations,
    arbre: () => relationsCompte.lireArbre(googleCompteRelations),
    sorte: relationsCompte.sorte,
    lecteur: relationsMp3.chargeurLecteur(document.getElementById('cadre-lecteur-mp3'))
  });
}
