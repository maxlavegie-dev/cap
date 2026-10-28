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
SOURCES = ["donnees_fictives.js", "etapes_par_defaut.js", "stockage.js", "taches.js", "dictee.js", "phrases_clavier.js", "preferences_clavier.js", "demandes.js", "app.js"]

TESTS_JS = r"""
(() => {
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
    for (const cle of [CLE_USAGE, CLE_HISTORIQUE, CLE_SILENCE]) localStorage.removeItem(cle);
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
    attendreEgal([annuler.type, annuler.message],
      ['attente_cerveau', '« Annule. » marchera quand le cerveau de Cap sera branché.'], 'Annuler');
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
    attendre(re.search(r"const\s+VERSION_CACHE\s*=\s*['\"]cap-v2['\"]\s*;", lire_texte("service-worker.js")),
             "VERSION_CACHE doit définir cap-v2")


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


TESTS_PWA = [
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
    source_style = (APP / "style.css").read_text(encoding="utf-8")
    corps_index = (APP / "index.html").read_text(encoding="utf-8")
    corps_body = re.search(r"<body>(.*?)</body>", corps_index, re.S).group(1)
    corps_body = re.sub(r"<script\b[^>]*>.*?</script>", "", corps_body, flags=re.S)
    return f"""<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>Tests Cap</title><style>{source_style}</style></head>
<body>
<pre id="resultat-tests"></pre>
<script>window.erreursPage = []; window.addEventListener('error', e => window.erreursPage.push(String(e.message)));</script>
{corps_body}
{scripts}
<script>const SOURCE_STOCKAGE = {source_json};</script>
<script>const SOURCE_DICTEE = {source_dictee_json};</script>
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
