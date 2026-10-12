# Plan d'amélioration — QuickOrder V3.1

Rédigé le 22 septembre 2026, à partir de la campagne de 46 cas et des 13 anomalies prouvées. Les résultats sont détaillés dans [`execution-report.md`](execution-report.md).

## Le principe qui guide ce plan

La campagne a mis en évidence une asymétrie nette : la couche technique est saine, la couche métier est absente. Trente tests sur trente passent sur l'authentification, la validation des formats et les codes HTTP, alors que les seize tests de règles métier échouent tous.

Nous ne proposons donc aucune refonte. L'objectif est d'installer, au bon endroit, les contrôles métier qui manquent, puis d'empêcher structurellement leur disparition future.

Les améliorations sont classées par priorité décroissante. Les efforts sont donnés en jours-homme, à titre indicatif.

| # | Amélioration | Priorité | Effort | Anomalies traitées |
|---|---|---|---|---|
| AM-1 | Rendre la création de commande idempotente | P0 | 2 j·h | BUG-005 |
| AM-2 | Centraliser la validation métier de la commande | P0 | 3 j·h | BUG-001, BUG-002, BUG-003, BUG-006 |
| AM-3 | Recalculer les montants côté serveur | P0 | 2 j·h | BUG-010, BUG-006 |
| AM-4 | Sécuriser les mouvements de stock | P1 | 2 j·h | BUG-003, BUG-004 |
| AM-5 | Formaliser le cycle de vie des commandes | P1 | 1,5 j·h | BUG-012 |
| AM-6 | Fiabiliser les avis clients | P2 | 1 j·h | BUG-011 |
| AM-7 | Faire de la promotion affichée la source de vérité | P2 | 1 j·h | BUG-007 |
| AM-8 | Corriger la découverte du catalogue | P2 | 1 j·h | BUG-008, BUG-009, BUG-013 |
| AM-9 | Installer un filet de tests automatisés en intégration continue | P1 | 3 j·h | Prévention |
| AM-10 | Corriger la suite de tests existante | P2 | 0,5 j·h | Dette technique |

Au total, environ 17 jours-homme.

## AM-1 — Rendre la création de commande idempotente

P0, 2 jours-homme, traite BUG-005 (bloquante).

Un paiement PayPal crée deux commandes identiques, sur l'interface web comme via l'API. C'est l'anomalie la plus coûteuse de l'audit : elle produit un litige financier à chaque commande, sans que le client ait quoi que ce soit à faire de particulier.

Nous proposons trois choses. D'abord supprimer la duplication dans le traitement PayPal : un paiement, une commande. Ensuite introduire une clé d'idempotence sur la création de commande, fournie par le client à chaque tentative ; une seconde requête portant la même clé retourne la commande déjà créée au lieu d'en créer une nouvelle. Enfin ajouter une contrainte d'unicité en base sur cette clé, pour que la garantie soit portée par la base de données et non par le seul code applicatif.

Pourquoi aller jusqu'à l'idempotence plutôt que de simplement retirer la duplication ? Parce que c'est la protection standard des systèmes de paiement, et qu'elle couvre bien plus que le défaut actuel : le double-clic du client, la réémission réseau, le rejeu d'une requête. Corriger uniquement la duplication laisserait tous ces cas ouverts.

Validation : RM05 et RM16 passent, le compteur de commandes augmente exactement de 1 par paiement, et rejouer la même requête ne crée pas de seconde commande.

## AM-2 — Centraliser la validation métier de la commande

P0, 3 jours-homme, traite BUG-001, BUG-002, BUG-003 et BUG-006.

Quatre règles sont affichées au client mais jamais contrôlées : le montant minimum, l'état ouvert du restaurant, la présence du produit en stock, et le montant suffisant en espèces. Elles manquent aux deux endroits, tunnel web et API — ce qui en dit long : le problème n'est pas un oubli ponctuel, c'est l'absence d'un point de contrôle commun.

Nous proposons de créer une fonction unique de validation, appelée obligatoirement par les deux canaux avant tout enregistrement :

| Contrôle | Règle | Refus si |
|---|---|---|
| Restaurant ouvert | `restaurant.is_open` | le restaurant est fermé |
| Montant minimum | `subtotal >= restaurant.minimum_order` | le sous-total est inférieur au minimum |
| Disponibilité produit | `product.available` | le produit est indisponible |
| Stock suffisant | `product.stock >= quantité` | le stock est insuffisant |
| Paiement espèces | `cash_received >= total` | le montant remis est inférieur au total |

La fonction devrait retourner la liste complète des motifs de refus, et non le premier rencontré, pour que le client corrige son panier en une seule fois.

Centraliser compte davantage que corriger, ici. Les quatre règles manquaient sur les deux canaux : tant que chaque canal implémente ses propres contrôles, l'écart se reproduira à la prochaine évolution. Un point de passage unique rend l'oubli structurellement impossible.

Validation : RM01, RM02, RM03, RM06, RM14 et RM15 passent, sur les deux canaux.

## AM-3 — Recalculer les montants côté serveur

P0, 2 jours-homme, traite BUG-010 et BUG-006.

L'endpoint de validation des coupons calcule la remise à partir du sous-total envoyé par le client, sans le vérifier. Un appel avec `subtotal: 999999` est accepté tel quel.

Il faut cesser d'accepter un montant venant du client comme base de calcul. Le sous-total doit être recalculé à partir du panier réel — identifiants de produits et quantités — et des prix en base. L'endpoint `/api/coupons/validate` devrait donc prendre en entrée le contenu du panier, et non un montant déjà calculé. Il faut aussi vérifier une seconde fois le montant au moment d'enregistrer la commande, car les prix peuvent changer entre la simulation et la validation.

C'est la règle de base de toute transaction : le client propose, le serveur dispose. Tout montant calculé côté client est une donnée d'affichage, jamais une donnée de décision. Cette correction ferme la faille de remise indue et fiabilise au passage le contrôle du paiement en espèces.

Validation : RM10 passe, un sous-total arbitraire est ignoré ou rejeté. L05 et L07 continuent de passer, ce qui prouve l'absence de régression sur le seuil et le plafond.

## AM-4 — Sécuriser les mouvements de stock

P1, 2 jours-homme, traite BUG-003 et BUG-004.

Le stock est décrémenté sans vérification préalable : il descend à −20 après une commande excédentaire, et les données de stock ne veulent alors plus rien dire.

Quatre mesures. Vérifier puis décrémenter dans la même transaction, avec verrouillage de la ligne produit, pour que deux commandes simultanées ne puissent pas consommer le même stock. Ajouter une contrainte en base interdisant un stock négatif, comme dernier rempart si un chemin de code oubliait le contrôle. Restituer le stock lors de l'annulation d'une commande — le parcours d'annulation existe et fonctionne, mais ne réapprovisionne pas. Et masquer ou désactiver le bouton d'ajout au panier pour un produit en rupture, afin que l'interface soit cohérente avec la règle.

La contrainte en base est ce qui distingue une correction d'une garantie. Quant à la restitution du stock, elle traite un défaut que la campagne n'a pas couvert mais qui se voit à la lecture du parcours d'annulation : il serait incohérent de corriger le décrément sans corriger l'incrément.

Validation : RM03, RM04 et RM14 passent. Le stock reste positif ou nul en toutes circonstances, y compris lors de deux commandes simultanées sur le dernier article.

## AM-5 — Formaliser le cycle de vie des commandes

P1, 1,5 jour-homme, traite BUG-012.

Le back-office accepte n'importe quelle transition de statut : une commande livrée peut redevenir « confirmée ». Le suivi perd alors toute fiabilité.

Il faut déclarer explicitement les transitions autorisées :

```
confirmed         → preparing, cancelled
preparing         → out_for_delivery, cancelled
out_for_delivery  → delivered
delivered         → (état final)
cancelled         → (état final)
```

Toute transition non déclarée doit être refusée, avec un message indiquant le statut courant et les transitions possibles. Il faut aussi journaliser chaque changement — qui, quand, ancien et nouveau statut — pour permettre d'arbitrer les litiges.

Un statut n'est pas un champ libre, c'est un automate. L'expliciter rend la règle lisible et testable, là où elle est aujourd'hui implicite. La journalisation répond à un besoin différent : sans historique, un litige client est inarbitrable.

Validation : RM12 passe, et les transitions valides restent possibles, ce que vérifie N07.

## AM-6 — Fiabiliser les avis clients

P2, 1 jour-homme, traite BUG-011.

Tout client connecté peut noter n'importe quel restaurant sans y avoir jamais commandé, et autant de fois qu'il le souhaite. Or la note est le critère de tri par défaut du catalogue.

Il faut conditionner le dépôt d'un avis à l'existence d'une commande livrée chez ce restaurant pour ce client, rattacher l'avis à la commande, et n'autoriser qu'un avis par commande. Afficher une mention « Commande vérifiée » sur les avis rendrait la garantie visible.

Le modèle de données prévoit déjà le lien entre avis et commande : le champ `order_id` existe mais n'est pas alimenté. La correction consiste donc à utiliser ce qui est là, pas à l'inventer. Et l'affichage de la mention transforme un contrôle technique en argument de confiance pour le client.

Validation : RM11 passe, un client sans commande ne peut pas déposer d'avis, et un client ayant commandé le peut toujours.

## AM-7 — Faire de la promotion affichée la source de vérité

P2, 1 jour-homme, traite BUG-007.

La fiche restaurant annonce « 15 % de réduction avec ATLAS15 », le coupon appliqué en accorde 10. L'écart est de cinq points, au détriment du client.

À court terme, il faut aligner le taux réel sur le taux annoncé, ou corriger l'annonce, après arbitrage commercial. Mais le fond du problème est ailleurs : il existe aujourd'hui deux sources de vérité. Le texte promotionnel affiché est saisi librement, indépendamment du coupon. Il devrait être généré à partir du coupon, pour que l'écart devienne impossible. Un test de cohérence vérifiant que toute promotion affichée correspond à un coupon actif au taux annoncé compléterait utilement le dispositif.

Corriger la valeur sans supprimer la double saisie laisserait le défaut réapparaître à la prochaine promotion. C'est la génération automatique du texte qui élimine réellement la classe de problème. L'enjeu n'est d'ailleurs pas que commercial : un écart entre le prix annoncé et le prix pratiqué est une pratique commerciale trompeuse.

Validation : RM07 passe, le taux appliqué égale le taux annoncé.

## AM-8 — Corriger la découverte du catalogue

P2, 1 jour-homme, traite BUG-008, BUG-009 et BUG-013.

Trois défauts ici. Le filtre « frais de livraison maximum » retourne exactement l'inverse de la demande : à 2,50 € maximum, il affiche les quatre restaurants les plus chers et masque les deux seuls qui correspondent. La recherche ignore la description, si bien que `q=romaines` ne retourne rien alors que le mot figure dans la description de Pizza Roma. Et l'API expose les restaurants fermés sans filtre possible.

Les corrections sont simples : inverser la comparaison du filtre de frais, étendre la recherche au nom et à la description en ignorant les accents et la casse (chercher « vegetarien » doit trouver « végétariennes »), et ajouter un paramètre `open_only` à `GET /api/restaurants` tout en signalant visuellement les restaurants fermés dans les résultats.

Ces trois défauts coûtent peu à corriger, mais ils se situent en haut du tunnel de conversion : un client qui ne trouve pas le restaurant qu'il cherche n'atteint jamais le parcours d'achat. Le filtre inversé est le plus pénalisant des trois, puisqu'il dessert précisément le client sensible au prix.

Validation : RM08, RM09 et RM13 passent.

## AM-9 — Installer un filet de tests automatisés en intégration continue

P1, 3 jours-homme, prévention.

Les seize règles métier manquantes n'avaient été détectées par aucun test avant cet audit. La suite existante ne compte que six tests, tous techniques. Rien n'empêche aujourd'hui le retour de ces défauts.

Nous proposons d'intégrer les 46 cas de la campagne comme suite de non-régression exécutée à chaque modification — le harnais `tools/run_campaign.py` est déjà rejouable en une commande. La livraison devrait être bloquée si un seul cas de règle métier échoue. Chaque anomalie corrigée mérite son propre test, pour garantir qu'un défaut corrigé ne revient pas. Publier le taux de réussite par catégorie à chaque exécution permettrait enfin de suivre la dette dans le temps.

C'est la seule amélioration de ce plan qui traite la cause plutôt que les symptômes. Les neuf autres corrigent l'existant ; celle-ci empêche la reconstitution du même écart. Son coût marginal est faible, puisque les tests sont déjà écrits et exécutables.

Validation : la suite s'exécute automatiquement et échoue si un cas régresse.

## AM-10 — Corriger la suite de tests existante

P2, 0,5 jour-homme, dette technique.

La suite livrée avec le projet échoue à l'exécution : `tests/test_smoke.py::test_api_orders_with_key` plante, cinq tests passent et un échoue.

La cause est la suivante. Le jeu de données de test crée l'utilisateur `test@example.com`, alors que le code de l'API retombe en dur sur `alice@example.com`, absent en environnement de test. L'utilisateur vaut alors `None`, et l'accès à son identifiant provoque une erreur.

Il faut supprimer le repli codé en dur sur un utilisateur nommé — l'appelant doit être identifié par l'authentification, pas deviné — aligner le jeu de données de test sur les besoins réels des tests, et faire échouer la construction si la suite ne passe pas à 100 %.

Une suite qui échoue en permanence cesse d'être un signal : l'équipe s'habitue au rouge et ne distingue plus une vraie régression d'un échec connu. Cet échec doit être traité avant AM-9, sans quoi le filet de sécurité naîtra déjà déconsidéré.

Il y a d'ailleurs un point plus sérieux derrière ce défaut de test. Le repli en dur sur `alice@example.com` signifie que, dans l'API, toute requête munie de la clé agit au nom de ce compte. C'est à corriger avant toute exposition réelle de l'API.

Validation : `pytest` passe à 100 % sur la suite existante.

## Dans quel ordre

| Étape | Contenu | Durée | Ce qui est acquis |
|---|---|---|---|
| Lot 1, levée du No-Go | AM-1, AM-2, AM-3 | ~7 j·h | Les 5 anomalies bloquantes et critiques sont corrigées |
| Lot 2, fiabilisation | AM-4, AM-5, AM-10 | ~4 j·h | Les anomalies majeures sont corrigées, la suite de tests est verte |
| Lot 3, prévention | AM-9 | ~3 j·h | La non-régression est automatisée |
| Lot 4, confiance et conversion | AM-6, AM-7, AM-8 | ~3 j·h | Avis fiables, promotions cohérentes, catalogue utilisable |

Après chaque lot, rejouer la campagne :

```bash
cd .. && docker compose down -v && docker compose up -d
cd quality-audit-team-X && python tools/run_campaign.py
```

L'objectif final est 46 Pass et 0 Fail.

## Quelques points relevés en passant

Ces sujets sortent du périmètre de la campagne, mais nous les avons rencontrés en cours d'audit et ils méritent d'être instruits.

Protection CSRF. Aucun jeton anti-CSRF n'apparaît sur les formulaires de connexion, de panier ou de checkout. À investiguer en priorité lors d'un audit de sécurité.

Identité de l'appelant API. Une clé unique et partagée agit au nom d'`alice@example.com`, comme expliqué dans AM-10. Un mécanisme d'identification par utilisateur est nécessaire avant toute ouverture de l'API.

Concurrence d'accès. Non testée. Deux commandes simultanées sur le dernier article pourraient aggraver BUG-004. AM-4 le prévoit, mais cela reste à vérifier.

Tests utilisateurs. La section 6 du brief n'a pas été réalisée. À mener pour objectiver le ressenti, en particulier sur le tunnel de commande.

Horodatages. Le code utilise `datetime.utcnow()`, une méthode dépréciée, ce qui produit des avertissements à chaque exécution et laisse une ambiguïté sur le fuseau horaire.
