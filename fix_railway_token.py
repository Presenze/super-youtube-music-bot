#!/usr/bin/env python3
"""
🚂 GiglioTube Bot - Fix Railway Token
Script per correggere il token del bot su Railway
"""

import os
import sys
import subprocess

def print_banner():
    """Stampa il banner del bot"""
    print("""
🚂✨ ================================================ ✨🚂
🚀        GIGLIOTUBE BOT - FIX RAILWAY TOKEN        🚀
🚂✨ ================================================ ✨🚂

🎯 Correzione token del bot su Railway!
    """)

def update_config_files():
    """Aggiorna tutti i file di configurazione con il token corretto"""
    print("🔧 Aggiornamento file di configurazione...")
    
    correct_token = "8237710386:AAF9MmADLR0PfihDtK8ZTmeDRi884MbV8HM"
    
    # Aggiorna config_railway.py
    config_railway_content = f'''import os

# Railway configuration - No external dependencies
# This file is designed specifically for Railway deployment

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    # Fallback token for testing (replace with your actual token)
    BOT_TOKEN = "{correct_token}"
    print("⚠️  Using fallback BOT_TOKEN. Please set BOT_TOKEN environment variable for production.")

# Download settings
DOWNLOAD_PATH = "downloads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit (PREMIUM)
SUPPORTED_FORMATS = ['mp3', 'm4a', 'wav', 'flac']

# Bot settings
MAX_CONCURRENT_DOWNLOADS = 5  # Increased for Railway
CLEANUP_AFTER_HOURS = 24

# Railway specific settings
RAILWAY_ENV = True
PLATFORM = 'railway'
LOG_LEVEL = "INFO"

print(f"🚂 Running on Railway platform")
'''
    
    with open('config_railway.py', 'w', encoding='utf-8') as f:
        f.write(config_railway_content)
    
    # Aggiorna config_production.py
    config_production_content = f'''import os

# Production configuration - No external dependencies
# This file is designed to work without python-dotenv

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    # Fallback token for testing (replace with your actual token)
    BOT_TOKEN = "{correct_token}"
    print("⚠️  Using fallback BOT_TOKEN. Please set BOT_TOKEN environment variable for production.")

# Download settings
DOWNLOAD_PATH = "downloads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit (PREMIUM)
SUPPORTED_FORMATS = ['mp3', 'm4a', 'wav', 'flac']

# Bot settings
MAX_CONCURRENT_DOWNLOADS = 5  # Increased for production
CLEANUP_AFTER_HOURS = 24

# Production specific settings
PRODUCTION_ENV = True
LOG_LEVEL = "INFO"

# Platform detection
PLATFORM = os.getenv('PLATFORM', 'unknown')
if os.getenv('RENDER'):
    PLATFORM = 'render'
elif os.getenv('RAILWAY'):
    PLATFORM = 'railway'
elif os.getenv('REPL_ID'):
    PLATFORM = 'replit'
elif os.getenv('VERCEL'):
    PLATFORM = 'vercel'
elif os.getenv('HEROKU'):
    PLATFORM = 'heroku'
elif os.getenv('CYCLIC'):
    PLATFORM = 'cyclic'

print(f"🚀 Running on platform: {{PLATFORM}}")
'''
    
    with open('config_production.py', 'w', encoding='utf-8') as f:
        f.write(config_production_content)
    
    # Aggiorna config_render.py
    config_render_content = f'''import os

# Try to load dotenv if available, but don't fail if it's not
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("ℹ️  python-dotenv not available, using environment variables only")

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    # Fallback token for testing (replace with your actual token)
    BOT_TOKEN = "{correct_token}"
    print("⚠️  Using fallback BOT_TOKEN. Please set BOT_TOKEN environment variable for production.")

# Download settings
DOWNLOAD_PATH = "downloads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit (PREMIUM)
SUPPORTED_FORMATS = ['mp3', 'm4a', 'wav', 'flac']

# Bot settings
MAX_CONCURRENT_DOWNLOADS = 5  # Aumentato per Render
CLEANUP_AFTER_HOURS = 24

# Render specific settings
RENDER_ENV = True
LOG_LEVEL = "INFO"
'''
    
    with open('config_render.py', 'w', encoding='utf-8') as f:
        f.write(config_render_content)
    
    # Aggiorna config.py
    config_content = f'''import os

# Try to load dotenv if available, but don't fail if it's not
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("ℹ️  python-dotenv not available, using environment variables only")

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN') or "{correct_token}"
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Download settings
DOWNLOAD_PATH = "downloads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
SUPPORTED_FORMATS = ['mp3', 'm4a', 'wav']

# Bot settings
MAX_CONCURRENT_DOWNLOADS = 3
CLEANUP_AFTER_HOURS = 24
'''
    
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("✅ File di configurazione aggiornati")

def commit_and_push():
    """Committa e pusha le modifiche"""
    print("📝 Commit e push modifiche...")
    
    try:
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Fix Railway bot token - use correct token'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("✅ Modifiche committate e pushate")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore durante commit/push: {e}")
        return False

def print_instructions():
    """Stampa le istruzioni per il fix"""
    print("""
🎯 ISTRUZIONI FIX RAILWAY TOKEN:

1. 🌐 Vai su Railway Dashboard
2. 🔧 Vai su "Variables" 
3. 🔑 Aggiorna BOT_TOKEN:
   - Vecchio: 7576082688:AAGJz-v5NG8QGKCezBA5qlhI3lYiatsgRd8
   - Nuovo: 8237710386:AAF9MmADLR0PfihDtK8ZTmeDRi884MbV8HM
4. 💾 Salva le modifiche
5. 🔄 Riavvia il servizio (Redeploy)
6. ⏳ Aspetta 2-3 minuti
7. 🎉 Il bot funzionerà correttamente!

🔍 Verifica:
- Controlla i logs su Railway
- Dovresti vedere: "🚂 Running on Railway platform"
- Il bot dovrebbe rispondere su Telegram

❓ Problemi?
- Assicurati che il token sia corretto
- Riavvia il servizio se necessario
- Controlla i logs per errori
    """)

def main():
    """Funzione principale"""
    print_banner()
    
    # Aggiorna configurazioni
    update_config_files()
    
    # Commit e push
    if not commit_and_push():
        print("\n❌ Errore durante commit/push. Fix manuale necessario.")
        return
    
    # Istruzioni
    print_instructions()
    
    print("\n🎉 Fix token completato!")
    print("📚 Ora vai su Railway e aggiorna il token nelle Variables!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Fix annullato dall'utente.")
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")
        print("Contatta il supporto se il problema persiste.")
