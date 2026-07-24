@echo off
title CoDrone Edu Vision Controller - Installer & Launcher
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0Installer.ps1"
