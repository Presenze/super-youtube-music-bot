@echo off
chcp 65001 >nul
title GiglioTube Bot - Deploy Automatico

echo.
echo 🎧✨ ================================================ ✨🎧
echo 🚀        GIGLIOTUBE BOT - DEPLOY AUTOMATICO        🚀
echo 🎧✨ ================================================ ✨🎧
echo.

echo 🔍 Controllo Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non installato!
    echo    Download: https://python.org/downloads
    pause
    exit /b 1
)
echo ✅ Python installato

echo.
echo 🔍 Controllo Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git non installato!
    echo    Download: https://git-scm.com/downloads
    pause
    exit /b 1
)
echo ✅ Git installato

echo.
echo 🚀 Avvio script di deploy...
python deploy_render.py

echo.
echo 🎉 Deploy completato!
echo 📚 Leggi DEPLOYMENT_GUIDE.md per maggiori dettagli
echo.
pause
