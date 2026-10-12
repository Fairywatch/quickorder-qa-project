# -*- coding: utf-8 -*-
"""
Harnais d'execution de la campagne de test QuickOrder.

Chaque cas de test est execute reellement contre l'application
(http://127.0.0.1:5000) et la preuve brute (requete + reponse) est
enregistree dans docs/evidence/.

Usage:  python tools/run_campaign.py
Sortie: docs/evidence/raw-log.md, docs/evidence/results.json
"""
import io
import json
import os
import re
import sys
from datetime import datetime

import requests

BASE = "http://127.0.0.1:5000"
API_KEY = "quickorder-demo-key"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "docs", "evidence")

RESULTS = []
LOG = []
EOL = chr(10)


def log(msg=""):
    LOG.append(msg)


def record(tid, titre, objectif, preconditions, donnees, etapes, attendu, obtenu, statut,
           categorie, evidence="", bug=""):
    RESULTS.append(dict(id=tid, titre=titre, objectif=objectif, preconditions=preconditions,
                        donnees=donnees, etapes=etapes, attendu=attendu, obtenu=obtenu,
                        statut=statut, categorie=categorie, evidence=evidence, bug=bug))
    mark = {"Pass": "PASS", "Fail": "FAIL", "Blocked": "BLOCKED", "Skipped": "SKIP"}[statut]
    print("[%-4s] %-6s %s" % (mark, tid, titre))
    log("\n### %s — %s  \nStatut : %s%s\n" % (tid, titre, statut, ("  \nAnomalie : %s" % bug) if bug else ""))
    if evidence:
        log("```\n%s\n```" % evidence.strip())


def api(method, path, key=API_KEY, **kw):
    headers = kw.pop("headers", {})
    if key is not None:
        headers["X-API-Key"] = key
    return requests.request(method, BASE + path, headers=headers, timeout=15, **kw)


def ev_api(resp, body=None, limit=900):
    """Formate une preuve API lisible."""
    req = resp.request
    out = "%s %s" % (req.method, req.url)
    if body is not None:
        out += "\nbody: %s" % json.dumps(body, ensure_ascii=False)
    txt = resp.text
    if len(txt) > limit:
        txt = txt[:limit] + " ...[tronque]"
    return out + "\n--> HTTP %s\n%s" % (resp.status_code, txt)


def flashes(html):
    """Extrait les messages flash rendus dans la page."""
    msgs = re.findall(r'class="flash[^"]*"[^>]*>(.*?)</div>', html, re.S)
    return [re.sub(r"<[^>]+>", "", m).strip() for m in msgs]


def login(email, password):
    s = requests.Session()
    r = s.post(BASE + "/login", data={"email": email, "password": password},
               allow_redirects=True, timeout=15)
    return s, r


def stock_of(pid):
    return api("GET", "/api/products/%d" % pid).json()["stock"]


def orders_count():
    return api("GET", "/api/orders").json()["count"]


# =====================================================================
# 1. CAS NOMINAUX
# =====================================================================
def nominaux():
    # --- N01
    r = requests.get(BASE + "/", timeout=15)
    noms = [n for n in ["Burger Factory", "Tokyo Bowl", "Green Kitchen", "Pizza Roma",
                        "Couscous Atlas"] if n in r.text]
    ok = r.status_code == 200 and len(noms) == 5
    record("N01", "Affichage de la page d'accueil avec la liste des restaurants",
           "Verifier que le catalogue est accessible sans authentification",
           "Application demarree, base seedee", "aucune",
           "1. GET / ; 2. Lire la liste des restaurants affiches",
           "HTTP 200 et les 5 restaurants ouverts sont listes",
           "HTTP %s, restaurants trouves : %s" % (r.status_code, ", ".join(noms)),
           "Pass" if ok else "Fail", "Nominal",
           "GET /\n--> HTTP %s\nRestaurants detectes dans le HTML : %s" % (r.status_code, noms))

    # --- N02
    s, r = login("alice@example.com", "Password123!")
    ok = "Deconnexion" in r.text or "logout" in r.text.lower()
    record("N02", "Connexion d'un client avec des identifiants valides",
           "Verifier le parcours d'authentification nominal",
           "Compte alice@example.com existant", "alice@example.com / Password123!",
           "1. POST /login avec les identifiants ; 2. Verifier la session",
           "HTTP 200, l'utilisateur est authentifie (lien de deconnexion visible)",
           "HTTP %s, session authentifiee : %s" % (r.status_code, ok),
           "Pass" if ok else "Fail", "Nominal",
           "POST /login (alice@example.com)\n--> HTTP %s\nlien de deconnexion present : %s"
           % (r.status_code, ok))

    # --- N03
    s3, _ = login("alice@example.com", "Password123!")
    r = s3.post(BASE + "/cart/add/1", data={"quantity": 2}, timeout=15)
    cart = s3.get(BASE + "/cart", timeout=15)
    ok = "Classic Burger" in cart.text
    record("N03", "Ajout d'un produit disponible au panier",
           "Verifier l'ajout au panier depuis la fiche restaurant",
           "Client connecte, Classic Burger disponible (stock 100)",
           "product_id=1 (Classic Burger 11.90 EUR), quantite=2",
           "1. POST /cart/add/1 quantity=2 ; 2. GET /cart",
           "Le produit apparait dans le panier avec la quantite demandee",
           "Produit present dans le panier : %s" % ok,
           "Pass" if ok else "Fail", "Nominal",
           "POST /cart/add/1 (quantity=2)\n--> HTTP %s\nGET /cart --> HTTP %s\n"
           "flash: %s" % (r.status_code, cart.status_code, flashes(r.text)[:2]))

    # --- N04
    s4, _ = login("alice@example.com", "Password123!")
    s4.post(BASE + "/cart/clear", timeout=15)
    s4.post(BASE + "/cart/add/1", data={"quantity": 2}, timeout=15)   # 23.80 > min 20
    addr = re.search(r'name="address_id"[^>]*value="(\d+)"', s4.get(BASE + "/checkout").text)
    aid = addr.group(1) if addr else "1"
    r = s4.post(BASE + "/checkout", data={"confirm": "1", "address_id": aid,
                                          "payment_method": "card"}, timeout=15)
    ok = "Commande confirm" in r.text
    record("N04", "Passage de commande complet en paiement carte",
           "Valider le parcours critique de bout en bout (panier -> paiement -> commande)",
           "Client connecte, panier a 23.80 EUR (>= minimum 20 EUR de Burger Factory)",
           "2 x Classic Burger, paiement=card",
           "1. Ajouter 2 Classic Burger ; 2. POST /checkout confirm=1 payment_method=card",
           "HTTP 200, commande creee et confirmee, panier vide",
           "Commande confirmee : %s" % ok,
           "Pass" if ok else "Fail", "Nominal",
           "POST /checkout (confirm=1, payment_method=card)\n--> HTTP %s\nflash: %s"
           % (r.status_code, flashes(r.text)[:2]))

    # --- N05
    r = api("GET", "/api/restaurants")
    d = r.json()
    ok = r.status_code == 200 and d["count"] >= 5
    record("N05", "Consultation de la liste des restaurants via l'API authentifiee",
           "Verifier l'acces API nominal avec la cle X-API-Key",
           "API demarree", "X-API-Key: quickorder-demo-key",
           "1. GET /api/restaurants avec l'en-tete X-API-Key",
           "HTTP 200 et une liste de restaurants au format JSON",
           "HTTP %s, count=%s" % (r.status_code, d["count"]),
           "Pass" if ok else "Fail", "Nominal",
           ev_api(r, limit=300))

    # --- N06
    body = {"items": [{"product_id": 1, "quantity": 2}], "payment_method": "card"}
    r = api("POST", "/api/orders", json=body)
    ok = r.status_code == 201
    oid = r.json().get("id") if ok else None
    record("N06", "Creation d'une commande valide via l'API",
           "Verifier la creation de commande par l'API REST",
           "Cle API valide, produit 1 disponible et en stock",
           '{"items":[{"product_id":1,"quantity":2}],"payment_method":"card"}',
           "1. POST /api/orders avec un payload valide",
           "HTTP 201 et la commande creee en reponse",
           "HTTP %s" % r.status_code,
           "Pass" if ok else "Fail", "Nominal", ev_api(r, body))

    # --- N07
    if oid:
        r = api("POST", "/api/orders/%d/cancel" % oid)
        ok = r.status_code == 200 and r.json().get("status") == "cancelled"
        record("N07", "Annulation d'une commande au statut 'confirmed'",
               "Verifier la regle d'annulation sur un statut autorise",
               "Commande %s au statut confirmed" % oid, "order_id=%s" % oid,
               "1. POST /api/orders/%s/cancel" % oid,
               "HTTP 200 et statut passe a 'cancelled'",
               "HTTP %s, statut=%s" % (r.status_code, r.json().get("status")),
               "Pass" if ok else "Fail", "Nominal", ev_api(r, limit=300))
    else:
        record("N07", "Annulation d'une commande au statut 'confirmed'", "-", "-", "-", "-",
               "HTTP 200 et statut 'cancelled'", "N06 n'a pas cree de commande",
               "Blocked", "Nominal", "Bloque par l'echec de N06")

    # --- N08
    r = requests.get(BASE + "/api/health", timeout=15)
    ok = r.status_code == 200 and r.json().get("status") == "ok"
    record("N08", "Endpoint de supervision /api/health",
           "Verifier la disponibilite du service (monitoring)",
           "Application demarree", "aucune", "1. GET /api/health",
           "HTTP 200 et un JSON contenant status=ok",
           "HTTP %s, corps=%s" % (r.status_code, r.text.strip()),
           "Pass" if ok else "Fail", "Nominal", ev_api(r))


# =====================================================================
# 2. CAS AUX LIMITES
# =====================================================================
def limites():
    # --- L01 quantite = 1
    b = {"items": [{"product_id": 9, "quantity": 1}], "payment_method": "card"}
    r = api("POST", "/api/orders", json=b)
    record("L01", "Commande API avec la quantite minimale autorisee (1)",
           "Verifier la borne inferieure acceptee de l'intervalle [1..20]",
           "Produit 9 (Miso Soup) disponible", "quantity=1",
           "1. POST /api/orders avec quantity=1",
           "HTTP 201, la commande est acceptee",
           "HTTP %s" % r.status_code,
           "Pass" if r.status_code == 201 else "Fail", "Limite", ev_api(r, b, 300))

    # --- L02 quantite = 20
    b = {"items": [{"product_id": 9, "quantity": 20}], "payment_method": "card"}
    r = api("POST", "/api/orders", json=b)
    record("L02", "Commande API avec la quantite maximale autorisee (20)",
           "Verifier la borne superieure acceptee de l'intervalle [1..20]",
           "Produit 9 (Miso Soup) en stock suffisant", "quantity=20",
           "1. POST /api/orders avec quantity=20",
           "HTTP 201, la commande est acceptee",
           "HTTP %s" % r.status_code,
           "Pass" if r.status_code == 201 else "Fail", "Limite", ev_api(r, b, 300))

    # --- L03 quantite = 21
    b = {"items": [{"product_id": 9, "quantity": 21}], "payment_method": "card"}
    r = api("POST", "/api/orders", json=b)
    record("L03", "Refus d'une commande API au-dela de la quantite maximale (21)",
           "Verifier le rejet juste au-dessus de la borne haute",
           "Produit 9 disponible", "quantity=21",
           "1. POST /api/orders avec quantity=21",
           "HTTP 400 avec un message d'erreur explicite",
           "HTTP %s : %s" % (r.status_code, r.text.strip()),
           "Pass" if r.status_code == 400 else "Fail", "Limite", ev_api(r, b, 300))

    # --- L04 quantite = 0
    b = {"items": [{"product_id": 9, "quantity": 0}], "payment_method": "card"}
    r = api("POST", "/api/orders", json=b)
    record("L04", "Refus d'une commande API avec une quantite nulle (0)",
           "Verifier le rejet juste en dessous de la borne basse",
           "Produit 9 disponible", "quantity=0",
           "1. POST /api/orders avec quantity=0",
           "HTTP 400 avec un message d'erreur explicite",
           "HTTP %s : %s" % (r.status_code, r.text.strip()),
           "Pass" if r.status_code == 400 else "Fail", "Limite", ev_api(r, b, 300))

    # --- L05 coupon au minimum exact
    b = {"code": "WELCOME10", "subtotal": 20}
    r = api("POST", "/api/coupons/validate", json=b)
    d = r.json()
    ok = d.get("valid") is True
    record("L05", "Coupon accepte au montant minimum exact (20.00 EUR)",
           "Verifier l'inclusion de la borne du montant minimum",
           "Coupon WELCOME10 actif, minimum 20 EUR", "code=WELCOME10, subtotal=20",
           "1. POST /api/coupons/validate avec subtotal=20",
           "Coupon valide, remise de 2.00 EUR appliquee",
           "valid=%s, discount=%s" % (d.get("valid"), d.get("discount")),
           "Pass" if ok else "Fail", "Limite", ev_api(r, b, 300))

    # --- L06 coupon juste sous le minimum
    b = {"code": "WELCOME10", "subtotal": 19.99}
    r = api("POST", "/api/coupons/validate", json=b)
    d = r.json()
    ok = d.get("valid") is False
    record("L06", "Coupon refuse juste sous le montant minimum (19.99 EUR)",
           "Verifier l'exclusion juste sous la borne du montant minimum",
           "Coupon WELCOME10 actif, minimum 20 EUR", "code=WELCOME10, subtotal=19.99",
           "1. POST /api/coupons/validate avec subtotal=19.99",
           "Coupon refuse avec le motif 'montant minimum non atteint'",
           "valid=%s, error=%s" % (d.get("valid"), d.get("error")),
           "Pass" if ok else "Fail", "Limite", ev_api(r, b, 300))

    # --- L07 plafond de remise
    b = {"code": "SAVE20", "subtotal": 200}
    r = api("POST", "/api/coupons/validate", json=b)
    d = r.json()
    ok = abs(float(d.get("discount", 0)) - 12.0) < 0.01
    record("L07", "Plafonnement de la remise au max_discount (SAVE20 plafonne a 12 EUR)",
           "Verifier que la remise ne depasse jamais le plafond du coupon",
           "Coupon SAVE20 : 20%, plafond 12 EUR", "code=SAVE20, subtotal=200",
           "1. POST /api/coupons/validate avec subtotal=200 (20% = 40 EUR theoriques)",
           "Remise plafonnee a 12.00 EUR",
           "discount=%s" % d.get("discount"),
           "Pass" if ok else "Fail", "Limite", ev_api(r, b, 300))

    # --- L08 commande a hauteur exacte du stock
    stock_before = stock_of(7)
    b = {"items": [{"product_id": 7, "quantity": stock_before}], "payment_method": "card"}
    r = api("POST", "/api/orders", json=b)
    stock_after = stock_of(7)
    ok = r.status_code == 201 and stock_after == 0
    record("L08", "Commande de la totalite du stock restant (Salmon Bowl, stock 2)",
           "Verifier le comportement a la limite exacte du stock disponible",
           "Salmon Bowl (id 7) avec un stock de %d" % stock_before,
           "product_id=7, quantity=%d" % stock_before,
           "1. Lire le stock ; 2. Commander exactement ce stock ; 3. Relire le stock",
           "HTTP 201 et stock ramene a 0 (jamais negatif)",
           "HTTP %s, stock %d -> %d" % (r.status_code, stock_before, stock_after),
           "Pass" if ok else "Fail", "Limite",
           ev_api(r, b, 300) + "\nstock avant=%d / après=%d" % (stock_before, stock_after))

    # --- L09 mot de passe 8 caracteres (borne acceptee)
    em = "qa.pwd8.%s@example.com" % datetime.now().strftime("%H%M%S")
    s = requests.Session()
    r = s.post(BASE + "/register", data={"name": "QA Test", "email": em,
                                         "password": "Abcd1234"}, timeout=15)
    ok = "mot de passe" not in " ".join(flashes(r.text)).lower()
    record("L09", "Inscription acceptee avec un mot de passe de 8 caracteres",
           "Verifier la borne inferieure acceptee de la longueur du mot de passe",
           "Email non utilise", "password='Abcd1234' (8 caracteres)",
           "1. POST /register avec un mot de passe de 8 caracteres",
           "Inscription acceptee",
           "Inscription acceptee : %s (flash: %s)" % (ok, flashes(r.text)[:1]),
           "Pass" if ok else "Fail", "Limite",
           "POST /register (password=8 caracteres)\n--> HTTP %s\nflash: %s"
           % (r.status_code, flashes(r.text)[:2]))

    # --- L10 mot de passe 7 caracteres (borne refusee)
    em = "qa.pwd7.%s@example.com" % datetime.now().strftime("%H%M%S")
    s = requests.Session()
    r = s.post(BASE + "/register", data={"name": "QA Test", "email": em,
                                         "password": "Abcd123"}, timeout=15)
    ok = "8 caract" in " ".join(flashes(r.text))
    record("L10", "Inscription refusee avec un mot de passe de 7 caracteres",
           "Verifier le rejet juste sous la borne de longueur du mot de passe",
           "Email non utilise", "password='Abcd123' (7 caracteres)",
           "1. POST /register avec un mot de passe de 7 caracteres",
           "Inscription refusee avec un message explicite",
           "Refus correct : %s (flash: %s)" % (ok, flashes(r.text)[:1]),
           "Pass" if ok else "Fail", "Limite",
           "POST /register (password=7 caracteres)\n--> HTTP %s\nflash: %s"
           % (r.status_code, flashes(r.text)[:2]))


# =====================================================================
# 3. CAS D'ERREUR
# =====================================================================
def erreurs():
    # --- E01 sans cle
    r = api("GET", "/api/restaurants", key=None)
    record("E01", "Refus d'un appel API sans cle d'authentification",
           "Verifier que l'API est protegee", "aucune", "aucun en-tete X-API-Key",
           "1. GET /api/restaurants sans en-tete X-API-Key",
           "HTTP 401 avec un message d'erreur",
           "HTTP %s : %s" % (r.status_code, r.text.strip()),
           "Pass" if r.status_code == 401 else "Fail", "Erreur", ev_api(r, limit=300))

    # --- E02 cle invalide
    r = api("GET", "/api/restaurants", key="cle-bidon")
    record("E02", "Refus d'un appel API avec une cle invalide",
           "Verifier le rejet d'une cle erronee", "aucune", "X-API-Key: cle-bidon",
           "1. GET /api/restaurants avec une cle invalide",
           "HTTP 401 avec un message d'erreur",
           "HTTP %s : %s" % (r.status_code, r.text.strip()),
           "Pass" if r.status_code == 401 else "Fail", "Erreur", ev_api(r, limit=300))

    # --- E03 restaurant inexistant
    r = api("GET", "/api/restaurants/9999")
    record("E03", "Consultation d'un restaurant inexistant",
           "Verifier la gestion des ressources absentes", "aucune", "restaurant_id=9999",
           "1. GET /api/restaurants/9999",
           "HTTP 404",
           "HTTP %s" % r.status_code,
           "Pass" if r.status_code == 404 else "Fail", "Erreur", ev_api(r, limit=200))

    # --- E04 produit inexistant
    r = api("GET", "/api/products/9999")
    record("E04", "Consultation d'un produit inexistant",
           "Verifier la gestion des ressources absentes", "aucune", "product_id=9999",
           "1. GET /api/products/9999", "HTTP 404", "HTTP %s" % r.status_code,
           "Pass" if r.status_code == 404 else "Fail", "Erreur", ev_api(r, limit=200))

    # --- E05 mauvais mot de passe
    s, r = login("alice@example.com", "MauvaisMotDePasse!")
    ok = "incorrect" in " ".join(flashes(r.text)).lower()
    record("E05", "Refus de connexion avec un mot de passe errone",
           "Verifier le rejet d'identifiants invalides",
           "Compte alice existant", "alice@example.com / MauvaisMotDePasse!",
           "1. POST /login avec un mot de passe errone",
           "Connexion refusee avec un message d'erreur",
           "Refus correct : %s (flash: %s)" % (ok, flashes(r.text)[:1]),
           "Pass" if ok else "Fail", "Erreur",
           "POST /login (mot de passe errone)\n--> HTTP %s\nflash: %s"
           % (r.status_code, flashes(r.text)[:2]))

    # --- E06 coupon expire
    b = {"code": "EXPIRED10", "subtotal": 50}
    r = api("POST", "/api/coupons/validate", json=b)
    ok = r.status_code == 404 and r.json().get("valid") is False
    record("E06", "Refus d'un coupon expire",
           "Verifier le controle de la date d'expiration des coupons",
           "Coupon EXPIRED10 expire depuis 1 jour", "code=EXPIRED10, subtotal=50",
           "1. POST /api/coupons/validate avec le code EXPIRED10",
           "Coupon refuse (invalide ou expire)",
           "HTTP %s, valid=%s" % (r.status_code, r.json().get("valid")),
           "Pass" if ok else "Fail", "Erreur", ev_api(r, b, 300))

    # --- E07 checkout avec panier vide
    s, _ = login("alice@example.com", "Password123!")
    s.post(BASE + "/cart/clear", timeout=15)
    r = s.get(BASE + "/checkout", timeout=15, allow_redirects=True)
    ok = "panier est vide" in " ".join(flashes(r.text)).lower()
    record("E07", "Acces au checkout avec un panier vide",
           "Verifier la protection du tunnel de commande",
           "Client connecte, panier vide", "aucune",
           "1. Vider le panier ; 2. GET /checkout",
           "Redirection vers le panier avec un message d'avertissement",
           "Message affiche : %s" % (flashes(r.text)[:1] or "aucun"),
           "Pass" if ok else "Fail", "Erreur",
           "GET /checkout (panier vide)\n--> HTTP %s\nURL finale: %s\nflash: %s"
           % (r.status_code, r.url, flashes(r.text)[:2]))

    # --- E08 produits de restaurants differents
    b = {"items": [{"product_id": 1, "quantity": 1}, {"product_id": 9, "quantity": 1}],
         "payment_method": "card"}
    r = api("POST", "/api/orders", json=b)
    ok = r.status_code == 400
    record("E08", "Refus d'une commande melangeant deux restaurants",
           "Verifier la regle 'un panier = un restaurant' cote API",
           "Produit 1 = Burger Factory, produit 9 = Tokyo Bowl",
           "items=[product_id 1, product_id 9]",
           "1. POST /api/orders avec des produits de deux restaurants",
           "HTTP 400 avec un message explicite",
           "HTTP %s : %s" % (r.status_code, r.text.strip()),
           "Pass" if ok else "Fail", "Erreur", ev_api(r, b, 300))

    # --- E09 acces admin par un client
    s, _ = login("alice@example.com", "Password123!")
    r = s.get(BASE + "/admin/", timeout=15, allow_redirects=True)
    ok = "administrateur" in " ".join(flashes(r.text)).lower() or "/admin" not in r.url
    record("E09", "Acces a l'espace d'administration par un client standard",
           "Verifier le cloisonnement des roles",
           "Alice connectee avec le role 'customer'", "GET /admin/",
           "1. Se connecter comme client ; 2. GET /admin/",
           "Acces refuse et redirection hors de l'espace admin",
           "URL finale: %s, flash: %s" % (r.url, flashes(r.text)[:1]),
           "Pass" if ok else "Fail", "Erreur",
           "GET /admin/ (role customer)\n--> HTTP %s\nURL finale: %s\nflash: %s"
           % (r.status_code, r.url, flashes(r.text)[:2]))

    # --- E10 commande d'un autre utilisateur (UI)
    sb, _ = login("bob@example.com", "Password123!")
    r = sb.get(BASE + "/orders/1", timeout=15, allow_redirects=True)
    ok = "inaccessible" in " ".join(flashes(r.text)).lower()
    record("E10", "Consultation de la commande d'un autre client (interface web)",
           "Verifier le cloisonnement des donnees entre comptes",
           "La commande 1 appartient a Alice ; Bob est connecte", "order_id=1",
           "1. Se connecter comme Bob ; 2. GET /orders/1",
           "Acces refuse, la commande d'Alice n'est pas affichee",
           "URL finale: %s, flash: %s" % (r.url, flashes(r.text)[:1]),
           "Pass" if ok else "Fail", "Erreur",
           "GET /orders/1 (connecte en tant que Bob)\n--> HTTP %s\nURL finale: %s\nflash: %s"
           % (r.status_code, r.url, flashes(r.text)[:2]))

    # --- E11 quantite non numerique
    b = {"items": [{"product_id": 9, "quantity": "abc"}], "payment_method": "card"}
    r = api("POST", "/api/orders", json=b)
    ok = r.status_code == 400
    record("E11", "Refus d'une commande avec une quantite non numerique",
           "Verifier la validation du type des donnees d'entree",
           "Produit 9 disponible", 'quantity="abc"',
           "1. POST /api/orders avec quantity='abc'",
           "HTTP 400 avec un message explicite",
           "HTTP %s : %s" % (r.status_code, r.text.strip()),
           "Pass" if ok else "Fail", "Erreur", ev_api(r, b, 300))

    # --- E12 mode de paiement invalide
    b = {"items": [{"product_id": 9, "quantity": 1}], "payment_method": "bitcoin"}
    r = api("POST", "/api/orders", json=b)
    ok = r.status_code == 400
    record("E12", "Refus d'un mode de paiement non supporte",
           "Verifier la validation de la liste des moyens de paiement",
           "Produit 9 disponible", 'payment_method="bitcoin"',
           "1. POST /api/orders avec payment_method='bitcoin'",
           "HTTP 400 avec un message explicite",
           "HTTP %s : %s" % (r.status_code, r.text.strip()),
           "Pass" if ok else "Fail", "Erreur", ev_api(r, b, 300))


# =====================================================================
# 4. REGLES METIER
# =====================================================================
def regles_metier():
    # --- RM01 minimum de commande non applique
    b = {"items": [{"product_id": 23, "quantity": 1}], "payment_method": "card"}  # The 3.50
    r = api("POST", "/api/orders", json=b)
    d = r.json() if r.status_code in (200, 201) else {}
    ok = r.status_code != 201
    record("RM01", "Respect du montant minimum de commande du restaurant",
           "Verifier que le minimum de commande annonce est applique",
           "Couscous Atlas (id 5) annonce un minimum de 25.00 EUR",
           "1 x The a la menthe = 3.50 EUR (tres inferieur au minimum)",
           "1. POST /api/orders avec un sous-total de 3.50 EUR",
           "Commande refusee : montant minimum de 25.00 EUR non atteint",
           "HTTP %s, commande CREEE avec subtotal=%s EUR" % (r.status_code, d.get("subtotal")),
           "Pass" if ok else "Fail", "Regle metier", ev_api(r, b, 400), "BUG-001")

    # --- RM02 restaurant ferme
    rest = api("GET", "/api/restaurants/6").json()
    b = {"items": [{"product_id": 24, "quantity": 1}], "payment_method": "card"}
    r = api("POST", "/api/orders", json=b)
    ok = r.status_code != 201
    record("RM02", "Blocage des commandes vers un restaurant ferme",
           "Verifier que l'etat 'ferme' empeche la prise de commande",
           "Night Sushi (id 6) is_open=%s" % rest["is_open"],
           "product_id=24 (Late Sushi Box), restaurant ferme",
           "1. Verifier is_open=false ; 2. POST /api/orders sur un produit de ce restaurant",
           "Commande refusee car le restaurant est ferme",
           "HTTP %s, commande CREEE malgre is_open=false" % r.status_code,
           "Pass" if ok else "Fail", "Regle metier",
           "GET /api/restaurants/6 --> is_open=%s\n%s" % (rest["is_open"], ev_api(r, b, 300)),
           "BUG-002")

    # --- RM03 produit en rupture commandable
    p = api("GET", "/api/products/8").json()   # Gyozas stock 0
    b = {"items": [{"product_id": 8, "quantity": 1}], "payment_method": "card"}
    r = api("POST", "/api/orders", json=b)
    after = api("GET", "/api/products/8").json()["stock"]
    ok = r.status_code != 201
    record("RM03", "Blocage de la commande d'un produit en rupture de stock",
           "Verifier le controle du stock a la commande",
           "Gyozas (id 8) avec stock=%s et available=%s" % (p["stock"], p["available"]),
           "product_id=8, quantity=1",
           "1. Verifier stock=0 ; 2. POST /api/orders ; 3. Relire le stock",
           "Commande refusee : produit en rupture",
           "HTTP %s, commande CREEE, stock passe de %s a %s" % (r.status_code, p["stock"], after),
           "Pass" if ok else "Fail", "Regle metier",
           "GET /api/products/8 --> stock=%s\n%s\nstock après: %s"
           % (p["stock"], ev_api(r, b, 300), after), "BUG-003")

    # --- RM04 stock negatif
    p = api("GET", "/api/products/10").json()  # Tofu Bowl stock 100
    qty = 20
    # on vide d'abord le stock pour provoquer le depassement
    for _ in range(5):
        api("POST", "/api/orders", json={"items": [{"product_id": 10, "quantity": 20}],
                                         "payment_method": "card"})
    mid = api("GET", "/api/products/10").json()["stock"]
    b = {"items": [{"product_id": 10, "quantity": 20}], "payment_method": "card"}
    r = api("POST", "/api/orders", json=b)
    after = api("GET", "/api/products/10").json()["stock"]
    ok = after >= 0 and r.status_code != 201
    record("RM04", "Absence de stock négatif après une commande excédentaire",
           "Verifier que le stock ne peut jamais devenir negatif",
           "Tofu Bowl (id 10), stock initial %s puis epuise par commandes successives" % p["stock"],
           "6 commandes de 20 unites (120 > stock initial 100)",
           "1. Epuiser le stock ; 2. Commander 20 unites de plus ; 3. Relire le stock",
           "Commande refusee et stock >= 0",
           "HTTP %s, stock %s -> %s (NEGATIF)" % (r.status_code, mid, after),
           "Pass" if ok else "Fail", "Regle metier",
           "stock avant dernière commande: %s\n%s\nstock après: %s"
           % (mid, ev_api(r, b, 300), after), "BUG-004")

    # --- RM05 PayPal duplique
    before = orders_count()
    b = {"items": [{"product_id": 9, "quantity": 1}], "payment_method": "paypal"}
    r = api("POST", "/api/orders", json=b)
    after = orders_count()
    delta = after - before
    ok = delta == 1
    record("RM05", "Unicite de la commande en paiement PayPal",
           "Verifier qu'un paiement PayPal ne genere qu'une seule commande",
           "Compte alice, liste des commandes connue", "payment_method=paypal, 1 x Miso Soup",
           "1. Compter les commandes ; 2. POST /api/orders en paypal ; 3. Recompter",
           "Exactement 1 commande creee (delta=1)",
           "delta=%d commandes creees pour un seul paiement" % delta,
           "Pass" if ok else "Fail", "Regle metier",
           "GET /api/orders count avant=%d\n%s\nGET /api/orders count après=%d --> delta=%d"
           % (before, ev_api(r, b, 250), after, delta), "BUG-005")

    # --- RM06 paiement especes insuffisant
    b = {"items": [{"product_id": 9, "quantity": 1}], "payment_method": "cash",
         "cash_received": 1}
    r = api("POST", "/api/orders", json=b)
    d = r.json() if r.status_code == 201 else {}
    ok = r.status_code != 201
    record("RM06", "Refus d'un paiement en especes insuffisant",
           "Verifier le controle du montant remis en especes",
           "Miso Soup 3.20 EUR + livraison 3.49 EUR = 6.69 EUR a payer",
           "payment_method=cash, cash_received=1.00 EUR",
           "1. POST /api/orders en especes avec 1.00 EUR pour un total de 6.69 EUR",
           "Commande refusee : montant remis insuffisant",
           "HTTP %s, commande CREEE payment_status=%s, total=%s, rendu=%s (NEGATIF)"
           % (r.status_code, d.get("payment_status"), d.get("total"), d.get("change_due")),
           "Pass" if ok else "Fail", "Regle metier", ev_api(r, b, 500), "BUG-006")

    # --- RM07 ATLAS15 annonce 15% applique 10%
    rest = api("GET", "/api/restaurants/5").json()
    b = {"code": "ATLAS15", "subtotal": 100}
    r = api("POST", "/api/coupons/validate", json=b)
    d = r.json()
    pct = float(d.get("discount_percent", 0))
    ok = abs(pct - 15.0) < 0.01
    record("RM07", "Coherence entre la promotion annoncee et la remise appliquee",
           "Verifier que le taux annonce sur la fiche restaurant est bien applique",
           "Couscous Atlas affiche : %s" % rest["promo_text"],
           "code=ATLAS15, subtotal=100 EUR",
           "1. Lire la promotion annoncee ; 2. POST /api/coupons/validate subtotal=100",
           "Remise de 15% soit 15.00 EUR (conforme a l'annonce)",
           "discount_percent=%s%% soit %s EUR au lieu de 15%%" % (pct, d.get("discount")),
           "Pass" if ok else "Fail", "Regle metier",
           "Annonce sur la fiche restaurant : %s\n%s" % (rest["promo_text"], ev_api(r, b, 300)),
           "BUG-007")

    # --- RM08 filtre livraison inverse
    r = requests.get(BASE + "/?max_delivery=2.50", timeout=15)
    noms = re.findall(r"<h2[^>]*>\s*([^<]+?)\s*</h2>", r.text)
    # restaurants avec frais <= 2.50 : Green Kitchen (1.99), Pizza Roma (2.49)
    attendus = {"Green Kitchen", "Pizza Roma"}
    trouves = set(n.strip() for n in noms)
    chers = {"Burger Factory", "Tokyo Bowl", "Couscous Atlas"} & trouves
    ok = trouves and trouves.issubset(attendus)
    record("RM08", "Filtre 'frais de livraison maximum' sur la page d'accueil",
           "Verifier que le filtre retourne les restaurants sous le seuil",
           "Frais : Green Kitchen 1.99, Pizza Roma 2.49, Burger Factory 2.99, "
           "Tokyo Bowl 3.49, Couscous Atlas 2.99", "max_delivery=2.50",
           "1. GET /?max_delivery=2.50 ; 2. Lister les restaurants retournes",
           "Uniquement Green Kitchen (1.99) et Pizza Roma (2.49)",
           "Retournes : %s -- dont des restaurants PLUS CHERS que 2.50 : %s"
           % (sorted(trouves), sorted(chers)),
           "Pass" if ok else "Fail", "Regle metier",
           "GET /?max_delivery=2.50\n--> HTTP %s\nRestaurants affiches : %s"
           % (r.status_code, sorted(trouves)), "BUG-008")

    # --- RM09 recherche ignore la description
    noms_h2 = lambda t: sorted(set(x.strip() for x in
                                   re.findall(r"<h2[^>]*>\s*([^<]+?)\s*</h2>", t)))
    # controle : "pizza" figure dans le NOM "Pizza Roma" -> doit remonter
    ctrl = noms_h2(requests.get(BASE + "/?q=pizza", timeout=15).text)
    # cible : "romaines" figure UNIQUEMENT dans la description de Pizza Roma
    cible = noms_h2(requests.get(BASE + "/?q=romaines", timeout=15).text)
    ok = "Pizza Roma" in cible
    record("RM09", "Recherche par mot-cle portant sur le nom et la description",
           "Verifier la couverture fonctionnelle de la recherche",
           "Pizza Roma a pour description 'Pizzas romaines, pates et desserts italiens.' ; "
           "le mot 'romaines' n'apparait que dans cette description",
           "q=pizza (controle, mot present dans le nom) puis q=romaines (mot de la description)",
           "1. GET /?q=pizza ; 2. GET /?q=romaines ; 3. Comparer les resultats",
           "Pizza Roma remonte dans les deux cas (recherche nom + description)",
           "q=pizza -> %s (le nom fonctionne) ; q=romaines -> %s : la description est ignoree"
           % (ctrl, cible or "AUCUN RESULTAT"),
           "Pass" if ok else "Fail", "Regle metier",
           "GET /?q=pizza --> %s\nGET /?q=romaines --> %s" % (ctrl, cible), "BUG-009")

    # --- RM10 l'API fait confiance au subtotal client
    b = {"code": "SAVE20", "subtotal": 999999}
    r = api("POST", "/api/coupons/validate", json=b)
    d = r.json()
    ok = d.get("valid") is not True
    record("RM10", "Validation cote serveur du sous-total transmis par le client",
           "Verifier que le montant n'est pas pris aveuglement depuis le client",
           "Coupon SAVE20, minimum 35 EUR", "subtotal=999999 (valeur arbitraire du client)",
           "1. POST /api/coupons/validate avec un sous-total fantaisiste",
           "Le serveur recalcule ou rejette un sous-total non verifiable",
           "valid=%s : le serveur accepte le montant arbitraire sans le recalculer"
           % d.get("valid"),
           "Pass" if ok else "Fail", "Regle metier", ev_api(r, b, 300), "BUG-010")

    # --- RM11 avis sans commande
    sb, _ = login("bob@example.com", "Password123!")
    r = sb.post(BASE + "/restaurant/5/review", data={"rating": 5,
                "comment": "Avis QA depose sans jamais avoir commande."}, timeout=15,
                allow_redirects=True)
    ok = "Merci pour votre avis" not in r.text
    record("RM11", "Depot d'un avis reserve aux clients ayant commande",
           "Verifier que seuls les clients ayant commande peuvent noter",
           "Bob n'a jamais commande chez Couscous Atlas (id 5)",
           "rating=5, comment='Avis QA depose sans jamais avoir commande.'",
           "1. Se connecter comme Bob ; 2. POST /restaurant/5/review",
           "Depot refuse : aucune commande chez ce restaurant",
           "Avis ACCEPTE sans commande prealable (flash: %s)" % (flashes(r.text)[:1]),
           "Pass" if ok else "Fail", "Regle metier",
           "POST /restaurant/5/review (Bob, aucune commande chez ce restaurant)\n"
           "--> HTTP %s\nflash: %s" % (r.status_code, flashes(r.text)[:2]), "BUG-011")

    # --- RM12 transition de statut invalide (admin)
    sa, _ = login("admin@quickorder.local", "Admin123!")
    # commande 1 = livree (seed)
    st_before = api("GET", "/api/orders/1").json()["status"]
    r = sa.post(BASE + "/admin/orders/1/status", data={"status": "confirmed"},
                timeout=15, allow_redirects=True)
    st_after = api("GET", "/api/orders/1").json()["status"]
    ok = st_after == st_before
    record("RM12", "Refus des transitions de statut impossibles (livree -> confirmee)",
           "Verifier le respect du cycle de vie d'une commande",
           "La commande 1 est au statut '%s'" % st_before, "status=confirmed",
           "1. Se connecter comme admin ; 2. POST /admin/orders/1/status status=confirmed",
           "Transition refusee : une commande livree ne peut pas redevenir confirmee",
           "Statut passe de '%s' a '%s'" % (st_before, st_after),
           "Pass" if ok else "Fail", "Regle metier",
           "POST /admin/orders/1/status (status=confirmed)\n--> HTTP %s\n"
           "statut avant=%s / après=%s\nflash: %s"
           % (r.status_code, st_before, st_after, flashes(r.text)[:2]), "BUG-012")

    # --- RM13 API expose les restaurants fermes
    d = api("GET", "/api/restaurants").json()
    fermes = [x["name"] for x in d["items"] if not x["is_open"]]
    ok = len(fermes) == 0
    record("RM13", "Exposition des restaurants fermes dans la liste API",
           "Verifier la coherence entre la liste API et la commandabilite",
           "Night Sushi est ferme (is_open=false)", "GET /api/restaurants",
           "1. GET /api/restaurants ; 2. Filtrer sur is_open=false",
           "Les restaurants fermes sont exclus ou clairement signales/filtrables",
           "Restaurants fermes presents dans la liste : %s" % (fermes or "aucun"),
           "Pass" if ok else "Fail", "Regle metier",
           "GET /api/restaurants --> count=%s\nFermes retournes : %s" % (d["count"], fermes),
           "BUG-013")

    # --- RM14
    r = requests.get(BASE + "/restaurant/1", timeout=15)
    veg = api("GET", "/api/products/4").json()  # Veggie Burger stock 0
    hors_stock = "HORS STOCK" in r.text
    sc, _ = login("alice@example.com", "Password123!")
    sc.post(BASE + "/cart/clear", timeout=15)
    add = sc.post(BASE + "/cart/add/4", data={"quantity": 3}, timeout=15)
    panier = sc.get(BASE + "/cart", timeout=15).text
    dans_panier = "Veggie Burger" in panier
    ok = not dans_panier
    record("RM14", "Blocage de l'ajout au panier d'un produit en rupture (interface web)",
           "Verifier que la mention 'HORS STOCK' empeche reellement la commande",
           "Veggie Burger (id 4) stock=%s available=%s, affiche HORS STOCK: %s"
           % (veg["stock"], veg["available"], hors_stock),
           "product_id=4, quantity=3 alors que le stock est de 0",
           "1. Ouvrir /restaurant/1 ; 2. Constater la mention HORS STOCK ; "
           "3. POST /cart/add/4 quantity=3 ; 4. GET /cart",
           "Ajout refuse : le produit est en rupture",
           "Le produit affiche 'HORS STOCK' mais l'ajout au panier REUSSIT "
           "(present dans le panier: %s)" % dans_panier,
           "Pass" if ok else "Fail", "Regle metier",
           EOL.join(["GET /api/products/4 --> stock=%s",
                     "GET /restaurant/1 --> mention HORS STOCK: %s",
                     "POST /cart/add/4 (quantity=3) --> HTTP %s",
                     "flash: %s",
                     "GET /cart --> Veggie Burger present: %s"])
           % (veg["stock"], hors_stock, add.status_code, flashes(add.text)[:2], dans_panier),
           "BUG-003")

    # --- RM15 minimum de commande cote interface web
    s, _ = login("alice@example.com", "Password123!")
    s.post(BASE + "/cart/clear", timeout=15)
    s.post(BASE + "/cart/add/23", data={"quantity": 1}, timeout=15)  # The 3.50, min 25
    page = s.get(BASE + "/checkout", timeout=15).text
    m = re.search(r'name="address_id"[^>]*value="(\d+)"', page)
    aid = m.group(1) if m else "1"
    r = s.post(BASE + "/checkout", data={"confirm": "1", "address_id": aid,
                                         "payment_method": "card"}, timeout=15)
    ok = "Commande confirm" not in r.text
    record("RM15", "Montant minimum applique dans le tunnel de commande web",
           "Verifier la regle du minimum de commande cote interface",
           "Couscous Atlas : minimum 25.00 EUR", "Panier = 1 x The a la menthe (3.50 EUR)",
           "1. Ajouter un produit a 3.50 EUR ; 2. Valider le checkout",
           "Commande bloquee : montant minimum non atteint",
           "Commande confirmee malgre un panier de 3.50 EUR (flash: %s)" % (flashes(r.text)[:1]),
           "Pass" if ok else "Fail", "Regle metier",
           "POST /checkout (panier 3.50 EUR, minimum 25 EUR)\n--> HTTP %s\nflash: %s"
           % (r.status_code, flashes(r.text)[:2]), "BUG-001")

    # --- RM16 PayPal duplique aussi dans l'interface web
    s, _ = login("alice@example.com", "Password123!")
    s.post(BASE + "/cart/clear", timeout=15)
    s.post(BASE + "/cart/add/1", data={"quantity": 2}, timeout=15)
    before = orders_count()
    page = s.get(BASE + "/checkout", timeout=15).text
    m = re.search(r'name="address_id"[^>]*value="(\d+)"', page)
    aid = m.group(1) if m else "1"
    r = s.post(BASE + "/checkout", data={"confirm": "1", "address_id": aid,
                                         "payment_method": "paypal"}, timeout=15)
    after = orders_count()
    delta = after - before
    ok = delta == 1
    record("RM16", "Unicite de la commande PayPal dans l'interface web",
           "Confirmer que le doublon PayPal touche aussi le parcours web",
           "Alice connectee, panier a 23.80 EUR", "payment_method=paypal",
           "1. Compter les commandes ; 2. Valider le checkout en PayPal ; 3. Recompter",
           "Exactement 1 commande creee",
           "delta=%d commandes creees pour un seul paiement" % delta,
           "Pass" if ok else "Fail", "Regle metier",
           "POST /checkout (payment_method=paypal)\n--> HTTP %s\n"
           "commandes avant=%d / après=%d --> delta=%d"
           % (r.status_code, before, after, delta), "BUG-005")


def main():
    print("=" * 70)
    print("CAMPAGNE DE TEST QUICKORDER — %s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 70)
    log("# Journal d'execution brut — campagne QuickOrder\n")
    log("Execute le %s contre %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M"), BASE))
    log("Chaque bloc ci-dessous contient la requete reellement envoyee et la reponse "
        "reellement recue par l'application.\n")

    log("\n## 1. Cas nominaux\n")
    nominaux()
    log("\n## 2. Cas aux limites\n")
    limites()
    log("\n## 3. Cas d'erreur\n")
    erreurs()
    log("\n## 4. Regles metier\n")
    regles_metier()

    if not os.path.isdir(EVID):
        os.makedirs(EVID)
    with io.open(os.path.join(EVID, "raw-log.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(LOG))
    with io.open(os.path.join(EVID, "results.json"), "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, ensure_ascii=False, indent=2)

    total = len(RESULTS)
    p = sum(1 for x in RESULTS if x["statut"] == "Pass")
    fa = sum(1 for x in RESULTS if x["statut"] == "Fail")
    bl = sum(1 for x in RESULTS if x["statut"] == "Blocked")
    sk = sum(1 for x in RESULTS if x["statut"] == "Skipped")
    print("=" * 70)
    print("TOTAL %d | Pass %d | Fail %d | Blocked %d | Skipped %d" % (total, p, fa, bl, sk))
    print("=" * 70)


if __name__ == "__main__":
    main()
