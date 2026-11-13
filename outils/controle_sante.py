# 09/11/2026 (décision de Max) : CONTRÔLE SANTÉ avant toute publication.
# Cherche, dans les fichiers qui partiraient (une version git : par défaut HEAD), les mots de santé : types de documents,
# professions, établissements, spécialités. Il gère les accents (« éléphant », « elephant » et « ÉLÉPHANT » sont le même mot).
# La LISTE DES MOTS n'est jamais dans le dépôt : elle est dans mots_sante.txt (ignoré par git, à côté du dépôt), un début
# de mot par ligne (ex. un début de mot de 5 lettres ou plus). Ce fichier-ci n'en contient aucun.
# Usage : python outils\controle_sante.py [version]      (version : HEAD, origin/main, une branche…)
# Résultat : 1) les mots trouvés hors des usages permis (doit être 0 avant publication) ; 2) les usages permis (gardés
# exprès par Max) ; 3) le nombre de fois où la CATÉGORIE « santé » apparaît, pour information.
import pathlib, re, subprocess, sys, unicodedata

RACINE = pathlib.Path(__file__).resolve().parent.parent
LISTE = RACINE / 'mots_sante.txt'
# Usages PERMIS par Max (09/11/2026), reconnus par un morceau de la ligne : mots génériques que le code doit reconnaître
# sur de vrais papiers (emetteur.js), consigne générale de l'IA, formule « document de santé ».
PERMIS = [
    ('app/emetteur.js', 'creche '), ('app/emetteur.js', 'secretariat '),
    ('app/consignes_cap.txt', 'conseil m'),
]
IGNORES = re.compile(r'\.(png|jpg|jpeg|ico|mp4|woff2?|pdf)$|^app/pdfjs/')

def plier(texte):
    return unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode('ascii').lower()

def main():
    version = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'
    if not LISTE.exists():
        print(f'Liste absente : {LISTE} (un début de mot par ligne). Contrôle impossible.'); return 2
    debuts = [plier(l.strip()) for l in LISTE.read_text(encoding='utf-8').splitlines() if l.strip() and not l.startswith('#')]
    motif = re.compile(r'\b(' + '|'.join(re.escape(d) for d in debuts) + r')', re.I)
    categorie = re.compile(r'\bsante\b')
    fichiers = subprocess.run(['git', 'ls-tree', '-r', '--name-only', version], cwd=RACINE, capture_output=True, text=True, encoding='utf-8').stdout.split('\n')
    interdits, permis, nb_categorie = [], [], 0
    for f in filter(None, fichiers):
        if IGNORES.search(f): continue
        texte = subprocess.run(['git', 'show', f'{version}:{f}'], cwd=RACINE, capture_output=True).stdout.decode('utf-8', 'ignore')
        for n, ligne in enumerate(texte.split('\n'), 1):
            plie = plier(ligne)
            nb_categorie += len(categorie.findall(plie.replace('document de sante', '')))
            for m in motif.finditer(plie):
                ok = any(f == pf and morceau in plie for pf, morceau in PERMIS)
                (permis if ok else interdits).append(f'{f}:{n} : « {m.group(0)}… »')
    print(f'Version contrôlée : {version}')
    print(f'1) Mots de santé hors usages permis : {len(interdits)}'); [print('   ', x) for x in interdits]
    print(f'2) Usages permis (gardés par Max) : {len(permis)}'); [print('   ', x) for x in permis]
    print(f'3) Catégorie « santé » (hors « document de santé ») : {nb_categorie} fois (information)')
    return 1 if interdits else 0

if __name__ == '__main__':
    sys.exit(main())
