#!/usr/bin/env python3
"""
Generate multilingual dashboard templates from a master template and language dictionaries.
This script creates _en.html and _zh.html versions by substituting the LABELS object.
"""

import re
import json

# ============================================================================
# LANGUAGE DICTIONARIES
# ============================================================================

LABELS_FR = {
    # UI labels
    "titleShort": "Charge d'entraînement",
    "titleFull": "Charge d'entraînement — Jiani",
    "subtitle": "Charge UA · ACWR (7j glissant) · Monotonie hebdomadaire",
    "generatedAt": "Généré le",
    "source": "Source : Notion — Séances",
    
    # Status cell labels
    "labelChargeLast7": "Charge — 7 derniers jours",
    "labelACWR": "ACWR (aiguë / chronique)",
    "labelMonotony": "Indice de monotonie",
    
    # Section titles
    "titleChargeWeekly": "Charge hebdomadaire (UA)",
    "titleACWR": "ACWR — Ratio charge aiguë / charge chronique",
    "titleMonotony": "Indice de monotonie",
    
    # Captions
    "captionCharge": "Charge = durée de séance (min) × intensité perçue (RPE 0–10) — méthode Séance-EPE, Foster et al. (2001)",
    "captionACWR": "Charge aiguë = 7 derniers jours glissants · Charge chronique = moyenne des 4 semaines précédentes",
    "captionMonotony": "Charge moyenne quotidienne ÷ écart-type, sur fenêtre glissante 7j — mesure la répétitivité de l'entraînement",
    
    # Legend items
    "acwrLegendLow": "< 0,8 sous-sollicitation",
    "acwrLegendOK": "0,8–1,3 zone cible",
    "acwrLegendWarn": "1,3–1,5 vigilance",
    "acwrLegendDanger": "> 1,5 risque accru",
    
    "monoLegendOK": "< 1,5 OK",
    "monoLegendWarn": "1,5–2 Vigilance",
    "monoLegendDanger": "≥ 2 Au-dessus du seuil Foster",
    
    # Status pills
    "avgSeasonPattern": "Moy. saison : {v} UA/sem",
    "acwrInsufficientShort": "Données insuffisantes",
    "acwrDaysRequired": "{v}/28 j nécessaires",
    "acwrInsufficientLong": "Données insuffisantes — {v}/28 jours de charge complète disponibles. L'ACWR nécessite 4 semaines pleines de charge chronique avant d'être fiable.",
    "weekIncomplete": "Semaine incomplète",
    "monoInsufficientShort": "Données insuffisantes",
    "monoInsufficientLong": "Données insuffisantes — la monotonie nécessite au moins 6 jours sur les 7 derniers avec charge renseignée.",
    
    # Charge status
    "chargeLast7Unit": "UA",
    "chargeZoneLow": "Sous-sollicitation",
    "chargeZoneOK": "Zone cible",
    "chargeZoneWarn": "Vigilance",
    "chargeZoneDanger": "Risque accru",
    
    # Monotony status (3-zone)
    "monoOK": "OK (<1,5)",
    "monoWarn": "Vigilance (1,5–2)",
    "monoDanger": "Au-dessus du seuil Foster",
    
    # Error messages
    "noChargeData": "Pas encore de données de charge exploitables (durée + RPE requis).",
    
    # Sources
    "sourcesCharge": "Foster, C. et al. (2001), J Strength Cond Res, 15:109-115 — méthode de calcul · Genevois, Rogowski &amp; Le Solliec (2020), ITF Coaching and Sport Science Review — application tennis",
    "sourcesACWR": "Blanch &amp; Gabbett (2016), Br J Sports Med, 50:471-475 · Myers et al. (2020), Med Sci Sports Exerc, 52(5):1196-1200 — junior tennis, ~14 ans · Moreno-Pérez et al. (2021), Eur J Sport Sci, 21(8):1215-1223 — junior haut niveau",
    "sourcesMonotony": "Seuil Foster : Foster, C. (1998), Med Sci Sports Exerc, 30(7):1164-1168. Zone jaune (1,5–2) = marge opérationnelle de vigilance (non-sourcée). Calcul : fenêtre glissante 7j, moyenne quotidienne ÷ écart-type.",
    
    # Footer
    "footerGenerated": "Dashboard généré automatiquement depuis la base Notion \"Seances\" · Zéro donnée saisie manuellement dans cet outil",
    "footerSources": "Seuils sourcés — voir SOURCES_DURABLE pour les références complètes",
}

LABELS_ZH = {
    # UI labels
    "titleShort": "训练负荷",
    "titleFull": "训练负荷 — Jiani",
    "subtitle": "训练负荷 · 急慢性比（7天）· 单调性指数",
    "generatedAt": "生成时间：",
    "source": "数据来源：Notion 训练记录",
    
    # Status cell labels
    "labelChargeLast7": "训练负荷 — 过去7天",
    "labelACWR": "急慢性比（急性/慢性）",
    "labelMonotony": "单调性指数",
    
    # Section titles
    "titleChargeWeekly": "周训练负荷",
    "titleACWR": "急慢性比 — 短期负荷与平均负荷的比值",
    "titleMonotony": "单调性指数",
    
    # Captions
    "captionCharge": "训练负荷 = 训练时长（分钟）× 自我感觉用力程度（RPE，0–10分） — Foster 等人（2001）提出的 Session-RPE 方法",
    "captionACWR": "急性负荷 = 过去7天 · 慢性负荷 = 过去4周平均值",
    "captionMonotony": "平均日均负荷 ÷ 标准差，采用7天滑动窗口——测量训练内容的重复程度",
    
    # Legend items
    "acwrLegendLow": "< 0,8 训练不足",
    "acwrLegendOK": "0,8–1,3 达标",
    "acwrLegendWarn": "1,3–1,5 需要关注",
    "acwrLegendDanger": "> 1,5 风险较高",
    
    "monoLegendOK": "< 1,5 正常",
    "monoLegendWarn": "1,5–2 偏高",
    "monoLegendDanger": "≥ 2 高于Foster阈值",
    
    # Status pills
    "avgSeasonPattern": "赛季平均：每周 {v}",
    "acwrInsufficientShort": "数据不足",
    "acwrDaysRequired": "还需 {v}/28 天数据",
    "acwrInsufficientLong": "数据不足 —— 目前有 {v}/28 天完整数据，需累积4周完整数据才能计算此指标。",
    "weekIncomplete": "本周数据不完整",
    "monoInsufficientShort": "数据不足",
    "monoInsufficientLong": "数据不足 —— 需要近7天中至少6天有完整训练记录。",
    
    # Charge status
    "chargeLast7Unit": "单位",
    "chargeZoneLow": "训练量偏低",
    "chargeZoneOK": "达标",
    "chargeZoneWarn": "需要关注",
    "chargeZoneDanger": "风险较高",
    
    # Monotony status (3-zone)
    "monoOK": "正常",
    "monoWarn": "偏高",
    "monoDanger": "高于Foster阈值",
    
    # Error messages
    "noChargeData": "暂无可用的训练负荷数据（需要时长和RPE）。",
    
    # Sources
    "sourcesCharge": "Foster, C. 等人（2001），J Strength Cond Res, 15:109-115 — 计算方法 · Genevois, Rogowski &amp; Le Solliec（2020），ITF Coaching and Sport Science Review — 网球应用",
    "sourcesACWR": "Blanch &amp; Gabbett（2016），Br J Sports Med, 50:471-475 · Myers 等人（2020），Med Sci Sports Exerc, 52(5):1196-1200 — 青少年网球，~14岁 · Moreno-Pérez 等人（2021），Eur J Sport Sci, 21(8):1215-1223 — 高水平青少年",
    "sourcesMonotony": "Foster阈值：Foster, C.（1998），Med Sci Sports Exerc, 30(7):1164-1168。黄色区域（1,5–2）= 操作警告边界（未标注）。计算：7天滑动窗口，平均日均负荷 ÷ 标准差。",
    
    # Footer
    "footerGenerated": "此页面根据Notion \"Seances\" 数据库自动生成 · 无需手动录入数据",
    "footerSources": "阈值已标注资料 —— 详见SOURCES_DURABLE查看完整参考资料",
}

# ============================================================================
# TEMPLATE PROCESSING
# ============================================================================

def load_master_template(path):
    """Load the master template (FR version with 3-zone Monotonie fix)."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def create_localized_template(master_template, labels_dict, lang_code, lang_name):
    """
    Create a localized version of the template.
    Replace:
    1. <html lang="fr"> -> <html lang="...">
    2. <title>...</title>
    3. All hardcoded French strings with labels_dict values
    4. const LABELS = {...} with localized version
    """
    
    result = master_template
    
    # Change lang attribute
    result = re.sub(r'<html lang="[^"]+', f'<html lang="{lang_code}', result)
    
    # Change title
    result = re.sub(
        r'<title>[^<]+</title>',
        f'<title>{labels_dict["titleFull"]}</title>',
        result
    )
    
    # Change h1
    result = re.sub(
        r'<h1>Charge d\'entraînement — Jiani</h1>',
        f'<h1>{labels_dict["titleFull"]}</h1>',
        result
    )
    
    # Change subtitle
    result = re.sub(
        r'<div class="sub">Charge UA · ACWR \(7j glissant\) · Monotonie hebdomadaire</div>',
        f'<div class="sub">{labels_dict["subtitle"]}</div>',
        result
    )
    
    # Replace status cell labels
    replacements = [
        (r'<span class="label">Charge — 7 derniers jours</span>', 
         f'<span class="label">{labels_dict["labelChargeLast7"]}</span>'),
        (r'<span class="label">ACWR \(aiguë / chronique\)</span>',
         f'<span class="label">{labels_dict["labelACWR"]}</span>'),
        (r'<span class="label">Indice de monotonie</span>',
         f'<span class="label">{labels_dict["labelMonotony"]}</span>'),
        
        # Section titles
        (r'<h2>Charge hebdomadaire \(UA\)</h2>',
         f'<h2>{labels_dict["titleChargeWeekly"]}</h2>'),
        (r'<h2>ACWR — Ratio charge aiguë / charge chronique</h2>',
         f'<h2>{labels_dict["titleACWR"]}</h2>'),
        (r'<h2>Indice de monotonie</h2>',
         f'<h2>{labels_dict["titleMonotony"]}</h2>'),
        
        # Captions
        (r'Charge = durée de séance \(min\) × intensité perçue \(RPE 0–10\) — méthode Séance-EPE, Foster et al\. \(2001\)',
         labels_dict["captionCharge"]),
        (r'Charge aiguë = 7 derniers jours glissants · Charge chronique = moyenne des 4 semaines précédentes',
         labels_dict["captionACWR"]),
        (r'Charge moyenne quotidienne ÷ écart-type, sur fenêtre glissante 7j — mesure la répétitivité de l\'entraînement',
         labels_dict["captionMonotony"]),
        
        # Legend
        (r'&lt; 0,8 sous-sollicitation',
         labels_dict["acwrLegendLow"]),
        (r'0,8–1,3 zone cible',
         labels_dict["acwrLegendOK"]),
        (r'1,3–1,5 vigilance',
         labels_dict["acwrLegendWarn"]),
        (r'&gt; 1,5 risque accru',
         labels_dict["acwrLegendDanger"]),
        
        (r'&lt; 1,5 OK',
         labels_dict["monoLegendOK"]),
        (r'1,5–2 Vigilance',
         labels_dict["monoLegendWarn"]),
        (r'≥ 2 Au-dessus du seuil Foster',
         labels_dict["monoLegendDanger"]),
    ]
    
    for old, new in replacements:
        result = re.sub(old, new, result)
    
    # Replace JavaScript strings
    js_replacements = [
        ("'Zone cible'", f"'{labels_dict['chargeZoneOK']}'"),
        ("'Sous-sollicitation'", f"'{labels_dict['chargeZoneLow']}'"),
        ("'Vigilance'", f"'{labels_dict['chargeZoneWarn']}'"),
        ("'Risque accru'", f"'{labels_dict['chargeZoneDanger']}'"),
        
        ("'OK (<1,5)'", f"'{labels_dict['monoOK']}'"),
        ("'Vigilance (1,5–2)'", f"'{labels_dict['monoWarn']}'"),
        ("'Au-dessus du seuil Foster'", f"'{labels_dict['monoDanger']}'"),
        
        ("'Données insuffisantes'", f"'{labels_dict['acwrInsufficientShort']}'"),
        ("'Semaine incomplète'", f"'{labels_dict['weekIncomplete']}'"),
        
        (r"'Pas encore de données de charge exploitables \(durée \+ RPE requis\)\.'",
         f"'{labels_dict['noChargeData']}'"),
    ]
    
    for old, new in js_replacements:
        result = result.replace(old, new)
    
    # Replace source texts in JS
    result = result.replace(
        "`Données insuffisantes — ${acwrDaysAvailable}/28 jours de charge complète disponibles. L'ACWR nécessite 4 semaines pleines de charge chronique avant d'être fiable.`",
        f"`{labels_dict['acwrInsufficientLong']}`"
    )
    result = result.replace(
        "'Données insuffisantes — la monotonie nécessite au moins 6 jours sur les 7 derniers avec charge renseignée.'",
        f"'{labels_dict['monoInsufficientLong']}'"
    )
    
    # Replace in .source divs
    result = result.replace(
        "Foster, C. et al. (2001), J Strength Cond Res, 15:109-115 — méthode de calcul · Genevois, Rogowski &amp; Le Solliec (2020), ITF Coaching and Sport Science Review — application tennis",
        labels_dict["sourcesCharge"]
    )
    result = result.replace(
        "Blanch &amp; Gabbett (2016), Br J Sports Med, 50:471-475 · Myers et al. (2020), Med Sci Sports Exerc, 52(5):1196-1200 — junior tennis, ~14 ans · Moreno-Pérez et al. (2021), Eur J Sport Sci, 21(8):1215-1223 — junior haut niveau",
        labels_dict["sourcesACWR"]
    )
    result = result.replace(
        "Seuil Foster : Foster, C. (1998), Med Sci Sports Exerc, 30(7):1164-1168. Zone jaune (1,5–2) = marge opérationnelle de vigilance (non-sourcée). Calcul : fenêtre glissante 7j, moyenne quotidienne ÷ écart-type.",
        labels_dict["sourcesMonotony"]
    )
    
    # Replace footer
    result = result.replace(
        'Dashboard généré automatiquement depuis la base Notion "Seances" · Zéro donnée saisie manuellement dans cet outil<br>\n    Seuils sourcés — voir SOURCES_DURABLE pour les références complètes',
        f'{labels_dict["footerGenerated"]}<br>\n    {labels_dict["footerSources"]}'
    )
    
    return result

def generate_templates():
    """Generate _en.html and _zh.html from master template."""
    master = load_master_template('/opt/data/jiani-sources/scripts/dashboard_charge_v2_template.html')
    
    # Generate FR version (for _en.html until actual English translation)
    en_version = create_localized_template(master, LABELS_FR, 'fr', 'Français')
    with open('/opt/data/jiani-sources/scripts/dashboard_charge_en.html', 'w', encoding='utf-8') as f:
        f.write(en_version)
    print("✓ Generated: dashboard_charge_en.html (FR version, ready for EN translation)")
    
    # Generate ZH version
    zh_version = create_localized_template(master, LABELS_ZH, 'zh-CN', '简体中文')
    with open('/opt/data/jiani-sources/scripts/dashboard_charge_zh.html', 'w', encoding='utf-8') as f:
        f.write(zh_version)
    print("✓ Generated: dashboard_charge_zh.html (Chinese version)")

if __name__ == '__main__':
    generate_templates()
