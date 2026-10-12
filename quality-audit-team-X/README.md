# Audit qualité — QuickOrder V3.1

Ce dépôt contient l'audit qualité de QuickOrder, une plateforme de livraison de repas, réalisé avant sa mise en production. Nous n'avons pas cherché à corriger l'application : notre travail consistait à évaluer sa qualité et à prouver ses défauts.

## Verdict : NO-GO

| Indicateur | Valeur |
|---|---|
| Cas de test exécutés | 46 |
| Pass | 30 (65 %) |
| Fail | 16 (35 %) |
| Blocked / Skipped | 0 / 0 |
| Anomalies distinctes | 13, dont 1 bloquante et 4 critiques |

Nous déconseillons la mise en production en l'état. Cinq anomalies bloquantes ou critiques touchent le parcours de commande et de paiement, et elles se déclenchent en usage normal — aucune manipulation particulière n'est nécessaire pour les reproduire.

## Ce que montre la campagne

QuickOrder affiche ses règles métier (montant minimum, restaurant fermé, produit en rupture, promotion à 15 %) mais n'en contrôle aucune au moment où le client s'engage financièrement.

Le résultat est nettement coupé en deux :

| Couche | Résultat | Ce qu'on en retient |
|---|---|---|
| Technique : authentification, validation des formats, codes HTTP, cloisonnement | 30 / 30 Pass | Les fondations sont saines |
| Métier : montant minimum, stock, paiement, promotions, statuts | 0 / 16 Pass | Les règles ne sont jamais appliquées |

C'est une bonne nouvelle pour la remédiation : il s'agit d'ajouter des contrôles, pas de refondre l'application.

Quelques écarts constatés entre l'affichage et le comportement réel :

| Règle affichée au client | Comportement réel |
|---|---|
| « Minimum 25,00 € » | Commande de 3,50 € acceptée |
| « FERMÉ » | Commande acceptée et marquée payée |
| « HORS STOCK » | Ajout au panier accepté, stock descendu à −20 |
| « 15 % de réduction » | 10 % appliqués |
| Paiement espèces de 1,00 € pour 6,69 € dus | Commande marquée `paid`, rendu de −5,69 € |

S'y ajoute l'anomalie qui nous inquiète le plus : tout paiement PayPal crée deux commandes, donc une double facturation et une double préparation. Le défaut est présent sur l'interface web comme sur l'API.

## Contenu du dépôt

```
quality-audit-team-X/
├── README.md
├── Audit-qualite-QuickOrder.docx    le rapport complet, format Word
├── docs/
│   ├── test-strategy.md             périmètre, parcours critiques, risques, priorisation
│   ├── risk-matrix.md               matrice risque x impact, 11 risques cotés
│   ├── test-cases.xlsx              les 46 cas de test, sur 3 feuilles
│   ├── execution-report.md          résultats, analyse et recommandation Go/No-Go
│   ├── bug-reports/                 13 fiches d'anomalie et leur index
│   ├── improvement-plan.md          10 améliorations priorisées
│   └── evidence/
│       ├── raw-log.md               journal brut des requêtes et des réponses
│       └── results.json             les mêmes résultats, exploitables par un script
└── tools/
    ├── run_campaign.py              le harnais qui exécute la campagne
    ├── gen_bugs.py                  génère les fiches d'anomalie
    ├── gen_xlsx.py                  génère le classeur de cas de test
    └── build_docx.js                génère le rapport Word
```

Si vous ne lisez qu'un seul fichier, prenez `docs/execution-report.md` : il contient la décision et son argumentaire. Pour le détail des cas, ouvrez `docs/test-cases.xlsx`. Pour savoir quoi corriger et dans quel ordre, `docs/improvement-plan.md`.

## Les 13 anomalies

| ID | Titre | Sévérité |
|---|---|---|
| [BUG-005](docs/bug-reports/BUG-005-paypal-double-commande.md) | Un paiement PayPal crée deux commandes identiques | Bloquante |
| [BUG-002](docs/bug-reports/BUG-002-restaurant-ferme.md) | Un restaurant fermé accepte les commandes | Critique |
| [BUG-003](docs/bug-reports/BUG-003-produit-rupture-commandable.md) | Un produit en rupture reste commandable | Critique |
| [BUG-006](docs/bug-reports/BUG-006-paiement-especes-insuffisant.md) | Paiement en espèces insuffisant accepté et marqué payé | Critique |
| [BUG-010](docs/bug-reports/BUG-010-subtotal-client-non-verifie.md) | Le montant transmis par le client n'est pas vérifié | Critique |
| [BUG-001](docs/bug-reports/BUG-001-minimum-commande-non-applique.md) | Montant minimum de commande jamais appliqué | Majeure |
| [BUG-004](docs/bug-reports/BUG-004-stock-negatif.md) | Le stock devient négatif | Majeure |
| [BUG-007](docs/bug-reports/BUG-007-coupon-atlas15-taux-incoherent.md) | Promotion annoncée à 15 %, appliquée à 10 % | Majeure |
| [BUG-008](docs/bug-reports/BUG-008-filtre-livraison-inverse.md) | Le filtre frais de livraison retourne l'inverse | Majeure |
| [BUG-011](docs/bug-reports/BUG-011-avis-sans-commande.md) | Avis possible sans avoir commandé | Majeure |
| [BUG-012](docs/bug-reports/BUG-012-transition-statut-invalide.md) | Transitions de statut impossibles acceptées | Majeure |
| [BUG-009](docs/bug-reports/BUG-009-recherche-ignore-description.md) | La recherche ignore la description | Mineure |
| [BUG-013](docs/bug-reports/BUG-013-api-expose-restaurants-fermes.md) | L'API expose les restaurants fermés | Mineure |

## Reproduire la campagne

Rien dans ce dépôt n'est déclaratif. Chaque résultat vient d'une requête HTTP réellement envoyée à l'application, et les réponses sont conservées dans [`docs/evidence/raw-log.md`](docs/evidence/raw-log.md). Vous pouvez tout rejouer.

Il vous faut Docker Desktop démarré, et Python 3.12 ou plus avec le paquet `requests` (ajoutez `openpyxl` si vous voulez régénérer le classeur).

```bash
# 1. Démarrer QuickOrder sur une base propre (racine du projet)
cd ..
docker compose down -v && docker compose up -d

# 2. Lancer la campagne complète
cd quality-audit-team-X
python tools/run_campaign.py
```

Comptez moins d'une minute pour les 46 cas. Sur la version que nous avons auditée, vous devez obtenir 30 Pass et 16 Fail. Une fois les correctifs appliqués, l'objectif est 46 Pass et 0 Fail.

Pour régénérer les livrables :

```bash
python tools/gen_bugs.py    # fiches d'anomalie
python tools/gen_xlsx.py    # classeur de cas de test
node tools/build_docx.js    # rapport Word
```

## Comment nous avons travaillé

Nous avons testé en boîte noire : l'application est sollicitée par ses interfaces réelles, en HTTP, sans jamais dépendre de son code interne.

Pour les défauts sensibles, nous avons cherché sur les deux canaux. Le doublon PayPal, par exemple, est prouvé une fois côté API (cas RM05) et une fois côté web (cas RM16) — un défaut présent des deux côtés ne se corrige pas au même endroit qu'un défaut isolé.

Chaque anomalie cite la requête envoyée et la réponse reçue, et la base est réinitialisée avant chaque exécution. Certains cas intègrent aussi un témoin pour écarter les faux positifs : BUG-009 vérifie d'abord que la recherche sur `?q=pizza` fonctionne, avant de conclure que `?q=romaines` échoue.

### Une précision sur la fiabilité des chiffres

Notre harnais de test a lui-même eu deux défauts, découverts en cours de campagne. Un sélecteur de messages d'alerte mal écrit produisait quatre faux échecs, et un sélecteur de noms de restaurants rendait inexploitables deux preuves. Nous les avons corrigés, puis rejoué la campagne entière sur une base remise à zéro. Tous les chiffres publiés ici viennent de cette dernière exécution.

Nous le mentionnons parce qu'un résultat de test ne vaut que ce que vaut l'instrument qui l'a produit.

## Ce que cet audit ne couvre pas

Les tests utilisateurs demandés par le brief (section 6) n'ont pas été réalisés : il faut trois scénarios joués par au moins deux personnes réelles. Nous n'avons donc aucune conclusion sur l'ergonomie ressentie, et le fichier `docs/user-feedback.md` n'existe pas.

Nous n'avons pas non plus mené de tests de performance ou de charge, ni d'audit de sécurité approfondi — nous signalons quand même qu'aucune protection CSRF n'apparaît sur les formulaires. La concurrence d'accès au stock n'a pas été testée, et tout a été vérifié sur un seul navigateur, sans contrôle mobile.

## Environnement testé

| Élément | Valeur |
|---|---|
| Application | QuickOrder V3.1, déployée via Docker Compose |
| URL | `http://127.0.0.1:5000`, Swagger sur `/docs/` |
| Clé API | `quickorder-demo-key`, en-tête `X-API-Key` |
| Comptes | `alice@example.com` / `Password123!`, `bob@example.com` / `Password123!`, `admin@quickorder.local` / `Admin123!` |
| Jeu de données | 6 restaurants dont 1 fermé, 25 produits dont 5 en rupture, 6 coupons dont 1 expiré |
| Date de campagne | 22 septembre 2026 |
