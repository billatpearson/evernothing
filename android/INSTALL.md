# EverNothing Android App - Installation Guide

## Prerequisites

- Android device (phone or tablet)
- Internet connection
- Termux app (terminal emulator for Android)

## Step 1: Install Termux

### Option A: F-Droid (Recommended)
1. Open browser on your Android device
2. Go to: https://f-droid.org
3. Tap "Download F-Droid"
4. Install F-Droid APK
5. Open F-Droid app
6. Search for "Termux"
7. Install Termux

### Option B: GitHub Releases
1. Go to: https://github.com/termux/termux-app/releases
2. Download latest `termux-app_vX.X.X+github-debug_universal.apk`
3. Install APK (enable "Install from unknown sources" if needed)

**Note**: Do NOT use Google Play Store version (outdated)

## Step 2: Setup Termux

Open Termux and run these commands:

```bash
# Update package lists
pkg update

# Upgrade installed packages
pkg upgrade

# Install Python
pkg install python

# Install git (to download EverNothing)
pkg install git
```

## Step 3: Download EverNothing

### Option A: Clone from Git Repository
```bash
# Navigate to home directory
cd ~

# Clone repository (replace with your repo URL)
git clone https://github.com/yourusername/evernothing.git

# Navigate to android folder
cd evernothing/android
```

### Option B: Manual Download
```bash
# Create directory
mkdir -p ~/evernothing/android
cd ~/evernothing/android

# Download files manually
# Use browser to download main.py, requirements.txt, README.md
# Save to: /storage/emulated/0/Download/

# Move files to Termux
cp /storage/emulated/0/Download/main.py .
cp /storage/emulated/0/Download/requirements.txt .
```

### Option C: Direct File Transfer
1. Connect Android device to computer via USB
2. Copy `android/` folder to device storage
3. In Termux:
```bash
cp -r /storage/emulated/0/Download/android ~/evernothing/
cd ~/evernothing/android
```

## Step 4: Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# This installs:
# - kivy (UI framework)
# - requests (HTTP client)
```

**Note**: Kivy installation may take 5-10 minutes on mobile devices.

## Step 5: Configure Server Connection

### For Local Testing (Flask on same device)
```bash
# No configuration needed - uses default localhost
export EVERNOTHING_SERVER=http://127.0.0.1:5000
```

### For Remote Server
```bash
# Set your Flask server IP address
export EVERNOTHING_SERVER=http://192.168.1.100:5000

# Or use domain name
export EVERNOTHING_SERVER=https://evernothing.example.com
```

**To make permanent**, add to `~/.bashrc`:
```bash
echo 'export EVERNOTHING_SERVER=http://YOUR_SERVER:5000' >> ~/.bashrc
```

## Step 6: Start Flask Backend

### Option A: On Same Android Device
Open a new Termux session (swipe from left, tap "New Session"):
```bash
cd ~/evernothing
python evernothing.py
```

### Option B: On Computer/Server
On your computer:
```bash
cd /path/to/evernothing
python evernothing.py

# Make accessible on network
python evernothing.py --host 0.0.0.0
```

Find your computer's IP:
- Windows: `ipconfig`
- Mac/Linux: `ifconfig` or `ip addr`

## Step 7: Run Android App

In Termux:
```bash
cd ~/evernothing/android
python main.py
```

The app will launch in fullscreen mode.

## Troubleshooting

### "Permission denied" errors
```bash
# Grant storage permissions
termux-setup-storage

# Accept permission prompt on device
```

### "Module not found" errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### "Connection refused" errors
```bash
# Check Flask is running
curl http://127.0.0.1:5000

# Check firewall allows port 5000
# On Flask server, ensure: app.run(host='0.0.0.0')
```

### Kivy installation fails
```bash
# Install build dependencies
pkg install clang python-numpy

# Retry installation
pip install kivy
```

### App crashes on startup
```bash
# Check Python version (need 3.7+)
python --version

# Check logs
python main.py 2>&1 | tee app.log
```

## Running in Background

### Keep Flask Running
```bash
# In Termux session 1
cd ~/evernothing
nohup python evernothing.py &
```

### Keep App Running
```bash
# In Termux session 2
cd ~/evernothing/android
python main.py
```

**Note**: Termux must stay in foreground or use Termux:Boot for background execution.

## Updating the App

```bash
cd ~/evernothing
git pull origin main
cd android
pip install --upgrade -r requirements.txt
```

## Uninstallation

```bash
# Remove app files
rm -rf ~/evernothing

# Uninstall Python packages
pip uninstall kivy requests -y

# Uninstall Termux (via Android settings)
```

## Quick Start Script

Create `~/start-evernothing.sh`:
```bash
#!/data/data/com.termux/files/usr/bin/bash
cd ~/evernothing/android
export EVERNOTHING_SERVER=http://127.0.0.1:5000
python main.py
```

Make executable and run:
```bash
chmod +x ~/start-evernothing.sh
~/start-evernothing.sh
```

## Alternative: Desktop Testing

Test on computer before deploying to Android:
```bash
# On Windows/Mac/Linux
pip install kivy requests
python main.py
```

## Network Configuration Tips

### Find Android Device IP
```bash
# In Termux
ifconfig wlan0 | grep inet
```

### Test Connectivity
```bash
# From Android to server
curl http://YOUR_SERVER:5000

# From server to Android (if running Flask on Android)
curl http://ANDROID_IP:5000
```

### Use Same WiFi Network
- Ensure Android device and Flask server on same WiFi
- Check router doesn't block device-to-device communication
- Disable VPN if connection fails

## Security Notes

- Use HTTPS for production (not HTTP)
- Don't expose Flask dev server to internet
- Use strong passwords
- Enable encryption in EverNothing settings
- Keep Termux and packages updated

## Support

For issues:
1. Check Termux logs: `python main.py 2>&1 | tee error.log`
2. Verify Flask backend is accessible
3. Test with `curl` before using app
4. Check GitHub issues or create new one
