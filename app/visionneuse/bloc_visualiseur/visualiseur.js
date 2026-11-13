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
    var centreY = zoneH / 2 + doc.zoomY + (doc.decalageDefilement || 0); // c119 : centre de la partie VISIBLE de la mosaique
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
      // 11/11/2026 (Claude Code, accord de Max, c114) : pour reconnaitre un toucher SIMPLE (court, sans glisser).
      if (nbPointeursDoc(doc) === 1) { doc.aBouge = false; doc.debutAppui = performance.now(); } else { doc.aBouge = true; }
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
        // 11/11/2026 (c114) : un glissement de plus de quelques pixels n'est pas un toucher simple.
        if (Math.abs(e.clientX - doc.departGlissement.x) + Math.abs(e.clientY - doc.departGlissement.y) > SEUIL_DEPLACEMENT_APPUI_LONG) doc.aBouge = true;
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
        // 11/11/2026 (Claude Code, accord de Max, c114) : document agrandi depuis la mosaique d'un chantier : un toucher
        // SIMPLE (court, sans glisser, sans second toucher dans le delai du double appui) le remet a sa place. Le double
        // appui, le pincement et le glissement gardent EXACTEMENT leur comportement.
        if (doc.surToucherSimple && !doc.aBouge && maintenant - (doc.debutAppui || 0) < DUREE_APPUI_LONG - 100) {
          var tempsAppui = maintenant;
          clearTimeout(doc.minuteurToucherSimple);
          doc.minuteurToucherSimple = setTimeout(function () {
            doc.minuteurToucherSimple = null;
            if (doc.dernierAppuiTemps === tempsAppui && doc.surToucherSimple) {
              doc.dernierAppuiTemps = 0;
              doc.surToucherSimple();
            }
          }, SEUIL_DOUBLE_APPUI + 30);
        }
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
    if (doc.minuteurToucherSimple) clearTimeout(doc.minuteurToucherSimple); // c114
    if (doc.estPdf && doc.pdfDoc) {
      doc.pdfDoc.destroy();
    }
    if (doc.adresse && doc.adresse.indexOf("blob:") === 0) {
      URL.revokeObjectURL(doc.adresse);
    }
    doc.carte.remove();
    documentsListe.splice(idx, 1);
    if (documentsListe.length === 0 && !miniatures.length) { // c114 : la mosaique garde la zone visible
      zoneImage.classList.remove("visible");
    }
    if (doc === docAgrandi) finirAgrandi(); // c114 : retire par la croix : la mosaique revient
  }

  // ==============================================================
  // 11/11/2026 (Claude Code, accord de Max, c114) : MOSAIQUE D'UN CHANTIER
  // Cap donne le nombre de documents, puis chaque miniature (petite image JPEG faite par Cap) des qu'elle est prete.
  // Les miniatures sont rangees en grille dans l'espace partage (cases egales ; au-dela de ce qui tient, la zone
  // defile). Un toucher sur une miniature : Cap lit le document entier et l'ouvre ICI comme n'importe quel document
  // (meme zoom, meme deplacement, memes pages de PDF) ; la mosaique se cache dessous. Un toucher simple sur le document
  // agrandi (ou sa croix) le retire et la mosaique revient, a la meme place. Un seul document entier a la fois.
  // ==============================================================
  var miniatures = [];
  var docAgrandi = null;
  var surFinAgrandi = null;
  var defilementMosaique = 0;
  var LARGEUR_MIN_MINIATURE = 110;

  function placerMosaique() {
    var n = miniatures.length;
    if (!n) return;
    var W = zoneImage.clientWidth || 1;
    var H = zoneImage.clientHeight || 1;
    // Le plus grand carre de case qui fait tout tenir ; si les cases deviennent trop petites, largeur minimale et
    // la zone defile vers le bas.
    var colonnes = 1, meilleure = 0;
    for (var c = 1; c <= n; c++) {
      var t = Math.min(W / c, H / Math.ceil(n / c));
      if (t > meilleure) { meilleure = t; colonnes = c; }
    }
    if (W / colonnes < LARGEUR_MIN_MINIATURE) colonnes = Math.max(1, Math.floor(W / LARGEUR_MIN_MINIATURE));
    var lignes = Math.ceil(n / colonnes);
    var cw = W / colonnes;
    var ch = Math.max(H / lignes, cw);
    if (lignes * ch > H && H / lignes >= cw * 0.75) ch = H / lignes;
    var marge = 6;
    for (var i = 0; i < n; i++) {
      if (miniatures[i].deplacee) continue; // c121 : une miniature posee par Max garde sa place
      var s = miniatures[i].carte.style;
      s.left = ((i % colonnes) * cw + marge) + "px";
      s.top = (Math.floor(i / colonnes) * ch + marge) + "px";
      s.width = (cw - 2 * marge) + "px";
      s.height = (ch - 2 * marge) + "px";
    }
  }

  function montrerMosaique(nombre, surToucher) {
    fermerMosaique();
    for (var i = 0; i < nombre; i++) {
      (function (index) {
        var carte = document.createElement("div");
        carte.className = "carte-document carte-miniature miniature-en-chargement";
        carte.setAttribute("role", "button");
        carte.setAttribute("aria-label", "Document " + (index + 1));
        var img = document.createElement("img");
        img.className = "image-miniature";
        img.alt = "";
        carte.appendChild(img);
        carte.addEventListener("click", function () {
          if (ignorerClic) { ignorerClic = false; return; } // c121 : le lever d'un deplacement n'est pas un toucher
          if (docAgrandi || typeof surToucher !== "function") return;
          surToucher(index);
        });
        zoneImage.appendChild(carte);
        var m = { carte: carte, img: img, deplacee: false };
        miniatures.push(m);
        brancherDeplacement(m); // c121
      })(i);
    }
    zoneImage.classList.add("visible", "en-mosaique");
    zoneImage.style.overflowY = "auto"; // beaucoup de miniatures : la zone defile
    placerMosaique();
  }

  // ==============================================================
  // 11/11/2026 (Claude Code, accord de Max, c121, marche 3) : DEPLACER UNE MINIATURE. Appui long (environ 0,5 s) sur une
  // miniature : elle est saisie (elle se souleve) ; on la glisse ; on la pose en levant le doigt. Elle garde cette place
  // (le reste de la mosaique ne bouge pas). Un toucher court garde son sens (plein ecran) ; un doigt qui bouge avant la
  // demi-seconde annule la saisie. Pas pendant qu'un document est agrandi. Rangement en memoire seulement (rien
  // d'enregistre) ; "comme au depart" le remet en grille.
  // ==============================================================
  var DUREE_SAISIE = 500;
  var ignorerClic = false;
  var arrangementModifie = false;
  // 11/11/2026 (c122, defaut vu par Max) : UNE SEULE image active a la fois, et plus de blocage. Avant (c121) : chaque
  // miniature gardait son propre geste en cours, efface seulement par SON propre lever ; un lever perdu (doigt leve
  // ailleurs) la bloquait pour toujours ; et la miniature saisie etait DEPLACEE dans la page pendant le geste (pour passer
  // devant), ce qui peut faire perdre le doigt au telephone. Maintenant : un seul geste pour toute la mosaique ; un nouvel
  // appui termine l'ancien geste ; le lever est attrape ou qu'il arrive ; la miniature saisie passe devant par son plan
  // (z-index), sans bouger dans la page ; l'ancienne reste exactement ou elle est.
  var geste = null;      // { m, id, x, y, left, top, saisie, minuteur }
  var planMiniatures = 0; // plan de la derniere miniature prise en main
  function terminerGeste() {
    var g = geste;
    if (!g) return;
    geste = null;
    clearTimeout(g.minuteur);
    if (!g.saisie) return;
    g.m.carte.classList.remove("miniature-saisie");
    if (parseFloat(g.m.carte.style.left) !== g.left || parseFloat(g.m.carte.style.top) !== g.top) { g.m.deplacee = true; arrangementModifie = true; }
    ignorerClic = true; // le "click" qui suit ce lever n'ouvre pas le document
    setTimeout(function () { ignorerClic = false; }, 400);
  }
  function brancherDeplacement(m) {
    var carte = m.carte;
    carte.addEventListener("pointerdown", function (e) {
      if (docAgrandi || defilementDeuxDoigts) return; // c160 : deux doigts qui font defiler la mosaique : pas de saisie
      terminerGeste(); // une seule image active : l'ancien geste (meme perdu) s'arrete, l'image reste ou elle est
      var g = { m: m, id: e.pointerId, x: e.clientX, y: e.clientY, left: parseFloat(carte.style.left) || 0, top: parseFloat(carte.style.top) || 0, saisie: false, minuteur: null };
      geste = g;
      g.minuteur = setTimeout(function () {
        if (geste !== g || docAgrandi) return;
        g.saisie = true;
        carte.classList.add("miniature-saisie");
        carte.style.zIndex = String(++planMiniatures); // devant les autres, SANS bouger dans la page
        try { carte.setPointerCapture(g.id); } catch (err) { /* rien */ }
      }, DUREE_SAISIE);
    });
    carte.addEventListener("pointermove", function (e) {
      var g = geste;
      if (!g || g.m !== m || e.pointerId !== g.id) return;
      var dx = e.clientX - g.x, dy = e.clientY - g.y;
      if (!g.saisie) {
        if (Math.abs(dx) + Math.abs(dy) > SEUIL_DEPLACEMENT_APPUI_LONG) terminerGeste(); // pas un appui long
        return;
      }
      carte.style.left = (g.left + dx) + "px";
      carte.style.top = (g.top + dy) + "px";
    });
  }
  // Le lever (ou l'annulation) de CE doigt termine le geste, ou qu'il arrive dans la page.
  function finDuDoigt(e) { if (geste && e.pointerId === geste.id) terminerGeste(); }
  document.addEventListener("pointerup", finDuDoigt, true);
  document.addEventListener("pointercancel", finDuDoigt, true);
  document.addEventListener("lostpointercapture", function (e) { if (geste && geste.saisie && e.pointerId === geste.id) terminerGeste(); }, true);

  // ==============================================================
  // 12/11/2026 (Claude Code, accord de Max, c160) : FAIRE DEFILER LA MOSAIQUE A DEUX DOIGTS. Regle de Max : la zone ou
  // tombent les deux doigts decide. Deux doigts sur la MEME miniature : reserve au zoom de cette case (plus tard) ; ici,
  // rien ne change. Deux doigts ailleurs (sur l'eau, ou sur deux cases differentes, l'eau n'etant visible qu'entre les
  // cases quand la mosaique depasse l'ecran) : la mosaique suit les deux doigts, seulement s'il y a de quoi defiler.
  // Un doigt seul : rien ne change (ondes sur l'eau, toucher, appui long). Pas pendant un document agrandi, ni pendant
  // qu'une miniature saisie est deplacee. Le lever de ces doigts n'ouvre aucun document.
  // ==============================================================
  var doigtsMosaique = {};          // pointerId -> { y, carte }
  var defilementDeuxDoigts = false;
  var moyenneDefilement = 0;
  function doigtsPoses() { var l = []; for (var k in doigtsMosaique) l.push(doigtsMosaique[k]); return l; }
  function moyenneDoigts() { var l = doigtsPoses(), t = 0; for (var i = 0; i < l.length; i++) t += l[i].y; return l.length ? t / l.length : 0; }
  zoneImage.addEventListener("pointerdown", function (e) {
    if (!zoneImage.classList.contains("en-mosaique") || docAgrandi) return;
    doigtsMosaique[e.pointerId] = { y: e.clientY, carte: (e.target && e.target.closest) ? e.target.closest(".carte-miniature") : null };
    var l = doigtsPoses();
    if (l.length < 2 || defilementDeuxDoigts) { moyenneDefilement = moyenneDoigts(); return; }
    if (geste && geste.saisie) return; // une miniature saisie est en train d'etre deplacee : elle garde la main
    if (l[0].carte && l[0].carte === l[1].carte) return; // deux doigts sur la meme miniature : zoom de la case (plus tard)
    defilementDeuxDoigts = true;
    terminerGeste(); // l'appui long eventuel du premier doigt est annule
    moyenneDefilement = moyenneDoigts();
  }, true);
  document.addEventListener("pointermove", function (e) {
    var d = doigtsMosaique[e.pointerId];
    if (!d) return;
    d.y = e.clientY;
    if (!defilementDeuxDoigts || docAgrandi || doigtsPoses().length < 2) return;
    var m = moyenneDoigts();
    if (zoneImage.scrollHeight > zoneImage.clientHeight) zoneImage.scrollTop -= (m - moyenneDefilement);
    moyenneDefilement = m;
  }, true);
  function finDoigtMosaique(e) {
    if (!doigtsMosaique[e.pointerId]) return;
    delete doigtsMosaique[e.pointerId];
    moyenneDefilement = moyenneDoigts();
    if (defilementDeuxDoigts) { ignorerClic = true; setTimeout(function () { ignorerClic = false; }, 400); }
    if (!doigtsPoses().length) defilementDeuxDoigts = false;
  }
  document.addEventListener("pointerup", finDoigtMosaique, true);
  document.addEventListener("pointercancel", finDoigtMosaique, true);

  function remettreMosaiqueCommeAuDepart() {
    terminerGeste(); // c122
    planMiniatures = 0;
    for (var i = 0; i < miniatures.length; i++) {
      miniatures[i].deplacee = false;
      miniatures[i].carte.style.zIndex = ""; // c122 : plan d'origine
      zoneImage.appendChild(miniatures[i].carte); // ordre d'origine
    }
    if (docAgrandi) zoneImage.appendChild(docAgrandi.carte); // le document agrandi reste au-dessus
    arrangementModifie = false;
    placerMosaique();
  }

  function remplirMiniature(index, adresse) {
    var m = miniatures[index];
    if (!m) return;
    m.img.src = adresse;
    m.carte.classList.remove("miniature-en-chargement", "miniature-illisible");
    if (m.texte) { m.texte.remove(); m.texte = null; } // c117 : la miniature est arrivee ensuite
  }

  // 11/11/2026 (Claude Code, accord de Max, c117) : la case DIT pourquoi elle n'a pas de miniature (texte donne par Cap,
  // jamais le nom du fichier) ; elle reste touchable : le document s'ouvre quand meme.
  function miniatureIllisible(index, texte) {
    var m = miniatures[index];
    if (!m) return;
    m.carte.classList.remove("miniature-en-chargement");
    m.carte.classList.add("miniature-illisible");
    if (!m.texte) {
      m.texte = document.createElement("span");
      m.texte.className = "texte-miniature";
      m.carte.appendChild(m.texte);
    }
    m.texte.textContent = texte || "Miniature impossible. Touche pour l'ouvrir.";
  }

  // 11/11/2026 (c120) : "index" = la miniature agrandie : SA case disparait pendant l'agrandi (sinon on la voit en double) ;
  // elle revient quand le document est remis a sa place. Les autres ne bougent pas.
  var miniatureAgrandie = -1;
  function agrandirDepuisMosaique(adresse, titre, surFin, index) {
    if (docAgrandi) retirerDocument(docAgrandi);
    terminerGeste(); // c122
    miniatureAgrandie = typeof index === "number" && miniatures[index] ? index : -1;
    if (miniatureAgrandie >= 0) miniatures[miniatureAgrandie].carte.style.visibility = "hidden";
    // 11/11/2026 (Claude Code, accord de Max, c119, marche 2) : la mosaique RESTE VISIBLE derriere le document agrandi,
    // a sa place (ni cachee, ni defilee) ; seul son defilement est bloque pendant l'agrandi. Le document est pose par-dessus,
    // au centre de la partie visible. Avant (c114) : miniatures cachees et mosaique remontee en haut.
    defilementMosaique = zoneImage.scrollTop;
    zoneImage.classList.add("agrandi-sur-mosaique");
    zoneImage.style.overflowY = "hidden";
    ajouterDocumentDepuisAdresse(adresse, titre);
    docAgrandi = documentsListe[documentsListe.length - 1] || null;
    if (docAgrandi) docAgrandi.decalageDefilement = defilementMosaique; // applique au chargement de l'image ou de la page
    if (docAgrandi) docAgrandi.carte.style.zIndex = "100000"; // c122 : toujours devant les miniatures, meme relevees
    surFinAgrandi = surFin || null;
    if (docAgrandi) docAgrandi.surToucherSimple = function () { retirerDocument(docAgrandi); };
    else finirAgrandi();
  }

  function finirAgrandi() {
    docAgrandi = null;
    zoneImage.classList.remove("agrandi-sur-mosaique"); // c119 (avant : "mosaique-cachee", miniatures cachees)
    if (miniatureAgrandie >= 0 && miniatures[miniatureAgrandie]) miniatures[miniatureAgrandie].carte.style.visibility = ""; // c120
    miniatureAgrandie = -1;
    if (miniatures.length) zoneImage.style.overflowY = "auto";
    zoneImage.scrollTop = defilementMosaique;
    var rappel = surFinAgrandi;
    surFinAgrandi = null;
    if (rappel) { try { rappel(); } catch (e) { /* rien */ } }
  }

  function fermerMosaique() {
    if (docAgrandi) retirerDocument(docAgrandi);
    for (var i = 0; i < miniatures.length; i++) miniatures[i].carte.remove();
    miniatures = [];
    zoneImage.classList.remove("en-mosaique", "agrandi-sur-mosaique");
    zoneImage.style.overflowY = "";
    if (!documentsListe.length) zoneImage.classList.remove("visible");
  }

  window.addEventListener("resize", placerMosaique);

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
    fermerMosaique(); // c114
    fermerTout();
  }

  window.Visualiseur = {
    montrerFichier: montrerFichier,
    montrerPlusieurs: montrerPlusieurs,
    fermer: fermer,
    // 11/11/2026 (Claude Code, accord de Max, c114) : la mosaique d'un chantier.
    montrerMosaique: montrerMosaique,
    remplirMiniature: remplirMiniature,
    miniatureIllisible: miniatureIllisible,
    agrandirDepuisMosaique: agrandirDepuisMosaique,
    // 11/11/2026 (Claude Code, accord de Max, c118) : chaque document ouvert reprend sa taille et sa place d'ouverture.
    remettreCommeAuDepart: function () {
      for (var i = 0; i < documentsListe.length; i++) reinitialiserZoomDoc(documentsListe[i]);
      remettreMosaiqueCommeAuDepart(); // c121 : la mosaique aussi, rangement compris
    },
    arrangementModifie: function () { return arrangementModifie; }, // c121 : repere en memoire seulement
    documentAgrandi: function () { return Boolean(docAgrandi); }
  };
})();
/* ================================================================
   FIN DU BLOC VISUALISEUR
   ================================================================ */
