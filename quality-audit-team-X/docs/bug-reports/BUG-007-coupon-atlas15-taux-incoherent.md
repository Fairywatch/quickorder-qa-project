# BUG-007 — La promotion ATLAS15 est annoncee a 15 % mais n'applique que 10 %

| | |
|---|---|
| Identifiant | BUG-007 |
| Severite | Majeure |
| Priorite | P2 |
| Risque couvert | R5 (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | RM07 |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

La fiche du restaurant Couscous Atlas annonce explicitement 15 % de reduction avec le code ATLAS15, et la page d'accueil relaie la meme promotion. Le coupon reellement enregistre applique 10 %.

## Preconditions

- Couscous Atlas affiche : Code ATLAS15 annonce comme -15% sur ce restaurant
- La fiche restaurant affiche : utilisez le code ATLAS15 pour obtenir 15 % de reduction

## Etapes de reproduction

1. Lire la promotion annoncee sur la fiche du restaurant
2. Valider le coupon : POST /api/coupons/validate avec code=ATLAS15 et subtotal=100
3. Comparer le taux applique au taux annonce

## Resultat attendu

Une remise de 15 %, soit 15,00 EUR pour un sous-total de 100 EUR, conformement a l'annonce.

## Resultat obtenu

discount_percent=10.0 et une remise de 10,00 EUR, soit 5,00 EUR de moins que le montant annonce au client.

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

Cas RM07 — Coherence entre la promotion annoncee et la remise appliquee

```
Annonce sur la fiche restaurant : 🎟️ Code ATLAS15 annoncé comme -15% sur ce restaurant
POST http://127.0.0.1:5000/api/coupons/validate
body: {"code": "ATLAS15", "subtotal": 100}
--> HTTP 200
{"code":"ATLAS15","discount":10.0,"discount_percent":10.0,"valid":true}
```

## Impact

Ecart entre la promotion commerciale affichee et la remise reellement accordee. Au-dela de la perte de confiance, cela constitue une pratique commerciale trompeuse susceptible d'etre contestee.
