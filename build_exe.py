import subprocess
import sys
import os

def build_executable():
    print("==================================================")
    print("  CoDrone Edu Vision Controller Executable Builder")
    print("==================================================")

    # Ensure pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("[*] PyInstaller not found. Installing pyinstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=CoDroneVisionController",
        "--add-data=requirements.txt;.",
        "main.py"
    ]

    print(f"[*] Running PyInstaller build: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    print("\n[+] BUILD COMPLETE!")
    print(f"    Executable folder output: {os.path.abspath('dist/CoDroneVisionController')}")
    print(f"    Main executable: {os.path.abspath('dist/CoDroneVisionController/CoDroneVisionController.exe')}")

if __name__ == "__main__":
    build_executable()
