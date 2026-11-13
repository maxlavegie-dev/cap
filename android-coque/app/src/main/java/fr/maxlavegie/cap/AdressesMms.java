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
