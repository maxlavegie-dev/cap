package fr.maxlavegie.cap;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.view.ViewGroup;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.ServiceWorkerClient;
import android.webkit.ServiceWorkerController;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;

import androidx.browser.customtabs.CustomTabsIntent;

import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
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
