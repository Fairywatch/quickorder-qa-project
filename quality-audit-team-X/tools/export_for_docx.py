# -*- coding: utf-8 -*-
"""Exporte les donnees reelles de la campagne, accents restaures, pour le .docx."""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from gen_bugs import BUGS          # noqa: E402
from accents import accentuer      # noqa: E402

DOCS = os.path.join(ROOT, "docs")
results = json.load(io.open(os.path.join(DOCS, "evidence", "results.json"),
                            encoding="utf-8"))


def acc(t):
    """Accentue du texte brut (pas de HTML ici)."""
    if not t:
        return t
    return accentuer(t)


def is_evidence(line):
    """Une ligne de preuve technique ne doit pas etre accentuee."""
    return bool(re.match(r"^(GET|POST|PUT|DELETE|body:|-->|\{|\[|stock|commandes|"
                         r"flash:|URL|Restaurants|Annonce|q=|params)", line.strip()))


def acc_evidence(t):
    """Les preuves restent brutes : ce sont des requetes et des reponses reelles."""
    return t


tests = []
for r in results:
    tests.append({
        "id": r["id"],
        "categorie": acc(r["categorie"]),
        "titre": acc(r["titre"]),
        "objectif": acc(r["objectif"]),
        "preconditions": acc(r["preconditions"]),
        "donnees": acc(r["donnees"]),
        "etapes": acc(r["etapes"]),
        "attendu": acc(r["attendu"]),
        "obtenu": acc(r["obtenu"]),
        "statut": r["statut"],
        "bug": r["bug"],
        "evidence": acc_evidence(r["evidence"]),
    })

ordre = {"Bloquante": 0, "Critique": 1, "Majeure": 2, "Mineure": 3}
bugs = []
for b in sorted(BUGS, key=lambda x: (ordre[x["severite"]], x["id"])):
    bugs.append({
        "id": b["id"],
        "titre": acc(b["titre"]),
        "severite": b["severite"],
        "priorite": acc(b["priorite"]),
        "risque": b["risque"],
        "cas": b["cas"],
        "contexte": acc(b["contexte"]),
        "preconditions": [acc(x) for x in b["preconditions"]],
        "etapes": [acc(x) for x in b["etapes"]],
        "attendu": acc(b["attendu"]),
        "obtenu": acc(b["obtenu"]),
        "impact": acc(b["impact"]),
        "preuves": [{"cas": c,
                     "titre": acc(next(t["titre"] for t in results if t["id"] == c)),
                     "texte": acc_evidence(next(t["evidence"] for t in results
                                                if t["id"] == c))}
                    for c in b["cas"]],
    })

total = len(tests)
npass = sum(1 for t in tests if t["statut"] == "Pass")
data = {
    "tests": tests,
    "bugs": bugs,
    "stats": {
        "total": total, "pass": npass, "fail": total - npass,
        "blocked": 0, "skipped": 0,
        "parCategorie": [
            {"nom": lib,
             "total": sum(1 for t in tests if t["categorie"] == cat),
             "pass": sum(1 for t in tests if t["categorie"] == cat and t["statut"] == "Pass"),
             "fail": sum(1 for t in tests if t["categorie"] == cat and t["statut"] == "Fail")}
            for cat, lib in [(u"Nominal", u"Cas nominaux"),
                             (u"Limite", u"Cas aux limites"),
                             (u"Erreur", u"Cas d'erreur"),
                             (u"Règle métier", u"Règles métier")]
        ],
        "severites": [{"nom": s, "n": sum(1 for b in bugs if b["severite"] == s)}
                      for s in ["Bloquante", "Critique", "Majeure", "Mineure"]],
    },
}

out = os.path.join(DOCS, "evidence", "docx-data.json")
with io.open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print("ecrit : %s" % out)
print("tests=%d pass=%d fail=%d bugs=%d"
      % (total, npass, total - npass, len(bugs)))
for c in data["stats"]["parCategorie"]:
    print("  %-18s %2d  (%d Pass / %d Fail)" % (c["nom"], c["total"], c["pass"], c["fail"]))
