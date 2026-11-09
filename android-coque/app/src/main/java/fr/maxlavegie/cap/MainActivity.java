package fr.maxlavegie.cap;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.MediaStore;
import android.widget.Toast;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.graphics.Color;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.ServiceWorkerClient;
import android.webkit.ServiceWorkerController;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;

import androidx.browser.customtabs.CustomTabsIntent;
import androidx.core.content.FileProvider;

import com.google.android.gms.tasks.Tasks;
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.documentscanner.GmsDocumentScanner;
import com.google.mlkit.vision.documentscanner.GmsDocumentScannerOptions;
import com.google.mlkit.vision.documentscanner.GmsDocumentScanning;
import com.google.mlkit.vision.documentscanner.GmsDocumentScanningResult;
import com.google.mlkit.vision.text.Text;
import com.google.mlkit.vision.text.TextRecognition;
import com.google.mlkit.vision.text.TextRecognizer;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

// Coque Android qui ouvre Cap tel qu'il est en ligne aujourd'hui (la version web publiée),
// dans une fenêtre plein écran sans barre d'adresse, avec en plus le pont du micro (étape B) :
// la reconnaissance vocale d'Android remplace celle de Chrome, qu'une coque WebView ne sait pas
// faire toute seule. Le site web lui-même n'est pas modifié : seul un petit script est injecté
// dans la page pour qu'elle retrouve la même fonction `SpeechRecognition` qu'elle utilise déjà.
//
// Étape C (réparation de la connexion Google) : Google refuse d'afficher son écran de connexion
// dans une fenêtre WebView embarquée (sécurité anti-hameçonnage). On ouvre donc cet écran dans le
// vrai Chrome sécurisé du téléphone (Custom Tabs), et quand Google a fini, il renvoie vers
// l'adresse de Cap ; la coque reconnaît cette adresse (voir AndroidManifest.xml) et se rouvre
// directement dessus, pour que la page retrouve son jeton exactement comme sur le web.
public class MainActivity extends Activity {

    private static final String URL_CAP = "https://maxlavegie-dev.github.io/cap/app/";
    private static final int CODE_PERMISSION_MICRO = 100;
    private static final int CODE_PERMISSION_CAMERA_PAGE = 101;
    private static final int CODE_PERMISSION_CAMERA_PHOTO = 102;
    private static final int CODE_PHOTO = 200;
    private static final int CODE_SCANNER = 300;
    // Numérisation, étape 3 (05/11/2026) : pages du scanner de Google, servies à Cap depuis ce
    // dossier temporaire privé, puis effacées (à la demande de Cap, et à chaque démarrage).
    private static final String PREFIXE_SCANS = "/cap/app/__coque__/scan/";
    private boolean scanEnCours = false;

    // Caméra (05/11/2026) : demande de caméra de la page en attente de l'accord d'Android, et
    // bouton « appareil photo du téléphone » en attente de la photo.
    private PermissionRequest demandeCameraEnAttente;
    private ValueCallback<Uri[]> retourPhotoEnAttente;
    private Uri photoEnCours;
    private File fichierPhotoEnCours;

    // Petit script injecté dans la page : il fabrique une classe qui ressemble à la vraie
    // SpeechRecognition du navigateur, mais qui parle en coulisses avec le code Android ci-dessous.
    // dictee.js (dans l'appli web) ne voit aucune différence : mêmes réglages, mêmes évènements.
    private static final String SCRIPT_PONT_MICRO =
        "(function(){"
        + "function PontMicro(){"
        + "this.lang='fr-FR';this.interimResults=true;this.continuous=false;this.maxAlternatives=1;"
        + "this.onresult=null;this.onerror=null;this.onend=null;this.onstart=null;"
        + "}"
        + "PontMicro.prototype.start=function(){"
        + "if(window.__pontMicroActif){return;}"
        + "window.__pontMicroActif=this;"
        + "if(typeof this.onstart==='function'){this.onstart();}"
        + "window.PontMicroAndroid.demarrerEcoute(this.lang||'fr-FR');"
        + "};"
        + "PontMicro.prototype.stop=function(){window.PontMicroAndroid.arreterEcoute();};"
        + "PontMicro.prototype.abort=function(){window.PontMicroAndroid.arreterEcoute();};"
        + "window.__pontRecevoirResultat=function(texte,estFinal){"
        + "var instance=window.__pontMicroActif;"
        + "if(!instance||typeof instance.onresult!=='function'){return;}"
        + "var segment=[{transcript:texte}];segment.isFinal=estFinal;"
        + "instance.onresult({resultIndex:0,results:[segment]});"
        + "};"
        + "window.__pontRecevoirErreur=function(code){"
        + "var instance=window.__pontMicroActif;"
        + "if(instance&&typeof instance.onerror==='function'){instance.onerror({error:code});}"
        + "};"
        + "window.__pontRecevoirFin=function(){"
        + "var instance=window.__pontMicroActif;window.__pontMicroActif=null;"
        + "if(instance&&typeof instance.onend==='function'){instance.onend();}"
        + "};"
        + "window.SpeechRecognition=PontMicro;"
        + "window.webkitSpeechRecognition=PontMicro;"
        + "})();";

    private FrameLayout racine;
    private WebView vue;
    // Fond de Cap (06/11/2026, lot c20) : pâle, couleur de l'eau. La vraie valeur vient de la page
    // (fond de <body>, réglage unique dans style.css) dès qu'elle est chargée ; celle-ci sert avant.
    private static final int FOND_PAR_DEFAUT = Color.parseColor("#EAF1F4");
    private SpeechRecognizer reconnaisseur;
    private boolean ecouteEnCours = false;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        demanderPermissionMicroSiBesoin();

        reconnaisseur = SpeechRecognizer.createSpeechRecognizer(this);
        reconnaisseur.setRecognitionListener(new EcouteurReconnaissance());

        vue = new WebView(this);
        WebSettings reglages = vue.getSettings();
        reglages.setJavaScriptEnabled(true);
        reglages.setDomStorageEnabled(true);
        reglages.setDatabaseEnabled(true);
        reglages.setMediaPlaybackRequiresUserGesture(false);
        vue.addJavascriptInterface(new PontMicroAndroid(), "PontMicroAndroid");
        vue.addJavascriptInterface(new ScannerAndroid(), "ScannerAndroid");
        vue.addJavascriptInterface(new CouleursAndroid(), "CouleursAndroid");
        vue.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
                view.evaluateJavascript(SCRIPT_PONT_MICRO, null);
            }

            // Lot c20 : la bande sous l'heure et sous la barre de navigation prend la couleur de fond
            // de la page (un seul réglage, dans style.css).
            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                view.evaluateJavascript("(function(){try{return getComputedStyle(document.body).backgroundColor;}catch(e){return '';}})()",
                    valeur -> appliquerFondDepuisPage(valeur));
            }

            // Version « essai » seulement : voir reponseLocale. Dans la coque normale, renvoie null.
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                WebResourceResponse scan = reponseScan(request.getUrl());
                if (scan != null) return scan;
                WebResourceResponse locale = reponseLocale(request.getUrl());
                return locale != null ? locale : super.shouldInterceptRequest(view, request);
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri adresse = request.getUrl();
                if ("accounts.google.com".equals(adresse.getHost())) {
                    ouvrirDansChromeSecurise(adresse);
                    return true;
                }
                // 09/11/2026 (petit tableur) : « Ouvrir le tableur » (Réglages) ouvre le tableur HORS de Cap
                // (appli Google Sheets si elle est là, sinon Chrome) : Cap reste ouvert derrière.
                if ("docs.google.com".equals(adresse.getHost()) && "https".equals(adresse.getScheme())) {
                    ouvrirHorsDeCap(adresse);
                    return true;
                }
                return false;
            }
        });

        vue.setWebChromeClient(new WebChromeClient() {
            // Le scanner de Cap demande la caméra (getUserMedia). Accordée seulement aux pages de
            // Cap, seulement la vidéo, et seulement si Max a autorisé la caméra dans Android.
            @Override
            public void onPermissionRequest(final PermissionRequest demande) {
                runOnUiThread(() -> traiterDemandeCamera(demande));
            }

            @Override
            public void onPermissionRequestCanceled(PermissionRequest demande) {
                if (demande == demandeCameraEnAttente) demandeCameraEnAttente = null;
            }

            // Bouton « appareil photo du téléphone » (champ fichier de Cap).
            @Override
            public boolean onShowFileChooser(WebView vueWeb, ValueCallback<Uri[]> retour,
                                             FileChooserParams parametres) {
                return ouvrirChoixPhoto(retour, parametres);
            }
        });

        // Cap installe un service worker, dont les téléchargements ne passent pas par le WebViewClient :
        // les pages du scanner (toutes versions) et, en version « essai », les fichiers de Cap de l'APK.
        ServiceWorkerController.getInstance().setServiceWorkerClient(new ServiceWorkerClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebResourceRequest request) {
                WebResourceResponse scan = reponseScan(request.getUrl());
                return scan != null ? scan : reponseLocale(request.getUrl());
            }
        });

        racine = new FrameLayout(this);
        racine.addView(vue, new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(racine);
        configurerBarresDuTelephone();

        effacerAncienDiagnostic();
        viderPhotosTemporaires();
        viderScans();
        String adresseDepart = adresseDeDepart(getIntent());
        vue.loadUrl(adresseDepart);
    }

    @Override
    protected void onNewIntent(Intent intention) {
        super.onNewIntent(intention);
        setIntent(intention);
        String adresseRetour = adresseDeRetourGoogle(intention);
        if (adresseRetour != null && vue != null) {
            chargerAdresseRetour(adresseRetour);
        }
    }

    // Étape C.4 (05/11/2026) : quand la coque est restée ouverte pendant la connexion, Cap est déjà
    // affiché sur la même page que l'adresse de retour ; seule la partie après « # » (le jeton)
    // change. Dans ce cas, le navigateur ne recharge pas la page et Cap ne lit jamais le jeton
    // (il ne le lit qu'au démarrage, dans google_connexion.js). On force donc un vrai
    // rechargement sur l'adresse de retour, exactement comme Google le fait sur le web.
    private void chargerAdresseRetour(String adresseRetour) {
        String actuelle = vue.getUrl();
        if (actuelle != null && sansFragment(actuelle).equals(sansFragment(adresseRetour))) {
            vue.evaluateJavascript("location.replace(" + JSONObject.quote(adresseRetour) + ");"
                + "location.reload();", null);
        } else {
            vue.loadUrl(adresseRetour);
        }
    }

    private static String sansFragment(String adresse) {
        int position = adresse.indexOf('#');
        return position < 0 ? adresse : adresse.substring(0, position);
    }

    // Les diagnostics temporaires (étapes C.1 à C.3) ont été retirés le 05/11/2026. Ils avaient pu
    // écrire le retour de Google, jeton compris, dans ce fichier du téléphone : on l'efface s'il
    // existe encore. Un échec n'empêche jamais la coque de démarrer.
    // ----- Lot c20 (06/11/2026) : plus de barre de titre « Cap ESSAI » ; barres du téléphone transparentes -----
    // L'heure, le réseau et la batterie s'affichent en sombre (lisibles sur un fond très clair) par-dessus
    // une bande de la couleur de fond de Cap. Les pages de Cap restent ENTRE la barre d'état et la barre
    // de navigation (et au-dessus du clavier) : aucun bouton ne peut passer dessous.
    @SuppressWarnings("deprecation")
    private void configurerBarresDuTelephone() {
        Window fenetre = getWindow();
        fenetre.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
        fenetre.setStatusBarColor(Color.TRANSPARENT);
        // Lot c21 : la barre du bas n'est plus transparente mais de la couleur envoyée par Cap (celle de
        // l'eau en bas de l'écran) ; transparente, elle laissait voir le fond plat, qui paraissait blanc.
        fenetre.setNavigationBarColor(FOND_PAR_DEFAUT);
        if (Build.VERSION.SDK_INT >= 29) fenetre.setNavigationBarContrastEnforced(false);
        int drapeaux = View.SYSTEM_UI_FLAG_LAYOUT_STABLE | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION;
        if (Build.VERSION.SDK_INT >= 23) drapeaux |= View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
        if (Build.VERSION.SDK_INT >= 26) drapeaux |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
        fenetre.getDecorView().setSystemUiVisibility(drapeaux);
        if (Build.VERSION.SDK_INT >= 30) {
            fenetre.setDecorFitsSystemWindows(false);
            WindowInsetsController controle = fenetre.getInsetsController();
            if (controle != null) {
                int clair = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
                controle.setSystemBarsAppearance(clair, clair);
            }
        }
        racine.setBackgroundColor(FOND_PAR_DEFAUT);
        vue.setBackgroundColor(FOND_PAR_DEFAUT);
        racine.setOnApplyWindowInsetsListener((v, encarts) -> {
            int gauche, haut, droite, bas;
            if (Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets marges = encarts.getInsets(WindowInsets.Type.systemBars()
                    | WindowInsets.Type.ime() | WindowInsets.Type.displayCutout());
                gauche = marges.left; haut = marges.top; droite = marges.right; bas = marges.bottom;
            } else {
                gauche = encarts.getSystemWindowInsetLeft(); haut = encarts.getSystemWindowInsetTop();
                droite = encarts.getSystemWindowInsetRight(); bas = encarts.getSystemWindowInsetBottom();
            }
            v.setPadding(gauche, haut, droite, bas);
            return Build.VERSION.SDK_INT >= 30 ? WindowInsets.CONSUMED : encarts.consumeSystemWindowInsets();
        });
        racine.requestApplyInsets();
    }

    // valeur : « "rgb(234, 241, 244)" » (couleur de fond de <body>) ; rien de lisible : on garde l'actuelle.
    private void appliquerFondDepuisPage(String valeur) {
        if (valeur == null) return;
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([0-9.]+))?\\)").matcher(valeur);
        if (!m.find()) return;
        if (m.group(4) != null && Double.parseDouble(m.group(4)) < 0.99) return;
        int couleur = Color.rgb(Integer.parseInt(m.group(1)), Integer.parseInt(m.group(2)), Integer.parseInt(m.group(3)));
        racine.setBackgroundColor(couleur);
        vue.setBackgroundColor(couleur);
    }

    // Lot c21 : Cap envoie la couleur des deux bandes (« #rrggbb »). Seulement des couleurs, vérifiées.
    private class CouleursAndroid {
        @JavascriptInterface
        public void changer(String haut, String bas) {
            final Integer couleurHaut = couleurHex(haut);
            final Integer couleurBas = couleurHex(bas);
            runOnUiThread(() -> {
                if (couleurHaut != null) {
                    racine.setBackgroundColor(couleurHaut);
                    vue.setBackgroundColor(couleurHaut);
                }
                if (couleurBas != null) getWindow().setNavigationBarColor(couleurBas);
            });
        }
    }

    private static Integer couleurHex(String valeur) {
        if (valeur == null || !valeur.matches("#[0-9a-fA-F]{6}")) return null;
        return Color.parseColor(valeur);
    }

    private void effacerAncienDiagnostic() {
        try {
            File dossier = getExternalFilesDir(null);
            if (dossier == null) return;
            File fichier = new File(dossier, "diagnostic_google.txt");
            if (fichier.exists()) fichier.delete();
        } catch (Exception erreur) {
            // Rien à faire : le fichier sera effacé au prochain démarrage.
        }
    }

    // Au premier lancement normal (icône de l'appli), on ouvre Cap comme d'habitude. Si la coque
    // est relancée directement par le retour de Google (voir AndroidManifest.xml), on ouvre plutôt
    // cette adresse de retour, qui contient le jeton de connexion dans son fragment (#...).
    private String adresseDeDepart(Intent intention) {
        String adresseRetour = adresseDeRetourGoogle(intention);
        return adresseRetour != null ? adresseRetour : URL_CAP;
    }

    private String adresseDeRetourGoogle(Intent intention) {
        if (intention == null || !Intent.ACTION_VIEW.equals(intention.getAction())) return null;
        Uri donnees = intention.getData();
        if (donnees == null || !"maxlavegie-dev.github.io".equals(donnees.getHost())) return null;
        return donnees.toString();
    }

    // Version « essai » (05/11/2026), pour tester sans rien publier : l'adresse reste celle du site
    // en ligne (même mémoire, même retour de Google), mais chaque fichier de Cap est lu dans l'APK
    // (copie du dossier app/ du PC) au lieu d'être téléchargé. Fichier absent : 404, jamais la
    // version en ligne, pour ne pas mélanger deux versions. Coque normale : renvoie toujours null.
    private static final String PREFIXE_CAP = "/cap/app/";

    private WebResourceResponse reponseLocale(Uri adresse) {
        if (!BuildConfig.FICHIERS_LOCAUX || adresse == null) return null;
        if (!"https".equals(adresse.getScheme()) || !"maxlavegie-dev.github.io".equals(adresse.getHost())) return null;
        String chemin = adresse.getPath();
        if (chemin == null || !chemin.startsWith(PREFIXE_CAP)) return null;
        String fichier = chemin.substring(PREFIXE_CAP.length());
        if (fichier.isEmpty()) fichier = "index.html";
        Map<String, String> entetes = new HashMap<>();
        entetes.put("Cache-Control", "no-store");
        if (!fichier.contains("..")) {
            try {
                InputStream flux = getAssets().open(fichier);
                return new WebResourceResponse(typeDe(fichier), "UTF-8", 200, "OK", entetes, flux);
            } catch (IOException erreur) {
                // Fichier absent de l'APK : 404 ci-dessous.
            }
        }
        return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found", entetes,
            new ByteArrayInputStream(new byte[0]));
    }

    private static String typeDe(String fichier) {
        String nom = fichier.toLowerCase();
        if (nom.endsWith(".html")) return "text/html";
        if (nom.endsWith(".js")) return "application/javascript";
        if (nom.endsWith(".css")) return "text/css";
        if (nom.endsWith(".webmanifest")) return "application/manifest+json";
        if (nom.endsWith(".json")) return "application/json";
        if (nom.endsWith(".png")) return "image/png";
        if (nom.endsWith(".svg")) return "image/svg+xml";
        if (nom.endsWith(".ico")) return "image/x-icon";
        if (nom.endsWith(".txt")) return "text/plain";
        return "application/octet-stream";
    }

    // Ouvre l'écran de connexion Google dans le vrai Chrome sécurisé du téléphone (onglet,
    // pas la WebView de la coque) : Google refuse de s'afficher dans une fenêtre embarquée.
    private void ouvrirDansChromeSecurise(Uri adresse) {
        new CustomTabsIntent.Builder().build().launchUrl(this, adresse);
    }

    // 09/11/2026 : lien vers un tableur Google (docs.google.com seulement, voir plus haut).
    private void ouvrirHorsDeCap(Uri adresse) {
        try {
            Intent vue = new Intent(Intent.ACTION_VIEW, adresse);
            vue.addCategory(Intent.CATEGORY_BROWSABLE);
            startActivity(vue);
        } catch (android.content.ActivityNotFoundException erreur) {
            ouvrirDansChromeSecurise(adresse);
        }
    }

    // ----- Numérisation, étape 3 (05/11/2026) : scanner de Google + lecture du texte -----
    // Cap appelle ScannerAndroid.scanner() ; l'écran de scan de Google s'ouvre (bords, nettoyage,
    // plusieurs pages). Au retour, chaque page est copiée dans un dossier temporaire privé, son
    // texte est lu SUR LE TÉLÉPHONE (aucun envoi, aucune IA), puis Cap reçoit, par
    // window.__scannerAndroidResultat, la liste {url, texte} des pages. Aucune autorisation Google.

    private File dossierScans() {
        return new File(getCacheDir(), "scans");
    }

    // Les pages peuvent être des documents personnels : effacées dès que Cap les a prises.
    private void viderScans() {
        File[] fichiers = dossierScans().listFiles();
        if (fichiers == null) return;
        for (File fichier : fichiers) {
            if (!fichier.delete()) fichier.deleteOnExit();
        }
    }

    // Sert une page du scanner à Cap, sous l'adresse de Cap (même origine), depuis le dossier privé.
    private WebResourceResponse reponseScan(Uri adresse) {
        if (adresse == null || !"https".equals(adresse.getScheme())
            || !"maxlavegie-dev.github.io".equals(adresse.getHost())) return null;
        String chemin = adresse.getPath();
        if (chemin == null || !chemin.startsWith(PREFIXE_SCANS)) return null;
        String nom = chemin.substring(PREFIXE_SCANS.length());
        Map<String, String> entetes = new HashMap<>();
        entetes.put("Cache-Control", "no-store");
        if (nom.matches("[A-Za-z0-9_.-]{1,80}") && !nom.contains("..")) {
            try {
                return new WebResourceResponse("image/jpeg", null, 200, "OK", entetes,
                    new java.io.FileInputStream(new File(dossierScans(), nom)));
            } catch (IOException erreur) {
                // Page absente : 404 ci-dessous.
            }
        }
        return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found", entetes,
            new ByteArrayInputStream(new byte[0]));
    }

    private void renvoyerScan(JSONObject resultat) {
        runOnUiThread(() -> appelerJs("window.__scannerAndroidResultat && window.__scannerAndroidResultat("
            + resultat.toString() + ");"));
    }

    private void renvoyerErreurScan(String message) {
        scanEnCours = false;
        try {
            renvoyerScan(new JSONObject().put("erreur", message));
        } catch (Exception ignoree) {
            // JSON impossible : rien à renvoyer.
        }
    }

    private class ScannerAndroid {
        @JavascriptInterface
        public void scanner() {
            runOnUiThread(() -> {
                if (scanEnCours) return;
                scanEnCours = true;
                GmsDocumentScannerOptions options = new GmsDocumentScannerOptions.Builder()
                    .setGalleryImportAllowed(false)
                    .setPageLimit(30)
                    .setResultFormats(GmsDocumentScannerOptions.RESULT_FORMAT_JPEG)
                    .setScannerMode(GmsDocumentScannerOptions.SCANNER_MODE_FULL)
                    .build();
                GmsDocumentScanner scanneur = GmsDocumentScanning.getClient(options);
                scanneur.getStartScanIntent(MainActivity.this)
                    .addOnSuccessListener(intention -> {
                        try {
                            startIntentSenderForResult(intention, CODE_SCANNER, null, 0, 0, 0);
                        } catch (Exception erreur) {
                            renvoyerErreurScan("L’écran de scan de Google n’a pas pu s’ouvrir.");
                        }
                    })
                    .addOnFailureListener(erreur -> renvoyerErreurScan(
                        "Le scanner de Google n’est pas disponible sur ce téléphone pour l’instant "
                        + "(services Google à jour et internet nécessaires la première fois)."));
            });
        }

        // Cap a pris les pages : on les efface du téléphone.
        @JavascriptInterface
        public void oublierPages() {
            viderScans();
        }
    }

    private void recevoirScan(int resultat, Intent donnees) {
        if (resultat != RESULT_OK) {
            scanEnCours = false;
            try { renvoyerScan(new JSONObject().put("annule", true)); } catch (Exception ignoree) { }
            return;
        }
        GmsDocumentScanningResult scan = GmsDocumentScanningResult.fromActivityResultIntent(donnees);
        if (scan == null || scan.getPages() == null || scan.getPages().isEmpty()) {
            renvoyerErreurScan("Le scanner de Google n’a rendu aucune page.");
            return;
        }
        final java.util.List<GmsDocumentScanningResult.Page> pages = scan.getPages();
        new Thread(() -> {
            TextRecognizer lecteur = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS);
            try {
                viderScans();
                File dossier = dossierScans();
                if (!dossier.isDirectory() && !dossier.mkdirs()) throw new IOException("dossier scans");
                String lot = String.valueOf(System.currentTimeMillis());
                JSONArray liste = new JSONArray();
                for (int i = 0; i < pages.size(); i++) {
                    Uri source = pages.get(i).getImageUri();
                    String nom = "page_" + lot + "_" + (i + 1) + ".jpg";
                    File cible = new File(dossier, nom);
                    try (InputStream entree = getContentResolver().openInputStream(source);
                         java.io.OutputStream sortie = new java.io.FileOutputStream(cible)) {
                        if (entree == null) throw new IOException("page illisible");
                        byte[] tampon = new byte[64 * 1024];
                        int lus;
                        while ((lus = entree.read(tampon)) > 0) sortie.write(tampon, 0, lus);
                    }
                    // Lecture du texte de CETTE page, avec diagnostic (jamais le texte dans le diagnostic) ;
                    // un échec est signalé pour cette page seulement.
                    JSONObject page = lirePage(lecteur, cible)
                        .put("url", "https://maxlavegie-dev.github.io" + PREFIXE_SCANS + nom)
                        .put("numero", i + 1);
                    if (!page.optBoolean("lu")) page.put("erreur", "Lecture du texte échouée sur la page " + (i + 1) + ".");
                    liste.put(page);
                }
                scanEnCours = false;
                renvoyerScan(new JSONObject().put("pages", liste));
            } catch (Exception erreur) {
                viderScans();
                renvoyerErreurScan("Les pages du scanner n’ont pas pu être préparées.");
            } finally {
                lecteur.close();
            }
        }).start();
    }

    // Lecture robuste d'une page (06/11/2026). L'orientation écrite dans la photo (EXIF) est
    // appliquée d'abord ; si la page donne moins de 20 caractères, elle est relue tournée d'un quart,
    // d'un demi et de trois quarts de tour, et la lecture qui donne le plus de texte est gardée.
    // Diagnostic renvoyé : taille en pixels, rotation EXIF, rotation ajoutée, blocs, lignes,
    // caractères, nombre d'essais. Le texte n'est renvoyé qu'à Cap (champ « texte »), jamais journalisé ici.
    private static final int CARACTERES_MINIMUM = 20;

    private JSONObject lirePage(TextRecognizer lecteur, File fichier) throws org.json.JSONException {
        JSONObject resultat = new JSONObject().put("lu", false).put("texte", "").put("caracteres", 0);
        android.graphics.Bitmap image = null;
        try {
            image = android.graphics.BitmapFactory.decodeFile(fichier.getAbsolutePath());
            if (image == null) return resultat;
            int exif = rotationExif(fichier);
            resultat.put("largeur", image.getWidth()).put("hauteur", image.getHeight()).put("rotation_exif", exif);
            Text meilleur = null;
            int meilleureRotation = 0;
            int essais = 0;
            for (int ajout : new int[]{0, 90, 180, 270}) {
                Text lecture;
                try {
                    lecture = Tasks.await(lecteur.process(InputImage.fromBitmap(image, (exif + ajout) % 360)));
                } catch (Exception erreur) {
                    continue;
                }
                essais++;
                if (meilleur == null || lecture.getText().length() > meilleur.getText().length()) {
                    meilleur = lecture;
                    meilleureRotation = ajout;
                }
                if (ajout == 0 && lecture.getText().length() >= CARACTERES_MINIMUM) break;
            }
            resultat.put("essais", essais);
            if (meilleur == null) return resultat;
            int lignes = 0;
            for (Text.TextBlock bloc : meilleur.getTextBlocks()) lignes += bloc.getLines().size();
            String texte = meilleur.getText();
            return resultat.put("lu", true).put("texte", texte).put("caracteres", texte.length())
                .put("rotation", meilleureRotation).put("blocs", meilleur.getTextBlocks().size()).put("lignes", lignes);
        } finally {
            if (image != null) image.recycle();
        }
    }

    private static int rotationExif(File fichier) {
        try {
            int orientation = new android.media.ExifInterface(fichier.getAbsolutePath())
                .getAttributeInt(android.media.ExifInterface.TAG_ORIENTATION, android.media.ExifInterface.ORIENTATION_NORMAL);
            switch (orientation) {
                case android.media.ExifInterface.ORIENTATION_ROTATE_90: return 90;
                case android.media.ExifInterface.ORIENTATION_ROTATE_180: return 180;
                case android.media.ExifInterface.ORIENTATION_ROTATE_270: return 270;
                default: return 0;
            }
        } catch (IOException erreur) {
            return 0;
        }
    }

    // ----- Caméra (05/11/2026) -----

    private boolean cameraAccordee() {
        return checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED;
    }

    private static boolean pageDeCap(Uri origine) {
        return origine != null && "https".equals(origine.getScheme())
            && "maxlavegie-dev.github.io".equals(origine.getHost());
    }

    private void traiterDemandeCamera(PermissionRequest demande) {
        boolean video = false;
        for (String ressource : demande.getResources()) {
            if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(ressource)) video = true;
        }
        if (!video || !pageDeCap(demande.getOrigin())) {
            demande.deny();
            return;
        }
        if (cameraAccordee()) {
            demande.grant(new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE});
            return;
        }
        if (demandeCameraEnAttente != null) demandeCameraEnAttente.deny();
        demandeCameraEnAttente = demande;
        requestPermissions(new String[]{Manifest.permission.CAMERA}, CODE_PERMISSION_CAMERA_PAGE);
    }

    private boolean ouvrirChoixPhoto(ValueCallback<Uri[]> retour, WebChromeClient.FileChooserParams parametres) {
        // Une seule demande à la fois : l'ancienne est annulée proprement (sinon le bouton reste bloqué).
        if (retourPhotoEnAttente != null) retourPhotoEnAttente.onReceiveValue(null);
        retourPhotoEnAttente = retour;
        if (!parametres.isCaptureEnabled()) {
            // Champ sans « capture » : simple choix d'un fichier existant.
            try {
                startActivityForResult(parametres.createIntent(), CODE_PHOTO);
            } catch (Exception erreur) {
                rendrePhoto(null);
            }
            return true;
        }
        // Android interdit d'ouvrir l'appareil photo à une appli qui déclare la caméra sans l'avoir
        // reçue : on demande donc d'abord l'autorisation si besoin.
        if (cameraAccordee()) lancerAppareilPhoto();
        else requestPermissions(new String[]{Manifest.permission.CAMERA}, CODE_PERMISSION_CAMERA_PHOTO);
        return true;
    }

    private File dossierPhotos() {
        return new File(getCacheDir(), "photos");
    }

    // Les photos peuvent être des documents personnels : jamais gardées au-delà de leur usage.
    private void viderPhotosTemporaires() {
        File[] fichiers = dossierPhotos().listFiles();
        if (fichiers == null) return;
        for (File fichier : fichiers) {
            if (!fichier.delete()) fichier.deleteOnExit();
        }
    }

    private void lancerAppareilPhoto() {
        try {
            viderPhotosTemporaires();
            File dossier = dossierPhotos();
            if (!dossier.isDirectory() && !dossier.mkdirs()) throw new IOException("dossier photos");
            File fichier = new File(dossier, "page_" + System.currentTimeMillis() + ".jpg");
            fichierPhotoEnCours = fichier;
            photoEnCours = FileProvider.getUriForFile(this, "fr.maxlavegie.cap.photos", fichier);
            Intent intention = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
            intention.putExtra(MediaStore.EXTRA_OUTPUT, photoEnCours);
            intention.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivityForResult(intention, CODE_PHOTO);
        } catch (Exception erreur) {
            photoEnCours = null;
            fichierPhotoEnCours = null;
            rendrePhoto(null);
        }
    }

    // Demande de Max (05/11/2026) : la photo du bouton « appareil photo du téléphone » est aussi
    // rangée dans la galerie, album « Cap » (Pictures/Cap), comme ses autres photos. Copie faite à
    // côté, sans retarder Cap ; un échec est dit à Max, et la photo part quand même dans Cap.
    // Android 10 et plus seulement : aucun droit Android de plus n'est nécessaire.
    private void copierDansGalerie(final File source) {
        if (source == null) return;
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
            direAMax("Photo non copiée dans la galerie : téléphone trop ancien.");
            return;
        }
        new Thread(() -> {
            ContentResolver resolveur = getContentResolver();
            Uri cible = null;
            try {
                String nom = "Cap_" + new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.FRANCE).format(new Date()) + ".jpg";
                ContentValues valeurs = new ContentValues();
                valeurs.put(MediaStore.Images.Media.DISPLAY_NAME, nom);
                valeurs.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
                valeurs.put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/Cap");
                valeurs.put(MediaStore.Images.Media.IS_PENDING, 1);
                cible = resolveur.insert(MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY), valeurs);
                if (cible == null) throw new IOException("galerie indisponible");
                try (InputStream entree = new FileInputStream(source);
                     OutputStream sortie = resolveur.openOutputStream(cible)) {
                    if (sortie == null) throw new IOException("galerie indisponible");
                    byte[] tampon = new byte[64 * 1024];
                    int lus;
                    while ((lus = entree.read(tampon)) > 0) sortie.write(tampon, 0, lus);
                }
                ContentValues fin = new ContentValues();
                fin.put(MediaStore.Images.Media.IS_PENDING, 0);
                resolveur.update(cible, fin, null, null);
                direAMax("Photo enregistrée dans la galerie (album Cap).");
            } catch (Exception erreur) {
                // Copie à moitié faite : on retire l'entrée vide de la galerie (jamais la photo de Cap).
                if (cible != null) {
                    try { resolveur.delete(cible, null, null); } catch (Exception ignoree) { }
                }
                direAMax("Photo non enregistrée dans la galerie. Elle est quand même dans Cap.");
            }
        }).start();
    }

    private void direAMax(final String texte) {
        runOnUiThread(() -> Toast.makeText(this, texte, Toast.LENGTH_LONG).show());
    }

    // Rend toujours une réponse à la page, même vide : sinon le bouton de Cap ne répond plus.
    private void rendrePhoto(Uri[] resultat) {
        if (retourPhotoEnAttente != null) retourPhotoEnAttente.onReceiveValue(resultat);
        retourPhotoEnAttente = null;
    }

    @Override
    protected void onActivityResult(int code, int resultat, Intent donnees) {
        super.onActivityResult(code, resultat, donnees);
        if (code == CODE_SCANNER) {
            recevoirScan(resultat, donnees);
            return;
        }
        if (code != CODE_PHOTO) return;
        Uri photo = photoEnCours;
        File fichierPhoto = fichierPhotoEnCours;
        photoEnCours = null;
        fichierPhotoEnCours = null;
        if (resultat != RESULT_OK) {
            rendrePhoto(null);
        } else if (photo != null) {
            rendrePhoto(new Uri[]{photo});
            if (fichierPhoto != null && fichierPhoto.length() > 0) copierDansGalerie(fichierPhoto);
        } else {
            rendrePhoto(WebChromeClient.FileChooserParams.parseResult(resultat, donnees));
        }
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] permissions, int[] resultats) {
        super.onRequestPermissionsResult(code, permissions, resultats);
        boolean accordee = resultats.length > 0 && resultats[0] == PackageManager.PERMISSION_GRANTED;
        if (code == CODE_PERMISSION_CAMERA_PAGE && demandeCameraEnAttente != null) {
            if (accordee) demandeCameraEnAttente.grant(new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE});
            else demandeCameraEnAttente.deny();
            demandeCameraEnAttente = null;
        } else if (code == CODE_PERMISSION_CAMERA_PHOTO) {
            if (accordee) lancerAppareilPhoto();
            else rendrePhoto(null);
        }
    }

    @Override
    protected void onDestroy() {
        if (reconnaisseur != null) {
            reconnaisseur.destroy();
        }
        super.onDestroy();
    }

    private void demanderPermissionMicroSiBesoin() {
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, CODE_PERMISSION_MICRO);
        }
    }

    private boolean permissionMicroAccordee() {
        return checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED;
    }

    // Convertit les codes d'erreur d'Android vers les mêmes mots que ceux que Chrome renvoie
    // déjà (dictee.js et app.js les connaissent : 'not-allowed', 'no-speech', 'network', etc.).
    private static String codeErreurWeb(int codeAndroid) {
        switch (codeAndroid) {
            case SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS:
                return "not-allowed";
            case SpeechRecognizer.ERROR_NO_MATCH:
            case SpeechRecognizer.ERROR_SPEECH_TIMEOUT:
                return "no-speech";
            case SpeechRecognizer.ERROR_NETWORK:
            case SpeechRecognizer.ERROR_NETWORK_TIMEOUT:
                return "network";
            case SpeechRecognizer.ERROR_AUDIO:
                return "audio-capture";
            case SpeechRecognizer.ERROR_CLIENT:
            case SpeechRecognizer.ERROR_RECOGNIZER_BUSY:
                return "aborted";
            default:
                return "inconnue";
        }
    }

    private void appelerJs(String script) {
        if (vue != null) {
            vue.evaluateJavascript(script, null);
        }
    }

    private void envoyerResultat(String texte, boolean estFinal) {
        appelerJs("window.__pontRecevoirResultat(" + JSONObject.quote(texte) + "," + estFinal + ");");
    }

    private void envoyerErreur(String code) {
        appelerJs("window.__pontRecevoirErreur(" + JSONObject.quote(code) + ");");
    }

    private void envoyerFin() {
        ecouteEnCours = false;
        appelerJs("window.__pontRecevoirFin();");
    }

    // Porte d'entrée appelée depuis la page web (dans dictee.js, via la classe injectée ci-dessus).
    private class PontMicroAndroid {
        @JavascriptInterface
        public void demarrerEcoute(final String langue) {
            runOnUiThread(() -> {
                if (!permissionMicroAccordee()) {
                    demanderPermissionMicroSiBesoin();
                    envoyerErreur("not-allowed");
                    envoyerFin();
                    return;
                }
                if (ecouteEnCours) {
                    envoyerErreur("aborted");
                    envoyerFin();
                    return;
                }
                Intent intention = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                intention.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                intention.putExtra(RecognizerIntent.EXTRA_LANGUAGE, langue != null ? langue : "fr-FR");
                intention.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true);
                intention.putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, getPackageName());
                ecouteEnCours = true;
                reconnaisseur.startListening(intention);
            });
        }

        @JavascriptInterface
        public void arreterEcoute() {
            runOnUiThread(() -> {
                if (ecouteEnCours) {
                    reconnaisseur.stopListening();
                }
            });
        }
    }

    private class EcouteurReconnaissance implements RecognitionListener {
        @Override
        public void onReadyForSpeech(Bundle params) {}

        @Override
        public void onBeginningOfSpeech() {}

        @Override
        public void onRmsChanged(float rmsdB) {}

        @Override
        public void onBufferReceived(byte[] buffer) {}

        @Override
        public void onEndOfSpeech() {}

        @Override
        public void onError(int error) {
            envoyerErreur(codeErreurWeb(error));
            envoyerFin();
        }

        @Override
        public void onResults(Bundle results) {
            ArrayList<String> hypotheses = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
            String texte = (hypotheses != null && !hypotheses.isEmpty()) ? hypotheses.get(0) : "";
            envoyerResultat(texte, true);
            envoyerFin();
        }

        @Override
        public void onPartialResults(Bundle partialResults) {
            ArrayList<String> hypotheses = partialResults.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
            if (hypotheses != null && !hypotheses.isEmpty()) {
                envoyerResultat(hypotheses.get(0), false);
            }
        }

        @Override
        public void onEvent(int eventType, Bundle params) {}
    }
}
