# -*- coding: utf-8 -*-
"""Genere les fiches d'anomalie a partir des preuves de la campagne."""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(ROOT, "docs", "evidence")
OUT = os.path.join(ROOT, "docs", "bug-reports")

results = {r["id"]: r for r in json.load(io.open(os.path.join(EVID, "results.json"),
                                                 encoding="utf-8"))}

BUGS = [
    dict(
        id="BUG-005", slug="paypal-double-commande",
        titre="Un paiement PayPal cree systematiquement deux commandes identiques",
        severite="Bloquante", priorite="P0 — correction avant toute mise en production",
        risque="R1", cas=["RM05", "RM16"],
        contexte=(
            "Le client choisit PayPal comme moyen de paiement, sur l'interface web "
            "comme via l'API. L'application enregistre deux commandes distinctes pour "
            "un seul acte d'achat. Le client est donc facture deux fois et le "
            "restaurant prepare deux fois la commande."),
        preconditions=[
            "Application demarree, base reinitialisee",
            "Compte client alice@example.com connecte (ou cle API valide)",
            "Un panier valide contenant au moins un produit",
        ],
        etapes=[
            "Relever le nombre de commandes du client : GET /api/orders -> champ count",
            "Passer une commande unique en choisissant payment_method=paypal",
            "Relever a nouveau le nombre de commandes : GET /api/orders",
        ],
        attendu=("Une seule commande est creee. Le compteur augmente de 1."),
        obtenu=("Deux commandes sont creees pour un seul paiement. Le compteur augmente "
                "de 2. Le defaut est reproduit a l'identique sur les deux canaux : "
                "API (RM05) et interface web (RM16)."),
        impact=(
            "Double facturation du client et double preparation par le restaurant. "
            "C'est l'anomalie la plus couteuse de l'audit : elle genere un litige "
            "financier a chaque commande PayPal, sans aucune action particuliere du "
            "client. Elle justifie a elle seule un No-Go."),
    ),
    dict(
        id="BUG-002", slug="restaurant-ferme",
        titre="Un restaurant ferme accepte les commandes",
        severite="Critique", priorite="P1",
        risque="R2", cas=["RM02"],
        contexte=(
            "Le restaurant Night Sushi est explicitement ferme (is_open=false) et "
            "affiche la mention FERME sur la page d'accueil. Il accepte pourtant les "
            "commandes : l'etat d'ouverture est affiche mais jamais controle au moment "
            "de l'engagement."),
        preconditions=[
            "Night Sushi (restaurant id 6) a is_open=false",
            "Le produit Late Sushi Box (id 24) appartient a ce restaurant",
        ],
        etapes=[
            "Verifier l'etat du restaurant : GET /api/restaurants/6 -> is_open=false",
            "Commander un produit de ce restaurant : POST /api/orders avec product_id=24",
        ],
        attendu=("La commande est refusee avec un message indiquant que le restaurant "
                 "est ferme."),
        obtenu=("HTTP 201 : la commande est creee et marquee payee, alors que le "
                "restaurant est ferme."),
        impact=(
            "Le client paie une commande qui ne sera jamais preparee ni livree. "
            "Remboursement systematique, perte de confiance et cout de traitement du "
            "litige."),
    ),
    dict(
        id="BUG-003", slug="produit-rupture-commandable",
        titre="Un produit en rupture de stock reste commandable",
        severite="Critique", priorite="P1",
        risque="R2", cas=["RM03", "RM14"],
        contexte=(
            "Les produits dont le stock est a 0 affichent bien la mention HORS STOCK "
            "sur la fiche restaurant, mais le bouton Ajouter reste actif et l'ajout au "
            "panier aboutit. La commande va ensuite jusqu'au paiement. L'information "
            "est donc purement decorative."),
        preconditions=[
            "Veggie Burger (produit id 4) : stock=0, available=true",
            "Gyozas (produit id 8) : stock=0, available=true",
        ],
        etapes=[
            "Ouvrir la fiche du restaurant : GET /restaurant/1",
            "Constater la mention HORS STOCK sur le Veggie Burger",
            "Ajouter malgre tout le produit au panier : POST /cart/add/4 quantity=3",
            "Consulter le panier : GET /cart",
            "Variante API : POST /api/orders avec product_id=8 (stock 0)",
        ],
        attendu=("L'ajout au panier est refuse et la commande est rejetee : le produit "
                 "est en rupture."),
        obtenu=("Le produit est ajoute au panier malgre la mention HORS STOCK. Cote API, "
                "la commande est acceptee (HTTP 201) et le stock passe de 0 a -1."),
        impact=(
            "Commande impossible a honorer, et stock qui devient incoherent. "
            "L'affichage HORS STOCK donne une fausse impression de controle : le "
            "client constate le probleme apres avoir paye."),
    ),
    dict(
        id="BUG-006", slug="paiement-especes-insuffisant",
        titre="Un paiement en especes inferieur au montant du est accepte et marque paye",
        severite="Critique", priorite="P1",
        risque="R3", cas=["RM06"],
        contexte=(
            "Lors d'un paiement en especes, le montant annonce par le client n'est pas "
            "compare au total a payer. La commande est enregistree comme payee et le "
            "montant a rendre devient negatif."),
        preconditions=[
            "Un produit commandable : Miso Soup (id 9) a 3,20 EUR",
            "Frais de livraison Tokyo Bowl : 3,49 EUR, soit un total de 6,69 EUR",
        ],
        etapes=[
            "Passer une commande avec payment_method=cash et cash_received=1",
            "Observer les champs payment_status, total et change_due de la reponse",
        ],
        attendu=("La commande est refusee : le montant remis (1,00 EUR) est inferieur "
                 "au total du (6,69 EUR)."),
        obtenu=("HTTP 201 : la commande est creee avec payment_status=paid, "
                "total=6.69 et change_due=-5.69. Le systeme annonce un rendu de monnaie "
                "negatif, ce qui n'a aucun sens comptable."),
        impact=(
            "Perte financiere directe a chaque occurrence : la commande est preparee et "
            "livree alors qu'elle n'est pas payee. Un montant a rendre negatif indique "
            "en outre une absence totale de controle de coherence comptable."),
    ),
    dict(
        id="BUG-010", slug="subtotal-client-non-verifie",
        titre="L'API de validation des coupons fait confiance au montant transmis par le client",
        severite="Critique", priorite="P1",
        risque="R4", cas=["RM10"],
        contexte=(
            "L'endpoint POST /api/coupons/validate calcule la remise a partir du "
            "sous-total envoye dans la requete, sans le recalculer ni le verifier "
            "cote serveur. N'importe quel appelant peut donc declarer le montant de "
            "son choix."),
        preconditions=[
            "Coupon SAVE20 actif : 20 %, montant minimum 35 EUR, plafond 12 EUR",
            "Cle API valide",
        ],
        etapes=[
            "Envoyer POST /api/coupons/validate avec un sous-total arbitraire : "
            "{\"code\": \"SAVE20\", \"subtotal\": 999999}",
            "Observer la reponse",
        ],
        attendu=("Le serveur recalcule le sous-total a partir du panier reel, ou refuse "
                 "un montant qu'il ne peut pas verifier."),
        obtenu=("Le serveur repond valid=true et calcule la remise sur le montant "
                "fantaisiste fourni par le client, sans aucune verification."),
        impact=(
            "Un client peut franchir artificiellement le seuil minimum d'un coupon et "
            "obtenir une remise a laquelle il n'a pas droit. C'est une faille de "
            "logique metier exploitable directement depuis l'API, sans outil "
            "particulier."),
    ),
    dict(
        id="BUG-001", slug="minimum-commande-non-applique",
        titre="Le montant minimum de commande annonce par le restaurant n'est jamais applique",
        severite="Majeure", priorite="P1",
        risque="R7", cas=["RM01", "RM15"],
        contexte=(
            "Chaque restaurant affiche un montant minimum de commande sur sa fiche. "
            "Ce montant est presente au client mais n'est controle ni dans le tunnel "
            "web, ni par l'API."),
        preconditions=[
            "Couscous Atlas (restaurant id 5) annonce un minimum de 25,00 EUR",
            "The a la menthe (produit id 23) a 3,50 EUR",
        ],
        etapes=[
            "Constater le minimum affiche sur la fiche du restaurant",
            "Interface web : ajouter 1 The a la menthe au panier puis valider le checkout",
            "API : POST /api/orders avec product_id=23, quantity=1",
        ],
        attendu=("La commande est bloquee tant que le sous-total n'atteint pas "
                 "25,00 EUR."),
        obtenu=("La commande de 3,50 EUR est confirmee sur les deux canaux. "
                "Cote web, le message Commande confirmee ! s'affiche normalement."),
        impact=(
            "Le restaurant recoit des commandes non rentables qu'il est contractuellement "
            "cense pouvoir refuser. La regle affichee au client n'a aucune valeur, ce "
            "qui expose a un litige avec les restaurants partenaires."),
    ),
    dict(
        id="BUG-004", slug="stock-negatif",
        titre="Le stock devient negatif apres une commande superieure aux quantites disponibles",
        severite="Majeure", priorite="P1",
        risque="R6", cas=["RM04"],
        contexte=(
            "Le stock est decremente sans verification prealable de sa valeur. Il peut "
            "donc descendre en dessous de zero et n'a plus aucune signification."),
        preconditions=[
            "Tofu Bowl (produit id 10), stock initial de 100 unites",
        ],
        etapes=[
            "Epuiser le stock par commandes successives de 20 unites",
            "Verifier que le stock est a 0 : GET /api/products/10",
            "Passer une commande supplementaire de 20 unites",
            "Relire le stock",
        ],
        attendu=("La commande est refusee et le stock reste superieur ou egal a 0."),
        obtenu=("HTTP 201 : la commande est acceptee et le stock passe de 0 a -20."),
        impact=(
            "Les donnees de stock ne sont plus exploitables : ni pour l'affichage "
            "client, ni pour le reapprovisionnement, ni pour le pilotage. Le defaut "
            "s'aggrave a chaque commande."),
    ),
    dict(
        id="BUG-007", slug="coupon-atlas15-taux-incoherent",
        titre="La promotion ATLAS15 est annoncee a 15 % mais n'applique que 10 %",
        severite="Majeure", priorite="P2",
        risque="R5", cas=["RM07"],
        contexte=(
            "La fiche du restaurant Couscous Atlas annonce explicitement 15 % de "
            "reduction avec le code ATLAS15, et la page d'accueil relaie la meme "
            "promotion. Le coupon reellement enregistre applique 10 %."),
        preconditions=[
            "Couscous Atlas affiche : Code ATLAS15 annonce comme -15% sur ce restaurant",
            "La fiche restaurant affiche : utilisez le code ATLAS15 pour obtenir 15 % de reduction",
        ],
        etapes=[
            "Lire la promotion annoncee sur la fiche du restaurant",
            "Valider le coupon : POST /api/coupons/validate avec code=ATLAS15 et subtotal=100",
            "Comparer le taux applique au taux annonce",
        ],
        attendu=("Une remise de 15 %, soit 15,00 EUR pour un sous-total de 100 EUR, "
                 "conformement a l'annonce."),
        obtenu=("discount_percent=10.0 et une remise de 10,00 EUR, soit 5,00 EUR de "
                "moins que le montant annonce au client."),
        impact=(
            "Ecart entre la promotion commerciale affichee et la remise reellement "
            "accordee. Au-dela de la perte de confiance, cela constitue une pratique "
            "commerciale trompeuse susceptible d'etre contestee."),
    ),
    dict(
        id="BUG-011", slug="avis-sans-commande",
        titre="Un client peut noter un restaurant ou il n'a jamais commande",
        severite="Majeure", priorite="P2",
        risque="R8", cas=["RM11"],
        contexte=(
            "Le depot d'un avis ne verifie pas que l'auteur a deja commande chez le "
            "restaurant concerne. Toute personne disposant d'un compte peut noter "
            "n'importe quel etablissement, autant de fois qu'elle le souhaite."),
        preconditions=[
            "Compte bob@example.com, qui n'a jamais commande chez Couscous Atlas (id 5)",
        ],
        etapes=[
            "Se connecter avec bob@example.com",
            "Deposer un avis : POST /restaurant/5/review avec rating=5 et un commentaire",
        ],
        attendu=("Le depot est refuse : aucune commande n'a ete passee chez ce "
                 "restaurant."),
        obtenu=("L'avis est enregistre et le message Merci pour votre avis ! est "
                "affiche."),
        impact=(
            "Les notes des restaurants ne sont pas fiables : elles peuvent etre "
            "gonflees ou sabotees a volonte. Or la note est le principal critere de "
            "choix du client et le critere de tri par defaut de la page d'accueil."),
    ),
    dict(
        id="BUG-012", slug="transition-statut-invalide",
        titre="Le back-office accepte des transitions de statut impossibles",
        severite="Majeure", priorite="P2",
        risque="R9", cas=["RM12"],
        contexte=(
            "L'administrateur peut affecter n'importe quel statut a une commande, sans "
            "controle du cycle de vie. Une commande deja livree peut redevenir "
            "confirmee, ou etre annulee apres livraison."),
        preconditions=[
            "La commande 1 est au statut delivered (donnees de demonstration)",
            "Compte administrateur admin@quickorder.local",
        ],
        etapes=[
            "Se connecter comme administrateur",
            "POST /admin/orders/1/status avec status=confirmed",
            "Relire le statut : GET /api/orders/1",
        ],
        attendu=("La transition est refusee : une commande livree ne peut pas revenir "
                 "a un statut anterieur."),
        obtenu=("Le statut passe de delivered a confirmed et le message Statut mis a "
                "jour s'affiche."),
        impact=(
            "Le suivi des commandes perd toute fiabilite : indicateurs fausses, "
            "commandes livrees reinjectees dans la file de preparation, litiges "
            "impossibles a arbitrer sur la base des statuts."),
    ),
    dict(
        id="BUG-008", slug="filtre-livraison-inverse",
        titre="Le filtre frais de livraison maximum retourne exactement l'inverse du resultat attendu",
        severite="Majeure", priorite="P2",
        risque="R10", cas=["RM08"],
        contexte=(
            "Sur la page d'accueil, le filtre des frais de livraison maximum selectionne "
            "les restaurants dont les frais sont superieurs ou egaux au seuil, au lieu "
            "d'inferieurs ou egaux. Le resultat est systematiquement l'inverse de la "
            "demande."),
        preconditions=[
            "Frais de livraison : Green Kitchen 1,99 - Pizza Roma 2,49 - "
            "Burger Factory 2,99 - Couscous Atlas 2,99 - Tokyo Bowl 3,49",
        ],
        etapes=[
            "Demander les restaurants a 2,50 EUR maximum : GET /?max_delivery=2.50",
            "Comparer la liste obtenue aux frais reels",
        ],
        attendu=("Green Kitchen (1,99 EUR) et Pizza Roma (2,49 EUR) uniquement."),
        obtenu=("Burger Factory, Couscous Atlas, Night Sushi et Tokyo Bowl : "
                "exactement les restaurants dont les frais DEPASSENT 2,50 EUR. Les deux "
                "seuls restaurants correspondant reellement au critere sont exclus."),
        impact=(
            "Le client sensible au prix se voit presenter les options les plus cheres "
            "et n'a aucun moyen de trouver les moins cheres. Perte de conversion "
            "directe sur un filtre mis en avant dans l'interface."),
    ),
    dict(
        id="BUG-009", slug="recherche-ignore-description",
        titre="La recherche ignore la description des restaurants",
        severite="Mineure", priorite="P3",
        risque="R10", cas=["RM09"],
        contexte=(
            "La recherche de la page d'accueil ne porte que sur le nom du restaurant. "
            "Les mots figurant dans la description, qui decrivent pourtant l'offre "
            "culinaire, ne remontent aucun resultat."),
        preconditions=[
            "Pizza Roma a pour description : Pizzas romaines, pates et desserts italiens.",
            "Le mot romaines n'apparait que dans cette description, dans aucun nom",
        ],
        etapes=[
            "Controle : GET /?q=pizza (le mot figure dans le nom Pizza Roma)",
            "Cible : GET /?q=romaines (le mot figure seulement dans la description)",
            "Comparer les deux resultats",
        ],
        attendu=("Pizza Roma remonte dans les deux cas : la recherche couvre le nom et "
                 "la description."),
        obtenu=("q=pizza retourne bien Pizza Roma, ce qui confirme que la recherche "
                "fonctionne sur le nom. q=romaines ne retourne aucun resultat : la "
                "description est totalement ignoree."),
        impact=(
            "Le client qui cherche un type de cuisine par mot-cle ne trouve pas les "
            "restaurants correspondants. Perte de trafic sur le catalogue, d'autant "
            "que la description est le seul champ decrivant reellement l'offre."),
    ),
    dict(
        id="BUG-013", slug="api-expose-restaurants-fermes",
        titre="L'API liste les restaurants fermes sans possibilite de les filtrer",
        severite="Mineure", priorite="P3",
        risque="R11", cas=["RM13"],
        contexte=(
            "GET /api/restaurants retourne l'ensemble des restaurants, y compris ceux "
            "qui sont fermes, et n'offre aucun parametre permettant de les exclure. "
            "Un consommateur de l'API affichera donc des etablissements non "
            "commandables."),
        preconditions=[
            "Night Sushi (id 6) a is_open=false",
        ],
        etapes=[
            "Appeler GET /api/restaurants avec une cle valide",
            "Filtrer la reponse sur is_open=false",
        ],
        attendu=("Les restaurants fermes sont exclus par defaut, ou un parametre "
                 "permet de les filtrer."),
        obtenu=("Night Sushi est retourne dans la liste. Le champ is_open permet de le "
                "detecter, mais aucun filtrage n'est propose par l'API."),
        impact=(
            "Chaque client de l'API doit reimplementer ce filtrage. Combine a "
            "BUG-002, qui autorise la commande chez un restaurant ferme, le risque "
            "d'erreur augmente sensiblement."),
    ),
]


TEMPLATE = u"""# {id} — {titre}

| | |
|---|---|
| Identifiant | {id} |
| Severite | {severite} |
| Priorite | {priorite} |
| Risque couvert | {risque} (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | {cas} |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

{contexte}

## Preconditions

{preconditions}

## Etapes de reproduction

{etapes}

## Resultat attendu

{attendu}

## Resultat obtenu

{obtenu}

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

{preuves}

## Impact

{impact}
"""


def fmt_list(items, numbered=False):
    if numbered:
        return "\n".join("%d. %s" % (i + 1, x) for i, x in enumerate(items))
    return "\n".join("- %s" % x for x in items)


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    index = []
    for b in BUGS:
        blocs = []
        for cid in b["cas"]:
            r = results.get(cid)
            if not r:
                continue
            blocs.append(u"Cas %s — %s\n\n```\n%s\n```" % (cid, r["titre"], r["evidence"].strip()))
        body = TEMPLATE.format(
            id=b["id"], titre=b["titre"], severite=b["severite"], priorite=b["priorite"],
            risque=b["risque"], cas=", ".join(b["cas"]), contexte=b["contexte"],
            preconditions=fmt_list(b["preconditions"]),
            etapes=fmt_list(b["etapes"], numbered=True),
            attendu=b["attendu"], obtenu=b["obtenu"],
            preuves="\n\n".join(blocs), impact=b["impact"])
        path = os.path.join(OUT, "%s-%s.md" % (b["id"], b["slug"]))
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(body)
        index.append(b)
        print("ecrit : %s" % os.path.basename(path))

    ordre = {"Bloquante": 0, "Critique": 1, "Majeure": 2, "Mineure": 3}
    index.sort(key=lambda x: (ordre[x["severite"]], x["id"]))
    lignes = [u"# Anomalies relevees — QuickOrder V3.1", u"",
              u"13 anomalies reproductibles, classees par severite decroissante.", u"",
              u"| ID | Titre | Severite | Priorite | Cas de test |",
              u"|---|---|---|---|---|"]
    for b in index:
        lignes.append(u"| [%s](%s-%s.md) | %s | %s | %s | %s |"
                      % (b["id"], b["id"], b["slug"], b["titre"], b["severite"],
                         b["priorite"].split(" ")[0], ", ".join(b["cas"])))
    lignes += [u"", u"## Repartition par severite", u"",
               u"| Severite | Nombre |", u"|---|---|"]
    for s in ["Bloquante", "Critique", "Majeure", "Mineure"]:
        lignes.append(u"| %s | %d |" % (s, sum(1 for b in index if b["severite"] == s)))
    lignes.append(u"| Total | %d |" % len(index))
    with io.open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lignes) + "\n")
    print("ecrit : README.md (index des anomalies)")


if __name__ == "__main__":
    main()
