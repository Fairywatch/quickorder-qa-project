# Matrice des risques — QuickOrder V3.1

Campagne du 22 septembre 2026, 46 cas de test. Les résultats détaillés sont dans [`execution-report.md`](execution-report.md).

## 1. Les échelles que nous avons retenues

La probabilité estime la chance que le risque se matérialise en production.

| Niveau | Signification |
|---|---|
| Faible (1) | Nécessite une combinaison rare de conditions |
| Moyenne (2) | Se produit lors d'un usage inhabituel mais réaliste |
| Élevée (3) | Se produit en usage normal, sans manipulation particulière |

L'impact mesure la conséquence pour l'entreprise si le risque se réalise.

| Niveau | Signification |
|---|---|
| Faible (1) | Gêne l'utilisateur, sans perte financière ni juridique |
| Moyen (2) | Perte de chiffre d'affaires, de confiance ou de qualité de pilotage |
| Fort (3) | Perte financière directe, litige client, non-conformité |
| Très fort (4) | Perte financière systématique ou risque juridique caractérisé |

La criticité est le produit des deux.

| Score | Niveau | Traitement |
|---|---|---|
| 9 à 12 | Critique | Correction obligatoire avant mise en production |
| 6 à 8 | Majeur | Correction avant production, ou contournement documenté et accepté |
| 3 à 5 | Modéré | Correction planifiée dans les itérations suivantes |
| 1 à 2 | Mineur | Traitement opportuniste |

## 2. Positionnement des risques

Chaque cellule renvoie aux risques détaillés au paragraphe suivant.

| | Impact faible (1) | Impact moyen (2) | Impact fort (3) | Impact très fort (4) |
|---|---|---|---|---|
| Probabilité élevée (3) | R10 — modéré (3) | R5, R6, R7 — majeur (6) | — | R1, R2 — critique (12) |
| Probabilité moyenne (2) | R11 — modéré (2) | R8, R9 — majeur (4) | R3, R4 — critique (6) | — |
| Probabilité faible (1) | — | — | — | — |

R3 et R4 n'obtiennent qu'un score de 6, ce qui les placerait en « majeur ». Nous les avons remontés en criticité critique : ils portent sur l'encaissement et sur l'intégrité des montants, et sur ces deux sujets nous ne voyons aucune tolérance acceptable avant une mise en production.

## 3. Détail des risques

| ID | Risque | Parcours | Prob. | Impact | Score | Criticité | Anomalie(s) | Statut |
|---|---|---|---|---|---|---|---|---|
| R1 | Double facturation : un paiement PayPal crée deux commandes identiques | PC1 | 3 | 4 | 12 | Critique | [BUG-005](bug-reports/BUG-005-paypal-double-commande.md) | Avéré |
| R2 | Commande encaissée mais non livrable : produit en rupture ou restaurant fermé | PC2, PC3 | 3 | 4 | 12 | Critique | [BUG-002](bug-reports/BUG-002-restaurant-ferme.md), [BUG-003](bug-reports/BUG-003-produit-rupture-commandable.md) | Avéré |
| R3 | Encaissement insuffisant : paiement espèces accepté sous le montant dû | PC1, PC4 | 2 | 3 | 6 | Critique | [BUG-006](bug-reports/BUG-006-paiement-especes-insuffisant.md) | Avéré |
| R4 | Manipulation des montants depuis le client pour obtenir une remise indue | PC4 | 2 | 3 | 6 | Critique | [BUG-010](bug-reports/BUG-010-subtotal-client-non-verifie.md) | Avéré |
| R5 | Publicité mensongère : promotion affichée à 15 %, appliquée à 10 % | PC4 | 3 | 2 | 6 | Majeur | [BUG-007](bug-reports/BUG-007-coupon-atlas15-taux-incoherent.md) | Avéré |
| R6 | Données de stock incohérentes : valeurs négatives en base | PC2 | 3 | 2 | 6 | Majeur | [BUG-004](bug-reports/BUG-004-stock-negatif.md) | Avéré |
| R7 | Montant minimum du restaurant non respecté : commandes non rentables | PC1 | 3 | 2 | 6 | Majeur | [BUG-001](bug-reports/BUG-001-minimum-commande-non-applique.md) | Avéré |
| R8 | Faux avis : notes déposées sans commande préalable | PC6 | 2 | 2 | 4 | Majeur | [BUG-011](bug-reports/BUG-011-avis-sans-commande.md) | Avéré |
| R9 | Cycle de vie des commandes non respecté : pilotage opérationnel faussé | PC7 | 2 | 2 | 4 | Majeur | [BUG-012](bug-reports/BUG-012-transition-statut-invalide.md) | Avéré |
| R10 | Découverte du catalogue défaillante : filtre inversé et recherche partielle | PC6 | 3 | 1 | 3 | Modéré | [BUG-008](bug-reports/BUG-008-filtre-livraison-inverse.md), [BUG-009](bug-reports/BUG-009-recherche-ignore-description.md) | Avéré |
| R11 | L'API expose des restaurants fermés sans distinction exploitable | PC6 | 2 | 1 | 2 | Modéré | [BUG-013](bug-reports/BUG-013-api-expose-restaurants-fermes.md) | Avéré |

Les onze risques que nous avions identifiés avant de tester se sont tous matérialisés pendant la campagne. Aucun n'est resté au stade d'hypothèse.

## 4. Ce qui a été testé sans rien trouver

Ces points se sont révélés conformes. C'est la base saine sur laquelle la remédiation peut s'appuyer.

| Domaine | Vérification | Résultat |
|---|---|---|
| Authentification API | Appel sans clé, puis avec une clé invalide : HTTP 401 | Conforme (E01, E02) |
| Cloisonnement des comptes | Bob ne peut pas consulter la commande d'Alice | Conforme (E10) |
| Cloisonnement des rôles | Un client ne peut pas accéder au back-office | Conforme (E09) |
| Validation des entrées API | Quantité hors bornes, non numérique, paiement inconnu : HTTP 400 | Conforme (L03, L04, E11, E12) |
| Règle « un panier = un restaurant » | Mélange de deux restaurants refusé | Conforme (E08) |
| Expiration des coupons | Coupon expiré rejeté | Conforme (E06) |
| Plafond de remise | `max_discount` correctement appliqué | Conforme (L07) |
| Politique de mot de passe | 7 caractères refusés, 8 acceptés | Conforme (L09, L10) |
| Ressources inexistantes | HTTP 404 correctement retourné | Conforme (E03, E04) |

Il y a une leçon à tirer de cette liste. Le problème de QuickOrder n'est pas technique : la couche HTTP, l'authentification et la validation des formats sont maîtrisées. Ce sont les règles métier qui manquent — validées à l'affichage, jamais au moment de l'engagement commercial.

## 5. Risques que nous n'avons pas couverts

| Risque résiduel | Pourquoi il reste ouvert | Ce que nous recommandons |
|---|---|---|
| Tenue en charge, temps de réponse | Hors périmètre, environnement non représentatif | Campagne de performance sur un environnement de pré-production |
| Vulnérabilités de sécurité (injection, XSS, CSRF) | Hors mandat — nous avons tout de même constaté qu'aucune protection CSRF n'est en place sur les formulaires | Audit de sécurité dédié |
| Concurrence d'accès sur le stock | Demande un outillage de test parallèle | Tester deux commandes simultanées sur le dernier article disponible |
| Accessibilité, compatibilité navigateurs | Hors périmètre | Audit RGAA et matrice de navigateurs |
| Ressenti utilisateur réel | Section 6 du brief, non réalisée | Organiser des tests sur 3 scénarios avec 2 personnes minimum |
