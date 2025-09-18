@echo off
echo Starting YouTube Music Download Bot...
echo.
echo Make sure you have:
echo 1. Python installed
echo 2. FFmpeg installed
echo 3. BOT_TOKEN set in .env file
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting bot...
python bot.py
pause
