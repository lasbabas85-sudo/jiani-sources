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

# Chemin de sortie — dossier servi par le conteneur nginx eval-jiani-web
OUTPUT_PATH = "/opt/data/eval-jiani/generated/dashboard_charge.html"

NOTION_API_VERSION = "2025-09-03"
NOTION_QUERY_URL = f"https://api.notion.com/v1/data_sources/{SEANCES_DATA_SOURCE_ID}/query"

# ---------------------------------------------------------------------------


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
    """Récupère toutes les séances avec date, durée et intensité perçue."""
    if not NOTION_TOKEN:
        print("Erreur : variable d'environnement NOTION_TOKEN manquante.")
        sys.exit(1)

    seances = []
    payload = {"page_size": 100}
    has_more = True

    while has_more:
        data = notion_post(NOTION_QUERY_URL, payload)

        for page in data.get("results", []):
            props = page.get("properties", {})

            date_prop = props.get("dates", {}).get("date")
            duree_prop = props.get("Durée séance (min)", {}).get("number")
            rpe_prop = props.get("Intensité perçue (joueuse)", {}).get("number")

            if not date_prop or duree_prop is None or rpe_prop is None:
                continue  # séance incomplète, on l'exclut du calcul (comportement volontaire)

            seances.append({
                "date": date_prop.get("start", "")[:10],
                "duree_min": duree_prop,
                "rpe": rpe_prop,
            })

        has_more = data.get("has_more", False)
        payload["start_cursor"] = data.get("next_cursor")

    return seances


def generate_html(seances):
    if not os.path.exists(TEMPLATE_PATH):
        print(f"Erreur : template introuvable à {TEMPLATE_PATH}")
        print("Copier dashboard_charge_v2_template.html à cet endroit avant de lancer le script.")
        sys.exit(1)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    seances_json = json.dumps(seances, ensure_ascii=False)
    now_str = datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y %H:%M")

    html = template.replace("{{SEANCES_JSON}}", seances_json)
    html = html.replace("{{GENERATED_AT}}", now_str)

    return html


def main():
    print(f"[{datetime.now().isoformat()}] Récupération des séances depuis Notion...")
    seances = fetch_seances()
    print(f"  → {len(seances)} séances exploitables (durée + RPE renseignés)")

    html = generate_html(seances)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  → Dashboard écrit dans {OUTPUT_PATH}")
    print("Terminé.")


if __name__ == "__main__":
    main()
