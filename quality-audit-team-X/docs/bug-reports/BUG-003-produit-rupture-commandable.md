# BUG-003 — Un produit en rupture de stock reste commandable

| | |
|---|---|
| Identifiant | BUG-003 |
| Severite | Critique |
| Priorite | P1 |
| Risque couvert | R2 (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | RM03, RM14 |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

Les produits dont le stock est a 0 affichent bien la mention HORS STOCK sur la fiche restaurant, mais le bouton Ajouter reste actif et l'ajout au panier aboutit. La commande va ensuite jusqu'au paiement. L'information est donc purement decorative.

## Preconditions

- Veggie Burger (produit id 4) : stock=0, available=true
- Gyozas (produit id 8) : stock=0, available=true

## Etapes de reproduction

1. Ouvrir la fiche du restaurant : GET /restaurant/1
2. Constater la mention HORS STOCK sur le Veggie Burger
3. Ajouter malgre tout le produit au panier : POST /cart/add/4 quantity=3
4. Consulter le panier : GET /cart
5. Variante API : POST /api/orders avec product_id=8 (stock 0)

## Resultat attendu

L'ajout au panier est refuse et la commande est rejetee : le produit est en rupture.

## Resultat obtenu

Le produit est ajoute au panier malgre la mention HORS STOCK. Cote API, la commande est acceptee (HTTP 201) et le stock passe de 0 a -1.

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

Cas RM03 — Blocage de la commande d'un produit en rupture de stock

```
GET /api/products/8 --> stock=-1
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 8, "quantity": 1}], "payment_method": "card"}
--> HTTP 201
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:11.471310","delivery_fee":3.49,"discount":0.0,"id":28,"items":[{"line_total":6.9,"product_id":8,"product_name":"Gyozas","quantity":1,"unit_price":6.9}],"payment_method":"card","payment_status":"paid","restaurant_id":2,"status":"c ...[tronque]
stock après: -2
```

Cas RM14 — Blocage de l'ajout au panier d'un produit en rupture (interface web)

```
GET /api/products/4 --> stock=0
GET /restaurant/1 --> mention HORS STOCK: True
POST /cart/add/4 (quantity=3) --> HTTP 200
flash: ['Veggie Burger ajouté au panier.', '🎟️ 🎟️ Code ATLAS15 annoncé comme -15% sur ce restaurant⭐ 4.9 · 40 min · Livraison 2.99 € · Minimum 25.00 €\nVoir le menu\nJaponaisOUVERT']
GET /cart --> Veggie Burger present: True
```

## Impact

Commande impossible a honorer, et stock qui devient incoherent. L'affichage HORS STOCK donne une fausse impression de controle : le client constate le probleme apres avoir paye.
