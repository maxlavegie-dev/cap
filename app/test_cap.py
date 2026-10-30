import html
import json
import pathlib
import re
import struct
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP = pathlib.Path(__file__).resolve().parent
EDGE = pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
SOURCES = ["donnees_fictives.js", "etapes_par_defaut.js", "stockage.js", "vibration.js", "annulation.js", "taches.js", "listes_choix.js", "indices_rangement.js", "sous_categories.js", "reglages_google.js", "google_connexion.js", "google_sheets.js", "google_agenda.js", "synchronisation.js", "dictee.js", "phrases_clavier.js", "preferences_clavier.js", "voix.js", "comprendre_dates.js", "comprendre_demande.js", "reglages_ia.js", "limite_ia.js", "cle_ia.js", "actions_cap.js", "cerveau.js", "cerveau_prepare.js", "journal_ia.js", "cerveau_claude.js", "demandes.js", "recherche.js", "journal_actions.js", "fiche_rendezvous.js", "choix_dates.js", "fermeture_fenetres.js", "fenetres_listes.js", "synchro_listes.js", "sauvegarde_drive.js", "tuiles.js", "mode_trier.js", "app.js"]

TESTS_JS = r"""
(async () => {
  const CLE = 'cap_taches_v1';
  const PREFIXE_SAUVEGARDE = CLE + '_illisible_';
  const CLE_USAGE = 'cap_usage_phrases_v1';
  const CLE_HISTORIQUE = 'cap_historique_demandes_v1';
  const CLE_SILENCE = 'cap_reponse_silencieuse_v1';
  const resultats = [];
  const MESSAGE_ILLISIBLE = 'La liste enregistrée était illisible. Une copie complète a été conservée sur ce téléphone ; les tâches fictives sont affichées.';

  function instanceStockage() {
    return new Function(SOURCE_STOCKAGE + '\nreturn stockage;')();
  }

  function clesSauvegarde() {
    return Object.keys(localStorage).filter(cle => cle.startsWith(PREFIXE_SAUVEGARDE));
  }

  function reinitialiser() {
    for (const cle of Object.keys(localStorage)) {
      if (cle.startsWith(CLE)) localStorage.removeItem(cle);
    }
    for (const cle of [CLE_USAGE, CLE_HISTORIQUE, CLE_SILENCE, 'cap_google_file_v1']) localStorage.removeItem(cle);
    const chargement = stockage.charger();
    TACHES.splice(0, TACHES.length, ...chargement.taches);
  }

  function attendre(condition, message) {
    if (!condition) throw new Error(message);
  }

  function attendreEgal(reel, attendu, message) {
    const r = JSON.stringify(reel);
    const a = JSON.stringify(attendu);
    if (r !== a) throw new Error(`${message} : attendu ${a}, reçu ${r}`);
  }

  function attendreErreur(fonction, fragment) {
    let message = null;
    try {
      fonction();
    } catch (erreur) {
      message = String(erreur && erreur.message ? erreur.message : erreur);
    }
    attendre(message !== null && message.includes(fragment),
      `erreur attendue contenant « ${fragment} », reçu : ${message}`);
  }

  function test(nom, fonction) {
    try {
      reinitialiser();
      fonction();
      resultats.push({ nom, ok: true, erreur: '' });
    } catch (erreur) {
      resultats.push({ nom, ok: false, erreur: String(erreur && erreur.message ? erreur.message : erreur) });
    }
  }

  const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

  test('modèles complets : dates et fait cohérents', () => {
    attendre(TACHES.length > 0, 'liste vide');
    const identifiants = new Set(TACHES.map(t => t.id));
    for (const t of TACHES) {
      attendre(DATE_RE.test(t.date_entree), `date_entree invalide pour ${t.id}`);
      for (const champ of ['echeance', 'date_realisation', 'avant_le', 'abandonnee_le']) {
        attendre(t[champ] === '' || DATE_RE.test(t[champ]), `${champ} invalide pour ${t.id}`);
      }
      attendre(t.fait === (t.date_realisation !== ''), `fait incohérent avec date_realisation pour ${t.id}`);
      attendre(['haute', 'normale', 'basse'].includes(t.priorite), `priorité invalide pour ${t.id}`);
      attendre(t.parente === '' || identifiants.has(t.parente), `parente inconnue pour ${t.id}`);
    }
  });

  test('hiérarchie fictive : albums 3 + 2 titres', () => {
    const titres = TACHES.filter(t => t.categorie === 'Musique' && !t.parente);
    attendre(titres.filter(t => t.sous_categorie === 'Album A').length === 3, 'Album A doit avoir 3 titres');
    attendre(titres.filter(t => t.sous_categorie === 'Album B').length === 2, 'Album B doit avoir 2 titres');
    const etapesDe = id => TACHES.filter(t => t.parente === id);
    const lucioles = titres.find(t => t.intitule === 'Les lucioles du large');
    attendre(lucioles, 'titre Les lucioles du large introuvable');
    attendreEgal(etapesDe(lucioles.id).length, 4, 'étapes de Les lucioles du large');
    const autres = titres.filter(t => t.id !== lucioles.id);
    for (const titre of autres) {
      attendreEgal(etapesDe(titre.id).length, 3, `étapes de ${titre.intitule}`);
    }
    const roman = TACHES.find(t => t.intitule === 'Les jardins suspendus de minuit');
    attendreEgal(etapesDe(roman.id).length, 3, 'étapes du roman');
  });

  test('créer conserve l’intitulé exact, caractères HTML compris', () => {
    const intitule = '<b>Ça & "é" &amp; <i>x</i></b> ’';
    const tache = creerTache({ intitule, categorie: 'Test' });
    attendreEgal(TACHES.find(t => t.id === tache.id).intitule, intitule, 'intitulé en mémoire');
    const sauvegarde = JSON.parse(localStorage.getItem(CLE));
    attendreEgal(sauvegarde.find(t => t.id === tache.id).intitule, intitule, 'intitulé sauvegardé');
  });

  test('identifiants au format unique et sans doublon', () => {
    const nouvelles = [];
    for (let i = 0; i < 20; i++) nouvelles.push(creerTache({ intitule: `Tâche ${i}`, categorie: 'Test' }));
    const ids = TACHES.map(t => t.id);
    attendre(new Set(ids).size === ids.length, 'identifiant en double');
    for (const t of nouvelles) {
      attendre(/^T-[0-9a-z]{12}$/.test(t.id), `format d’identifiant incorrect : ${t.id}`);
    }
  });

  test('étapes par défaut : modèles, catégories et erreurs', () => {
    const parent = creerAvecEtapesParDefaut({ intitule: 'Titre test', categorie: 'Musique', sous_categorie: 'Album T' }, "Titre d'album");
    const etapes = TACHES.filter(t => t.parente === parent.id);
    attendreEgal(etapes.map(t => t.intitule), ETAPES_PAR_DEFAUT["Titre d'album"], 'étapes Titre d’album');
    for (const etape of etapes) {
      attendre(etape.categorie === 'Musique' && etape.sous_categorie === 'Album T', 'catégorie d’étape incorrecte');
    }
    const roman = creerAvecEtapesParDefaut({ intitule: 'Mon roman', categorie: 'Écriture', sous_categorie: 'Roman' }, 'Roman');
    attendreEgal(TACHES.filter(t => t.parente === roman.id).map(t => t.intitule), ETAPES_PAR_DEFAUT.Roman, 'étapes Roman');
    const avant = TACHES.length;
    attendreErreur(() => creerAvecEtapesParDefaut({ intitule: 'X' }, 'Inconnu'), 'introuvable');
    attendreErreur(() => creerAvecEtapesParDefaut({ intitule: 'X', parente: parent.id }, 'Roman'), 'réservées');
    attendreEgal(TACHES.length, avant, 'nombre de tâches après erreurs');
  });

  test('cocher et décocher : date locale', () => {
    const tache = creerTache({ intitule: 'Cocher', categorie: 'Test' });
    cocher(tache.id, true);
    const coche = TACHES.find(t => t.id === tache.id);
    attendre(coche.fait === true, 'tâche non cochée');
    attendreEgal(coche.date_realisation, dateDuJour(), 'date de réalisation');
    cocher(tache.id, false);
    const decochee = TACHES.find(t => t.id === tache.id);
    attendre(decochee.fait === false && decochee.date_realisation === '', 'tâche non décochée');
    attendreErreur(() => cocher(tache.id, 'oui'), 'cochée ou décochée');
  });

  test('abandon et remise sans perte et sans cascade', () => {
    const parent = creerTache({ intitule: 'Parent', categorie: 'Test' });
    const e1 = ajouterEtape(parent.id, 'Étape 1');
    const e2 = ajouterEtape(parent.id, 'Étape 2');
    const nombre = TACHES.length;
    abandonner(parent.id);
    attendreEgal(TACHES.find(t => t.id === parent.id).abandonnee_le, dateDuJour(), 'date d’abandon');
    attendre(TACHES.find(t => t.id === e1.id).abandonnee_le === '', 'cascade sur étape 1');
    attendre(TACHES.find(t => t.id === e2.id).abandonnee_le === '', 'cascade sur étape 2');
    attendreEgal(TACHES.length, nombre, 'nombre de tâches après abandon');
    attendreErreur(() => ajouterEtape(parent.id, 'Refusée'), 'Remets');
    remettre(parent.id);
    attendre(TACHES.find(t => t.id === parent.id).abandonnee_le === '', 'remise incomplète');
    attendreEgal(TACHES.length, nombre, 'nombre de tâches après remise');
    attendreEgal(TACHES.find(t => t.id === e1.id).intitule, 'Étape 1', 'intitulé conservé');
  });

  test('progression exclut les tâches abandonnées', () => {
    const parent = creerTache({ intitule: 'Projet', categorie: 'Test', sous_categorie: 'Progr' });
    const a = ajouterEtape(parent.id, 'A');
    const b = ajouterEtape(parent.id, 'B');
    creerTache({ intitule: 'Solo', categorie: 'Test', sous_categorie: 'Progr' });
    cocher(a.id, true);
    attendreEgal(avancementTache(parent.id), { faites: 1, total: 2 }, 'avancement tâche');
    attendreEgal(avancementSousCategorie('Test', 'Progr'), 50, 'avancement sous-catégorie');
    abandonner(b.id);
    attendreEgal(avancementTache(parent.id), { faites: 1, total: 1 }, 'avancement après abandon');
    attendreEgal(avancementSousCategorie('Test', 'Progr'), 100, 'sous-catégorie après abandon');
    remettre(b.id);
    attendreEgal(avancementSousCategorie('Test', 'Progr'), 50, 'sous-catégorie après remise');
  });

  test('joursRestants compte les jours civils en UTC', () => {
    attendreEgal(joursRestants(dateDuJour()), 0, 'aujourd’hui');
    const demain = new Date(`${dateDuJour()}T00:00:00Z`);
    demain.setUTCDate(demain.getUTCDate() + 1);
    attendreEgal(joursRestants(demain.toISOString().slice(0, 10)), 1, 'demain');
    attendreEgal(joursRestants('2026-03-30') - joursRestants('2026-03-29'), 1, 'changement d’heure de mars');
    attendreEgal(joursRestants('2026-10-26') - joursRestants('2026-10-25'), 1, 'changement d’heure d’octobre');
    attendreErreur(() => joursRestants('2026-02-30'), 'valide');
    attendreErreur(() => joursRestants('2026-13-01'), 'valide');
    attendreErreur(() => joursRestants('2026-1-01'), 'valide');
  });

  test('erreur d’enregistrement : retour arrière complet', () => {
    const parent = creerTache({ intitule: 'Avant', categorie: 'Test' });
    const avant = JSON.stringify(TACHES);
    const original = stockage.enregistrer;
    stockage.enregistrer = () => { throw new Error('Simulation'); };
    try {
      attendreErreur(() => creerTache({ intitule: 'Nouvelle', categorie: 'Test' }), 'Simulation');
      attendreErreur(() => cocher(parent.id, true), 'Simulation');
      attendreErreur(() => abandonner(parent.id), 'Simulation');
    } finally {
      stockage.enregistrer = original;
    }
    attendre(JSON.stringify(TACHES) === avant, 'liste modifiée après retour arrière');
    attendre(!TACHES.some(t => t.intitule === 'Nouvelle'), 'nouvelle tâche restée en mémoire');
    const restee = TACHES.find(t => t.id === parent.id);
    attendre(restee.fait === false && restee.abandonnee_le === '', 'modification restée en mémoire');
  });

  test('sauvegarde localStorage cohérente avec la mémoire', () => {
    const tache = creerTache({ intitule: 'Sauvegarde', categorie: 'Test' });
    cocher(tache.id, true);
    attendreEgal(JSON.parse(localStorage.getItem(CLE)), TACHES, 'contenu sauvegardé');
  });

  test('stockage : liste illisible copiée puis fictives affichées', () => {
    const brut = 'pas du json {';
    localStorage.setItem(CLE, brut);
    const chargement = instanceStockage().charger();
    const sauvegardes = clesSauvegarde();
    attendreEgal(sauvegardes.length, 1, 'nombre de copies de sécurité');
    attendre(localStorage.getItem(sauvegardes[0]) === brut, 'copie de sécurité différente de l’original');
    attendreEgal(chargement.message, MESSAGE_ILLISIBLE, 'message');
    attendreEgal(chargement.taches.length, TACHES_FICTIVES.length, 'nombre de tâches fictives');
    attendre(localStorage.getItem(CLE) === JSON.stringify(chargement.taches), 'fictives non sauvegardées');
  });

  test('stockage : liste vide [] ne relance pas les fictives', () => {
    localStorage.setItem(CLE, '[]');
    const chargement = instanceStockage().charger();
    attendreEgal(chargement.taches, [], 'liste chargée');
    attendreEgal(chargement.message, '', 'message');
    attendreEgal(clesSauvegarde().length, 0, 'copies de sécurité');
  });

  test('stockage : copie de sécurité refusée, original intact et verrouillé', () => {
    const brut = 'pas du json {';
    localStorage.setItem(CLE, brut);
    const original = Storage.prototype.setItem;
    Storage.prototype.setItem = function () { throw new Error('refus'); };
    let chargement;
    let instance;
    try {
      instance = instanceStockage();
      chargement = instance.charger();
    } finally {
      Storage.prototype.setItem = original;
    }
    attendre(chargement.message.startsWith('La liste enregistrée est illisible et sa copie de sécurité a échoué'),
      `message inattendu : ${chargement.message}`);
    attendre(localStorage.getItem(CLE) === brut, 'original modifié');
    attendreEgal(clesSauvegarde().length, 0, 'copies de sécurité');
    attendreErreur(() => instance.enregistrer(chargement.taches), 'Sauvegarde indisponible');
    attendre(localStorage.getItem(CLE) === brut, 'original modifié après verrouillage');
  });

  test('stockage : accès refusé en lecture, modifications bloquées', () => {
    const original = Storage.prototype.getItem;
    Storage.prototype.getItem = function () { throw new Error('refus'); };
    let chargement;
    let instance;
    try {
      instance = instanceStockage();
      chargement = instance.charger();
    } finally {
      Storage.prototype.getItem = original;
    }
    attendre(chargement.message.includes('inaccessible'), `message inattendu : ${chargement.message}`);
    attendreErreur(() => instance.enregistrer(chargement.taches), 'Sauvegarde indisponible');
  });

  test('stockage : conflit avec une autre fenêtre bloque l’écriture', () => {
    localStorage.setItem(CLE, JSON.stringify(TACHES_FICTIVES));
    const instance = instanceStockage();
    const chargement = instance.charger();
    localStorage.setItem(CLE, '[]');
    attendreErreur(() => instance.enregistrer(chargement.taches), 'autre fenêtre');
    attendre(localStorage.getItem(CLE) === '[]', 'contenu écrasé malgré le conflit');
  });

  function fauxConstructeur() {
    const instances = [];
    const comportement = { constructeur: false, start: false, stop: false };
    class FauxReconnaissance {
      constructor() {
        if (comportement.constructeur) throw new Error('constructeur');
        this.lang = '';
        this.interimResults = null;
        this.continuous = null;
        this.maxAlternatives = null;
        this.demarrages = 0;
        this.arrets = 0;
        instances.push(this);
      }
      start() {
        this.demarrages++;
        if (comportement.start) throw new Error('start');
      }
      stop() {
        this.arrets++;
        if (comportement.stop) throw new Error('stop');
      }
    }
    return { classe: FauxReconnaissance, instances, comportement };
  }

  function avecConstructeurs(sr, wk, fonction) {
    const noms = ['SpeechRecognition', 'webkitSpeechRecognition'];
    const avant = noms.map(nom => [nom, Object.prototype.hasOwnProperty.call(window, nom), window[nom]]);
    window.SpeechRecognition = sr;
    window.webkitSpeechRecognition = wk;
    try {
      return fonction();
    } finally {
      for (const [nom, existait, valeur] of avant) {
        if (existait) window[nom] = valeur;
        else delete window[nom];
      }
    }
  }

  function nouvelleDictee() {
    return new Function(SOURCE_DICTEE + '\nreturn dictee;')();
  }

  function rappels() {
    const journal = [];
    return {
      journal,
      surProvisoire: texte => journal.push(['provisoire', texte]),
      surFinal: texte => journal.push(['final', texte]),
      surErreur: code => journal.push(['erreur', code]),
      surFin: () => journal.push(['fin'])
    };
  }

  function segment(texte, final) {
    const liste = [{ transcript: texte }];
    liste.isFinal = final;
    return liste;
  }

  test('dictée : provisoire puis final, sans répétition', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      const r = rappels();
      d.demarrer(r);
      const instance = fake.instances[0];
      instance.onresult({ resultIndex: 0, results: [segment('  Bonjour <b>Ça</b> ', false)] });
      instance.onresult({ resultIndex: 0, results: [segment('Bonjour à tous', true)] });
      instance.onresult({ resultIndex: 1, results: [segment('Bonjour à tous', true), segment('merci', false)] });
      attendreEgal(r.journal, [['provisoire', '  Bonjour <b>Ça</b> '], ['final', 'Bonjour à tous'], ['provisoire', 'merci']], 'transmissions');
    });
  });

  test('dictée : réglages fr-FR, continu faux, une alternative', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      d.demarrer(rappels());
      attendreEgal(fake.instances.length, 1, 'nombre d’instances');
      const instance = fake.instances[0];
      attendreEgal([instance.lang, instance.interimResults, instance.continuous, instance.maxAlternatives, instance.demarrages],
        ['fr-FR', true, false, 1, 1], 'réglages');
      attendre(d.enCours(), 'écoute non démarrée');
    });
  });

  test('dictée : erreur API transmise, nouveau départ après onend', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      const r = rappels();
      d.demarrer(r);
      fake.instances[0].onerror({ error: 'network' });
      attendreEgal(r.journal, [['erreur', 'network']], 'erreur transmise');
      attendre(d.enCours(), 'état libéré avant onend');
      d.demarrer(r);
      fake.instances[0].onend();
      attendreEgal(r.journal, [['erreur', 'network'], ['erreur', 'occupee'], ['fin']], 'fin attendue');
      attendre(!d.enCours(), 'état non libéré après onend');
      d.demarrer(r);
      attendreEgal(fake.instances.length, 2, 'nouveau départ');
    });
  });

  test('dictée : pas de double départ', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      const r = rappels();
      d.demarrer(r);
      d.demarrer(r);
      attendreEgal(r.journal, [['erreur', 'occupee']], 'double départ');
      attendreEgal(fake.instances.length, 1, 'nombre d’instances');
      attendreEgal(fake.instances[0].demarrages, 1, 'nombre de démarrages');
    });
  });

  test('dictée : arrêt attend onend, pas de départ pendant l’arrêt', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      const r = rappels();
      d.demarrer(r);
      d.arreter();
      attendreEgal(fake.instances[0].arrets, 1, 'arrêts');
      attendre(d.enCours(), 'état libéré avant onend');
      d.demarrer(r);
      fake.instances[0].onend();
      attendre(!d.enCours(), 'état non libéré après onend');
      attendreEgal(r.journal, [['erreur', 'occupee'], ['fin']], 'arrêt');
    });
  });

  test('dictée : constructeurs absents, indisponible', () => {
    avecConstructeurs(undefined, undefined, () => {
      const d = nouvelleDictee();
      attendreEgal(d.disponible(), false, 'disponible');
      const r = rappels();
      d.demarrer(r);
      attendreEgal(r.journal, [['erreur', 'indisponible'], ['fin']], 'démarrage refusé');
      attendre(!d.enCours(), 'état coincé');
    });
  });

  test('dictée : webkitSpeechRecognition seul, disponible', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(undefined, fake.classe, () => {
      attendreEgal(nouvelleDictee().disponible(), true, 'disponible');
    });
  });

  test('dictée : échecs constructeur, départ et arrêt sans état coincé', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      const r1 = rappels();
      fake.comportement.constructeur = true;
      d.demarrer(r1);
      attendreEgal(r1.journal, [['erreur', 'constructeur'], ['fin']], 'échec constructeur');
      attendre(!d.enCours(), 'état coincé après constructeur');
      fake.comportement.constructeur = false;
      const r2 = rappels();
      fake.comportement.start = true;
      d.demarrer(r2);
      attendreEgal(r2.journal, [['erreur', 'demarrage'], ['fin']], 'échec démarrage');
      attendre(!d.enCours(), 'état coincé après démarrage');
      fake.comportement.start = false;
      const r3 = rappels();
      d.demarrer(r3);
      attendre(d.enCours(), 'nouveau départ impossible');
      fake.comportement.stop = true;
      d.arreter();
      attendreEgal(r3.journal, [['erreur', 'arret']], 'échec arrêt');
      attendre(d.enCours(), 'écoute libérée alors que le micro pourrait écouter');
      d.demarrer(rappels());
      attendreEgal(fake.instances.length, 2, 'aucun départ supplémentaire après arrêt échoué');
      fake.instances[1].onend();
      attendre(!d.enCours(), 'état coincé après fin');
    });
  });

  test('dictée : anciens callbacks ignorés après fin', () => {
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      const d = nouvelleDictee();
      const r = rappels();
      d.demarrer(r);
      const ancienne = fake.instances[0];
      ancienne.onend();
      d.demarrer(r);
      const longueur = r.journal.length;
      ancienne.onresult({ resultIndex: 0, results: [segment('vieux', true)] });
      ancienne.onerror({ error: 'network' });
      ancienne.onend();
      attendreEgal(r.journal.length, longueur, 'callback ancien transmis');
      attendre(d.enCours(), 'nouvelle écoute arrêtée par un ancien callback');
    });
  });

  test('tâche dictée : À trier, origine dictée, intitulé exact sauvegardé', () => {
    const intitule = 'Appeler le garage « Dupont » : 2 pneus & <b>urgent</b> ’';
    const tache = creerTache({ intitule, categorie: 'À trier', origine: 'dictée' });
    const enMemoire = TACHES.find(t => t.id === tache.id);
    attendreEgal([enMemoire.intitule, enMemoire.categorie, enMemoire.origine], [intitule, 'À trier', 'dictée'], 'mémoire');
    const sauvee = JSON.parse(localStorage.getItem(CLE)).find(t => t.id === tache.id);
    attendreEgal([sauvee.intitule, sauvee.categorie, sauvee.origine], [intitule, 'À trier', 'dictée'], 'sauvegarde');
  });

  test('dictée : constructeur lu au démarrage, pas à la création', () => {
    const d = nouvelleDictee();
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      attendreEgal(d.disponible(), true, 'disponible après injection');
      d.demarrer(rappels());
      attendreEgal(fake.instances.length, 1, 'constructeur non lu au démarrage');
      d.arreter();
      fake.instances[0].onend();
    });
  });

  function micro() {
    return document.getElementById('microphone');
  }

  function cliquerMicro() {
    micro().click();
  }

  function texteStatut() {
    return Array.from(document.getElementById('statut').childNodes)
      .filter(noeud => noeud.nodeType === Node.TEXT_NODE)
      .map(noeud => noeud.textContent)
      .join('');
  }

  function sessionMicro(fonction) {
    if (document.getElementById('ecran-complet').hidden) document.getElementById('basculer-vue').click();
    const fake = fauxConstructeur();
    avecConstructeurs(fake.classe, undefined, () => {
      try {
        fonction(fake);
      } finally {
        for (const instance of fake.instances) instance.onend();
      }
    });
  }

  test('micro : état actif, provisoire puis final', () => {
    sessionMicro(fake => {
      cliquerMicro();
      attendreEgal(micro().getAttribute('aria-pressed'), 'true', 'état actif');
      attendreEgal(micro().getAttribute('aria-label'), 'Arrêter la dictée', 'libellé actif');
      const instance = fake.instances[0];
      instance.onresult({ resultIndex: 0, results: [segment('Bonjour', false)] });
      attendreEgal(texteStatut(), 'Bonjour', 'provisoire');
      instance.onresult({ resultIndex: 0, results: [segment('  <b>Ça</b> & "x"  ', true)] });
      attendreEgal(texteStatut(), 'Ajoutée dans À trier : « <b>Ça</b> & "x" »', 'final');
      attendre(Array.from(document.querySelectorAll('#liste-taches .intitule')).some(s => s.textContent === '<b>Ça</b> & "x"'),
        'intitulé non affiché tel quel');
      attendre(document.querySelector('#liste-taches b') === null, 'HTML interprété');
      instance.onend();
      attendreEgal(micro().getAttribute('aria-pressed'), 'false', 'état repos');
      attendreEgal(micro().getAttribute('aria-label'), 'Dicter une tâche', 'libellé repos');
      attendreEgal(texteStatut(), 'Ajoutée dans À trier : « <b>Ça</b> & "x" »', 'message conservé après fin');
    });
  });

  test('micro : À trier en premier, sans sous-titre', () => {
    sessionMicro(fake => {
      cliquerMicro();
      fake.instances[0].onresult({ resultIndex: 0, results: [segment('Note', true)] });
      const premiere = document.querySelector('#liste-taches section.categorie');
      attendreEgal(premiere.querySelector('h2').textContent, 'À trier', 'première catégorie');
      const sousSection = Array.from(document.querySelectorAll('#liste-taches section.sous-categorie'))
        .find(s => Array.from(s.querySelectorAll('.intitule')).some(i => i.textContent === 'Note'));
      attendre(sousSection && !sousSection.querySelector('h3'), 'sous-titre présent pour À trier');
    });
  });

  test('micro : Annuler abandonne sans supprimer', () => {
    sessionMicro(fake => {
      cliquerMicro();
      fake.instances[0].onresult({ resultIndex: 0, results: [segment('Pain', true)] });
      fake.instances[0].onend();
      const avant = TACHES.length;
      const bouton = document.querySelector('.annuler-dictee');
      attendre(bouton, 'bouton Annuler absent');
      attendreEgal(getComputedStyle(bouton).pointerEvents, 'auto', 'bouton cliquable');
      bouton.click();
      const tache = TACHES.find(t => t.intitule === 'Pain');
      attendreEgal(tache.abandonnee_le, dateDuJour(), 'date d’abandon');
      attendreEgal(TACHES.length, avant, 'nombre de tâches');
      attendreEgal(texteStatut(), 'Tâche abandonnée : tu la retrouves dans les tâches abandonnées.', 'annonce');
    });
  });

  test('micro : sauvegarde refusée, texte conservé après fin', () => {
    const original = stockage.enregistrer;
    stockage.enregistrer = () => { throw new Error('Simulation'); };
    try {
      sessionMicro(fake => {
        cliquerMicro();
        fake.instances[0].onresult({ resultIndex: 0, results: [segment('Acheter du lait', true)] });
        fake.instances[0].onend();
        attendreEgal(texteStatut(), 'Simulation Texte dicté à recopier : « Acheter du lait »', 'message');
        attendre(!TACHES.some(t => t.intitule === 'Acheter du lait'), 'tâche créée malgré le refus');
      });
    } finally {
      stockage.enregistrer = original;
    }
  });

  test('micro : codes d’erreur, fin attendue et retour normal', () => {
    sessionMicro(fake => {
      cliquerMicro();
      fake.instances[0].onerror({ error: 'aborted' });
      attendreEgal(texteStatut(), '', 'arrêt volontaire silencieux');
      fake.instances[0].onend();
      cliquerMicro();
      attendreEgal(fake.instances.length, 2, 'retour normal');
      fake.instances[1].onerror({ error: 'network' });
      attendreEgal(texteStatut(), "La dictée a besoin d'internet pour l'instant.", 'message réseau');
      fake.instances[1].onend();
      attendreEgal(micro().getAttribute('aria-pressed'), 'false', 'état repos après erreur');
      cliquerMicro();
      attendreEgal(fake.instances.length, 3, 'nouveau départ après erreur');
      attendreEgal(micro().getAttribute('aria-pressed'), 'true', 'état actif après erreur');
    });
  });

  test('micro : tous les messages d’erreur et final vide', () => {
    sessionMicro(fake => {
      const messages = {
        'not-allowed': 'Le micro est bloqué. Autorise-le pour cette page dans le navigateur.',
        'service-not-allowed': 'Le micro est bloqué. Autorise-le pour cette page dans le navigateur.',
        'no-speech': "Je n'ai rien entendu, réessaie.",
        'audio-capture': 'Aucun micro trouvé.',
        inconnu: "La dictée n'a pas marché, réessaie."
      };
      for (const [code, message] of Object.entries(messages)) {
        cliquerMicro();
        const instance = fake.instances.at(-1);
        instance.onerror({ error: code });
        instance.onend();
        attendreEgal(texteStatut(), message, code);
        attendreEgal(micro().getAttribute('aria-pressed'), 'false', 'repos');
      }
      const avant = TACHES.length;
      cliquerMicro();
      const instance = fake.instances.at(-1);
      instance.onresult({ resultIndex: 0, results: [segment('   ', true)] });
      instance.onend();
      attendreEgal(TACHES.length, avant, 'aucune tâche vide créée');
      attendreEgal(texteStatut(), "Je n'ai rien entendu, réessaie.", 'final vide');
    });
  });

  test('micro : deuxième clic arrête, fin attendue', () => {
    sessionMicro(fake => {
      cliquerMicro();
      cliquerMicro();
      attendreEgal(fake.instances.length, 1, 'nouvelle écoute au lieu d’arrêt');
      attendreEgal(fake.instances[0].arrets, 1, 'arrêt demandé');
      attendreEgal(micro().getAttribute('aria-pressed'), 'true', 'état avant fin');
      fake.instances[0].onend();
      attendreEgal(micro().getAttribute('aria-pressed'), 'false', 'état après fin');
    });
  });

  test('micro : indisponible, message sans état actif', () => {
    avecConstructeurs(undefined, undefined, () => {
      cliquerMicro();
      attendreEgal(texteStatut(), "La dictée n'est pas disponible dans ce navigateur. Utilise le bouton +.", 'message');
      attendreEgal(micro().getAttribute('aria-pressed'), 'false', 'état');
    });
  });

  test('micro : bouton Annuler expire après 8 secondes', () => {
    const original = window.setTimeout;
    const delais = [];
    window.setTimeout = (fonction, delai, ...args) => {
      if (delai === 8000) {
        delais.push(fonction);
        return 0;
      }
      return original.call(window, fonction, delai, ...args);
    };
    try {
      sessionMicro(fake => {
        cliquerMicro();
        fake.instances[0].onresult({ resultIndex: 0, results: [segment('Lait', true)] });
        fake.instances[0].onend();
        attendreEgal(delais.length, 1, 'délai d’expiration');
        attendre(document.querySelector('.annuler-dictee'), 'Annuler absent avant délai');
        delais[0]();
        attendre(document.querySelector('.annuler-dictee') === null, 'Annuler toujours présent');
      });
    } finally {
      window.setTimeout = original;
    }
  });

  test('catalogue : 11 phrases, 4 catégories, actions exactes', () => {
    attendreEgal(PHRASES_CLAVIER.map(p => p.id),
      ['retrouver', 'dictionnaire', 'dernier-mail', 'agenda', 'ajouter-tache', 'rappel', 'resumer-mails', 'brouillon', 'reformuler', 'continuer', 'annuler'], 'identifiants');
    attendreEgal(PHRASES_CLAVIER.map(p => p.debut),
      ['Retrouve-moi...', 'Cherche dans mon dictionnaire...', 'Retrouve le dernier mail de...', "Qu'est-ce que j'ai le...", 'Ajoute à ma to-do...', 'Rappelle-moi de...', 'Résume mes mails de...', 'Prépare un brouillon de réponse à...', 'Reformule en plus...', 'Continue.', 'Annule.'], 'débuts');
    attendreEgal([...new Set(PHRASES_CLAVIER.map(p => p.categorie))], ['Retrouver', 'Agenda et to-do', 'Mails', 'Général'], 'catégories');
    attendreEgal(PHRASES_CLAVIER.filter(p => p.action !== '').map(p => [p.id, p.action]), [['ajouter-tache', 'ajouter_tache']], 'actions');
    attendreEgal(PHRASES_CLAVIER.filter(p => !p.a_completer).map(p => p.id), ['continuer', 'annuler'], 'phrases sans complément');
  });

  test('composerTexte : … ou ... retirés, complément garde ses caractères', () => {
    attendreEgal(composerTexte(PHRASES_CLAVIER.find(p => p.id === 'brouillon'), '  Marc Dupont  '),
      'Prépare un brouillon de réponse à Marc Dupont', 'points ASCII');
    attendreEgal(composerTexte({ debut: 'Retrouve-moi…' }, '  le pain  '), 'Retrouve-moi le pain', 'points Unicode');
    attendreEgal(composerTexte({ debut: 'Cherche  …' }, ''), 'Cherche', 'complément vide');
    attendreEgal(composerTexte({ debut: 'Reformule en plus...' }, ' Ça & "é" <b>x</b> ’ '),
      'Reformule en plus Ça & "é" <b>x</b> ’', 'complément exact');
  });

  test('ajouter-tache : complément dans À trier, origine et fictif exacts', () => {
    const clavier = traiterDemande({ texte: 'Ajoute à ma to-do... acheter du pain', source: 'clavier', id_phrase: 'ajouter-tache', complement: '  acheter du pain  ' });
    attendreEgal([clavier.tache.intitule, clavier.tache.categorie, clavier.tache.sous_categorie, clavier.tache.origine, clavier.tache.fictif],
      ['acheter du pain', 'À trier', '', 'ajout à la main', false], 'tâche clavier');
    attendreEgal(clavier.message, 'Ajoutée dans À trier : « acheter du pain »', 'message');
    const micro = traiterDemande({ texte: 'Ajoute à ma to-do... lait', source: 'micro', id_phrase: 'ajouter-tache', complement: 'lait' });
    attendreEgal([micro.tache.intitule, micro.tache.origine, micro.tache.fictif], ['lait', 'dictée', false], 'tâche micro');
  });

  test('saisie libre : intitulé mot pour mot, HTML non interprété, historique exact', () => {
    const texte = '  Note <i>vite</i> & "ça" ’  ';
    const resultat = traiterDemande({ texte, source: 'saisie' });
    attendreEgal([resultat.type, resultat.tache.intitule, resultat.tache.origine, resultat.tache.fictif],
      ['tache', 'Note <i>vite</i> & "ça" ’', 'ajout à la main', false], 'tâche');
    attendreEgal(resultat.message, 'Ajoutée dans À trier : « Note <i>vite</i> & "ça" ’ »', 'message');
    const historique = preferencesClavier.historique();
    attendreEgal(historique.length, 1, 'nombre d’entrées');
    attendreEgal([historique[0].texte, historique[0].id_phrase, historique[0].complement, historique[0].source],
      [texte, '', '', 'saisie'], 'champs historique');
    attendre(!Number.isNaN(Date.parse(historique[0].date)), 'date d’historique invalide');
  });

  test('Continuer et Annuler : pas de tâche, historique et usage enregistrés', () => {
    const avant = TACHES.length;
    const continuer = traiterDemande({ texte: 'Continue.', source: 'clavier', id_phrase: 'continuer' });
    attendreEgal([continuer.type, continuer.message],
      ['attente_cerveau', '« Continue. » marchera quand le cerveau de Cap sera branché.'], 'Continuer');
    const annuler = traiterDemande({ texte: 'Annule.', source: 'micro', id_phrase: 'annuler' });
    attendreEgal([annuler.type, annuler.message], ['annuler', ''], 'Annuler');
    attendreEgal(TACHES.length, avant, 'tâche créée');
    attendreEgal(preferencesClavier.plusUtilisees(5).map(p => p.id), ['continuer', 'annuler'], 'usages');
    attendreEgal(preferencesClavier.historique().map(e => [e.id_phrase, e.source, e.texte]),
      [['annuler', 'micro', 'Annule.'], ['continuer', 'clavier', 'Continue.']], 'historique');
  });

  test('demande vide : message exact, rien dans historique ni usage', () => {
    const avant = TACHES.length;
    attendreEgal(traiterDemande({ texte: '   ', source: 'micro' }), { type: 'vide', message: "Je n'ai rien entendu, réessaie." }, 'micro vide');
    attendreEgal(traiterDemande({ texte: ' ', source: 'saisie' }), { type: 'vide', message: "Je n'ai rien reçu, réessaie." }, 'saisie vide');
    attendreEgal(traiterDemande({ texte: 'Ajoute à ma to-do...', source: 'micro', id_phrase: 'ajouter-tache', complement: '   ' }),
      { type: 'vide', message: "Je n'ai rien entendu, réessaie." }, 'complément vide');
    attendreEgal(TACHES.length, avant, 'tâche créée');
    attendreEgal(preferencesClavier.historique(), [], 'historique');
    attendreEgal(preferencesClavier.plusUtilisees(5), [], 'usages');
  });

  test('compteurs : ordre décroissant, égalité dans l’ordre du catalogue, phrases utilisées seulement', () => {
    preferencesClavier.compterUtilisation('rappel');
    preferencesClavier.compterUtilisation('brouillon');
    preferencesClavier.compterUtilisation('retrouver');
    preferencesClavier.compterUtilisation('brouillon');
    preferencesClavier.compterUtilisation('retrouver');
    preferencesClavier.compterUtilisation('inconnue');
    attendreEgal(preferencesClavier.plusUtilisees(10).map(p => p.id), ['retrouver', 'brouillon', 'rappel'], 'ordre');
    attendreEgal(preferencesClavier.plusUtilisees(2).map(p => p.id), ['retrouver', 'brouillon'], 'limite');
    attendreEgal(preferencesClavier.plusUtilisees(0), [], 'limite nulle');
    attendreEgal(preferencesClavier.plusUtilisees(-3), [], 'limite négative');
    attendreEgal(JSON.parse(localStorage.getItem(CLE_USAGE)), { rappel: 1, brouillon: 2, retrouver: 2 }, 'stockage');
  });

  test('historique : 20 entrées maximum, plus récente en premier, champs exacts', () => {
    for (let i = 0; i <= 20; i++) {
      traiterDemande({ texte: `Demande ${i}`, source: 'saisie', id_phrase: 'rappel', complement: `c${i}` });
    }
    const historique = preferencesClavier.historique();
    attendreEgal(historique.length, 20, 'longueur');
    attendreEgal(historique[0].texte, 'Demande 20', 'plus récente');
    attendreEgal(historique[19].texte, 'Demande 1', 'plus ancienne conservée');
    attendreEgal(Object.keys(historique[0]).sort(), ['complement', 'date', 'id_phrase', 'source', 'texte'], 'champs');
    attendreEgal([historique[0].id_phrase, historique[0].complement, historique[0].source], ['rappel', 'c20', 'saisie'], 'valeurs');
    attendre(historique.every(e => Number.isFinite(Date.parse(e.date))), 'date invalide');
    attendreEgal(JSON.parse(localStorage.getItem(CLE_USAGE)).rappel, 21, 'usage');
  });

  test('réponse silencieuse : vrai par défaut, faux stocké et relu', () => {
    attendreEgal(preferencesClavier.silencieux(), true, 'défaut');
    preferencesClavier.definirSilencieux('non');
    attendreEgal(preferencesClavier.silencieux(), true, 'valeur non booléenne');
    attendreEgal(localStorage.getItem(CLE_SILENCE), null, 'rien stocké');
    preferencesClavier.definirSilencieux(false);
    attendreEgal(localStorage.getItem(CLE_SILENCE), 'false', 'stockage');
    attendreEgal(preferencesClavier.silencieux(), false, 'relecture');
  });

  test('préférences vides : valeurs par défaut', () => {
    attendreEgal([preferencesClavier.plusUtilisees(5), preferencesClavier.historique(), preferencesClavier.silencieux()],
      [[], [], true], 'valeurs par défaut');
  });

  test('données invalides : JSON cassé ou structure fausse, valeurs vides, tâches intactes', () => {
    const taches = JSON.stringify(TACHES);
    for (const brut of ['{pas json', '[1]', 'null', '{"rappel":-1}', '{"rappel":1.5}', '{"rappel":"2"}']) {
      localStorage.setItem(CLE_USAGE, brut);
      attendreEgal(preferencesClavier.plusUtilisees(5), [], `usages : ${brut}`);
    }
    for (const brut of ['{pas json', 'null', '[{"texte":"a"}]',
      '[{"texte":"a","id_phrase":"","complement":"","source":"autre","date":"2026-10-28T00:00:00.000Z"}]',
      '[{"texte":"a","id_phrase":"","complement":"","source":"saisie","date":"pas une date"}]']) {
      localStorage.setItem(CLE_HISTORIQUE, brut);
      attendreEgal(preferencesClavier.historique(), [], `historique : ${brut}`);
    }
    for (const brut of ['pas json', '"non"', '1', 'null']) {
      localStorage.setItem(CLE_SILENCE, brut);
      attendreEgal(preferencesClavier.silencieux(), true, `silencieux : ${brut}`);
    }
    attendreEgal(JSON.stringify(TACHES), taches, 'tâches modifiées');
  });

  test('localStorage refusé : lecture et écriture sans erreur, méthodes restaurées', () => {
    const getItemOriginal = Storage.prototype.getItem;
    const setItemOriginal = Storage.prototype.setItem;
    let lecture;
    Storage.prototype.getItem = function () { throw new Error('refus'); };
    try {
      lecture = [preferencesClavier.plusUtilisees(5), preferencesClavier.historique(), preferencesClavier.silencieux()];
    } finally {
      Storage.prototype.getItem = getItemOriginal;
    }
    attendreEgal(lecture, [[], [], true], 'lecture refusée');
    Storage.prototype.setItem = function () { throw new Error('refus'); };
    try {
      preferencesClavier.compterUtilisation('rappel');
      preferencesClavier.ajouterHistorique({ texte: 'Test', source: 'saisie' });
      preferencesClavier.definirSilencieux(false);
    } finally {
      Storage.prototype.setItem = setItemOriginal;
    }
    attendreEgal([localStorage.getItem(CLE_USAGE), localStorage.getItem(CLE_HISTORIQUE), localStorage.getItem(CLE_SILENCE)],
      [null, null, null], 'rien écrit');
  });

  test('demande : erreur de création propagée, ni historique ni usage', () => {
    const avant = TACHES.length;
    const original = stockage.enregistrer;
    stockage.enregistrer = () => { throw new Error('Simulation'); };
    try {
      attendreErreur(() => traiterDemande({ texte: 'Retrouve-moi la facture', source: 'clavier', id_phrase: 'retrouver', complement: 'la facture' }), 'Simulation');
    } finally {
      stockage.enregistrer = original;
    }
    attendreEgal(TACHES.length, avant, 'tâche restée');
    attendreEgal(preferencesClavier.historique(), [], 'historique');
    attendreEgal(preferencesClavier.plusUtilisees(5), [], 'usages');
  });

  function avecClavier(fonction) {
    const panneau = document.getElementById('clavier');
    document.getElementById('ouvrir-clavier').click();
    try {
      attendre(panneau.open, 'panneau non ouvert');
      document.getElementById('enlever-phrase').click();
      document.getElementById('saisie-demande').value = '';
      fonction(panneau, document.getElementById('saisie-demande'));
    } finally {
      panneau.close();
    }
  }

  function choisirDebut(debut) {
    const bouton = Array.from(document.querySelectorAll('#categories-clavier button'))
      .find(b => b.textContent === debut);
    attendre(bouton, `phrase absente : ${debut}`);
    bouton.click();
  }

  test('clavier : ouverture, catégories, grandes touches et silence mémorisé', () => {
    avecClavier(panneau => {
      attendreEgal(Array.from(panneau.querySelectorAll('#categories-clavier h3')).map(n => n.textContent),
        ['Retrouver', 'Agenda et to-do', 'Mails', 'Général'], 'catégories');
      attendreEgal(panneau.querySelectorAll('#categories-clavier button').length, 11, 'touches');
      attendreEgal(document.getElementById('section-plus-utilisees').hidden, true, 'favoris masqués');
      attendreEgal(document.getElementById('section-historique').hidden, true, 'historique masqué');
      for (const bouton of panneau.querySelectorAll('button')) {
        attendre(parseFloat(getComputedStyle(bouton).minHeight) >= 56, 'touche trop petite');
      }
      const interrupteur = document.getElementById('reponse-silencieuse');
      attendreEgal(interrupteur.getAttribute('aria-checked'), 'true', 'silence par défaut');
      interrupteur.click();
      attendreEgal(preferencesClavier.silencieux(), false, 'silence changé');
      panneau.close();
      document.getElementById('ouvrir-clavier').click();
      attendreEgal(interrupteur.getAttribute('aria-checked'), 'false', 'silence relu');
    });
  });

  test('clavier : compléter, envoyer, fermer et afficher la tâche avec Annuler', () => {
    avecClavier((panneau, saisie) => {
      choisirDebut('Ajoute à ma to-do...');
      attendre(document.activeElement === saisie, 'focus champ');
      attendreEgal(document.getElementById('debut-phrase').textContent, 'Ajoute à ma to-do...', 'début choisi');
      saisie.value = 'acheter du pain';
      document.getElementById('formulaire-demande').requestSubmit();
      attendre(!panneau.open, 'panneau encore ouvert');
      attendreEgal(saisie.value, '', 'champ non vidé');
      attendre(document.getElementById('phrase-selectionnee').hidden, 'phrase non vidée');
      attendre(Array.from(document.querySelectorAll('#liste-taches .intitule')).some(n => n.textContent === 'acheter du pain'), 'tâche non visible');
      attendreEgal(texteStatut(), 'Ajoutée dans À trier : « acheter du pain »', 'annonce');
      const bouton = document.querySelector('#statut .annuler-dictee');
      attendre(bouton, 'Annuler absent');
      bouton.click();
      attendreEgal(TACHES.find(t => t.intitule === 'acheter du pain').abandonnee_le, dateDuJour(), 'abandon sans perte');
    });
  });

  test('clavier : phrase composée et saisie libre affichées sans HTML interprété', () => {
    avecClavier((panneau, saisie) => {
      choisirDebut('Retrouve-moi...');
      saisie.value = 'le mail <b>FICTIF</b>';
      document.getElementById('formulaire-demande').requestSubmit();
      attendreEgal(preferencesClavier.historique()[0].texte, 'Retrouve-moi le mail <b>FICTIF</b>', 'composition');
      document.getElementById('ouvrir-clavier').click();
      saisie.value = '<i>FICTIF</i> & texte libre';
      document.getElementById('formulaire-demande').requestSubmit();
      attendreEgal(TACHES.at(-1).intitule, '<i>FICTIF</i> & texte libre', 'texte libre');
      attendreEgal(preferencesClavier.historique()[0].source, 'saisie', 'origine libre');
      attendre(!document.querySelector('#liste-taches b, #liste-taches i'), 'HTML interprété');
    });
  });

  test('clavier : historique relancé à l’identique, favoris et limites affichées', () => {
    for (let i = 0; i < 12; i++) {
      preferencesClavier.ajouterHistorique({ texte: `Retrouve-moi FICTIF ${i}`, source: 'clavier', id_phrase: 'retrouver', complement: `FICTIF ${i}` });
    }
    for (const phrase of PHRASES_CLAVIER.slice(0, 6)) preferencesClavier.compterUtilisation(phrase.id);
    avecClavier(panneau => {
      attendreEgal(document.querySelectorAll('#plus-utilisees button').length, 4, '4 favoris maximum');
      attendreEgal(document.querySelectorAll('#historique-demandes button').length, 10, '10 demandes maximum');
      const avant = preferencesClavier.historique()[0];
      const bouton = document.querySelector('#historique-demandes button');
      attendreEgal(bouton.textContent, avant.texte, 'texte affiché');
      bouton.click();
      attendre(!panneau.open, 'panneau encore ouvert');
      const apres = preferencesClavier.historique()[0];
      for (const champ of ['texte', 'source', 'id_phrase', 'complement']) attendreEgal(apres[champ], avant[champ], champ);
      attendreEgal(TACHES.at(-1).intitule, avant.texte, 'tâche relancée');
    });
  });

  test('clavier : Continue envoyé immédiatement sans tâche', () => {
    avecClavier(panneau => {
      const avant = TACHES.length;
      choisirDebut('Continue.');
      attendre(!panneau.open, 'panneau non fermé');
      attendreEgal(TACHES.length, avant, 'tâche créée');
      attendreEgal(texteStatut(), '« Continue. » marchera quand le cerveau de Cap sera branché.', 'message');
      attendre(!document.querySelector('#statut .annuler-dictee'), 'Annuler inapproprié');
    });
  });

  test('clavier : erreur conserve panneau, complément et phrase sélectionnée', () => {
    avecClavier((panneau, saisie) => {
      choisirDebut('Ajoute à ma to-do...');
      saisie.value = 'FICTIF à conserver';
      const original = stockage.enregistrer;
      stockage.enregistrer = () => { throw new Error('Simulation clavier'); };
      try {
        document.getElementById('formulaire-demande').requestSubmit();
        attendre(panneau.open, 'panneau fermé malgré erreur');
        attendreEgal(saisie.value, 'FICTIF à conserver', 'texte perdu');
        attendre(!document.getElementById('phrase-selectionnee').hidden, 'phrase perdue');
        const erreur = panneau.querySelector('.erreur');
        attendre(!erreur.hidden && erreur.textContent.includes('Simulation clavier'), 'erreur absente');
        attendreEgal(preferencesClavier.historique(), [], 'historique après erreur');
      } finally {
        stockage.enregistrer = original;
      }
    });
  });

  test('clavier : demande vide et complément manquant gardent le panneau', () => {
    avecClavier((panneau, saisie) => {
      const avant = TACHES.length;
      saisie.value = '  ';
      document.getElementById('formulaire-demande').requestSubmit();
      attendre(panneau.open, 'panneau fermé sur vide');
      choisirDebut('Retrouve-moi...');
      document.getElementById('formulaire-demande').requestSubmit();
      attendre(panneau.open, 'panneau fermé sans complément');
      attendreEgal(TACHES.length, avant, 'tâche vide créée');
      attendreEgal(preferencesClavier.historique(), [], 'historique vide');
      document.getElementById('enlever-phrase').click();
      attendre(document.getElementById('phrase-selectionnee').hidden, 'phrase non enlevée');
    });
  });

  test('micro : porte d’entrée commune alimente l’historique sans phrase', () => {
    sessionMicro(fake => {
      cliquerMicro();
      fake.instances[0].onresult({ resultIndex: 0, results: [segment('FICTIF micro commun', true)] });
      const entree = preferencesClavier.historique()[0];
      attendreEgal([entree.texte, entree.source, entree.id_phrase, entree.complement],
        ['FICTIF micro commun', 'micro', '', ''], 'historique micro');
    });
  });

  function nettoyerGoogle() {
    for (const espace of [localStorage, sessionStorage]) {
      for (const cle of Object.keys(espace)) {
        if (cle.startsWith('cap_google_')) espace.removeItem(cle);
      }
    }
  }

  function espaceMemoire() {
    const valeurs = new Map();
    return {
      getItem: cle => valeurs.has(cle) ? valeurs.get(cle) : null,
      setItem: (cle, valeur) => valeurs.set(cle, String(valeur)),
      removeItem: cle => valeurs.delete(cle)
    };
  }

  function objetIsole(source, nom, parametres) {
    return new Function(...Object.keys(parametres), source + `\nreturn ${nom};`)(...Object.values(parametres));
  }

  function contexteGoogle() {
    const contexte = {
      localStorage: espaceMemoire(), sessionStorage: espaceMemoire(), window: new EventTarget(),
      navigator: { onLine: true }, requetes: [], redirections: [], historiques: [],
      intervalles: [], delais: new Map(), cadres: [], maintenant: Date.now(),
      location: { hash: '', pathname: '/tests.html', search: '?fictif=1' }
    };
    contexte.Date = class extends Date { static now() { return contexte.maintenant; } };
    contexte.setInterval = (rappel, delai) => contexte.intervalles.push({ rappel, delai });
    let prochainDelai = 0;
    contexte.setTimeout = (rappel, delai) => {
      contexte.delais.set(++prochainDelai, { rappel, delai });
      return prochainDelai;
    };
    contexte.clearTimeout = id => contexte.delais.delete(id);
    contexte.location.assign = adresse => contexte.redirections.push(new URL(adresse));
    contexte.history = { replaceState: (...argumentsAppel) => {
      contexte.historiques.push(argumentsAppel);
      contexte.location.hash = '';
    } };
    contexte.repondre = async () => { throw new Error('Requête simulée non prévue'); };
    contexte.fetch = async (adresse, options = {}) => {
      const requete = { url: new URL(adresse), methode: options.method || 'GET', options,
        corps: options.body ? JSON.parse(options.body) : null };
      contexte.requetes.push(requete);
      return contexte.repondre(requete);
    };
    contexte.googleConnexion = { connecte: () => true, appeler: contexte.fetch };
    contexte.stockage = objetIsole(SOURCE_STOCKAGE, 'stockage', {
      localStorage: contexte.localStorage, TACHES_FICTIVES
    });
    contexte.stockage.charger();
    contexte.TACHES = TACHES_FICTIVES.filter(tache => !tache.parente).slice(0, 3).map(tache => ({ ...tache }));
    contexte.stockage.enregistrer(contexte.TACHES);
    contexte.connexion = () => objetIsole(SOURCE_GOOGLE_CONNEXION, 'googleConnexion', {
      localStorage: contexte.localStorage, sessionStorage: contexte.sessionStorage,
      window: contexte.window, location: contexte.location, history: contexte.history,
      fetch: contexte.fetch, REGLAGES_GOOGLE, crypto, navigator: contexte.navigator, Date: contexte.Date
    });
    contexte.sheets = () => objetIsole(SOURCE_GOOGLE_SHEETS, 'googleSheets', {
      localStorage: contexte.localStorage, googleConnexion: contexte.googleConnexion,
      REGLAGES_GOOGLE, TACHES: contexte.TACHES, stockage: contexte.stockage,
      ETAPES_PAR_DEFAUT, PHRASES_CLAVIER, window: contexte.window
    });
    contexte.sync = googleSheets => objetIsole(SOURCE_SYNCHRONISATION, 'synchronisation', {
      localStorage: contexte.localStorage, window: contexte.window, navigator: contexte.navigator,
      googleConnexion: contexte.googleConnexion, googleSheets, TACHES: contexte.TACHES,
      stockage: contexte.stockage, setInterval: contexte.setInterval, Date: contexte.Date
    });
    contexte.agenda = () => objetIsole(SOURCE_GOOGLE_AGENDA, 'googleAgenda', {
      localStorage: contexte.localStorage, googleConnexion: contexte.googleConnexion, REGLAGES_GOOGLE,
      navigator: contexte.navigator
    });
    return contexte;
  }

  function reponseGoogle(contenu, statut = 200) {
    return new Response(JSON.stringify(contenu), { status: statut, headers: { 'Content-Type': 'application/json' } });
  }

  async function attendreRejet(fonction, fragment) {
    let message = '';
    try { await fonction(); } catch (erreur) { message = String(erreur.message || erreur); }
    attendre(message.includes(fragment), `rejet attendu contenant « ${fragment} », reçu : ${message}`);
  }

  async function testAsync(nom, fonction) {
    let contexte;
    try {
      nettoyerGoogle();
      reinitialiser();
      contexte = contexteGoogle();
      await fonction(contexte);
      for (const requete of contexte.requetes) {
        const patchAgendaFictif = requete.methode === 'PATCH' && contexte.agendaModifiable
          && requete.url.origin === 'https://www.googleapis.com'
          && requete.url.pathname === `/calendar/v3/calendars/${encodeURIComponent(contexte.agendaModifiable)}/events/rdv-fictif`
          && contexte.agendaModifiable !== 'primary';
        attendre(['GET', 'POST'].includes(requete.methode) || patchAgendaFictif, 'opération destructive interdite');
        attendre(!/:clear(?:\?|$)|:batchClear(?:\?|$)/.test(requete.url.href), 'effacement interdit');
        attendre(!requete.corps?.requests?.some(action => Object.keys(action).some(cle => /delete|cutPaste/i.test(cle))),
          'suppression de lignes ou de feuilles interdite');
      }
      resultats.push({ nom, ok: true, erreur: '' });
    } catch (erreur) {
      resultats.push({ nom, ok: false, erreur: String(erreur.message || erreur) });
    } finally {
      for (const cadre of contexte?.cadres || []) cadre.remove();
      nettoyerGoogle();
    }
  }

  const CHAMPS_GOOGLE = ['id', 'intitule', 'categorie', 'sous_categorie', 'fait', 'date_entree',
    'echeance', 'date_realisation', 'priorite', 'parente', 'note', 'avant_le', 'abandonnee_le', 'origine', 'fictif'];
  const ENTETES_GOOGLE = ['Identifiant', 'Intitulé', 'Catégorie', 'Sous-catégorie', 'Fait', "Date d'entrée",
    'Échéance', 'Date de réalisation', 'Priorité', 'Tâche parente', 'Note', 'Avant le', 'Abandonnée le', 'Origine', 'Fictif'];
  const ligneGoogle = tache => CHAMPS_GOOGLE.map(champ => tache[champ]);
  const lireFileGoogle = contexte => JSON.parse(contexte.localStorage.getItem('cap_google_file_v1') || '[]');

  for (const espace of ['sessionStorage', 'localStorage']) {
    await testAsync(`Google OAuth : retour valide avec état en ${espace}`, async c => {
      c[espace].setItem('cap_google_etat_v1', 'etat-fictif');
      c.location.hash = '#access_token=jeton-fictif&expires_in=3600&token_type=Bearer&state=etat-fictif';
      const connexion = c.connexion();
      attendre(connexion.connecte(), 'connexion refusée');
      attendreEgal(connexion.jeton(), 'jeton-fictif', 'jeton');
      attendreEgal(c.location.hash, '', 'fragment effacé');
      attendreEgal(c.historiques, [[null, '', '/tests.html?fictif=1']], 'URL nettoyée sans navigation');
      for (const stockageEtat of [c.localStorage, c.sessionStorage]) {
        attendreEgal(stockageEtat.getItem('cap_google_etat_v1'), null, 'état consommé');
      }
      attendreEgal(c.requetes.length, 0, 'aucun réseau au retour OAuth');
    });
  }

  await testAsync('Google OAuth : mauvais état refusé et fragment effacé', async c => {
    c.sessionStorage.setItem('cap_google_etat_v1', 'attendu-fictif');
    c.localStorage.setItem('cap_google_jeton_v1', JSON.stringify({ jeton: 'ancien-fictif', expiration: Date.now() + 3600000 }));
    c.location.hash = '#access_token=intrus-fictif&expires_in=3600&token_type=Bearer&state=incorrect-fictif';
    const connexion = c.connexion();
    attendre(!connexion.connecte(), 'mauvais état accepté');
    attendre(connexion.message().includes('sécurité'), 'erreur de sécurité absente');
    attendreEgal(c.localStorage.getItem('cap_google_jeton_v1'), null, 'ancien jeton retiré');
    attendreEgal(c.sessionStorage.getItem('cap_google_etat_v1'), null, 'état retiré');
    attendreEgal(c.location.hash, '', 'fragment retiré même en erreur');
    attendreEgal(c.historiques.length, 1, 'nettoyage du fragment');
  });

  await testAsync('Google OAuth : redirection et nouvel état aléatoire', async c => {
    const connexion = c.connexion();
    connexion.seConnecter();
    connexion.seConnecter();
    attendreEgal(c.redirections.length, 2, 'redirections simulées');
    const [premiere, seconde] = c.redirections;
    attendreEgal(seconde.origin + seconde.pathname, 'https://accounts.google.com/o/oauth2/v2/auth', 'destination OAuth');
    const parametres = seconde.searchParams;
    for (const [cle, valeur] of Object.entries({ client_id: REGLAGES_GOOGLE.id_client,
      redirect_uri: REGLAGES_GOOGLE.adresse_retour, response_type: 'token',
      scope: REGLAGES_GOOGLE.autorisations.join(' '), include_granted_scopes: 'true' })) {
      attendreEgal(parametres.get(cle), valeur, `paramètre ${cle}`);
    }
    attendre(/^[a-f0-9]{64}$/.test(parametres.get('state')), 'état insuffisant');
    attendre(premiere.searchParams.get('state') !== parametres.get('state'), 'état réutilisé');
    for (const espace of [c.localStorage, c.sessionStorage]) {
      attendreEgal(espace.getItem('cap_google_etat_v1'), parametres.get('state'), 'état enregistré');
    }
    attendre(!parametres.has('client_secret'), 'secret dans la redirection');
    attendreEgal(c.requetes.length, 0, 'aucun fetch de connexion');
  });

  await testAsync('Google connexion : Response, statut HTTP et destinations autorisées', async c => {
    c.localStorage.setItem('cap_google_jeton_v1', JSON.stringify({ jeton: 'jeton-fictif', expiration: Date.now() + 3600000 }));
    const connexion = c.connexion();
    c.repondre = async () => reponseGoogle({ fictif: true });
    const reponse = await connexion.appeler('https://www.googleapis.com/drive/v3/files');
    attendre(reponse instanceof Response, 'Response non renvoyée');
    attendreEgal(await reponse.json(), { fictif: true }, 'contenu réponse');
    attendreEgal(c.requetes[0].options.headers.get('Authorization'), 'Bearer jeton-fictif', 'autorisation');
    attendreEgal(c.requetes[0].options.cache, 'no-store', 'jeton hors cache');
    attendreEgal(c.requetes[0].options.redirect, 'error', 'redirections interdites');
    c.repondre = async () => reponseGoogle({}, 403);
    let statut;
    try { await connexion.appeler('https://sheets.googleapis.com/v4/spreadsheets'); }
    catch (erreur) { statut = erreur.statut; }
    attendreEgal(statut, 403, 'statut HTTP conservé');
    const nombre = c.requetes.length;
    await attendreRejet(() => connexion.appeler('http://www.googleapis.com/drive/v3/files'), 'non autorisée');
    await attendreRejet(() => connexion.appeler('https://accounts.google.com/o/oauth2/v2/auth'), 'non autorisée');
    attendreEgal(c.requetes.length, nombre, 'destinations interdites jamais appelées');
  });

  await testAsync('Google Sheets : création RAW, entêtes, trois onglets et cases booléennes', async c => {
    c.repondre = async r => {
      if (r.methode === 'GET' && r.url.pathname === '/drive/v3/files') return reponseGoogle({ files: [] });
      if (r.methode === 'POST' && r.url.pathname === '/v4/spreadsheets') return reponseGoogle({ spreadsheetId: 'tableau-fictif' });
      if (r.methode === 'POST' && ['/v4/spreadsheets/tableau-fictif/values:batchUpdate', '/v4/spreadsheets/tableau-fictif:batchUpdate'].includes(r.url.pathname)) return reponseGoogle({});
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const sheets = c.sheets();
    attendreEgal(await sheets.trouverOuCreer(), { id: 'tableau-fictif', cree: true }, 'tableau créé');
    const creation = c.requetes.find(r => r.url.pathname === '/v4/spreadsheets').corps;
    attendreEgal(creation.properties.title, REGLAGES_GOOGLE.nom_fichier_taches, 'nom fictif');
    attendreEgal(creation.sheets.map(onglet => onglet.properties.title), Object.values(REGLAGES_GOOGLE.onglets), 'trois onglets');
    attendre(creation.sheets.every(onglet => onglet.properties.gridProperties.frozenRowCount === 1), 'entêtes non figées');
    const remplissage = c.requetes.find(r => r.url.pathname.endsWith('/values:batchUpdate')).corps;
    attendreEgal(remplissage.valueInputOption, 'RAW', 'écriture brute');
    attendreEgal(remplissage.data.length, 5, 'cinq onglets remplis');
    attendreEgal(remplissage.data[0].values, [ENTETES_GOOGLE, ...c.TACHES.map(ligneGoogle)], 'entêtes et tâches exactes');
    attendreEgal(remplissage.data[1].values, [['Modèle', 'Étape', 'Retirée le', 'Modifiée le'], ...Object.entries(ETAPES_PAR_DEFAUT).flatMap(([modele, etapes]) => etapes.map(etape => [modele, etape, '', '']))], 'modèles');
    attendreEgal(remplissage.data[2].values, [['Catégorie', 'Sous-catégorie de', 'Couleur', 'Retirée le', 'Modifiée le', 'Ordre']], 'catégories');
    attendreEgal(remplissage.data[3].values, [['Date et heure', 'Venu de', 'Ce que Max a dit ou touché', 'Ce que Cap a compris', 'Ce que Cap a fait']], 'journal');
    attendreEgal(remplissage.data[4].values, [['Identifiant', 'Catégorie', 'Début', 'À compléter', 'Action'], ...PHRASES_CLAVIER.map(p => [p.id, p.categorie, p.debut, p.a_completer, p.action])], 'phrases');
    const validations = c.requetes.find(r => r.url.pathname.endsWith('tableau-fictif:batchUpdate')).corps.requests;
    attendreEgal(validations.map(r => r.setDataValidation.range.startColumnIndex), [4, 14], 'colonnes booléennes');
    attendre(validations.every(r => r.setDataValidation.rule.condition.type === 'BOOLEAN' && r.setDataValidation.rule.strict), 'validation booléenne');
    attendreEgal(c.localStorage.getItem('cap_google_fichier_v1'), 'tableau-fictif', 'identifiant conservé');
  });

  async function sheetsExistant(c, lignes) {
    c.localStorage.setItem('cap_google_fichier_v1', 'tableau-fictif');
    c.repondre = async r => {
      if (r.methode === 'GET' && r.url.pathname === '/drive/v3/files/tableau-fictif') return reponseGoogle({ id: 'tableau-fictif', trashed: false });
      if (r.methode === 'GET' && r.url.pathname.startsWith('/v4/spreadsheets/tableau-fictif/values/')) {
        attendreEgal(r.url.searchParams.get('valueRenderOption'), 'UNFORMATTED_VALUE', 'lecture sans formatage');
        return reponseGoogle({ values: [ENTETES_GOOGLE, ...lignes] });
      }
      if (r.methode === 'POST' && (r.url.pathname.endsWith('/values:batchUpdate') || r.url.pathname.endsWith(':append'))) return reponseGoogle({});
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const sheets = c.sheets();
    attendreEgal(await sheets.trouverOuCreer(), { id: 'tableau-fictif', cree: false }, 'tableau retrouvé');
    return sheets;
  }

  await testAsync('Google Sheets : mise à jour ligne existante et append sans effacement', async c => {
    const [existante, nouvelle] = c.TACHES;
    const sheets = await sheetsExistant(c, [[], ligneGoogle(existante)]);
    const modifiee = { ...existante, intitule: '=FICTIF <b>texte exact</b>' };
    attendreEgal(await sheets.ecrireTaches([modifiee, nouvelle]), [existante.id, nouvelle.id], 'identifiants écrits');
    const misesAJour = c.requetes.filter(r => r.methode === 'POST');
    attendreEgal(misesAJour.length, 2, 'update et append seulement');
    attendreEgal(misesAJour[0].corps, { valueInputOption: 'RAW', data: [{ range: "'Tâches'!A3:O3", values: [ligneGoogle(modifiee)] }] }, 'ligne exacte mise à jour');
    attendreEgal(misesAJour[1].url.searchParams.get('valueInputOption'), 'RAW', 'append brut');
    attendreEgal(misesAJour[1].url.searchParams.get('insertDataOption'), 'INSERT_ROWS', 'ajout sans écraser');
    attendreEgal(misesAJour[1].corps.values, [ligneGoogle(nouvelle)], 'nouvelle tâche exacte');
  });

  await testAsync('Google Sheets : lignes illisibles, doublons et parents protégés', async c => {
    const [parent, doublon, invalide] = c.TACHES;
    const enfant = { ...parent, id: 'enfant-fictif', intitule: 'Étape FICTIF', parente: parent.id };
    const orpheline = { ...parent, id: 'orpheline-fictive', parente: 'parent-inconnu-fictif' };
    const lignes = [ligneGoogle(parent), ligneGoogle(doublon), ligneGoogle(doublon),
      ligneGoogle({ ...invalide, fait: 'illisible' }), ligneGoogle(enfant), ligneGoogle(orpheline)];
    const sheets = await sheetsExistant(c, lignes);
    const lecture = await sheets.lireTaches();
    attendreEgal(lecture.taches.map(t => t.id), [parent.id, enfant.id], 'seules les lignes valides admises');
    attendreEgal([...lecture.lignes], [[parent.id, 2], [enfant.id, 6]], 'numéros de lignes');
    attendreEgal(lecture.illisibles.map(l => l.ligne).sort((a, b) => a - b), [3, 4, 5, 7], 'lignes protégées');
    attendreEgal(await sheets.ecrireTaches([parent, doublon, invalide, orpheline]), [parent.id], 'seule la tâche saine écrite');
    const ecritures = c.requetes.filter(r => r.methode === 'POST');
    attendreEgal(ecritures.length, 1, 'aucun append des identifiants protégés');
    attendreEgal(ecritures[0].corps.data.map(d => d.range), ["'Tâches'!A2:O2"], 'aucune ligne illisible touchée');
  });

  await testAsync('Google Sheets : entêtes illisibles bloquent toute écriture', async c => {
    const sheets = await sheetsExistant(c, []);
    c.repondre = async () => reponseGoogle({ values: [['Entêtes FICTIF incorrectes']] });
    await attendreRejet(() => sheets.ecrireTaches(c.TACHES), 'colonnes');
    attendreEgal(c.requetes.filter(r => r.methode !== 'GET').length, 0, 'aucune écriture');
  });

  function fauxSheetsSync(c, distantes, illisibles = []) {
    const envois = [];
    return {
      envois,
      trouverOuCreer: async () => ({ id: 'tableau-fictif', cree: false }),
      lireTaches: async () => ({ taches: distantes.map(t => ({ ...t })), illisibles,
        lignes: new Map(distantes.map((t, indice) => [t.id, indice + 2])) }),
      ecrireTaches: async taches => { envois.push(taches.map(t => ({ ...t }))); return taches.map(t => t.id); }
    };
  }

  await testAsync('Google sync : fusion remote hors file, local en file et zéro perte', async c => {
    const [horsFile, enFile, absente] = c.TACHES;
    const inconnue = { ...horsFile, id: 'distante-fictive', intitule: 'Inconnue locale FICTIF' };
    const protege = { ...horsFile, id: 'protegee-fictive' };
    c.TACHES.push(protege);
    c.stockage.enregistrer(c.TACHES);
    c.localStorage.setItem('cap_google_file_v1', JSON.stringify([enFile.id]));
    const sheets = fauxSheetsSync(c, [{ ...horsFile, note: 'Google FICTIF' },
      { ...enFile, note: 'Ancienne version Google FICTIF' }, inconnue], [{ id: protege.id, ligne: 9 }]);
    const sync = c.sync(sheets);
    await sync.demarrer();
    attendreEgal(c.TACHES.find(t => t.id === horsFile.id).note, 'Google FICTIF', 'Google gagne hors file');
    attendreEgal(c.TACHES.find(t => t.id === enFile.id), enFile, 'local gagne en file');
    attendreEgal(c.TACHES.find(t => t.id === inconnue.id), inconnue, 'inconnue importée');
    attendreEgal(c.TACHES.find(t => t.id === absente.id), absente, 'absente conservée');
    attendreEgal(c.TACHES.find(t => t.id === protege.id), protege, 'illisible distante ne retire pas le local');
    attendreEgal(c.TACHES.length, 5, 'aucune tâche perdue');
    attendreEgal(sheets.envois.flat().map(t => t.id).sort(), [enFile.id, absente.id].sort(), 'absente et file envoyées, protégée ignorée');
    attendreEgal(lireFileGoogle(c), [], 'file acquittée');
    attendreEgal(JSON.parse(c.localStorage.getItem(CLE)), c.TACHES, 'fusion sauvegardée');
    attendre(sync.etat().includes('illisibles'), 'avertissement des lignes illisibles');
  });

  await testAsync('Google sync : échec de validation, mémoire et sauvegarde intactes', async c => {
    const avant = JSON.stringify(c.TACHES);
    const sauvegarde = c.localStorage.getItem(CLE);
    c.localStorage.setItem('cap_google_file_v1', JSON.stringify([c.TACHES[1].id]));
    const queue = c.localStorage.getItem('cap_google_file_v1');
    const sheets = fauxSheetsSync(c, [{ ...c.TACHES[0], parente: 'parent-absent-fictif' }]);
    const sync = c.sync(sheets);
    await sync.demarrer();
    attendreEgal(JSON.stringify(c.TACHES), avant, 'mémoire inchangée');
    attendreEgal(c.localStorage.getItem(CLE), sauvegarde, 'sauvegarde inchangée');
    attendreEgal(c.localStorage.getItem('cap_google_file_v1'), queue, 'file inchangée');
    attendreEgal(sheets.envois.length, 0, 'aucun envoi après validation refusée');
    attendre(sync.etat().includes('interrompue'), 'erreur visible');
  });

  await testAsync('Google sync : panne réseau garde la file puis reprise sans perte', async c => {
    const sheets = fauxSheetsSync(c, c.TACHES);
    const sync = c.sync(sheets);
    await sync.demarrer();
    const envoyer = sheets.ecrireTaches;
    sheets.ecrireTaches = async () => { throw new TypeError('Réseau FICTIF indisponible'); };
    c.navigator.onLine = false;
    sync.signaler([c.TACHES[0].id, c.TACHES[0].id]);
    attendreEgal(lireFileGoogle(c), [c.TACHES[0].id], 'file dédupliquée hors connexion');
    c.navigator.onLine = true;
    await sync.envoyer();
    attendreEgal(lireFileGoogle(c), [c.TACHES[0].id], 'file conservée après panne');
    attendre(sync.etat().includes('attente'), 'panne annoncée');
    sheets.ecrireTaches = envoyer;
    await sync.envoyer();
    attendreEgal(lireFileGoogle(c), [], 'file vidée après succès');
    attendreEgal(sheets.envois.flat().map(t => t.id), [c.TACHES[0].id], 'tâche envoyée une fois avec succès');
    attendreEgal(sync.etat(), 'synchronisé', 'reprise terminée');
  });

  await testAsync('Google sync : fetch échoue, file persistante puis retour en ligne', async c => {
    c.localStorage.setItem('cap_google_jeton_v1', JSON.stringify({ jeton: 'jeton-fictif', expiration: Date.now() + 3600000 }));
    c.googleConnexion = c.connexion();
    const sheets = await sheetsExistant(c, c.TACHES.map(ligneGoogle));
    const repondre = c.repondre;
    const sync = c.sync(sheets);
    await sync.demarrer();
    c.navigator.onLine = false;
    sync.signaler([c.TACHES[0].id]);
    c.repondre = async () => { throw new TypeError('Fetch FICTIF interrompu'); };
    c.navigator.onLine = true;
    await sync.envoyer();
    attendreEgal(lireFileGoogle(c), [c.TACHES[0].id], 'file persistante après fetch refusé');
    const nouvelleSession = c.sync(c.sheets());
    c.repondre = repondre;
    c.window.dispatchEvent(new Event('online'));
    await nouvelleSession.demarrer();
    await sync.envoyer();
    attendreEgal(lireFileGoogle(c), [], 'file reprise et acquittée');
    attendre(c.requetes.some(r => r.methode === 'POST' && r.url.pathname.endsWith('/values:batchUpdate')), 'écriture Google simulée absente');
  });

  await testAsync('Google sync : verrou et nouvelle version pendant un envoi', async c => {
    const sheets = fauxSheetsSync(c, c.TACHES);
    const sync = c.sync(sheets);
    await sync.demarrer();
    c.navigator.onLine = false;
    sync.signaler([c.TACHES[0].id]);
    let terminer;
    const appels = [];
    sheets.ecrireTaches = async taches => {
      appels.push(taches.map(tache => ({ ...tache })));
      if (appels.length === 1) await new Promise(resolve => { terminer = resolve; });
      return taches.map(tache => tache.id);
    };
    c.navigator.onLine = true;
    const premier = sync.envoyer();
    const second = sync.envoyer();
    attendre(premier === second, 'deux envois concurrents');
    await Promise.resolve();
    c.TACHES[0].note = 'Nouvelle note FICTIF pendant l’envoi';
    c.stockage.enregistrer(c.TACHES);
    sync.signaler([c.TACHES[0].id]);
    terminer();
    await premier;
    attendreEgal(appels.length, 2, 'la nouvelle version doit être envoyée séparément');
    attendreEgal(appels[1][0].note, c.TACHES[0].note, 'dernière version conservée');
    attendreEgal(lireFileGoogle(c), [], 'seule la dernière version réussie acquittée');
  });

  await testAsync('Google sync : 401 retire le jeton mais conserve la file', async c => {
    c.localStorage.setItem('cap_google_jeton_v1', JSON.stringify({ jeton: 'jeton-fictif', expiration: Date.now() + 3600000 }));
    c.googleConnexion = c.connexion();
    const sheets = fauxSheetsSync(c, c.TACHES);
    const sync = c.sync(sheets);
    await sync.demarrer();
    c.navigator.onLine = false;
    sync.signaler([c.TACHES[0].id]);
    c.navigator.onLine = true;
    let deconnexions = 0;
    c.window.addEventListener('cap-google-deconnecte', () => deconnexions++);
    c.repondre = async () => reponseGoogle({}, 401);
    sheets.ecrireTaches = async () => c.googleConnexion.appeler('https://sheets.googleapis.com/v4/spreadsheets/tableau-fictif');
    const avant = JSON.stringify(c.TACHES);
    await sync.envoyer();
    attendreEgal(deconnexions, 1, 'déconnexion signalée');
    attendre(!c.googleConnexion.connecte(), 'jeton invalide conservé');
    attendreEgal(lireFileGoogle(c), [c.TACHES[0].id], 'file conservée après 401');
    attendreEgal(JSON.stringify(c.TACHES), avant, 'aucune tâche modifiée');
    await sync.envoyer();
    attendreEgal(c.requetes.length, 1, 'pas de nouvel appel sans connexion');
  });

  await testAsync('Google Agenda : heures Paris et horaires de journées entières', async c => {
    c.localStorage.setItem('cap_google_agenda_v1', 'agenda-fictif');
    c.repondre = async r => {
      if (r.methode === 'GET' && r.url.pathname === '/calendar/v3/calendars/agenda-fictif') return reponseGoogle({ id: 'agenda-fictif' });
      if (r.methode === 'GET' && r.url.pathname === '/calendar/v3/calendars/agenda-fictif/events') {
        attendreEgal(r.url.searchParams.get('singleEvents'), 'true', 'récurrences dépliées');
        attendreEgal(r.url.searchParams.get('orderBy'), 'startTime', 'tri chronologique');
        attendreEgal(r.url.searchParams.get('maxResults'), '5', 'limite');
        return reponseGoogle({ items: [
          { summary: 'Horaire FICTIF', start: { dateTime: '2030-01-10T09:15:00Z' } },
          { summary: 'Journée FICTIF', start: { date: '2030-01-11' }, description: '14h30 – lieu FICTIF' },
          { summary: 'Autre FICTIF', start: { date: '2030-01-12' }, description: '9:05 – lieu FICTIF' },
          { summary: 'Sans heure FICTIF', start: { date: '2030-01-13' }, description: 'Toute la journée' },
          { summary: 'Annulé FICTIF', status: 'cancelled', start: { date: '2030-01-14' } }
        ] });
      }
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    attendreEgal((await c.agenda().prochainsRendezVous(5)).map(({ titre, date, heure, journee_entiere }) =>
      ({ titre, date, heure, journee_entiere })), [
      { titre: 'Horaire FICTIF', date: '2030-01-10', heure: '10:15', journee_entiere: false },
      { titre: 'Journée FICTIF', date: '2030-01-11', heure: '14:30', journee_entiere: true },
      { titre: 'Autre FICTIF', date: '2030-01-12', heure: '09:05', journee_entiere: true },
      { titre: 'Sans heure FICTIF', date: '2030-01-13', heure: '', journee_entiere: true }
    ], 'rendez-vous normalisés');
    attendre(c.requetes.every(r => r.methode === 'GET'), 'lecture seule de l’agenda existant');
  });

  await testAsync('Google Agenda : agenda secondaire, quatre FICTIF, jamais le principal', async c => {
    c.localStorage.setItem('cap_google_agenda_v1', 'primary');
    c.repondre = async r => {
      if (r.methode === 'GET' && r.url.pathname === '/calendar/v3/users/me/calendarList') {
        return reponseGoogle({ items: [{ id: 'primary', summary: REGLAGES_GOOGLE.nom_agenda, primary: true }] });
      }
      if (r.methode === 'POST' && r.url.pathname === '/calendar/v3/calendars') {
        attendreEgal(r.corps.summary, REGLAGES_GOOGLE.nom_agenda, 'nom de l’agenda secondaire');
        return reponseGoogle({ id: 'agenda-secondaire-fictif' });
      }
      if (r.methode === 'POST' && r.url.pathname === '/calendar/v3/calendars/agenda-secondaire-fictif/events') return reponseGoogle({ id: 'evenement-fictif' });
      if (r.methode === 'GET' && r.url.pathname === '/calendar/v3/calendars/agenda-secondaire-fictif') return reponseGoogle({ id: 'agenda-secondaire-fictif' });
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const agenda = c.agenda();
    attendreEgal(await agenda.trouverOuCreer(), 'agenda-secondaire-fictif', 'agenda secondaire créé');
    const evenements = c.requetes.filter(r => r.methode === 'POST' && r.url.pathname.endsWith('/events'));
    attendreEgal(evenements.length, 4, 'quatre rendez-vous fictifs');
    attendre(evenements.every(r => r.corps.summary.startsWith('FICTIF – ')), 'rendez-vous non marqué fictif');
    attendreEgal(c.requetes.find(r => r.methode === 'POST' && r.url.pathname === '/calendar/v3/calendars').corps.timeZone,
      'Europe/Paris', 'fuseau de l’agenda');
    const aujourdHuiParis = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Paris' }).format(new Date());
    for (const evenement of evenements) {
      const date = (evenement.corps.start.date || evenement.corps.start.dateTime).slice(0, 10);
      const jours = (new Date(`${date}T12:00:00Z`) - new Date(`${aujourdHuiParis}T12:00:00Z`)) / 86400000;
      attendre(jours >= 1 && jours <= 7, 'rendez-vous hors des sept prochains jours');
    }
    attendreEgal(evenements.filter(r => r.corps.start.date).length, 1, 'une journée entière');
    attendreEgal(evenements.filter(r => r.corps.start.dateTime).length, 3, 'trois rendez-vous horaires');
    attendre(evenements.every(r => r.corps.end.date || r.corps.end.dateTime), 'fin manquante');
    attendreEgal(await agenda.trouverOuCreer(), 'agenda-secondaire-fictif', 'agenda réutilisé');
    attendreEgal(c.requetes.filter(r => r.methode === 'POST').length, 5, 'aucune seconde création');
    attendre(c.requetes.every(r => !r.url.pathname.includes('/calendars/primary')), 'agenda principal touché');
  });

  await testAsync('Google Agenda : accès liste refusé et formats d’heures en description', async c => {
    let cree = false;
    const descriptions = ['14h30 – FICTIF', '14h – FICTIF', '14:30 – FICTIF', '9h05 – FICTIF',
      '25h30 – FICTIF', '14h99 – FICTIF', '14h300 – FICTIF', 'FICTIF à 14h'];
    c.repondre = async r => {
      if (r.url.pathname.endsWith('/users/me/calendarList')) {
        const erreur = new Error('Accès refusé FICTIF');
        erreur.statut = 403;
        throw erreur;
      }
      if (r.methode === 'POST' && r.url.pathname === '/calendar/v3/calendars') {
        cree = true;
        return reponseGoogle({ id: 'agenda-secondaire-fictif' });
      }
      if (r.methode === 'POST' && r.url.pathname.endsWith('/events')) return reponseGoogle({});
      if (r.methode === 'GET' && r.url.pathname.endsWith('/events')) {
        return reponseGoogle({ items: descriptions.map(description => ({
          summary: 'Heure FICTIF', start: { date: '2030-01-11' }, description
        })) });
      }
      throw new Error('Requête inattendue FICTIF');
    };
    const rendezVous = await c.agenda().prochainsRendezVous(8);
    attendre(cree, '403 ne doit pas empêcher la création de l’agenda secondaire');
    attendreEgal(rendezVous.map(rendezVous => rendezVous.heure),
      ['14:30', '14:00', '14:30', '09:05', '', '', '', ''], 'formats exacts et heures invalides');
  });

  function preparerFicheRendezVous(c, changements = {}) {
    const evenement = {
      id: 'rdv-fictif', etag: '"version-fictive"', summary: 'Consultation FICTIF',
      location: '12 rue Fictive',
      description: 'Préparation FICTIF\nTéléphone : 01 00 00 00 00\nMail : cabinet.fictif@example.com',
      start: { dateTime: '2030-01-10T09:15:00Z' },
      end: { dateTime: '2030-01-10T10:00:00Z' },
      reminders: { useDefault: false, overrides: [{ method: 'popup', minutes: 60 }, { method: 'email', minutes: 10 }] },
      ...changements
    };
    c.agendaModifiable = 'agenda-fictif';
    c.localStorage.setItem('cap_google_agenda_v1', c.agendaModifiable);
    c.repondre = async r => {
      const base = `/calendar/v3/calendars/${encodeURIComponent(c.agendaModifiable)}`;
      if (r.methode === 'GET' && r.url.pathname === base) {
        return reponseGoogle({ id: c.agendaModifiable, summary: REGLAGES_GOOGLE.nom_agenda, primary: false });
      }
      if (r.methode === 'GET' && r.url.pathname === `${base}/events`) return reponseGoogle({ items: [evenement] });
      if (r.methode === 'GET' && r.url.pathname === `${base}/events/${evenement.id}`) return reponseGoogle(evenement);
      if (r.methode === 'PATCH' && r.url.pathname === `${base}/events/${evenement.id}`) {
        const resultat = { ...evenement, ...r.corps };
        for (const champ of ['start', 'end']) {
          if (r.corps[champ]?.dateTime) resultat[champ] = { ...r.corps[champ],
            dateTime: r.corps[champ].dateTime + (r.corps[champ].dateTime.startsWith('2030-07-') ? '+02:00' : '+01:00') };
        }
        return reponseGoogle(resultat);
      }
      throw new Error(`Requête de fiche inattendue : ${r.methode} ${r.url}`);
    };
    return evenement;
  }

  function ancienRendezVous(evenement) {
    return Object.fromEntries(['summary', 'location', 'description', 'start', 'end', 'reminders']
      .map(champ => [champ, evenement[champ] ?? null]));
  }

  await testAsync('Google Agenda fiche : description canonique aller-retour sans perte', async c => {
    const agenda = c.agenda();
    const informations = { heure_journee: '09:05', notes: 'Notes FICTIF <b>libres</b>\nDeuxième ligne\n',
      telephone: '01 00 00 00 00', mail: 'contact.fictif@example.com' };
    const texte = '09h05 – Notes FICTIF <b>libres</b>\nDeuxième ligne\n\nTéléphone : 01 00 00 00 00\nMail : contact.fictif@example.com';
    attendreEgal(agenda.ecrireDescription(informations), texte, 'description canonique');
    attendreEgal(agenda.lireDescription(texte), informations, 'champs extraits');
    attendreEgal(agenda.ecrireDescription(agenda.lireDescription(texte)), texte, 'second aller-retour');
    attendreEgal(c.requetes.length, 0, 'conversion locale');
  });

  for (const libelle of ['Téléphone', 'TELEPHONE', 'tÉlÉpHoNe']) {
    await testAsync(`Google Agenda fiche : extraction accent et casse ${libelle}`, async c => {
      attendreEgal(c.agenda().lireDescription(`Notes FICTIF\n${libelle} : 01 00 00 00 00\nmAiL : fictif@example.com`),
        { heure_journee: '', notes: 'Notes FICTIF', telephone: '01 00 00 00 00', mail: 'fictif@example.com' }, 'coordonnées extraites');
    });
  }

  await testAsync('Google Agenda fiche : notes libres et anciennes coordonnées doublonnées conservées', async c => {
    const agenda = c.agenda();
    const notes = 'Texte FICTIF à 14h\nTéléphone : ancien FICTIF\nMail : ancien.fictif@example.com\n\nTéléphone :\nMail :\nFin <b>FICTIF</b>';
    const texte = `${notes}\nTéléphone : 01 00 00 00 00\nMail : nouveau.fictif@example.com`;
    const informations = agenda.lireDescription(texte);
    attendreEgal(informations, { heure_journee: '', notes, telephone: '01 00 00 00 00', mail: 'nouveau.fictif@example.com' }, 'doublons gardés dans les notes');
    attendreEgal(agenda.ecrireDescription(informations), texte, 'texte complet conservé');
    attendreEgal(agenda.lireDescription('Notes FICTIF\n  espaces conservés  '),
      { heure_journee: '', notes: 'Notes FICTIF\n  espaces conservés  ', telephone: '', mail: '' }, 'notes libres intactes');
  });

  await testAsync('Google Agenda fiche : heure de journée entière extraite et réécrite', async c => {
    const agenda = c.agenda();
    for (const texte of ['9h05 – Notes FICTIF', '09:05 — Notes FICTIF', '9h05 - Notes FICTIF']) {
      const informations = agenda.lireDescription(texte);
      attendreEgal(informations, { heure_journee: '09:05', notes: 'Notes FICTIF', telephone: '', mail: '' }, 'heure et notes');
      attendreEgal(agenda.ecrireDescription(informations), '09h05 – Notes FICTIF', 'heure canonique');
    }
    attendreEgal(agenda.lireDescription('14h – Notes FICTIF').heure_journee, '14:00', 'heure sans minutes');
    attendreEgal(agenda.lireDescription('25h30 – Notes FICTIF').notes, '25h30 – Notes FICTIF', 'heure invalide conservée');
  });

  await testAsync('Google Agenda fiche : prochains rendez-vous enrichis et cache identique', async c => {
    const evenement = preparerFicheRendezVous(c);
    const agenda = c.agenda();
    const attendu = { id: evenement.id, titre: evenement.summary, date: '2030-01-10', heure: '10:15', heure_fin: '11:00',
      journee_entiere: false, lieu: evenement.location, notes: 'Préparation FICTIF', telephone: '01 00 00 00 00',
      mail: 'cabinet.fictif@example.com', rappels: [60], description: evenement.description };
    attendreEgal(await agenda.prochainsRendezVous(), [attendu], 'tous les champs de la fiche');
    attendreEgal(agenda.lireCache(), [attendu], 'lecture du cache enrichi');
    const cache = c.localStorage.getItem('cap_google_rendezvous_v1');
    attendreEgal(JSON.parse(cache).rendezvous, [attendu], 'cache persistant');
    c.googleConnexion.connecte = () => false;
    const nombre = c.requetes.length;
    attendreEgal(await agenda.prochainsRendezVous(), [attendu], 'secours hors connexion enrichi');
    attendreEgal(c.requetes.length, nombre, 'aucune requête déconnectée');
    attendreEgal(c.localStorage.getItem('cap_google_rendezvous_v1'), cache, 'cache non réécrit');
  });

  await testAsync('Google Agenda fiche : PATCH limité après identité, GET événement et historique complet', async c => {
    const evenement = preparerFicheRendezVous(c);
    const operations = [];
    const enregistrer = c.localStorage.setItem;
    c.localStorage.setItem = (cle, valeur) => {
      if (cle === 'cap_rdv_historique_v1') operations.push('historique');
      return enregistrer(cle, valeur);
    };
    const repondre = c.repondre;
    c.repondre = async r => {
      operations.push(`${r.methode} ${r.url.pathname}`);
      if (r.methode === 'PATCH') {
        const historique = JSON.parse(c.localStorage.getItem('cap_rdv_historique_v1'));
        attendreEgal(historique[0].ancien, ancienRendezVous(evenement), 'sauvegarde déjà écrite avant PATCH');
        attendreEgal(r.corps, { summary: 'Nouveau titre FICTIF' }, 'uniquement le champ demandé');
        attendreEgal(r.options.headers['If-Match'], evenement.etag, 'version concurrente protégée');
      }
      return repondre(r);
    };
    const avant = Date.now();
    const agenda = c.agenda();
    const resultat = await agenda.modifierRendezVous(evenement.id, { titre: 'Nouveau titre FICTIF' });
    attendreEgal(operations[0], 'GET /calendar/v3/calendars/agenda-fictif', 'identité agenda avant événement');
    attendreEgal(operations.filter(operation => operation !== 'GET /calendar/v3/calendars/agenda-fictif'),
      ['GET /calendar/v3/calendars/agenda-fictif/events/rdv-fictif', 'historique',
        'PATCH /calendar/v3/calendars/agenda-fictif/events/rdv-fictif'], 'GET événement puis sauvegarde puis PATCH');
    const historique = agenda.lireHistorique();
    attendreEgal(historique.length, 1, 'une ancienne version');
    attendreEgal(historique[0].id, evenement.id, 'identifiant sauvegardé');
    attendre(Date.parse(historique[0].enregistre_le) >= avant && Date.parse(historique[0].enregistre_le) <= Date.now(), 'date réelle de sauvegarde');
    attendreEgal(historique[0].ancien, ancienRendezVous(evenement), 'tous les champs anciens');
    attendreEgal(resultat, { id: evenement.id, titre: 'Nouveau titre FICTIF', date: '2030-01-10', heure: '10:15', heure_fin: '11:00',
      journee_entiere: false, lieu: evenement.location, notes: 'Préparation FICTIF', telephone: '01 00 00 00 00',
      mail: 'cabinet.fictif@example.com', rappels: [60], description: evenement.description }, 'objet de retour enrichi');
    attendreEgal(agenda.lireCache(), [resultat], 'fiche modifiée mise en cache');
    attendre(c.requetes.every(r => !r.url.pathname.includes('/calendars/primary') && r.methode !== 'DELETE'), 'jamais primary ni DELETE');
  });

  await testAsync('Google Agenda fiche : agenda découvert par trouverOuCreer utilisé pour le PATCH', async c => {
    const evenement = preparerFicheRendezVous(c);
    c.localStorage.setItem('cap_google_agenda_v1', 'primary');
    c.agendaModifiable = 'agenda-decouvert-fictif';
    const repondre = c.repondre;
    c.repondre = async r => r.url.pathname === '/calendar/v3/users/me/calendarList'
      ? reponseGoogle({ items: [{ id: 'primary', summary: REGLAGES_GOOGLE.nom_agenda, primary: true },
        { id: c.agendaModifiable, summary: REGLAGES_GOOGLE.nom_agenda, primary: false }] }) : repondre(r);
    await c.agenda().modifierRendezVous(evenement.id, { lieu: 'Autre lieu FICTIF' });
    attendreEgal(c.localStorage.getItem('cap_google_agenda_v1'), c.agendaModifiable, 'identifiant découvert mémorisé');
    attendreEgal(c.requetes.filter(r => r.methode === 'PATCH').map(r => r.url.pathname),
      ['/calendar/v3/calendars/agenda-decouvert-fictif/events/rdv-fictif'], 'PATCH seulement sur l’agenda trouvé');
    attendre(c.requetes.every(r => !r.url.pathname.includes('/calendars/primary') && r.methode !== 'DELETE'), 'principal et suppression interdits');
  });

  await testAsync('Google Agenda fiche : historique limité à 100, plus récent en premier', async c => {
    const evenement = preparerFicheRendezVous(c);
    const precedents = Array.from({ length: 100 }, (_, i) => ({ id: `ancien-fictif-${i}`, enregistre_le: '2029-01-01T00:00:00Z', ancien: {} }));
    c.localStorage.setItem('cap_rdv_historique_v1', JSON.stringify(precedents));
    const agenda = c.agenda();
    await agenda.modifierRendezVous(evenement.id, { lieu: 'Lieu modifié FICTIF' });
    const historique = agenda.lireHistorique();
    attendreEgal(historique.length, 100, 'plafond de versions');
    attendreEgal(historique[0].ancien, ancienRendezVous(evenement), 'nouvelle sauvegarde première');
    attendreEgal(historique[0].id, evenement.id, 'nouvelle sauvegarde identifiée');
    attendreEgal(historique.slice(1), precedents.slice(0, 99), 'ordre ancien conservé, plus ancien écarté');
  });

  for (const panne of ['écriture refusée', 'JSON illisible', 'objet au lieu de liste']) {
    await testAsync(`Google Agenda fiche : historique ${panne} bloque le PATCH`, async c => {
      const evenement = preparerFicheRendezVous(c);
      const brut = panne === 'JSON illisible' ? '{illisible FICTIF' : panne === 'objet au lieu de liste' ? '{}' : '[]';
      c.localStorage.setItem('cap_rdv_historique_v1', brut);
      const cache = JSON.stringify({ rendezvous: [{ id: evenement.id, titre: 'Cache FICTIF', date: '2030-01-10' }] });
      c.localStorage.setItem('cap_google_rendezvous_v1', cache);
      const enregistrer = c.localStorage.setItem;
      if (panne === 'écriture refusée') c.localStorage.setItem = (cle, valeur) => {
        if (cle === 'cap_rdv_historique_v1') throw new Error('Quota FICTIF');
        return enregistrer(cle, valeur);
      };
      await attendreRejet(() => c.agenda().modifierRendezVous(evenement.id, { titre: 'Refusé FICTIF' }),
        'Impossible de sauvegarder l’ancienne version sur ce téléphone. Le rendez-vous n’a pas été modifié.');
      attendre(c.requetes.some(r => r.methode === 'GET' && r.url.pathname.endsWith('/events/rdv-fictif')), 'ancienne version relue');
      attendre(!c.requetes.some(r => r.methode === 'PATCH'), 'aucun PATCH sans sauvegarde');
      attendreEgal(c.localStorage.getItem('cap_rdv_historique_v1'), brut, 'historique original intact');
      attendreEgal(c.localStorage.getItem('cap_google_rendezvous_v1'), cache, 'cache intact');
    });
  }

  for (const identite of [{ summary: 'Autre agenda FICTIF', primary: false },
    { summary: REGLAGES_GOOGLE.nom_agenda, primary: true }]) {
    await testAsync(`Google Agenda fiche : identité agenda refusée ${identite.primary ? 'principal' : 'mauvais nom'}`, async c => {
      const evenement = preparerFicheRendezVous(c);
      c.repondre = async r => {
        attendreEgal(r.methode, 'GET', 'lecture seulement');
        attendreEgal(r.url.pathname, '/calendar/v3/calendars/agenda-fictif', 'aucun accès événement avant identité');
        return reponseGoogle({ id: c.agendaModifiable, ...identite });
      };
      await attendreRejet(() => c.agenda().modifierRendezVous(evenement.id, { titre: 'Refusé FICTIF' }), 'FICTIF');
      attendre(c.requetes.length > 0 && c.requetes.every(r => !r.url.pathname.includes('/events')), 'refus avant GET événement');
      attendreEgal(c.localStorage.getItem('cap_rdv_historique_v1'), null, 'aucun historique créé');
    });
  }

  await testAsync('Google Agenda fiche : PATCH horaire Europe Paris, description et rappels popup', async c => {
    const evenement = preparerFicheRendezVous(c);
    const changements = { titre: 'Titre modifié FICTIF', date: '2030-07-12', heure: '14:30', heure_fin: '15:45',
      lieu: 'Studio FICTIF', notes: 'Nouvelles notes FICTIF\nDeuxième ligne', telephone: '02 00 00 00 00',
      mail: 'nouveau.fictif@example.com', rappels: [0, 60, 1440, 10080, 40320] };
    const description = 'Nouvelles notes FICTIF\nDeuxième ligne\nTéléphone : 02 00 00 00 00\nMail : nouveau.fictif@example.com';
    const resultat = await c.agenda().modifierRendezVous(evenement.id, changements);
    attendreEgal(c.requetes.find(r => r.methode === 'PATCH').corps, {
      summary: changements.titre, location: changements.lieu, description,
      start: { dateTime: '2030-07-12T14:30:00', timeZone: 'Europe/Paris' },
      end: { dateTime: '2030-07-12T15:45:00', timeZone: 'Europe/Paris' },
      reminders: { useDefault: false, overrides: changements.rappels.map(minutes => ({ method: 'popup', minutes })) }
    }, 'corps exact sans champs supplémentaires');
    attendreEgal(resultat, { id: evenement.id, titre: changements.titre, date: changements.date, heure: changements.heure,
      heure_fin: changements.heure_fin, journee_entiere: false, lieu: changements.lieu, notes: changements.notes,
      telephone: changements.telephone, mail: changements.mail, rappels: changements.rappels, description }, 'retour complet après PATCH');
  });

  await testAsync('Google Agenda fiche : suppression des coordonnées et des rappels sans DELETE', async c => {
    const evenement = preparerFicheRendezVous(c);
    const resultat = await c.agenda().modifierRendezVous(evenement.id, { telephone: '', mail: '', rappels: [] });
    attendreEgal(c.requetes.find(r => r.methode === 'PATCH').corps,
      { description: 'Préparation FICTIF', reminders: { useDefault: false, overrides: [] } }, 'vidage limité aux champs');
    attendreEgal([resultat.telephone, resultat.mail, resultat.rappels], ['', '', []], 'coordonnées et rappels vides');
  });

  await testAsync('Google Agenda fiche : heure seule de journée entière ne change aucune date', async c => {
    const evenement = preparerFicheRendezVous(c, { start: { date: '2030-01-10' }, end: { date: '2030-01-13' },
      description: '09h05 – Notes FICTIF\nTéléphone : 01 00 00 00 00\nMail : fictif@example.com' });
    const resultat = await c.agenda().modifierRendezVous(evenement.id, { heure: '14:30' });
    const description = '14h30 – Notes FICTIF\nTéléphone : 01 00 00 00 00\nMail : fictif@example.com';
    attendreEgal(c.requetes.find(r => r.methode === 'PATCH').corps, { description }, 'uniquement la description');
    attendreEgal(resultat, { id: evenement.id, titre: evenement.summary, date: '2030-01-10', heure: '14:30', heure_fin: '',
      journee_entiere: true, lieu: evenement.location, notes: 'Notes FICTIF', telephone: '01 00 00 00 00',
      mail: 'fictif@example.com', rappels: [60], description }, 'journée entière toujours entière');
  });

  await testAsync('Google Agenda fiche : déplacement journée entière préserve durée multijour', async c => {
    const evenement = preparerFicheRendezVous(c, { start: { date: '2030-01-10' }, end: { date: '2030-01-13' },
      description: '09h05 – Notes FICTIF' });
    const resultat = await c.agenda().modifierRendezVous(evenement.id, { date: '2030-03-30' });
    attendreEgal(c.requetes.find(r => r.methode === 'PATCH').corps,
      { start: { date: '2030-03-30' }, end: { date: '2030-04-02' } }, 'trois jours civils, fin exclusive');
    attendreEgal([resultat.date, resultat.heure, resultat.journee_entiere], ['2030-03-30', '09:05', true], 'horaire descriptif conservé');
  });

  for (const etat of ['hors ligne', 'déconnecté']) {
    await testAsync(`Google Agenda fiche : ${etat} refuse sans requête`, async c => {
      preparerFicheRendezVous(c);
      if (etat === 'hors ligne') c.navigator.onLine = false;
      else c.googleConnexion.connecte = () => false;
      await attendreRejet(() => c.agenda().modifierRendezVous('rdv-fictif', { titre: 'Refusé FICTIF' }), 'connecté à Google');
      attendreEgal(c.requetes.length, 0, 'aucune requête');
      attendreEgal(c.localStorage.getItem('cap_rdv_historique_v1'), null, 'aucune sauvegarde inutile');
    });
  }

  const nouveauRdv = { titre: 'test notification FICTIF', date: '2030-01-10', heure: '11:45', heure_fin: '12:45',
    lieu: '', telephone: '', mail: '', notes: '', rappels: [10] };

  await testAsync('Google Agenda création : POST sur l’agenda FICTIF avec rappel popup', async c => {
    preparerFicheRendezVous(c);
    const repondre = c.repondre;
    let envoye = null;
    c.repondre = async r => {
      if (r.methode === 'POST') {
        attendreEgal(r.url.pathname, '/calendar/v3/calendars/agenda-fictif/events', 'agenda FICTIF seulement');
        envoye = r.corps;
        return reponseGoogle({ id: 'nouveau-fictif', ...r.corps,
          start: { dateTime: '2030-01-10T11:45:00+01:00' }, end: { dateTime: '2030-01-10T12:45:00+01:00' } });
      }
      return repondre(r);
    };
    const resultat = await c.agenda().creerRendezVous(nouveauRdv);
    attendre(envoye, 'aucun POST');
    attendreEgal(envoye.summary, 'test notification FICTIF', 'titre envoyé');
    attendreEgal(envoye.start, { dateTime: '2030-01-10T11:45:00', timeZone: 'Europe/Paris' }, 'début');
    attendreEgal(envoye.end, { dateTime: '2030-01-10T12:45:00', timeZone: 'Europe/Paris' }, 'fin');
    attendreEgal(envoye.reminders, { useDefault: false, overrides: [{ method: 'popup', minutes: 10 }] }, 'rappel');
    attendreEgal([resultat.id, resultat.date, resultat.heure, resultat.rappels], ['nouveau-fictif', '2030-01-10', '11:45', [10]], 'résultat');
    attendre(c.agenda().lireCache().some(rdv => rdv.id === 'nouveau-fictif'), 'cache mis à jour');
    attendre(c.requetes.every(r => !['DELETE', 'PATCH', 'PUT'].includes(r.methode)), 'aucune autre écriture');
  });

  for (const etat of ['hors ligne', 'déconnecté', 'principal', 'fin avant début']) {
    await testAsync(`Google Agenda création : refus ${etat} sans POST`, async c => {
      preparerFicheRendezVous(c);
      let champs = nouveauRdv;
      if (etat === 'hors ligne') c.navigator.onLine = false;
      if (etat === 'déconnecté') c.googleConnexion.connecte = () => false;
      if (etat === 'fin avant début') champs = { ...nouveauRdv, heure_fin: '11:00' };
      if (etat === 'principal') {
        c.repondre = async r => {
          attendreEgal(r.methode, 'GET', 'lecture seulement');
          return reponseGoogle({ id: c.agendaModifiable, summary: REGLAGES_GOOGLE.nom_agenda, primary: true });
        };
      }
      await attendreRejet(() => c.agenda().creerRendezVous(champs), '');
      attendre(c.requetes.every(r => r.methode !== 'POST'), 'aucun POST');
    });
  }

  test('Compréhension : la phrase de Max donne un rendez-vous à 11h45 aujourd’hui', () => {
    const maintenant = new Date(2026, 9, 29, 10, 0);
    const rdv = comprendreDemande.rendezVous('Ajoute-moi un rendez-vous à 11h45 aujourd\'hui, intitulé test notification, avec un rappel dix minutes avant', maintenant);
    attendreEgal([rdv.titre, rdv.date, rdv.heure, rdv.heure_fin, rdv.rappels], ['test notification', '2026-10-29', '11:45', '12:45', [10]], 'brouillon');
  });

  test('Compréhension : dates, heures, rappels et refus', () => {
    const maintenant = new Date(2026, 9, 29, 10, 0);
    const cas = [
      ['rendez-vous demain à midi chez le dentiste FICTIF', '2026-10-30', '12:00', []],
      ['rdv le 12 novembre à 9 heures et demie, rappel une demi-heure avant', '2026-11-12', '09:30', [30]],
      ['rendez-vous lundi 14h garage FICTIF avec un rappel la veille', '2026-11-02', '14:00', [1440]],
      ['rendez-vous le 3/02 à 8h05', '2027-02-03', '08:05', []]
    ];
    for (const [phrase, date, heure, rappels] of cas) {
      const rdv = comprendreDemande.rendezVous(phrase, maintenant);
      attendreEgal([rdv.date, rdv.heure, rdv.rappels], [date, heure, rappels], phrase);
    }
    attendreEgal(comprendreDemande.rendezVous('acheter du pain FICTIF', maintenant), null, 'pas de rendez-vous');
    attendreEgal(comprendreDemande.rendezVous('reporte le rendez-vous à demain', maintenant), null, 'report exclu');
    attendreEgal(comprendreDemande.report('Reporte ça à demain'), { cible: 'tache' }, 'report tâche');
    attendreEgal(comprendreDemande.report('décale le rendez-vous à demain'), { cible: 'rendez-vous' }, 'report rdv');
    attendreEgal(comprendreDemande.report('reporte à après-demain'), null, 'après-demain non géré');
  });

  const modificationsRdvInvalides = [
    ['titre vide', { titre: '' }, 'titre'], ['titre blanc', { titre: '   ' }, 'titre'],
    ['date impossible', { date: '2030-02-30' }, 'date'], ['date mois invalide', { date: '2030-13-01' }, 'date'],
    ['date format court', { date: '2030-1-01' }, 'date'], ['date vide', { date: '' }, 'date'],
    ['mail invalide', { mail: 'adresse-fictive' }, 'mail'],
    ['mail multiligne', { mail: 'fictif@example.com\nCopie : autre.fictif@example.com' }, 'mail'],
    ['téléphone multiligne', { telephone: '01 00 00 00 00\nMail : fictif@example.com' }, 'ligne'],
    ['heure invalide', { heure: '24:00' }, 'heure'], ['minutes invalides', { heure: '12:60' }, 'heure'],
    ['heure format court', { heure: '9:05' }, 'heure'], ['fin invalide', { heure_fin: '25:00' }, 'heure'],
    ['rappels négatifs', { rappels: [-1] }, 'rappels'], ['rappels au-delà limite', { rappels: [40321] }, 'rappels'],
    ['rappels décimaux', { rappels: [0.5] }, 'rappels'], ['rappels texte', { rappels: ['60'] }, 'rappels'],
    ['rappels pas liste', { rappels: 60 }, 'rappels'], ['six rappels', { rappels: [0, 1, 2, 3, 4, 5] }, 'rappels'],
    ['champ interdit', { summary: 'FICTIF' }, 'autorisée'], ['titre non texte', { titre: 42 }, 'invalide']
  ];
  for (const [nom, changements, message] of modificationsRdvInvalides) {
    await testAsync(`Google Agenda fiche : validation ${nom} sans requête`, async c => {
      preparerFicheRendezVous(c);
      await attendreRejet(() => c.agenda().modifierRendezVous('rdv-fictif', changements), message);
      attendreEgal(c.requetes.length, 0, 'validation avant tout accès Google');
      attendreEgal(c.localStorage.getItem('cap_rdv_historique_v1'), null, 'aucune sauvegarde de modification invalide');
    });
  }

  for (const changements of [{ heure: '' }, { heure_fin: '' }, { heure: '11:00', heure_fin: '11:00' },
    { heure: '12:00', heure_fin: '11:00' }]) {
    await testAsync(`Google Agenda fiche : plage horaire incohérente ${JSON.stringify(changements)}`, async c => {
      preparerFicheRendezVous(c);
      await attendreRejet(() => c.agenda().modifierRendezVous('rdv-fictif', changements), 'heure');
      attendre(c.requetes.every(r => r.methode === 'GET'), 'aucune écriture avec plage invalide');
      attendreEgal(c.localStorage.getItem('cap_rdv_historique_v1'), null, 'pas de sauvegarde inutile');
    });
  }

  await testAsync('Google Agenda fiche : heure de fin interdite pour une journée entière', async c => {
    preparerFicheRendezVous(c, { start: { date: '2030-01-10' }, end: { date: '2030-01-11' } });
    await attendreRejet(() => c.agenda().modifierRendezVous('rdv-fictif', { heure_fin: '15:00' }), 'journée entière');
    attendre(c.requetes.every(r => r.methode === 'GET'), 'aucun PATCH');
    attendreEgal(c.localStorage.getItem('cap_rdv_historique_v1'), null, 'historique inchangé');
  });

  for (const statut of [412, 500]) {
    await testAsync(`Google Agenda fiche : erreur PATCH ${statut} garde ancienne version et cache intact`, async c => {
      const evenement = preparerFicheRendezVous(c);
      const agenda = c.agenda();
      await agenda.prochainsRendezVous();
      const cache = c.localStorage.getItem('cap_google_rendezvous_v1');
      const repondre = c.repondre;
      c.repondre = async r => r.methode === 'PATCH' ? reponseGoogle({ erreur: 'Échec FICTIF' }, statut) : repondre(r);
      await attendreRejet(() => agenda.modifierRendezVous(evenement.id, { titre: 'Échec FICTIF' }), String(statut));
      attendreEgal(agenda.lireHistorique().length, 1, 'ancienne version toujours disponible');
      attendreEgal(agenda.lireHistorique()[0].ancien, ancienRendezVous(evenement), 'sauvegarde complète après erreur');
      attendreEgal(c.localStorage.getItem('cap_google_rendezvous_v1'), cache, 'cache strictement inchangé');
      attendreEgal(c.requetes.filter(r => r.methode === 'PATCH').length, 1, 'pas de répétition de modification');
    });
  }

  await testAsync('Google et service worker : aucune interception ni cache hors origine', async c => {
    const rappels = new Map();
    const origine = location.origin;
    const fauxSelf = { registration: { scope: `${origine}/src/` }, location: { origin: origine },
      addEventListener: (nom, rappel) => rappels.set(nom, rappel) };
    let cachesOuverts = 0;
    objetIsole(SOURCE_SERVICE_WORKER, 'undefined', { self: fauxSelf,
      caches: { open: async () => { cachesOuverts++; throw new Error('Cache inattendu'); } }, fetch: c.fetch });
    const intercepter = rappels.get('fetch');
    attendre(typeof intercepter === 'function', 'gestionnaire fetch absent');
    let interceptions = 0;
    for (const url of ['https://www.googleapis.com/calendar/v3/calendars',
      'https://sheets.googleapis.com/v4/spreadsheets', `${origine}/hors-precache-fictif`]) {
      intercepter({ request: new Request(url), respondWith: () => interceptions++ });
    }
    intercepter({ request: new Request(`${origine}/src/app.js`, { method: 'POST', body: 'FICTIF' }), respondWith: () => interceptions++ });
    attendreEgal(interceptions, 0, 'requêtes Google ou non précachées ignorées');
    attendreEgal(cachesOuverts, 0, 'cache non ouvert');
    attendreEgal(c.requetes.length, 0, 'aucun fetch du service worker');
  });

  async function viderMicrotaches() {
    for (let i = 0; i < 40; i++) await Promise.resolve();
  }

  function preparerConnexion(c, duree = 3600000) {
    c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
    c.localStorage.setItem('cap_google_jeton_v1', JSON.stringify({
      jeton: 'jeton-fictif', expiration: c.maintenant + duree
    }));
    c.googleConnexion = c.connexion();
  }

  function interfaceIsolee(c, { largeur = 1024, hauteur = 768, avant = () => {} } = {}) {
    const cadre = document.createElement('iframe');
    cadre.style.cssText = `position:fixed;left:0;top:0;width:${largeur}px;height:${hauteur}px;border:0;`;
    document.body.append(cadre);
    c.cadres.push(cadre);
    const doc = cadre.contentDocument;
    const modele = new DOMParser().parseFromString(SOURCE_HTML, 'text/html');
    modele.querySelectorAll('script').forEach(script => script.remove());
    doc.documentElement.lang = 'fr';
    doc.body.replaceChildren(...Array.from(modele.body.childNodes, noeud => doc.importNode(noeud, true)));
    const style = doc.createElement('style');
    style.textContent = SOURCE_STYLE;
    doc.head.append(style);
    const vibrations = [];
    c.navigator.vibrate = duree => { vibrations.push(duree); return true; };
    let cache = false;
    Object.defineProperty(doc, 'hidden', { configurable: true, get: () => cache });
    const dicteeSimulee = { disponible: () => false, enCours: () => false };
    const ui = {
      doc, cadre, vibrations, dictee: dicteeSimulee,
      parId: id => doc.getElementById(id),
      visibilite(masque) {
        cache = masque;
        doc.dispatchEvent(new Event('visibilitychange'));
      },
      actualiser: () => c.window.dispatchEvent(new Event('cap-google-etat'))
    };
    avant(ui);
    const agendaSimule = { prochainsRendezVous: async () => [], lireCache: () => c.agenda().lireCache() };
    const etapesIsolees = JSON.parse(JSON.stringify(ETAPES_PAR_DEFAUT));
    ui.listesChoix = objetIsole(SOURCE_LISTES_CHOIX, 'listesChoix', {
      localStorage: c.localStorage, window: c.window, TACHES: c.TACHES, ETAPES_PAR_DEFAUT: etapesIsolees, dateDuJour
    });
    ui.choixDates = objetIsole(SOURCE_CHOIX_DATES, 'choixDates', {
      document: doc, Date: c.Date, comprendreDemande, dictee: ui.dictee
    });
    ui.fermetureFenetres = objetIsole(SOURCE_FERMETURE_FENETRES, 'fermetureFenetres', {
      document: doc, setTimeout: c.setTimeout, clearTimeout: c.clearTimeout, CSS, Event
    });
    ui.fenetresListes = objetIsole(SOURCE_FENETRES_LISTES, 'fenetresListes', {
      document: doc, listesChoix: ui.listesChoix, setTimeout: c.setTimeout, clearTimeout: c.clearTimeout,
      fermetureFenetres: ui.fermetureFenetres
    });
    ui.etapesParDefaut = etapesIsolees;
    ui.journalActions = objetIsole(SOURCE_JOURNAL_ACTIONS, 'journalActions', { localStorage: c.localStorage, googleSheets: undefined });
    ui.classer = (id, categorie, sousCategorie) => {
      const tache = c.TACHES.find(item => item.id === id);
      const ancienne = { categorie: tache.categorie, sous_categorie: tache.sous_categorie };
      tache.categorie = categorie;
      tache.sous_categorie = sousCategorie;
      return ancienne;
    };
    ui.tuiles = objetIsole(SOURCE_TUILES, 'tuiles', { document: doc, navigator: c.navigator, setTimeout, clearTimeout });
    ui.modeTrier = objetIsole(SOURCE_MODE_TRIER, 'modeTrier', {
      document: doc, TACHES: c.TACHES, listesChoix: ui.listesChoix, classer: ui.classer, dictee: ui.dictee,
      journalActions: ui.journalActions, setTimeout: c.setTimeout, clearTimeout: c.clearTimeout
    });
    ui.sauvegardes = [];
    ui.sauvegardeDrive = {
      etat: () => ({ derniere: '', dossier: '', nombre: 0 }),
      sauvegarder: async () => { ui.sauvegardes.push(1); return { nom: 'Cap – FICTIF – sauvegarde', nombre: 1, enTrop: 0 }; },
      verifierAutomatique: async () => null, aFaire: () => false
    };
    objetIsole(SOURCE_APP, 'undefined', {
      document: doc, window: c.window, navigator: c.navigator, Date: c.Date,
      setInterval: c.setInterval, setTimeout: c.setTimeout, clearTimeout: c.clearTimeout,
      googleConnexion: c.googleConnexion, synchronisation: c.synchronisation,
      recherche,
      ficheRendezVous: objetIsole(SOURCE_FICHE_RDV, 'ficheRendezVous', {
        document: doc, navigator: c.navigator, googleConnexion: c.googleConnexion, googleAgenda: agendaSimule
      }),
      journalActions: ui.journalActions,
      tuiles: ui.tuiles, modeTrier: ui.modeTrier, sauvegardeDrive: ui.sauvegardeDrive, REGLAGES_GOOGLE,
      googleAgenda: agendaSimule,
      TACHES: c.TACHES, INFO_CHARGEMENT: '', ETAPES_PAR_DEFAUT: etapesIsolees,
      listesChoix: ui.listesChoix, choixDates: ui.choixDates, fenetresListes: ui.fenetresListes, fermetureFenetres: ui.fermetureFenetres,
      avancementTache: () => ({ faites: 0, total: 0 }), avancementSousCategorie: () => 0,
      joursRestants, dateDuJour, ajouterEtape, abandonner, remettre, cocher,
      reporterADemain, changerEcheance, creerAvecEtapesParDefaut, creerTache, traiterDemande, composerTexte,
      preferencesClavier, PHRASES_CLAVIER, dictee: dicteeSimulee
    });
    return ui;
  }

  function preparerInterface(c, options) {
    c.googleConnexion = c.connexion();
    c.synchronisation = c.sync(fauxSheetsSync(c, c.TACHES));
    return interfaceIsolee(c, options);
  }

  function glisser(ui, cible, x, y, finX, finY) {
    for (const [type, touches, changedTouches] of [
      ['touchstart', [{ clientX: x, clientY: y }], []],
      ['touchend', [], [{ clientX: finX, clientY: finY }]]
    ]) {
      const evenement = new Event(type, { bubbles: true });
      Object.defineProperties(evenement, { touches: { value: touches }, changedTouches: { value: changedTouches } });
      cible.dispatchEvent(evenement);
    }
  }

  for (const code of ['interaction_required', 'login_required', 'consent_required', 'account_selection_required']) {
    await testAsync(`Google silencieux : ${code} demande un geste et affiche l’alerte`, async c => {
      c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
      const connexion = c.connexion();
      attendre(connexion.tenterSilencieux(true), 'tentative silencieuse absente');
      const etat = c.redirections[0].searchParams.get('state');
      attendreEgal(c.localStorage.getItem('cap_google_etat_silencieux_v1'), etat, 'marqueur lié au state');
      c.location.hash = `#error=${code}&state=${etat}`;
      const ui = preparerInterface(c);
      attendre(c.googleConnexion.besoinGeste(), 'accord non demandé');
      attendreEgal(c.localStorage.getItem('cap_google_besoin_geste_v1'), 'oui', 'geste persistant');
      attendre(!ui.parId('alerte-google').hidden, 'alerte cachée');
      attendre(ui.parId('texte-alerte-google').textContent.includes('Google demande ton accord'), 'message d’accord absent');
      attendreEgal(c.localStorage.getItem('cap_google_etat_silencieux_v1'), null, 'marqueur consommé');
      attendreEgal(c.redirections.length, 1, 'aucune boucle silencieuse');
      c.maintenant += 700000;
      attendre(!c.googleConnexion.tenterSilencieux(true), 'nouvelle tentative malgré le geste requis');
      const recharge = c.connexion();
      attendre(recharge.besoinGeste(), 'geste perdu au rechargement');
    });
  }

  await testAsync('Google silencieux : access_denied reste un refus sans boucle', async c => {
    c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
    c.connexion().seConnecter({ silencieux: true });
    const etat = c.redirections[0].searchParams.get('state');
    c.location.hash = `#error=access_denied&state=${etat}`;
    const ui = preparerInterface(c);
    attendre(!c.googleConnexion.connecte(), 'refus accepté');
    attendre(!c.googleConnexion.besoinGeste(), 'refus confondu avec interaction requise');
    attendre(c.googleConnexion.message().includes('pas été autorisée'), 'message de refus absent');
    attendre(!ui.parId('alerte-google').hidden, 'refus non affiché');
    attendre(!c.googleConnexion.tenterSilencieux(true), 'boucle après refus');
    attendreEgal(c.localStorage.getItem('cap_google_jeton_v1'), null, 'jeton après refus');
  });

  await testAsync('Google silencieux : marqueur seul et mauvais state ne contournent pas la sécurité', async c => {
    c.localStorage.setItem('cap_google_etat_v1', 'attendu-fictif');
    c.localStorage.setItem('cap_google_etat_silencieux_v1', 'intrus-fictif');
    c.location.hash = '#error=interaction_required&state=intrus-fictif';
    const ui = preparerInterface(c);
    attendre(c.googleConnexion.message().includes('sécurité'), 'mauvais state accepté');
    attendre(!c.googleConnexion.besoinGeste(), 'erreur de sécurité transformée en demande d’accord');
    attendre(!c.googleConnexion.connecte(), 'connexion acceptée');
    attendre(!ui.parId('alerte-google').hidden, 'erreur non affichée');
    attendreEgal(c.location.hash, '', 'fragment nettoyé');
    attendreEgal(c.redirections.length, 0, 'aucune redirection après erreur');
  });

  await testAsync('Google silencieux : erreur interactive non liée au marqueur reste un refus', async c => {
    c.localStorage.setItem('cap_google_etat_v1', 'attendu-fictif');
    c.localStorage.setItem('cap_google_etat_silencieux_v1', 'autre-fictif');
    c.location.hash = '#error=consent_required&state=attendu-fictif';
    const connexion = c.connexion();
    attendre(!connexion.besoinGeste(), 'marqueur sans rapport accepté');
    attendre(connexion.message().includes('pas été autorisée'), 'refus absent');
  });

  await testAsync('Google silencieux : throttle dix minutes, prompt none et horodatage', async c => {
    c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
    const connexion = c.connexion();
    attendre(connexion.tenterSilencieux(true), 'première tentative absente');
    attendreEgal(c.redirections[0].searchParams.get('prompt'), 'none', 'prompt silencieux');
    attendreEgal(Number(c.localStorage.getItem('cap_google_silencieux_v1')), c.maintenant, 'date de tentative');
    attendre(!connexion.tenterSilencieux(true), 'tentative immédiate répétée');
    c.maintenant += 600000;
    attendre(!connexion.tenterSilencieux(true), 'tentative à dix minutes exactement');
    c.maintenant++;
    attendre(connexion.tenterSilencieux(true), 'pas de reprise après dix minutes');
    attendreEgal(c.redirections.length, 2, 'nombre de redirections');
    attendre(c.redirections[0].searchParams.get('state') !== c.redirections[1].searchParams.get('state'), 'state réutilisé');
  });

  for (const cas of ['jamais connecté', 'hors ligne', 'jeton supérieur à cinq minutes', 'conditions refusées']) {
    await testAsync(`Google silencieux : aucune tentative si ${cas}`, async c => {
      if (cas !== 'jamais connecté') c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
      if (cas === 'hors ligne') c.navigator.onLine = false;
      if (cas === 'jeton supérieur à cinq minutes') preparerConnexion(c, 300001);
      const connexion = c.connexion();
      attendre(!connexion.tenterSilencieux(cas !== 'conditions refusées'), 'tentative indésirable');
      attendreEgal(c.redirections.length, 0, 'redirection indésirable');
      attendreEgal(c.localStorage.getItem('cap_google_silencieux_v1'), null, 'throttle consommé sans tentative');
    });
  }

  for (const cas of ['dialogue', 'dictée', 'texte', 'page cachée']) {
    await testAsync(`Interface Google : aucune reconnexion silencieuse pendant ${cas}`, async c => {
      c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
      const ui = preparerInterface(c, { avant(ui) {
        if (cas === 'dialogue') ui.parId('clavier').showModal();
        if (cas === 'dictée') ui.dictee.enCours = () => true;
        if (cas === 'texte') ui.parId('saisie-demande').value = 'Demande FICTIF en cours';
        if (cas === 'page cachée') ui.visibilite(true);
      } });
      attendreEgal(c.redirections.length, 0, 'redirection au démarrage');
      if (cas !== 'page cachée') ui.visibilite(false);
      attendreEgal(c.redirections.length, 0, 'redirection au retour visible');
      if (cas === 'dialogue') ui.parId('clavier').close();
      if (cas === 'dictée') ui.dictee.enCours = () => false;
      if (cas === 'texte') ui.parId('saisie-demande').value = '';
      ui.visibilite(false);
      attendreEgal(c.redirections.length, 1, 'reprise une fois l’interface libre');
      attendreEgal(c.redirections[0].searchParams.get('prompt'), 'none', 'reprise silencieuse');
    });
  }

  await testAsync('Interface Google : expiration, nombre en attente et une seule vibration', async c => {
    preparerConnexion(c, 120000);
    c.localStorage.setItem('cap_google_silencieux_v1', String(c.maintenant));
    const sheets = fauxSheetsSync(c, c.TACHES);
    c.synchronisation = c.sync(sheets);
    const ui = interfaceIsolee(c);
    await viderMicrotaches();
    attendre(ui.parId('alerte-google').hidden, 'alerte avant expiration');
    c.navigator.onLine = false;
    c.synchronisation.signaler(c.TACHES.slice(0, 2).map(t => t.id));
    const expiration = c.googleConnexion.expiration();
    attendreEgal(expiration, c.maintenant + 120000, 'expiration exposée');
    const minuterie = Array.from(c.delais.values()).find(delai => delai.delai === 60001);
    attendre(minuterie, 'minuteur d’expiration absent');
    c.maintenant = expiration - 59999;
    minuterie.rappel();
    attendre(!ui.parId('alerte-google').hidden, 'alerte après expiration');
    attendre(ui.parId('texte-alerte-google').textContent.includes('2 tâches attendent'), 'mauvais nombre dans l’alerte');
    attendre(ui.parId('texte-etat-google').textContent.includes('2 en attente'), 'nombre hors ligne absent');
    ui.actualiser();
    ui.visibilite(false);
    attendreEgal(ui.vibrations, [200], 'vibration répétée');
    attendreEgal(lireFileGoogle(c).length, 2, 'file perdue à l’expiration');
    ui.parId('redonner-acces-google').click();
    attendreEgal(c.redirections.length, 1, 'bouton sans redirection');
    attendre(!c.redirections[0].searchParams.has('prompt'), 'bouton encore silencieux');
    attendreEgal(c.localStorage.getItem('cap_google_etat_silencieux_v1'), null, 'marqueur silencieux après clic');
  });

  await testAsync('Interface Google : retour OAuth valide démarre et envoie automatiquement la file', async c => {
    c.localStorage.setItem('cap_google_etat_v1', 'retour-fictif');
    c.localStorage.setItem('cap_google_etat_silencieux_v1', 'retour-fictif');
    c.localStorage.setItem('cap_google_besoin_geste_v1', 'oui');
    c.localStorage.setItem('cap_google_file_v1', JSON.stringify([c.TACHES[0].id]));
    c.location.hash = '#access_token=jeton-fictif&expires_in=3600&token_type=Bearer&state=retour-fictif';
    c.googleConnexion = c.connexion();
    const sheets = fauxSheetsSync(c, c.TACHES);
    c.synchronisation = c.sync(sheets);
    const ui = interfaceIsolee(c);
    attendre(ui.parId('synchroniser-maintenant').disabled, 'bouton actif pendant le démarrage');
    await viderMicrotaches();
    attendreEgal(sheets.envois.flat().map(t => t.id), [c.TACHES[0].id], 'file non envoyée par le démarrage de l’app');
    attendreEgal(lireFileGoogle(c), [], 'file non acquittée');
    attendre(!c.googleConnexion.besoinGeste(), 'geste non réinitialisé');
    attendre(ui.parId('alerte-google').hidden, 'alerte après retour valide');
    attendreEgal(c.redirections.length, 0, 'redirection supplémentaire');
    attendreEgal(c.localStorage.getItem('cap_google_etat_silencieux_v1'), null, 'marqueur non consommé');
  });

  await testAsync('Interface Google : 403 retire le jeton, affiche l’alerte et garde la file', async c => {
    preparerConnexion(c);
    const sheets = fauxSheetsSync(c, c.TACHES);
    c.synchronisation = c.sync(sheets);
    const ui = interfaceIsolee(c);
    await viderMicrotaches();
    c.navigator.onLine = false;
    c.synchronisation.signaler([c.TACHES[0].id, c.TACHES[1].id]);
    c.navigator.onLine = true;
    c.repondre = async () => reponseGoogle({}, 403);
    sheets.ecrireTaches = async () => c.googleConnexion.appeler('https://sheets.googleapis.com/v4/spreadsheets/tableau-fictif');
    let evenements = 0;
    c.window.addEventListener('cap-google-deconnecte', () => evenements++);
    ui.parId('basculer-vue').click();
    ui.parId('synchroniser-maintenant').click();
    await viderMicrotaches();
    attendreEgal(evenements, 1, 'événement de déconnexion absent');
    attendreEgal(c.localStorage.getItem('cap_google_jeton_v1'), null, 'jeton non retiré');
    attendreEgal(lireFileGoogle(c), c.TACHES.slice(0, 2).map(t => t.id), 'file modifiée après 403');
    attendre(!ui.parId('alerte-google').hidden, 'alerte absente');
    attendre(ui.parId('texte-alerte-google').textContent.includes('403'), 'raison 403 absente');
    attendre(ui.parId('texte-alerte-google').textContent.includes('2 tâches attendent'), 'nombre incorrect');
    attendre(!c.synchronisation.informations().pret, 'sync encore prête après déconnexion');
    attendreEgal(c.localStorage.getItem('cap_google_dernier_envoi_v1'), null, 'succès inventé après 403');
    attendreEgal(ui.vibrations, [200], 'vibration de déconnexion');
  });

  await testAsync('Interface Google : synchronisation manuelle, verrou, heure du dernier succès', async c => {
    preparerConnexion(c);
    const sheets = fauxSheetsSync(c, c.TACHES);
    c.synchronisation = c.sync(sheets);
    const ui = interfaceIsolee(c);
    await viderMicrotaches();
    attendreEgal(c.synchronisation.informations(), {
      nombre: 0, pret: true, enCours: false, dernierEnvoi: 0, erreur: '', illisibles: 0
    }, 'informations au repos');
    c.navigator.onLine = false;
    c.synchronisation.signaler([c.TACHES[0].id]);
    c.navigator.onLine = true;
    let terminer;
    sheets.ecrireTaches = taches => new Promise(resolve => {
      terminer = () => resolve(taches.map(t => t.id));
    });
    ui.parId('basculer-vue').click();
    const bouton = ui.parId('synchroniser-maintenant');
    bouton.click();
    attendre(c.synchronisation.informations().enCours, 'verrou absent');
    attendre(bouton.disabled && bouton.textContent === 'Envoi…', 'bouton non désactivé');
    await viderMicrotaches();
    attendre(typeof terminer === 'function', 'envoi non lancé');
    attendreEgal(c.localStorage.getItem('cap_google_dernier_envoi_v1'), null, 'succès avant réponse');
    c.maintenant += 45000;
    terminer();
    await viderMicrotaches();
    attendreEgal(Number(c.localStorage.getItem('cap_google_dernier_envoi_v1')), c.maintenant, 'heure de succès non sauvegardée');
    attendreEgal(c.synchronisation.informations().dernierEnvoi, c.maintenant, 'heure non exposée');
    const heure = new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(new Date(c.maintenant));
    attendreEgal(ui.parId('dernier-envoi').textContent, `Dernier envoi réussi : ${heure}`, 'heure affichée');
    attendre(!bouton.disabled, 'bouton bloqué après succès');
    attendreEgal(ui.parId('texte-etat-google').textContent, 'Tout est envoyé', 'état final');
  });

  await testAsync('Google sync : reprise périodique à soixante secondes, sans réseau hors ligne', async c => {
    preparerConnexion(c);
    const sheets = fauxSheetsSync(c, c.TACHES);
    const sync = c.sync(sheets);
    await sync.demarrer();
    c.navigator.onLine = false;
    sync.signaler([c.TACHES[0].id]);
    const rappels = c.intervalles.filter(intervalle => intervalle.delai === 60000);
    attendreEgal(rappels.length, 1, 'intervalle de reprise');
    rappels[0].rappel();
    await viderMicrotaches();
    attendreEgal(sheets.envois.length, 0, 'envoi hors ligne');
    c.navigator.onLine = true;
    rappels[0].rappel();
    await viderMicrotaches();
    attendreEgal(sheets.envois.flat().map(t => t.id), [c.TACHES[0].id], 'reprise périodique absente');
    attendreEgal(lireFileGoogle(c), [], 'file non acquittée');
  });

  await testAsync('Interface Google : reprise de la file au retour visible seulement', async c => {
    preparerConnexion(c);
    const sheets = fauxSheetsSync(c, c.TACHES);
    c.synchronisation = c.sync(sheets);
    const ui = interfaceIsolee(c);
    await viderMicrotaches();
    c.navigator.onLine = false;
    c.synchronisation.signaler([c.TACHES[0].id]);
    c.navigator.onLine = true;
    ui.visibilite(true);
    await viderMicrotaches();
    attendreEgal(sheets.envois.length, 0, 'reprise lors du masquage');
    ui.visibilite(false);
    await viderMicrotaches();
    attendreEgal(sheets.envois.flat().map(t => t.id), [c.TACHES[0].id], 'reprise au retour visible absente');
    attendreEgal(lireFileGoogle(c), [], 'file non acquittée');
  });

  await testAsync('Interface Google : première connexion, alerte vide et aucun renouvellement par minuteur', async c => {
    const ui = preparerInterface(c);
    attendre(ui.parId('alerte-google').hidden, 'alerte avant toute connexion');
    attendre(!ui.parId('connexion-google').hidden, 'première connexion indisponible');
    c.googleConnexion.deconnecter();
    ui.actualiser();
    attendre(!ui.parId('alerte-google').hidden, 'alerte sans jeton absente');
    attendre(ui.parId('texte-alerte-google').textContent.includes('Rien n’est perdu.'), 'message pour file vide absent');
    attendre(ui.parId('connexion-google').hidden, 'première connexion encore affichée');
    attendre(ui.parId('synchroniser-maintenant').hidden, 'envoi proposé sans accès');
    const surveillance = c.intervalles.find(intervalle => intervalle.delai === 30000);
    attendre(surveillance, 'surveillance toutes les trente secondes absente');
    c.maintenant += 700000;
    surveillance.rappel();
    surveillance.rappel();
    attendreEgal(c.redirections.length, 0, 'renouvellement déclenché par un minuteur');
    attendreEgal(ui.vibrations, [200], 'vibration répétée avec une file vide');
    attendre(c.connexion().reconnexion(), 'connexion passée oubliée au rechargement');
  });

  await testAsync('Accueil : liste cachée et inerte, horloge et commandes visibles', async c => {
    const ui = preparerInterface(c);
    attendre(ui.parId('ecran-complet').hidden && ui.parId('ecran-complet').inert, 'liste initialement accessible');
    attendre(!ui.parId('accueil').hidden, 'accueil caché');
    attendreEgal(ui.parId('basculer-vue').getAttribute('aria-expanded'), 'false', 'état du bouton');
    for (const cible of [ui.doc.querySelector('header.horloge'), ui.doc.querySelector('footer.dictee'), ui.parId('microphone')]) {
      const rectangle = cible.getBoundingClientRect();
      attendre(rectangle.width > 0 && rectangle.height > 0, 'horloge ou commandes invisibles');
      attendre(rectangle.top >= 0 && rectangle.bottom <= ui.cadre.clientHeight + 1, 'horloge ou commandes hors écran');
    }
    attendre(ui.parId('date').textContent.length > 0, 'date vide');
    attendre(!ui.parId('heure'), 'heure encore affichée');
    const recherche = ui.parId('zone-recherche').getBoundingClientRect();
    const barre = ui.doc.querySelector('.barre-recherche').getBoundingClientRect();
    attendre(barre.bottom <= ui.doc.querySelector('footer.dictee').getBoundingClientRect().top + 1, 'barre de recherche pas au-dessus des boutons');
    attendre(recherche.top > ui.cadre.clientHeight / 2, 'barre de recherche pas en bas');
    attendre(ui.doc.querySelector('.choix-source').contains(ui.parId('source-recherche')), 'menu hors de la barre');
    ui.parId('basculer-vue').click();
    attendre(!ui.parId('ecran-complet').hidden && !ui.parId('ecran-complet').inert, 'vue complète non ouverte');
    attendre(ui.parId('accueil').hidden, 'accueil encore visible');
    attendreEgal(ui.parId('basculer-vue').getAttribute('aria-expanded'), 'true', 'état ouvert');
    ui.parId('basculer-vue').click();
    attendre(ui.parId('ecran-complet').hidden, 'retour accueil impossible');
  });

  await testAsync('Accueil : gestes haut, bas en haut et liste déjà défilée', async c => {
    const ui = preparerInterface(c);
    const ecran = ui.parId('ecran-complet');
    glisser(ui, ui.parId('accueil'), 100, 300, 100, 180);
    attendre(!ecran.hidden, 'geste haut sans ouverture');
    attendre(ecran.scrollHeight > ecran.clientHeight, 'liste non défilable pour le test');
    ecran.scrollTop = 80;
    glisser(ui, ecran, 100, 180, 100, 300);
    attendre(!ecran.hidden, 'geste bas ferme une liste défilée');
    ecran.scrollTop = 0;
    glisser(ui, ecran, 100, 180, 100, 300);
    attendre(ecran.hidden, 'geste bas en haut sans retour accueil');
  });

  await testAsync('Accueil : gestes horizontaux, courts et sur boutons ignorés', async c => {
    const ui = preparerInterface(c);
    const ecran = ui.parId('ecran-complet');
    glisser(ui, ui.parId('accueil'), 100, 300, 250, 220);
    attendre(ecran.hidden, 'geste horizontal ouvre la liste');
    glisser(ui, ui.parId('accueil'), 100, 300, 100, 250);
    attendre(ecran.hidden, 'geste trop court ouvre la liste');
    glisser(ui, ui.parId('basculer-vue'), 100, 300, 100, 180);
    attendre(ecran.hidden, 'geste sur bouton ouvre la liste');
    ui.parId('clavier').showModal();
    glisser(ui, ui.parId('accueil'), 100, 300, 100, 180);
    attendre(ecran.hidden, 'geste pendant dialogue ouvre la liste');
    ui.parId('clavier').close();
  });

  for (const [largeur, hauteur] of [[1024, 768], [360, 560]]) {
    await testAsync(`Présentation : tailles calculées et aucun débordement à ${largeur} × ${hauteur}`, async c => {
      const ui = preparerInterface(c, { largeur, hauteur });
      const style = noeud => ui.cadre.contentWindow.getComputedStyle(noeud);
      attendreEgal(parseFloat(style(ui.parId('date')).fontSize), 18.5, 'taille de la date modifiée');
      attendreEgal(style(ui.doc.querySelector('header.horloge')).textAlign, 'center', 'date non centrée');
      ui.parId('basculer-vue').click();
      const intitule = ui.doc.querySelector('#liste-taches .intitule');
      attendreEgal(parseFloat(style(intitule).fontSize), 18.7, 'taille de la liste');
      attendre(parseFloat(style(intitule).fontSize) > 17, 'liste non agrandie');
      attendre(ui.doc.documentElement.scrollWidth <= largeur, 'débordement horizontal du document');
      attendre(ui.doc.body.scrollWidth <= largeur, 'débordement horizontal du corps');
      const liste = ui.parId('ecran-complet');
      attendre(liste.scrollWidth <= liste.clientWidth, 'débordement horizontal de la liste');
      c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
      c.googleConnexion.deconnecter();
      c.localStorage.setItem('cap_google_file_v1', JSON.stringify(c.TACHES.map(t => t.id)));
      ui.actualiser();
      const alerte = ui.parId('alerte-google');
      attendre(!alerte.hidden, 'alerte non affichée pour contrôle de largeur');
      attendre(alerte.scrollWidth <= alerte.clientWidth, 'débordement de l’alerte');
      for (const cible of [alerte, ui.doc.querySelector('footer.dictee')]) {
        const rectangle = cible.getBoundingClientRect();
        attendre(rectangle.left >= 0 && rectangle.right <= largeur + 1, 'élément hors largeur disponible');
      }
    });
  }

  test('Recherche : normalisation des accents et de la casse', () => {
    attendreEgal(recherche.normaliser('Été À ÇÔTÉ e\u0301'), 'ete a cote e', 'normalisation');
    attendreEgal(recherche.normaliser(null), '', 'champ absent');
  });

  test('Recherche : tous les champs des tâches, faites incluses et abandonnées exclues', () => {
    const liste = [
      { intitule: 'FICTIF Café', categorie: 'Maison', sous_categorie: 'Étage', note: 'Réparer', fait: true },
      { intitule: 'FICTIF Café abandonné', abandonnee_le: '2030-01-01' }
    ];
    for (const texte of ['CAFE', 'maison', 'etage', 'reparer']) {
      attendreEgal(recherche.chercherTaches(liste, texte), [liste[0]], texte);
    }
    attendreEgal(recherche.chercherTaches(liste, ' '), [], 'requête vide');
    attendreEgal(recherche.chercherTaches(liste, 'absent'), [], 'absent');
  });

  test('Recherche : rendez-vous par titre, lieu et description sans mutation', () => {
    const liste = [{ titre: 'FICTIF Répétition', lieu: 'Théâtre', description: 'Éclairage', date: '2030-01-01', heure: '14:32' }];
    const avant = JSON.stringify(liste);
    for (const texte of ['repetition', 'THEATRE', 'eclairage']) {
      attendreEgal(recherche.chercherRendezVous(liste, texte), liste, texte);
    }
    attendreEgal(recherche.chercherRendezVous(liste, ''), [], 'vide');
    attendreEgal(JSON.stringify(liste), avant, 'données modifiées');
  });

  test('Journal : trente entrées, ordre et intitulé exact', () => {
    const memoire = espaceMemoire();
    const journal = objetIsole(SOURCE_JOURNAL_ACTIONS, 'journalActions', { localStorage: memoire });
    for (let i = 0; i < 35; i++) journal.noter('ajout', `FICTIF ${i} <b>Été</b>  `);
    const entrees = journal.lire();
    attendreEgal(entrees.length, 30, 'limite');
    attendreEgal(entrees[0].texte, 'FICTIF 34 <b>Été</b>  ', 'plus récente');
    attendreEgal(entrees[29].texte, 'FICTIF 5 <b>Été</b>  ', 'plus ancienne');
    attendre(entrees.every(entree => Number.isFinite(Date.parse(entree.heure))), 'heure ISO');
    attendreEgal(Object.keys(entrees[0]), ['heure', 'type', 'texte'], 'structure');
  });

  test('Journal : JSON cassé et structures invalides', () => {
    const memoire = espaceMemoire();
    const journal = objetIsole(SOURCE_JOURNAL_ACTIONS, 'journalActions', { localStorage: memoire });
    for (const brut of ['{cassé', 'null', '{}', '[null,{},42]']) {
      memoire.setItem('cap_journal_actions_v1', brut);
      attendreEgal(journal.lire(), [], 'lecture robuste');
      journal.noter('ajout', 'FICTIF après corruption');
      attendreEgal(journal.lire().length, 1, 'écriture après corruption');
    }
  });

  test('Journal : stockage refusé en lecture et écriture sans erreur', () => {
    const journal = objetIsole(SOURCE_JOURNAL_ACTIONS, 'journalActions', {
      localStorage: { getItem() { throw new Error('refus'); }, setItem() { throw new Error('refus'); } }
    });
    attendreEgal(journal.lire(), [], 'lecture refusée');
    journal.noter('ajout', 'FICTIF refus');
  });

  test('Journal : toutes les actions réussies et aucune après échec', () => {
    localStorage.removeItem('cap_journal_actions_v1');
    const texte = '  FICTIF <b>Été</b> exact  ';
    const tache = creerTache({ intitule: texte });
    cocher(tache.id, true);
    cocher(tache.id, false);
    abandonner(tache.id);
    remettre(tache.id);
    attendreEgal(journalActions.lire().map(entree => entree.type),
      ['remise', 'abandon', 'remise à faire', 'fait', 'ajout'], 'actions');
    attendre(journalActions.lire().every(entree => entree.texte === texte), 'intitulé reformulé');
    const avant = JSON.stringify(journalActions.lire());
    const original = stockage.enregistrer;
    stockage.enregistrer = () => { throw new Error('FICTIF refus'); };
    try {
      attendreErreur(() => creerTache({ intitule: 'FICTIF échec' }), 'refus');
      attendreErreur(() => cocher(tache.id, true), 'refus');
      attendreErreur(() => abandonner(tache.id), 'refus');
    } finally {
      stockage.enregistrer = original;
    }
    attendreEgal(JSON.stringify(journalActions.lire()), avant, 'action échouée journalisée');
  });

  test('Journal : ajout clavier libre et dictée par la porte commune', () => {
    localStorage.removeItem('cap_journal_actions_v1');
    for (const source of ['micro', 'clavier', 'saisie']) {
      traiterDemande({ texte: `FICTIF journal ${source}`, source });
      attendreEgal(journalActions.lire()[0].texte, `FICTIF journal ${source}`, source);
    }
    attendreEgal(journalActions.lire().length, 3, 'doublon journal');
  });

  test('Dernières actions : affichage immédiat après ajout et coche', () => {
    localStorage.removeItem('cap_journal_actions_v1');
    document.getElementById('ajouter').click();
    document.getElementById('intitule').value = 'FICTIF journal interface';
    document.getElementById('formulaire-ajout').requestSubmit();
    const zone = document.getElementById('dernieres-actions');
    attendre(!zone.hidden, 'zone cachée après ajout');
    attendre(zone.textContent.includes('Ajouté : FICTIF journal interface'), 'ajout absent');
    const tache = TACHES.find(tache => tache.intitule === 'FICTIF journal interface');
    const caseTache = document.getElementById(`tache-${tache.id}`);
    caseTache.checked = true;
    caseTache.dispatchEvent(new Event('change'));
    attendre(document.getElementById('liste-actions').firstElementChild.textContent.includes('Fait : FICTIF journal interface'), 'coche absente');
    attendre(!document.getElementById('liste-taches').querySelector(`[data-tache="${tache.id}"]`), 'tâche cochée encore dans la liste');
  });

  function tacheInterface(intitule, cochee = false) {
    document.getElementById('ajouter').click();
    document.getElementById('intitule').value = intitule;
    document.getElementById('formulaire-ajout').requestSubmit();
    const tache = TACHES.find(tache => tache.intitule === intitule);
    attendre(tache, 'tâche de test non créée');
    if (cochee) {
      const caseTache = document.getElementById(`tache-${tache.id}`);
      caseTache.checked = true;
      caseTache.dispatchEvent(new Event('change'));
    }
    return tache;
  }

  test('Terminées : ligne repliée en bas, compteur, décocher remet la tâche dans sa catégorie', () => {
    const bouton = document.getElementById('basculer-terminees');
    const liste = document.getElementById('liste-terminees');
    const tache = tacheInterface('FICTIF terminée interface', true);
    const nombre = TACHES.filter(t => t.fait && !t.abandonnee_le && (!t.parente || !TACHES.some(p => p.id === t.parente && !p.abandonnee_le))).length;
    attendre(!bouton.hidden, 'ligne Terminées cachée');
    attendreEgal(bouton.textContent, `Terminées (${nombre})`, 'compteur');
    attendre(liste.hidden, 'liste ouverte par défaut');
    attendreEgal(bouton.getAttribute('aria-expanded'), 'false', 'aria fermé');
    bouton.click();
    attendre(!liste.hidden, 'liste non ouverte');
    const caseTache = document.getElementById(`tache-${tache.id}`);
    attendre(liste.contains(caseTache) && caseTache.checked, 'tâche absente des terminées');
    caseTache.checked = false;
    caseTache.dispatchEvent(new Event('change'));
    attendre(!tache.fait, 'tâche encore cochée');
    attendre(document.getElementById(`tache-${tache.id}`).closest('.categorie'), 'tâche pas revenue dans sa catégorie');
    attendreEgal(bouton.textContent, `Terminées (${nombre - 1})`, 'compteur après décoche');
    bouton.click();
    attendre(liste.hidden, 'liste non refermée');
    attendre(TACHES.includes(tache), 'tâche perdue');
  });

  function listesIsolees(taches = [], etapes = { Roman: ['Relire'] }, memoire = espaceMemoire(), fenetre = new EventTarget()) {
    let evenements = 0;
    fenetre.addEventListener('cap-listes-changees', () => { evenements += 1; });
    const instance = objetIsole(SOURCE_LISTES_CHOIX, 'listesChoix', {
      localStorage: memoire, window: fenetre, TACHES: taches, ETAPES_PAR_DEFAUT: etapes, dateDuJour: () => '2026-10-29'
    });
    return { instance, memoire, etapes, fenetre, evenements: () => evenements };
  }

  const boutonTexte = (racine, texte) => Array.from(racine.querySelectorAll('button')).find(bouton => bouton.textContent === texte);
  const texteJour = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

  function remettreListesPage(etapesAvant) {
    document.querySelectorAll('dialog[open]').forEach(dialogue => dialogue.close());
    if (etapesAvant) {
      for (const nom of Object.keys(ETAPES_PAR_DEFAUT)) if (!(nom in etapesAvant)) delete ETAPES_PAR_DEFAUT[nom];
    }
    localStorage.removeItem('cap_listes_v1');
    localStorage.removeItem('cap_listes_a_envoyer_v1');
    listesChoix.recharger();
  }

  test('Listes : À trier en tête, plus utilisées ensuite, couleurs et sous-catégories', () => {
    const taches = [
      { categorie: 'Musique', sous_categorie: 'Guitare' }, { categorie: 'Jardin', sous_categorie: '' },
      { categorie: 'Jardin', sous_categorie: '' }, { categorie: 'Écriture', sous_categorie: '', abandonnee_le: '2026-01-01' }
    ];
    const l = listesIsolees(taches);
    attendreEgal(l.instance.categories(), ['À trier', 'Jardin', 'Musique', 'Écriture', 'Quotidien'], 'ordre');
    attendreEgal(l.instance.couleur('À trier'), '#6f6f6f', 'gris pour À trier');
    const couleurs = l.instance.categories().map(nom => l.instance.couleur(nom));
    attendreEgal(new Set(couleurs).size, couleurs.length, 'une couleur par catégorie');
    attendre(couleurs.every(couleur => /^#[0-9a-f]{6}$/i.test(couleur)), 'couleurs valides');
    attendreEgal(l.instance.categories('Musique'), ['Guitare'], 'sous-catégorie reprise des tâches');
    attendreEgal(l.instance.modeles(), ['Roman'], 'modèles de départ');
    attendre(!l.instance.aEnvoyer(), 'rien à envoyer au départ');
    attendreEgal(l.instance.ajouterCategorie('  Voyage   lointain '), 'Voyage lointain', 'nom nettoyé');
    attendre(l.instance.categories().includes('Voyage lointain') && l.instance.aEnvoyer() && l.evenements() > 0, 'ajout signalé');
    attendreEgal(l.instance.ajouterCategorie('musique'), 'Musique', 'pas de doublon');
    attendreEgal(l.instance.categories().filter(nom => nom === 'Musique').length, 1, 'Musique unique');
    l.instance.ajouterCategorie('Basse', 'Musique');
    attendreEgal(l.instance.categories('Musique'), ['Guitare', 'Basse'], 'sous-catégorie ajoutée');
    attendreEgal(l.instance.ajouterCategorie('x'.repeat(80)).length, 60, '60 caractères au plus');
    attendreErreur(() => l.instance.ajouterCategorie('   '), 'Indique un nom');
    attendreErreur(() => l.instance.ajouterCategorie('Solo', 'Inconnue'), 'introuvable');
    const relue = listesIsolees(taches, { Roman: ['Relire'] }, l.memoire);
    attendreEgal(relue.instance.categories('Musique'), ['Guitare', 'Basse'], 'relu après redémarrage');
  });

  test('Listes : retirer n’efface rien, remettre, modèles ajoutés et retirés', () => {
    const l = listesIsolees([{ categorie: 'Jardin', sous_categorie: '' }]);
    attendreEgal(l.instance.retirer('categorie', ['Jardin']), ['Jardin'], 'retrait');
    attendre(!l.instance.categories().includes('Jardin'), 'Jardin encore proposé');
    attendreEgal(l.instance.categoriesRetirees(), [{ nom: 'Jardin', retiree_le: '2026-10-29' }], 'retirée avec la date');
    attendre(l.instance.exporter().categories.some(categorie => categorie.nom === 'Jardin'), 'Jardin effacé');
    attendreEgal(l.instance.remettre('categorie', ['Jardin']), ['Jardin'], 'remise');
    attendre(l.instance.categories().includes('Jardin'), 'Jardin pas revenu');
    attendreEgal(l.instance.ajouterModele('Concert', ['Répéter', '', '  Jouer  ']), 'Concert', 'modèle ajouté');
    attendreEgal(l.etapes.Concert, ['Répéter', 'Jouer'], 'étapes enregistrées pour la création');
    attendreErreur(() => l.instance.ajouterModele('concert', ['A']), 'existe déjà');
    attendreErreur(() => l.instance.ajouterModele('Vide', ['  ']), 'au moins une étape');
    attendreErreur(() => l.instance.ajouterModele('Long', Array.from({ length: 21 }, (_, i) => `É${i}`)), 'Vingt étapes');
    l.instance.retirer('modele', ['Roman']);
    attendreEgal(l.instance.modeles(), ['Concert'], 'Roman retiré du menu');
    attendreEgal(l.etapes.Roman, ['Relire'], 'Roman gardé');
    attendreEgal(l.instance.exporter().modeles.find(modele => modele.nom === 'Roman').retiree_le, '2026-10-29', 'date de retrait');
    attendreEgal(l.instance.ajouterModele('roman', ['Relire', 'Envoyer']), 'Roman', 'modèle remis par un nouvel ajout');
    attendreEgal(l.instance.etapes('Roman'), ['Relire', 'Envoyer'], 'nouvelles étapes');
    attendreEgal(l.instance.modeles(), ['Roman', 'Concert'], 'ordre conservé');
  });

  test('Listes : fusion avec le tableau, la modification la plus récente gagne', () => {
    const l = listesIsolees([]);
    l.instance.retirer('categorie', ['Musique']);
    l.instance.marquerEnvoye();
    l.instance.fusionner({
      modeles: [
        { nom: 'Roman', etapes: ['A', 'B'], retiree_le: '', modifie_le: '2099-01-01T00:00:00.000Z' },
        { nom: 'Album', etapes: ['Mixer'], retiree_le: '', modifie_le: '' }
      ],
      categories: [
        { nom: 'musique', parente: '', couleur: '#123456', retiree_le: '', modifie_le: '2000-01-01T00:00:00.000Z' },
        { nom: 'Sport', parente: '', couleur: '', retiree_le: '', modifie_le: '' },
        { nom: 'Course', parente: 'Sport', couleur: '', retiree_le: '', modifie_le: '' }
      ]
    });
    attendreEgal(l.instance.etapes('Roman'), ['A', 'B'], 'version distante plus récente');
    attendreEgal(l.etapes.Album, ['Mixer'], 'modèle distant ajouté');
    attendre(!l.instance.categories().includes('Musique'), 'retrait local plus récent perdu');
    attendreEgal(l.instance.couleur('Musique'), '#123456', 'couleur du tableau');
    attendre(/^#[0-9a-f]{6}$/i.test(l.instance.couleur('Sport')), 'couleur donnée à Sport');
    attendreEgal(l.instance.categories('Sport'), ['Course'], 'sous-catégorie distante');
    attendre(!l.instance.aEnvoyer(), 'la fusion seule ne demande pas d’envoi');
  });

  test('Compréhension : ce week-end, semaine prochaine et jours pour les dates', () => {
    const jeudi = new Date(2026, 9, 29, 12);
    attendreEgal(comprendreDemande.date('ce week-end', jeudi), '2026-10-31', 'week-end depuis jeudi');
    attendreEgal(comprendreDemande.date('ce week-end', new Date(2026, 9, 31, 12)), '2026-10-31', 'samedi');
    attendreEgal(comprendreDemande.date('ce weekend', new Date(2026, 10, 1, 12)), '2026-11-01', 'dimanche');
    attendreEgal(comprendreDemande.date('semaine prochaine', jeudi), '2026-11-02', 'lundi suivant');
    attendreEgal(comprendreDemande.date('la semaine prochaine', new Date(2026, 10, 2, 12)), '2026-11-09', 'depuis un lundi');
    attendreEgal(comprendreDemande.date('Vendredi', jeudi), '2026-10-30', 'vendredi');
    attendreEgal(comprendreDemande.date('le 12 novembre', jeudi), '2026-11-12', 'date en toutes lettres');
    attendreEgal(comprendreDemande.date('blabla', jeudi), '', 'rien inventé');
    attendreEgal(choixDates.dateRapide("aujourd'hui", jeudi), '2026-10-29', 'bouton Aujourd’hui');
  });

  test('Dates : toutes les façons de dire une date par rapport à aujourd’hui', () => {
    const jeudi = new Date(2026, 9, 29, 9);
    const cas = [
      ['dans deux semaines', '2026-11-12'], ['vendredi dans deux semaines', '2026-11-13'],
      ['dans 2 semaines, vendredi', '2026-11-13'], ['dans un mois', '2026-11-29'],
      ['le premier lundi du mois prochain', '2026-11-02'], ['le dernier vendredi du mois prochain', '2026-11-27'],
      ['après-demain', '2026-10-31'], ['dans trois jours', '2026-11-01'], ['lundi en huit', '2026-11-09'],
      ['mardi en quinze', '2026-11-17'], ['la semaine prochaine, mercredi', '2026-11-04'],
      ['mercredi de la semaine prochaine', '2026-11-04'], ['fin du mois', '2026-10-31'],
      ['fin du mois prochain', '2026-11-30'], ['dans une quinzaine', '2026-11-12'], ['dans un an', '2027-10-29'],
      ['le premier mardi de décembre', '2026-12-01'], ['le 3 février', '2027-02-03'],
      ['le quinze novembre', '2026-11-15'], ['ce jeudi', '2026-10-29'], ['mardi prochain', '2026-11-03']
    ];
    for (const [phrase, attendu] of cas) {
      const resultat = comprendreDates.trouver(phrase, jeudi);
      attendreEgal([resultat.date, resultat.choix], [attendu, []], phrase);
    }
    attendreEgal(comprendreDates.trouver('dans un mois', new Date(2027, 0, 31, 9)).date, '2027-02-28', 'fin de mois raccourcie');
    attendreEgal(comprendreDates.trouver('jeudi', jeudi).choix, ['2026-10-29', '2026-11-05'], 'jeudi un jeudi : question');
    attendreEgal(comprendreDates.trouver('vendredi prochain', jeudi).choix, ['2026-10-30', '2026-11-06'], 'vendredi prochain : question');
    attendreEgal(comprendreDates.trouver('dans 8 jours', jeudi).choix, ['2026-11-05', '2026-11-06'], 'huit jours : question');
    attendreEgal(comprendreDates.trouver('le 15', jeudi).date, '', 'le 15 seul ignoré dans une phrase');
    attendreEgal(comprendreDates.trouver('le 15', jeudi, { seul: true }).date, '2026-11-15', 'le 15 dans Dire la date');
    attendreEgal(comprendreDates.trouver('acheter du pain FICTIF', jeudi), { date: '', choix: [], morceau: '' }, 'rien inventé');
    const rdv = comprendreDemande.rendezVous('rendez-vous jeudi à 10h garage FICTIF', jeudi);
    attendreEgal([rdv.date, rdv.choix_date], ['', ['2026-10-29', '2026-11-05']], 'rendez-vous : date à demander');
  });

  test('Dates : une tâche dictée reçoit son échéance, et Cap demande quand il hésite', () => {
    const avant = TACHES.length;
    const resultat = traiterDemande({ texte: 'Rappeler le garage FICTIF dans deux semaines', source: 'micro' });
    attendreEgal(resultat.type, 'tache', 'type');
    attendreEgal(resultat.tache.intitule, 'Rappeler le garage FICTIF dans deux semaines', 'intitulé intact');
    attendreEgal(resultat.tache.echeance, comprendreDates.trouver('dans deux semaines').date, 'échéance');
    attendreEgal(TACHES.length, avant + 1, 'une tâche ajoutée');
    const hesite = traiterDemande({ texte: 'Arroser les plantes FICTIF dans 8 jours', source: 'micro' });
    attendreEgal([hesite.tache.echeance, hesite.choix_echeance.length], ['', 2], 'hésitation : pas de date devinée');
  });

  test('Ajouter une tâche : dates en menus, boutons rapides, date impossible refusée', () => {
    remettreListesPage();
    document.getElementById('ajouter').click();
    const formulaireTache = document.getElementById('formulaire-ajout');
    attendreEgal(formulaireTache.querySelectorAll('input[type="date"]').length, 0, 'plus de saisie JJ/MM/AAAA');
    const jour = document.getElementById('echeance-jour');
    const mois = document.getElementById('echeance-mois');
    const annee = document.getElementById('echeance-annee');
    const echeance = document.getElementById('echeance');
    attendre(jour && mois && annee, 'trois menus absents');
    attendreEgal(annee.options[1].value, String(new Date().getFullYear()), 'année en cours en premier');
    attendreEgal(mois.options[11].textContent, 'novembre', 'mois en toutes lettres');
    attendreEgal(echeance.value, '', 'vide par défaut');
    const zone = jour.closest('.champ-date');
    attendreEgal(Array.from(zone.querySelectorAll('.boutons-rapides button'), b => b.textContent),
      ['Aujourd’hui', 'Demain', 'Ce week-end', 'Semaine prochaine'], 'quatre boutons rapides');
    const demain = new Date();
    demain.setDate(demain.getDate() + 1);
    boutonTexte(zone, 'Demain').click();
    attendreEgal(echeance.value, texteJour(demain), 'Demain');
    attendreEgal([jour.value, mois.value, annee.value], texteJour(demain).split('-').reverse(), 'menus remplis d’un coup');
    attendreEgal(boutonTexte(zone, 'Demain').getAttribute('aria-pressed'), 'true', 'bouton marqué');
    boutonTexte(zone, 'Ce week-end').click();
    const weekend = new Date(`${echeance.value}T12:00:00`);
    attendre([0, 6].includes(weekend.getDay()) && echeance.value >= texteJour(new Date()), 'week-end incorrect');
    boutonTexte(zone, 'Semaine prochaine').click();
    attendre(new Date(`${echeance.value}T12:00:00`).getDay() === 1 && echeance.value > texteJour(new Date()), 'semaine prochaine incorrecte');
    boutonTexte(zone, 'Effacer').click();
    attendreEgal([echeance.value, jour.value, mois.value, annee.value], ['', '', '', ''], 'effacé');
    mois.value = '03';
    mois.dispatchEvent(new Event('change'));
    attendreEgal([jour.value, annee.value], [String(new Date().getDate()).padStart(2, '0'), String(new Date().getFullYear())], 'jour et année du jour complétés');
    jour.value = '31';
    mois.value = '02';
    jour.dispatchEvent(new Event('change'));
    attendreEgal(echeance.value, '', 'date impossible gardée');
    attendre(jour.validationMessage.includes('n’existe pas'), 'pas de message pour le 31 février');
    document.getElementById('intitule').value = 'FICTIF date impossible';
    const avant = TACHES.length;
    formulaireTache.requestSubmit();
    attendreEgal(TACHES.length, avant, 'tâche créée avec une date impossible');
    jour.value = '28';
    jour.dispatchEvent(new Event('change'));
    attendreEgal(echeance.value, `${annee.value}-02-28`, '28 février');
    attendreEgal(jour.validationMessage, '', 'message retiré');
    boutonTexte(document.getElementById('avant-le-jour').closest('.champ-date'), 'Aujourd’hui').click();
    document.getElementById('intitule').value = 'FICTIF dates menus';
    formulaireTache.requestSubmit();
    const tache = TACHES.find(item => item.intitule === 'FICTIF dates menus');
    attendre(tache, 'tâche non créée');
    attendreEgal([tache.echeance, tache.avant_le], [`${annee.value}-02-28`, texteJour(new Date())], 'dates enregistrées');
    document.getElementById('ajouter').click();
    attendreEgal([echeance.value, jour.value, document.getElementById('avant-le').value], ['', '', ''], 'formulaire remis à zéro');
    remettreListesPage();
  });

  test('Ajouter une tâche : catégories en gros boutons, sous-catégories, ajouter et retirer sans effacer', () => {
    remettreListesPage();
    document.getElementById('ajouter').click();
    document.getElementById('choisir-categorie').click();
    const fenetre = document.getElementById('fenetre-liste');
    attendre(fenetre.open, 'liste des catégories pas ouverte');
    attendreEgal(fenetre.querySelectorAll('input, textarea').length, 0, 'aucun champ texte, donc pas de clavier');
    const premiers = Array.from(fenetre.querySelector('.grille-choix').querySelectorAll('.bouton-choix'), b => b.textContent);
    attendreEgal(premiers[0], 'À trier', 'À trier en premier');
    attendre(['Musique', 'Écriture', 'Quotidien'].every(nom => premiers.includes(nom)), 'catégories prêtes absentes');
    boutonTexte(fenetre, '+ Ajouter').click();
    document.getElementById('nom-nouvel-element').value = 'Jardin FICTIF';
    fenetre.querySelector('form').requestSubmit();
    const jardin = boutonTexte(fenetre, 'Jardin FICTIF');
    attendre(jardin, 'nouvelle catégorie pas devenue un bouton');
    attendre(jardin.style.getPropertyValue('--couleur-choix'), 'nouvelle catégorie sans couleur');
    jardin.click();
    attendreEgal(document.getElementById('titre-fenetre-liste').textContent, 'Jardin FICTIF : sous-catégorie', 'sous-catégories ouvertes');
    boutonTexte(fenetre, '+ Ajouter').click();
    document.getElementById('nom-nouvel-element').value = 'Potager';
    fenetre.querySelector('form').requestSubmit();
    boutonTexte(fenetre, 'Potager').click();
    attendre(!fenetre.open, 'fenêtre restée ouverte après le choix');
    attendreEgal([document.getElementById('categorie').value, document.getElementById('sous-categorie').value], ['Jardin FICTIF', 'Potager'], 'choix enregistré');
    attendreEgal(document.getElementById('texte-categorie').textContent, 'Jardin FICTIF › Potager', 'choix affiché');
    document.getElementById('intitule').value = 'FICTIF catégorie boutons';
    document.getElementById('formulaire-ajout').requestSubmit();
    const tache = TACHES.find(item => item.intitule === 'FICTIF catégorie boutons');
    attendreEgal([tache.categorie, tache.sous_categorie], ['Jardin FICTIF', 'Potager'], 'tâche classée');
    const section = document.getElementById(`tache-${tache.id}`).closest('section.categorie');
    attendreEgal(section.style.getPropertyValue('--couleur-categorie'), listesChoix.couleur('Jardin FICTIF'), 'couleur dans la liste');
    document.getElementById('ajouter').click();
    document.getElementById('choisir-categorie').click();
    boutonTexte(fenetre, 'Modifier').click();
    const retirer = Array.from(fenetre.querySelectorAll('.bouton-retirer'))[0];
    attendre(retirer.hidden, 'Retirer visible sans case cochée');
    const caseJardin = Array.from(fenetre.querySelectorAll('.liste-cases input')).find(c => c.value === 'Jardin FICTIF');
    caseJardin.checked = true;
    caseJardin.dispatchEvent(new Event('change'));
    attendre(!retirer.hidden && retirer.textContent === 'Retirer (1)', 'bouton Retirer (1) absent');
    retirer.click();
    attendre(!listesChoix.categories().includes('Jardin FICTIF'), 'catégorie encore proposée');
    attendre(listesChoix.exporter().categories.find(c => c.nom === 'Jardin FICTIF').retiree_le, 'catégorie effacée au lieu d’être marquée');
    attendre(fenetre.querySelector('.section-retirees').textContent.includes('Jardin FICTIF'), 'pas dans Retirées');
    const bandeau = document.getElementById('annulation-liste');
    attendre(!bandeau.hidden, 'pas de bouton Annuler');
    boutonTexte(bandeau, 'Annuler').click();
    attendre(listesChoix.categories().includes('Jardin FICTIF'), 'Annuler n’a pas remis la catégorie');
    attendre(TACHES.includes(tache) && tache.categorie === 'Jardin FICTIF', 'tâche touchée');
    remettreListesPage();
  });

  test('Étapes par défaut : Ajouter et Modifier la liste depuis le menu', () => {
    const etapesAvant = JSON.parse(JSON.stringify(ETAPES_PAR_DEFAUT));
    remettreListesPage(etapesAvant);
    document.getElementById('ajouter').click();
    const selection = document.getElementById('modele');
    const options = Array.from(selection.options);
    attendreEgal(options.slice(-2).map(o => [o.value, o.textContent]), [['__ajouter', 'Ajouter…'], ['__modifier', 'Modifier la liste…']], 'deux choix en bas');
    selection.value = '__ajouter';
    selection.dispatchEvent(new Event('change'));
    attendreEgal(selection.value, '', 'menu remis à l’ancien choix');
    const fenetre = document.getElementById('fenetre-liste');
    attendre(fenetre.open, 'fenêtre d’ajout pas ouverte');
    document.getElementById('nom-nouvel-element').value = 'Concert FICTIF';
    document.getElementById('etapes-nouveau-modele').value = 'Répéter\n\nJouer';
    fenetre.querySelector('form').requestSubmit();
    attendre(!fenetre.open, 'fenêtre restée ouverte');
    attendreEgal(selection.value, 'Concert FICTIF', 'nouveau modèle choisi');
    attendreEgal(ETAPES_PAR_DEFAUT['Concert FICTIF'], ['Répéter', 'Jouer'], 'étapes enregistrées');
    attendre(listesChoix.aEnvoyer(), 'pas marqué pour le tableau');
    document.getElementById('intitule').value = 'FICTIF concert';
    document.getElementById('formulaire-ajout').requestSubmit();
    const parent = TACHES.find(item => item.intitule === 'FICTIF concert');
    attendreEgal(TACHES.filter(item => item.parente === parent.id).map(item => item.intitule), ['Répéter', 'Jouer'], 'étapes créées');
    document.getElementById('ajouter').click();
    selection.value = '__modifier';
    selection.dispatchEvent(new Event('change'));
    attendre(fenetre.open, 'fenêtre Modifier pas ouverte');
    const retirer = fenetre.querySelector('.bouton-retirer');
    attendre(retirer.hidden, 'Retirer visible d’emblée');
    const caseConcert = Array.from(fenetre.querySelectorAll('.liste-cases input')).find(c => c.value === 'Concert FICTIF');
    caseConcert.checked = true;
    caseConcert.dispatchEvent(new Event('change'));
    attendreEgal(retirer.textContent, 'Retirer (1)', 'compteur');
    fenetre.querySelector('.bouton-retirer').click();
    attendre(!listesChoix.modeles().includes('Concert FICTIF'), 'modèle encore proposé');
    attendre(!Array.from(selection.options).some(o => o.value === 'Concert FICTIF'), 'modèle encore dans le menu');
    attendreEgal(listesChoix.modelesRetires().map(m => m.nom), ['Concert FICTIF'], 'modèle gardé comme retiré');
    boutonTexte(document.getElementById('annulation-liste'), 'Annuler').click();
    attendre(listesChoix.modeles().includes('Concert FICTIF'), 'Annuler sans effet');
    const caseDeNouveau = Array.from(fenetre.querySelectorAll('.liste-cases input')).find(c => c.value === 'Concert FICTIF');
    caseDeNouveau.checked = true;
    caseDeNouveau.dispatchEvent(new Event('change'));
    fenetre.querySelector('.bouton-retirer').click();
    boutonTexte(fenetre.querySelector('.section-retirees'), 'Remettre').click();
    attendre(listesChoix.modeles().includes('Concert FICTIF'), 'Remettre sans effet');
    attendre(Array.from(selection.options).some(o => o.value === 'Concert FICTIF'), 'modèle pas revenu dans le menu');
    remettreListesPage(etapesAvant);
  });

  test('Dates : ligne en toutes lettres sous les menus, vide si la date est vide', () => {
    attendreEgal(choixDates.dateEnLettres('2026-11-02'), 'lundi 2 novembre 2026', 'lundi 2 novembre');
    attendreEgal(choixDates.dateEnLettres('2026-02-31'), '', 'date impossible');
    attendreEgal(choixDates.dateEnLettres(''), '', 'date vide');
    remettreListesPage();
    document.getElementById('ajouter').click();
    const lisible = document.getElementById('echeance-lisible');
    const echeance = document.getElementById('echeance');
    attendreEgal(lisible.textContent, '', 'rien tant que la date est vide');
    const zone = lisible.closest('.champ-date');
    boutonTexte(zone, 'Demain').click();
    attendreEgal(lisible.textContent, choixDates.dateEnLettres(echeance.value), 'bouton rapide');
    const jour = document.getElementById('echeance-jour');
    const mois = document.getElementById('echeance-mois');
    const annee = document.getElementById('echeance-annee');
    jour.value = '02';
    mois.value = '11';
    annee.value = '2026';
    annee.dispatchEvent(new Event('change'));
    attendreEgal(lisible.textContent, 'lundi 2 novembre 2026', 'menus');
    boutonTexte(zone, 'Effacer').click();
    attendreEgal(lisible.textContent, '', 'effacée');
    remettreListesPage();
  });

  test('Dire la date : écoute, relance si rien entendu, texte provisoire et dates dites', () => {
    let rappels = null;
    let demarrages = 0;
    const dicteeSimulee = {
      disponible: () => true,
      enCours: () => false,
      arreter() {},
      demarrer(r) { rappels = r; demarrages += 1; }
    };
    const instance = objetIsole(SOURCE_CHOIX_DATES, 'choixDates', {
      document, Date, comprendreDemande, dictee: dicteeSimulee, setTimeout: f => f()
    });
    const cible = document.createElement('input');
    cible.type = 'hidden';
    cible.id = 'date-essai-dictee';
    const conteneur = document.createElement('div');
    conteneur.dataset.cible = cible.id;
    conteneur.dataset.libelle = 'Essai';
    document.body.append(cible, conteneur);
    try {
      instance.installer(conteneur);
      const dire = boutonTexte(conteneur, 'Dire la date');
      const aide = conteneur.querySelector('.aide-date');
      attendre(!dire.hidden, 'bouton caché');
      dire.click();
      attendreEgal(demarrages, 1, 'écoute lancée');
      attendre(aide.textContent.includes('Je t’écoute'), 'pas de message d’écoute');
      rappels.surErreur('no-speech');
      rappels.surFin();
      attendreEgal(demarrages, 2, 'pas de relance après un silence');
      rappels.surFin();
      attendre(aide.textContent.includes('rien entendu'), 'pas de message après la relance');
      const jeudi = new Date();
      dire.click();
      rappels.surProvisoire('vendredi');
      attendre(aide.textContent.includes('vendredi'), 'texte entendu non affiché');
      rappels.surFin();
      attendreEgal(cible.value, comprendreDemande.date('vendredi', jeudi), 'texte provisoire non utilisé');
      dire.click();
      rappels.surFinal('demain');
      rappels.surFin();
      attendreEgal(cible.value, comprendreDemande.date('demain', new Date()), 'demain');
      dire.click();
      rappels.surFinal('le 15 novembre');
      rappels.surFin();
      attendreEgal(cible.value.slice(5), '11-15', 'le 15 novembre');
      attendre(conteneur.querySelector('.date-lisible').textContent.includes('15 novembre'), 'ligne lisible');
      dire.click();
      rappels.surErreur('not-allowed');
      rappels.surFin();
      attendre(aide.textContent.includes('bloqué'), 'micro bloqué non expliqué');
    } finally {
      cible.remove();
      conteneur.remove();
    }
  });

  test('Petites fenêtres : toucher à côté ferme, question Garder, Jeter et Continuer', () => {
    remettreListesPage();
    for (const id of ['clavier', 'menu-tache', 'ajout-tache']) {
      attendreEgal(document.querySelectorAll(`#${id} [data-fermer]`).length, 0, `bouton retour dans ${id}`);
    }
    const ajout = document.getElementById('ajout-tache');
    const intitule = document.getElementById('intitule');
    document.getElementById('ajouter').click();
    const cadre = ajout.getBoundingClientRect();
    ajout.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: cadre.left + 2, clientY: cadre.top + 2 }));
    attendre(ajout.open, 'fermée en touchant dedans');
    fermetureFenetres.toucheACote(ajout);
    attendre(!ajout.open, 'fenêtre vide pas fermée');
    document.getElementById('ajouter').click();
    intitule.value = 'FICTIF brouillon';
    intitule.dispatchEvent(new Event('input', { bubbles: true }));
    fermetureFenetres.toucheACote(ajout);
    attendre(ajout.open, 'fermée alors que Max avait écrit');
    const question = () => ajout.querySelector('.question-fermeture');
    attendre(question(), 'pas de question');
    attendreEgal(Array.from(question().querySelectorAll('button'), b => b.textContent), ['Garder', 'Jeter', 'Continuer'], 'trois boutons');
    boutonTexte(question(), 'Continuer').click();
    attendre(ajout.open && !question() && intitule.value === 'FICTIF brouillon', 'Continuer');
    fermetureFenetres.toucheACote(ajout);
    boutonTexte(question(), 'Garder').click();
    attendre(!ajout.open, 'Garder n’a pas fermé');
    document.getElementById('ajouter').click();
    attendreEgal(intitule.value, 'FICTIF brouillon', 'texte gardé retrouvé');
    fermetureFenetres.toucheACote(ajout);
    boutonTexte(question(), 'Jeter').click();
    attendre(!ajout.open, 'Jeter n’a pas fermé');
    const bandeau = document.querySelector('.annulation-fenetre');
    attendre(bandeau, 'pas de bouton Annuler après Jeter');
    document.getElementById('ajouter').click();
    attendreEgal(intitule.value, '', 'texte jeté revenu tout seul');
    ajout.close();
    boutonTexte(bandeau, 'Annuler').click();
    attendre(ajout.open, 'Annuler n’a pas rouvert');
    attendreEgal(intitule.value, 'FICTIF brouillon', 'Annuler n’a pas remis le texte');
    attendre(!document.querySelector('.annulation-fenetre'), 'bandeau resté');
    intitule.value = '';
    ajout.close();
    document.getElementById('ajouter').click();
    document.getElementById('choisir-categorie').click();
    const fenetre = document.getElementById('fenetre-liste');
    attendre(!boutonTexte(fenetre, 'Fermer') && !boutonTexte(fenetre, 'Retour'), 'bouton retour encore là');
    boutonTexte(fenetre, '+ Ajouter').click();
    const nom = document.getElementById('nom-nouvel-element');
    nom.value = 'Jardin FICTIF';
    nom.dispatchEvent(new Event('input', { bubbles: true }));
    fermetureFenetres.toucheACote(fenetre);
    boutonTexte(fenetre.querySelector('.question-fermeture'), 'Garder').click();
    attendre(fenetre.open, 'fenêtre d’avant pas revenue');
    attendreEgal(document.getElementById('titre-fenetre-liste').textContent, 'Catégorie', 'retour à la liste des catégories');
    attendre(ajout.open, 'fenêtre principale fermée');
    boutonTexte(fenetre, '+ Ajouter').click();
    attendreEgal(document.getElementById('nom-nouvel-element').value, 'Jardin FICTIF', 'nom gardé');
    document.getElementById('nom-nouvel-element').value = '';
    fermetureFenetres.toucheACote(fenetre);
    attendreEgal(document.getElementById('titre-fenetre-liste').textContent, 'Catégorie', 'vide : retour direct');
    fermetureFenetres.toucheACote(fenetre);
    attendre(!fenetre.open && ajout.open, 'catégories : retour à la fenêtre Ajouter');
    attendre(!listesChoix.categories().includes('Jardin FICTIF'), 'catégorie créée sans le vouloir');
    remettreListesPage();
  });

  await testAsync('Google Sheets listes : lecture, ancien entête, onglet Catégories ajouté sans rien effacer', async c => {
    c.localStorage.setItem('cap_google_fichier_v1', 'tableau-fictif');
    let ongletsPresents = ['Tâches', 'Étapes par défaut', 'Phrases du clavier'];
    let lignesModeles = [['Modèle', 'Étape'], ['Roman', 'Relire'], ['Roman', 'Corriger'], ['Album', 'Mixer']];
    c.repondre = async r => {
      const chemin = decodeURIComponent(r.url.pathname);
      if (r.methode === 'GET' && chemin === '/drive/v3/files/tableau-fictif') return reponseGoogle({ id: 'tableau-fictif', trashed: false });
      if (r.methode === 'GET' && chemin === '/v4/spreadsheets/tableau-fictif') return reponseGoogle({ sheets: ongletsPresents.map(title => ({ properties: { title } })) });
      if (r.methode === 'GET' && chemin.includes('Étapes par défaut')) return reponseGoogle({ values: lignesModeles });
      if (r.methode === 'GET' && chemin.includes('Catégories')) return reponseGoogle({ values: [] });
      if (r.methode === 'POST') return reponseGoogle({});
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const sheets = c.sheets();
    await sheets.trouverOuCreer();
    const lecture = await sheets.lireListes();
    attendreEgal(lecture.modeles.map(m => [m.nom, m.etapes]), [['Roman', ['Relire', 'Corriger']], ['Album', ['Mixer']]], 'modèles lus');
    attendreEgal(lecture.manquants, ['Catégories'], 'onglet manquant repéré');
    await sheets.ecrireListes({
      modeles: [{ nom: 'Roman', etapes: ['Relire'], retiree_le: '2026-10-29', modifie_le: 'x' }],
      categories: [{ nom: 'À trier', parente: '', couleur: '#6f6f6f', retiree_le: '', modifie_le: '' }]
    });
    const ajoutOnglet = c.requetes.find(r => r.url.pathname.endsWith('tableau-fictif:batchUpdate')).corps.requests;
    attendreEgal(ajoutOnglet.map(a => a.addSheet.properties.title), ['Catégories'], 'onglet Catégories ajouté');
    const ecriture = c.requetes.find(r => r.url.pathname.endsWith('/values:batchUpdate')).corps;
    attendreEgal(ecriture.valueInputOption, 'RAW', 'écriture brute');
    attendreEgal(ecriture.data[0].values, [['Modèle', 'Étape', 'Retirée le', 'Modifiée le'], ['Roman', 'Relire', '2026-10-29', 'x'], ['', '', '', ''], ['', '', '', '']], 'lignes anciennes recouvertes, aucune suppression');
    attendreEgal(ecriture.data[1].values, [['Catégorie', 'Sous-catégorie de', 'Couleur', 'Retirée le', 'Modifiée le', 'Ordre'], ['À trier', '', '#6f6f6f', '', '', '']], 'catégories écrites');
    ongletsPresents = [...ongletsPresents, 'Catégories'];
    lignesModeles = [['Nom', 'Truc'], ['Roman', 'Relire']];
    const avant = c.requetes.filter(r => r.methode === 'POST').length;
    await attendreRejet(() => sheets.ecrireListes({ modeles: [], categories: [] }), 'illisibles');
    lignesModeles = [['Modèle', 'Étape'], ['Roman', 42]];
    await attendreRejet(() => sheets.ecrireListes({ modeles: [], categories: [] }), 'illisible');
    attendreEgal(c.requetes.filter(r => r.methode === 'POST').length, avant, 'aucune écriture sur un tableau illisible');
  });

  await testAsync('Synchro listes : lit, fusionne, écrit, puis seulement après un changement', async c => {
    const memoire = espaceMemoire();
    const l = listesIsolees([], { Roman: ['Relire'] }, memoire, c.window);
    const ecritures = [];
    let echec = false;
    const fauxSheets = {
      trouverOuCreer: async () => ({ id: 'tableau-fictif', cree: false }),
      lireListes: async () => ({ modeles: [], categories: [{ nom: 'Sport', parente: '', couleur: '', retiree_le: '', modifie_le: '' }] }),
      ecrireListes: async donnees => {
        if (echec) throw new Error('panne simulée');
        ecritures.push(donnees);
      }
    };
    const synchro = objetIsole(SOURCE_SYNCHRO_LISTES, 'synchroListes', {
      googleConnexion: c.googleConnexion, navigator: c.navigator, googleSheets: fauxSheets, listesChoix: l.instance,
      localStorage: memoire, window: c.window, setInterval: c.setInterval, Date: c.Date
    });
    attendreEgal(await synchro.synchroniser(), true, 'première synchronisation');
    attendreEgal(ecritures.length, 1, 'une écriture');
    attendre(ecritures[0].categories.some(cat => cat.nom === 'Sport') && l.instance.categories().includes('Sport'), 'fusion absente');
    attendreEgal(await synchro.synchroniser(), false, 'rien à refaire');
    attendreEgal(ecritures.length, 1, 'pas de réécriture inutile');
    l.instance.ajouterCategorie('Voyage');
    await synchro.synchroniser();
    attendreEgal(ecritures.length, 2, 'changement envoyé');
    attendre(ecritures[1].categories.some(cat => cat.nom === 'Voyage'), 'Voyage absent');
    echec = true;
    l.instance.ajouterCategorie('Cuisine');
    await synchro.synchroniser();
    attendre(l.instance.aEnvoyer(), 'changement perdu après une panne');
    attendre(synchro.erreur().includes('panne simulée'), 'erreur non gardée');
    echec = false;
    attendreEgal(await synchro.synchroniser(), false, 'nouvel essai trop tôt');
    c.maintenant += 61000;
    attendreEgal(await synchro.synchroniser(), true, 'nouvel essai après une minute');
    attendre(ecritures.at(-1).categories.some(cat => cat.nom === 'Cuisine') && !l.instance.aEnvoyer(), 'Cuisine pas envoyée');
    c.navigator.onLine = false;
    l.instance.ajouterCategorie('Hors ligne');
    const nombre = ecritures.length;
    attendreEgal(await synchro.synchroniser(), false, 'hors ligne');
    attendreEgal(ecritures.length, nombre, 'aucun envoi hors ligne');
    attendre(l.instance.aEnvoyer(), 'changement hors ligne gardé');
  });

  test('Glisser et report : droite coche, gauche reporte à demain, Annuler remet', () => {
    const tache = tacheInterface('FICTIF glisser interface');
    const glisser = ecart => {
      const ligne = document.getElementById('liste-taches').querySelector(`[data-tache="${tache.id}"]`);
      ligne.getBoundingClientRect = () => ({ width: 300 });
      Object.defineProperty(ligne, 'offsetWidth', { configurable: true, value: 300 });
      const options = { bubbles: true, pointerId: 7, pointerType: 'touch', clientY: 10 };
      ligne.dispatchEvent(new PointerEvent('pointerdown', { ...options, clientX: 150 }));
      ligne.dispatchEvent(new PointerEvent('pointermove', { ...options, clientX: 150 + ecart / 2 }));
      ligne.dispatchEvent(new PointerEvent('pointermove', { ...options, clientX: 150 + ecart }));
      ligne.dispatchEvent(new PointerEvent('pointerup', { ...options, clientX: 150 + ecart }));
    };
    const demain = new Date();
    demain.setDate(demain.getDate() + 1);
    const texteDemain = `${demain.getFullYear()}-${String(demain.getMonth() + 1).padStart(2, '0')}-${String(demain.getDate()).padStart(2, '0')}`;
    const ancienne = tache.echeance;
    glisser(-120);
    attendreEgal(tache.echeance, texteDemain, 'échéance demain');
    attendre(!tache.fait, 'report ne coche pas');
    let annuler = document.querySelector('#statut .annuler-dictee');
    attendre(annuler, 'pas de bouton Annuler après report');
    annuler.click();
    attendreEgal(tache.echeance, ancienne, 'report annulé');
    glisser(40);
    attendre(!tache.fait, 'petit glisser ne coche pas');
    glisser(120);
    attendre(tache.fait, 'glisser à droite ne coche pas');
    annuler = document.querySelector('#statut .annuler-dictee');
    attendre(annuler, 'pas de bouton Annuler après coche');
    annuler.click();
    attendre(!tache.fait, 'coche non annulée');
    attendre(TACHES.includes(tache), 'tâche perdue');
  });

  test('Voix : « Reporte ça à demain » reporte la dernière tâche ouverte', () => {
    const tache = tacheInterface('FICTIF voix interface');
    const nombre = TACHES.length;
    const ancienne = tache.echeance;
    document.querySelector(`[data-tache="${tache.id}"] .options-tache`).click();
    document.getElementById('menu-tache').close();
    document.getElementById('ouvrir-clavier').click();
    document.getElementById('saisie-demande').value = 'Reporte ça à demain';
    document.getElementById('formulaire-demande').requestSubmit();
    const demain = new Date();
    demain.setDate(demain.getDate() + 1);
    attendreEgal(tache.echeance, `${demain.getFullYear()}-${String(demain.getMonth() + 1).padStart(2, '0')}-${String(demain.getDate()).padStart(2, '0')}`, 'tâche ouverte reportée');
    attendreEgal(TACHES.length, nombre, 'aucune tâche créée');
    if (document.getElementById('clavier').open) document.getElementById('clavier').close();
    document.querySelector('#statut .annuler-dictee').click();
    attendreEgal(tache.echeance, ancienne, 'report vocal annulé');
    const proposeRdv = traiterDemande({ texte: 'Ajoute-moi un rendez-vous à 11h45 aujourd\'hui, intitulé test, rappel dix minutes avant', source: 'micro', agenda_disponible: true });
    attendre(proposeRdv.type === 'proposition' && proposeRdv.message.includes('à 11 h 45') && proposeRdv.message.endsWith('c’est bien ça ?'), `rendez-vous redit : ${proposeRdv.message}`);
    attendre(!document.getElementById('fiche-rendez-vous').open, 'la fiche rendez-vous ne s’ouvre pas toute seule');
    const corrige = traiterDemande({ texte: 'Non, à 16h', source: 'micro', agenda_disponible: true });
    attendre(corrige.type === 'proposition' && corrige.message.includes('à 16 h') && !corrige.message.includes('11 h 45'), `correction reformulée : ${corrige.message}`);
    attendreEgal(traiterDemande({ texte: 'Non', source: 'micro', agenda_disponible: true }).message, 'D’accord, je n’inscris rien dans l’agenda.', 'non : rien inscrit');
    attendreEgal(TACHES.length, nombre, 'rendez-vous connecté : aucune tâche');
    const sansHeure = actionsCap.preparerProposition('proposer_rendez_vous', { titre: 'Dentiste FICTIF', date: '2027-01-11', lieu: 'rue FICTIVE' });
    attendreEgal([sansHeure.manque, sansHeure.texte], ['heure', 'À quelle heure ?'], 'heure manquante : une seule question');
    const complete = actionsCap.completerProposition(sansHeure, 'à 15h30');
    attendreEgal(actionsCap.preparerProposition('proposer_rendez_vous', complete).texte,
      'Rendez-vous « Dentiste FICTIF » le lundi 11 janvier 2027 à 15 h 30, rue FICTIVE, c’est bien ça ?', 'jour de la semaine calculé par Cap');
    const deuxDates = actionsCap.preparerProposition('proposer_rendez_vous', { titre: 'FICTIF', heure: '10:00', choix_date: ['2027-01-07', '2027-01-14'] });
    attendre(deuxDates.manque === 'date' && deuxDates.texte.includes(' ou le '), `deux dates possibles : ${deuxDates.texte}`);
    attendreEgal(actionsCap.completerProposition(deuxDates, 'le 14').date, '2027-01-14', 'date choisie');
    attendreEgal([actionsCap.heureDite('midi'), actionsCap.heureDite('9 heures 05'), actionsCap.heureDite('rien')], ['12:00', '09:05', ''], 'heures dites');
    cerveau.proposer({ type: 'action', action: 'proposer_rendez_vous', parametres: { titre: 'FICTIF', date: '2027-01-11', heure: '10:00' } });
    attendreEgal(traiterDemande({ texte: 'annule', source: 'micro' }).message, 'D’accord, je n’inscris rien dans l’agenda.', '« annule » pendant une proposition : rien inscrit');
    attendre(!cerveau.propositionEnAttente(), 'proposition oubliée');
    const horsLigne = traiterDemande({ texte: 'rendez-vous demain à 9h FICTIF', source: 'micro', agenda_disponible: false });
    attendre(horsLigne.type === 'tache' && horsLigne.message.includes('PAS dans l\'agenda'), 'message honnête hors connexion');
    abandonner(horsLigne.tache.id);
    attendreEgal(tache.echeance, ancienne, 'traiterDemande seul ne modifie pas');
  });

  await testAsync('Dernières actions : zone cachée si vide', async c => {
    const ui = preparerInterface(c);
    attendre(ui.parId('dernieres-actions').hidden, 'zone vide visible');
  });

  await testAsync('Dernières actions : cinq lignes, heure, hier et date courte', async c => {
    const aujourdHui = new Date();
    const hier = new Date();
    hier.setDate(hier.getDate() - 1);
    const ancien = new Date();
    ancien.setDate(ancien.getDate() - 3);
    const dates = [aujourdHui, hier, ancien, aujourdHui, aujourdHui, aujourdHui];
    c.localStorage.setItem('cap_journal_actions_v1', JSON.stringify(dates.map((date, index) => ({
      heure: date.toISOString(), type: 'ajout', texte: `FICTIF ${index}`
    }))));
    const ui = preparerInterface(c);
    const lignes = [...ui.parId('liste-actions').children];
    attendreEgal(lignes.length, 5, 'limite affichage');
    attendre(/\d{2}:\d{2} · Ajouté : FICTIF 0/.test(lignes[0].textContent), 'heure locale');
    attendre(lignes[1].textContent.includes('hier'), 'hier absent');
    attendre(lignes[2].textContent.includes(new Intl.DateTimeFormat('fr-FR', { day: '2-digit', month: '2-digit' }).format(ancien)), 'date courte absente');
  });

  await testAsync('Recherche accueil : options futures grisées et inaccessibles', async c => {
    const ui = preparerInterface(c);
    const select = ui.parId('source-recherche');
    attendreEgal([...select.options].map(option => option.textContent),
      ['Tâches', 'Rendez-vous', 'Gmail (plus tard)', 'Drive (plus tard)', 'Archives perso (plus tard)', 'Mémoire perso (plus tard)'], 'options');
    attendreEgal(select.selectedIndex, 0, 'choix initial');
    attendre([...select.options].slice(2).every(option => option.disabled), 'option future accessible');
    const style = ui.cadre.contentWindow.getComputedStyle(select.options[2]);
    attendre(style.color !== ui.cadre.contentWindow.getComputedStyle(select.options[0]).color, 'options non grisées');
    const champ = ui.parId('saisie-recherche');
    attendreEgal([champ.type, champ.getAttribute('enterkeyhint'), champ.autocomplete], ['search', 'search', 'off'], 'champ mobile');
    attendre(Boolean(champ.getAttribute('aria-label')), 'étiquette absente');
  });

  await testAsync('Recherche accueil : résultats à chaque input, vide et message exact', async c => {
    const ui = preparerInterface(c);
    const champ = ui.parId('saisie-recherche');
    const liste = ui.parId('resultats-recherche');
    attendreEgal(liste.textContent, '', 'texte à vide');
    champ.value = 'FICTIF zz introuvable';
    champ.dispatchEvent(new Event('input'));
    attendreEgal(liste.textContent.trim(), 'Rien trouvé dans Tâches', 'message exact');
    champ.value = c.TACHES[0].intitule;
    champ.dispatchEvent(new Event('input'));
    attendre(liste.querySelector('button'), 'résultat sans validation absent');
    champ.value = '';
    champ.dispatchEvent(new Event('input'));
    attendreEgal(liste.textContent, '', 'effacement');
    ui.parId('source-recherche').value = ui.parId('source-recherche').options[1].value;
    champ.value = 'introuvable';
    ui.parId('source-recherche').dispatchEvent(new Event('change'));
    attendreEgal(liste.textContent.trim(), 'Rien trouvé dans Rendez-vous', 'changement source');
  });

  await testAsync('Recherche accueil : trente résultats, autres et tâches faites', async c => {
    c.TACHES.splice(0, c.TACHES.length, ...Array.from({ length: 36 }, (_, index) => ({
      ...TACHES_FICTIVES[0], id: `FICTIF-${index}`, intitule: `FICTIF résultat ${index}`, fait: index === 0, abandonnee_le: ''
    })));
    const ui = preparerInterface(c);
    ui.parId('saisie-recherche').value = 'resultat';
    ui.parId('saisie-recherche').dispatchEvent(new Event('input'));
    attendreEgal(ui.parId('resultats-recherche').querySelectorAll('button').length, 30, 'limite');
    attendre(ui.parId('resultats-recherche').textContent.includes('et 6 autres…'), 'compteur');
    attendre(ui.parId('resultats-recherche').querySelector('button').textContent.toLowerCase().includes('fait'), 'statut fait');
  });

  await testAsync('Recherche accueil : toucher tâche ouvre, défile et surligne deux secondes', async c => {
    const ui = preparerInterface(c);
    const champ = ui.parId('saisie-recherche');
    champ.value = c.TACHES[0].intitule;
    champ.dispatchEvent(new Event('input'));
    let defile = false;
    const prototype = ui.cadre.contentWindow.Element.prototype;
    const ancienDefilement = prototype.scrollIntoView;
    prototype.scrollIntoView = function () { if (this.matches('li')) defile = true; };
    try {
      ui.parId('resultats-recherche').querySelector('button').click();
    } finally {
      prototype.scrollIntoView = ancienDefilement;
    }
    const ligne = ui.doc.getElementById(`tache-${c.TACHES[0].id}`).closest('li');
    attendre(!ui.parId('ecran-complet').hidden, 'vue complète fermée');
    attendreEgal(ui.parId('ecran-complet').dataset.vue, 'tout', 'grande liste ouverte');
    attendre(defile, 'pas de défilement');
    attendre(ligne.classList.contains('surbrillance-recherche'), 'surbrillance absente');
    const delai = [...c.delais.values()].find(delai => delai.delai === 2000);
    attendre(delai, 'durée incorrecte');
    delai.rappel();
    attendre(!ligne.classList.contains('surbrillance-recherche'), 'surbrillance persistante');
  });

  await testAsync('Recherche accueil : rendez-vous locaux, date et heure, accès sans réseau', async c => {
    c.localStorage.setItem('cap_google_rendezvous_v1', JSON.stringify({ rendezvous: [
      { titre: 'FICTIF Répétition', lieu: 'Théâtre', description: 'Éclairage', date: '2030-01-10', heure: '14:32' }
    ] }));
    const ui = preparerInterface(c);
    ui.parId('source-recherche').selectedIndex = 1;
    ui.parId('saisie-recherche').value = 'theatre';
    ui.parId('saisie-recherche').dispatchEvent(new Event('input'));
    const resultat = ui.parId('resultats-recherche').querySelector('button');
    attendre(resultat && resultat.textContent.includes('14:32') && resultat.textContent.includes('10'), 'date et heure absentes');
    resultat.click();
    attendre(ui.parId('fiche-rendez-vous').open, 'fiche non ouverte');
    attendre(ui.parId('cartes-rdv').textContent.includes('Théâtre'), 'rendez-vous non montré');
    attendreEgal(c.requetes.length, 0, 'recherche déclenche du réseau');
  });

  await testAsync('Recherche accueil : glissements ignorés depuis barre et liste', async c => {
    const ui = preparerInterface(c);
    ui.parId('saisie-recherche').value = 'introuvable';
    ui.parId('saisie-recherche').dispatchEvent(new Event('input'));
    for (const cible of [ui.parId('zone-recherche'), ui.parId('saisie-recherche'), ui.parId('resultats-recherche'), ui.parId('resultats-recherche').firstElementChild]) {
      glisser(ui, cible, 100, 300, 100, 180);
      attendre(ui.parId('ecran-complet').hidden, 'geste ouvre depuis la recherche');
    }
  });

  await testAsync('Recherche accueil : texte bloque reconnexion silencieuse', async c => {
    c.localStorage.setItem('cap_google_deja_connecte_v1', 'oui');
    const ui = preparerInterface(c, { avant(ui) { ui.parId('saisie-recherche').value = 'FICTIF en cours'; } });
    attendreEgal(c.redirections.length, 0, 'redirection pendant recherche');
    ui.visibilite(false);
    attendreEgal(c.redirections.length, 0, 'redirection au retour');
    ui.parId('saisie-recherche').value = '';
    ui.visibilite(false);
    attendreEgal(c.redirections.length, 1, 'reconnexion non rétablie après effacement');
  });

  await testAsync('Recherche accueil : aucun débordement avec résultats à 360 × 560', async c => {
    c.TACHES.splice(0, c.TACHES.length, ...Array.from({ length: 35 }, (_, index) => ({
      ...TACHES_FICTIVES[0], id: `FICTIF-${index}`, intitule: `FICTIF ${'long'.repeat(80)} ${index}`, abandonnee_le: ''
    })));
    const ui = preparerInterface(c, { largeur: 360, hauteur: 560 });
    ui.parId('saisie-recherche').value = 'fictif';
    ui.parId('saisie-recherche').dispatchEvent(new Event('input'));
    attendre(ui.doc.documentElement.scrollWidth <= 360 && ui.doc.body.scrollWidth <= 360, 'débordement horizontal');
    attendre(ui.doc.documentElement.scrollHeight <= 560 && ui.doc.body.scrollHeight <= 560, 'débordement vertical');
    const liste = ui.parId('resultats-recherche');
    attendre(liste.scrollHeight > liste.clientHeight && liste.clientHeight > 0, 'résultats non défilables');
    attendre(liste.getBoundingClientRect().bottom <= 560, 'résultats hors écran');
    attendre(liste.getBoundingClientRect().bottom <= ui.doc.querySelector('.barre-recherche').getBoundingClientRect().top, 'résultats pas au-dessus de la barre');
    attendre(liste.getBoundingClientRect().top >= ui.doc.querySelector('header.horloge').getBoundingClientRect().bottom, 'résultats sur la date');
    for (const id of ['microphone', 'ouvrir-clavier', 'ajouter', 'saisie-recherche', 'source-recherche']) {
      const rect = ui.parId(id).getBoundingClientRect();
      attendre(rect.top >= 0 && rect.bottom <= 560 && rect.height >= 48, `${id} hors écran ou trop petit`);
    }
  });

  await testAsync('Google Agenda : copie locale conserve lieu et description pour la recherche', async c => {
    c.localStorage.setItem('cap_google_agenda_v1', 'agenda-fictif');
    c.repondre = async r => reponseGoogle(r.url.pathname.endsWith('/events') ? { items: [
      { summary: 'FICTIF rendez-vous', location: 'Théâtre FICTIF', description: 'Éclairage FICTIF', start: { date: '2030-01-10' } }
    ] } : { id: 'agenda-fictif' });
    const agenda = c.agenda();
    await agenda.prochainsRendezVous();
    attendreEgal(recherche.chercherRendezVous(agenda.lireCache(), 'theatre').length, 1, 'lieu perdu');
    attendreEgal(recherche.chercherRendezVous(agenda.lireCache(), 'eclairage').length, 1, 'description perdue');
  });

  function tachesTuiles(c) {
    const modele = { ...TACHES_FICTIVES[0], parente: '', fait: false, abandonnee_le: '', echeance: '', avant_le: '', sous_categorie: '' };
    c.TACHES.splice(0, c.TACHES.length,
      { ...modele, id: 'FICTIF-T1', intitule: 'FICTIF idée en vrac', categorie: 'À trier' },
      { ...modele, id: 'FICTIF-T2', intitule: 'FICTIF autre idée', categorie: 'À trier' },
      { ...modele, id: 'FICTIF-T3', intitule: 'FICTIF accorder la guitare', categorie: 'Musique', echeance: '2020-01-01' },
      { ...modele, id: 'FICTIF-T4', intitule: 'FICTIF chapitre fini', categorie: 'Écriture', fait: true });
  }

  function dicteeQuiEntend(ui, texte) {
    ui.dictee.disponible = () => true;
    ui.dictee.enCours = () => false;
    ui.dictee.arreter = () => {};
    ui.dictee.demarrer = rappels => { rappels.surFinal(texte); rappels.surFin(); };
  }

  await testAsync('Tuiles : fixes d’abord, À trier en tête, compteurs, Tout, Ajouter et Modifier à la fin', async c => {
    tachesTuiles(c);
    const ui = preparerInterface(c);
    const tuilesAffichees = Array.from(ui.parId('tuiles').querySelectorAll('.tuile'));
    const titres = tuilesAffichees.map(t => t.querySelector('.titre-tuile').textContent);
    attendreEgal(titres.slice(0, 4), ['Dernières actions', 'Prochains rendez-vous', 'Aujourd’hui', 'Trier'], 'tuiles fixes');
    attendreEgal(titres[4], 'À trier', 'À trier pas en premier');
    attendreEgal(titres.slice(-3), ['Tout', '+ Ajouter', 'Modifier'], 'tuiles de fin');
    const compteur = titre => tuilesAffichees.find(t => t.querySelector('.titre-tuile').textContent === titre).querySelector('.compteur-tuile')?.textContent;
    attendreEgal(compteur('À trier'), '(2)', 'compteur À trier');
    attendreEgal(compteur('Musique'), '(1)', 'compteur Musique');
    attendreEgal(compteur('Écriture'), '(0)', 'tâche cochée comptée');
    attendreEgal(compteur('Trier'), '(2)', 'compteur Trier');
    attendreEgal(compteur('Aujourd’hui'), '(1)', 'retard compté');
    attendreEgal(compteur('Tout'), '(3)', 'compteur Tout');
    attendre(tuilesAffichees.filter(t => t.classList.contains('tuile-fixe')).every(t => !t.classList.contains('deplacable') && !t.querySelector('.micro-tuile')), 'tuile fixe déplaçable');
    attendre(tuilesAffichees.filter(t => t.classList.contains('tuile-categorie')).every(t => t.querySelector('.micro-tuile')), 'micro absent');
    attendre(!tuilesAffichees[4].classList.contains('deplacable'), 'À trier déplaçable');
    attendreEgal(ui.parId('ecran-complet').dataset.vue, 'tuiles', 'vue de départ');
    attendre(ui.parId('liste-taches').classList.contains('hors-vue'), 'longue liste visible sous les tuiles');
  });

  await testAsync('Tuiles : une catégorie ouvre sa liste, ‹ Tuiles revient, Tout et Aujourd’hui filtrent', async c => {
    tachesTuiles(c);
    const ui = preparerInterface(c);
    ui.parId('basculer-vue').click();
    const ouvrirTuileTitre = titre => Array.from(ui.parId('tuiles').querySelectorAll('.ouvrir-tuile'))
      .find(b => b.querySelector('.titre-tuile').textContent === titre).click();
    ouvrirTuileTitre('Musique');
    attendreEgal(ui.parId('titre-vue').textContent, 'Musique', 'titre');
    attendre(!ui.parId('retour-tuiles').hidden, 'retour caché');
    attendre(ui.parId('tuiles').classList.contains('hors-vue'), 'tuiles encore visibles');
    const intitules = () => Array.from(ui.parId('liste-taches').querySelectorAll('[data-tache]'), n => c.TACHES.find(t => t.id === n.dataset.tache)?.intitule).filter(Boolean);
    attendreEgal(intitules(), ['FICTIF accorder la guitare'], 'filtre catégorie');
    ui.parId('retour-tuiles').click();
    attendreEgal(ui.parId('ecran-complet').dataset.vue, 'tuiles', 'retour aux tuiles');
    ouvrirTuileTitre('Aujourd’hui');
    attendreEgal(intitules(), ['FICTIF accorder la guitare'], 'filtre aujourd’hui');
    ui.parId('retour-tuiles').click();
    ouvrirTuileTitre('Tout');
    attendreEgal(intitules().length, 3, 'grande liste');
    attendre(!ui.parId('basculer-archive').classList.contains('hors-vue'), 'archive absente de Tout');
    ui.parId('basculer-vue').click();
    attendreEgal(ui.parId('ecran-complet').dataset.vue, 'tuiles', 'accueil remet les tuiles');
  });

  await testAsync('Tuiles : le micro d’une tuile range la tâche dictée dans sa catégorie', async c => {
    tachesTuiles(c);
    const ui = preparerInterface(c);
    dicteeQuiEntend(ui, 'FICTIF changer les cordes');
    const pendantOriginal = ui.journalActions.pendant;
    ui.journalActions.pendant = (contexte, action) => {
      ui.journalActions.consigner({ ...contexte, fait: 'FICTIF' });
      return pendantOriginal(contexte, action);
    };
    const tuileMusique = ui.parId('tuiles').querySelector('.tuile[data-categorie="Musique"]');
    tuileMusique.querySelector('.micro-tuile').click();
    const creee = TACHES.find(t => t.intitule === 'FICTIF changer les cordes');
    attendre(creee, 'tâche non créée');
    attendreEgal(creee.categorie, 'Musique', 'catégorie de la tuile');
    attendreEgal(creee.origine, 'dictée', 'origine');
    const ligne = ui.journalActions.lireComplet().find(l => l[3].includes('Musique'));
    attendre(ligne && ligne[1] === 'micro de la tuile Musique' && ligne[2] === 'FICTIF changer les cordes', 'journal incomplet');
  });

  await testAsync('Dates : micro de tuile, échéance dite, puis question à deux boutons si Cap hésite', async c => {
    tachesTuiles(c);
    const ui = preparerInterface(c);
    const tuile = () => ui.parId('tuiles').querySelector('.tuile[data-categorie="Musique"]');
    dicteeQuiEntend(ui, 'FICTIF accorder la guitare après-demain');
    tuile().querySelector('.micro-tuile').click();
    const avecDate = TACHES.find(t => t.intitule === 'FICTIF accorder la guitare après-demain');
    attendreEgal(avecDate.echeance, comprendreDates.trouver('après-demain').date, 'échéance dite');
    attendre(!ui.parId('question-date').open, 'pas de question si la date est sûre');
    dicteeQuiEntend(ui, 'FICTIF répéter dans 8 jours');
    tuile().querySelector('.micro-tuile').click();
    const hesite = TACHES.find(t => t.intitule === 'FICTIF répéter dans 8 jours');
    attendreEgal(hesite.echeance, '', 'rien deviné');
    const question = ui.parId('question-date');
    attendre(question.open, 'question ouverte');
    const boutons = [...question.querySelectorAll('.choix-date-possible')];
    attendreEgal(boutons.length, 2, 'deux boutons');
    const attendu = comprendreDates.trouver('dans 8 jours').choix[1];
    boutons[1].click();
    attendre(!question.open, 'question fermée');
    attendreEgal(TACHES.find(t => t.id === hesite.id).echeance, attendu, 'date choisie');
  });

  test('Sous-catégories : nommée, contenu proche, sinon À classer, jamais par défaut', () => {
    const modele = { parente: '', abandonnee_le: '', categorie: 'Écriture' };
    const taches = [
      { ...modele, intitule: 'Les jardins suspendus de minuit', sous_categorie: 'Roman' },
      { ...modele, intitule: 'Relire', sous_categorie: 'Roman', parente: 'X' },
      { ...modele, intitule: 'Noter l’idée du train qui ne s’arrête jamais', sous_categorie: 'Scénarios' }
    ];
    const subs = ['Scénarios', 'Roman'];
    const t = texte => sousCategories.trouver(texte, 'Écriture', subs, taches).sous_categorie;
    attendreEgal(t('Relire le chapitre 2 des Jardins suspendus de minuit'), 'Roman', 'contenu proche');
    attendreEgal(t("J'ai une idée de scénario d'horreur"), 'Scénarios', 'nommée au singulier');
    attendreEgal(t('Aide-moi en roman à finir de relire tel chapitre'), 'Roman', 'nommée');
    attendreEgal(t('Penser à acheter des cahiers'), 'À classer', 'pas clair');
    attendreEgal(t('Commencer à écrire mon livre pour enfants'), 'À classer', 'pas de défaut');
    attendreEgal(t('Un roman ou un scénario'), 'À classer', 'deux nommées');
    attendreEgal(t('Relire le train'), 'À classer', 'un seul mot commun ne suffit pas');
    attendreEgal(sousCategories.trouver('Acheter du pain', 'Quotidien', [], taches).sous_categorie, '', 'sans sous-catégorie');
    attendreEgal(sousCategories.trouver('rien', 'Écriture', ['À classer'], taches).sous_categorie, '', 'À classer n’est pas une vraie sous-catégorie');
  });

  await testAsync('Sous-catégories : micro de la tuile Écriture, puis À classer affiché en premier sans pourcentage', async c => {
    tachesTuiles(c);
    const modele = { ...c.TACHES[0], fait: false, categorie: 'Écriture' };
    c.TACHES.push(
      { ...modele, id: 'FICTIF-T5', intitule: 'Les jardins suspendus de minuit', sous_categorie: 'Roman' },
      { ...modele, id: 'FICTIF-T6', intitule: 'Noter l’idée du train', sous_categorie: 'Scénarios' },
      { ...modele, id: 'FICTIF-T7', intitule: 'FICTIF déjà à classer', sous_categorie: 'À classer' },
      { ...modele, id: 'FICTIF-T8', intitule: 'FICTIF ancienne sans sous-catégorie', sous_categorie: '' });
    const ui = preparerInterface(c);
    const micro = () => ui.parId('tuiles').querySelector('.tuile[data-categorie="Écriture"] .micro-tuile');
    const dicter = texte => { dicteeQuiEntend(ui, texte); micro().click(); return TACHES.find(t => t.intitule === texte); };
    attendreEgal(dicter('Relire le chapitre 2 des Jardins suspendus de minuit').sous_categorie, 'Roman', 'Roman');
    attendreEgal(dicter("J'ai une idée de scénario d'horreur").sous_categorie, 'Scénarios', 'Scénarios');
    const cahiers = dicter('Penser à acheter des cahiers');
    attendreEgal(cahiers.sous_categorie, 'À classer', 'À classer');
    attendreEgal(cahiers.categorie, 'Écriture', 'reste dans Écriture');
    attendreEgal(dicter('Réécrire la scène 4').sous_categorie, 'Scénarios', 'indice « scène »');
    attendreEgal(dicter('Revoir le personnage principal').sous_categorie, 'Roman', 'indice « personnage »');
    attendreEgal(dicter('Une scène du chapitre 3').sous_categorie, 'À classer', 'deux indices : À classer');
    attendre(!ui.listesChoix.categories('Écriture').includes('À classer'), 'À classer ne devient pas une sous-catégorie à choisir');
    Array.from(ui.parId('tuiles').querySelectorAll('.ouvrir-tuile')).find(b => b.querySelector('.titre-tuile').textContent === 'Écriture').click();
    const titres = Array.from(ui.parId('liste-taches').querySelectorAll('.sous-categorie h3'), h => h.firstChild.textContent);
    attendreEgal(titres[0], 'À classer', 'À classer en premier');
    attendre(!ui.parId('liste-taches').querySelector('.sous-categorie h3').querySelector('.pourcentage'), 'pas de pourcentage');
    const sections = Array.from(ui.parId('liste-taches').querySelectorAll('.sous-categorie'));
    attendre(sections.length && sections.every(section => section.querySelector('h3')), 'aucune case en vrac sans intitulé');
    attendreEgal(titres.filter(titre => titre === 'À classer').length, 1, 'un seul groupe À classer');
    const aClasser = sections.find(section => section.querySelector('h3').firstChild.textContent === 'À classer');
    attendre(aClasser.textContent.includes('FICTIF ancienne sans sous-catégorie'), 'ancienne tâche sans sous-catégorie sous « À classer »');
  });

  await testAsync('Trier : + Ajouter crée la catégorie et y range la tâche, Modifier la retire sans perte, Annuler la ramène', async c => {
    tachesTuiles(c);
    const ui = preparerInterface(c);
    const trier = ui.parId('mode-trier');
    const liste = ui.parId('fenetre-liste');
    Array.from(ui.parId('tuiles').querySelectorAll('.ouvrir-tuile')).find(b => b.querySelector('.titre-tuile').textContent === 'Trier').click();
    attendre(trier.querySelector('.outils-tri'), 'boutons discrets absents');
    boutonTexte(trier, '+ Ajouter').click();
    attendre(liste.open, 'formulaire de création ouvert');
    liste.querySelector('#nom-nouvel-element').value = 'FICTIF Jardin';
    liste.querySelector('form').requestSubmit();
    attendre(!liste.open, 'formulaire fermé');
    attendreEgal(c.TACHES.find(t => t.id === 'FICTIF-T1').categorie, 'FICTIF Jardin', 'tâche rangée tout de suite');
    attendre(trier.open, 'Trier reste ouvert');
    attendreEgal(trier.querySelector('.tache-a-trier').textContent, 'FICTIF autre idée', 'tâche suivante');
    attendre(Array.from(trier.querySelectorAll('.choix-tri'), b => b.textContent).includes('FICTIF Jardin'), 'nouvelle catégorie proposée');
    boutonTexte(trier, 'Modifier').click();
    attendre(liste.open, 'Modifier ouvert');
    const caseJardin = Array.from(liste.querySelectorAll('input[type="checkbox"]')).find(i => i.value === 'FICTIF Jardin');
    caseJardin.checked = true;
    caseJardin.dispatchEvent(new Event('change'));
    boutonTexte(liste, 'Retirer (1)').click();
    attendre(!ui.listesChoix.categories().includes('FICTIF Jardin'), 'catégorie retirée');
    attendreEgal(c.TACHES.find(t => t.id === 'FICTIF-T1').categorie, 'FICTIF Jardin', 'la tâche ne disparaît pas');
    boutonTexte(ui.parId('annulation-liste'), 'Annuler').click();
    attendre(ui.listesChoix.categories().includes('FICTIF Jardin'), 'Annuler ramène la catégorie');
    liste.close();
    await new Promise(r => setTimeout(r, 0));
    attendre(Array.from(trier.querySelectorAll('.choix-tri'), b => b.textContent).includes('FICTIF Jardin'), 'Trier mis à jour après fermeture');
    trier.close();
  });

  test('Annuler : phrases reconnues, une seule fois, délai de 8 secondes, vibration', () => {
    for (const phrase of ['Annule', 'Annule.', 'annule ça', 'Annuler', 'Cap, annule la dernière action', 'Annule ce que tu viens de faire'])
      attendre(annulation.estDemande(phrase), `reconnue : ${phrase}`);
    for (const phrase of ['Annuler le rendez-vous chez le dentiste', 'Annule ma réunion de lundi', 'Appeler Annie'])
      attendre(!annulation.estDemande(phrase), `pas une annulation : ${phrase}`);
    let defaits = 0;
    let retires = 0;
    annulation.proposer({ annuler: () => { defaits += 1; }, messageApres: 'FICTIF défait', retirer: () => { retires += 1; } });
    attendreEgal(annulation.annulerDerniere(), 'FICTIF défait', 'message');
    attendreEgal(annulation.annulerDerniere(), '', 'une seule fois');
    attendreEgal([defaits, retires], [1, 1], 'défait et bouton retiré');
    const vraiNow = Date.now;
    try {
      annulation.proposer({ annuler: () => { defaits += 1; } });
      const depart = vraiNow();
      Date.now = () => depart + 8001;
      attendreEgal(annulation.annulerDerniere(), '', 'trop tard');
      Date.now = vraiNow;
      annulation.proposer({ annuler: () => { defaits += 1; } });
      annulation.garderPendantEcoute();
      Date.now = () => depart + 12000;
      attendreEgal(annulation.annulerDerniere(), 'C’est annulé.', 'le micro laisse le temps de dire Annule');
    } finally {
      Date.now = vraiNow;
    }
    attendreEgal(defaits, 2, 'rien défait après le délai');
    const vraiVibrer = navigator.vibrate;
    const durees = [];
    try {
      Object.defineProperty(navigator, 'vibrate', { value: duree => { durees.push(duree); return true; }, configurable: true });
      Date.now = () => vraiNow() + 60000;
      abandonner(creerTache({ intitule: 'FICTIF vibration', origine: 'ajout à la main' }).id);
      attendreEgal(durees, [30], 'vibration courte à chaque action');
    } finally {
      Date.now = vraiNow;
      Object.defineProperty(navigator, 'vibrate', { value: vraiVibrer, configurable: true });
    }
  });

  test('Annuler partout : ajout, case cochée, abandon, puis « Annule » au clavier et à la voix', () => {
    const statut = document.getElementById('statut');
    const tache = tacheInterface('FICTIF annuler partout');
    attendre(statut.querySelector('.annuler-dictee'), 'Annuler après ajout au formulaire');
    const nombre = TACHES.length;
    const cocherCase = () => {
      const caseTache = document.getElementById(`tache-${tache.id}`);
      caseTache.checked = !caseTache.checked;
      caseTache.dispatchEvent(new Event('change'));
    };
    cocherCase();
    attendre(tache.fait, 'cochée');
    statut.querySelector('.annuler-dictee').click();
    attendre(!tache.fait, 'Annuler décoche');
    attendre(!statut.querySelector('.annuler-dictee'), 'bouton retiré après usage');
    cocherCase();
    document.getElementById('ouvrir-clavier').click();
    document.getElementById('saisie-demande').value = 'Annule';
    document.getElementById('formulaire-demande').requestSubmit();
    if (document.getElementById('clavier').open) document.getElementById('clavier').close();
    attendre(!tache.fait, '« Annule » au clavier décoche');
    document.querySelector(`[data-tache="${tache.id}"] .options-tache`).click();
    document.getElementById('abandonner-tache').click();
    document.getElementById('confirmer-abandon').click();
    attendre(tache.abandonnee_le, 'abandonnée');
    attendre(statut.querySelector('.annuler-dictee'), 'Annuler après abandon');
    const sauve = { ...dictee };
    try {
      dictee.disponible = () => true;
      dictee.enCours = () => false;
      dictee.demarrer = rappels => { rappels.surFinal('Annule ça'); rappels.surFin?.(); };
      document.getElementById('microphone').click();
      attendreEgal(tache.abandonnee_le, '', '« Annule » à la voix remet la tâche');
      document.getElementById('microphone').click();
      attendre(/plus rien à annuler/.test(statut.textContent), 'rien à annuler deux fois');
    } finally {
      Object.assign(dictee, sauve);
    }
    attendreEgal(TACHES.length, nombre, 'aucune tâche « Annule » créée, rien effacé');
    abandonner(tache.id);
  });

  await (async () => {
    const nom = 'Mode conversation : appui long, écoute continue, « stop », bouton Arrêter';
    const sauve = { ...dictee };
    const micro = document.getElementById('microphone');
    const bandeau = document.getElementById('bandeau-live');
    const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
    try {
      const nombre = TACHES.length;
      const phrases = ['Ajoute dans Quotidien : FICTIF live un', 'Ajoute dans Quotidien : FICTIF live deux', 'stop'];
      let ecoutes = 0;
      dictee.disponible = () => true;
      dictee.enCours = () => false;
      dictee.arreter = () => {};
      dictee.demarrer = rappels => {
        ecoutes += 1;
        const phrase = phrases.shift();
        setTimeout(() => { if (phrase) rappels.surFinal(phrase); rappels.surFin(); }, 10);
      };
      micro.dispatchEvent(new Event('pointerdown'));
      await pause(500);
      micro.dispatchEvent(new Event('pointerup'));
      attendre(bandeau.hidden && ecoutes === 0, 'appui court : pas de mode conversation');
      micro.dispatchEvent(new Event('pointerdown'));
      await pause(2100);
      attendre(!bandeau.hidden && micro.classList.contains('live'), 'appui long : mode conversation visible');
      micro.click();
      attendre(!bandeau.hidden, 'le clic qui suit l’appui long n’arrête pas le mode');
      await pause(1200);
      const ajoutees = TACHES.slice(nombre).map(tache => tache.intitule);
      attendreEgal(ajoutees, ['FICTIF live un', 'FICTIF live deux'], 'deux phrases traitées sans rappuyer');
      attendre(bandeau.hidden && !micro.classList.contains('live'), '« stop » arrête le mode conversation');
      attendre(document.getElementById('statut').textContent.includes('Mode conversation arrêté'), 'arrêt annoncé');
      phrases.push();
      micro.dispatchEvent(new Event('pointerdown'));
      await pause(2100);
      attendre(!bandeau.hidden, 'mode relancé');
      document.getElementById('arreter-live').click();
      attendre(bandeau.hidden, 'bouton Arrêter');
      TACHES.slice(nombre).forEach(tache => abandonner(tache.id));
      resultats.push({ nom, ok: true, erreur: '' });
    } catch (erreur) {
      resultats.push({ nom, ok: false, erreur: String(erreur && erreur.message ? erreur.message : erreur) });
    } finally {
      document.getElementById('arreter-live').click();
      Object.assign(dictee, sauve);
    }
  })();

  test('Cerveau préparé : range seulement ce qui est nommé, intitulé mot pour mot, réponse courte', () => {
    const debut = traiterDemande({ texte: 'Ajoute dans Écriture : relire le chapitre 2 FICTIF', source: 'micro' });
    attendreEgal([debut.type, debut.tache.intitule, debut.tache.categorie, debut.tache.sous_categorie, debut.tache.origine],
      ['tache', 'relire le chapitre 2 FICTIF', 'Écriture', 'Roman', 'dictée'], 'catégorie nommée au début, indice « chapitre »');
    attendreEgal(debut.parole, 'C’est noté dans Écriture, Roman.', 'réponse parlée');
    const flou = traiterDemande({ texte: 'Ajoute dans Écriture : acheter un carnet FICTIF', source: 'micro' });
    attendreEgal(flou.tache.sous_categorie, 'À classer', 'rien d’évident : À classer');
    const scenario = traiterDemande({ texte: 'J’ai une idée de scénario d’horreur FICTIF', source: 'micro' });
    attendreEgal([scenario.tache.intitule, scenario.tache.categorie, scenario.tache.sous_categorie],
      ['J’ai une idée de scénario d’horreur FICTIF', 'Écriture', 'Scénarios'], 'sous-catégorie nommée dans la phrase');
    const fin = traiterDemande({ texte: 'Ajoute rappeler Paul FICTIF dans Quotidien Courses', source: 'saisie' });
    attendreEgal([fin.tache.intitule, fin.tache.categorie, fin.tache.sous_categorie, fin.message],
      ['rappeler Paul FICTIF', 'Quotidien', 'Courses', 'Ajoutée dans Quotidien › Courses : « rappeler Paul FICTIF »'], 'désignation à la fin');
    const liste = traiterDemande({ texte: 'Ajoute acheter du pain FICTIF à ma to-do', source: 'saisie' });
    attendreEgal([liste.tache.intitule, liste.tache.categorie, liste.message],
      ['acheter du pain FICTIF', 'À trier', 'Ajoutée dans À trier : « acheter du pain FICTIF »'], 'à ma to-do');
    for (const texte of ['Note de frais FICTIF', 'Penser à acheter des cahiers FICTIF', 'Ajoute du sel FICTIF']) {
      const resultat = traiterDemande({ texte, source: 'saisie' });
      attendreEgal([resultat.tache.intitule, resultat.tache.categorie], [texte, 'À trier'], `rien de nommé : ${texte}`);
    }
    const date = traiterDemande({ texte: 'Ajoute dans Musique : mixer le titre FICTIF dans deux semaines', source: 'micro' });
    const attendue = new Date();
    attendue.setDate(attendue.getDate() + 14);
    attendreEgal([date.tache.categorie, date.tache.echeance],
      ['Musique', `${attendue.getFullYear()}-${String(attendue.getMonth() + 1).padStart(2, '0')}-${String(attendue.getDate()).padStart(2, '0')}`],
      'date dite naturellement');
  });

  test('Cerveau préparé : indices évidents (titre du roman, scène, chapitre), sinon À trier', () => {
    reinitialiser();
    const sous = listesChoix.categories('Écriture');
    attendre(sous.includes('Roman') && sous.includes('Scénarios'), `sous-catégories fictives : ${sous.join(', ')}`);
    const roman = traiterDemande({ texte: 'Relire le chapitre 2 des Jardins suspendus de minuit', source: 'micro' });
    attendreEgal([roman.tache.intitule, roman.tache.categorie, roman.tache.sous_categorie],
      ['Relire le chapitre 2 des Jardins suspendus de minuit', 'Écriture', 'Roman'], 'titre du roman');
    const titre = traiterDemande({ texte: 'Relire les jardins suspendus de minuit FICTIF', source: 'micro' });
    attendreEgal([titre.tache.categorie, titre.tache.sous_categorie], ['Écriture', 'Roman'], 'titre seul');
    const scene = traiterDemande({ texte: 'Réécrire la scène 4', source: 'micro' });
    attendreEgal([scene.tache.intitule, scene.tache.categorie, scene.tache.sous_categorie], ['Réécrire la scène 4', 'Écriture', 'Scénarios'], 'scène');
    const dialogues = traiterDemande({ texte: 'Corriger les dialogues FICTIF', source: 'saisie' });
    attendreEgal(dialogues.tache.sous_categorie, 'Scénarios', 'dialogues au pluriel');
    const deux = traiterDemande({ texte: 'Une scène du chapitre 3 FICTIF', source: 'micro' });
    attendreEgal([deux.tache.categorie, deux.tache.sous_categorie], ['Écriture', 'À classer'], 'deux indices : À classer');
    const rien = traiterDemande({ texte: 'Scener les arbres FICTIF', source: 'micro' });
    attendreEgal(rien.tache.categorie, 'À trier', 'mot voisin ignoré');
  });

  await testAsync('Dernières actions : toucher une ligne ouvre la liste sur la tâche', async c => {
    tachesTuiles(c);
    const tache = c.TACHES.find(item => !item.parente && !item.fait && !item.abandonnee_le);
    c.localStorage.setItem('cap_journal_actions_v1', JSON.stringify([
      { heure: new Date().toISOString(), type: 'ajout', texte: tache.intitule, id: tache.id },
      { heure: new Date().toISOString(), type: 'ajout', texte: 'FICTIF tâche disparue', id: 'FICTIF-absente' }
    ]));
    const ui = preparerInterface(c);
    const lignes = ui.parId('liste-actions').querySelectorAll('li');
    attendreEgal(lignes.length, 2, 'deux lignes');
    attendre(!lignes[1].querySelector('button'), 'tâche introuvable : simple texte');
    const bouton = lignes[0].querySelector('button.lien-action');
    attendre(bouton && bouton.textContent.includes(tache.intitule), 'ligne cliquable');
    bouton.click();
    const ligne = ui.parId('liste-taches').querySelector(`[data-tache="${tache.id}"]`);
    attendre(ligne && ligne.classList.contains('surbrillance-recherche'), 'tâche surlignée dans la liste');
    attendreEgal(ui.doc.activeElement, ligne, 'tâche mise en avant');
    try {
      journalActions.noter('ajout', 'FICTIF avec id', 'FICTIF-id-1');
      const premiere = journalActions.lire()[0];
      attendreEgal([premiere.texte, premiere.id], ['FICTIF avec id', 'FICTIF-id-1'], 'id gardé');
    } finally {
      localStorage.removeItem('cap_journal_actions_v1');
    }
  });

  test('Cerveau préparé : deux catégories citées, une seule question, puis la réponse range la tâche', () => {
    const avant = TACHES.length;
    const texte = 'Idée FICTIF entre musique et écriture';
    const question = traiterDemande({ texte, source: 'micro' });
    attendreEgal(question.type, 'question', 'question posée');
    attendre(/^Je la range dans (Musique|Écriture) ou dans (Musique|Écriture) \?$/.test(question.message)
      && question.message.includes('Musique') && question.message.includes('Écriture'), `question courte : ${question.message}`);
    attendreEgal(TACHES.length, avant, 'rien créé avant la réponse');
    const reponse = traiterDemande({ texte: 'Écriture', source: 'micro' });
    attendreEgal([reponse.tache.intitule, reponse.tache.categorie], [texte, 'Écriture'], 'rangée après la réponse');
    traiterDemande({ texte, source: 'micro' });
    const aTrier = traiterDemande({ texte: 'À trier', source: 'micro' });
    attendreEgal([aTrier.tache.intitule, aTrier.tache.categorie], [texte, 'À trier'], 'réponse « À trier »');
    traiterDemande({ texte, source: 'micro' });
    const autre = traiterDemande({ texte: 'Arroser FICTIF', source: 'micro' });
    attendreEgal([autre.tache.intitule, autre.tache.categorie, cerveau.questionEnAttente()], ['Arroser FICTIF', 'À trier', false],
      'une autre demande fait oublier la question');
  });

  test('Cerveau : frontière des actions, action inconnue refusée, rien de supprimé', () => {
    const avant = TACHES.length;
    attendreErreur(() => actionsCap.executer('supprimer_tout', {}), 'ne sait pas');
    attendreErreur(() => actionsCap.executer('ajouter_tache', { intitule: 'FICTIF', categorie: 'Catégorie inventée FICTIF' }), 'n’existe pas');
    attendreErreur(() => actionsCap.executer('ajouter_tache', { intitule: 'FICTIF', categorie: 'Musique', sous_categorie: 'Inventée FICTIF' }), 'n’existe pas');
    cerveau.enregistrerFournisseur('essai', { nom: 'essai', payant: false, comprendre: () => ({ type: 'action', action: 'supprimer_tout' }) });
    try {
      cerveau.choisirFournisseur('essai');
      const resultat = traiterDemande({ texte: 'FICTIF efface tout', source: 'saisie' });
      attendreEgal([resultat.type, resultat.message], ['question', 'Je n’ai pas compris. Tu peux redire ta demande autrement ?'], 'pas compris');
    } finally {
      cerveau.choisirFournisseur('auto');
    }
    attendreEgal(TACHES.length, avant, 'aucune tâche créée ni retirée');
    attendreEgal(cerveau.fournisseurActif(), 'prepare', 'réponses préparées par défaut');
  });

  await (async () => {
    const nom = 'Cerveau : modèle interchangeable en ligne, limite de 60 échanges et alerte à 50';
    try {
      reinitialiser();
      const cle = 'cap_echanges_ia_v1';
      cerveau.enregistrerFournisseur('essai-en-ligne', {
        nom: 'essai', payant: true,
        comprendre: () => Promise.resolve({ type: 'action', action: 'ajouter_tache',
          parametres: { intitule: 'FICTIF en ligne', categorie: 'Quotidien', sous_categorie: 'Maison' } })
      });
      try {
        cerveau.choisirFournisseur('essai-en-ligne');
        localStorage.setItem(cle, JSON.stringify({ jour: dateDuJour(), nombre: 49 }));
        const enCours = traiterDemande({ texte: 'FICTIF en ligne', source: 'saisie' });
        attendreEgal(enCours.type, 'reflexion', 'réponse attendue');
        const fini = await enCours.suite;
        attendreEgal([fini.tache.intitule, fini.tache.categorie, fini.tache.sous_categorie], ['FICTIF en ligne', 'Quotidien', 'Maison'], 'tâche rangée');
        attendre(fini.message.includes('Attention : 50 échanges'), `alerte à 50 : ${fini.message}`);
        localStorage.setItem(cle, JSON.stringify({ jour: dateDuJour(), nombre: 60 }));
        const limite = traiterDemande({ texte: 'FICTIF limite', source: 'saisie' });
        attendreEgal([limite.type, limite.tache.categorie], ['tache', 'À trier'], 'réponses préparées à la limite');
        attendre(limite.message.includes('J’ai atteint ma limite pour aujourd’hui'), `limite annoncée : ${limite.message}`);
        localStorage.setItem(cle, JSON.stringify({ jour: '2000-01-01', nombre: 60 }));
        attendreEgal([limiteIA.utilises(), limiteIA.peutEchanger()], [0, true], 'nouveau jour');
      } finally {
        cerveau.choisirFournisseur('auto');
        localStorage.removeItem(cle);
      }
      resultats.push({ nom, ok: true, erreur: '' });
    } catch (erreur) {
      resultats.push({ nom, ok: false, erreur: String(erreur && erreur.message ? erreur.message : erreur) });
    }
  })();

  test('Limite IA réglable par Max, alerte avant la limite, dépense du mois', () => {
    try {
      attendreEgal([limiteIA.maximum(), limiteIA.seuilAlerte()], [60, 50], 'réglage par défaut');
      attendreEgal(limiteIA.definirMaximum('100'), 100, 'limite changée');
      attendreEgal([limiteIA.maximum(), limiteIA.seuilAlerte()], [100, 83], 'nouvelle limite et alerte');
      for (const mauvais of ['0', '-3', '2.5', 'beaucoup', '5000']) attendreErreur(() => limiteIA.definirMaximum(mauvais), 'entier');
      attendreEgal(limiteIA.maximum(), 100, 'mauvaise valeur refusée sans rien changer');
      localStorage.setItem('cap_echanges_ia_v1', JSON.stringify({ jour: dateDuJour(), nombre: 99 }));
      const dernier = limiteIA.compter();
      attendreEgal([dernier.nombre, dernier.restants, limiteIA.peutEchanger()], [100, 0, false], 'limite atteinte');
      attendre(dernier.alerte.includes('dernier échange'), `prévenu : ${dernier.alerte}`);
      attendreEgal(limiteIA.depenseDuMois(), 0, 'rien dépensé');
      const euros = limiteIA.ajouterDepense(1000000, 0);
      attendre(Math.abs(euros - 0.92) < 1e-9 && Math.abs(limiteIA.depenseDuMois() - 0.92) < 1e-9, `dépense : ${euros}`);
      localStorage.setItem('cap_depense_ia_v1', JSON.stringify({ mois: '2000-01', euros: 5 }));
      attendreEgal(limiteIA.depenseDuMois(), 0, 'nouveau mois');
      localStorage.removeItem('cap_echanges_ia_v1');
      attendreEgal(limiteIA.plafondMensuel(), 4, 'plafond du mois par défaut : 4 € (crédit de 5 dollars)');
      attendreEgal(limiteIA.definirPlafond('2,50'), 2.5, 'plafond réglé par Max, virgule acceptée');
      for (const mauvais of ['0', '-1', 'cher', '2,555', '5000']) attendreErreur(() => limiteIA.definirPlafond(mauvais), 'euros');
      attendreEgal([limiteIA.plafondMensuel(), limiteIA.maximum()], [2.5, 100], 'mauvais plafond refusé, limite du jour gardée');
      localStorage.setItem('cap_depense_ia_v1', JSON.stringify({ mois: dateDuJour().slice(0, 7), euros: 2.1 }));
      attendre(limiteIA.peutEchanger() && limiteIA.compter().alerte.includes('plafond de 2,50 €'), 'prévenu à 80 % du plafond');
      localStorage.setItem('cap_depense_ia_v1', JSON.stringify({ mois: dateDuJour().slice(0, 7), euros: 2.5 }));
      attendre(!limiteIA.peutEchanger() && limiteIA.raisonArret().includes('plafond de dépense du mois'), 'arrêt net au plafond');
    } finally {
      ['cap_echanges_ia_v1', 'cap_reglages_ia_v1', 'cap_depense_ia_v1'].forEach(nom => localStorage.removeItem(nom));
    }
  });

  test('Clé de l’IA : vérifiée, gardée sur le téléphone, jamais affichée en entier', () => {
    try {
      attendreEgal([cleIA.presente(), cleIA.apercu()], [false, ''], 'pas de clé au départ');
      attendreEgal(cerveau.fournisseurActif(), 'prepare', 'sans clé : réponses préparées');
      for (const mauvaise of ['', 'bonjour', 'sk-ant-court', 'sk-ant-FICTIF avec des espaces dedans 0000']) {
        attendreErreur(() => cleIA.enregistrer(mauvaise), 'Rien n’a été enregistré');
      }
      attendreEgal(cleIA.presente(), false, 'mauvaise clé refusée');
      cleIA.enregistrer('  sk-ant-FICTIF-0000000000000000000000abcd  ');
      attendreEgal([cleIA.lire(), cleIA.apercu()], ['sk-ant-FICTIF-0000000000000000000000abcd', '…abcd'], 'clé gardée, aperçu court');
      attendreEgal(cerveau.fournisseurActif(), 'claude', 'avec clé : Claude');
      cleIA.retirer();
      attendreEgal([cleIA.presente(), cerveau.fournisseurActif()], [false, 'prepare'], 'clé retirée');
    } finally {
      cleIA.retirer();
    }
  });

  await (async () => {
    const nom = 'Claude : consignes BROUILLON jamais envoyées, dialogue, action mot pour mot, clé seulement dans l’en-tête';
    const vraiFetch = window.fetch;
    const CLE_FICTIVE = 'sk-ant-FICTIF-0000000000000000000000wxyz';
    const envois = [];
    let consignes = 'BROUILLON : pas encore validé par Max.\nTu es Cap FICTIF.';
    let reponses = [];
    let lecturesFiche = 0;
    window.fetch = (adresse, options = {}) => {
      if (adresse === REGLAGES_IA.fichier_consignes) {
        lecturesFiche += 1;
        if (consignes === null) return Promise.resolve({ ok: false, status: 404, text: () => Promise.resolve('') });
        return Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve(consignes) });
      }
      if (adresse !== REGLAGES_IA.adresse) return Promise.reject(new Error('Hors de ce test.'));
      envois.push({ adresse, options });
      const suivante = reponses.shift();
      return Promise.resolve({ ok: suivante.statut === 200, status: suivante.statut, json: () => Promise.resolve(suivante.corps) });
    };
    try {
      reinitialiser();
      cleIA.enregistrer(CLE_FICTIVE);
      cerveauClaude.oublier();
      attendreEgal(cerveau.fournisseurActif(), 'claude', 'Claude choisi avec la clé');
      const brouillon = await traiterDemande({ texte: 'Ajoute dans Quotidien : FICTIF brouillon', source: 'saisie' }).suite;
      attendreEgal([brouillon.type, brouillon.tache.categorie, envois.length], ['tache', 'Quotidien', 0], 'brouillon : rien envoyé, réponses préparées');
      attendre(brouillon.message.includes('pas encore validée par Max') && brouillon.message.includes('Réponse préparée'), `prévenu : ${brouillon.message}`);
      attendreEgal(limiteIA.utilises(), 0, 'échange non compté');
      attendre((await cerveauClaude.etatConsignes()).includes('pas encore validé'), 'état des consignes');

      consignes = null;
      cerveauClaude.oublier();
      const sansFiche = await traiterDemande({ texte: 'Ajoute dans Quotidien : FICTIF sans fiche', source: 'saisie' }).suite;
      attendreEgal([sansFiche.type, envois.length], ['tache', 0], 'fiche introuvable : Claude jamais appelé');
      attendre(sansFiche.message.includes('pas pu lire ma fiche'), `prévenu : ${sansFiche.message}`);

      localStorage.removeItem('cap_consignes_v1');
      let changements = 0;
      const surChangement = () => { changements += 1; };
      window.addEventListener('cap-consignes-changees', surChangement);
      consignes = 'Tu es Cap FICTIF.';
      cerveauClaude.oublier();
      attendreEgal(await cerveauClaude.etatConsignes(), 'pret', 'consignes validées');
      const info = cerveauClaude.infoConsignes();
      attendre(info && /^[0-9a-f]{8}$/.test(info.empreinte) && info.lue_le && info.version_du, 'date de lecture et version retenues');
      consignes = 'Tu es Cap FICTIF, version 2.';
      cerveauClaude.oublier();
      await cerveauClaude.precharger();
      attendre(changements === 1 && cerveauClaude.infoConsignes().empreinte !== info.empreinte, 'Max prévenu quand la fiche change');
      cerveauClaude.oublier();
      await cerveauClaude.precharger();
      window.removeEventListener('cap-consignes-changees', surChangement);
      attendreEgal(changements, 1, 'même fiche relue : pas de nouvelle alerte');
      consignes = 'Tu es Cap FICTIF.';
      cerveauClaude.oublier();
      journalIA.effacer();
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'Salut Max, ça va bien. Et toi ?' }], usage: { input_tokens: 1000, output_tokens: 20 } } });
      const conversation = await traiterDemande({ texte: 'Salut Cap, ça va ?', source: 'micro' }).suite;
      attendreEgal([conversation.type, conversation.message, conversation.parole],
        ['reponse', 'Salut Max, ça va bien. Et toi ?', 'Salut Max, ça va bien. Et toi ?'], 'vraie conversation');
      const envoi = envois[0];
      const corps = JSON.parse(envoi.options.body);
      attendreEgal([envoi.adresse, envoi.options.method, envoi.options.headers['x-api-key'], envoi.options.headers['anthropic-version'],
        envoi.options.headers['anthropic-dangerous-direct-browser-access']],
        [REGLAGES_IA.adresse, 'POST', CLE_FICTIVE, '2023-06-01', 'true'], 'en-têtes');
      attendre(!envoi.options.body.includes(CLE_FICTIVE), 'la clé n’est jamais dans le corps');
      attendreEgal([corps.model, corps.messages.length, corps.messages[0].content], [REGLAGES_IA.modele, 1, 'Salut Cap, ça va ?'], 'message envoyé');
      attendre(/^Nous sommes le \S+ \d{1,2} \S+ \d{4}, il est \d{1,2} h \d{2}\.\nTu es Cap FICTIF\./.test(corps.system) && corps.system.includes('Quotidien'),
        `date et heure, puis consignes et catégories envoyées : ${corps.system.slice(0, 80)}`);
      attendreEgal([corps.tools[0].name, corps.tools[0].input_schema.required], ['ajouter_tache', ['intitule']], 'outils du catalogue');
      attendreEgal(limiteIA.utilises(), 1, 'échange compté');
      attendre(limiteIA.depenseDuMois() > 0, 'dépense comptée');

      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'C’est noté dans Quotidien, Maison.' },
        { type: 'tool_use', name: 'ajouter_tache', input: { intitule: 'arroser les plantes FICTIF', categorie: 'Quotidien', sous_categorie: 'Maison' } }],
        usage: { input_tokens: 1000, output_tokens: 40 } } });
      const action = await traiterDemande({ texte: 'Pense à arroser les plantes FICTIF', source: 'micro' }).suite;
      attendreEgal([action.type, action.tache.intitule, action.tache.categorie, action.tache.sous_categorie, action.parole],
        ['tache', 'arroser les plantes FICTIF', 'Quotidien', 'Maison', 'C’est noté dans Quotidien, Maison.'], 'action exécutée et dite');
      attendreEgal(JSON.parse(envois[1].options.body).messages.length, 3, 'la conversation est retenue');
      const journal = journalIA.lire();
      attendreEgal([journal.length, journal[1].dit, journal[1].repondu, journal[0].dit], [2, 'Salut Cap, ça va ?', 'Salut Max, ça va bien. Et toi ?', 'Pense à arroser les plantes FICTIF'], 'historique de l’IA');
      attendre(journal[0].action.includes('arroser les plantes FICTIF'), `action notée : ${journal[0].action}`);
      attendre(!localStorage.getItem('cap_journal_ia_v1').includes(CLE_FICTIVE), 'la clé n’est jamais dans l’historique');

      let avant = TACHES.length;
      reponses.push({ statut: 200, corps: { content: [{ type: 'tool_use', name: 'ajouter_tache', input: { intitule: 'Acheter du lait FICTIF' } }] } });
      const reformulee = await traiterDemande({ texte: 'Il faudrait du lait FICTIF', source: 'micro' }).suite;
      attendreEgal([reformulee.type, TACHES.length], ['proposition', avant], 'reformulation : proposition, rien créé avant le oui');
      attendre(reformulee.message.startsWith('Je mets « Acheter du lait FICTIF » dans À trier') && reformulee.message.endsWith('ça te va ?')
        && !reformulee.message.includes('répéter'), reformulee.message);
      const envoisProposition = envois.length;
      const oui = traiterDemande({ texte: 'Oui, vas-y', source: 'micro' });
      attendreEgal([oui.type, oui.tache.intitule, TACHES.length, envois.length], ['tache', 'Acheter du lait FICTIF', avant + 1, envoisProposition], 'oui : rangé par Cap, sans nouvel appel');
      attendre(oui.tache.note.includes('Dit par Max : « ') && oui.tache.note.includes('Il faudrait du lait FICTIF'), `mots exacts gardés : ${oui.tache.note}`);
      abandonner(oui.tache.id);
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'Bonne idée.' },
        { type: 'tool_use', name: 'proposer_rangement', input: { intitule: 'Un homme tombe amoureux FICTIF', categorie: 'Inconnue FICTIF', raison: 'c’est une histoire.' } }] } });
      const idee = await traiterDemande({ texte: 'J’ai une idée, un homme qui tombe amoureux FICTIF', source: 'micro' }).suite;
      attendre(idee.type === 'proposition' && idee.message.includes('À trier') && !idee.message.includes('Bonne idée'), `catégorie inconnue : À trier proposé, Cap formule : ${idee.message}`);
      const nombreAvantNon = TACHES.length;
      const non = traiterDemande({ texte: 'Non merci', source: 'micro' });
      attendreEgal([non.type, non.message, TACHES.length], ['reponse', 'D’accord, je ne range rien.', nombreAvantNon], 'non : rien rangé');
      attendre(JSON.parse(envois[envois.length - 1].options.body).system.includes('Ne demande jamais à Max de répéter ses mots'), 'consigne : jamais répéter');
      avant = TACHES.length;
      reponses.push({ statut: 200, corps: { content: [
        { type: 'tool_use', name: 'ajouter_tache', input: { intitule: 'un FICTIF' } },
        { type: 'tool_use', name: 'ajouter_tache', input: { intitule: 'deux FICTIF' } }] } });
      const plusieurs = await traiterDemande({ texte: 'Ajoute un FICTIF et deux FICTIF', source: 'micro' }).suite;
      attendreEgal([plusieurs.type, TACHES.length], ['reponse', avant], 'plusieurs actions d’un coup refusées');
      reponses.push({ statut: 200, corps: { content: [{ type: 'tool_use', name: 'supprimer_tout', input: { intitule: 'tout FICTIF' } }] } });
      const inconnue = await traiterDemande({ texte: 'Efface tout FICTIF', source: 'micro' }).suite;
      attendreEgal([inconnue.type, TACHES.length], ['question', avant], 'action inconnue refusée');

      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'Le numéro de ton médecin est le 01 23 45 67 89.' }] } });
      const invente = await traiterDemande({ texte: 'Quel est le numéro de mon médecin FICTIF ?', source: 'micro' }).suite;
      attendreEgal([invente.type, invente.message], ['reponse', 'Je ne sais pas : tu ne m’as jamais donné ce numéro.'], 'numéro inconnu : « je ne sais pas », jamais inventé');
      attendre(JSON.parse(envois[envois.length - 1].options.body).system.includes('réponds « Je ne sais pas. »'), 'consigne « je ne sais pas » envoyée à chaque échange');
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'Je ne sais pas.' }] } });
      const sait = await traiterDemande({ texte: 'Et le numéro de la pharmacie FICTIF ?', source: 'micro' }).suite;
      attendreEgal(sait.message, 'Je ne sais pas.', 'Claude qui dit ne pas savoir : réponse gardée');
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'C’est le 06 11 22 33 44.' }] } });
      const donne = await traiterDemande({ texte: 'Retiens le 0611223344 pour le garage FICTIF, et redis-le moi', source: 'micro' }).suite;
      attendreEgal(donne.message, 'C’est le 06 11 22 33 44.', 'numéro donné par Max : répété sans souci');
      cerveauClaude.nouvelleConversation();
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'Bonjour Max.' }] } });
      await traiterDemande({ texte: 'Bonjour FICTIF', source: 'micro' }).suite;
      attendreEgal(JSON.parse(envois[envois.length - 1].options.body).messages.length, 1, 'nouvelle ouverture : l’IA repart de zéro');

      const aFaire = TACHES.filter(tache => !tache.fait && !tache.abandonnee_le).length;
      const empreinteTaches = JSON.stringify(TACHES);
      reponses.push({ statut: 200, corps: { content: [{ type: 'tool_use', id: 'lecture1', name: 'lire_taches', input: { etat: 'a_faire' } }] } });
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: `Tu as ${aFaire} tâches à faire.` }] } });
      const envoisLecture = envois.length;
      const compte = await traiterDemande({ texte: 'Combien ai-je de tâches à faire FICTIF ?', source: 'micro' }).suite;
      attendreEgal([compte.type, compte.message, envois.length - envoisLecture], ['reponse', `Tu as ${aFaire} tâches à faire.`, 2], 'lecture : deux appels, réponse dite');
      const second = JSON.parse(envois[envois.length - 1].options.body).messages;
      const resultat = second[second.length - 1].content[0];
      const lu = JSON.parse(resultat.content);
      attendreEgal([resultat.type, resultat.tool_use_id, lu.nombre, lu.taches.length <= 25], ['tool_result', 'lecture1', aFaire, true], 'Cap a lu les tâches et renvoyé le nombre exact');
      attendre(lu.taches.every(tache => Object.keys(tache).join() === 'intitule,categorie,sous_categorie,echeance,fait'), 'strict nécessaire : copie réduite');
      attendreEgal(JSON.stringify(TACHES), empreinteTaches, 'lecture seule : rien modifié');
      attendreEgal(actionsCap.lire('lire_taches', { categorie: 'Inconnue FICTIF' }).erreur, 'La catégorie « Inconnue FICTIF » n’existe pas.', 'catégorie inconnue signalée');
      const rdv = actionsCap.lire('lire_rendez_vous', { du: '2027-01-01', au: '2027-01-31' });
      attendreEgal([rdv.du, rdv.au, typeof rdv.nombre], ['2027-01-01', '2027-01-31', 'number'], 'lecture des rendez-vous');
      attendreEgal(cerveau.proposer({ type: 'action', action: 'lire_taches', parametres: {} }).type, 'question', 'une lecture n’est jamais exécutée comme une action');

      const lecturesAvant = lecturesFiche;
      await cerveauClaude.enregistrerFiche('  Tu es Cap FICTIF, fiche collée sur le téléphone.  ');
      attendreEgal([cerveauClaude.ficheTelephone(), cerveauClaude.origineFiche(), cerveauClaude.infoConsignes().origine],
        ['Tu es Cap FICTIF, fiche collée sur le téléphone.', 'telephone', 'telephone'], 'fiche gardée sur le téléphone');
      reponses.push({ statut: 200, corps: { content: [{ type: 'text', text: 'Bien reçu, Max.' }] } });
      await traiterDemande({ texte: 'Tu as ma fiche FICTIF ?', source: 'micro' }).suite;
      const systemeTelephone = JSON.parse(envois[envois.length - 1].options.body).system;
      attendre(systemeTelephone.includes('fiche collée sur le téléphone') && !systemeTelephone.includes(consignes), 'Claude lit exactement la fiche collée par Max');
      attendreEgal(lecturesFiche, lecturesAvant, 'la fiche publique n’est même pas lue quand Max a collé la sienne');
      let videRefusee = false;
      try { await cerveauClaude.enregistrerFiche('   '); } catch (erreur) { videRefusee = erreur.message.includes('vide'); }
      attendre(videRefusee && cerveauClaude.ficheTelephone().includes('fiche collée'), 'fiche vide refusée, l’ancienne gardée');
      await cerveauClaude.retirerFiche();
      attendreEgal([cerveauClaude.ficheTelephone(), cerveauClaude.origineFiche(), await cerveauClaude.etatConsignes()], ['', 'secours', 'pret'], 'retour à la fiche de secours');

      const utilises = limiteIA.utilises();
      reponses.push({ statut: 401, corps: {} });
      const refusee = await traiterDemande({ texte: 'Ajoute dans Quotidien : FICTIF clé refusée', source: 'saisie' }).suite;
      attendreEgal([refusee.type, refusee.tache.categorie, limiteIA.utilises()], ['tache', 'Quotidien', utilises], 'clé refusée : réponses préparées, non compté');
      attendre(refusee.message.includes('clé n’est plus acceptée') && refusee.message.includes('expiré') && refusee.message.includes('en créer une nouvelle'), refusee.message);
      attendre(!refusee.message.includes(CLE_FICTIVE), 'la clé n’est jamais dans un message d’erreur');

      localStorage.setItem('cap_depense_ia_v1', JSON.stringify({ mois: dateDuJour().slice(0, 7), euros: 10 }));
      const envoisAvant = envois.length;
      const immediat = traiterDemande({ texte: 'Ajoute dans Quotidien : FICTIF plafond', source: 'saisie' });
      const plafond = immediat.suite ? await immediat.suite : immediat;
      attendreEgal([plafond.type, envois.length], ['tache', envoisAvant], 'plafond du mois atteint : Claude n’est plus appelé');
      attendre(plafond.message.includes('plafond de dépense du mois'), plafond.message);
      attendreEgal(cerveauClaude.maintenantParis(new Date('2026-10-30T09:37:00Z')), 'Nous sommes le vendredi 30 octobre 2026, il est 10 h 37.', 'date et heure de Paris');
      resultats.push({ nom, ok: true, erreur: '' });
    } catch (erreur) {
      resultats.push({ nom, ok: false, erreur: String(erreur && erreur.message ? erreur.message : erreur) });
    } finally {
      window.fetch = vraiFetch;
      cleIA.retirer();
      cerveauClaude.oublier();
      ['cap_echanges_ia_v1', 'cap_depense_ia_v1', 'cap_journal_ia_v1', 'cap_consignes_v1', 'cap_fiche_consignes_v1'].forEach(cle => localStorage.removeItem(cle));
    }
  })();

  await testAsync('Réglages du cerveau : clé tapée dans Cap, limite changée, champ vidé', async c => {
    const ui = preparerInterface(c);
    const vraiFetch = window.fetch;
    window.fetch = () => Promise.resolve({ ok: true, status: 200, text: () => Promise.resolve('BROUILLON FICTIF\nTu es Cap.') });
    try {
      ui.parId('ouvrir-reglages-ia').click();
      const fenetre = ui.parId('reglages-ia');
      attendre(fenetre.open, 'fenêtre ouverte');
      ui.parId('cle-ia').value = 'pas une clé';
      ui.parId('formulaire-cle-ia').requestSubmit();
      attendre(!fenetre.querySelector('.erreur').hidden && !cleIA.presente(), 'mauvaise clé refusée et expliquée');
      ui.parId('cle-ia').value = 'sk-ant-FICTIF-0000000000000000000000abcd';
      ui.parId('formulaire-cle-ia').requestSubmit();
      attendreEgal([cleIA.presente(), ui.parId('cle-ia').value], [true, ''], 'clé enregistrée, champ vidé');
      attendre(ui.parId('texte-cerveau').textContent.includes(REGLAGES_IA.nom), 'tuile du cerveau à jour');
      ui.parId('limite-ia').value = '100';
      ui.parId('formulaire-limite-ia').requestSubmit();
      attendreEgal(limiteIA.maximum(), 100, 'limite changée par Max');
      ui.parId('plafond-ia').value = '7,5';
      ui.parId('formulaire-plafond-ia').requestSubmit();
      attendreEgal(limiteIA.plafondMensuel(), 7.5, 'plafond changé par Max');
      ui.parId('texte-fiche-ia').value = 'Tu es Cap FICTIF, fiche collée par Max.';
      ui.parId('formulaire-fiche-ia').requestSubmit();
      await new Promise(resolve => setTimeout(resolve, 20));
      attendreEgal([cerveauClaude.ficheTelephone(), ui.parId('retirer-fiche-ia').hidden], ['Tu es Cap FICTIF, fiche collée par Max.', false], 'fiche collée et gardée sur le téléphone');
      attendre(ui.parId('fiche-ia').textContent.includes('ta fiche, gardée sur ce téléphone'), ui.parId('fiche-ia').textContent);
      ui.parId('retirer-fiche-ia').click();
      await new Promise(resolve => setTimeout(resolve, 20));
      attendreEgal([cerveauClaude.ficheTelephone(), ui.parId('texte-fiche-ia').value, ui.parId('retirer-fiche-ia').hidden], ['', '', true], 'retour à la fiche de secours');
      journalIA.noter({ dit: 'FICTIF bonjour', repondu: 'FICTIF salut' });
      await new Promise(resolve => setTimeout(resolve, 0));
      ui.parId('formulaire-limite-ia').requestSubmit();
      attendre(ui.parId('liste-journal-ia').textContent.includes('FICTIF salut'), 'historique de l’IA visible');
      attendre(/Conversation du \d{2}\/\d{2} à \d{1,2} h \d{2} \(1 échange\)/.test(ui.parId('liste-journal-ia').querySelector('summary').textContent), 'conversation datée');
      journalIA.nouvelleConversation();
      journalIA.noter({ dit: 'FICTIF deuxième ouverture', repondu: 'FICTIF re' });
      const groupes = journalIA.conversations();
      attendreEgal([groupes.length, groupes[0].echanges[0].dit, groupes[1].echanges[0].dit], [2, 'FICTIF deuxième ouverture', 'FICTIF bonjour'], 'une conversation par ouverture, la plus récente d’abord');
      ui.parId('effacer-journal-ia').click();
      attendreEgal([journalIA.lire().length, ui.parId('liste-journal-ia').textContent.includes('FICTIF')], [0, false], 'effacé d’un geste');
      ui.parId('retirer-cle-ia').click();
      attendreEgal(cleIA.presente(), false, 'clé retirée');
      await new Promise(resolve => setTimeout(resolve, 0));
    } finally {
      window.fetch = vraiFetch;
      cleIA.retirer();
      cerveauClaude.oublier();
      ['cap_reglages_ia_v1', 'cap_journal_ia_v1', 'cap_consignes_v1', 'cap_fiche_consignes_v1'].forEach(cle => localStorage.removeItem(cle));
    }
  });

  test('Voix : silence par défaut, puis Cap dit ce qu’il a fait en français', () => {
    const dits = [];
    const vraiConstructeur = window.SpeechSynthesisUtterance;
    Object.defineProperty(window, 'speechSynthesis', { value: { cancel() {}, speak(enonce) { dits.push([enonce.text, enonce.lang]); } }, configurable: true });
    window.SpeechSynthesisUtterance = function (texte) { this.text = texte; };
    try {
      attendreEgal(voix.dire('FICTIF'), false, 'silencieux par défaut');
      preferencesClavier.definirSilencieux(false);
      document.getElementById('ouvrir-clavier').click();
      document.getElementById('saisie-demande').value = 'Ajoute dans Quotidien : FICTIF parler';
      document.getElementById('formulaire-demande').requestSubmit();
      if (document.getElementById('clavier').open) document.getElementById('clavier').close();
      attendreEgal(dits, [['C’est noté dans Quotidien, À classer.', 'fr-FR']], 'réponse parlée');
      const tache = TACHES.find(item => item.intitule === 'FICTIF parler');
      attendre(tache && document.querySelector('#statut .annuler-dictee'), 'Annuler proposé après l’action du cerveau');
      document.querySelector('#statut .annuler-dictee').click();
      attendre(tache.abandonnee_le, 'Annuler fonctionne, rien d’effacé');
    } finally {
      delete window.speechSynthesis;
      window.SpeechSynthesisUtterance = vraiConstructeur;
      preferencesClavier.definirSilencieux(true);
    }
  });

  await testAsync('Trier : toucher une catégorie, Annuler, puis la voix range la tâche suivante', async c => {
    tachesTuiles(c);
    const ui = preparerInterface(c);
    const fenetre = ui.parId('mode-trier');
    Array.from(ui.parId('tuiles').querySelectorAll('.ouvrir-tuile')).find(b => b.querySelector('.titre-tuile').textContent === 'Trier').click();
    attendre(fenetre.open, 'Trier fermé');
    attendreEgal(fenetre.querySelector('.tache-a-trier').textContent, 'FICTIF idée en vrac', 'première tâche');
    const choix = Array.from(fenetre.querySelectorAll('.choix-tri'), b => b.textContent);
    attendre(!choix.includes('À trier') && choix.includes('Musique'), 'choix de catégories');
    boutonTexte(fenetre, 'Écriture').click();
    attendreEgal(c.TACHES.find(t => t.id === 'FICTIF-T1').categorie, 'Écriture', 'tâche rangée');
    attendreEgal(fenetre.querySelector('.tache-a-trier').textContent, 'FICTIF autre idée', 'tâche suivante');
    boutonTexte(fenetre, 'Annuler').click();
    attendreEgal(c.TACHES.find(t => t.id === 'FICTIF-T1').categorie, 'À trier', 'Annuler');
    attendreEgal(fenetre.querySelector('.tache-a-trier').textContent, 'FICTIF idée en vrac', 'tâche revenue');
    dicteeQuiEntend(ui, 'mets ça dans musique');
    fenetre.querySelector('.micro-tri').click();
    attendreEgal(c.TACHES.find(t => t.id === 'FICTIF-T1').categorie, 'Musique', 'voix');
    attendreEgal(ui.modeTrier.reconnaitre('quotidien'), 'Quotidien', 'reconnaissance');
    attendreEgal(ui.modeTrier.reconnaitre('rien du tout'), '', 'pas d’invention');
    boutonTexte(fenetre, 'Passer').click();
    attendre(fenetre.querySelector('.revoir-passees'), 'revoir les passées');
    attendreEgal(c.TACHES.length, 4, 'aucune tâche effacée');
    ui.fermetureFenetres.toucheACote(fenetre);
    attendre(!fenetre.open, 'toucher à côté ne ferme pas Trier');
  });

  test('Ordre des tuiles : ordonner garde le choix de Max, À trier reste devant', () => {
    const { instance } = listesIsolees([]);
    attendreEgal(instance.categories().slice(0, 4), ['À trier', 'Musique', 'Écriture', 'Quotidien'], 'départ');
    attendre(instance.ordonner(['Quotidien', 'Musique', 'Écriture']), 'aucun changement');
    attendreEgal(instance.categories().slice(0, 4), ['À trier', 'Quotidien', 'Musique', 'Écriture'], 'ordre choisi');
    attendre(!instance.ordonner(['Quotidien', 'Musique', 'Écriture']), 'réécriture inutile');
  });

  test('Classer : change la catégorie de la tâche et de ses étapes, rien n’est effacé', () => {
    const tache = creerTache({ intitule: 'FICTIF à classer', categorie: 'À trier', sous_categorie: '' });
    ajouterEtape(tache.id, 'FICTIF étape');
    const total = TACHES.length;
    const ancienne = classer(tache.id, 'Musique', '');
    attendreEgal(ancienne.categorie, 'À trier', 'ancienne catégorie');
    attendre(TACHES.filter(t => t.id === tache.id || t.parente === tache.id).every(t => t.categorie === 'Musique'), 'étapes non suivies');
    attendreEgal(TACHES.length, total, 'tâche effacée');
  });

  await testAsync('Aide : bouton en haut à droite, gestes listés, fermeture en touchant à côté', async c => {
    const ui = preparerInterface(c);
    ui.parId('basculer-vue').click();
    const bouton = ui.parId('ouvrir-aide');
    const entete = bouton.parentElement.getBoundingClientRect();
    const cadre = bouton.getBoundingClientRect();
    attendre(Math.abs(entete.right - cadre.right) < 2 && cadre.top - entete.top < 20, 'Aide pas en haut à droite');
    bouton.click();
    const aide = ui.parId('aide');
    attendre(aide.open, 'aide fermée');
    attendre(aide.querySelectorAll('.geste-aide').length >= 6, 'gestes manquants');
    attendre(aide.textContent.includes('droite') && aide.textContent.includes('Annuler'), 'contenu incomplet');
    attendreEgal(aide.querySelectorAll('[data-fermer]').length, 0, 'bouton retour présent');
    ui.fermetureFenetres.toucheACote(aide);
    attendre(!aide.open, 'aide pas fermée en touchant à côté');
  });

  test('Journal complet : contexte, heure à la seconde, masquage des secrets', () => {
    const memoire = espaceMemoire();
    const j = objetIsole(SOURCE_JOURNAL_ACTIONS, 'journalActions', { localStorage: memoire, googleSheets: undefined });
    j.pendant({ source: 'micro', entree: 'ajoute FICTIF pain', compris: 'ajouter une tâche' }, () => j.noter('ajout', 'FICTIF pain'));
    j.consigner({ source: 'clavier', entree: 'mon mot de passe est Secret123 et ma carte 4970 1234 5678 9012', compris: 'rien', fait: 'rien' });
    const lignes = j.lireComplet();
    attendreEgal(lignes.length, 2, 'deux lignes');
    attendre(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(lignes[0][0]), 'heure');
    attendreEgal(lignes[0].slice(1), ['micro', 'ajoute FICTIF pain', 'ajouter une tâche', 'ajout de la tâche : FICTIF pain'], 'ligne');
    attendre(!lignes[1][2].includes('Secret123') && !lignes[1][2].includes('9012'), 'secret conservé');
    j.noter('fait', 'FICTIF pain');
    attendreEgal(j.lireComplet()[2][1], 'écran touché', 'source par défaut');
  });

  await testAsync('Journal complet : envoi en ajout à la fin de l’onglet, file vidée seulement après succès', async c => {
    preparerConnexion(c);
    let ongletPresent = false;
    let panne = true;
    c.repondre = async r => {
      const chemin = decodeURIComponent(r.url.pathname);
      if (r.methode === 'GET' && chemin === '/drive/v3/files/tableau-fictif') return reponseGoogle({ id: 'tableau-fictif', trashed: false });
      if (r.methode === 'GET' && chemin === '/v4/spreadsheets/tableau-fictif') return reponseGoogle({ sheets: [{ properties: { title: 'Tâches' } }, ...(ongletPresent ? [{ properties: { title: 'Journal' } }] : [])] });
      if (r.methode === 'POST' && chemin.endsWith(':append')) {
        if (panne) return reponseGoogle({ error: { message: 'panne' } }, 500);
        return reponseGoogle({});
      }
      if (r.methode === 'POST') { ongletPresent = true; return reponseGoogle({}); }
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    c.localStorage.setItem('cap_google_fichier_v1', 'tableau-fictif');
    const sheets = c.sheets();
    const j = objetIsole(SOURCE_JOURNAL_ACTIONS, 'journalActions', {
      localStorage: c.localStorage, googleSheets: sheets, googleConnexion: c.googleConnexion,
      navigator: c.navigator, synchronisation: { informations: () => ({ pret: true }) }, setTimeout: () => 0
    });
    j.consigner({ source: 'micro', entree: 'FICTIF', compris: 'test', fait: 'rien' });
    attendreEgal(await j.envoyer(), false, 'panne non signalée');
    attendreEgal(j.enAttente(), 1, 'ligne perdue après une panne');
    panne = false;
    attendreEgal(await j.envoyer(), true, 'envoi');
    attendreEgal(j.enAttente(), 0, 'file non vidée');
    const ajout = c.requetes.filter(r => decodeURIComponent(r.url.pathname).endsWith(':append')).pop();
    attendre(decodeURIComponent(ajout.url.pathname).includes('Journal'), 'mauvais onglet');
    attendreEgal(ajout.url.searchParams.get('insertDataOption'), 'INSERT_ROWS', 'ajout sans écraser');
    attendreEgal(ajout.corps.values[0].slice(1), ['micro', 'FICTIF', 'test', 'rien'], 'contenu');
    attendre(c.requetes.every(r => !['DELETE'].includes(r.methode) && !r.url.pathname.includes(':clear')), 'effacement');
  });

  await testAsync('Sauvegarde Drive : copie datée dans le dossier, aucune suppression, hebdomadaire après la première', async c => {
    preparerConnexion(c);
    c.localStorage.setItem('cap_google_fichier_v1', 'tableau-fictif');
    c.repondre = async r => {
      const chemin = decodeURIComponent(r.url.pathname);
      if (r.methode === 'GET' && chemin === '/drive/v3/files/tableau-fictif') return reponseGoogle({ id: 'tableau-fictif', trashed: false });
      if (r.methode === 'GET' && chemin === '/drive/v3/files' && r.url.searchParams.get('q').includes('folder')) return reponseGoogle({ files: [] });
      if (r.methode === 'POST' && chemin === '/drive/v3/files') return reponseGoogle({ id: 'dossier-fictif' });
      if (r.methode === 'POST' && chemin === '/drive/v3/files/tableau-fictif/copy') return reponseGoogle({ id: 'copie-fictive', name: r.corps.name });
      if (r.methode === 'GET' && chemin === '/drive/v3/files') return reponseGoogle({ files: Array.from({ length: 6 }, (_, i) => ({ id: `c${i}` })) });
      throw new Error(`Requête inattendue : ${r.url}`);
    };
    const sheets = c.sheets();
    const s = objetIsole(SOURCE_SAUVEGARDE_DRIVE, 'sauvegardeDrive', {
      localStorage: c.localStorage, window: c.window, googleConnexion: c.googleConnexion, googleSheets: sheets,
      REGLAGES_GOOGLE, journalActions: { consigner: () => {} }
    });
    attendre(!s.aFaire(), 'automatique avant la première');
    attendreEgal(await s.verifierAutomatique(), null, 'sauvegarde automatique sans accord');
    const resultat = await s.sauvegarder();
    const copie = c.requetes.find(r => r.url.pathname.endsWith('/copy'));
    attendre(copie.corps.name.includes('sauvegarde du') && copie.corps.name.includes('FICTIF'), 'nom de la copie');
    attendreEgal(copie.corps.parents, ['dossier-fictif'], 'dossier');
    attendreEgal(resultat.enTrop, 1, 'copies en trop');
    attendre(c.requetes.every(r => r.methode !== 'DELETE' && !(r.corps && r.corps.trashed)), 'suppression');
    attendre(!s.aFaire(Date.now()), 'refait aussitôt');
    attendre(s.aFaire(Date.now() + 8 * 24 * 3600 * 1000), 'pas refait après une semaine');
    attendreEgal(s.etat().nombre, 6, 'nombre de copies');
  });

  const erreursPage = window.erreursPage || [];
  const reussis = resultats.filter(r => r.ok).length;
  document.getElementById('resultat-tests').textContent = JSON.stringify({
    erreurs_page: erreursPage,
    reussis,
    total: resultats.length,
    tests: resultats
  });
})();
"""


MANIFEST = "manifest.webmanifest"
FAVICON = "icones/favicon.png"
ATTENDUS_MANIFEST = {
    "name": "Cap",
    "short_name": "Cap",
    "lang": "fr",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#FDE6C3",
    "theme_color": "#4F87B5",
}
ICONES_MANIFEST = [
    ("icones/icone-192.png", 192, "any"),
    ("icones/icone-512.png", 512, "any"),
    ("icones/icone-maskable-512.png", 512, "maskable"),
]


def attendre(condition, message):
    if not condition:
        raise AssertionError(message)


def lire_texte(nom):
    return (APP / nom).read_text(encoding="utf-8")


def lire_json(nom):
    return json.loads(lire_texte(nom))


def lire_html():
    return lire_texte("index.html")


def attribut(balise, nom):
    trouve = re.search(rf'\b{nom}="([^"]*)"', balise)
    return trouve.group(1) if trouve else None


def normaliser(entree):
    return entree[2:] if entree.startswith("./") else entree


def lire_precache():
    texte = lire_texte("service-worker.js")
    trouve = re.search(r"const\s+FICHIERS_PRECACHE\s*=\s*(\[.*?\])\s*;", texte, re.S)
    attendre(trouve, "FICHIERS_PRECACHE introuvable dans service-worker.js")
    try:
        liste = json.loads(trouve.group(1))
    except ValueError as erreur:
        raise AssertionError(f"FICHIERS_PRECACHE n’est pas un tableau JSON valide : {erreur}")
    attendre(isinstance(liste, list) and all(isinstance(e, str) for e in liste),
             "FICHIERS_PRECACHE doit contenir uniquement des chaînes")
    return liste


def lire_png(chemin):
    attendre(chemin.is_file(), f"fichier introuvable : {chemin.relative_to(APP).as_posix()}")
    with open(chemin, "rb") as fichier:
        entete = fichier.read(24)
    attendre(len(entete) == 24 and entete[:8] == b"\x89PNG\r\n\x1a\n" and entete[12:16] == b"IHDR",
             f"signature PNG invalide : {chemin.name}")
    return struct.unpack(">II", entete[16:24])


def verifier_fichiers_requis():
    requis = ["index.html", "style.css", MANIFEST, "service-worker.js", "installation.js", FAVICON]
    requis += [chemin for chemin, _, _ in ICONES_MANIFEST]
    requis += SOURCES
    manquants = [nom for nom in requis if not (APP / nom).is_file()]
    attendre(not manquants, f"fichiers manquants : {', '.join(manquants)}")


def verifier_manifest():
    manifest = lire_json(MANIFEST)
    for champ, valeur in ATTENDUS_MANIFEST.items():
        attendre(manifest.get(champ) == valeur,
                 f"manifest {champ} attendu {valeur!r}, reçu {manifest.get(champ)!r}")


def verifier_icones_manifest():
    icones = lire_json(MANIFEST).get("icons")
    attendre(isinstance(icones, list) and len(icones) == len(ICONES_MANIFEST),
             f"le manifest doit déclarer exactement {len(ICONES_MANIFEST)} icônes")
    for chemin, taille, usage in ICONES_MANIFEST:
        entree = next((i for i in icones if isinstance(i, dict) and i.get("src") == chemin), None)
        attendre(entree is not None, f"icône absente du manifest : {chemin}")
        attendre(entree.get("sizes") == f"{taille}x{taille}",
                 f"taille déclarée incorrecte pour {chemin} : {entree.get('sizes')!r}")
        attendre(entree.get("purpose", "any") == usage,
                 f"usage déclaré incorrect pour {chemin} : {entree.get('purpose')!r}")


def verifier_png():
    for chemin, taille, _ in ICONES_MANIFEST:
        largeur, hauteur = lire_png(APP / chemin)
        attendre(largeur == taille and hauteur == taille,
                 f"dimensions de {chemin} : {largeur}x{hauteur}, attendu {taille}x{taille}")
    largeur, hauteur = lire_png(APP / FAVICON)
    attendre(largeur == 48 and hauteur == 48, f"dimensions de {FAVICON} : {largeur}x{hauteur}, attendu 48x48")


def verifier_liens_manifest_favicon():
    liens = re.findall(r"<link\b[^>]*>", lire_html(), re.I)
    attendre(any(attribut(l, "rel") == "manifest" and attribut(l, "href") == MANIFEST for l in liens),
             f"lien manifest vers {MANIFEST} absent de index.html")
    attendre(any(attribut(l, "rel") == "icon" and attribut(l, "href") == FAVICON for l in liens),
             f"lien favicon vers {FAVICON} absent de index.html")
    attendre(any(attribut(l, "rel") == "apple-touch-icon"
                 and attribut(l, "href") == "icones/icone-192.png" for l in liens),
             "lien apple-touch-icon absent de index.html")


def verifier_liens_locaux():
    references = re.findall(r'\b(?:href|src)="([^"]*)"', lire_html())
    manquants = []
    for reference in references:
        if reference in ("", "./") or reference.startswith(("http://", "https://", "//", "data:", "mailto:", "#")):
            continue
        cible = reference.split("#", 1)[0].split("?", 1)[0]
        if cible and not (APP / cible).is_file():
            manquants.append(reference)
    attendre(not manquants, f"liens locaux introuvables dans index.html : {', '.join(manquants)}")


def verifier_version_cache():
    attendre(re.search(r"const\s+VERSION_CACHE\s*=\s*['\"]cap-v19['\"]\s*;", lire_texte("service-worker.js")),
             "VERSION_CACHE doit définir cap-v19")


def verifier_precache_fichiers_existent():
    for entree in lire_precache():
        nom = normaliser(entree)
        if nom in ("", "."):
            continue
        attendre((APP / nom).is_file(), f"fichier précaché introuvable : {entree}")


def verifier_precache_couverture():
    precache = {normaliser(e) for e in lire_precache()}
    requis = ["index.html", "style.css", MANIFEST]
    requis += [p.name for p in APP.glob("*.js")]
    requis += [p.relative_to(APP).as_posix() for p in (APP / "icones").glob("*.png")]
    manquants = sorted(nom for nom in requis if nom not in precache)
    attendre(not manquants, f"absents de FICHIERS_PRECACHE : {', '.join(manquants)}")


def verifier_installation_en_dernier():
    if not (APP / "installation.js").is_file():
        return
    scripts = re.findall(r'<script\b[^>]*\bsrc="([^"]*)"', lire_html())
    attendre([normaliser(script) for script in scripts] == SOURCES + ["installation.js"],
             "les scripts du clavier doivent suivre dictee.js, avant app.js et installation.js")


def verifier_rien_de_prive_publie():
    # Les mots privés (prénoms des proches, phrases de la fiche de Max) sont dans mots_prives.txt, jamais publié.
    racine = APP.parent
    liste = racine / "mots_prives.txt"
    attendre(liste.is_file(), "mots_prives.txt absent : impossible de vérifier qu'aucun prénom de proche n'est publié")
    ignore = subprocess.run(["git", "check-ignore", "-q", str(liste)], cwd=racine)
    attendre(ignore.returncode == 0, "mots_prives.txt doit rester dans .gitignore")
    mots = [ligne.strip() for ligne in liste.read_text(encoding="utf-8").splitlines() if ligne.strip() and not ligne.startswith("#")]
    attendre(mots, "mots_prives.txt est vide")
    sortie = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                            cwd=racine, capture_output=True, check=True).stdout.decode("utf-8")
    fautifs = []
    for nom in filter(None, sortie.split("\0")):
        chemin = racine / nom
        if not chemin.is_file() or chemin.suffix.lower() in {".png", ".ico"}:
            continue
        texte = chemin.read_text(encoding="utf-8", errors="ignore").casefold()
        if any(re.search(rf"(?<!\w){re.escape(mot.casefold())}(?!\w)", texte) for mot in mots):
            fautifs.append(nom)
        if re.search(r"sk-ant-(?!FICTIF)[A-Za-z0-9_-]{20,}", chemin.read_text(encoding="utf-8", errors="ignore")):
            fautifs.append(f"{nom} (clé)")
    attendre(not fautifs, f"donnée privée dans des fichiers publiables : {', '.join(fautifs)}")


TESTS_PWA = [
    ("Publication : aucun prénom de proche, aucune phrase de la fiche, aucune clé", verifier_rien_de_prive_publie),
    ("PWA : fichiers requis présents", verifier_fichiers_requis),
    ("PWA : manifest, champs attendus", verifier_manifest),
    ("PWA : manifest, icônes déclarées", verifier_icones_manifest),
    ("PWA : icônes PNG, dimensions et signature", verifier_png),
    ("PWA : HTML, liens manifest et favicon", verifier_liens_manifest_favicon),
    ("PWA : HTML, liens locaux existants", verifier_liens_locaux),
    ("PWA : service-worker, version de cache", verifier_version_cache),
    ("PWA : service-worker, fichiers précachés existants", verifier_precache_fichiers_existent),
    ("PWA : service-worker, couverture de la précache", verifier_precache_couverture),
    ("PWA : installation.js chargé en dernier", verifier_installation_en_dernier),
]


def executer_tests_pwa():
    resultats = []
    for nom, fonction in TESTS_PWA:
        try:
            fonction()
            resultats.append({"nom": nom, "ok": True, "erreur": ""})
        except Exception as erreur:
            resultats.append({"nom": nom, "ok": False, "erreur": str(erreur) or type(erreur).__name__})
    return resultats


def afficher_resultat(test):
    if test["ok"]:
        print(f"OK     {test['nom']}")
    else:
        print(f"ECHEC  {test['nom']} : {test['erreur']}")


def construire_page():
    source_stockage = (APP / "stockage.js").read_text(encoding="utf-8")
    scripts = "\n".join(f'<script src="/src/{nom}"></script>' for nom in SOURCES)
    source_json = json.dumps(source_stockage).replace("</", "<\\/")
    source_dictee = (APP / "dictee.js").read_text(encoding="utf-8")
    source_dictee_json = json.dumps(source_dictee).replace("</", "<\\/")
    sources_google = {
        "SOURCE_GOOGLE_CONNEXION": "google_connexion.js",
        "SOURCE_GOOGLE_SHEETS": "google_sheets.js",
        "SOURCE_GOOGLE_AGENDA": "google_agenda.js",
        "SOURCE_SYNCHRONISATION": "synchronisation.js",
        "SOURCE_SERVICE_WORKER": "service-worker.js",
        "SOURCE_APP": "app.js",
        "SOURCE_JOURNAL_ACTIONS": "journal_actions.js",
        "SOURCE_FICHE_RDV": "fiche_rendezvous.js",
        "SOURCE_LISTES_CHOIX": "listes_choix.js",
        "SOURCE_CHOIX_DATES": "choix_dates.js",
        "SOURCE_FENETRES_LISTES": "fenetres_listes.js",
        "SOURCE_FERMETURE_FENETRES": "fermeture_fenetres.js",
        "SOURCE_SYNCHRO_LISTES": "synchro_listes.js",
        "SOURCE_SAUVEGARDE_DRIVE": "sauvegarde_drive.js",
        "SOURCE_TUILES": "tuiles.js",
        "SOURCE_MODE_TRIER": "mode_trier.js",
        "SOURCE_HTML": "index.html",
        "SOURCE_STYLE": "style.css",
    }
    scripts_sources_google = []
    for constante, nom in sources_google.items():
        source_google_json = json.dumps(lire_texte(nom)).replace("</", "<\\/")
        scripts_sources_google.append(f"<script>const {constante} = {source_google_json};</script>")
    scripts_sources_google = "\n".join(scripts_sources_google)
    source_style = (APP / "style.css").read_text(encoding="utf-8")
    corps_index = (APP / "index.html").read_text(encoding="utf-8")
    corps_body = re.search(r"<body>(.*?)</body>", corps_index, re.S).group(1)
    corps_body = re.sub(r"<script\b[^>]*>.*?</script>", "", corps_body, flags=re.S)
    return f"""<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>Tests Cap</title><style>{source_style}</style></head>
<body>
<pre id="resultat-tests"></pre>
<script>
window.erreursPage = [];
window.addEventListener('error', e => window.erreursPage.push(String(e.message)));
window.addEventListener('unhandledrejection', e => window.erreursPage.push(String(e.reason)));
window.fetch = async () => {{
  const message = 'Vrai fetch interdit dans les tests';
  window.erreursPage.push(message);
  throw new Error(message);
}};
for (const espace of [localStorage, sessionStorage]) {{
  for (const cle of Object.keys(espace)) {{
    if (cle.startsWith('cap_google_')) espace.removeItem(cle);
  }}
}}
</script>
{corps_body}
{scripts}
<script>const SOURCE_STOCKAGE = {source_json};</script>
<script>const SOURCE_DICTEE = {source_dictee_json};</script>
{scripts_sources_google}
<script>{TESTS_JS}</script>
</body>
</html>
"""


class Gestionnaire(BaseHTTPRequestHandler):
    def do_GET(self):
        chemin = self.path.split("?", 1)[0]
        if chemin == "/tests.html":
            corps = construire_page().encode("utf-8")
            type_contenu = "text/html; charset=utf-8"
        elif chemin.startswith("/src/") and chemin[5:] in SOURCES:
            corps = (APP / chemin[5:]).read_bytes()
            type_contenu = "text/javascript; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", type_contenu)
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def log_message(self, format, *args):
        pass


def executer_tests(port):
    url = f"http://127.0.0.1:{port}/tests.html"
    with tempfile.TemporaryDirectory(dir=APP, ignore_cleanup_errors=True) as profil:
        commande = [
            str(EDGE),
            "--headless",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            f"--user-data-dir={profil}",
            "--dump-dom",
            "--virtual-time-budget=3000",
            url,
        ]
        try:
            resultat = subprocess.run(commande, capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:
            return None
        return resultat.stdout.decode("utf-8", errors="replace")


def main():
    resultats_pwa = executer_tests_pwa()
    for test in resultats_pwa:
        afficher_resultat(test)
    if not EDGE.exists():
        print(f"Edge introuvable : {EDGE}")
        return 2
    serveur = ThreadingHTTPServer(("127.0.0.1", 0), Gestionnaire)
    thread = threading.Thread(target=serveur.serve_forever, daemon=True)
    thread.start()
    try:
        sortie = executer_tests(serveur.server_address[1])
    finally:
        serveur.shutdown()
        serveur.server_close()

    if sortie is None:
        print("Délai dépassé lors de l’exécution d’Edge.")
        return 1
    trouve = re.search(r'<pre id="resultat-tests">(.*?)</pre>', sortie, re.S)
    if not trouve:
        print("Résultat des tests introuvable dans le DOM.")
        return 1
    rapport = json.loads(html.unescape(trouve.group(1)))

    for erreur in rapport["erreurs_page"]:
        print(f"ERREUR PAGE : {erreur}")
    for test in rapport["tests"]:
        afficher_resultat(test)
    reussis = rapport["reussis"] + sum(1 for test in resultats_pwa if test["ok"])
    total = rapport["total"] + len(resultats_pwa)
    print(f"{reussis}/{total} tests réussis")

    echec = rapport["erreurs_page"] or reussis != total
    return 1 if echec else 0


if __name__ == "__main__":
    sys.exit(main())
