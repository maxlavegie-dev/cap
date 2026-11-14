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

    static List<String> correspondants(boolean envoye, Object... lignes) {
        List<Integer> types = new ArrayList<>();
        List<String> adresses = new ArrayList<>();
        for (int i = 0; i < lignes.length; i += 2) { types.add((Integer) lignes[i]); adresses.add((String) lignes[i + 1]); }
        return AdressesMms.correspondants(types, adresses, envoye);
    }

    static List<String> participants(Object... lignes) {
        List<Integer> types = new ArrayList<>();
        List<String> adresses = new ArrayList<>();
        for (int i = 0; i < lignes.length; i += 2) { types.add((Integer) lignes[i]); adresses.add((String) lignes[i + 1]); }
        return AdressesMms.participants(types, adresses);
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
        // 13/11/2026 (P3) : sens et correspondants (FICTIFS).
        verifier("sens : 1 = reçu", AdressesMms.sens(1).equals("recu") ? 1 : 0, 1);
        verifier("sens : 2 = envoyé", AdressesMms.sens(2).equals("envoye") ? 1 : 0, 1);
        verifier("sens : 3 = brouillon (P7)", AdressesMms.sens(3).equals("brouillon") ? 1 : 0, 1);
        verifier("sens : 4, 5, 6, 0 = autre", (AdressesMms.sens(4) + AdressesMms.sens(5) + AdressesMms.sens(6) + AdressesMms.sens(0)).equals("autreautreautreautre") ? 1 : 0, 1);
        verifier("reçu : le seul correspondant est l'expéditeur", correspondants(false, F, "+33639980031", T, "+33639980001", C, "+33639980031").size(), 1);
        verifier("reçu : c'est bien l'expéditeur", correspondants(false, F, "+33639980031", T, "+33639980001").get(0).equals("+33639980031") ? 1 : 0, 1);
        verifier("envoyé à une personne : Max (jeton) retiré", correspondants(true, F, "insert-address-token", T, "+33639980031").size(), 1);
        verifier("envoyé à un groupe de trois", correspondants(true, F, "insert-address-token", T, "+33639980031", T, "+33639980032", C, "06 39 98 00 33").size(), 3);
        verifier("envoyé : le même destinataire écrit deux fois", correspondants(true, F, "insert-address-token", T, "+33639980031", C, "06 39 98 00 31").size(), 1);
        verifier("envoyé : aucune adresse", correspondants(true).size(), 0);
        verifier("groupe reçu : tous les participants, sans doublon ni jeton", participants(F, "+33639980031", T, "+33639980001", T, "+33639980032", C, "06 39 98 00 31", T, "insert-address-token").size(), 3);
        // 14/11/2026 (P6) : pièces copiables et identifiants (FICTIFS).
        verifier("pièce : image/jpeg permise", "image/jpeg".equals(AdressesMms.typePiece("image/jpeg")) ? 1 : 0, 1);
        verifier("pièce : image/jpg devient image/jpeg", "image/jpeg".equals(AdressesMms.typePiece("Image/JPG")) ? 1 : 0, 1);
        verifier("pièce : vidéo 3gpp avec paramètre", "video/3gpp".equals(AdressesMms.typePiece("video/3gpp; name=x")) ? 1 : 0, 1);
        verifier("pièce : texte, smil, son, fiche, vide : refusés", (AdressesMms.typePiece("text/plain") == null && AdressesMms.typePiece("application/smil") == null
            && AdressesMms.typePiece("audio/amr") == null && AdressesMms.typePiece("text/x-vcard") == null && AdressesMms.typePiece(null) == null
            && AdressesMms.typePiece("image/svg+xml") == null && AdressesMms.typePiece("video/mp4x") == null) ? 1 : 0, 1);
        verifier("identifiant : chiffres seulement", (AdressesMms.idSur("901") && !AdressesMms.idSur("9 01") && !AdressesMms.idSur("1 OR 1=1")
            && !AdressesMms.idSur("") && !AdressesMms.idSur(null) && !AdressesMms.idSur("1234567890123456789")) ? 1 : 0, 1);
        System.out.println(echecs == 0 ? "TOUT BON" : echecs + " ECHEC(S)");
        System.exit(echecs == 0 ? 0 : 1);
    }
}
