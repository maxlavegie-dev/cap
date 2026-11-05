package fr.maxlavegie.cap;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import androidx.browser.customtabs.CustomTabsIntent;

import org.json.JSONObject;

import java.io.File;
import java.io.FileWriter;
import java.util.ArrayList;

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

    // DEBUG TEMPORAIRE (étape C.1, 05/11/2026) : à retirer après le diagnostic de la coque Android.
    // Surveille les réponses 401/403 de Google (sans toucher au site web, qui reste tel qu'il est en
    // ligne) pour afficher dans une fenêtre native le détail exact renvoyé par Google.
    private static final String SCRIPT_DEBUG_GOOGLE =
        "(function(){"
        + "if(window.__debugGoogleInstalle){return;}window.__debugGoogleInstalle=true;"
        + "var original=window.fetch;"
        + "window.fetch=function(entree,options){"
        + "return original(entree,options).then(function(reponse){"
        + "try{"
        + "var adresse=typeof entree==='string'?entree:(entree&&entree.url)||'';"
        + "if((reponse.status===401||reponse.status===403)&&/googleapis\\.com|accounts\\.google\\.com/.test(adresse)){"
        + "reponse.clone().text().then(function(corps){"
        + "window.PontMicroAndroid&&window.PontMicroAndroid.afficherDebugGoogle("
        + "'Reponse '+reponse.status+' pour '+adresse+' : '+corps.slice(0,500));"
        + "}).catch(function(){});"
        + "}"
        + "}catch(erreur){}"
        + "return reponse;"
        + "});"
        + "};"
        + "})();";

    private FrameLayout racine;
    private WebView vue;
    private SpeechRecognizer reconnaisseur;
    private boolean ecouteEnCours = false;
    // DEBUG TEMPORAIRE (étape C.3, 05/11/2026) : la bannière de diagnostic est maintenant une vue
    // Android native, posée au-dessus de la WebView dans `racine` (pas injectée dans la page web).
    // Elle s'affiche dès que le retour de Google est détecté, sans attendre que la page ait chargé,
    // et la page web (app.js) ne peut jamais l'effacer puisqu'elle n'en fait pas partie.
    private View banniereNative;

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
                view.evaluateJavascript(SCRIPT_DEBUG_GOOGLE, null);
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

        racine = new FrameLayout(this);
        racine.addView(vue, new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(racine);

        String adresseDepart = adresseDeDepart(getIntent());
        // DEBUG TEMPORAIRE (étape C.1/C.3, 05/11/2026) : à retirer après le diagnostic de la coque
        // Android. Sur un vrai téléphone, Android tue souvent la coque pendant que Chrome est
        // ouvert : le retour de Google passe alors par onCreate (ici), pas par onNewIntent. La
        // bannière s'affiche tout de suite, sans attendre que la page ait chargé.
        afficherDebugSiRetourGoogle(adresseDepart, "onCreate");
        vue.loadUrl(adresseDepart);
    }

    @Override
    protected void onNewIntent(Intent intention) {
        super.onNewIntent(intention);
        setIntent(intention);
        String adresseRetour = adresseDeRetourGoogle(intention);
        if (adresseRetour != null && vue != null) {
            afficherDebugSiRetourGoogle(adresseRetour, "onNewIntent");
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

    // DEBUG TEMPORAIRE (étape C.1/C.3, 05/11/2026) : à retirer après le diagnostic de la coque
    // Android. Affiche tout de suite le détail exact du retour de Google (fragment #...), sans
    // attendre le chargement de la page : utile si Cap affiche une erreur de vérification de
    // sécurité, car la page peut alors être remplacée avant qu'on ait eu le temps de la lire.
    private void afficherDebugSiRetourGoogle(String adresse, String origine) {
        if (adresse == null) return;
        Uri uriRetour = Uri.parse(adresse);
        String fragment = uriRetour.getFragment();
        if (fragment != null && !fragment.isEmpty()) {
            afficherDebug("Retour de Google (" + origine + ", fragment d'adresse) :\n" + fragment);
        }
    }

    // DEBUG TEMPORAIRE (étape C.3, 05/11/2026) : à retirer après le diagnostic de la coque Android.
    // Affiche le diagnostic dans une vue Android native posée au-dessus de la WebView (pas dans la
    // page web) : la page web ne peut jamais l'effacer, même si elle se recharge ou se remplace par
    // un écran d'erreur juste après. Reste affichée tant que « Fermer » n'est pas touché.
    private void afficherDebug(String texte) {
        injecterBanniereNative(texte);
        ecrireDiagnosticFichier(texte);
    }

    private void injecterBanniereNative(String texte) {
        runOnUiThread(() -> {
            if (racine == null) return;
            if (banniereNative != null) {
                racine.removeView(banniereNative);
                banniereNative = null;
            }
            FrameLayout bandeau = new FrameLayout(this);
            bandeau.setBackgroundColor(Color.WHITE);

            TextView corps = new TextView(this);
            corps.setText(texte);
            corps.setTextColor(Color.BLACK);
            corps.setTextIsSelectable(true);
            corps.setPadding(32, 140, 32, 32);
            ScrollView defilement = new ScrollView(this);
            defilement.addView(corps, new ScrollView.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
            bandeau.addView(defilement, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

            Button bouton = new Button(this);
            bouton.setText("Fermer");
            bouton.setOnClickListener(v -> {
                racine.removeView(bandeau);
                if (banniereNative == bandeau) banniereNative = null;
            });
            FrameLayout.LayoutParams reglagesBouton = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.TOP | Gravity.START);
            reglagesBouton.topMargin = 48;
            reglagesBouton.leftMargin = 32;
            bandeau.addView(bouton, reglagesBouton);

            racine.addView(bandeau, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
            bandeau.bringToFront();
            banniereNative = bandeau;
        });
    }

    private void ecrireDiagnosticFichier(String texte) {
        try {
            File dossier = getExternalFilesDir(null);
            if (dossier == null) return;
            File fichier = new File(dossier, "diagnostic_google.txt");
            try (FileWriter ecrivain = new FileWriter(fichier, false)) {
                ecrivain.write(texte);
            }
        } catch (Exception erreur) {
            // Diagnostic de confort uniquement : un échec d'écriture ne doit jamais faire planter la coque.
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

        // DEBUG TEMPORAIRE (étape C.1, 05/11/2026) : à retirer après le diagnostic de la coque Android.
        @JavascriptInterface
        public void afficherDebugGoogle(final String texte) {
            afficherDebug(texte);
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
