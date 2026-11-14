'use strict';

// 12/11/2026 (accord écrit de Max, marches M3a, M3b, M3c) : les deux boutons des MMS dans « Réglages du Drive ».
// - « Lire mes derniers MMS » : demande l'autorisation SMS d'Android si besoin (Max accepte ou refuse), lit les 20 derniers
//   MMS reçus, les classe (personne / à trier) et affiche des NOMBRES seulement. Rien n'est copié, rien n'est envoyé.
// - « Répétition MMS » : montre ce qui serait créé dans le compte Cap (dossiers VIDES et FICTIFS) et où iraient de faux
//   messages ; rien n'est créé sans « Oui, créer ». Aucun dossier « r_ », aucun vrai MMS.
// Le DOM : textContent seulement.
const mmsEcran = (() => {
  // 14/11/2026 (P7d) : tailleDialogue : la taille maximale d'un fichier « Dialogue » (4 Mo ; plus petite seulement pour les tests FICTIFS).
  function brancher(doc, { compte, stockage = (typeof localStorage !== 'undefined' ? localStorage : null), fenetre = window, tailleDialogue = mmsDialogue.TAILLE_FICHIER } = {}) {
    const el = id => doc.getElementById(id);
    const lire = el('lire-mms');
    const repetition = el('repetition-mms');
    const zone = el('resultat-mms');
    const barre = el('barre-mms');
    const oui = el('oui-mms');
    const non = el('non-mms');
    if (![lire, repetition, zone, barre, oui, non].every(Boolean) || !compte) return null;
    const montrer = (texte, question = false) => {
      zone.hidden = false;
      zone.textContent = texte;
      barre.hidden = !question;
      oui.disabled = false;
      oui.textContent = question && (attendu === 'copie' || attendu === 'dialogue') ? 'Oui, copier' : 'Oui, créer'; // 14/11/2026 (P6, P7c)
      try { zone.scrollIntoView({ block: 'nearest' }); } catch (erreur) {}
    };
    const raison = erreur => String(erreur && erreur.message || 'raison inconnue').slice(0, 220);
    let occupe = false;
    let attendu = 'creer'; // 14/11/2026 (P6) : déclaré ici (montrer s'en sert)

    async function lireMms() {
      if (occupe) return '';
      if (!mmsLecture.disponible(fenetre)) { montrer('La lecture des MMS se fait seulement dans l’application Cap du téléphone.'); return ''; }
      occupe = true;
      try {
        if (!mmsLecture.autorise(fenetre)) {
          montrer('Android va te demander l’autorisation de lire tes SMS et MMS. Cap les lit seulement : il n’envoie, n’efface et ne copie rien.');
          if (!(await mmsLecture.demander(fenetre))) { montrer('Autorisation refusée : rien n’a été lu.'); return ''; }
        }
        montrer('Lecture en cours… (rien n’est copié ni envoyé)');
        const { cle, index, personnes, dossiers } = await mmsRangement.preparerIndex(stockage);
        const messages = await mmsLecture.lireRecents(cle, fenetre);
        const t = mmsRangement.texte(mmsRangement.resumer(mmsRangement.classer(messages, index), dossiers)); // c177 : + les dossiers r_ (nombres)
        const avertissement = personnes ? '' : ' (Aucun numéro de relation dans la copie des coordonnées : touche d’abord « Tout synchroniser ».)';
        montrer(t + avertissement);
        return t;
      } catch (erreur) {
        montrer(`${raison(erreur)} Rien n’a été copié ni envoyé.`);
        return '';
      } finally { occupe = false; }
    }

    async function preparerRepetition() {
      if (occupe) return '';
      if (!compte.connecte()) { montrer('Le compte Cap n’est pas connecté : touche « Autoriser la lecture du compte Cap », puis recommence.'); return ''; }
      occupe = true;
      try {
        montrer('Lecture du compte Cap… (rien n’est modifié)');
        const p = await mmsRepetition.preparer(compte);
        const demo = `Avec de faux messages, voici où ils iraient : ${mmsRepetition.demonstration().join(' ; ')}.`;
        if (!p.aCreer.length) { montrer(`Les dossiers de répétition existent déjà dans le compte Cap : rien à créer. ${demo}`); return ''; }
        attendu = 'creer'; // 13/11/2026 (P4) : la barre Oui/Non sert aussi à l'essai d'envoi
        montrer(`Répétition FICTIVE. Cap va créer, dans le Drive du compte Cap, des dossiers VIDES : ${p.aCreer.join(', ')}. Aucun dossier « r_ », aucun vrai MMS, rien d’effacé. ${demo} Créer ?`, true);
        return 'question';
      } catch (erreur) {
        montrer(`${raison(erreur)} Rien n’a été créé.`);
        return '';
      } finally { occupe = false; }
    }

    // ----- 13/11/2026 (accord de Max, P4 = M3d) : « Essai d'envoi » : UN faux fichier FICTIF dans « Personne Test FICTIF »
    // (répétition, compte Cap), après la question et le Oui de Max. Rien remplacé, rien effacé ; déjà envoyé : jamais renvoyé.
    const essai = el('essai-envoi-mms');
    async function preparerEssai() {
      if (occupe) return '';
      if (!compte.connecte()) { montrer('Le compte Cap n’est pas connecté : touche « Autoriser la lecture du compte Cap », puis recommence.'); return ''; }
      occupe = true;
      try {
        montrer('Lecture du compte Cap… (rien n’est modifié)');
        const p = await mmsRepetition.preparerEnvoi(compte);
        if (p.dejaLa) { montrer(`Le fichier d’essai « ${p.nom} » a déjà été envoyé${p.corbeille ? ' (il est à la corbeille)' : ''} : rien n’est renvoyé.`); return ''; }
        if (!p.pret) { montrer(p.raison); return ''; }
        attendu = 'envoi';
        montrer(`Essai FICTIF : Cap va envoyer UN faux fichier texte « ${p.nom} » dans le dossier de répétition « ${p.dossier} » (Drive du compte Cap). Aucun vrai message, rien remplacé, rien effacé. Envoyer ?`, true);
        return 'question';
      } catch (erreur) {
        montrer(`${raison(erreur)} Rien n’a été envoyé.`);
        return '';
      } finally { occupe = false; }
    }
    async function confirmerEnvoi() {
      try {
        montrer('Envoi en cours… (rien n’est remplacé ni effacé)');
        const r = await mmsRepetition.envoyerEssai(compte);
        const t = r.dejaLa ? `Le fichier d’essai avait déjà été envoyé${r.corbeille ? ' (il est à la corbeille)' : ''} : rien n’est renvoyé.` : `C’est fait : « ${r.nom} » est dans « ${r.dossier} » (répétition, Drive du compte Cap).`;
        montrer(t);
        return t;
      } catch (erreur) {
        const t = `${raison(erreur)}`;
        montrer(t);
        return t;
      }
    }
    if (essai) essai.addEventListener('click', () => { void preparerEssai(); });

    async function confirmer() {
      if (occupe || barre.hidden) return '';
      occupe = true;
      oui.disabled = true;
      if (attendu === 'envoi') { try { return await confirmerEnvoi(); } finally { attendu = 'creer'; occupe = false; } }
      if (attendu === 'copie') { try { return await confirmerCopie(); } finally { attendu = 'creer'; occupe = false; } } // 14/11/2026 (P6)
      if (attendu === 'dialogue') { try { return await confirmerDialogue(); } finally { attendu = 'creer'; occupe = false; } } // 14/11/2026 (P7c)
      if (attendu === 'dossiers') { try { return await confirmerDossiers(); } finally { attendu = 'creer'; occupe = false; non.textContent = 'Non'; non.disabled = false; } } // 13/11/2026 (P5 temps 2)
      try {
        montrer('Création en cours… (rien n’est effacé)');
        const r = await mmsRepetition.creer(compte);
        const t = r.dejaLa ? 'Les dossiers de répétition existaient déjà : rien créé.' : `C’est fait, dans le Drive du compte Cap : ${r.cree.map(n => `« ${n} »`).join(', ')}.`;
        montrer(t);
        return t;
      } catch (erreur) {
        const t = `${raison(erreur)} Rien n’a été effacé ; tu peux réessayer : ce qui existe déjà ne sera pas recréé.`;
        montrer(t);
        return t;
      } finally { occupe = false; }
    }

    // ----- 13/11/2026 (accord de Max, P3) : « Inventaire des SMS et MMS » : des NOMBRES seulement (reçus, envoyés, autres ;
    // correspondants par sorte ; codes exclus ; doutes ; « À trier » ; période en dates). Rien copié, rien envoyé, rien gardé.
    const inventaire = el('inventaire-mms');
    async function faireInventaire() {
      if (occupe) return '';
      if (!mmsLecture.disponible(fenetre)) { montrer('L’inventaire se fait seulement dans l’application Cap du téléphone.'); return ''; }
      occupe = true;
      try {
        if (!mmsLecture.autorise(fenetre)) {
          montrer('Android va te demander l’autorisation de lire tes SMS et MMS. Cap les lit seulement : il n’envoie, n’efface et ne copie rien.');
          if (!(await mmsLecture.demander(fenetre))) { montrer('Autorisation refusée : rien n’a été lu.'); return ''; }
        }
        montrer('Inventaire en cours… (des nombres seulement ; rien n’est copié ni envoyé)');
        const { cle, index } = await mmsRangement.preparerIndex(stockage);
        const lignes = await mmsLecture.lireInventaire(cle, index, fenetre);
        const t = inventaireEchanges.texte(inventaireEchanges.compter(lignes));
        montrer(t);
        return t;
      } catch (erreur) {
        montrer(`${raison(erreur)} Rien n’a été copié ni envoyé.`);
        return '';
      } finally { occupe = false; }
    }
    if (inventaire) inventaire.addEventListener('click', () => { void faireInventaire(); });

    // ----- 13/11/2026 (accord de Max, P5 = M3e, TEMPS 1) : « Dossiers par expéditeur : la liste en nombres ». Inventaire (comme P3,
    // + la personne en empreinte éphémère), puis LECTURE SEULE du Drive du compte Cap (ce qui existe déjà), puis des NOMBRES.
    // Rien n'est créé, rien n'est copié : aucune question « Oui, créer » ici (elle viendra au temps 2, sur le Oui de Max).
    const listeDossiers = el('liste-dossiers-mms');
    async function faireListeDossiers() {
      if (occupe) return '';
      if (!mmsLecture.disponible(fenetre)) { montrer('La liste se fait seulement dans l’application Cap du téléphone.'); return ''; }
      occupe = true;
      try {
        if (!mmsLecture.autorise(fenetre)) {
          montrer('Android va te demander l’autorisation de lire tes SMS et MMS. Cap les lit seulement : il n’envoie, n’efface et ne copie rien.');
          if (!(await mmsLecture.demander(fenetre))) { montrer('Autorisation refusée : rien n’a été lu.'); return ''; }
        }
        montrer('Liste en cours… (des nombres seulement ; rien n’est créé ni copié)');
        const { cle, index } = await mmsRangement.preparerIndex(stockage);
        const lignes = await mmsLecture.lireInventaire(cle, index, fenetre, { avecPersonne: true });
        const etat = await mmsDossiers.lireEtat(compte);
        const plan = mmsDossiers.planifier(lignes, etat);
        let t = mmsDossiers.texte(plan);
        if (etat.homonymes) t += `
Un dossier « ${mmsDossiers.NOM_RACINE} » fait à la main existe déjà (${etat.homonymes}) : Cap ne s’en servira pas, il n’y touche pas.`;
        if (etat.nonMarques) t += `
Dans « ${mmsDossiers.NOM_RACINE} », ${etat.nonMarques} dossier(s) non marqué(s) par Cap : jamais touchés.`;
        montrer(t);
        return t;
      } catch (erreur) {
        montrer(`${raison(erreur)} Rien n’a été créé ni copié.`);
        return '';
      } finally { occupe = false; }
    }
    if (listeDossiers) listeDossiers.addEventListener('click', () => { void faireListeDossiers(); });

    // ----- 13/11/2026 (accord de Max, P5 = M3e, TEMPS 2) : « Dossiers par expéditeur : créer ». La liste EN NOMBRES (comme
    // au temps 1, avec la clé STABLE du téléphone), puis la question « Oui, créer ». Le plan montré est figé (copie) : la
    // création n'en fera jamais plus. Pendant la création, « Non » devient « Arrêter » (arrêt avant le dossier suivant).
    // Dossiers VIDES seulement ; aucun message copié ; rien d'effacé ; l'ancien rangement « r_ » n'est pas touché.
    const creerDossiersB = el('creer-dossiers-mms');
    let planMontre = null;
    let arret = false;
    async function preparerDossiers() {
      if (occupe) return '';
      if (!mmsLecture.disponible(fenetre)) { montrer('La création se fait seulement dans l’application Cap du téléphone.'); return ''; }
      occupe = true;
      try {
        if (!mmsLecture.autorise(fenetre)) {
          montrer('Android va te demander l’autorisation de lire tes SMS et MMS. Cap les lit seulement : il n’envoie, n’efface et ne copie rien.');
          if (!(await mmsLecture.demander(fenetre))) { montrer('Autorisation refusée : rien n’a été lu.'); return ''; }
        }
        montrer('Liste en cours… (des nombres seulement ; rien n’est créé ni copié)');
        const { cle, index } = await mmsRangement.preparerIndex(stockage);
        const lignes = await mmsLecture.lireInventaire(cle, index, fenetre, { avecPersonne: true, stable: true, etiquettes: true });
        const etat = await mmsDossiers.lireEtat(compte);
        const plan = mmsDossiers.planifier(lignes, etat);
        mmsDossiers.verifierPlan(plan, plan);
        if (!plan.total) { const t = `${mmsDossiers.texte(plan)}\nRien à créer : tout existe déjà.`; montrer(t); return t; }
        planMontre = JSON.parse(JSON.stringify(plan)); // la liste MONTRÉE, figée
        attendu = 'dossiers';
        const t = `${mmsDossiers.texte(plan)}\nTouche « Oui, créer » pour créer ces dossiers VIDES (${plan.total} au plus), un à la fois. Pendant la création, « Arrêter » les arrête. Aucun message n’est copié.`;
        montrer(t, true);
        return t;
      } catch (erreur) {
        planMontre = null;
        montrer(`${raison(erreur)} Rien n’a été créé.`);
        return '';
      } finally { occupe = false; }
    }
    async function confirmerDossiers() {
      const plan = planMontre;
      planMontre = null;
      if (!plan) return '';
      arret = false;
      barre.hidden = false;
      oui.disabled = true;
      non.textContent = 'Arrêter';
      non.disabled = false;
      zone.textContent = 'Création en cours… (un dossier à la fois ; rien n’est effacé)';
      const r = await mmsCreationDossiers.creer(compte, plan, JSON.parse(JSON.stringify(plan)), {
        arreter: () => arret,
        progres: x => { zone.textContent = `Création en cours : ${x.crees} dossier(s) créé(s), ${plan.total} au plus… (« Arrêter » pour arrêter)`; }
      });
      const t = [r.erreur ? `Arrêt : ${r.erreur}` : (r.arrete ? 'Arrêté à ta demande.' : 'C’est fait, dans le Drive du compte Cap.'),
        `Créés : ${r.crees}. Déjà là : ${r.dejaLa}. À la corbeille (pas recréés) : ${r.corbeille}.`,
        'Aucun message copié, rien d’effacé. Tu peux relancer : ce qui existe ne sera pas recréé.'].join('\n');
      montrer(t);
      return t;
    }
    if (creerDossiersB) creerDossiersB.addEventListener('click', () => { void preparerDossiers(); });

    // ----- 14/11/2026 (accord de Max, P6) : « Copier UN message avec pièce jointe ». Max choisit la PERSONNE (seulement les
    // personnes connues qui ont leur dossier dans « MMS des relations » et au moins un message avec image ou vidéo), puis UN
    // message (date, reçu ou envoyé, sortes de pièces : aucun contenu), puis « Oui, copier » (sorte, taille, sens, dossier
    // d'arrivée). Rien ne part avant. Le message reste sur le téléphone ; rien n'est effacé. Les noms restent sur l'écran du
    // téléphone (ils ne vont nulle part ailleurs).
    const copierB = el('copier-message-mms');
    const choix = el('choix-copie-mms');
    let personnesCopie = [];
    let personneChoisie = null;
    let copieMontree = null;
    const viderChoix = () => { if (choix) choix.replaceChildren(); };
    const boutonChoix = (texteBouton, action) => {
      const b = doc.createElement('button');
      b.type = 'button';
      b.className = 'relations-gros-bouton';
      b.textContent = texteBouton;
      b.addEventListener('click', () => { void action(); });
      choix.appendChild(b);
      return b;
    };
    async function preparerCopie() {
      if (occupe || !choix) return '';
      if (!mmsLecture.disponible(fenetre)) { montrer('La copie se fait seulement dans l’application Cap du téléphone.'); return ''; }
      if (!compte.connecte()) { montrer('Le compte Cap n’est pas connecté : touche « Autoriser la lecture du compte Cap », puis recommence.'); return ''; }
      occupe = true;
      viderChoix();
      copieMontree = null;
      personneChoisie = null;
      attendu = 'creer';
      try {
        if (!mmsLecture.autorise(fenetre)) {
          montrer('Android va te demander l’autorisation de lire tes SMS et MMS. Cap les lit seulement : il n’envoie, n’efface et ne copie rien.');
          if (!(await mmsLecture.demander(fenetre))) { montrer('Autorisation refusée : rien n’a été lu.'); return ''; }
        }
        montrer('Lecture en cours… (rien n’est copié)');
        const { cle, index } = await mmsRangement.preparerIndex(stockage);
        const lignes = await mmsLecture.lireInventaire(cle, index, fenetre, { avecPersonne: true, stable: true, etiquettes: true, pieces: true });
        const etat = await mmsDossiers.lireEtat(compte);
        const existants = new Set(etat.existants);
        personnesCopie = mmsCopie.personnes(lignes).filter(p => existants.has(p.cle));
        if (!personnesCopie.length) { const t = 'Aucune personne connue avec un dossier et un message avec image ou vidéo : rien à copier.'; montrer(t); return t; }
        for (const p of personnesCopie) boutonChoix(`${p.nom} : ${p.messages.length} message${p.messages.length > 1 ? 's' : ''}`, () => choisirPersonne(p.cle));
        const n = personnesCopie.length;
        const t = `Choisis la personne (${n} personne${n > 1 ? 's' : ''} connue${n > 1 ? 's' : ''} avec au moins un message avec image ou vidéo). Rien n’est copié.`;
        montrer(t);
        return t;
      } catch (erreur) {
        montrer(`${raison(erreur)} Rien n’a été copié.`);
        return '';
      } finally { occupe = false; }
    }
    async function choisirPersonne(clePersonne) {
      if (occupe || !choix) return '';
      const p = personnesCopie.find(x => x.cle === clePersonne);
      if (!p) return '';
      personneChoisie = p;
      viderChoix();
      const montres = p.messages.slice(0, 30);
      for (const m of montres) boutonChoix(mmsCopie.texteMessage(m), () => choisirMessage(m.mid));
      const t = `${p.nom} : choisis UN message (${montres.length} montré${montres.length > 1 ? 's' : ''}, du plus récent au plus ancien${p.messages.length > montres.length ? ` ; ${p.messages.length} en tout` : ''}). Rien n’est copié.`;
      montrer(t);
      return t;
    }
    async function choisirMessage(mid) {
      if (occupe || !personneChoisie) return '';
      const m = personneChoisie.messages.find(x => x.mid === mid);
      if (!m) return '';
      occupe = true;
      viderChoix();
      try {
        montrer('Lecture de la pièce… (rien n’est copié)');
        const prop = await mmsCopie.preparer(compte, personneChoisie, m, (a, b) => mmsLecture.lirePiece(a, b, fenetre));
        if (!prop.pieces.length) {
          const t = prop.deja ? 'Ce message est déjà copié : rien n’est recopié.' : 'Aucune pièce de ce message ne peut être copiée (plus de 5 Mo) : rien n’est copié.';
          montrer(t);
          return t;
        }
        copieMontree = prop;
        attendu = 'copie';
        const t = `${mmsCopie.texte(prop)}\nTouche « Oui, copier » pour copier, ou « Non ».`;
        montrer(t, true);
        return t;
      } catch (erreur) {
        copieMontree = null;
        montrer(raison(erreur));
        return '';
      } finally { occupe = false; }
    }
    async function confirmerCopie() {
      const prop = copieMontree;
      copieMontree = null;
      personneChoisie = null;
      if (!prop) return '';
      zone.textContent = 'Copie en cours… (rien n’est effacé)';
      const r = await mmsCopie.copier(compte, prop, { pieces: prop.pieces.length });
      const s = r.copiees > 1 ? 's' : '';
      const t = [r.erreur ? `Arrêt : ${r.erreur}` : (r.copiees ? `C’est fait : ${r.copiees} pièce${s} copiée${s} dans « ${r.nom} » (${r.noms.join(', ')}).` : 'Rien de nouveau à copier.'),
        `Déjà copiées (pas recopiées) : ${r.deja}.${r.sousCree ? ` « ${r.nom} » a été créé.` : ''}`,
        'Le message est toujours sur ton téléphone. Rien n’a été effacé. Tu peux relancer : rien ne sera copié deux fois.'].join('\n');
      montrer(t);
      return t;
    }
    if (copierB) copierB.addEventListener('click', () => { void preparerCopie(); });

    // ----- 14/11/2026 (accord de Max, P7b) : « Textes des messages (Dialogue) ». Max choisit la PERSONNE (connue, avec son
    // dossier dans « MMS des relations ») ; Cap montre, en NOMBRES seulement, ce que ferait « Oui, copier » (ses 10 plus anciens
    // messages pas encore copiés). P7c (accord de Max) : puis « Oui, copier » ou « Non » ; rien ne part avant. Les textes restent en
    // mémoire le temps de la préparation et de la copie, puis sont oubliés ; ils ne sont jamais affichés.
    const dialogueB = el('dialogue-mms');
    const choixD = el('choix-dialogue-mms');
    let personnesDialogue = [];
    let lignesDialogue = null;
    let dialogueMontre = null; // P7c : la proposition montrée (copiée seulement après « Oui, copier »)
    const viderChoixD = () => { if (choixD) choixD.replaceChildren(); };
    async function preparerDialogue() {
      if (occupe || !choixD) return '';
      if (!mmsLecture.disponible(fenetre)) { montrer('La copie se fait seulement dans l’application Cap du téléphone.'); return ''; }
      if (!compte.connecte()) { montrer('Le compte Cap n’est pas connecté : touche « Autoriser la lecture du compte Cap », puis recommence.'); return ''; }
      occupe = true;
      viderChoixD();
      lignesDialogue = null;
      dialogueMontre = null;
      attendu = 'creer';
      try {
        if (!mmsLecture.autorise(fenetre)) {
          montrer('Android va te demander l’autorisation de lire tes SMS et MMS. Cap les lit seulement : il n’envoie, n’efface et ne copie rien.');
          if (!(await mmsLecture.demander(fenetre))) { montrer('Autorisation refusée : rien n’a été lu.'); return ''; }
        }
        montrer('Lecture en cours… (rien n’est copié)');
        const { cle, index } = await mmsRangement.preparerIndex(stockage);
        const lignes = await mmsLecture.lireInventaire(cle, index, fenetre, { avecPersonne: true, stable: true, etiquettes: true, pieces: true, textes: true });
        const etat = await mmsDossiers.lireEtat(compte);
        const existants = new Set(etat.existants);
        personnesDialogue = mmsDialogue.personnes(lignes).filter(p => existants.has(p.cle));
        if (!personnesDialogue.length) { const t = 'Aucune personne connue avec un dossier et un message à copier : rien à copier.'; montrer(t); return t; }
        lignesDialogue = lignes;
        for (const p of personnesDialogue) {
          const b = doc.createElement('button');
          b.type = 'button';
          b.className = 'relations-gros-bouton';
          b.textContent = `${p.nom} : ${p.total} message${p.total > 1 ? 's' : ''}`;
          b.addEventListener('click', () => { void choisirPersonneDialogue(p.cle); });
          choixD.appendChild(b);
        }
        const n = personnesDialogue.length;
        const t = `Choisis la personne (${n} personne${n > 1 ? 's' : ''} connue${n > 1 ? 's' : ''}). Rien n’est copié.`;
        montrer(t);
        return t;
      } catch (erreur) {
        lignesDialogue = null;
        montrer(`${raison(erreur)} Rien n’a été copié.`);
        return '';
      } finally { occupe = false; }
    }
    async function choisirPersonneDialogue(clePersonne) {
      if (occupe || !lignesDialogue) return '';
      const p = personnesDialogue.find(x => x.cle === clePersonne);
      if (!p) return '';
      occupe = true;
      viderChoixD();
      const lignes = lignesDialogue;
      lignesDialogue = null; // oubliées après cette préparation
      try {
        montrer('Préparation… (rien n’est copié)');
        const prop = await mmsDialogue.preparer(compte, p, lignes, { tailleMax: tailleDialogue });
        if (prop.rien) { const t = mmsDialogue.texte(prop); montrer(t); return t; }
        dialogueMontre = prop;
        attendu = 'dialogue';
        const t = `${mmsDialogue.texte(prop)}\nTouche « Oui, copier » pour copier, ou « Non ».`;
        montrer(t, true);
        return t;
      } catch (erreur) {
        dialogueMontre = null;
        montrer(raison(erreur));
        return '';
      } finally { occupe = false; }
    }
    async function confirmerDialogue() { // P7c : après « Oui, copier » seulement
      const prop = dialogueMontre;
      dialogueMontre = null;
      if (!prop) return '';
      const n = prop.nombres.messages;
      const k = prop.fichiers.length;
      zone.textContent = 'Copie en cours… (rien n’est effacé)';
      const r = await mmsDialogue.copier(compte, prop, { messages: n, fichiers: k }); // 14/11/2026 (P7d) : tous les fichiers, un seul Oui
      const pl = (x, un, plusieurs = `${un}s`) => `${x} ${x > 1 ? plusieurs : un}`;
      const bons = r.faits.filter(f => f.relu === 'identique');
      const lignes = [];
      if (r.faits.length === 1 && !r.erreur && k === 1) lignes.push(`C’est fait : « ${r.nom} » créé dans « Dialogue »${r.sousCree ? ' (dossier créé)' : ''}, avec ${pl(n, 'message')}.`);
      else if (r.faits.length === k && !r.erreur && bons.length === k) lignes.push(`C’est fait : ${k} fichiers créés dans « Dialogue »${r.sousCree ? ' (dossier créé)' : ''}, de « ${r.faits[0].nom} » à « ${r.nom} », avec ${pl(n, 'message')}.`);
      else {
        lignes.push(r.erreur ? `Arrêt : ${r.erreur}` : `Arrêt après « ${r.nom} ».`);
        if (r.faits.length) lignes.push(`Créés : ${r.faits.map(f => `« ${f.nom} »`).join(', ')} (${pl(r.messages, 'message')}). Pas copiés : ${pl(r.pasFaits.fichiers, 'fichier')} (${pl(r.pasFaits.messages, 'message')}).`);
      }
      const relu = r.faits.length ? ({ identique: k > 1 ? `Relecture dans le Drive : ${bons.length === 1 ? 'le fichier est identique' : `les ${bons.length} fichiers sont identiques`} à ce qui était préparé.` : 'Relecture dans le Drive : identique à ce qui était préparé.',
        'différent': `Relecture dans le Drive : « ${r.nom} » est DIFFÉRENT de ce qui était préparé : arrêt. Ne relance pas ; préviens Claude Code.`,
        impossible: `Relecture dans le Drive : impossible pour « ${r.nom} » (le fichier est créé) : arrêt. Regarde-le dans le Drive ; préviens Claude Code.` }[r.relu] || '') : '';
      const t = [...lignes, relu, `Les messages sont toujours sur ton téléphone. Rien n’a été effacé ni remplacé.${r.relu === 'différent' ? '' : ' Tu peux relancer : rien ne sera copié deux fois.'}`].filter(Boolean).join('\n');
      montrer(t);
      return t;
    }
    if (dialogueB) dialogueB.addEventListener('click', () => { void preparerDialogue(); });

    lire.addEventListener('click', () => { void lireMms(); });
    repetition.addEventListener('click', () => { void preparerRepetition(); });
    oui.addEventListener('click', () => { void confirmer(); });
    non.addEventListener('click', () => {
      if (occupe && attendu === 'dossiers') { arret = true; non.disabled = true; return; } // 13/11/2026 (P5 temps 2) : « Arrêter »
      if (!occupe) { montrer(attendu === 'envoi' ? 'Rien n’a été envoyé.' : (attendu === 'copie' || attendu === 'dialogue' ? 'Rien n’a été copié.' : 'Rien n’a été créé.')); attendu = 'creer'; planMontre = null; copieMontree = null; viderChoix(); lignesDialogue = null; dialogueMontre = null; viderChoixD(); } // 14/11/2026 (P6) : + la copie
    });
    return { lireMms, preparerRepetition, confirmer, faireInventaire, preparerEssai, faireListeDossiers, preparerDossiers, preparerCopie, choisirPersonne, choisirMessage, preparerDialogue, choisirPersonneDialogue }; // 14/11/2026 (P7b) : + le Dialogue (nombres) // 14/11/2026 (P6) : + la copie // 13/11/2026 (P5) : + la liste ; temps 2 : + la création
  }
  return { brancher };
})();

if (typeof document !== 'undefined' && !(typeof window !== 'undefined' && window.CAP_TESTS)) {
  mmsEcran.instance = mmsEcran.brancher(document, { compte: googleCompteRelations });
}
