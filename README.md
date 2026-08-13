# jiani-sources

Mémoire durable des sources scientifiques pour Jiani Pan (U14 elite tennis).

## Structure

- **sources/pmid/** — Articles PubMed (1 fichier .md par PMID)
- **sources/cssr/** — Documents CSSR ITF (1 fichier .md par CSSR)
- **sources/pdfs/** — Fichiers fédéraux référencés
- **data/** — Exports CSV (sources.csv, cssr.csv)
- **indices/** — Index par pertinence, thème, timeline

## Données validées

- **46 PMID** (PubMed articles)
- **72 CSSR** (ITF Coaching & Sport Science Resources)
- **Vérification:** 2026-08-13
- **Garantie:** Zéro fabrication — chaque source vérifiée avant ajout

## Taxonomie pertinence

| Niveau | PMID | CSSR | Total |
|--------|------|------|-------|
| 🟢🟢🟢 TRES HAUTE | 0 | 21 | 21 |
| 🟢🟢 HIGH | 26 | 19 | 45 |
| 🟡 PARTIEL | 17 | 22 | 39 |
| 🔴 NON | 3 | 10 | 13 |
| **TOTAL** | **46** | **72** | **118** |

## Usage

```bash
# Lister toutes les sources par pertinence
cat data/sources.csv | grep "HIGH"

# Ajouter une nouvelle source
# 1. Créer sources/pmid/XXXXXXXX.md ou sources/cssr/NNN_sujet.md
# 2. Ajouter ligne à data/sources.csv
# 3. Commit + push
```
