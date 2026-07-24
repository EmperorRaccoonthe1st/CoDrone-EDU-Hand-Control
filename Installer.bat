@echo off
setlocal enabledelayedexpansion
title CoDrone Edu Vision Controller Installer

set "INSTALLER_DIR=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%INSTALLER_DIR%Installer.ps1"
