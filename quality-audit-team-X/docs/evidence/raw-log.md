# Journal d'execution brut — campagne QuickOrder

Execute le 2026-09-22 15:14 contre http://127.0.0.1:5000

Chaque bloc ci-dessous contient la requete reellement envoyee et la reponse reellement recue par l'application.


## 1. Cas nominaux


### N01 — Affichage de la page d'accueil avec la liste des restaurants  
Statut : Pass

```
GET /
--> HTTP 200
Restaurants detectes dans le HTML : ['Burger Factory', 'Tokyo Bowl', 'Green Kitchen', 'Pizza Roma', 'Couscous Atlas']
```

### N02 — Connexion d'un client avec des identifiants valides  
Statut : Pass

```
POST /login (alice@example.com)
--> HTTP 200
lien de deconnexion present : True
```

### N03 — Ajout d'un produit disponible au panier  
Statut : Pass

```
POST /cart/add/1 (quantity=2)
--> HTTP 200
GET /cart --> HTTP 200
flash: ['Classic Burger ajouté au panier.', '🎟️ 🎟️ Code ATLAS15 annoncé comme -15% sur ce restaurant⭐ 4.9 · 40 min · Livraison 2.99 € · Minimum 25.00 €\nVoir le menu\nJaponaisOUVERT']
```

### N04 — Passage de commande complet en paiement carte  
Statut : Pass

```
POST /checkout (confirm=1, payment_method=card)
--> HTTP 200
flash: ['Commande confirmée !']
```

### N05 — Consultation de la liste des restaurants via l'API authentifiee  
Statut : Pass

```
GET http://127.0.0.1:5000/api/restaurants
--> HTTP 200
{"count":6,"items":[{"address":"7 boulevard Voltaire, Paris","category":"Marocain","delivery_fee":2.99,"delivery_time_min":40,"description":"Cuisine marocaine familiale et g\u00e9n\u00e9reuse.","id":5,"is_open":true,"minimum_order":25.0,"name":"Couscous Atlas","promo_text":"\ud83c\udf9f\ufe0f Code A ...[tronque]
```

### N06 — Creation d'une commande valide via l'API  
Statut : Pass

```
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 1, "quantity": 2}], "payment_method": "card"}
--> HTTP 201
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:09.435999","delivery_fee":2.99,"discount":0.0,"id":23,"items":[{"line_total":23.8,"product_id":1,"product_name":"Classic Burger","quantity":2,"unit_price":11.9}],"payment_method":"card","payment_status":"paid","restaurant_id":1,"status":"confirmed","subtotal":23.8,"total":26.79}
```

### N07 — Annulation d'une commande au statut 'confirmed'  
Statut : Pass

```
POST http://127.0.0.1:5000/api/orders/23/cancel
--> HTTP 200
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:09.435999","delivery_fee":2.99,"discount":0.0,"id":23,"items":[{"line_total":23.8,"product_id":1,"product_name":"Classic Burger","quantity":2,"unit_price":11.9}],"payment_method":"card","payment_status":"paid","restaurant_id":1," ...[tronque]
```

### N08 — Endpoint de supervision /api/health  
Statut : Pass

```
GET http://127.0.0.1:5000/api/health
--> HTTP 200
{"service":"quickorder","status":"ok","timestamp":"2026-09-22T13:14:09.514431"}
```

## 2. Cas aux limites


### L01 — Commande API avec la quantite minimale autorisee (1)  
Statut : Pass

```
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 9, "quantity": 1}], "payment_method": "card"}
--> HTTP 201
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:09.544141","delivery_fee":3.49,"discount":0.0,"id":24,"items":[{"line_total":3.2,"product_id":9,"product_name":"Miso Soup","quantity":1,"unit_price":3.2}],"payment_method":"card","payment_status":"paid","restaurant_id":2,"status" ...[tronque]
```

### L02 — Commande API avec la quantite maximale autorisee (20)  
Statut : Pass

```
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 9, "quantity": 20}], "payment_method": "card"}
--> HTTP 201
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:09.591227","delivery_fee":3.49,"discount":0.0,"id":25,"items":[{"line_total":64.0,"product_id":9,"product_name":"Miso Soup","quantity":20,"unit_price":3.2}],"payment_method":"card","payment_status":"paid","restaurant_id":2,"statu ...[tronque]
```

### L03 — Refus d'une commande API au-dela de la quantite maximale (21)  
Statut : Pass

```
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 9, "quantity": 21}], "payment_method": "card"}
--> HTTP 400
{"error":"quantity must be between 1 and 20"}
```

### L04 — Refus d'une commande API avec une quantite nulle (0)  
Statut : Pass

```
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 9, "quantity": 0}], "payment_method": "card"}
--> HTTP 400
{"error":"quantity must be between 1 and 20"}
```

### L05 — Coupon accepte au montant minimum exact (20.00 EUR)  
Statut : Pass

```
POST http://127.0.0.1:5000/api/coupons/validate
body: {"code": "WELCOME10", "subtotal": 20}
--> HTTP 200
{"code":"WELCOME10","discount":2.0,"discount_percent":10.0,"valid":true}
```

### L06 — Coupon refuse juste sous le montant minimum (19.99 EUR)  
Statut : Pass

```
POST http://127.0.0.1:5000/api/coupons/validate
body: {"code": "WELCOME10", "subtotal": 19.99}
--> HTTP 200
{"error":"Montant minimum non atteint.","minimum":20.0,"valid":false}
```

### L07 — Plafonnement de la remise au max_discount (SAVE20 plafonne a 12 EUR)  
Statut : Pass

```
POST http://127.0.0.1:5000/api/coupons/validate
body: {"code": "SAVE20", "subtotal": 200}
--> HTTP 200
{"code":"SAVE20","discount":12.0,"discount_percent":20.0,"valid":true}
```

### L08 — Commande de la totalite du stock restant (Salmon Bowl, stock 2)  
Statut : Fail

```
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 7, "quantity": 0}], "payment_method": "card"}
--> HTTP 400
{"error":"quantity must be between 1 and 20"}

stock avant=0 / après=0
```

### L09 — Inscription acceptee avec un mot de passe de 8 caracteres  
Statut : Pass

```
POST /register (password=8 caracteres)
--> HTTP 200
flash: ['🎟️ 🎟️ Code ATLAS15 annoncé comme -15% sur ce restaurant⭐ 4.9 · 40 min · Livraison 2.99 € · Minimum 25.00 €\nVoir le menu\nJaponaisOUVERT', '🎟️ Livraison gratuite dès 30 € avec TOKYO30⭐ 4.8 · 35 min · Livraison 3.49 € · Minimum 15.00 €\nVoir le menu\nBurgersOUVERT']
```

### L10 — Inscription refusee avec un mot de passe de 7 caracteres  
Statut : Pass

```
POST /register (password=7 caracteres)
--> HTTP 200
flash: ['Nom, email valide et mot de passe d&#39;au moins 8 caractères requis.']
```

## 3. Cas d'erreur


### E01 — Refus d'un appel API sans cle d'authentification  
Statut : Pass

```
GET http://127.0.0.1:5000/api/restaurants
--> HTTP 401
{"error":"missing or invalid X-API-Key","hint":"Use Swagger > Authorize"}
```

### E02 — Refus d'un appel API avec une cle invalide  
Statut : Pass

```
GET http://127.0.0.1:5000/api/restaurants
--> HTTP 401
{"error":"missing or invalid X-API-Key","hint":"Use Swagger > Authorize"}
```

### E03 — Consultation d'un restaurant inexistant  
Statut : Pass

```
GET http://127.0.0.1:5000/api/restaurants/9999
--> HTTP 404
<!doctype html>
<html lang=en>
<title>404 Not Found</title>
<h1>Not Found</h1>
<p>The requested URL was not found on the server. If you entered the URL manually please check your spelling and try agai ...[tronque]
```

### E04 — Consultation d'un produit inexistant  
Statut : Pass

```
GET http://127.0.0.1:5000/api/products/9999
--> HTTP 404
<!doctype html>
<html lang=en>
<title>404 Not Found</title>
<h1>Not Found</h1>
<p>The requested URL was not found on the server. If you entered the URL manually please check your spelling and try agai ...[tronque]
```

### E05 — Refus de connexion avec un mot de passe errone  
Statut : Pass

```
POST /login (mot de passe errone)
--> HTTP 200
flash: ['Email ou mot de passe incorrect.']
```

### E06 — Refus d'un coupon expire  
Statut : Pass

```
POST http://127.0.0.1:5000/api/coupons/validate
body: {"code": "EXPIRED10", "subtotal": 50}
--> HTTP 404
{"error":"Coupon invalide ou expir\u00e9.","valid":false}
```

### E07 — Acces au checkout avec un panier vide  
Statut : Pass

```
GET /checkout (panier vide)
--> HTTP 200
URL finale: http://127.0.0.1:5000/cart
flash: ['Votre panier est vide.']
```

### E08 — Refus d'une commande melangeant deux restaurants  
Statut : Pass

```
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 1, "quantity": 1}, {"product_id": 9, "quantity": 1}], "payment_method": "card"}
--> HTTP 400
{"error":"all products must belong to the same restaurant"}
```

### E09 — Acces a l'espace d'administration par un client standard  
Statut : Pass

```
GET /admin/ (role customer)
--> HTTP 200
URL finale: http://127.0.0.1:5000/
flash: ['Accès réservé aux administrateurs.', '🎟️ 🎟️ Code ATLAS15 annoncé comme -15% sur ce restaurant⭐ 4.9 · 40 min · Livraison 2.99 € · Minimum 25.00 €\nVoir le menu\nJaponaisOUVERT']
```

### E10 — Consultation de la commande d'un autre client (interface web)  
Statut : Pass

```
GET /orders/1 (connecte en tant que Bob)
--> HTTP 200
URL finale: http://127.0.0.1:5000/orders
flash: ['Commande inaccessible.']
```

### E11 — Refus d'une commande avec une quantite non numerique  
Statut : Pass

```
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 9, "quantity": "abc"}], "payment_method": "card"}
--> HTTP 400
{"error":"quantity must be an integer"}
```

### E12 — Refus d'un mode de paiement non supporte  
Statut : Pass

```
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 9, "quantity": 1}], "payment_method": "bitcoin"}
--> HTTP 400
{"error":"invalid payment_method"}
```

## 4. Regles metier


### RM01 — Respect du montant minimum de commande du restaurant  
Statut : Fail  
Anomalie : BUG-001

```
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 23, "quantity": 1}], "payment_method": "card"}
--> HTTP 201
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:11.361333","delivery_fee":2.99,"discount":0.0,"id":26,"items":[{"line_total":3.5,"product_id":23,"product_name":"Th\u00e9 \u00e0 la menthe","quantity":1,"unit_price":3.5}],"payment_method":"card","payment_status":"paid","restaurant_id":5,"status":"confirmed","subtotal":3.5,"total":6.49}
```

### RM02 — Blocage des commandes vers un restaurant ferme  
Statut : Fail  
Anomalie : BUG-002

```
GET /api/restaurants/6 --> is_open=False
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 24, "quantity": 1}], "payment_method": "card"}
--> HTTP 201
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:11.422231","delivery_fee":2.99,"discount":0.0,"id":27,"items":[{"line_total":14.0,"product_id":24,"product_name":"Late Sushi Box","quantity":1,"unit_price":14.0}],"payment_method":"card","payment_status":"paid","restaurant_id":6, ...[tronque]
```

### RM03 — Blocage de la commande d'un produit en rupture de stock  
Statut : Fail  
Anomalie : BUG-003

```
GET /api/products/8 --> stock=-1
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 8, "quantity": 1}], "payment_method": "card"}
--> HTTP 201
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:11.471310","delivery_fee":3.49,"discount":0.0,"id":28,"items":[{"line_total":6.9,"product_id":8,"product_name":"Gyozas","quantity":1,"unit_price":6.9}],"payment_method":"card","payment_status":"paid","restaurant_id":2,"status":"c ...[tronque]
stock après: -2
```

### RM04 — Absence de stock négatif après une commande excédentaire  
Statut : Fail  
Anomalie : BUG-004

```
stock avant dernière commande: -120
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 10, "quantity": 20}], "payment_method": "card"}
--> HTTP 201
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:11.824994","delivery_fee":3.49,"discount":0.0,"id":34,"items":[{"line_total":258.0,"product_id":10,"product_name":"Tofu Bowl","quantity":20,"unit_price":12.9}],"payment_method":"card","payment_status":"paid","restaurant_id":2,"st ...[tronque]
stock après: -140
```

### RM05 — Unicite de la commande en paiement PayPal  
Statut : Fail  
Anomalie : BUG-005

```
GET /api/orders count avant=34
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 9, "quantity": 1}], "payment_method": "paypal"}
--> HTTP 201
{"cash_received":null,"change_due":null,"created_at":"2026-09-22T13:14:11.959574","delivery_fee":3.49,"discount":0.0,"id":35,"items":[{"line_total":3.2,"product_id":9,"product_name":"Miso Soup","quantity":1,"unit_price":3.2}],"payment_method":"paypal ...[tronque]
GET /api/orders count après=36 --> delta=2
```

### RM06 — Refus d'un paiement en especes insuffisant  
Statut : Fail  
Anomalie : BUG-006

```
POST http://127.0.0.1:5000/api/orders
body: {"items": [{"product_id": 9, "quantity": 1}], "payment_method": "cash", "cash_received": 1}
--> HTTP 201
{"cash_received":1.0,"change_due":-5.69,"created_at":"2026-09-22T13:14:12.051825","delivery_fee":3.49,"discount":0.0,"id":37,"items":[{"line_total":3.2,"product_id":9,"product_name":"Miso Soup","quantity":1,"unit_price":3.2}],"payment_method":"cash","payment_status":"paid","restaurant_id":2,"status":"confirmed","subtotal":3.2,"total":6.69}
```

### RM07 — Coherence entre la promotion annoncee et la remise appliquee  
Statut : Fail  
Anomalie : BUG-007

```
Annonce sur la fiche restaurant : 🎟️ Code ATLAS15 annoncé comme -15% sur ce restaurant
POST http://127.0.0.1:5000/api/coupons/validate
body: {"code": "ATLAS15", "subtotal": 100}
--> HTTP 200
{"code":"ATLAS15","discount":10.0,"discount_percent":10.0,"valid":true}
```

### RM08 — Filtre 'frais de livraison maximum' sur la page d'accueil  
Statut : Fail  
Anomalie : BUG-008

```
GET /?max_delivery=2.50
--> HTTP 200
Restaurants affiches : ['Burger Factory', 'Couscous Atlas', 'Night Sushi', 'Tokyo Bowl']
```

### RM09 — Recherche par mot-cle portant sur le nom et la description  
Statut : Fail  
Anomalie : BUG-009

```
GET /?q=pizza --> ['Pizza Roma']
GET /?q=romaines --> []
```

### RM10 — Validation cote serveur du sous-total transmis par le client  
Statut : Fail  
Anomalie : BUG-010

```
POST http://127.0.0.1:5000/api/coupons/validate
body: {"code": "SAVE20", "subtotal": 999999}
--> HTTP 200
{"code":"SAVE20","discount":12.0,"discount_percent":20.0,"valid":true}
```

### RM11 — Depot d'un avis reserve aux clients ayant commande  
Statut : Fail  
Anomalie : BUG-011

```
POST /restaurant/5/review (Bob, aucune commande chez ce restaurant)
--> HTTP 200
flash: ['Merci pour votre avis !', 'Promotion annoncée : 🎟️ Code ATLAS15 annoncé comme -15% sur ce restaurant']
```

### RM12 — Refus des transitions de statut impossibles (livree -> confirmee)  
Statut : Pass  
Anomalie : BUG-012

```
POST /admin/orders/1/status (status=confirmed)
--> HTTP 200
statut avant=confirmed / après=confirmed
flash: ['Statut mis à jour.']
```

### RM13 — Exposition des restaurants fermes dans la liste API  
Statut : Fail  
Anomalie : BUG-013

```
GET /api/restaurants --> count=6
Fermes retournes : ['Night Sushi']
```

### RM14 — Blocage de l'ajout au panier d'un produit en rupture (interface web)  
Statut : Fail  
Anomalie : BUG-003

```
GET /api/products/4 --> stock=0
GET /restaurant/1 --> mention HORS STOCK: True
POST /cart/add/4 (quantity=3) --> HTTP 200
flash: ['Veggie Burger ajouté au panier.', '🎟️ 🎟️ Code ATLAS15 annoncé comme -15% sur ce restaurant⭐ 4.9 · 40 min · Livraison 2.99 € · Minimum 25.00 €\nVoir le menu\nJaponaisOUVERT']
GET /cart --> Veggie Burger present: True
```

### RM15 — Montant minimum applique dans le tunnel de commande web  
Statut : Fail  
Anomalie : BUG-001

```
POST /checkout (panier 3.50 EUR, minimum 25 EUR)
--> HTTP 200
flash: ['Commande confirmée !']
```

### RM16 — Unicite de la commande PayPal dans l'interface web  
Statut : Fail  
Anomalie : BUG-005

```
POST /checkout (payment_method=paypal)
--> HTTP 200
commandes avant=38 / après=40 --> delta=2
```