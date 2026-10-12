# BUG-008 — Le filtre frais de livraison maximum retourne exactement l'inverse du resultat attendu

| | |
|---|---|
| Identifiant | BUG-008 |
| Severite | Majeure |
| Priorite | P2 |
| Risque couvert | R10 (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | RM08 |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

Sur la page d'accueil, le filtre des frais de livraison maximum selectionne les restaurants dont les frais sont superieurs ou egaux au seuil, au lieu d'inferieurs ou egaux. Le resultat est systematiquement l'inverse de la demande.

## Preconditions

- Frais de livraison : Green Kitchen 1,99 - Pizza Roma 2,49 - Burger Factory 2,99 - Couscous Atlas 2,99 - Tokyo Bowl 3,49

## Etapes de reproduction

1. Demander les restaurants a 2,50 EUR maximum : GET /?max_delivery=2.50
2. Comparer la liste obtenue aux frais reels

## Resultat attendu

Green Kitchen (1,99 EUR) et Pizza Roma (2,49 EUR) uniquement.

## Resultat obtenu

Burger Factory, Couscous Atlas, Night Sushi et Tokyo Bowl : exactement les restaurants dont les frais DEPASSENT 2,50 EUR. Les deux seuls restaurants correspondant reellement au critere sont exclus.

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

Cas RM08 — Filtre 'frais de livraison maximum' sur la page d'accueil

```
GET /?max_delivery=2.50
--> HTTP 200
Restaurants affiches : ['Burger Factory', 'Couscous Atlas', 'Night Sushi', 'Tokyo Bowl']
```

## Impact

Le client sensible au prix se voit presenter les options les plus cheres et n'a aucun moyen de trouver les moins cheres. Perte de conversion directe sur un filtre mis en avant dans l'interface.
