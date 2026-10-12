# Anomalies relevees — QuickOrder V3.1

13 anomalies reproductibles, classees par severite decroissante.

| ID | Titre | Severite | Priorite | Cas de test |
|---|---|---|---|---|
| [BUG-005](BUG-005-paypal-double-commande.md) | Un paiement PayPal cree systematiquement deux commandes identiques | Bloquante | P0 | RM05, RM16 |
| [BUG-002](BUG-002-restaurant-ferme.md) | Un restaurant ferme accepte les commandes | Critique | P1 | RM02 |
| [BUG-003](BUG-003-produit-rupture-commandable.md) | Un produit en rupture de stock reste commandable | Critique | P1 | RM03, RM14 |
| [BUG-006](BUG-006-paiement-especes-insuffisant.md) | Un paiement en especes inferieur au montant du est accepte et marque paye | Critique | P1 | RM06 |
| [BUG-010](BUG-010-subtotal-client-non-verifie.md) | L'API de validation des coupons fait confiance au montant transmis par le client | Critique | P1 | RM10 |
| [BUG-001](BUG-001-minimum-commande-non-applique.md) | Le montant minimum de commande annonce par le restaurant n'est jamais applique | Majeure | P1 | RM01, RM15 |
| [BUG-004](BUG-004-stock-negatif.md) | Le stock devient negatif apres une commande superieure aux quantites disponibles | Majeure | P1 | RM04 |
| [BUG-007](BUG-007-coupon-atlas15-taux-incoherent.md) | La promotion ATLAS15 est annoncee a 15 % mais n'applique que 10 % | Majeure | P2 | RM07 |
| [BUG-008](BUG-008-filtre-livraison-inverse.md) | Le filtre frais de livraison maximum retourne exactement l'inverse du resultat attendu | Majeure | P2 | RM08 |
| [BUG-011](BUG-011-avis-sans-commande.md) | Un client peut noter un restaurant ou il n'a jamais commande | Majeure | P2 | RM11 |
| [BUG-012](BUG-012-transition-statut-invalide.md) | Le back-office accepte des transitions de statut impossibles | Majeure | P2 | RM12 |
| [BUG-009](BUG-009-recherche-ignore-description.md) | La recherche ignore la description des restaurants | Mineure | P3 | RM09 |
| [BUG-013](BUG-013-api-expose-restaurants-fermes.md) | L'API liste les restaurants fermes sans possibilite de les filtrer | Mineure | P3 | RM13 |

## Repartition par severite

| Severite | Nombre |
|---|---|
| Bloquante | 1 |
| Critique | 4 |
| Majeure | 6 |
| Mineure | 2 |
| Total | 13 |
