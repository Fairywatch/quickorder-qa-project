# BUG-004 — Le stock devient negatif apres une commande superieure aux quantites disponibles

| | |
|---|---|
| Identifiant | BUG-004 |
| Severite | Majeure |
| Priorite | P1 |
| Risque couvert | R6 (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | RM04 |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

Le stock est decremente sans verification prealable de sa valeur. Il peut donc descendre en dessous de zero et n'a plus aucune signification.

## Preconditions

- Tofu Bowl (produit id 10), stock initial de 100 unites

## Etapes de reproduction

1. Epuiser le stock par commandes successives de 20 unites
2. Verifier que le stock est a 0 : GET /api/products/10
3. Passer une commande supplementaire de 20 unites
4. Relire le stock

## Resultat attendu

La commande est refusee et le stock reste superieur ou egal a 0.

## Resultat obtenu

HTTP 201 : la commande est acceptee et le stock passe de 0 a -20.

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

Cas RM04 — Absence de stock négatif après une commande excédentaire

```
stock avant dernière commande: -120
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 10, "quantity": 20}], "payment_method": "card"}
--> HTTP 201
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:11.824994","delivery_fee":3.49,"discount":0.0,"id":34,"items":[{"line_total":258.0,"product_id":10,"product_name":"Tofu Bowl","quantity":20,"unit_price":12.9}],"payment_method":"card","payment_status":"paid","restaurant_id":2,"st ...[tronque]
stock après: -140
```

## Impact

Les donnees de stock ne sont plus exploitables : ni pour l'affichage client, ni pour le reapprovisionnement, ni pour le pilotage. Le defaut s'aggrave a chaque commande.
