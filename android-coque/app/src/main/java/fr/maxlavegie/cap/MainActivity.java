package fr.maxlavegie.cap;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

// Coque Android vide : ouvre Cap tel qu'il est en ligne aujourd'hui (la version web publiée),
// dans une fenêtre plein écran sans barre d'adresse. Rien d'autre : pas de scanner, pas de pont
// pour la dictée (Android ne sait pas le faire nativement dans une coque, voir le journal de bord).
public class MainActivity extends Activity {

    private static final String URL_CAP = "https://maxlavegie-dev.github.io/cap/app/";

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        WebView vue = new WebView(this);
        WebSettings reglages = vue.getSettings();
        reglages.setJavaScriptEnabled(true);
        reglages.setDomStorageEnabled(true);
        reglages.setDatabaseEnabled(true);
        reglages.setMediaPlaybackRequiresUserGesture(false);
        vue.setWebViewClient(new WebViewClient());

        setContentView(vue);
        vue.loadUrl(URL_CAP);
    }
}
