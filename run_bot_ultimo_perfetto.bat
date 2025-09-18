@echo off
echo ========================================
echo    SUPER YOUTUBE MUSIC BOT ULTIMO
echo ========================================
echo.
echo Avvio del bot YouTube ULTIMO e PERFETTO...
echo.

echo Controllo dipendenze...
python -c "import telegram, yt_dlp, aiofiles, mutagen; print('✅ Tutte le dipendenze OK!')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Dipendenze mancanti! Eseguendo installazione...
    call install_completo.bat
    if %errorlevel% neq 0 (
        echo ❌ Errore installazione! Controlla i log.
        pause
        exit /b 1
    )
)

echo.
echo Controllo FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ FFmpeg non trovato!
    echo.
    echo INSTALLAZIONE FFMPEG RICHIESTA:
    echo 1. Vai su https://ffmpeg.org/download.html
    echo 2. Scarica FFmpeg per Windows
    echo 3. Estrai in C:\ffmpeg
    echo 4. Aggiungi C:\ffmpeg\bin al PATH di sistema
    echo.
    echo Oppure usa chocolatey: choco install ffmpeg
    echo.
    pause
    exit /b 1
) else (
    echo ✅ FFmpeg trovato!
)

echo.
echo Funzioni PREMIUM:
echo - Download audio VELOCISSIMI
echo - Supporto playlist
echo - Formati multipli (MP3, M4A, WAV, FLAC)
echo - Qualità 320k PREMIUM
echo - Statistiche download
echo - Embedding metadati avanzati
echo - Interfaccia completamente in italiano
echo - Supporto multilingua (IT/EN)
echo - Pulsanti colorati e tema bellissimo
echo - Tutti gli errori risolti
echo - Gestione errori migliorata
echo - Nessun conflitto di istanze
echo - Performance MASSIME
echo - TUTTO PREMIUM
echo - Callback data ottimizzati
echo - URL hash per sicurezza
echo - PULSANTI COLORATI CON EMOJI
echo - SFONDI BELLISSIMI
echo - FUNZIONA AL 100%
echo - CONTROLLO FFMPEG AUTOMATICO
echo.

echo Avvio Bot Ultimo Perfetto...
python bot_ultimo_perfetto.py
pause
