# BUG-001 — Le montant minimum de commande annonce par le restaurant n'est jamais applique

| | |
|---|---|
| Identifiant | BUG-001 |
| Severite | Majeure |
| Priorite | P1 |
| Risque couvert | R7 (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | RM01, RM15 |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

Chaque restaurant affiche un montant minimum de commande sur sa fiche. Ce montant est presente au client mais n'est controle ni dans le tunnel web, ni par l'API.

## Preconditions

- Couscous Atlas (restaurant id 5) annonce un minimum de 25,00 EUR
- The a la menthe (produit id 23) a 3,50 EUR

## Etapes de reproduction

1. Constater le minimum affiche sur la fiche du restaurant
2. Interface web : ajouter 1 The a la menthe au panier puis valider le checkout
3. API : POST /api/orders avec product_id=23, quantity=1

## Resultat attendu

La commande est bloquee tant que le sous-total n'atteint pas 25,00 EUR.

## Resultat obtenu

La commande de 3,50 EUR est confirmee sur les deux canaux. Cote web, le message Commande confirmee ! s'affiche normalement.

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

Cas RM01 — Respect du montant minimum de commande du restaurant

```
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 23, "quantity": 1}], "payment_method": "card"}
--> HTTP 201
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:11.361333","delivery_fee":2.99,"discount":0.0,"id":26,"items":[{"line_total":3.5,"product_id":23,"product_name":"Th\u00e9 \u00e0 la menthe","quantity":1,"unit_price":3.5}],"payment_method":"card","payment_status":"paid","restaurant_id":5,"status":"confirmed","subtotal":3.5,"total":6.49}
```

Cas RM15 — Montant minimum applique dans le tunnel de commande web

```
POST /checkout (panier 3.50 EUR, minimum 25 EUR)
--> HTTP 200
flash: ['Commande confirmée !']
```

## Impact

Le restaurant recoit des commandes non rentables qu'il est contractuellement cense pouvoir refuser. La regle affichee au client n'a aucune valeur, ce qui expose a un litige avec les restaurants partenaires.
