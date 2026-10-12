# BUG-013 — L'API liste les restaurants fermes sans possibilite de les filtrer

| | |
|---|---|
| Identifiant | BUG-013 |
| Severite | Mineure |
| Priorite | P3 |
| Risque couvert | R11 (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | RM13 |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

GET /api/restaurants retourne l'ensemble des restaurants, y compris ceux qui sont fermes, et n'offre aucun parametre permettant de les exclure. Un consommateur de l'API affichera donc des etablissements non commandables.

## Preconditions

- Night Sushi (id 6) a is_open=false

## Etapes de reproduction

1. Appeler GET /api/restaurants avec une cle valide
2. Filtrer la reponse sur is_open=false

## Resultat attendu

Les restaurants fermes sont exclus par defaut, ou un parametre permet de les filtrer.

## Resultat obtenu

Night Sushi est retourne dans la liste. Le champ is_open permet de le detecter, mais aucun filtrage n'est propose par l'API.

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

Cas RM13 — Exposition des restaurants fermes dans la liste API

```
GET /api/restaurants --> count=6
Fermes retournes : ['Night Sushi']
```

## Impact

Chaque client de l'API doit reimplementer ce filtrage. Combine a BUG-002, qui autorise la commande chez un restaurant ferme, le risque d'erreur augmente sensiblement.
