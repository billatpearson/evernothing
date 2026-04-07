#!/data/data/com.termux/files/usr/bin/bash
# EverNothing Android — one-command installer for Termux
# Usage (in Termux):
#   curl -fsSL https://raw.githubusercontent.com/billatpearson/evernothing/main/evernothing_android/install_android.sh | bash

set -e

INSTALL_DIR="$HOME/evernothing"
REPO_URL="https://raw.githubusercontent.com/billatpearson/evernothing/main/evernothing_android"

echo "========================================"
echo "  EverNothing Android Installer"
echo "========================================"

# 1. System packages
echo "[1/5] Installing system packages..."
pkg update -y -q
pkg install -y python git curl 2>/dev/null || true

# 2. Python packages
echo "[2/5] Installing Python packages..."
pip install --quiet --upgrade pip
pip install --quiet flask flask-login werkzeug boto3 cryptography python-dotenv

# 3. App directory
echo "[3/5] Setting up app directory..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download app files
for f in evernothing_android.py config_loader.py requirements.txt; do
    echo "  Downloading $f..."
    curl -fsSL "$REPO_URL/$f" -o "$f"
done

# 4. Config file (only if not already present)
if [ ! -f config.ini ]; then
    echo "[4/5] Creating config.ini..."
    cat > config.ini << 'EOF'
[AWS]
# Your S3 bucket name for database checkpoints
S3_BUCKET_NAME =
AWS_REGION     = us-east-1
# Leave blank to use IAM role / instance profile
AWS_ACCESS_KEY_ID     =
AWS_SECRET_ACCESS_KEY =

[APP]
# Leave SECRET_KEY blank to auto-generate (sessions won't persist across restarts)
SECRET_KEY =
DB_FILE    = evernothing.db
HOST       = 127.0.0.1
PORT       = 5000
EOF
    echo "  *** Edit ~/evernothing/config.ini and add your S3 bucket + AWS credentials ***"
else
    echo "[4/5] config.ini already exists — skipping."
fi

# 5. Start script
echo "[5/5] Creating start script..."
cat > "$INSTALL_DIR/start.sh" << 'STARTEOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/evernothing"
echo "Starting EverNothing..."
echo "Open your browser at: http://127.0.0.1:5000"
echo "Press Ctrl+C to stop."
python evernothing_android.py
STARTEOF
chmod +x "$INSTALL_DIR/start.sh"

echo ""
echo "========================================"
echo "  Installation complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Edit config:  nano ~/evernothing/config.ini"
echo "     - Set S3_BUCKET_NAME to your bucket"
echo "     - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
echo ""
echo "  2. Start the app: bash ~/evernothing/start.sh"
echo ""
echo "  3. Open Chrome on your phone:"
echo "     http://127.0.0.1:5000"
echo ""
echo "  The database checkpoints to S3 every 15 minutes automatically."
echo "  You can also tap 'Sync Now' in the app at any time."
echo ""
