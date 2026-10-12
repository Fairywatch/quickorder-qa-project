# BUG-011 — Un client peut noter un restaurant ou il n'a jamais commande

| | |
|---|---|
| Identifiant | BUG-011 |
| Severite | Majeure |
| Priorite | P2 |
| Risque couvert | R8 (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | RM11 |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

Le depot d'un avis ne verifie pas que l'auteur a deja commande chez le restaurant concerne. Toute personne disposant d'un compte peut noter n'importe quel etablissement, autant de fois qu'elle le souhaite.

## Preconditions

- Compte bob@example.com, qui n'a jamais commande chez Couscous Atlas (id 5)

## Etapes de reproduction

1. Se connecter avec bob@example.com
2. Deposer un avis : POST /restaurant/5/review avec rating=5 et un commentaire

## Resultat attendu

Le depot est refuse : aucune commande n'a ete passee chez ce restaurant.

## Resultat obtenu

L'avis est enregistre et le message Merci pour votre avis ! est affiche.

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

Cas RM11 — Depot d'un avis reserve aux clients ayant commande

```
POST /restaurant/5/review (Bob, aucune commande chez ce restaurant)
--> HTTP 200
flash: ['Merci pour votre avis !', 'Promotion annoncée : 🎟️ Code ATLAS15 annoncé comme -15% sur ce restaurant']
```

## Impact

Les notes des restaurants ne sont pas fiables : elles peuvent etre gonflees ou sabotees a volonte. Or la note est le principal critere de choix du client et le critere de tri par defaut de la page d'accueil.
