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

  function brancher(doc, { compte, arbre, sorte, lecteur, urls = URL }) {
    const el = id => doc.getElementById(id);
    const ouvrir = el('musique-compte-relations');
    const fenetre = el('musique-relations');
    const etat = el('etat-musique-relations');
    const liste = el('liste-musique-relations');
    const retour = el('retour-musique-relations');
    const fermer = el('fermer-musique-relations');
    const fenetreLecteur = el('lecteur-mp3-relations');
    const etatLecteur = el('etat-lecteur-mp3');
    const fermerLecteur = el('fermer-lecteur-mp3');
    if (![ouvrir, fenetre, etat, liste, retour, fermer, fenetreLecteur, etatLecteur, fermerLecteur].every(Boolean)) return;
    const raison = erreur => String(erreur && erreur.message || 'raison inconnue').slice(0, 220);
    const noeud = (balise, classe, texte) => {
      const n = doc.createElement(balise);
      if (classe) n.className = classe;
      if (texte !== undefined) n.textContent = texte;
      return n;
    };
    let dossiers = [];
    let adresseEnCours = null;
    // Lecteur de Zencoder, une fois chargé (fermer ne le charge jamais pour rien).
    let zencoderPret = null;
    let demande = 0;

    const montrerDossiers = () => {
      retour.hidden = true;
      etat.textContent = `${dossiers.length} dossier(s) avec de la musique. Touche un dossier.`;
      liste.replaceChildren(...dossiers.map(d => {
        const bouton = noeud('button', 'choix-grand-affichage', `${d.nom} (${d.musique.total} MP3)`);
        bouton.type = 'button';
        bouton.addEventListener('click', () => montrerMorceaux(d));
        return bouton;
      }));
    };

    const ligne = morceau => {
      const bouton = noeud('button', 'ligne-morceau');
      bouton.type = 'button';
      bouton.append(noeud('span', 'numero-morceau', String(morceau.numero)), noeud('span', 'nom-morceau', morceau.nom));
      bouton.addEventListener('click', () => { void jouer(morceau); });
      return bouton;
    };

    const montrerMorceaux = d => {
      retour.hidden = dossiers.length < 2;
      etat.textContent = `${d.nom} : ${d.musique.total} MP3. Touche un morceau.`;
      const blocs = [];
      if (d.musique.libres.length) blocs.push(noeud('h3', 'titre-liste-morceaux', 'Morceaux'), ...d.musique.libres.map(ligne));
      for (const album of d.musique.albums) {
        blocs.push(noeud('h3', 'titre-liste-morceaux', `${album.nom} (liste de lecture, ${album.morceaux.length})`), ...album.morceaux.map(ligne));
      }
      liste.replaceChildren(...blocs);
      // Un seul morceau : lancement direct.
      if (d.musique.total === 1) void jouer(d.musique.libres[0] || d.musique.albums[0].morceaux[0]);
    };

    // Message posé sur le lecteur, seulement pendant le chargement ou en cas de problème.
    // 07/11/2026 (demande de Max) : le titre « Morceau N : nom » au-dessus du lecteur est désactivé
    // (il répétait le titre affiché par le lecteur) : une fois le morceau lancé, le message est caché.
    const message = texte => { etatLecteur.hidden = false; etatLecteur.textContent = texte; };

    async function jouer(morceau) {
      const numeroDemande = ++demande;
      if (!fenetreLecteur.open) fenetreLecteur.showModal();
      if (morceau.taille > TAILLE_MAX) {
        message(`« ${morceau.nom} » est trop gros (${Math.round(morceau.taille / 1e6)} Mo, plus de 60 Mo) : pas chargé.`);
        return;
      }
      message(`Lecture en cours… (chargement de « ${morceau.nom} »)`);
      etatLecteur.classList.add('en-lecture');
      try {
        const [zencoder, reponse] = await Promise.all([lecteur(), compte.appeler(`${drive}/${encodeURIComponent(morceau.id)}?alt=media`)]);
        zencoderPret = zencoder;
        const contenu = await reponse.blob();
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
      } catch (erreur) {
        if (numeroDemande === demande) message(`Morceau non lu : ${raison(erreur)}`);
      } finally {
        if (numeroDemande === demande) etatLecteur.classList.remove('en-lecture');
      }
    }

    ouvrir.addEventListener('click', () => attenteLecture.pendant(ouvrir, async () => {
      if (!fenetre.open) fenetre.showModal();
      liste.replaceChildren();
      retour.hidden = true;
      etat.textContent = 'Lecture du Drive du compte Cap… (rien n’est modifié)';
      try {
        const r = dossiersAvecMp3(await arbre(), sorte);
        dossiers = r.dossiers;
        if (r.racines !== 1) { etat.textContent = r.racines ? 'Plusieurs dossiers « Relations » à la racine du compte Cap : garde-en un seul.' : 'Aucun dossier « Relations » à la racine du compte Cap.'; return; }
        if (!dossiers.length) { etat.textContent = 'Aucun MP3 dans les dossiers « r_ » de « Relations ».'; return; }
        // Un seul dossier avec de la musique : sa liste directement.
        if (dossiers.length === 1) montrerMorceaux(dossiers[0]); else montrerDossiers();
      } catch (erreur) { etat.textContent = `${raison(erreur)} Rien n’a été modifié.`; }
    }));
    retour.addEventListener('click', montrerDossiers);
    fermer.addEventListener('click', () => fenetre.close());
    // « Arrêter et fermer » (posé sur le lecteur), ou fenêtre fermée autrement (retour du téléphone) :
    // la musique s'arrête, la mémoire est libérée, le lecteur est vidé (il se rechargera à la prochaine ouverture).
    fenetreLecteur.addEventListener('close', () => {
      demande++;
      etatLecteur.classList.remove('en-lecture');
      if (zencoderPret) zencoderPret.arreter();
      zencoderPret = null;
      if (typeof lecteur.vider === 'function') lecteur.vider();
      if (adresseEnCours) { urls.revokeObjectURL(adresseEnCours); adresseEnCours = null; }
    });
    fermerLecteur.addEventListener('click', () => { if (fenetreLecteur.open) fenetreLecteur.close(); });
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
