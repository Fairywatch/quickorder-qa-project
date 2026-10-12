# BUG-010 — L'API de validation des coupons fait confiance au montant transmis par le client

| | |
|---|---|
| Identifiant | BUG-010 |
| Severite | Critique |
| Priorite | P1 |
| Risque couvert | R4 (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | RM10 |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

L'endpoint POST /api/coupons/validate calcule la remise a partir du sous-total envoye dans la requete, sans le recalculer ni le verifier cote serveur. N'importe quel appelant peut donc declarer le montant de son choix.

## Preconditions

- Coupon SAVE20 actif : 20 %, montant minimum 35 EUR, plafond 12 EUR
- Cle API valide

## Etapes de reproduction

1. Envoyer POST /api/coupons/validate avec un sous-total arbitraire : {"code": "SAVE20", "subtotal": 999999}
2. Observer la reponse

## Resultat attendu

Le serveur recalcule le sous-total a partir du panier reel, ou refuse un montant qu'il ne peut pas verifier.

## Resultat obtenu

Le serveur repond valid=true et calcule la remise sur le montant fantaisiste fourni par le client, sans aucune verification.

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

Cas RM10 — Validation cote serveur du sous-total transmis par le client

```
POST http://127.0.0.1:5000/api/coupons/validate
body: {"code": "SAVE20", "subtotal": 999999}
--> HTTP 200
{"code":"SAVE20","discount":12.0,"discount_percent":20.0,"valid":true}
```

## Impact

Un client peut franchir artificiellement le seuil minimum d'un coupon et obtenir une remise a laquelle il n'a pas droit. C'est une faille de logique metier exploitable directement depuis l'API, sans outil particulier.
