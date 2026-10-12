# BUG-005 — Un paiement PayPal cree systematiquement deux commandes identiques

| | |
|---|---|
| Identifiant | BUG-005 |
| Severite | Bloquante |
| Priorite | P0 — correction avant toute mise en production |
| Risque couvert | R1 (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | RM05, RM16 |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

Le client choisit PayPal comme moyen de paiement, sur l'interface web comme via l'API. L'application enregistre deux commandes distinctes pour un seul acte d'achat. Le client est donc facture deux fois et le restaurant prepare deux fois la commande.

## Preconditions

- Application demarree, base reinitialisee
- Compte client alice@example.com connecte (ou cle API valide)
- Un panier valide contenant au moins un produit

## Etapes de reproduction

1. Relever le nombre de commandes du client : GET /api/orders -> champ count
2. Passer une commande unique en choisissant payment_method=paypal
3. Relever a nouveau le nombre de commandes : GET /api/orders

## Resultat attendu

Une seule commande est creee. Le compteur augmente de 1.

## Resultat obtenu

Deux commandes sont creees pour un seul paiement. Le compteur augmente de 2. Le defaut est reproduit a l'identique sur les deux canaux : API (RM05) et interface web (RM16).

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

Cas RM05 — Unicite de la commande en paiement PayPal

```
GET /api/orders count avant=34
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 9, "quantity": 1}], "payment_method": "paypal"}
--> HTTP 201
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:11.959574","delivery_fee":3.49,"discount":0.0,"id":35,"items":[{"line_total":3.2,"product_id":9,"product_name":"Miso Soup","quantity":1,"unit_price":3.2}],"payment_method":"paypal ...[tronque]
GET /api/orders count après=36 --> delta=2
```

Cas RM16 — Unicite de la commande PayPal dans l'interface web

```
POST /checkout (payment_method=paypal)
--> HTTP 200
commandes avant=38 / après=40 --> delta=2
```

## Impact

Double facturation du client et double preparation par le restaurant. C'est l'anomalie la plus couteuse de l'audit : elle genere un litige financier a chaque commande PayPal, sans aucune action particuliere du client. Elle justifie a elle seule un No-Go.
