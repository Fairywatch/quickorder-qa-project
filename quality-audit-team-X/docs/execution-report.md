# Rapport d'exécution — QuickOrder V3.1

Campagne du 22 septembre 2026. Environnement Docker Compose sur `http://127.0.0.1:5000`, base réinitialisée avant le lancement. 46 cas exécutés sur l'interface web et l'API REST.

Les preuves brutes sont dans [`evidence/raw-log.md`](evidence/raw-log.md), et les mêmes résultats sous forme exploitable dans [`evidence/results.json`](evidence/results.json).

## 1. Les chiffres

| Indicateur | Valeur |
|---|---|
| Tests exécutés | 46 |
| Pass | 30 (65 %) |
| Fail | 16 (35 %) |
| Blocked | 0 |
| Skipped | 0 |
| Anomalies distinctes | 13 |
| Taux d'exécution | 100 %, aucun cas bloqué |

Par catégorie :

| Catégorie | Total | Pass | Fail | Taux de réussite |
|---|---|---|---|---|
| Cas nominaux | 8 | 8 | 0 | 100 % |
| Cas aux limites | 10 | 10 | 0 | 100 % |
| Cas d'erreur | 12 | 12 | 0 | 100 % |
| Règles métier | 16 | 0 | 16 | 0 % |
| Total | 46 | 30 | 16 | 65 % |

Le brief demandait au minimum 24 cas, soit 6 par catégorie. Nous en avons écrit et exécuté 46, avec au moins 8 cas dans chaque catégorie.

## 2. Comment lire ce résultat

Le tableau ci-dessus est frappant par sa coupure nette, et c'est le principal enseignement de la campagne.

La couche technique est saine. Trente tests sur trente passent sur l'authentification, la validation des formats d'entrée, les codes HTTP, la gestion des ressources absentes et le cloisonnement des comptes. L'API renvoie les bons codes — 401, 400, 404, 409 — refuse les quantités hors bornes, rejette les coupons expirés et empêche un client d'accéder aux commandes d'un autre.

La couche métier, elle, est absente. Les seize cas de règles métier échouent, sans une seule exception. Le produit affiche ses règles — montant minimum, état ouvert ou fermé, mention « HORS STOCK », promotion à 15 % — mais n'en contrôle aucune au moment où le client s'engage financièrement.

Dit autrement : QuickOrder sait refuser une requête mal formée, mais pas une commande commercialement invalide.

Voici les écarts que nous avons constatés entre ce que le client lit et ce que le système fait :

| Règle affichée au client | Contrôle réel |
|---|---|
| « Minimum 25,00 € » sur Couscous Atlas | Commande de 3,50 € acceptée |
| « FERMÉ » sur Night Sushi | Commande acceptée et marquée payée |
| « HORS STOCK » sur le Veggie Burger | Ajout au panier accepté |
| « 15 % de réduction avec ATLAS15 » | 10 % appliqués |
| Paiement espèces de 1,00 € pour 6,69 € dus | Commande marquée `paid`, rendu de −5,69 € |

## 3. Les cas en échec

Les seize échecs se rattachent à treize anomalies distinctes : certaines sont prouvées deux fois, une fois sur chaque canal.

| Cas | Intitulé | Résultat obtenu | Anomalie |
|---|---|---|---|
| RM01 | Montant minimum de commande | Commande de 3,50 € acceptée pour un minimum de 25 € | [BUG-001](bug-reports/BUG-001-minimum-commande-non-applique.md) |
| RM02 | Restaurant fermé | HTTP 201 malgré `is_open=false` | [BUG-002](bug-reports/BUG-002-restaurant-ferme.md) |
| RM03 | Produit en rupture, côté API | HTTP 201, stock passé de 0 à −1 | [BUG-003](bug-reports/BUG-003-produit-rupture-commandable.md) |
| RM04 | Stock négatif | Stock passé de 0 à −20 | [BUG-004](bug-reports/BUG-004-stock-negatif.md) |
| RM05 | Doublon PayPal, côté API | 2 commandes créées pour 1 paiement | [BUG-005](bug-reports/BUG-005-paypal-double-commande.md) |
| RM06 | Paiement espèces insuffisant | `payment_status=paid`, `change_due=-5.69` | [BUG-006](bug-reports/BUG-006-paiement-especes-insuffisant.md) |
| RM07 | Cohérence de la promotion | 10 % appliqués au lieu des 15 % annoncés | [BUG-007](bug-reports/BUG-007-coupon-atlas15-taux-incoherent.md) |
| RM08 | Filtre frais de livraison | Retourne les 4 restaurants les plus chers | [BUG-008](bug-reports/BUG-008-filtre-livraison-inverse.md) |
| RM09 | Recherche sur la description | `q=romaines` ne retourne aucun résultat | [BUG-009](bug-reports/BUG-009-recherche-ignore-description.md) |
| RM10 | Sous-total transmis par le client | `subtotal=999999` accepté sans vérification | [BUG-010](bug-reports/BUG-010-subtotal-client-non-verifie.md) |
| RM11 | Avis sans commande | Avis enregistré par un client n'ayant jamais commandé | [BUG-011](bug-reports/BUG-011-avis-sans-commande.md) |
| RM12 | Transition de statut | `delivered` vers `confirmed` acceptée | [BUG-012](bug-reports/BUG-012-transition-statut-invalide.md) |
| RM13 | Restaurants fermés dans l'API | Night Sushi listé sans filtre possible | [BUG-013](bug-reports/BUG-013-api-expose-restaurants-fermes.md) |
| RM14 | Produit en rupture, côté web | Mention « HORS STOCK » affichée, ajout au panier réussi | [BUG-003](bug-reports/BUG-003-produit-rupture-commandable.md) |
| RM15 | Montant minimum, côté web | « Commande confirmée ! » pour un panier de 3,50 € | [BUG-001](bug-reports/BUG-001-minimum-commande-non-applique.md) |
| RM16 | Doublon PayPal, côté web | 2 commandes créées pour 1 paiement | [BUG-005](bug-reports/BUG-005-paypal-double-commande.md) |

## 4. Les risques, maintenant qu'ils sont avérés

Les risques listés ci-dessous ne sont plus des hypothèses. Chacun repose sur une preuve reproductible.

### Risques critiques, bloquants pour la production

| Risque | Anomalie | Ce qui se passe concrètement |
|---|---|---|
| Double facturation | BUG-005 | Chaque paiement PayPal crée deux commandes. Le client est débité deux fois, le restaurant prépare deux fois, et rien de particulier n'est nécessaire pour déclencher le défaut. Reproduit sur les deux canaux |
| Commande non livrable | BUG-002, BUG-003 | Le client paie pour un restaurant fermé ou un produit en rupture. Remboursement systématique |
| Encaissement insuffisant | BUG-006 | Commande livrée mais non payée, avec un rendu de monnaie négatif enregistré en base |
| Manipulation des montants | BUG-010 | Le montant est pris tel quel depuis le client. Une remise indue s'obtient sans outil particulier |

### Risques majeurs

| Risque | Anomalie | Ce qui se passe concrètement |
|---|---|---|
| Publicité trompeuse | BUG-007 | Cinq points d'écart entre la promotion affichée et la remise accordée |
| Intégrité des données | BUG-004 | Des stocks négatifs, donc des données inutilisables pour le réapprovisionnement |
| Rentabilité des commandes | BUG-001 | Le minimum négocié avec les restaurants partenaires n'est jamais appliqué |
| Fiabilité des notes | BUG-011 | Les avis sont manipulables, alors que la note est le critère de tri par défaut du catalogue |
| Pilotage opérationnel | BUG-012 | Les statuts de commande ne reflètent plus la réalité |

### Risques modérés

| Risque | Anomalie | Ce qui se passe concrètement |
|---|---|---|
| Découverte du catalogue | BUG-008, BUG-009 | Le filtre prix retourne l'inverse de la demande, et la recherche ne couvre pas l'offre décrite |
| Cohérence de l'API | BUG-013 | Les restaurants fermés sont exposés sans filtrage possible |

## 5. Ce qui fonctionne

Ne retenir que les échecs donnerait une image fausse du produit. Les fondations suivantes sont solides et ne demandent aucune reprise :

- L'authentification API rejette correctement une clé absente ou invalide, en HTTP 401 (E01, E02).
- Le cloisonnement des comptes tient : Bob ne peut pas consulter la commande d'Alice (E10).
- Le cloisonnement des rôles tient aussi : un client ne peut pas accéder au back-office (E09).
- La validation des entrées rejette en HTTP 400 les quantités hors bornes, les types incorrects et les moyens de paiement inconnus (L03, L04, E11, E12).
- Les bornes des intervalles sont justes : quantités 1 et 20 acceptées, 0 et 21 refusées.
- Les règles de coupons sont respectées : montant minimum à la borne exacte, plafond de remise appliqué, coupon expiré rejeté (L05, L06, L07, E06).
- La politique de mot de passe fonctionne : 7 caractères refusés, 8 acceptés (L09, L10).
- La règle « un panier égale un restaurant » est appliquée (E08).
- Le parcours nominal va bien de la page d'accueil à la confirmation de commande (N01 à N08).

Cela change la nature du travail de remédiation : les correctifs consistent à ajouter des contrôles métier, pas à refondre l'application. L'architecture, elle, tient.

## 6. Notre recommandation : NO-GO

Nous déconseillons la mise en production de QuickOrder V3.1 en l'état.

Le critère que nous nous étions fixé dans la [stratégie de test](test-strategy.md) était le suivant : No-Go dès qu'une anomalie bloquante ou critique touche un parcours critique. Il est atteint cinq fois.

1. BUG-005, bloquante : double facturation sur tout paiement PayPal, sur les deux canaux.
2. BUG-002, critique : commande acceptée chez un restaurant fermé.
3. BUG-003, critique : commande acceptée sur un produit en rupture.
4. BUG-006, critique : commande livrée sans encaissement suffisant.
5. BUG-010, critique : montants manipulables depuis le client.

Ces cinq anomalies touchent toutes PC1, commander et payer, qui est le seul parcours générant du chiffre d'affaires. Elles se déclenchent en usage normal, sans manipulation experte. Mettre le produit en production exposerait l'entreprise à un litige financier dès les premières commandes.

### Ce qu'il faut pour lever le No-Go

| Étape | Condition | Anomalies concernées |
|---|---|---|
| 1, obligatoire | Corriger les anomalies bloquantes et critiques | BUG-005, BUG-002, BUG-003, BUG-006, BUG-010 |
| 2, obligatoire | Revalider complètement : les 46 cas rejoués, 46 Pass attendus | Campagne entière |
| 3, fortement recommandé | Corriger les anomalies majeures | BUG-001, BUG-004, BUG-007, BUG-011, BUG-012 |
| 4, planifiable | Traiter les anomalies mineures dans une itération ultérieure | BUG-008, BUG-009, BUG-013 |

Un Go sous conditions deviendrait envisageable après les étapes 1 à 3, à condition de désactiver le paiement PayPal jusqu'à ce que BUG-005 soit revalidé en production.

### Revalidation

La campagne se rejoue telle quelle, ce qui permet de vérifier les correctifs sans réécrire les tests :

```bash
cd ..
docker compose down -v && docker compose up -d
cd quality-audit-team-X
python tools/run_campaign.py
```

Le critère de succès est simple : 46 Pass, 0 Fail.

## 7. Ce que cette campagne ne démontre pas

Quelques précisions, par honnêteté méthodologique.

Les tests utilisateurs de la section 6 du brief n'ont pas été réalisés : ils demandent trois scénarios joués par au moins deux personnes réelles. Ce rapport ne contient donc aucune conclusion sur l'ergonomie ressentie.

Nous n'avons mené aucun test de performance ou de charge : rien ne peut être affirmé sur la tenue en production. Pas d'audit de sécurité approfondi non plus, même si nous signalons au passage qu'aucune protection CSRF n'apparaît sur les formulaires.

La concurrence d'accès n'a pas été testée. Deux commandes simultanées sur le dernier article disponible pourraient aggraver BUG-004. Enfin, nous n'avons utilisé qu'un seul navigateur, sans vérification mobile.

### Sur la fiabilité de nos propres chiffres

Deux défauts de notre harnais de test ont été découverts pendant la campagne. Le premier, un sélecteur incorrect des messages d'alerte, produisait quatre faux échecs (L10, E05, E07, E10). Le second, un sélecteur incorrect des noms de restaurants, rendait inexploitables les preuves de RM08 et RM09.

Nous les avons corrigés, puis rejoué la campagne entière sur une base réinitialisée. Tous les chiffres de ce rapport viennent de cette dernière exécution. Nous le mentionnons volontairement : un résultat de test ne vaut que ce que vaut l'instrument qui l'a produit.
