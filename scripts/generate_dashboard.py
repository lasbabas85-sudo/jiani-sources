#!/usr/bin/env python3
"""
Generate dashboard HTML from Notion Seances database.

Usage:
  python3 generate_dashboard.py --notion-token <TOKEN> --output <PATH>

This script:
1. Fetches all seances from Notion "Seances" database
2. Extracts: date, duree_min (Durée séance), rpe (Intensité perçue)
3. Replaces {{SEANCES_JSON}} and {{GENERATED_AT}} in the template
4. Writes the final HTML to --output
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import requests
import argparse

# Notion API constants
NOTION_API_VERSION = "2022-06-28"
NOTION_SEANCES_DB_ID = "3824293d-742f-8084-945c-000b885a1b37"

def fetch_seances(token):
    """Fetch all seances from Notion database."""
    url = f"https://api.notion.com/v1/databases/{NOTION_SEANCES_DB_ID}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json"
    }
    
    seances = []
    cursor = None
    
    while True:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        for page in data.get("results", []):
            props = page.get("properties", {})
            
            # Extract date
            dates_prop = props.get("dates", {})
            date_val = None
            if dates_prop.get("type") == "date":
                date_obj = dates_prop.get("date", {})
                if date_obj:
                    date_val = date_obj.get("start")
            
            # Extract duree_min
            duree_prop = props.get("Durée séance (min)", {})
            duree_min = None
            if duree_prop.get("type") == "number":
                duree_min = duree_prop.get("number")
            
            # Extract rpe (Intensité perçue)
            rpe_prop = props.get("Intensité perçue (joueuse)", {})
            rpe = None
            if rpe_prop.get("type") == "number":
                rpe = rpe_prop.get("number")
            
            # Only include if both duree_min and rpe are present
            if date_val and duree_min is not None and rpe is not None:
                seances.append({
                    "date": date_val,
                    "duree_min": int(duree_min),
                    "rpe": float(rpe)
                })
        
        cursor = data.get("next_cursor")
        if not cursor:
            break
    
    return sorted(seances, key=lambda x: x["date"])

def generate_dashboard(token, output_path):
    """Generate dashboard HTML."""
    
    # Fetch seances
    print("Fetching seances from Notion...", file=sys.stderr)
    seances = fetch_seances(token)
    print(f"  Found {len(seances)} seances", file=sys.stderr)
    
    # Load template
    template_path = Path(__file__).parent / "dashboard_charge_v2_template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    # Replace placeholders
    seances_json = json.dumps(seances, ensure_ascii=False)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    html = template.replace("{{SEANCES_JSON}}", seances_json)
    html = html.replace("{{GENERATED_AT}}", generated_at)
    
    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Dashboard generated: {output_file}", file=sys.stderr)
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dashboard from Notion seances")
    parser.add_argument("--notion-token", required=True, help="Notion API token")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    
    args = parser.parse_args()
    
    try:
        generate_dashboard(args.notion_token, args.output)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
