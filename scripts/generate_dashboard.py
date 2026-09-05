#!/usr/bin/env python3
"""
Génère dashboard_charge_v2.html à partir des données Notion (base Séances)
et le publie dans le dossier servi par nginx (eval-jiani-web).

Usage : python3 generate_dashboard.py
À planifier via cron sur le VPS Hetzner, ex. tous les jours à 6h :
    0 6 * * * cd /opt/data/scripts && python3 generate_dashboard.py >> /opt/data/logs/dashboard.log 2>&1

Prérequis :
    Aucun — utilise uniquement la bibliothèque standard Python (urllib), pas besoin de pip.
    Variable d'environnement NOTION_TOKEN (token d'intégration Notion, permissions lecture sur la base Séances)
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# CONFIGURATION — à adapter si besoin
# ---------------------------------------------------------------------------
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "") or os.environ.get("NOTION_API_TOKEN", "")
SEANCES_DATA_SOURCE_ID = "3824293d-742f-8084-945c-000b885a1b37"

# Chemin du template (généré par Claude, à copier une fois sur le serveur)
TEMPLATE_PATH = "/opt/data/scripts/dashboard_charge_v2_template.html"

# Dossier de sortie — servi par le conteneur nginx eval-jiani-web
OUTPUT_DIR = "/opt/data/eval-jiani/generated"

# Une langue = un fichier de sortie. Ajouter/retirer une entrée ici suffit
# pour changer les versions générées (pas besoin de toucher au reste du script).
OUTPUT_FILES = {
    "en": os.path.join(OUTPUT_DIR, "dashboard_charge_en.html"),
    "zh": os.path.join(OUTPUT_DIR, "dashboard_charge_zh.html"),
}

NOTION_API_VERSION = "2025-09-03"
NOTION_QUERY_URL = f"https://api.notion.com/v1/data_sources/{SEANCES_DATA_SOURCE_ID}/query"

# ---------------------------------------------------------------------------
# TRADUCTIONS — tous les textes visibles du dashboard, par langue.
# EN = version technique complète (Bas + préparateur physique)
# ZH = version simplifiée pour parents + Jiani (moins de jargon, pas de
#      citations bibliographiques détaillées dans les sources)
# ---------------------------------------------------------------------------
TRANSLATIONS = {
    "en": {
        "lang": "en",
        "title": "Training Load — Jiani",
        "h1": "Training Load — Jiani",
        "sub": "Load (AU) · ACWR (7-day rolling) · Weekly Monotony",
        "generated_label": "Generated on",
        "source_label": "Source: Notion — Sessions",
        "label_charge": "Load — Last 7 Days",
        "label_acwr": "ACWR (Acute / Chronic)",
        "label_monotony": "Monotony Index",
        "unit": "AU",
        "p1_h2": "Weekly Load (AU)",
        "p1_caption": "Load = session duration (min) \u00d7 perceived exertion (RPE 0\u201310) \u2014 session-RPE method, Foster et al. (2001)",
        "p1_source": "Foster, C. et al. (2001), J Strength Cond Res, 15:109-115 \u2014 calculation method \u00b7 Genevois, Rogowski &amp; Le Solliec (2020), ITF Coaching and Sport Science Review \u2014 tennis application",
        "p2_h2": "ACWR \u2014 Acute:Chronic Workload Ratio",
        "p2_caption": "Acute load = last 7 rolling days \u00b7 Chronic load = average of the preceding 4 weeks",
        "p2_legend_low": "&lt; 0.8 undertraining",
        "p2_legend_ok": "0.8\u20131.3 target zone",
        "p2_legend_warn": "1.3\u20131.5 caution",
        "p2_legend_danger": "&gt; 1.5 elevated risk",
        "p2_source": "Blanch &amp; Gabbett (2016), Br J Sports Med, 50:471-475 \u00b7 Myers et al. (2020), Med Sci Sports Exerc, 52(5):1196-1200 \u2014 junior tennis, ~14 y \u00b7 Moreno-P\u00e9rez et al. (2021), Eur J Sport Sci, 21(8):1215-1223 \u2014 elite junior",
        "p3_h2": "Monotony Index",
        "p3_caption": "Mean daily load \u00f7 standard deviation, 7-day rolling window \u2014 measures training repetitiveness",
        "p3_legend_ok": "\u2264 1.5 recommended",
        "p3_legend_vigilance": "1.5\u20132 caution",
        "p3_legend_danger": "&gt; 2 elevated risk",
        "p3_source": "Formula and threshold: Foster, C. (1998), Med Sci Sports Exerc, 30(7):1164-1168 \u2014 original fixed calendar-week calculation; adapted here to a 7-day rolling window for consistency with ACWR",
        "footer_1": "Dashboard auto-generated from the Notion &quot;Sessions&quot; database \u00b7 Zero manual data entry in this tool",
        "footer_2": "Thresholds sourced \u2014 see SOURCES_DURABLE for full references",
        "avg_season_pattern": "Season avg: {v} AU/week",
        "insufficient_short": "Insufficient data",
        "acwr_days_pattern": "{v}/28 days needed",
        "zone_target": "Target zone",
        "zone_low": "Undertraining",
        "zone_warn": "Caution",
        "zone_danger": "Elevated risk",
        "week_incomplete": "Incomplete week",
        "mono_ok": "OK (\u2264 1.5)",
        "mono_warn": "Caution",
        "mono_above": "Above threshold",
        "no_charge_data": "No usable load data yet (duration + RPE required).",
        "acwr_insufficient_pattern": "Insufficient data \u2014 {v}/28 days of complete load available. ACWR requires 4 full weeks of chronic load to be reliable.",
        "mono_insufficient": "Insufficient data \u2014 monotony requires at least 6 of the last 7 days with recorded load.",
        "date_format": "%d %b %Y, %H:%M",
        "date_format_short": "%d %b %Y",
        "alert_banner_pattern": "\u26a0\ufe0f {type} \u2014 {zone} (reported since {date})",
        "alert_zones": {
            "Lombaires": "Lower back", "Épaule": "Shoulder", "Genou": "Knee",
            "Cheville": "Ankle", "Poignet": "Wrist", "Coude": "Elbow",
            "Ischio-jambiers": "Hamstring", "Mollet": "Calf",
            "Dos (haut)": "Upper back", "Cou": "Neck", "Autre": "Other",
        },
        "alert_types": {
            "Courbature": "Soreness", "Tension": "Tightness", "Douleur": "Pain",
            "Gêne": "Discomfort", "Blessure": "Injury",
        },
        "range_7d": "7 days", "range_1m": "1 month", "range_3m": "3 months",
        "range_6m": "6 months", "range_season": "Full season",
    },
    "zh": {
        "lang": "zh-CN",
        "title": "训练负荷 — Jiani",
        "h1": "训练负荷追踪 — Jiani",
        "sub": "每周负荷 · 急慢性负荷比（7天）· 训练单调指数",
        "generated_label": "生成时间：",
        "source_label": "数据来源：Notion 训练记录",
        "label_charge": "近7天负荷",
        "label_acwr": "急慢性负荷比",
        "label_monotony": "训练单调指数",
        "unit": "单位",
        "p1_h2": "每周训练负荷",
        "p1_caption": "负荷 = 训练时长（分钟）× 自我感觉用力程度（RPE，0-10分）",
        "p1_source": "参考文献：Foster 等（2001）运动训练负荷监测方法",
        "p2_h2": "急慢性负荷比（ACWR）",
        "p2_caption": "比较近期训练量（近7天）与平常训练量（近4周平均），帮助判断训练量变化是否在安全范围内",
        "p2_legend_low": "偏低 —— 训练量不足",
        "p2_legend_ok": "达标 —— 训练量合适",
        "p2_legend_warn": "需要关注 —— 训练量增长较快",
        "p2_legend_danger": "风险较高 —— 建议适当减少训练量",
        "p2_source": "参考文献：青少年网球运动负荷监测相关研究",
        "p3_h2": "训练单调指数",
        "p3_caption": "反映近期训练内容是否过于单一重复，数值越高代表训练变化越少",
        "p3_legend_ok": "正常范围",
        "p3_legend_vigilance": "临界区间 —— 需要关注",
        "p3_legend_danger": "偏高 —— 建议增加训练变化",
        "p3_source": "参考文献：运动训练负荷监测方法（Foster, 1998）",
        "footer_1": "本页面根据训练记录自动生成 · 无需手动录入数据",
        "footer_2": "所有数据标准均有科学文献依据",
        "avg_season_pattern": "本赛季平均：每周 {v}",
        "insufficient_short": "数据不足",
        "acwr_days_pattern": "还需 {v}/28 天数据",
        "zone_target": "达标",
        "zone_low": "训练量偏低",
        "zone_warn": "需要关注",
        "zone_danger": "风险较高",
        "week_incomplete": "本周数据不完整",
        "mono_ok": "正常",
        "mono_warn": "需要关注",
        "mono_above": "偏高",
        "no_charge_data": "暂无可用的训练负荷数据（需要时长和RPE）。",
        "acwr_insufficient_pattern": "数据不足 —— 目前有 {v}/28 天完整数据，需累积4周完整数据才能计算此指标。",
        "mono_insufficient": "数据不足 —— 需要近7天中至少6天有完整训练记录。",
        "date_format": "%Y年%m月%d日 %H:%M",
        "date_format_short": "%m月%d日",
        "alert_banner_pattern": "\u26a0\ufe0f {zone}{type}（自{date}起）",
        "alert_zones": {
            "Lombaires": "腰部", "Épaule": "肩部", "Genou": "膝盖",
            "Cheville": "脚踝", "Poignet": "手腕", "Coude": "手肘",
            "Ischio-jambiers": "腘绳肌", "Mollet": "小腿",
            "Dos (haut)": "上背部", "Cou": "颈部", "Autre": "其他部位",
        },
        "alert_types": {
            "Courbature": "酸痛", "Tension": "紧张", "Douleur": "疼痛",
            "Gêne": "不适", "Blessure": "受伤",
        },
        "range_7d": "7天", "range_1m": "1个月", "range_3m": "3个月",
        "range_6m": "6个月", "range_season": "整个赛季",
    },
}


def notion_post(url, payload):
    """POST JSON vers l'API Notion via urllib (aucune dépendance externe)."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_API_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:500]
        print(f"Erreur API Notion ({e.code}): {err_body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Erreur réseau vers l'API Notion : {e.reason}")
        sys.exit(1)


def fetch_seances():
    """Récupère toutes les entrées de la base Séances (avec ou sans durée/RPE).

    Chaque entrée inclut systématiquement Zone alerte / Type alerte si renseignés,
    même quand durée ou RPE manquent (ex: séance de récup sans charge chiffrée
    mais avec une douleur signalée).
    """
    if not NOTION_TOKEN:
        print("Erreur : variable d'environnement NOTION_TOKEN manquante.")
        sys.exit(1)

    entries = []
    payload = {"page_size": 100}
    has_more = True

    while has_more:
        data = notion_post(NOTION_QUERY_URL, payload)

        for page in data.get("results", []):
            props = page.get("properties", {})

            date_prop = props.get("dates", {}).get("date")
            if not date_prop:
                continue  # pas de date exploitable, on ignore la ligne

            duree_prop = props.get("Durée séance (min)", {}).get("number")
            rpe_prop = props.get("Intensité perçue (joueuse)", {}).get("number")

            zone_select = props.get("Zone alerte", {}).get("select")
            type_select = props.get("Type alerte", {}).get("select")

            entries.append({
                "date": date_prop.get("start", "")[:10],
                "duree_min": duree_prop,
                "rpe": rpe_prop,
                "zone_alerte": zone_select.get("name") if zone_select else None,
                "type_alerte": type_select.get("name") if type_select else None,
            })

        has_more = data.get("has_more", False)
        payload["start_cursor"] = data.get("next_cursor")

    return entries


def filter_seances_for_charge(entries):
    """Ne garde que les entrées exploitables pour le calcul de charge (durée + RPE)."""
    return [
        {"date": e["date"], "duree_min": e["duree_min"], "rpe": e["rpe"]}
        for e in entries
        if e["duree_min"] is not None and e["rpe"] is not None
    ]


def compute_alert_status(entries):
    """Détermine l'alerte physique active, le cas échéant.

    Règle (validée par Bas) : l'alerte est active si la séance la plus récente
    a Zone alerte ou Type alerte renseigné. La date de début ("depuis le...")
    remonte tant que les séances précédentes ont aussi l'alerte renseignée en
    continu. Un champ vide sur une séance = fin de l'alerte (pas de mot-clé
    "résolu" nécessaire).
    """
    dated = sorted([e for e in entries if e["date"]], key=lambda e: e["date"])
    if not dated:
        return None

    last = dated[-1]
    if not last["zone_alerte"] and not last["type_alerte"]:
        return None  # dernière séance connue = rien signalé -> pas d'alerte active

    since_date = last["date"]
    for e in reversed(dated[:-1]):
        if e["zone_alerte"] or e["type_alerte"]:
            since_date = e["date"]
        else:
            break

    return {
        "zone": last["zone_alerte"],
        "type": last["type_alerte"],
        "since": since_date,
    }


def generate_html(entries, lang):
    """Génère le HTML pour une langue donnée (lang = 'en' ou 'zh')."""
    if not os.path.exists(TEMPLATE_PATH):
        print(f"Erreur : template introuvable à {TEMPLATE_PATH}")
        print("Copier dashboard_charge_v2_template.html à cet endroit avant de lancer le script.")
        sys.exit(1)

    if lang not in TRANSLATIONS:
        print(f"Erreur : langue '{lang}' inconnue dans TRANSLATIONS.")
        sys.exit(1)

    t = TRANSLATIONS[lang]
    seances = filter_seances_for_charge(entries)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    seances_json = json.dumps(seances, ensure_ascii=False)
    now_str = datetime.now(timezone.utc).astimezone().strftime(t["date_format"])

    # Bannière d'alerte physique — vide si rien d'actif (voir compute_alert_status)
    alert = compute_alert_status(entries)
    if alert:
        zone_label = t["alert_zones"].get(alert["zone"], alert["zone"] or "")
        type_label = t["alert_types"].get(alert["type"], alert["type"] or "")
        since_label = datetime.strptime(alert["since"], "%Y-%m-%d").strftime(t["date_format_short"])
        alert_banner_html = (
            '<div class="alert-banner">'
            + t["alert_banner_pattern"].format(type=type_label, zone=zone_label, date=since_label)
            + "</div>"
        )
    else:
        alert_banner_html = ""

    # Libellés utilisés dynamiquement par le JS côté client (zones, messages
    # "données insuffisantes", sélecteur de périodes, etc.) — un seul objet LABELS.
    js_labels = {
        "unit": t["unit"],
        "avgSeasonPattern": t["avg_season_pattern"],
        "insufficientShort": t["insufficient_short"],
        "acwrDaysPattern": t["acwr_days_pattern"],
        "zoneTarget": t["zone_target"],
        "zoneLow": t["zone_low"],
        "zoneWarn": t["zone_warn"],
        "zoneDanger": t["zone_danger"],
        "weekIncomplete": t["week_incomplete"],
        "monoOk": t["mono_ok"],
        "monoWarn": t["mono_warn"],
        "monoAbove": t["mono_above"],
        "noChargeData": t["no_charge_data"],
        "acwrInsufficientPattern": t["acwr_insufficient_pattern"],
        "monoInsufficient": t["mono_insufficient"],
    }

    html = template
    # Remplacements simples texte -> placeholder (dans l'ordre n'a pas d'importance)
    static_replacements = {
        "{{T_LANG}}": t["lang"],
        "{{T_TITLE}}": t["title"],
        "{{T_H1}}": t["h1"],
        "{{T_SUB}}": t["sub"],
        "{{T_GENERATED_LABEL}}": t["generated_label"],
        "{{T_SOURCE_LABEL}}": t["source_label"],
        "{{T_LABEL_CHARGE}}": t["label_charge"],
        "{{T_LABEL_ACWR}}": t["label_acwr"],
        "{{T_LABEL_MONOTONY}}": t["label_monotony"],
        "{{T_UNIT}}": t["unit"],
        "{{T_P1_H2}}": t["p1_h2"],
        "{{T_P1_CAPTION}}": t["p1_caption"],
        "{{T_P1_SOURCE}}": t["p1_source"],
        "{{T_P2_H2}}": t["p2_h2"],
        "{{T_P2_CAPTION}}": t["p2_caption"],
        "{{T_P2_LEGEND_LOW}}": t["p2_legend_low"],
        "{{T_P2_LEGEND_OK}}": t["p2_legend_ok"],
        "{{T_P2_LEGEND_WARN}}": t["p2_legend_warn"],
        "{{T_P2_LEGEND_DANGER}}": t["p2_legend_danger"],
        "{{T_P2_SOURCE}}": t["p2_source"],
        "{{T_P3_H2}}": t["p3_h2"],
        "{{T_P3_CAPTION}}": t["p3_caption"],
        "{{T_P3_LEGEND_OK}}": t["p3_legend_ok"],
        "{{T_P3_LEGEND_VIGILANCE}}": t["p3_legend_vigilance"],
        "{{T_P3_LEGEND_DANGER}}": t["p3_legend_danger"],
        "{{T_P3_SOURCE}}": t["p3_source"],
        "{{T_FOOTER_1}}": t["footer_1"],
        "{{T_FOOTER_2}}": t["footer_2"],
        "{{ALERT_BANNER}}": alert_banner_html,
        "{{T_RANGE_7D}}": t["range_7d"],
        "{{T_RANGE_1M}}": t["range_1m"],
        "{{T_RANGE_3M}}": t["range_3m"],
        "{{T_RANGE_6M}}": t["range_6m"],
        "{{T_RANGE_SEASON}}": t["range_season"],
    }
    for placeholder, value in static_replacements.items():
        html = html.replace(placeholder, value)

    html = html.replace("{{SEANCES_JSON}}", seances_json)
    html = html.replace("{{LABELS_JSON}}", json.dumps(js_labels, ensure_ascii=False))
    html = html.replace("{{GENERATED_AT}}", now_str)

    return html


def main():
    print(f"[{datetime.now().isoformat()}] Récupération des séances depuis Notion...")
    entries = fetch_seances()
    seances = filter_seances_for_charge(entries)
    print(f"  → {len(entries)} entrées récupérées, {len(seances)} exploitables (durée + RPE renseignés)")

    alert = compute_alert_status(entries)
    if alert:
        print(f"  → Alerte physique active : {alert['zone']} / {alert['type']} depuis le {alert['since']}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for lang, output_path in OUTPUT_FILES.items():
        html = generate_html(entries, lang)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  → Dashboard ({lang}) écrit dans {output_path}")

    print("Terminé.")


if __name__ == "__main__":
    main()
