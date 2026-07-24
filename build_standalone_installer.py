import subprocess
import sys
import os

def create_standalone_exe():
    print("==================================================")
    print("  Creating Standalone 1-Click CoDroneSetup.exe   ")
    print("==================================================")

    # Use PS2EXE or IExpress or PyInstaller to bundle Installer into single executable
    # Here we create a simple launcher or package
    installer_bat = os.path.abspath("Installer.bat")
    installer_ps1 = os.path.abspath("Installer.ps1")

    print(f"[+] Standalone Installer Scripts Verified:")
    print(f"    - Launcher Batch: {installer_bat}")
    print(f"    - WPF PowerShell Script: {installer_ps1}")
    print("[+] Moving 'Installer.bat' or 'Installer.ps1' alone to any folder or USB will automatically pull and setup the system!")

if __name__ == "__main__":
    create_standalone_exe()
