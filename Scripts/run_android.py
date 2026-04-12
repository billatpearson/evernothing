"""
Launcher for EverNothing Android app.
Finds the Python interpreter that has Kivy installed and runs main.py.

Usage:
  python run_android.py
"""

import subprocess
import sys
import os

CANDIDATES = [
    sys.executable,
    r"C:\Users\bills\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0\python.exe",
    "python3.9",
    "python3",
    "python",
]

def find_kivy_python():
    for py in CANDIDATES:
        try:
            result = subprocess.run(
                [py, "-c", "import kivy"],
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return py
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None

if __name__ == "__main__":
    py = find_kivy_python()
    if not py:
        print("ERROR: No Python interpreter with Kivy found.")
        print("Install Kivy: pip install kivy")
        sys.exit(1)

    main_py = os.path.join(os.path.dirname(__file__), "android", "main.py")
    print(f"Using interpreter: {py}")
    os.execv(py, [py, main_py])
