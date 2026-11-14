# 13/11/2026 (Agent 3) : tests FICTIFS de visionneuse_web.js, sans réseau.
# Lance Edge sans fenêtre sur chaque page de tests, lit les résultats écrits dans la page, les affiche.
# 13/11/2026 (marche 4) : + page_test_branchement.html (lit visionneuse_cap.js et index.html de Cap, SANS les modifier).
# 13/11/2026 (intégration dans Cap, Opus) : copié de C:\Users\revox\Agent3\module_web\tests ; lancé aussi par app\test_cap.py.
# Usage : python -I test_visionneuse_web.py   (code de sortie 0 = tout passe, 1 = au moins un échec)
import html
import json
import pathlib
import re
import subprocess
import sys
import tempfile

ICI = pathlib.Path(__file__).resolve().parent
PAGES = [ICI / "page_test.html", ICI / "page_test_branchement.html"]
EDGE = pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")


def lancer_page(page):
    with tempfile.TemporaryDirectory(prefix="agent3_tests_") as profil:
        commande = [str(EDGE), "--headless=new", "--disable-gpu", "--no-first-run", "--allow-file-access-from-files",
                    f"--user-data-dir={profil}", "--virtual-time-budget=5000", "--dump-dom", page.as_uri()]
        sortie = subprocess.run(commande, capture_output=True, timeout=120)
    texte = html.unescape(sortie.stdout.decode("utf-8", errors="replace"))
    # 13/11/2026 (marche 4) : seulement dans <pre id="resultats"> (le texte du script contient aussi « RESULTATS_JSON: »).
    m = re.search(r'<pre id="resultats">RESULTATS_JSON:(.*?):FIN</pre>', texte, re.S)
    if not m:
        return [{"nom": f"{page.name} : la page n'a rendu aucun résultat", "ok": False, "detail": texte[-500:]}]
    return [dict(r, nom=f"{page.name} : {r['nom']}") for r in json.loads(m.group(1))]


def lancer():
    resultats = []
    for page in PAGES:
        resultats += lancer_page(page)
    rates = [r for r in resultats if not r["ok"]]
    for r in rates:
        print(f"ÉCHEC : {r['nom']} -> {r['detail'][:300]}")
    print(f"{len(resultats) - len(rates)} / {len(resultats)} tests réussis.")
    return 1 if rates or not resultats else 0


if __name__ == "__main__":
    sys.exit(lancer())
