#!/bin/bash
# Dashboard Installation Script for Hetzner VPS
# Installs generate_dashboard.py + cron job + verification tools
# Run this ONCE on the VPS as the `bas` user

set -e

echo "=== Dashboard Installation ==="
echo "This script will:"
echo "1. Download generate_dashboard.py from GitHub"
echo "2. Create config files (.env)"
echo "3. Set up daily cron job at 6:00 AM"
echo "4. Verify installation"
echo ""

# ============================================================================
# CONFIGURATION (adjust these values)
# ============================================================================

REPO_URL="https://raw.githubusercontent.com/lasbabas85-sudo/jiani-sources/main"
INSTALL_DIR="$HOME/dashboard"
SCRIPT_NAME="generate_dashboard.py"
OUTPUT_DIR="$HOME/generated"  # Directory for multilingual outputs (_en.html + _zh.html)
NOTION_TOKEN_VAR="NOTION_API_TOKEN"  # Must match .env variable name

# ============================================================================
# STEP 1: Create directories
# ============================================================================

echo "Step 1: Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$OUTPUT_DIR"

# ============================================================================
# STEP 2: Download script
# ============================================================================

echo "Step 2: Downloading generate_dashboard.py from GitHub..."
curl -fsSL "$REPO_URL/scripts/generate_dashboard.py" -o "$INSTALL_DIR/$SCRIPT_NAME"
chmod +x "$INSTALL_DIR/$SCRIPT_NAME"
echo "✓ Downloaded to: $INSTALL_DIR/$SCRIPT_NAME"

# ============================================================================
# STEP 3: Check/create .env file
# ============================================================================

echo "Step 3: Checking environment configuration..."

ENV_FILE="$HOME/.env"

if [ -f "$ENV_FILE" ]; then
    echo "✓ Found existing $ENV_FILE"
    if grep -q "^$NOTION_TOKEN_VAR=" "$ENV_FILE"; then
        echo "✓ $NOTION_TOKEN_VAR already set"
    else
        echo "⚠️  $NOTION_TOKEN_VAR not found in .env — you'll need to add it manually"
        echo "   Format: $NOTION_TOKEN_VAR=your_token..."
    fi
else
    echo "⚠️  $ENV_FILE not found"
    echo "   You'll need to create it with: $NOTION_TOKEN_VAR=your_token..."
fi

# ============================================================================
# STEP 4: Create wrapper script for cron
# ============================================================================

echo "Step 4: Creating cron wrapper script..."

cat > "$INSTALL_DIR/run_dashboard.sh" << 'EOF'
#!/bin/bash
# Wrapper for cron: loads env + runs generator

set -a
if [ -f ~/.env ]; then
    source ~/.env
fi
set +a

INSTALL_DIR="$(dirname "$0")"
OUTPUT_DIR="$HOME/generated"
PYTHON_SCRIPT="$INSTALL_DIR/generate_dashboard.py"
LOG_FILE="$INSTALL_DIR/dashboard_last_run.log"

# Run generator with error logging (generates both _en.html and _zh.html)
{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting dashboard generation (multilingual: en, zh)..."
    python3 "$PYTHON_SCRIPT" \
        --notion-token "$NOTION_API_TOKEN" \
        --output-dir "$OUTPUT_DIR" \
        --languages "en,zh" 2>&1
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ All dashboards generated successfully"
        echo "Output:"
        [ -f "$OUTPUT_DIR/dashboard_charge_en.html" ] && echo "  - $OUTPUT_DIR/dashboard_charge_en.html ($(stat --format=%s "$OUTPUT_DIR/dashboard_charge_en.html") bytes)"
        [ -f "$OUTPUT_DIR/dashboard_charge_zh.html" ] && echo "  - $OUTPUT_DIR/dashboard_charge_zh.html ($(stat --format=%s "$OUTPUT_DIR/dashboard_charge_zh.html") bytes)"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✗ FAILED with exit code $EXIT_CODE"
        exit $EXIT_CODE
    fi
} | tee -a "$LOG_FILE"
EOF

chmod +x "$INSTALL_DIR/run_dashboard.sh"
echo "✓ Wrapper script created at: $INSTALL_DIR/run_dashboard.sh"

# ============================================================================
# STEP 5: Setup cron job
# ============================================================================

echo "Step 5: Setting up cron job..."

CRON_SCHEDULE="0 6 * * *"  # 6:00 AM daily
CRON_JOB="$CRON_SCHEDULE $INSTALL_DIR/run_dashboard.sh"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -F "$INSTALL_DIR/run_dashboard.sh" >/dev/null; then
    echo "✓ Cron job already exists"
    echo "Current crontab entry:"
    crontab -l 2>/dev/null | grep "$INSTALL_DIR/run_dashboard.sh"
else
    echo "Adding new cron job..."
    (crontab -l 2>/dev/null || true; echo "$CRON_JOB") | crontab -
    echo "✓ Cron job installed"
fi

# ============================================================================
# STEP 6: Verify installation
# ============================================================================

echo ""
echo "Step 6: Verification..."

CHECKS_PASSED=0
CHECKS_TOTAL=3

# Check 1: Script exists
if [ -f "$INSTALL_DIR/$SCRIPT_NAME" ]; then
    echo "✓ Script exists: $INSTALL_DIR/$SCRIPT_NAME"
    ((CHECKS_PASSED++))
else
    echo "✗ Script missing: $INSTALL_DIR/$SCRIPT_NAME"
fi

# Check 2: Wrapper exists
if [ -f "$INSTALL_DIR/run_dashboard.sh" ]; then
    echo "✓ Wrapper exists: $INSTALL_DIR/run_dashboard.sh"
    ((CHECKS_PASSED++))
else
    echo "✗ Wrapper missing: $INSTALL_DIR/run_dashboard.sh"
fi

# Check 3: Cron job configured
if crontab -l 2>/dev/null | grep -F "run_dashboard.sh" >/dev/null; then
    echo "✓ Cron job configured (6:00 AM daily)"
    ((CHECKS_PASSED++))
else
    echo "✗ Cron job not found"
fi

echo ""
echo "=== Installation Summary ==="
echo "Checks passed: $CHECKS_PASSED/$CHECKS_TOTAL"
echo ""
echo "📁 Installation directory: $INSTALL_DIR"
echo "📂 Output directory: $OUTPUT_DIR"
echo "  - dashboard_charge_en.html (generated daily)"
echo "  - dashboard_charge_zh.html (generated daily)"
echo "📋 Last run log: $INSTALL_DIR/dashboard_last_run.log"
echo "⏰ Cron schedule: Daily at 6:00 AM"
echo ""
echo "To test manually, run:"
echo "  $INSTALL_DIR/run_dashboard.sh"
echo ""
echo "To view cron logs:"
echo "  tail -f $INSTALL_DIR/dashboard_last_run.log"
echo ""
echo "To see cron job:"
echo "  crontab -l | grep run_dashboard"
echo ""
echo "✅ Installation complete!"
