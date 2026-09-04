# 📋 REVIEW PRÉ-DÉPLOIEMENT VPS — Refactorisation multilingue (Option A)

## Commit : `f8c0751`

### ✅ Vérifications complétées

#### 1. **Intégrité des templates**
- ✓ `dashboard_charge_en.html` : 501 lignes, {{SEANCES_JSON}} × 1, {{GENERATED_AT}} × 1
- ✓ `dashboard_charge_zh.html` : 501 lignes, {{SEANCES_JSON}} × 1, {{GENERATED_AT}} × 1
- ✓ Monotonie 3-zone (targetMax:1.5, warnMax:2) présent dans les deux
- ✓ Aucune donnée figée, uniquement placeholders

#### 2. **Refactorisation generate_dashboard.py**

**Arguments (nouveau format) :**
```bash
python3 generate_dashboard.py \
  --notion-token <TOKEN> \
  --output-dir ~/generated \
  --languages en,zh              # default, comma-separated
```

**Changements clés :**
- ✓ `--output-dir` remplace `--output` (output dir, pas fichier unique)
- ✓ `--languages` argument optionnel, défaut "en,zh"
- ✓ `LANGUAGE_TEMPLATES` dict mappe langues → fichiers template
- ✓ `generate_dashboard_for_language()` fonction par langue
- ✓ Une seule fetch Notion, injection JSON dupliquée pour toutes les langues
- ✓ Logging par langue : `[EN]` / `[ZH]` prefixes

**Flux d'exécution :**
```
generate_dashboard(token, output_dir, ["en", "zh"])
  └─ Fetch Notion seances (1 seule fois)
  └─ For each language in ["en", "zh"]:
       ├─ Load template: dashboard_charge_{language}.html
       ├─ Replace {{SEANCES_JSON}} + {{GENERATED_AT}}
       ├─ Write: ~/generated/dashboard_charge_{language}.html
       └─ Log: [EN] / [ZH] success
```

#### 3. **Refactorisation install-dashboard.sh (wrapper cron)**

**Avant (monolingue) :**
```bash
python3 generate_dashboard.py --notion-token TOKEN --output ~/generated/dashboard_charge_en.html
```

**Après (multilingue) :**
```bash
python3 generate_dashboard.py \
  --notion-token TOKEN \
  --output-dir ~/generated \
  --languages "en,zh"
```

**Impact :**
- ✓ Une seule exécution produit les deux fichiers
- ✓ Log reflète les deux outputs (affiche sizes des deux fichiers)
- ✓ Bash syntax validée (`bash -n`)

#### 4. **Vérifications syntaxe**
- ✓ `generate_dashboard.py` : Python syntax OK, imports valides
- ✓ `install-dashboard.sh` : Bash syntax OK, pas de `fi` en trop
- ✓ Structure script-templates linkage : ✓ OK

---

## 📊 Différences avec l'ancienne approche (monolingue)

| Point | Avant | Après |
|-------|-------|-------|
| **Appel cron** | `--output dashboard_charge_en.html` | `--output-dir ~/generated --languages en,zh` |
| **Fichiers générés** | 1 seul (_en) | 2 fichiers (_en + _zh) en 1 exécution |
| **Fetch Notion** | 1 fetch | 1 fetch (partagée entre les 2 langues) |
| **Templates chargées** | 1 template (v2_template.html) | 2 templates (dashboard_charge_en.html + zh) |
| **Cron job durée** | T secondes | ~T secondes (pas d'overhead, fetch partagée) |

---

## 🚀 Flux de déploiement sur le VPS

**1. Installation via install-dashboard.sh :**
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/lasbabas85-sudo/jiani-sources/main/scripts/install-dashboard.sh)
```

**2. Cron job créé :**
```bash
0 6 * * * ~/dashboard/run_dashboard.sh >> ~/dashboard/dashboard_last_run.log 2>&1
```

**3. À 6:00 AM chaque jour, cron exécute :**
```bash
~/dashboard/run_dashboard.sh
  └─ python3 ~/dashboard/generate_dashboard.py \
       --notion-token $NOTION_API_TOKEN \
       --output-dir ~/generated \
       --languages "en,zh"
    └─ Génère:
       - ~/generated/dashboard_charge_en.html
       - ~/generated/dashboard_charge_zh.html
    └─ Log: ~/dashboard/dashboard_last_run.log
```

**4. Résultat visible dans les URLs :**
```
https://bas.jiani.dev/generated/dashboard_charge_en.html   ← Version FR (renommage _en)
https://bas.jiani.dev/generated/dashboard_charge_zh.html   ← Version chinoise
```

---

## ⚠️ Notes importantes avant déploiement

1. **VPS prerequisites :**
   - Python 3 + pip
   - `pip install requests` (présent dans install-dashboard.sh)
   - Répertoire `~/generated/` créé par le script

2. **Notion token :**
   - Doit être dans `~/.env` (créé par install-dashboard.sh ou à ajouter manuellement)
   - Format : `NOTION_API_TOKEN=secret_...`

3. **Templates sources :**
   - Script télécharge les templates depuis GitHub `/main/scripts/`
   - Si tu modifies les templates, pousse sur GitHub avant le déploiement

4. **Compatibilité backwards :**
   - Ancien format `--output <file>` ne fonctionne plus
   - Si vous aviez un autre script l'appelant, à mettre à jour

5. **Extensibilité :**
   - Pour ajouter `--languages en,zh,fr` plus tard :
     1. Créer `dashboard_charge_fr.html` depuis le template générateur
     2. Ajouter `"fr": "dashboard_charge_fr.html"` à `LANGUAGE_TEMPLATES`
     3. Lancer : `python3 generate_dashboard.py --languages en,zh,fr`

---

## ✓ À toi de vérifier

Avant push VPS, tu dois vérifier :

1. **Sur cette machine :**
   ```bash
   cd /opt/data/jiani-sources
   git log --oneline -2  # Doit montrer commit f8c0751
   ls -lh scripts/dashboard_charge_{en,zh}.html  # Doit exister
   grep "{{SEANCES_JSON}}" scripts/dashboard_charge_{en,zh}.html  # Doit trouver 1 chacun
   ```

2. **Syntaxe :**
   ```bash
   bash -n scripts/install-dashboard.sh  # Doit OK
   python3 -m py_compile scripts/generate_dashboard.py  # Doit OK
   ```

3. **Logique :**
   - Télécharger les 2 templates depuis GitHub et vérifier le contenu
   - Vérifier que les labels chinois sont dans le bon fichier

---

## 🎯 Prochaines étapes

- [ ] Tu vérifies les points ci-dessus
- [ ] Une fois OK, je peux déployer sur le VPS Hetzner
- [ ] Post-déploiement : test cron + validation des deux fichiers générés

---

**Commit GitHub :** `f8c0751`
**Date vérification locale :** 2026-09-04
**Status :** ✅ Prêt pour review utilisateur
