# 📊 Dashboard Charge d'Entraînement — Installation & Maintenance

Documentation complète pour installer, configurer, et dépanner le dashboard `dashboard_charge.html` sur le VPS Hetzner.

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Installation rapide](#installation-rapide)
4. [Configuration détaillée](#configuration-détaillée)
5. [Cron job — Comment ça marche](#cron-job--comment-ça-marche)
6. [Relancer manuellement](#relancer-manuellement)
7. [Dépannage](#dépannage)
8. [Logs et monitoring](#logs-et-monitoring)

---

## Vue d'ensemble

Le dashboard `dashboard_charge.html` affiche :
- **Charge hebdomadaire** (UA = Unités Arbitraires)
- **ACWR** (ratio charge aiguë / charge chronique)
- **Indice de monotonie** (avec 3 zones : OK/Vigilance/Danger)

**Données source :** La base Notion "Séances" (database ID `3824293d-742f-8084-945c-000b885a1b37`)

**Fichier généré :** `~/generated/dashboard_charge_en.html` (contenu en français pour l'instant)

**Mise à jour :** Automatique chaque jour à **6:00 AM UTC** (cron job)

---

## Architecture

```
VPS Hetzner (bas@vps.jiani.dev)
│
├─ ~/.env                                  # Token Notion
├─ ~/dashboard/
│  ├─ generate_dashboard.py               # Script Python (téléchargé de GitHub)
│  ├─ run_dashboard.sh                    # Wrapper pour cron
│  └─ dashboard_last_run.log              # Logs de chaque exécution
│
├─ ~/generated/
│  ├─ dashboard_charge_en.html            # Fichier généré (renommage, contenu FR)
│  └─ dashboard_charge_zh.html            # À intégrer ultérieurement (template v3)
│
└─ crontab
   └─ 0 6 * * * ~/dashboard/run_dashboard.sh  # Exécution quotidienne
```

---

## Installation rapide

**Prérequis :**
- Python 3.7+ avec module `requests`
- Token Notion valide (stocké dans `~/.env`)
- Accès curl vers `api.notion.com`

**Commande unique :**

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/lasbabas85-sudo/jiani-sources/main/scripts/install-dashboard.sh)
```

Cela va :
1. ✅ Télécharger `generate_dashboard.py` depuis GitHub
2. ✅ Créer le wrapper `run_dashboard.sh`
3. ✅ Installer le cron job
4. ✅ Vérifier que tout fonctionne

---

## Configuration détaillée

### 1. Token Notion

**Fichier :** `~/.env`

```bash
NOTION_API_TOKEN=secret_123abc...
```

Le token doit avoir l'accès en lecture/écriture sur la database Séances.

**Vérification :**
```bash
curl -s -H "Authorization: Bearer $NOTION_API_TOKEN" \
  https://api.notion.com/v1/users/me | jq .object
```

Doit retourner `"user"` (pas une erreur 401).

### 2. Chemins d'accès

Édite les variables dans `install-dashboard.sh` si tes chemins sont différents :

```bash
INSTALL_DIR="$HOME/dashboard"           # Où vit le script
OUTPUT_HTML="$HOME/public_html/dashboard_charge.html"  # Où est généré le HTML
```

Par défaut, supposent :
- `~/dashboard/` existe
- `~/public_html/` est la racine web (adapt si c'est `/var/www/html` ou autre)

### 3. Cron schedule

Le script s'exécute **6:00 AM UTC** chaque jour. Pour changer :

```bash
crontab -e
```

Trouve la ligne :
```
0 6 * * * /home/bas/dashboard/run_dashboard.sh
```

Modifie le `0 6` :
- `0 3` = 3:00 AM
- `30 22` = 22:30 (10:30 PM)
- `*/2 * * * *` = Toutes les 2 heures

Sauve (`:wq` en vi).

---

## Cron job — Comment ça marche

Le cron execute **une seule commande** à **6:00 AM** :

```bash
/home/bas/dashboard/run_dashboard.sh
```

Ce script fait :

1. **Charge les variables d'env** depuis `~/.env`
   ```bash
   source ~/.env
   ```

2. **Appelle le générateur Python** avec le token + chemin de sortie
   ```bash
   python3 generate_dashboard.py --notion-token $NOTION_API_TOKEN --output $OUTPUT_HTML
   ```

3. **Enregistre le résultat** dans `dashboard_last_run.log`
   ```bash
   [2026-09-04 06:00:15] Starting dashboard generation...
   [2026-09-04 06:00:18] ✓ Dashboard generated successfully
   Output: /home/bas/public_html/dashboard_charge.html (12345 bytes)
   ```

---

## Relancer manuellement

Tu n'as **pas besoin** d'attendre 6:00 AM pour tester. Relance à la demande :

```bash
cd ~/dashboard
./run_dashboard.sh
```

Ou avec logs affichés en temps réel :

```bash
./run_dashboard.sh | tail -20
```

### Test rapide après installation

```bash
# Vérifier que le script est exécutable
ls -la ~/dashboard/run_dashboard.sh

# Exécuter une fois pour tester
~/dashboard/run_dashboard.sh

# Vérifier que le HTML a été généré
ls -lh ~/public_html/dashboard_charge.html

# Vérifier qu'il contient du JSON valide (pas le placeholder {{SEANCES_JSON}})
grep -c "{{SEANCES_JSON}}" ~/public_html/dashboard_charge.html  # Doit afficher 0
grep -c "const SEANCES = \[" ~/public_html/dashboard_charge.html  # Doit afficher 1
```

---

## Dépannage

### Problème : Cron job ne s'exécute pas à l'heure prévue

**Diagnostic :**
```bash
# Vérifier que le cron est actif
sudo service cron status

# Vérifier l'entrée dans crontab
crontab -l | grep run_dashboard

# Consulter les logs système du cron
sudo journalctl -u cron --since "today" -f
```

**Solutions :**
- Redémarrer cron : `sudo systemctl restart cron`
- Vérifie que la syntaxe de crontab est correcte (5 colonnes avant la commande)
- Assure-toi que `run_dashboard.sh` est exécutable : `chmod +x ~/dashboard/run_dashboard.sh`

### Problème : "Erreur 401 — Token invalide"

**Diagnostic :**
```bash
# Teste le token directement
curl -s -H "Authorization: Bearer $NOTION_API_TOKEN" \
  https://api.notion.com/v1/users/me
```

Si erreur 401 ou vide :
```bash
# Vérifier que .env est readable et chargé
cat ~/.env | grep NOTION_API_TOKEN

# Vérifier que le token n'a pas été copié mal
echo $NOTION_API_TOKEN | wc -c  # Doit être ~50 caractères
```

**Solution :**
- Récupère un nouveau token Notion (Settings → Connections → Create integration)
- Mets-le à jour dans `~/.env`
- Relance le test curl ci-dessus

### Problème : "Données insuffisantes" ou pas de graphique

**Diagnostic :**
```bash
# Vérifier le log de dernière exécution
tail -20 ~/dashboard/dashboard_last_run.log

# Vérifier que le HTML contient bien du JSON
grep "const SEANCES = " ~/public_html/dashboard_charge.html | head -c 200
```

**Causes possibles :**
1. **Aucune séance dans Notion** — crée quelques séances de test
2. **Données manquantes** — chaque séance doit avoir : date, durée (min), intensité perçue (RPE)
3. **Database ID incorrect** — vérifie l'ID dans `generate_dashboard.py` ligne ~15

### Problème : "Permission denied" ou champ vide dans log

**Diagnostic :**
```bash
# Vérifier que .env existe et est lisible
ls -la ~/.env

# Vérifier les permissions
stat ~/.env
# Doit montrer que tu peux lire (r--)

# Vérifier que le répertoire de sortie est inscriptible
ls -la ~/public_html/
# Doit montrer que tu peux écrire (rwx)
```

**Solution :**
```bash
# Corriger les permissions
chmod 644 ~/.env
chmod 755 ~/public_html/
```

---

## Logs et monitoring

### Voir les logs de dernière exécution

```bash
cat ~/dashboard/dashboard_last_run.log
```

Affiche quelque chose comme :
```
[2026-09-04 06:00:15] Starting dashboard generation...
Fetching seances from Notion...
  Found 34 seances
[2026-09-04 06:00:18] ✓ Dashboard generated successfully
Output: /home/bas/public_html/dashboard_charge.html (12345 bytes)
```

### Suivre les logs en temps réel

```bash
tail -f ~/dashboard/dashboard_last_run.log
```

Appuie sur `Ctrl+C` pour arrêter.

### Historique complet des exécutions

```bash
# Tous les logs depuis hier
grep "Starting dashboard" ~/dashboard/dashboard_last_run.log | tail -10

# Chercher les erreurs
grep "FAILED\|Error\|✗" ~/dashboard/dashboard_last_run.log
```

### Vérifier que ça marche

```bash
# Le fichier HTML existe et est à jour ?
ls -lh ~/generated/dashboard_charge_en.html

# Il contient du vrai JSON (pas le placeholder) ?
grep -c "{{SEANCES_JSON}}" ~/generated/dashboard_charge_en.html
# Doit afficher: 0 (pas de placeholder non remplacé)

# Compter le nombre de séances dans le JSON
grep -o '"date"' ~/generated/dashboard_charge_en.html | wc -l
# Doit afficher > 0
```

---

## Maintenance régulière

### Mettre à jour le script depuis GitHub

Le script se télécharge automatiquement à chaque installation. Pour mettre à jour manuellement :

```bash
curl -fsSL https://raw.githubusercontent.com/lasbabas85-sudo/jiani-sources/main/scripts/generate_dashboard.py \
  -o ~/dashboard/generate_dashboard.py
chmod +x ~/dashboard/generate_dashboard.py
```

### Nettoyer les anciens logs

```bash
# Garder seulement les 100 dernières lignes
tail -100 ~/dashboard/dashboard_last_run.log > ~/dashboard/dashboard_last_run.log.tmp
mv ~/dashboard/dashboard_last_run.log.tmp ~/dashboard/dashboard_last_run.log
```

Ou avec logrotate (configurable dans cron) :

```bash
# Ajouter à crontab (une fois par semaine, dimanche 23:00)
55 23 * * 0 tail -200 ~/dashboard/dashboard_last_run.log > /tmp/log.tmp && mv /tmp/log.tmp ~/dashboard/dashboard_last_run.log
```

---

## Checklist rapide avant problème signalé à Claude

Avant de demander de l'aide :

- [ ] `crontab -l | grep run_dashboard` — la ligne existe ?
- [ ] `tail ~/dashboard/dashboard_last_run.log` — dernière exécution réussie (✓) ou échouée (✗) ?
- [ ] `ls -lh ~/public_html/dashboard_charge.html` — fichier existe et > 10 KB ?
- [ ] `curl -s -H "Authorization: Bearer $NOTION_API_TOKEN" https://api.notion.com/v1/users/me | jq .` — token valide (retourne un objet, pas erreur 401) ?
- [ ] `grep "{{SEANCES_JSON}}" ~/public_html/dashboard_charge.html | wc -l` — affiche 0 (pas de placeholder) ?

Si tout ✅ : le dashboard fonctionne, le problème est probablement côté affichage/web.

---

## Support

**Documenté dans :** Journal Technique Jiani → "Règle 9 — Wrappers Notion"

**Questions fréquentes :** Voir section "Dépannage" ci-dessus.

**Contact :** Partage de la page avec Patrick (Notion, page "Partagé — Patrick (suivi charge)")
