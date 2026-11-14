package fr.maxlavegie.cap;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

// 12/11/2026 (c176, défaut de c175 vu par Max) : COMPTAGE des destinataires d'un MMS reçu, sans Android (testé sur le PC).
// Sur le Pixel, chaque MMS reçu porte l'adresse de l'expéditeur AUSSI en copie (type 130) : c175 comptait donc 2 destinataires
// (Max + l'expéditeur) et rangeait TOUT en « groupe ». Maintenant : destinataires DIFFÉRENTS (TO et copie), sans l'expéditeur.
// Deux écritures du même numéro (« +33 6… », « 06… ») comptent pour un. Aucune adresse n'est gardée ni écrite.
final class AdressesMms {
    static final int FROM = 137, TO = 151, CC = 130;
    private AdressesMms() {}

    // Clé de comparaison : les 9 derniers chiffres (« +33 6 39… » = « 06 39… ») ; sans chiffre : le texte en minuscules.
    static String cle(String adresse) {
        if (adresse == null) return "";
        String chiffres = adresse.replaceAll("[^0-9]", "");
        if (chiffres.isEmpty()) return adresse.trim().toLowerCase();
        return chiffres.length() > 9 ? chiffres.substring(chiffres.length() - 9) : chiffres;
    }

    // 13/11/2026 (P3, inventaire) : sens d'un SMS (colonne « type » : 1 reçu, 2 envoyé ; brouillon, en attente, échec : autre)
    // et d'un MMS (colonne « msg_box » : 1 reçu, 2 envoyé ; autre sinon).
    static String sens(int boite) {
        if (boite == 1) return "recu";
        if (boite == 2) return "envoye";
        if (boite == 3) return "brouillon"; // 14/11/2026 (P7, décision de Max) : brouillons exclus et comptés à part
        return "autre";
    }

    // 13/11/2026 (P3) : les CORRESPONDANTS d'un MMS, sans doublon (9 derniers chiffres) : reçu = l'expéditeur ; envoyé = les
    // destinataires (TO et copie), sans Max lui-même (« insert-address-token ») ni l'expéditeur. Rien n'est gardé ni écrit.
    static List<String> correspondants(List<Integer> types, List<String> adresses, boolean envoye) {
        List<String> rendus = new java.util.ArrayList<>();
        Set<String> vus = new HashSet<>();
        Set<String> expediteurs = new HashSet<>();
        for (int i = 0; i < types.size(); i++) if (types.get(i) == FROM) expediteurs.add(cle(adresses.get(i)));
        for (int i = 0; i < types.size(); i++) {
            int t = types.get(i);
            String a = adresses.get(i);
            boolean garde = envoye ? (t == TO || t == CC) : t == FROM;
            if (!garde || a == null) continue;
            if (envoye && (a.trim().equalsIgnoreCase("insert-address-token") || expediteurs.contains(cle(a)))) continue;
            if (vus.add(cle(a))) rendus.add(a);
        }
        return rendus;
    }

    // 13/11/2026 (P3) : TOUS les participants d'un MMS de groupe reçu (expéditeur, destinataires, copies), sans doublon et sans
    // le jeton « insert-address-token » : la même liste pour chaque message du même groupe (le numéro de Max y est aussi).
    static List<String> participants(List<Integer> types, List<String> adresses) {
        List<String> rendus = new java.util.ArrayList<>();
        Set<String> vus = new HashSet<>();
        for (int i = 0; i < types.size(); i++) {
            int t = types.get(i);
            String a = adresses.get(i);
            if ((t != FROM && t != TO && t != CC) || a == null || a.trim().equalsIgnoreCase("insert-address-token")) continue;
            if (vus.add(cle(a))) rendus.add(a);
        }
        return rendus;
    }

    // 14/11/2026 (accord de Max, P6) : une pièce de MMS que Cap peut COPIER : image ou vidéo des types permis par l'envoi du
    // compte Cap (P4), et rien d'autre (ni le texte, ni la mise en page « smil », ni le son, ni les fiches de contact).
    // Rend le type propre (« image/jpg » devient « image/jpeg »), ou null. Testé sur le PC.
    static String typePiece(String ct) {
        if (ct == null) return null;
        String t = ct.split(";")[0].trim().toLowerCase(java.util.Locale.ROOT);
        if (t.equals("image/jpg") || t.equals("image/pjpeg")) t = "image/jpeg";
        return t.matches("image/(jpeg|png|gif|webp|heic|heif)|video/(mp4|3gpp|webm|quicktime)") ? t : null;
    }

    // 14/11/2026 (P6) : un identifiant de message ou de pièce venu de la page : des chiffres seulement.
    static boolean idSur(String id) {
        return id != null && id.matches("[0-9]{1,18}");
    }

    // types[i], adresses[i] : les lignes « addr » d'un MMS.
    static int destinataires(List<Integer> types, List<String> adresses) {
        Set<String> expediteurs = new HashSet<>();
        for (int i = 0; i < types.size(); i++) if (types.get(i) == FROM) expediteurs.add(cle(adresses.get(i)));
        Set<String> vus = new HashSet<>();
        int n = 0;
        for (int i = 0; i < types.size(); i++) {
            int t = types.get(i);
            if (t != TO && t != CC) continue;
            String k = cle(adresses.get(i));
            if (expediteurs.contains(k)) continue; // l'expéditeur répété (en copie, ou parmi les destinataires)
            if (!k.isEmpty() && !vus.add(k)) continue; // le même destinataire deux fois
            n++;
        }
        return n;
    }
}
