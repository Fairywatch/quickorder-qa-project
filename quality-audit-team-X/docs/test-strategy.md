# Stratégie de test — QuickOrder V3.1

Équipe d'audit qualité QuickOrder. Version testée : QuickOrder V3.1, déployée avec `docker compose up`. Environnement : `http://127.0.0.1:5000`, base SQLite réinitialisée avant chaque campagne. Rédigé le 22 septembre 2026.

## 1. Pourquoi cette campagne

Nous devons évaluer la qualité de QuickOrder avant sa mise en production et rendre une recommandation Go ou No-Go, appuyée sur des preuves que n'importe qui peut rejouer.

Il ne s'agit pas de corriger l'application. Il s'agit de démontrer ses défauts. Pour chaque anomalie que nous déclarons, le lecteur doit pouvoir retrouver la requête HTTP que nous avons envoyée et la réponse que l'application nous a renvoyée — tout est consigné dans `evidence/raw-log.md`.

## 2. Périmètre

### Ce que nous testons

| Domaine | Détail |
|---|---|
| Catalogue | Page d'accueil, recherche, filtres (catégorie, frais de livraison, végétarien), tri |
| Fiche restaurant | Affichage du menu, état ouvert ou fermé, affichage du stock |
| Panier | Ajout, modification de quantité, suppression, règle « un seul restaurant » |
| Tunnel de commande | Checkout, adresse, coupons, moyens de paiement (carte, PayPal, espèces) |
| Compte client | Inscription, connexion, déconnexion, profil, adresses |
| Commandes | Historique, détail, annulation, recommande |
| Avis et favoris | Dépôt d'avis, ajout et retrait de favoris |
| Back-office | Tableau de bord admin, changement de statut des commandes |
| API REST | Les 11 endpoints `/api/*` documentés dans Swagger, authentification par `X-API-Key` |
| Règles métier | Montant minimum, stock, restaurant fermé, coupons, cycle de vie des commandes |

### Ce que nous laissons de côté

| Exclusion | Pourquoi |
|---|---|
| Tests de performance et de charge | Aucun objectif de performance n'est spécifié, et un environnement local mono-conteneur ne serait pas représentatif |
| Audit de sécurité approfondi (pentest, OWASP complet) | Hors mandat. Nous vérifions seulement les contrôles d'accès fonctionnels |
| Compatibilité multi-navigateurs et mobile | Aucune matrice de navigateurs cibles ne nous a été fournie |
| Accessibilité (RGAA, WCAG) | Non demandé par le brief. À prévoir dans un second audit |
| Intégration réelle des paiements | Les paiements sont simulés dans l'application, aucun prestataire n'est connecté |
| Envoi d'e-mails et notifications | La fonctionnalité n'existe pas dans l'application |
| Tests utilisateurs (section 6 du brief) | Non réalisés : il faut des participants humains, que nous n'avons pas pu mobiliser |

## 3. Les parcours critiques

Nous les avons classés par impact business décroissant, et c'est là que nous avons concentré l'effort.

| # | Parcours | Pourquoi il compte |
|---|---|---|
| PC1 | Commander et payer | C'est le seul parcours qui génère du chiffre d'affaires. Toute anomalie s'y traduit directement en perte d'argent ou en litige client |
| PC2 | Cohérence du stock | Une commande acceptée sur un produit indisponible est une commande qu'on ne peut pas livrer : remboursement, perte de confiance |
| PC3 | Disponibilité du restaurant | Une commande vers un restaurant fermé ne sera jamais préparée |
| PC4 | Calcul du montant | Une erreur de calcul est une perte financière directe, dans un sens ou dans l'autre |
| PC5 | Authentification et cloisonnement des comptes | Un accès aux commandes ou aux données d'un autre client, c'est un incident RGPD |
| PC6 | Découverte du catalogue | Sans découverte fiable, le client n'arrive jamais jusqu'au parcours d'achat |
| PC7 | Back-office, suivi des commandes | Le pilotage opérationnel dépend de la fiabilité des statuts |

## 4. Les risques que nous anticipions

| ID | Risque | Probabilité | Impact | Criticité |
|---|---|---|---|---|
| R1 | Double facturation du client (doublon de commande) | Élevée | Très fort | Critique |
| R2 | Commande encaissée mais non livrable (stock ou restaurant fermé) | Élevée | Très fort | Critique |
| R3 | Encaissement inférieur au montant dû (paiement espèces) | Moyenne | Fort | Critique |
| R4 | Manipulation des montants depuis le client (remise indue) | Moyenne | Fort | Critique |
| R5 | Publicité mensongère sur une promotion affichée | Élevée | Moyen | Majeur |
| R6 | Incohérence des données de stock (valeurs négatives) | Élevée | Moyen | Majeur |
| R7 | Non-respect du montant minimum imposé par le restaurant | Élevée | Moyen | Majeur |
| R8 | Faux avis dégradant la confiance dans les notes | Moyenne | Moyen | Majeur |
| R9 | Statuts de commande incohérents (pilotage faussé) | Moyenne | Moyen | Majeur |
| R10 | Résultats de recherche et de filtres erronés (perte de trafic) | Élevée | Faible | Modéré |
| R11 | Exposition de données non commandables via l'API | Moyenne | Faible | Modéré |

La cotation complète, avec les scores et les anomalies rattachées, est dans [`risk-matrix.md`](risk-matrix.md).

## 5. Les types de tests retenus

| Type | Comment nous l'avons mis en œuvre |
|---|---|
| Fonctionnels boîte noire | C'est le cœur de la campagne : l'application est sollicitée par ses interfaces réelles, en HTTP, sans dépendre de son code |
| Cas nominaux | Vérifient que le parcours standard fonctionne (8 cas) |
| Cas aux limites | Bornes des intervalles : quantités 0, 1, 20 et 21, montant minimum à 19,99 puis 20,00, stock exact, mot de passe de 7 et 8 caractères (10 cas) |
| Cas d'erreur et robustesse | Entrées invalides, ressources absentes, authentification et droits (12 cas) |
| Règles métier | Confrontation du comportement réel aux règles que le produit annonce (16 cas) |
| Tests d'API REST | Endpoints `/api/*`, codes HTTP, schémas de réponse, authentification par clé |
| Tests d'interface web | Parcours réels avec gestion de session et de cookies, lecture des messages affichés |
| Tests croisés interface et API | Un même défaut est cherché sur les deux canaux. Le doublon PayPal, par exemple, est prouvé par RM05 côté API et RM16 côté web |
| Non-régression | Le harnais `tools/run_campaign.py` se rejoue à l'identique, ce qui permettra de revalider les correctifs |

## 6. Ordre d'exécution

Nous avons priorisé par criticité du parcours d'abord, puis par probabilité de défaillance.

| Priorité | Cible | Cas concernés |
|---|---|---|
| P0, à tester en premier | PC1 à PC4 : paiement, stock, restaurant fermé, calculs | RM01 à RM08, RM14 à RM16, N04, N06 |
| P1 | PC5 : authentification, droits, cloisonnement des comptes | E01, E02, E05, E09, E10, RM10 |
| P2 | Robustesse des entrées et bornes | L01 à L10, E03, E04, E06, E07, E08, E11, E12 |
| P3 | PC6 et PC7 : découverte du catalogue et back-office | RM09, RM11, RM12, RM13, N01 |

## 7. Quand commencer, quand s'arrêter, comment décider

Nous ne lançons la campagne que si l'application démarre, que `/api/health` répond `status: ok`, et que la base a été réinitialisée sur les données de démonstration avec `docker compose down -v`.

Nous considérons la campagne terminée quand les 46 cas ont été exécutés et que chaque anomalie déclarée dispose d'une preuve rejouable.

Pour la décision finale, nous nous sommes fixé trois règles à l'avance :

- No-Go si au moins une anomalie bloquante ou critique touche un parcours critique, de PC1 à PC5.
- Go sous conditions si seules des anomalies majeures ou mineures subsistent, avec des correctifs planifiés.
- Go si aucune anomalie de sévérité supérieure à mineure ne subsiste.

Fixer ces règles avant de tester nous évite d'ajuster le verdict aux résultats.

## 8. Environnement et outillage

| Élément | Valeur |
|---|---|
| Déploiement | Docker Compose, image `python:3.12-slim` |
| URL | `http://127.0.0.1:5000`, Swagger sur `/docs/` |
| Clé API | `quickorder-demo-key`, en-tête `X-API-Key` |
| Comptes | `alice@example.com` / `Password123!`, `bob@example.com` / `Password123!`, `admin@quickorder.local` / `Admin123!` |
| Outils | Navigateur et DevTools, Swagger UI, harnais Python `requests` (`tools/run_campaign.py`) |
| Jeu de données | Données de démonstration de `seed.py` : 6 restaurants dont 1 fermé, 25 produits dont 5 en rupture, 6 coupons dont 1 expiré |

### Reproductibilité

Toute la campagne se rejoue en deux commandes :

```bash
cd ..            # racine de quickorder-qa-project
docker compose down -v && docker compose up -d     # base remise à zéro
cd quality-audit-team-X
python tools/run_campaign.py                       # 46 cas exécutés
```

Chaque exécution régénère `docs/evidence/raw-log.md` et `docs/evidence/results.json`.

Une précision pour finir : notre harnais a lui-même eu deux défauts, découverts en cours de campagne — un sélecteur de messages d'alerte, puis un sélecteur de noms de restaurants. À eux deux, ils produisaient cinq résultats faux. Nous les avons corrigés et rejoué la campagne entière sur base réinitialisée. Les chiffres publiés viennent tous de cette dernière exécution.
