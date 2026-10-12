# BUG-002 — Un restaurant ferme accepte les commandes

| | |
|---|---|
| Identifiant | BUG-002 |
| Severite | Critique |
| Priorite | P1 |
| Risque couvert | R2 (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | RM02 |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

Le restaurant Night Sushi est explicitement ferme (is_open=false) et affiche la mention FERME sur la page d'accueil. Il accepte pourtant les commandes : l'etat d'ouverture est affiche mais jamais controle au moment de l'engagement.

## Preconditions

- Night Sushi (restaurant id 6) a is_open=false
- Le produit Late Sushi Box (id 24) appartient a ce restaurant

## Etapes de reproduction

1. Verifier l'etat du restaurant : GET /api/restaurants/6 -> is_open=false
2. Commander un produit de ce restaurant : POST /api/orders avec product_id=24

## Resultat attendu

La commande est refusee avec un message indiquant que le restaurant est ferme.

## Resultat obtenu

HTTP 201 : la commande est creee et marquee payee, alors que le restaurant est ferme.

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

Cas RM02 — Blocage des commandes vers un restaurant ferme

```
GET /api/restaurants/6 --> is_open=False
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 24, "quantity": 1}], "payment_method": "card"}
--> HTTP 201
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:11.422231","delivery_fee":2.99,"discount":0.0,"id":27,"items":[{"line_total":14.0,"product_id":24,"product_name":"Late Sushi Box","quantity":1,"unit_price":14.0}],"payment_method":"card","payment_status":"paid","restaurant_id":6, ...[tronque]
```

## Impact

Le client paie une commande qui ne sera jamais preparee ni livree. Remboursement systematique, perte de confiance et cout de traitement du litige.
