#!/usr/bin/env python3
"""
🚀 GiglioTube Bot - Test All Deployments
Script per testare tutte le opzioni di deploy gratuite
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def print_banner():
    """Stampa il banner del bot"""
    print("""
🎧✨ ================================================ ✨🎧
🚀     GIGLIOTUBE BOT - TEST TUTTE LE OPZIONI        🚀
🎧✨ ================================================ ✨🎧

🎯 Testa tutte le opzioni di deploy gratuite!
    """)

def check_requirements():
    """Controlla i requisiti per il deploy"""
    print("🔍 Controllo requisiti...")
    
    # Controlla se git è installato
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
        print("✅ Git installato")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git non installato! Installa Git prima di continuare.")
        return False
    
    # Controlla se siamo in un repository git
    try:
        subprocess.run(['git', 'status'], capture_output=True, check=True)
        print("✅ Repository Git trovato")
    except subprocess.CalledProcessError:
        print("❌ Non sei in un repository Git!")
        print("   Esegui: git init && git add . && git commit -m 'Initial commit'")
        return False
    
    print("✅ Tutti i requisiti soddisfatti")
    return True

def get_bot_token():
    """Ottiene il token del bot dall'utente"""
    print("\n🤖 Configurazione Bot Telegram:")
    print("1. Vai su https://t.me/BotFather")
    print("2. Crea un nuovo bot con /newbot")
    print("3. Copia il token che ricevi")
    print()
    
    while True:
        token = input("🔑 Inserisci il token del bot: ").strip()
        
        if not token:
            print("❌ Token non può essere vuoto!")
            continue
            
        if not token.count(':') == 1:
            print("❌ Formato token non valido! Dovrebbe essere: 123456789:ABCdef...")
            continue
            
        if len(token.split(':')[0]) < 8:
            print("❌ Token sembra troppo corto!")
            continue
            
        return token

def update_all_configs(token):
    """Aggiorna tutte le configurazioni con il token"""
    print("⚙️  Aggiornamento configurazioni...")
    
    # Aggiorna config_render.py
    config_content = f'''import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    # Fallback token for testing
    BOT_TOKEN = "{token}"
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
        f.write(config_content)
    
    # Aggiorna main_replit.py
    replit_content = f'''#!/usr/bin/env python3
"""
GiglioTube Bot - Main file for Replit deployment
"""

import os
import sys
import logging

# Set up logging for Replit
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for Replit deployment"""
    logger.info("🚀 Starting GiglioTube Bot on Replit...")
    
    # Set token for Replit
    os.environ['BOT_TOKEN'] = '{token}'
    
    # Check if we're on Replit
    if os.getenv('REPL_ID'):
        logger.info("✅ Running on Replit platform")
    else:
        logger.info("ℹ️  Running locally")
    
    # Import and run the bot
    try:
        from gigliotube import main as bot_main
        logger.info("✅ Bot module imported successfully")
        bot_main()
    except ImportError as e:
        logger.error(f"❌ Failed to import bot module: {{e}}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Bot startup failed: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open('main_replit.py', 'w', encoding='utf-8') as f:
        f.write(replit_content)
    
    # Crea file .env
    env_content = f"""# GiglioTube Bot Environment Variables
BOT_TOKEN={token}
PYTHONUNBUFFERED=1
TZ=Europe/Rome
RENDER=true
REPLIT=true
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Configurazioni aggiornate")

def commit_and_push():
    """Committa e pusha le modifiche"""
    print("📝 Commit e push modifiche...")
    
    try:
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Ready for all deployments'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("✅ Modifiche committate e pushate")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore durante commit/push: {e}")
        return False

def show_deployment_options():
    """Mostra tutte le opzioni di deploy"""
    print("""
🎯 OPZIONI DI DEPLOY DISPONIBILI:

1. 🚀 RENDER.COM (RACCOMANDATO #1)
   ✅ Completamente gratuito per sempre
   ✅ FFmpeg preinstallato
   ✅ Molto stabile
   🌐 https://render.com

2. 🚂 RAILWAY.APP (RACCOMANDATO #2)
   ✅ $5 crediti gratuiti/mese
   ✅ Database incluso
   ✅ Monitoring avanzato
   🌐 https://railway.app

3. 🎨 REPLIT (PER PRINCIPIANTI)
   ✅ Completamente gratuito
   ✅ Editor online integrato
   ✅ Deploy con un click
   🌐 https://replit.com

4. ⚡ CYCLIC.SH (ULTRA VELOCE)
   ✅ Completamente gratuito
   ✅ Deploy automatico
   ✅ Molto veloce
   🌐 https://cyclic.sh

5. 🚀 VERCEL (PER DEVELOPER)
   ✅ Hobby plan gratuito
   ✅ CDN globale
   ✅ Molto professionale
   🌐 https://vercel.com

6. 🟣 HEROKU (CLASSICO)
   ✅ Hobby plan gratuito
   ✅ Molto stabile
   ⚠️ Si spegne dopo 30 min di inattività
   🌐 https://heroku.com
    """)

def open_all_platforms():
    """Apre tutte le piattaforme nel browser"""
    print("🌐 Apertura piattaforme nel browser...")
    
    platforms = [
        "https://render.com/dashboard",
        "https://railway.app/dashboard",
        "https://replit.com",
        "https://cyclic.sh",
        "https://vercel.com/dashboard",
        "https://heroku.com/dashboard"
    ]
    
    for platform in platforms:
        try:
            webbrowser.open(platform)
            print(f"✅ Aperto: {platform}")
        except Exception as e:
            print(f"❌ Errore apertura {platform}: {e}")

def print_deployment_instructions():
    """Stampa le istruzioni per il deploy"""
    print("""
🎯 ISTRUZIONI DEPLOY:

🚀 RENDER.COM (RACCOMANDATO):
1. Vai su https://render.com (già aperto)
2. Login con GitHub
3. "New +" → "Web Service"
4. Connetti repository
5. Configura:
   - Build Command: pip install -r requirements.txt
   - Start Command: python start_render.py
6. Environment Variables:
   - BOT_TOKEN: [il tuo token]
   - PYTHONUNBUFFERED: 1
   - TZ: Europe/Rome
   - RENDER: true
7. Deploy! 🎉

🚂 RAILWAY.APP:
1. Vai su https://railway.app (già aperto)
2. Login con GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Seleziona repository
5. Environment Variables:
   - BOT_TOKEN: [il tuo token]
   - PYTHONUNBUFFERED: 1
   - TZ: Europe/Rome
6. Deploy! 🎉

🎨 REPLIT (PIÙ FACILE):
1. Vai su https://replit.com (già aperto)
2. Login con GitHub
3. "Create Repl" → "Import from GitHub repo"
4. Inserisci URL repository
5. Environment Variables:
   - BOT_TOKEN: [il tuo token]
6. Clicca "Run"! 🎉

⚡ CYCLIC.SH:
1. Vai su https://cyclic.sh (già aperto)
2. Login con GitHub
3. "Deploy Now" → Seleziona repository
4. Environment Variables:
   - BOT_TOKEN: [il tuo token]
   - PYTHONUNBUFFERED: 1
   - TZ: Europe/Rome
5. Deploy! 🎉

🚀 VERCEL:
1. Vai su https://vercel.com (già aperto)
2. Login con GitHub
3. "New Project" → Seleziona repository
4. Environment Variables:
   - BOT_TOKEN: [il tuo token]
   - PYTHONUNBUFFERED: 1
   - TZ: Europe/Rome
5. Deploy! 🎉

🟣 HEROKU:
1. Vai su https://heroku.com (già aperto)
2. Login con GitHub
3. "New" → "Create new app"
4. Connetti repository
5. Environment Variables:
   - BOT_TOKEN: [il tuo token]
   - PYTHONUNBUFFERED: 1
   - TZ: Europe/Rome
6. Deploy! 🎉
    """)

def main():
    """Funzione principale"""
    print_banner()
    
    # Controlla requisiti
    if not check_requirements():
        print("\n❌ Requisiti non soddisfatti. Risolvi i problemi sopra e riprova.")
        return
    
    # Ottieni token bot
    token = get_bot_token()
    
    # Aggiorna configurazioni
    update_all_configs(token)
    
    # Commit e push
    if not commit_and_push():
        print("\n❌ Errore durante commit/push. Deploy annullato.")
        return
    
    # Mostra opzioni
    show_deployment_options()
    
    # Apri piattaforme
    open_all_platforms()
    
    # Istruzioni
    print_deployment_instructions()
    
    print("\n🎉 Setup completato per TUTTE le piattaforme!")
    print("📚 Per maggiori dettagli, leggi TUTTE_OPZIONI_DEPLOY.md")
    print("🚀 Scegli la piattaforma che preferisci e segui le istruzioni!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Deploy annullato dall'utente.")
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")
        print("Contatta il supporto se il problema persiste.")
