/* ================================================================
   BLOC ISOLE : VISUALISEUR DE DOCUMENTS (FICTIF) - A BRANCHER DANS CAP
   ================================================================
   Un seul grand espace partage ("#zone-image", voir visualiseur.css)
   peut afficher plusieurs documents en meme temps (images et PDF
   sans distinction), chacun deplacable et zoomable librement, et
   pouvant en recouvrir un autre. Voir LISEZ_MOI.txt pour le mode
   d'emploi complet (fichiers necessaires, ou placer le HTML, comment
   appeler les fonctions).

   CE FICHIER ATTEND, DEJA PRESENTS DANS LA PAGE AU MOMENT OU IL
   S'EXECUTE :
   - un element avec id="zone-image" (voir LISEZ_MOI.txt pour le
     morceau de HTML exact a inclure) ;
   - pdf.js deja charge en scripts classiques AVANT ce fichier
     (pdfjs/pdf.worker.min.js puis pdfjs/pdf.min.js), comme dans
     l'essai (voir LISEZ_MOI.txt).

   Fonctions publiques exposees sur "window.Visualiseur" tout en bas
   de ce fichier : montrerFichier, montrerPlusieurs, fermer.
   ================================================================ */
(function () {
  "use strict";

  var zoneImage = document.getElementById("zone-image");

  // Chemin du fichier "worker" de pdf.js, relatif a la page qui
  // charge ce script. A ajuster ici si Cap range le dossier "pdfjs"
  // ailleurs (voir LISEZ_MOI.txt).
  var CHEMIN_PDFJS_WORKER = "pdfjs/pdf.worker.min.js";
  // 07/11/2026 (Claude Code, accord de Max) : pdf.js de Cap, rangé dans app/pdfjs (la visionneuse est dans app/visionneuse).
  CHEMIN_PDFJS_WORKER = "../pdfjs/pdf.worker.min.js";
  if (window.pdfjsLib) {
    pdfjsLib.GlobalWorkerOptions.workerSrc = CHEMIN_PDFJS_WORKER;
  }

  var LIMITE_DOCUMENTS = 12;
  var ZOOM_MIN = 0.5, ZOOM_MAX = 6;
  // 08/11/2026 (Claude Code, accord de Max) : dézoom jusqu'au quart de la taille d'ouverture (au lieu de la moitié).
  ZOOM_MIN = 0.25;
  var SEUIL_DOUBLE_APPUI = 320;

  var documentsListe = [];
  var compteurDocuments = 0;

  // Un document est considere PDF si son titre se termine par
  // ".pdf" (insensible a la casse).
  function estUnPdf(titre) {
    return /\.pdf$/i.test(titre || "");
  }

  // Espace partage : TOUS les documents se mesurent par rapport a la
  // MEME zone (#zone-image), jamais par rapport a leur propre carte
  // (qui, elle, change de taille a chaque zoom). Ainsi, tous les
  // documents ont la meme limite de zoom arriere.
  //
  // doc.largeurNaturelle / doc.hauteurNaturelle : taille naturelle de
  // l'image, ou taille du canvas sur lequel une page de PDF est
  // rendue. Le reste du zoom/deplacement est identique pour les deux.
  function calculerEchelleBaseDoc(doc) {
    var contW = zoneImage.clientWidth || 1;
    var contH = zoneImage.clientHeight || 1;
    doc.echelleBase = Math.min(contW / (doc.largeurNaturelle || 1), contH / (doc.hauteurNaturelle || 1));
  }

  function limiterDeplacementDoc(doc) {
    var echelleTotale = doc.echelleBase * doc.zoomEchelle;
    var largeurAffichee = (doc.largeurNaturelle || 0) * echelleTotale;
    var hauteurAffichee = (doc.hauteurNaturelle || 0) * echelleTotale;
    var contW = zoneImage.clientWidth || 0;
    var contH = zoneImage.clientHeight || 0;
    var margeMin = 40;
    var maxX = Math.max(0, largeurAffichee / 2 + contW / 2 - margeMin);
    var maxY = Math.max(0, hauteurAffichee / 2 + contH / 2 - margeMin);
    doc.zoomX = Math.max(-maxX, Math.min(maxX, doc.zoomX));
    doc.zoomY = Math.max(-maxY, Math.min(maxY, doc.zoomY));
  }

  // La carte (doc.carte) est positionnee et dimensionnee ici pour
  // coller exactement au rectangle visible de l'image/page : c'est
  // la carte entiere qui bouge et change de taille (pas de
  // "transform" sur l'image elle-meme). Les boutons et reperes
  // places dans la carte restent donc toujours a la bonne taille et
  // au bon endroit, sans calcul supplementaire.
  function appliquerTransformImageDoc(doc) {
    limiterDeplacementDoc(doc);
    var echelleTotale = doc.echelleBase * doc.zoomEchelle;
    var largeurAffichee = (doc.largeurNaturelle || 0) * echelleTotale;
    var hauteurAffichee = (doc.hauteurNaturelle || 0) * echelleTotale;
    var zoneW = zoneImage.clientWidth || 0;
    var zoneH = zoneImage.clientHeight || 0;
    var centreX = zoneW / 2 + doc.zoomX;
    var centreY = zoneH / 2 + doc.zoomY;
    doc.carte.style.left = (centreX - largeurAffichee / 2) + "px";
    doc.carte.style.top = (centreY - hauteurAffichee / 2) + "px";
    doc.carte.style.width = largeurAffichee + "px";
    doc.carte.style.height = hauteurAffichee + "px";
  }

  function reinitialiserZoomDoc(doc) {
    doc.zoomEchelle = 1;
    doc.zoomX = 0;
    doc.zoomY = 0;
    appliquerTransformImageDoc(doc);
  }

  function nbPointeursDoc(doc) {
    var n = 0;
    for (var id in doc.pointeurs) if (doc.pointeurs.hasOwnProperty(id)) n++;
    return n;
  }

  function centrePointeursDoc(doc) {
    var ids = Object.keys(doc.pointeurs);
    var p1 = doc.pointeurs[ids[0]];
    var p2 = doc.pointeurs[ids[1]];
    return { x: (p1.x + p2.x) / 2, y: (p1.y + p2.y) / 2 };
  }

  function distancePointeursDoc(doc) {
    var ids = Object.keys(doc.pointeurs);
    var p1 = doc.pointeurs[ids[0]];
    var p2 = doc.pointeurs[ids[1]];
    return Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
  }

  // Appui long (environ 0,5 seconde) : bascule le document entre
  // premier et dernier plan. Un deplacement de plus de quelques
  // millimetres avant la fin du delai annule l'appui long (c'est
  // alors un glissement normal, pas un changement d'ordre). Aucune
  // vibration.
  var DUREE_APPUI_LONG = 550;
  var SEUIL_DEPLACEMENT_APPUI_LONG = 8;

  // Deplace la carte en fin (premier plan) ou en debut (dernier plan)
  // des enfants de #zone-image : l'ordre d'affichage suit simplement
  // l'ordre dans le document, aucun z-index necessaire.
  function basculerOrdreDoc(doc) {
    if (doc.auPremierPlan) {
      zoneImage.insertBefore(doc.carte, zoneImage.firstChild);
      doc.auPremierPlan = false;
    } else {
      zoneImage.appendChild(doc.carte);
      doc.auPremierPlan = true;
    }
    declencherEclat(doc);
  }

  // Eclat discret (voir CSS "eclat-ordre-doc") : on retire puis
  // remet la classe pour pouvoir le relancer meme si le document
  // vient deja de clignoter recemment.
  function declencherEclat(doc) {
    doc.carte.classList.remove("eclat-ordre");
    void doc.carte.offsetWidth;
    doc.carte.classList.add("eclat-ordre");
  }

  // Attache pincement, glissement, double-appui, molette et appui
  // long a la carte d'un document (image ou page de PDF, qui
  // partagent exactement le meme code de zoom/deplacement).
  function attacherEvenementsImage(doc) {
    var carte = doc.carte;

    carte.addEventListener("animationend", function () {
      carte.classList.remove("eclat-ordre");
    });

    function annulerAppuiLong() {
      if (doc.minuteurAppuiLong) {
        clearTimeout(doc.minuteurAppuiLong);
        doc.minuteurAppuiLong = null;
      }
    }

    carte.addEventListener("pointerdown", function (e) {
      doc.pointeurs[e.pointerId] = { x: e.clientX, y: e.clientY };
      if (nbPointeursDoc(doc) === 2) {
        annulerAppuiLong();
        doc.distanceDepartPincement = distancePointeursDoc(doc);
        doc.echelleDepartPincement = doc.zoomEchelle;
        doc.dernierePositionPincement = centrePointeursDoc(doc);
        doc.departGlissement = null;
        // 08/11/2026 (Claude Code, accord de Max) : un pincement commence ; ses doigts levés ne comptent pas comme un double appui.
        doc.pincementRecent = true;
      } else if (nbPointeursDoc(doc) === 1) {
        doc.departGlissement = { x: e.clientX, y: e.clientY, zoomX: doc.zoomX, zoomY: doc.zoomY };
        // 08/11/2026 (Claude Code, accord de Max) : nouveau geste, l'ancien pincement est fini.
        doc.pincementRecent = false;
        doc.positionAppuiLong = { x: e.clientX, y: e.clientY };
        annulerAppuiLong();
        doc.minuteurAppuiLong = setTimeout(function () {
          doc.minuteurAppuiLong = null;
          basculerOrdreDoc(doc);
        }, DUREE_APPUI_LONG);
      }
    });

    carte.addEventListener("pointermove", function (e) {
      if (!doc.pointeurs.hasOwnProperty(e.pointerId)) return;
      doc.pointeurs[e.pointerId] = { x: e.clientX, y: e.clientY };

      if (doc.minuteurAppuiLong && doc.positionAppuiLong) {
        var ecartX = e.clientX - doc.positionAppuiLong.x;
        var ecartY = e.clientY - doc.positionAppuiLong.y;
        if (Math.sqrt(ecartX * ecartX + ecartY * ecartY) > SEUIL_DEPLACEMENT_APPUI_LONG) {
          annulerAppuiLong();
        }
      }

      if (nbPointeursDoc(doc) === 2) {
        var distanceActuelle = distancePointeursDoc(doc);
        if (doc.distanceDepartPincement > 0) {
          var nouvelleEchelle = doc.echelleDepartPincement * (distanceActuelle / doc.distanceDepartPincement);
          doc.zoomEchelle = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, nouvelleEchelle));
        }
        var centreActuel = centrePointeursDoc(doc);
        doc.zoomX += centreActuel.x - doc.dernierePositionPincement.x;
        doc.zoomY += centreActuel.y - doc.dernierePositionPincement.y;
        doc.dernierePositionPincement = centreActuel;
        appliquerTransformImageDoc(doc);
      } else if (nbPointeursDoc(doc) === 1 && doc.departGlissement) {
        doc.zoomX = doc.departGlissement.zoomX + (e.clientX - doc.departGlissement.x);
        doc.zoomY = doc.departGlissement.zoomY + (e.clientY - doc.departGlissement.y);
        appliquerTransformImageDoc(doc);
      }
    });

    function finPointeur(e) {
      delete doc.pointeurs[e.pointerId];
      annulerAppuiLong();
      if (nbPointeursDoc(doc) < 2) {
        doc.distanceDepartPincement = 0;
      }
      if (nbPointeursDoc(doc) === 0) {
        doc.departGlissement = null;
      }
    }

    carte.addEventListener("pointerup", finPointeur);
    carte.addEventListener("pointercancel", finPointeur);

    carte.addEventListener("pointerup", function (e) {
      // 08/11/2026 (Claude Code, accord de Max) : fin d'un pincement = pas un double appui (sinon saut à 2,5 ou retour à 1 au lâcher).
      if (doc.pincementRecent) {
        if (nbPointeursDoc(doc) === 0) doc.pincementRecent = false;
        doc.dernierAppuiTemps = 0;
        return;
      }
      var maintenant = performance.now();
      if (maintenant - doc.dernierAppuiTemps < SEUIL_DOUBLE_APPUI) {
        if (doc.zoomEchelle > 1.05) {
          reinitialiserZoomDoc(doc);
        } else {
          doc.zoomEchelle = 2.5;
          appliquerTransformImageDoc(doc);
        }
        doc.dernierAppuiTemps = 0;
      } else {
        doc.dernierAppuiTemps = maintenant;
      }
    });

    carte.addEventListener("wheel", function (e) {
      e.preventDefault();
      var delta = e.deltaY < 0 ? 1.12 : 1 / 1.12;
      doc.zoomEchelle = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, doc.zoomEchelle * delta));
      appliquerTransformImageDoc(doc);
    }, { passive: false });
  }

  // Rendu d'une page de PDF sur un canvas : le canvas est ensuite
  // traite exactement comme une image (meme classe CSS, meme zoom/
  // deplacement, memes fonctions calculerEchelleBaseDoc /
  // appliquerTransformImageDoc ci-dessus).
  var ECHELLE_RENDU_PDF = Math.min(3, (window.devicePixelRatio || 1) * 2);

  // Affiche un message d'erreur VISIBLE a l'ecran (au lieu d'un
  // simple ecran noir muet) quand un PDF ne peut pas etre lu ou
  // affiche. Donne une taille de secours a la carte pour que le
  // message soit bien centre et lisible, meme si aucune page n'a pu
  // etre rendue.
  var TAILLE_PLACEHOLDER_ERREUR_PDF = { largeur: 280, hauteur: 360 };

  function afficherErreurPdf(doc, message) {
    doc.largeurNaturelle = TAILLE_PLACEHOLDER_ERREUR_PDF.largeur;
    doc.hauteurNaturelle = TAILLE_PLACEHOLDER_ERREUR_PDF.hauteur;
    calculerEchelleBaseDoc(doc);
    reinitialiserZoomDoc(doc);
    doc.etiquettePage.textContent = message;
    doc.etiquettePage.classList.add("erreur-pdf");
    doc.boutonPagePrecedente.style.visibility = "hidden";
    doc.boutonPageSuivante.style.visibility = "hidden";
  }

  function afficherPagePdf(doc) {
    doc.pdfDoc.getPage(doc.pageNum).then(function (page) {
      var viewport = page.getViewport({ scale: ECHELLE_RENDU_PDF });
      doc.canvas.width = viewport.width;
      doc.canvas.height = viewport.height;
      var ctxPdf = doc.canvas.getContext("2d");
      return page.render({ canvasContext: ctxPdf, viewport: viewport }).promise.then(function () {
        doc.largeurNaturelle = viewport.width;
        doc.hauteurNaturelle = viewport.height;
        calculerEchelleBaseDoc(doc);
        reinitialiserZoomDoc(doc);
        doc.etiquettePage.textContent = "page " + doc.pageNum + " sur " + doc.pageCount;
        doc.boutonPagePrecedente.style.visibility = doc.pageNum > 1 ? "visible" : "hidden";
        doc.boutonPageSuivante.style.visibility = doc.pageNum < doc.pageCount ? "visible" : "hidden";
      });
    }).catch(function (erreur) {
      afficherErreurPdf(doc, "page illisible");
      console.error("Erreur d'affichage de la page PDF :", erreur);
    });
  }

  function changerPagePdf(doc, delta) {
    if (!doc.pdfDoc) return;
    var nouvellePage = doc.pageNum + delta;
    if (nouvellePage < 1 || nouvellePage > doc.pageCount) return;
    doc.pageNum = nouvellePage;
    afficherPagePdf(doc);
  }

  // Charge un PDF depuis son adresse ("adresse" est tout ce que
  // "fetch" sait lire : une adresse locale temporaire "blob:", ou
  // plus tard une vraie adresse fournie par Cap). Jamais envoye
  // nulle part : tout reste en memoire dans la page.
  function chargerPdf(doc, adresse) {
    fetch(adresse).then(function (reponse) {
      return reponse.arrayBuffer();
    }).then(function (tampon) {
      return pdfjsLib.getDocument({ data: new Uint8Array(tampon) }).promise;
    }).then(function (pdfDoc) {
      doc.pdfDoc = pdfDoc;
      doc.pageCount = pdfDoc.numPages;
      doc.pageNum = 1;
      afficherPagePdf(doc);
    }).catch(function (erreur) {
      afficherErreurPdf(doc, "PDF illisible");
      console.error("Erreur de lecture du PDF :", erreur);
    });
  }

  // Ajoute un document dans l'espace partage (image ou PDF), sans
  // retirer les documents deja presents : il apparait au premier
  // plan (ajoute en dernier dans #zone-image). Ignore silencieusement
  // au-dela de la limite de 12 documents. "adresse" est une adresse
  // utilisable par <img>/fetch (adresse locale temporaire ou adresse
  // reelle fournie par Cap) ; "titre" sert a reconnaitre un PDF
  // (extension ".pdf") et a l'affichage eventuel du nom par la page
  // qui utilise ce bloc.
  function ajouterDocumentDepuisAdresse(adresse, titre) {
    if (documentsListe.length >= LIMITE_DOCUMENTS) return;

    var estPdf = estUnPdf(titre);
    var carte = document.createElement("div");
    carte.className = "carte-document";

    var doc = {
      id: ++compteurDocuments,
      adresse: adresse,
      titre: titre,
      estPdf: estPdf,
      carte: carte,
      zoomEchelle: 1,
      zoomX: 0,
      zoomY: 0,
      echelleBase: 1,
      largeurNaturelle: 1,
      hauteurNaturelle: 1,
      pointeurs: {},
      distanceDepartPincement: 0,
      echelleDepartPincement: 1,
      dernierePositionPincement: { x: 0, y: 0 },
      departGlissement: null,
      dernierAppuiTemps: 0,
      minuteurAppuiLong: null,
      positionAppuiLong: null,
      auPremierPlan: true
    };

    if (estPdf) {
      var canvasEl = document.createElement("canvas");
      canvasEl.className = "image-document";
      carte.appendChild(canvasEl);
      doc.canvas = canvasEl;
      doc.elementVisuel = canvasEl;
      doc.pageNum = 1;
      doc.pageCount = 1;

      var etiquettePage = document.createElement("div");
      etiquettePage.className = "etiquette-page-pdf";
      etiquettePage.textContent = "chargement...";
      carte.appendChild(etiquettePage);
      doc.etiquettePage = etiquettePage;

      var boutonPagePrecedente = document.createElement("button");
      boutonPagePrecedente.className = "bouton-page-pdf bouton-page-precedente";
      boutonPagePrecedente.textContent = "\u2039";
      boutonPagePrecedente.title = "Page precedente";
      boutonPagePrecedente.style.visibility = "hidden";
      boutonPagePrecedente.addEventListener("click", function (e) {
        e.stopPropagation();
        changerPagePdf(doc, -1);
      });
      carte.appendChild(boutonPagePrecedente);
      doc.boutonPagePrecedente = boutonPagePrecedente;

      var boutonPageSuivante = document.createElement("button");
      boutonPageSuivante.className = "bouton-page-pdf bouton-page-suivante";
      boutonPageSuivante.textContent = "\u203a";
      boutonPageSuivante.title = "Page suivante";
      boutonPageSuivante.style.visibility = "hidden";
      boutonPageSuivante.addEventListener("click", function (e) {
        e.stopPropagation();
        changerPagePdf(doc, 1);
      });
      carte.appendChild(boutonPageSuivante);
      doc.boutonPageSuivante = boutonPageSuivante;

      attacherEvenementsImage(doc);
      chargerPdf(doc, adresse);
    } else {
      var imgEl = document.createElement("img");
      imgEl.className = "image-document";
      imgEl.alt = titre || "";
      carte.appendChild(imgEl);
      doc.elementVisuel = imgEl;
      imgEl.onload = function () {
        doc.largeurNaturelle = imgEl.naturalWidth || 1;
        doc.hauteurNaturelle = imgEl.naturalHeight || 1;
        calculerEchelleBaseDoc(doc);
        reinitialiserZoomDoc(doc);
      };
      imgEl.src = adresse;
      attacherEvenementsImage(doc);
    }

    var boutonRetirer = document.createElement("button");
    boutonRetirer.className = "bouton-retirer-document";
    boutonRetirer.textContent = "\u00d7";
    boutonRetirer.title = "Retirer ce document";
    boutonRetirer.addEventListener("click", function (e) {
      e.stopPropagation();
      retirerDocument(doc);
    });
    carte.appendChild(boutonRetirer);

    zoneImage.appendChild(carte);
    documentsListe.push(doc);
    zoneImage.classList.add("visible");
  }

  // Retire un document de l'espace partage. Si l'adresse est une
  // adresse locale temporaire ("blob:"), elle est liberee (plus
  // besoin de la memoire qu'elle occupait).
  function retirerDocument(doc) {
    var idx = documentsListe.indexOf(doc);
    if (idx < 0) return;
    if (doc.minuteurAppuiLong) clearTimeout(doc.minuteurAppuiLong);
    if (doc.estPdf && doc.pdfDoc) {
      doc.pdfDoc.destroy();
    }
    if (doc.adresse && doc.adresse.indexOf("blob:") === 0) {
      URL.revokeObjectURL(doc.adresse);
    }
    doc.carte.remove();
    documentsListe.splice(idx, 1);
    if (documentsListe.length === 0) {
      zoneImage.classList.remove("visible");
    }
  }

  function fermerTout() {
    documentsListe.slice().forEach(retirerDocument);
  }

  // ==============================================================
  // FONCTIONS PUBLIQUES - A BRANCHER DANS CAP
  // ==============================================================

  // A BRANCHER DANS CAP : affiche UN document dans l'espace partage,
  // sans retirer ceux deja affiches. "adresse" doit pouvoir etre lue
  // par <img src="..."> et par "fetch(...)" (adresse locale "blob:",
  // ou adresse fournie par Cap). "titre" sert a reconnaitre un PDF
  // (il doit se terminer par ".pdf") et, si besoin, a l'affichage du
  // nom par la page appelante.
  function montrerFichier(adresse, titre) {
    ajouterDocumentDepuisAdresse(adresse, titre);
  }

  // A BRANCHER DANS CAP : affiche PLUSIEURS documents d'un coup.
  // "liste" est un tableau d'objets { adresse: "...", titre: "..." }.
  // Chaque document respecte la meme limite de 12 (ceux en trop sont
  // ignores silencieusement, comme pour montrerFichier).
  function montrerPlusieurs(liste) {
    if (!liste) return;
    for (var i = 0; i < liste.length; i++) {
      if (documentsListe.length >= LIMITE_DOCUMENTS) break;
      montrerFichier(liste[i].adresse, liste[i].titre);
    }
  }

  // A BRANCHER DANS CAP : ferme TOUS les documents actuellement
  // affiches et vide l'espace partage.
  function fermer() {
    fermerTout();
  }

  window.Visualiseur = {
    montrerFichier: montrerFichier,
    montrerPlusieurs: montrerPlusieurs,
    fermer: fermer
  };
})();
/* ================================================================
   FIN DU BLOC VISUALISEUR
   ================================================================ */
