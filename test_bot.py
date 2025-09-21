#!/usr/bin/env python3
"""
GiglioTube Bot - Test Script
Testa tutte le configurazioni e dipendenze
"""

import os
import sys
import importlib

def test_imports():
    """Testa tutti gli import necessari"""
    print("🔍 Testando import...")
    
    # Test import base
    try:
        import asyncio
        print("✅ asyncio")
    except ImportError as e:
        print(f"❌ asyncio: {e}")
        return False
    
    try:
        import json
        print("✅ json")
    except ImportError as e:
        print(f"❌ json: {e}")
        return False
    
    try:
        import logging
        print("✅ logging")
    except ImportError as e:
        print(f"❌ logging: {e}")
        return False
    
    # Test import opzionali
    try:
        import yt_dlp
        print("✅ yt-dlp")
    except ImportError as e:
        print(f"⚠️  yt-dlp: {e}")
    
    try:
        from telegram import Update
        print("✅ python-telegram-bot")
    except ImportError as e:
        print(f"⚠️  python-telegram-bot: {e}")
    
    try:
        import aiofiles
        print("✅ aiofiles")
    except ImportError as e:
        print(f"⚠️  aiofiles: {e}")
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv")
    except ImportError as e:
        print(f"⚠️  python-dotenv: {e}")
    
    return True

def test_configs():
    """Testa tutte le configurazioni"""
    print("\n🔧 Testando configurazioni...")
    
    # Test config_production.py
    try:
        from config_production import BOT_TOKEN, DOWNLOAD_PATH, MAX_FILE_SIZE
        print("✅ config_production.py")
        print(f"   BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
        print(f"   DOWNLOAD_PATH: {DOWNLOAD_PATH}")
        print(f"   MAX_FILE_SIZE: {MAX_FILE_SIZE}")
    except ImportError as e:
        print(f"❌ config_production.py: {e}")
        return False
    
    # Test config.py
    try:
        from config import BOT_TOKEN, DOWNLOAD_PATH
        print("✅ config.py")
    except ImportError as e:
        print(f"⚠️  config.py: {e}")
    
    # Test config_render.py
    try:
        from config_render import BOT_TOKEN, DOWNLOAD_PATH
        print("✅ config_render.py")
    except ImportError as e:
        print(f"⚠️  config_render.py: {e}")
    
    return True

def test_bot_import():
    """Testa l'import del bot principale"""
    print("\n🤖 Testando bot principale...")
    
    try:
        from gigliotube import SuperYouTubeDownloader
        print("✅ SuperYouTubeDownloader class")
        
        # Test creazione istanza
        downloader = SuperYouTubeDownloader()
        print("✅ Bot instance created")
        
        # Test metodi base
        stats = downloader.load_stats()
        print(f"✅ Stats loaded: {stats}")
        
        prefs = downloader.load_preferences()
        print(f"✅ Preferences loaded: {prefs}")
        
        langs = downloader.load_languages()
        print(f"✅ Languages loaded: {langs}")
        
    except ImportError as e:
        print(f"❌ Bot import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Bot creation failed: {e}")
        return False
    
    return True

def test_ffmpeg():
    """Testa FFmpeg"""
    print("\n🎵 Testando FFmpeg...")
    
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ FFmpeg disponibile")
            return True
        else:
            print("⚠️  FFmpeg non funziona correttamente")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg non installato")
        return False
    except subprocess.TimeoutExpired:
        print("⚠️  FFmpeg timeout")
        return False
    except Exception as e:
        print(f"❌ Errore FFmpeg: {e}")
        return False

def test_environment():
    """Testa variabili d'ambiente"""
    print("\n🌍 Testando ambiente...")
    
    # Test variabili d'ambiente
    env_vars = ['BOT_TOKEN', 'PYTHONUNBUFFERED', 'TZ']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:20]}..." if len(value) > 20 else f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: non impostata")
    
    # Test platform detection
    platform = os.getenv('PLATFORM', 'unknown')
    print(f"✅ Platform: {platform}")
    
    return True

def main():
    """Funzione principale di test"""
    print("""
🎧✨ ================================================ ✨🎧
🚀        GIGLIOTUBE BOT - TEST COMPLETO            🚀
🎧✨ ================================================ ✨🎧
    """)
    
    tests = [
        ("Import Base", test_imports),
        ("Configurazioni", test_configs),
        ("Bot Principale", test_bot_import),
        ("FFmpeg", test_ffmpeg),
        ("Ambiente", test_environment)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 Test: {test_name}")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSATO")
            else:
                print(f"❌ {test_name}: FALLITO")
        except Exception as e:
            print(f"❌ {test_name}: ERRORE - {e}")
            results.append((test_name, False))
    
    # Riepilogo
    print(f"\n{'='*50}")
    print("📊 RIEPILOGO TEST")
    print('='*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSATO" if result else "❌ FALLITO"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 Risultato: {passed}/{total} test passati")
    
    if passed == total:
        print("🎉 TUTTI I TEST PASSATI! Il bot è pronto per il deployment! 🚀")
        return True
    else:
        print("⚠️  Alcuni test sono falliti. Controlla gli errori sopra.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Test interrotto dall'utente.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")
        sys.exit(1)
