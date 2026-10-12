# BUG-012 — Le back-office accepte des transitions de statut impossibles

| | |
|---|---|
| Identifiant | BUG-012 |
| Severite | Majeure |
| Priorite | P2 |
| Risque couvert | R9 (voir [risk-matrix.md](../risk-matrix.md)) |
| Cas de test | RM12 |
| Version | QuickOrder V3.1 (Docker) |
| Environnement | http://127.0.0.1:5000 — base reinitialisee |
| Date de detection | 22/09/2026 |
| Statut | Ouvert |

## Contexte

L'administrateur peut affecter n'importe quel statut a une commande, sans controle du cycle de vie. Une commande deja livree peut redevenir confirmee, ou etre annulee apres livraison.

## Preconditions

- La commande 1 est au statut delivered (donnees de demonstration)
- Compte administrateur admin@quickorder.local

## Etapes de reproduction

1. Se connecter comme administrateur
2. POST /admin/orders/1/status avec status=confirmed
3. Relire le statut : GET /api/orders/1

## Resultat attendu

La transition est refusee : une commande livree ne peut pas revenir a un statut anterieur.

## Resultat obtenu

Le statut passe de delivered a confirmed et le message Statut mis a jour s'affiche.

## Preuve

Extraits du journal d'execution ([`evidence/raw-log.md`](../evidence/raw-log.md)), requetes
reellement envoyees et reponses reellement recues :

Cas RM12 — Refus des transitions de statut impossibles (livree -> confirmee)

```
POST /admin/orders/1/status (status=confirmed)
--> HTTP 200
statut avant=confirmed / après=confirmed
flash: ['Statut mis à jour.']
```

## Impact

Le suivi des commandes perd toute fiabilite : indicateurs fausses, commandes livrees reinjectees dans la file de preparation, litiges impossibles a arbitrer sur la base des statuts.
