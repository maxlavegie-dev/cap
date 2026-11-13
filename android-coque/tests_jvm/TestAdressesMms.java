package fr.maxlavegie.cap;

import java.util.ArrayList;
import java.util.List;

/** 12/11/2026 (c176) : tests FICTIFS du comptage des destinataires d'un MMS (numéros de la plage de fiction). Lancés sur le PC. */
public class TestAdressesMms {
    static int echecs = 0;

    static int compter(Object... lignes) {
        List<Integer> types = new ArrayList<>();
        List<String> adresses = new ArrayList<>();
        for (int i = 0; i < lignes.length; i += 2) { types.add((Integer) lignes[i]); adresses.add((String) lignes[i + 1]); }
        return AdressesMms.destinataires(types, adresses);
    }

    static void verifier(String nom, int reel, int attendu) {
        boolean ok = reel == attendu;
        System.out.println((ok ? "PASS  " : "FAIL  ") + nom + (ok ? "" : "  -> " + reel + " au lieu de " + attendu));
        if (!ok) echecs++;
    }

    public static void main(String[] args) {
        int F = AdressesMms.FROM, T = AdressesMms.TO, C = AdressesMms.CC;
        // La forme vue sur le Pixel (types seulement, 12/11/2026) : expéditeur, Max en destinataire, l'expéditeur répété en copie.
        verifier("MMS d'une seule personne, expéditeur répété en copie", compter(F, "+33639980031", T, "+33639980001", C, "+33639980031"), 1);
        verifier("même chose, numéro écrit autrement en copie", compter(F, "+33639980031", T, "+33639980001", C, "06 39 98 00 31"), 1);
        verifier("MMS d'une seule personne, sans copie", compter(F, "+33639980031", T, "+33639980001"), 1);
        verifier("destinataire masqué (jeton)", compter(F, "+33639980031", T, "insert-address-token", C, "+33639980031"), 1);
        verifier("vrai groupe : Max et deux autres", compter(F, "+33639980031", T, "+33639980001", T, "+33639980032", T, "+33639980033"), 3);
        verifier("vrai groupe avec copie répétée", compter(F, "+33639980031", T, "+33639980001", C, "+33639980031", C, "+33639980032"), 2);
        verifier("le même destinataire deux fois", compter(F, "+33639980031", T, "+33639980001", T, "0639980001"), 1);
        verifier("expéditeur répété parmi les destinataires", compter(F, "+33639980031", T, "+33639980001", T, "+33639980031"), 1);
        verifier("aucune adresse", compter(), 0);
        System.out.println(echecs == 0 ? "TOUT BON" : echecs + " ECHEC(S)");
        System.exit(echecs == 0 ? 0 : 1);
    }
}
