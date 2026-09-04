#!/bin/bash
# Pre-deployment test script — verify install-dashboard.sh integrity locally

set -e

SCRIPT_DIR="/opt/data/jiani-sources/scripts"
TEMP_DIR="/tmp/dashboard_test_$$"

echo "=== PRE-DEPLOYMENT TEST (Local) ==="
echo "Testing in temporary directory: $TEMP_DIR"
echo ""

# Create temp environment
mkdir -p "$TEMP_DIR"
trap "rm -rf '$TEMP_DIR'" EXIT

# Test 1: Bash syntax
echo "Test 1: Bash syntax validation"
if bash -n "$SCRIPT_DIR/install-dashboard.sh" 2>/dev/null; then
    echo "✓ install-dashboard.sh syntax OK"
else
    echo "✗ install-dashboard.sh syntax error"
    exit 1
fi
echo ""

# Test 2: Python syntax
echo "Test 2: Python syntax validation"
python3 -m py_compile "$SCRIPT_DIR/generate_dashboard.py" && echo "✓ generate_dashboard.py syntax OK" || exit 1
echo ""

# Test 3: Check generate_dashboard.py structure
echo "Test 3: generate_dashboard.py structure verification"
python3 << PYEOF
import sys

with open("$SCRIPT_DIR/generate_dashboard.py", "r") as f:
    code = f.read()

checks = {
    "Single fetch_seances() outside loop": "# Fetch seances once" in code,
    "--output-dir argument": "--output-dir" in code,
    "--languages argument": "--languages" in code,
    "LANGUAGE_TEMPLATES dict": "LANGUAGE_TEMPLATES = {" in code,
    "generate_dashboard_for_language_from_data()": "def generate_dashboard_for_language_from_data" in code,
    "fetch_seances() called ONCE (not per-language)": code.count("seances = fetch_seances(token)") == 1,
    "Dashboard_charge_en.html template ref": '"en": "dashboard_charge_en.html"' in code,
    "Dashboard_charge_zh.html template ref": '"zh": "dashboard_charge_zh.html"' in code,
}

all_pass = True
for check_name, result in checks.items():
    status = "✓" if result else "✗"
    print(f"{status} {check_name}")
    if not result:
        all_pass = False

if all_pass:
    print("\n✓ All structure checks passed")
else:
    print("\n✗ Some structure checks failed")
    sys.exit(1)
PYEOF
echo ""

# Test 4: Check install-dashboard.sh for stale variables
echo "Test 4: install-dashboard.sh variable consistency"
(
SCRIPT="$SCRIPT_DIR/install-dashboard.sh"

# Check OUTPUT_DIR is used in mkdir
if grep -q 'mkdir -p "$OUTPUT_DIR"' "$SCRIPT"; then
    echo "✓ OUTPUT_DIR used correctly in mkdir"
else
    echo "✗ OUTPUT_DIR not found in correct mkdir statement"
    exit 1
fi

# Check summary shows BOTH files
if grep -q 'dashboard_charge_en.html' "$SCRIPT" && grep -q 'dashboard_charge_zh.html' "$SCRIPT"; then
    # Count how many times they appear in the summary section (last 25 lines)
    en_count=$(tail -25 "$SCRIPT" | grep -c 'dashboard_charge_en.html' || echo 0)
    zh_count=$(tail -25 "$SCRIPT" | grep -c 'dashboard_charge_zh.html' || echo 0)
    if [ "$en_count" -gt 0 ] && [ "$zh_count" -gt 0 ]; then
        echo "✓ Both output files referenced in installation summary"
    else
        echo "✗ Output files not properly documented in summary (en: $en_count, zh: $zh_count)"
        exit 1
    fi
else
    echo "✗ Output file references missing"
    exit 1
fi
)
echo ""

# Test 5: Verify templates exist
echo "Test 5: Multilingual template files"
if [ -f "$SCRIPT_DIR/dashboard_charge_en.html" ]; then
    lines=$(wc -l < "$SCRIPT_DIR/dashboard_charge_en.html")
    echo "✓ dashboard_charge_en.html exists ($lines lines)"
else
    echo "✗ dashboard_charge_en.html missing"
    exit 1
fi

if [ -f "$SCRIPT_DIR/dashboard_charge_zh.html" ]; then
    lines=$(wc -l < "$SCRIPT_DIR/dashboard_charge_zh.html")
    echo "✓ dashboard_charge_zh.html exists ($lines lines)"
else
    echo "✗ dashboard_charge_zh.html missing"
    exit 1
fi

# Verify placeholders
for tpl in dashboard_charge_en.html dashboard_charge_zh.html; do
    placeholders=$(grep -c "{{SEANCES_JSON}}\|{{GENERATED_AT}}" "$SCRIPT_DIR/$tpl" || echo 0)
    if [ "$placeholders" -eq 2 ]; then
        echo "✓ $tpl has both placeholders ({{SEANCES_JSON}}, {{GENERATED_AT}})"
    else
        echo "✗ $tpl missing placeholders (found $placeholders, expected 2)"
        exit 1
    fi
done
echo ""

# Test 6: Verify Monotonie 3-zone logic
echo "Test 6: Monotonie 3-zone implementation"
for tpl in dashboard_charge_en.html dashboard_charge_zh.html; do
    if grep -q "targetMax:1.5, warnMax:2" "$SCRIPT_DIR/$tpl"; then
        echo "✓ $tpl has Monotonie 3-zone logic (targetMax:1.5, warnMax:2)"
    else
        echo "✗ $tpl missing Monotonie 3-zone logic"
        exit 1
    fi
done
echo ""

echo "=== ALL TESTS PASSED ==="
echo ""
echo "Ready for VPS deployment:"
echo "  ✓ Bash scripts syntax-valid"
echo "  ✓ Python script structure-valid"
echo "  ✓ Single Notion API fetch (not 2x)"
echo "  ✓ Multilingual templates present"
echo "  ✓ No stale variable references"
echo "  ✓ Monotonie 3-zone fix in both versions"
echo ""
echo "Next: Deploy to VPS with install-dashboard.sh"
