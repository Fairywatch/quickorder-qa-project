# BUG-006 — Un paiement en especes inferieur au montant du est accepte et marque paye

| | |
|---|---|
| Identifiant | BUG-006 |
| Severite | Critique |
| Priorite | P1 |
| Risque couvert | R3 (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | RM06 |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

Lors d'un paiement en especes, le montant annonce par le client n'est pas compare au total a payer. La commande est enregistree comme payee et le montant a rendre devient negatif.

## Preconditions

- Un produit commandable : Miso Soup (id 9) a 3,20 EUR
- Frais de livraison Tokyo Bowl : 3,49 EUR, soit un total de 6,69 EUR

## Etapes de reproduction

1. Passer une commande avec payment_method=cash et cash_received=1
2. Observer les champs payment_status, total et change_due de la reponse

## Resultat attendu

La commande est refusee : le montant remis (1,00 EUR) est inferieur au total du (6,69 EUR).

## Resultat obtenu

HTTP 201 : la commande est creee avec payment_status=paid, total=6.69 et change_due=-5.69. Le systeme annonce un rendu de monnaie negatif, ce qui n'a aucun sens comptable.

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

Cas RM06 — Refus d'un paiement en especes insuffisant

```
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 9, "quantity": 1}], "payment_method": "cash", "cash_received": 1}
--> HTTP 201
{"cash_received":1.0,"change_due":-5.69,"created_at":"2026-09-22T13:14:12.051825","delivery_fee":3.49,"discount":0.0,"id":37,"items":[{"line_total":3.2,"product_id":9,"product_name":"Miso Soup","quantity":1,"unit_price":3.2}],"payment_method":"cash","payment_status":"paid","restaurant_id":2,"status":"confirmed","subtotal":3.2,"total":6.69}
```

## Impact

Perte financiere directe a chaque occurrence : la commande est preparee et livree alors qu'elle n'est pas payee. Un montant a rendre negatif indique en outre une absence totale de controle de coherence comptable.
