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
import android.view.ViewGroup;
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
        vue.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
                view.evaluateJavascript(SCRIPT_PONT_MICRO, null);
            }

            // Version « essai » seulement : voir reponseLocale. Dans la coque normale, renvoie null.
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
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

        // Version « essai » seulement : Cap installe un service worker, dont les téléchargements ne
        // passent pas par le WebViewClient ; on les sert aussi depuis les fichiers de l'APK.
        if (BuildConfig.FICHIERS_LOCAUX) {
            ServiceWorkerController.getInstance().setServiceWorkerClient(new ServiceWorkerClient() {
                @Override
                public WebResourceResponse shouldInterceptRequest(WebResourceRequest request) {
                    return reponseLocale(request.getUrl());
                }
            });
        }

        racine = new FrameLayout(this);
        racine.addView(vue, new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(racine);

        effacerAncienDiagnostic();
        viderPhotosTemporaires();
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
