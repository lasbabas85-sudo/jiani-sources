# 📋 DÉCOUVERTE TEMPLATE MULTILINGUE — Analyse

## Résumé trouvé

**Sur la machine de dev** (non le VPS `bas@vps.jiani.dev`) :

### Fichiers existants
```
/opt/data/eval-jiani/generated/
├── dashboard_charge.html        (499 lignes, 20 KB) — Version FR générique
├── dashboard_charge_en.html     (597 lignes, 25 KB) — Version EN (copie FR, prête pour traduction)
└── dashboard_charge_zh.html     (597 lignes, 25 KB) — Version ZH (VRAIE TRADUCTION CHINOISE)
```

### Structure technique

**Tous les 3 templates contiennent :**
- `const SEANCES = [...]` — Données JSON réelles Notion (ligne 247)
- `const LABELS = {...}` — Dictionnaire labels UI
- Reste du code (charting, logique) — **identique**

### Différences clés

| Élément | `_en.html` | `_zh.html` |
|---------|-----------|-----------|
| `<html lang>` | `en-US` | `zh-CN` |
| `<title>` | 🟡 Mélange (FR + EN) | ✅ Full CH `训练负荷` |
| `h1`, headers | 🟡 Mélange (FR + EN) | ✅ Full CH `训练负荷追踪` |
| `LABELS` object | 🟡 Mélange (FR + EN) | ✅ **Entièrement en chinois** |
| `const SEANCES` | ✅ Données réelles | ✅ Données réelles |

### Exemple de `LABELS` chinois (zh)
```javascript
const LABELS = {
  "unit": "单位",
  "avgSeasonPattern": "本赛季平均：每周 {v}",
  "zoneTarget": "达标",
  "zoneLow": "训练量偏低",
  "zoneWarn": "需要关注",
  "zoneDanger": "风险较高",
  "acwrInsufficientPattern": "数据不足 —— 目前有 {v}/28 天完整数据，需累积4周完整数据才能计算此指标。",
  "monoInsufficient": "数据不足 —— 需要近7天中至少6天有完整训练记录。",
  // ... 12 clés au total
};
```

---

## Stratégie pour intégrer `_zh`

### Option A : Utiliser le template v3 existant (RECOMMANDÉ)

1. **Extraire l'objet `LABELS` chinois** du template `_zh.html` existant
2. **Créer une variable de template** dans le générateur :
   ```python
   LABELS_ZH = {...}  # Le dictionnaire chinois
   LABELS_EN = {...}  # Le dictionnaire français (ou anglais futur)
   ```
3. **Modifier `generate_dashboard.py`** pour supporter `--language` ou générer les deux fichiers :
   ```bash
   generate_dashboard.py --notion-token TOKEN --output ~/generated/ --languages en,zh
   ```
4. **Utiliser le même template HTML** pour les deux versions, remplacer uniquement :
   - `const LABELS = {FR labels}` → `const LABELS = {ZH labels}`
   - `<html lang="...">` et `<title>` selon la langue

### Option B : Trois fichiers template séparés (plus simple maintenant, mais moins maintenable)

- `dashboard_charge_v2_template_en.html` (FR pour l'instant)
- `dashboard_charge_v2_template_zh.html` (CH existant)
- Générer les deux à chaque cron (double appel Python)

---

## Prochaines étapes (toi)

1. **Décision** : Option A (multilingue + 1 template) ou Option B (3 templates séparés) ?
2. **Si Option A** : Je refactorise `generate_dashboard.py` pour supporter `--languages` et crée la structure LABELS dicts
3. **Si Option B** : Je crée un wrapper dans `run_dashboard.sh` qui appelle le générateur 2 fois (une pour `_en`, une pour `_zh`)

---

## Données trouvées

- ✅ Template ZH complet → copié à `jiani-sources/scripts/dashboard_charge_v2_template_zh.html`
- ✅ LABELS chinois extrait et préservé
- ✅ Données JSON réelles confirmées dans les 3 fichiers
- ✅ Pas de dépendance externe (tout est self-contained)

---

## Note sur le VPS

Le script `vps-template-discovery.sh` n'a rien trouvé sur **cette machine** car :
- Pas de `/home/bas/` — c'est un environnement de dev (`/opt/data`)
- Pas de VPS accessible en SSH depuis ici
- **La vraie découverte** : les templates multilingues **existent déjà localement** et n'ont pas besoin de reconnaissance VPS

Le VPS recevra les fichiers générés via le script `install-dashboard.sh` (qui télécharge depuis GitHub).
