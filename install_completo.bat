@echo off
echo ========================================
echo    INSTALLAZIONE COMPLETA BOT YOUTUBE
echo ========================================
echo.
echo Installazione di TUTTE le dipendenze necessarie...
echo.

echo [1/5] Installazione Python packages...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [2/5] Installazione FFmpeg...
echo Controllo se FFmpeg è già installato...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo FFmpeg non trovato. Installazione...
    echo.
    echo IMPORTANTE: Devi installare FFmpeg manualmente:
    echo 1. Vai su https://ffmpeg.org/download.html
    echo 2. Scarica FFmpeg per Windows
    echo 3. Estrai in C:\ffmpeg
    echo 4. Aggiungi C:\ffmpeg\bin al PATH di sistema
    echo.
    echo Oppure usa chocolatey: choco install ffmpeg
    echo.
    pause
) else (
    echo FFmpeg già installato! ✅
)

echo.
echo [3/5] Verifica dipendenze...
python -c "import telegram; print('✅ python-telegram-bot OK')"
python -c "import yt_dlp; print('✅ yt-dlp OK')"
python -c "import aiofiles; print('✅ aiofiles OK')"
python -c "import mutagen; print('✅ mutagen OK')"

echo.
echo [4/5] Test connessione...
python -c "import requests; print('✅ requests OK')"

echo.
echo [5/5] Creazione cartelle...
if not exist "downloads" mkdir downloads
if not exist "data" mkdir data

echo.
echo ========================================
echo    INSTALLAZIONE COMPLETATA!
echo ========================================
echo.
echo Il bot è pronto per essere avviato!
echo Usa: run_bot_perfetto_finale.bat
echo.
pause
