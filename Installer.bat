@echo off
setlocal enabledelayedexpansion
title CoDrone Edu Vision Controller Installer

:: Resolve current script folder cleanly with quotes
set "INSTALLER_DIR=%~dp0"

:: Launch PowerShell WPF Installer GUI with ExecutionPolicy Bypass
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%INSTALLER_DIR%Installer.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Installer exited with status code %ERRORLEVEL%.
    pause
)
