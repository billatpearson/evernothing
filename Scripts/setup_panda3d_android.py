#!/usr/bin/env python3
"""
EverNothing - Panda3D Android Setup
Creates project structure for Panda3D Android deployment

Usage:
    python setup_panda3d_android.py
"""

import os
import sys

def create_directory_structure():
    """Create Panda3D Android project structure"""
    
    structure = {
        'android/': {
            'app/': {
                'src/': {
                    'main/': {
                        'python/': {},
                        'assets/': {},
                        'res/': {
                            'drawable/': {},
                            'layout/': {},
                            'values/': {}
                        }
                    }
                },
                'build.gradle': None
            },
            'gradle/': {
                'wrapper/': {}
            },
            'build.gradle': None,
            'settings.gradle': None,
            'gradle.properties': None,
            'local.properties': None
        }
    }
    
    def create_structure(base_path, structure):
        for name, content in structure.items():
            path = os.path.join(base_path, name)
            if content is None:
                # It's a file placeholder
                continue
            else:
                # It's a directory
                os.makedirs(path, exist_ok=True)
                print(f"✅ Created: {path}")
                if content:
                    create_structure(path, content)
    
    create_structure('.', structure)

def create_main_py():
    """Create main Python entry point"""
    
    content = '''"""
EverNothing - Panda3D Android Main
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
import requests
import json

class EverNothingApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Configuration
        self.server_url = "http://127.0.0.1:5000"
        self.token = None
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup basic UI"""
        # Load font
        font = loader.loadFont("cmr12.egg")
        
        # Title
        title = OnscreenText(
            text="EverNothing",
            pos=(0, 0.9),
            scale=0.1,
            fg=(1, 0.84, 0, 1),  # Gold
            align=TextNode.ACenter
        )
        
        # Login button
        self.login_btn = DirectButton(
            text="Login",
            scale=0.1,
            pos=(0, 0, 0.5),
            command=self.show_login
        )
        
        # Notes button
        self.notes_btn = DirectButton(
            text="My Notes",
            scale=0.1,
            pos=(0, 0, 0.3),
            command=self.show_notes
        )
        
    def show_login(self):
        """Show login screen"""
        print("Login screen")
        # TODO: Implement login UI
        
    def show_notes(self):
        """Show notes list"""
        print("Notes screen")
        # TODO: Implement notes UI
        
    def api_call(self, endpoint, method="GET", data=None):
        """Make API call to server"""
        url = f"{self.server_url}{endpoint}"
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            
            return response.json()
        except Exception as e:
            print(f"API Error: {e}")
            return None

app = EverNothingApp()
app.run()
'''
    
    path = 'android/app/src/main/python/main.py'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"✅ Created: {path}")

def create_build_gradle():
    """Create build.gradle files"""
    
    # Root build.gradle
    root_gradle = '''buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:7.4.2'
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

task clean(type: Delete) {
    delete rootProject.buildDir
}
'''
    
    # App build.gradle
    app_gradle = '''plugins {
    id 'com.android.application'
}

android {
    compileSdk 33
    
    defaultConfig {
        applicationId "com.evernothing.app"
        minSdk 21
        targetSdk 33
        versionCode 1
        versionName "1.0"
        
        ndk {
            abiFilters 'armeabi-v7a', 'arm64-v8a'
        }
    }
    
    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt')
        }
    }
    
    sourceSets {
        main {
            python.srcDirs = ['src/main/python']
        }
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.9.0'
}
'''
    
    with open('android/build.gradle', 'w') as f:
        f.write(root_gradle)
    print("✅ Created: android/build.gradle")
    
    with open('android/app/build.gradle', 'w') as f:
        f.write(app_gradle)
    print("✅ Created: android/app/build.gradle")

def create_settings_gradle():
    """Create settings.gradle"""
    
    content = '''rootProject.name = "EverNothing"
include ':app'
'''
    
    with open('android/settings.gradle', 'w') as f:
        f.write(content)
    print("✅ Created: android/settings.gradle")

def create_manifest():
    """Create AndroidManifest.xml"""
    
    content = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.evernothing.app">
    
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    
    <application
        android:allowBackup="true"
        android:icon="@drawable/ic_launcher"
        android:label="EverNothing"
        android:theme="@style/Theme.AppCompat.Light.DarkActionBar">
        
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
'''
    
    path = 'android/app/src/main/AndroidManifest.xml'
    with open(path, 'w') as f:
        f.write(content)
    print(f"✅ Created: {path}")

def create_readme():
    """Create Android README"""
    
    content = '''# EverNothing - Panda3D Android

## Prerequisites

- Android Studio
- Android SDK (API 21+)
- NDK
- Python 3.7+
- Panda3D SDK

## Setup

1. Install Panda3D:
```bash
pip install panda3d
```

2. Install Android SDK and NDK via Android Studio

3. Build the project:
```bash
cd android
./gradlew assembleDebug
```

4. Install on device:
```bash
./gradlew installDebug
```

## Project Structure

```
android/
├── app/
│   ├── src/
│   │   └── main/
│   │       ├── python/
│   │       │   └── main.py          # Main Python app
│   │       ├── assets/              # Assets (images, fonts)
│   │       ├── res/                 # Android resources
│   │       └── AndroidManifest.xml  # App manifest
│   └── build.gradle                 # App build config
├── gradle/                          # Gradle wrapper
├── build.gradle                     # Root build config
└── settings.gradle                  # Project settings
```

## Development

### Run on Emulator

1. Start Android emulator
2. Run: `./gradlew installDebug`
3. Launch app from emulator

### Run on Device

1. Enable USB debugging on device
2. Connect device via USB
3. Run: `./gradlew installDebug`

### Debug

```bash
adb logcat | grep python
```

## Configuration

Edit `main.py` to configure server URL:

```python
self.server_url = "http://YOUR_SERVER_IP:5000"
```

## Building APK

```bash
cd android
./gradlew assembleRelease
```

APK location: `app/build/outputs/apk/release/app-release.apk`

## Troubleshooting

### Build Errors

- Ensure Android SDK is installed
- Check NDK version compatibility
- Verify Panda3D is installed

### Connection Errors

- Use device IP, not localhost
- Ensure server is accessible from device
- Check firewall settings

## Notes

- This is a basic Panda3D setup
- For production, consider using Kivy or BeeWare instead
- Panda3D Android support is experimental
'''
    
    with open('android/README.md', 'w') as f:
        f.write(content)
    print("✅ Created: android/README.md")

def main():
    print("=" * 70)
    print("  EverNothing - Panda3D Android Setup")
    print("=" * 70)
    
    print("\n⚠️  NOTE: Panda3D Android support is experimental.")
    print("Consider using Kivy or BeeWare for better Android support.\n")
    
    response = input("Continue with Panda3D setup? (yes/no): ").lower()
    if response != 'yes':
        print("Setup cancelled.")
        sys.exit(0)
    
    print("\n[1/6] Creating directory structure...")
    create_directory_structure()
    
    print("\n[2/6] Creating main.py...")
    create_main_py()
    
    print("\n[3/6] Creating build.gradle files...")
    create_build_gradle()
    
    print("\n[4/6] Creating settings.gradle...")
    create_settings_gradle()
    
    print("\n[5/6] Creating AndroidManifest.xml...")
    create_manifest()
    
    print("\n[6/6] Creating README...")
    create_readme()
    
    print("\n" + "=" * 70)
    print("  Setup Complete! 🎉")
    print("=" * 70)
    
    print("\nNext steps:")
    print("1. Install Panda3D: pip install panda3d")
    print("2. Open android/ in Android Studio")
    print("3. Build: cd android && ./gradlew assembleDebug")
    print("4. See android/README.md for details")
    
    print("\n⚠️  Alternative: Use Kivy for better Android support")
    print("   See: https://kivy.org/doc/stable/guide/packaging-android.html")

if __name__ == '__main__':
    main()
