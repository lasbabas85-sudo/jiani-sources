# 🚀 DEPLOYMENT GUIDE — VPS Hetzner

## Pré-requis

- Accès SSH au VPS : `ssh bas@vps.jiani.dev`
- Utilisateur `bas` (ou root, c'est le compte de déploiement)
- Python 3 + pip disponibles
- Internet pour télécharger depuis GitHub

## Étapes de déploiement

### 1. Vérifications locales (cette machine)

Avant de déployer sur le VPS, exécute le test local :

```bash
bash scripts/test_pre_deployment.sh
```

**Résultat attendu :**
```
=== ALL TESTS PASSED ===

Ready for VPS deployment:
  ✓ Bash scripts syntax-valid
  ✓ Python script structure-valid
  ✓ Single Notion API fetch (not 2x)
  ✓ Multilingual templates present
  ✓ No stale variable references
  ✓ Monotonie 3-zone fix in both versions
```

✅ Tests OK sur cette machine (commit `28a0629`)

---

### 2. Déploiement sur le VPS

SSH sur le VPS :

```bash
ssh bas@vps.jiani.dev
```

Puis télécharge et exécute l'installateur :

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/lasbabas85-sudo/jiani-sources/main/scripts/install-dashboard.sh)
```

L'installateur fait :
1. Crée `~/dashboard/` (répertoire d'installation)
2. Télécharge `generate_dashboard.py` depuis GitHub
3. Crée `run_dashboard.sh` (wrapper pour cron)
4. Crée `~/.env` (ou avertit si absent — à remplir manuellement)
5. Ajoute le cron job (6:00 AM chaque jour)
6. Vérifie l'installation

**Output attendu :**
```
=== Installation Summary ===
Checks passed: 3/3

📁 Installation directory: /home/bas/dashboard
📂 Output directory: /home/bas/generated
  - dashboard_charge_en.html (generated daily)
  - dashboard_charge_zh.html (generated daily)
📋 Last run log: /home/bas/dashboard/dashboard_last_run.log
⏰ Cron schedule: Daily at 6:00 AM

✅ Installation complete!
```

---

### 3. Configuration manuelle (si nécessaire)

Si `~/.env` n'existe pas, crée-le :

```bash
echo "NOTION_API_TOKEN=ntn_VOTRE_TOKEN_ICI..." >> ~/.env
chmod 600 ~/.env
```

Remplace `ntn_VOTRE_TOKEN_ICI...` par ton token Notion réel.

---

### 4. Test manuel du cron

Une fois l'installation terminée, teste le wrapper manuellement :

```bash
~/dashboard/run_dashboard.sh
```

**Output attendu :**
```
[2026-09-04 HH:MM:SS] Starting dashboard generation (multilingual: en, zh)...
Fetching seances from Notion (shared across all languages)...
  Found 34 seances

[EN] Loading template: dashboard_charge_en.html
[EN] ✓ Dashboard generated: /home/bas/generated/dashboard_charge_en.html
[ZH] Loading template: dashboard_charge_zh.html
[ZH] ✓ Dashboard generated: /home/bas/generated/dashboard_charge_zh.html

[2026-09-04 HH:MM:SS] ✓ All dashboards generated successfully
Output:
  - /home/bas/generated/dashboard_charge_en.html (XXXX bytes)
  - /home/bas/generated/dashboard_charge_zh.html (XXXX bytes)
```

---

### 5. Vérification des fichiers générés

```bash
# Vérifie que les deux fichiers existent
ls -lh ~/generated/dashboard_charge_*.html

# Vérifie qu'ils contiennent du contenu injecté (pas de {{SEANCES_JSON}})
grep -c "{{SEANCES_JSON}}" ~/generated/dashboard_charge_*.html
# ✅ Résultat attendu : 0 pour les deux (placeholders remplacés)

# Vérifie que les données JSON sont présentes
grep -c '"date"' ~/generated/dashboard_charge_en.html
grep -c '"date"' ~/generated/dashboard_charge_zh.html
# ✅ Résultat attendu : > 0 pour les deux (données injectées)

# Vérifie les labels chinois dans la version ZH
grep "训练负荷" ~/generated/dashboard_charge_zh.html
# ✅ Résultat attendu : "Training Load — Jiani" en chinois
```

---

### 6. Vérification du cron job

```bash
# Vérifie que le cron job est bien installé
crontab -l | grep run_dashboard

# Doit afficher :
# 0 6 * * * /home/bas/dashboard/run_dashboard.sh >> /home/bas/dashboard/dashboard_last_run.log 2>&1

# Vérifie le log des dernières exécutions
tail -20 ~/dashboard/dashboard_last_run.log
```

---

## 🔧 Troubleshooting

### Problème : "Permission denied" sur ~/.env

```bash
# Vérifie les permissions
stat ~/.env

# Doit être readable par l'utilisateur `bas`
chmod 600 ~/.env
```

### Problème : "Module not found: requests"

```bash
# Installe les dépendances
pip install requests

# Ou avec pip3 si pip n'existe pas
pip3 install requests
```

### Problème : Fichiers `_en` et `_zh` ne sont pas générés

```bash
# Vérifie le log d'erreur
tail -50 ~/dashboard/dashboard_last_run.log

# Teste le script directement avec debug
python3 ~/dashboard/generate_dashboard.py \
  --notion-token "$(cat ~/.env | grep NOTION_API_TOKEN | cut -d= -f2)" \
  --output-dir ~/generated \
  --languages "en,zh"
```

### Problème : Données vides ({{SEANCES_JSON}} reste dans le fichier)

```bash
# Vérifie que le token Notion est valide
echo $NOTION_API_TOKEN

# Teste la connexion Notion
python3 << 'PYEOF'
import requests
import os

token = os.getenv("NOTION_API_TOKEN")
if not token:
    print("✗ Token not found in environment")
else:
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"}
    try:
        r = requests.get("https://api.notion.com/v1/search", headers=headers)
        if r.status_code == 200:
            print("✓ Notion API connection OK")
        else:
            print(f"✗ Notion API error: {r.status_code} — {r.text}")
    except Exception as e:
        print(f"✗ Connection error: {e}")
PYEOF
```

---

## 📊 Vérification post-déploiement

Après que le cron ait tourné au moins une fois (6:00 AM ou après un test manuel) :

```bash
# 1. Fichiers existent et ont du contenu
ls -lh ~/generated/dashboard_charge_*.html
# ✅ Chaque fichier > 10 KB

# 2. Pas de placeholders résiduels
grep "{{SEANCES_JSON}}\|{{GENERATED_AT}}" ~/generated/dashboard_charge_*.html
# ✅ Aucune correspondance

# 3. Données JSON présentes
head -1 ~/generated/dashboard_charge_en.html | grep -o '"date"' | wc -l
# ✅ > 0 (des dates trouvées dans le JSON)

# 4. Labels chinois dans ZH
grep "操作计划\|单位\|目标" ~/generated/dashboard_charge_zh.html | wc -l
# ✅ > 0 (des labels en chinois trouvés)

# 5. Cron logs montrent succès
tail -5 ~/dashboard/dashboard_last_run.log | grep "✓ All dashboards"
# ✅ Message de succès visible
```

---

## 📋 Checklist finale

Avant de déclarer le déploiement complet :

- [ ] Test local (`test_pre_deployment.sh`) ✅ PASS
- [ ] SSH sur le VPS OK
- [ ] `install-dashboard.sh` exécuté sans erreur
- [ ] `~/.env` créé avec token Notion valide
- [ ] `~/dashboard/run_dashboard.sh` exécuté manuellement avec succès
- [ ] Les deux fichiers `_en.html` et `_zh.html` générés et contiennent du contenu
- [ ] Aucun `{{placeholder}}` résiduel
- [ ] Cron job visible dans `crontab -l`
- [ ] Log du cron montre executions réussies

---

## 🎯 Résultat attendu

**Deux fichiers générés chaque jour à 6:00 AM :**

```
https://bas.jiani.dev/generated/dashboard_charge_en.html   ← Version FR (renommée _en)
https://bas.jiani.dev/generated/dashboard_charge_zh.html   ← Version ZH (complète traduction chinoise)
```

Chaque fichier contient :
- ✅ Graphique "Charge d'entraînement" (Training Load)
- ✅ Graphique "ACWR" (Acute:Chronic Workload Ratio)
- ✅ Graphique "Indice de monotonie" avec 3 zones (OK < 1.5, Vigilance 1.5–2, Danger ≥2)
- ✅ Données injectées depuis Notion (pas de placeholders)
- ✅ Timestamp de génération (UTC)
- ✅ Labels localisés (FR pour `_en.html`, ZH pour `_zh.html`)

---

**Auteur :** Claude (Hermes AI)
**Date :** 2026-09-04
**Commit :** `28a0629` (test script) + `31f2ff3` (fixes)
**Status :** ✅ Prêt pour déploiement VPS
