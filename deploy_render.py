#!/usr/bin/env python3
"""
🚀 GiglioTube Bot - Deploy Script per Render.com
Script automatico per configurare e deployare il bot su Render
"""

import os
import sys
import subprocess
import json
import webbrowser
from pathlib import Path

def print_banner():
    """Stampa il banner del bot"""
    print("""
🎧✨ ================================================ ✨🎧
🚀        GIGLIOTUBE BOT - DEPLOY AUTOMATICO        🚀
🎧✨ ================================================ ✨🎧

🎯 Deploy gratuito su Render.com in 3 semplici passi!
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
        print("   Download: https://git-scm.com/downloads")
        return False
    
    # Controlla se siamo in un repository git
    try:
        subprocess.run(['git', 'status'], capture_output=True, check=True)
        print("✅ Repository Git trovato")
    except subprocess.CalledProcessError:
        print("❌ Non sei in un repository Git!")
        print("   Esegui: git init && git add . && git commit -m 'Initial commit'")
        return False
    
    # Controlla file necessari
    required_files = [
        'gigliotube.py',
        'start_render.py', 
        'requirements.txt',
        'render.yaml',
        'config_render.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ File mancanti: {', '.join(missing_files)}")
        return False
    
    print("✅ Tutti i file necessari trovati")
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

def update_config(token):
    """Aggiorna la configurazione con il token"""
    print("⚙️  Aggiornamento configurazione...")
    
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
    
    print("✅ Configurazione aggiornata")

def create_env_file(token):
    """Crea file .env per test locale"""
    env_content = f"""# GiglioTube Bot Environment Variables
BOT_TOKEN={token}
PYTHONUNBUFFERED=1
TZ=Europe/Rome
RENDER=true
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ File .env creato")

def commit_changes():
    """Committa le modifiche su Git"""
    print("📝 Commit modifiche su Git...")
    
    try:
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Deploy ready for Render'], check=True)
        print("✅ Modifiche committate")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore durante commit: {e}")
        return False

def push_to_github():
    """Push su GitHub"""
    print("🚀 Push su GitHub...")
    
    try:
        # Controlla se esiste un remote origin
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Nessun remote GitHub configurato!")
            print("   Configura GitHub:")
            print("   1. Crea repository su GitHub")
            print("   2. Esegui: git remote add origin https://github.com/tuo-username/repo.git")
            return False
        
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("✅ Push su GitHub completato")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore durante push: {e}")
        return False

def open_render_dashboard():
    """Apre il dashboard di Render"""
    print("\n🌐 Apertura dashboard Render...")
    webbrowser.open('https://render.com/dashboard')
    print("✅ Dashboard Render aperto nel browser")

def print_deploy_instructions():
    """Stampa le istruzioni per il deploy"""
    print("""
🎯 ISTRUZIONI DEPLOY SU RENDER:

1. 🌐 Vai su https://render.com (già aperto nel browser)
2. 🔐 Fai login con GitHub
3. ➕ Clicca "New +" → "Web Service"
4. 🔗 Connetti il tuo repository GitHub
5. ⚙️  Configura:
   - Name: gigliotube-bot
   - Environment: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: python start_render.py
6. 🔑 Environment Variables:
   - BOT_TOKEN: [il tuo token]
   - PYTHONUNBUFFERED: 1
   - TZ: Europe/Rome
   - RENDER: true
7. 🚀 Clicca "Create Web Service"
8. ⏳ Aspetta 5-10 minuti per il deploy
9. 🎉 Il bot sarà online!

📱 Test del bot:
- Cerca il tuo bot su Telegram
- Invia /start
- Testa con un URL YouTube

🔍 Monitoraggio:
- Dashboard Render → Logs per vedere i log in tempo reale
- Il bot si riavvia automaticamente se si blocca

❓ Problemi?
- Controlla i logs su Render
- Verifica che il token sia corretto
- Assicurati che FFmpeg sia installato (Render lo fa automaticamente)
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
    
    # Aggiorna configurazione
    update_config(token)
    create_env_file(token)
    
    # Commit e push
    if not commit_changes():
        print("\n❌ Errore durante commit. Deploy annullato.")
        return
    
    if not push_to_github():
        print("\n❌ Errore durante push. Deploy annullato.")
        return
    
    # Apri dashboard e istruzioni
    open_render_dashboard()
    print_deploy_instructions()
    
    print("\n🎉 Setup completato! Segui le istruzioni sopra per completare il deploy.")
    print("📚 Per maggiori dettagli, leggi DEPLOYMENT_GUIDE.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Deploy annullato dall'utente.")
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")
        print("Contatta il supporto se il problema persiste.")
