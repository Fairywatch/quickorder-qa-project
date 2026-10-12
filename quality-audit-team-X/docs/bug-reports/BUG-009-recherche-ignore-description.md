# BUG-009 — La recherche ignore la description des restaurants

| | |
|---|---|
| Identifiant | BUG-009 |
| Severite | Mineure |
| Priorite | P3 |
| Risque couvert | R10 (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | RM09 |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

La recherche de la page d'accueil ne porte que sur le nom du restaurant. Les mots figurant dans la description, qui decrivent pourtant l'offre culinaire, ne remontent aucun resultat.

## Preconditions

- Pizza Roma a pour description : Pizzas romaines, pates et desserts italiens.
- Le mot romaines n'apparait que dans cette description, dans aucun nom

## Etapes de reproduction

1. Controle : GET /?q=pizza (le mot figure dans le nom Pizza Roma)
2. Cible : GET /?q=romaines (le mot figure seulement dans la description)
3. Comparer les deux resultats

## Resultat attendu

Pizza Roma remonte dans les deux cas : la recherche couvre le nom et la description.

## Resultat obtenu

q=pizza retourne bien Pizza Roma, ce qui confirme que la recherche fonctionne sur le nom. q=romaines ne retourne aucun resultat : la description est totalement ignoree.

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

Cas RM09 — Recherche par mot-cle portant sur le nom et la description

```
GET /?q=pizza --> ['Pizza Roma']
GET /?q=romaines --> []
```

## Impact

Le client qui cherche un type de cuisine par mot-cle ne trouve pas les restaurants correspondants. Perte de trafic sur le catalogue, d'autant que la description est le seul champ decrivant reellement l'offre.
