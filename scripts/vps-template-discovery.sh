#!/bin/bash
# Reconnaissance VPS — chercher template v3 ou fichiers dashboard multilingues
# Exécute ceci sur le VPS pour aider à clarifier la situation

echo "🔍 Searching for dashboard templates and v3 files..."
echo ""

# Chercher tous les fichiers HTML contenant "dashboard" ou "graphique"
echo "=== HTML files with 'dashboard' or 'graphique' ===" 
find ~ -name "*dashboard*" -o -name "*graphique*" 2>/dev/null | head -20

echo ""
echo "=== Files with '_en', '_zh', '_fr' suffixes ==="
find ~ -type f \( -name "*_en.html" -o -name "*_zh.html" -o -name "*_fr.html" \) 2>/dev/null

echo ""
echo "=== Files with 'v3' in name (dashboard-related) ==="
find ~ -type f -name "*v3*" 2>/dev/null | grep -i -E "(dashboard|graph|html)" | head -10

echo ""
echo "=== Content search: files containing 'dashboard_charge_zh' ==="
grep -r "dashboard_charge_zh" ~ 2>/dev/null | head -5

echo ""
echo "=== Content search: files containing '<html' with 'zh' or 'chinese' ==="
find ~ -type f -name "*.html" -exec grep -l "zh\|chinese\|中文" {} \; 2>/dev/null | head -10

echo ""
echo "✅ Done. If you found a v3 or _zh file, share its full path so I can inspect it."
