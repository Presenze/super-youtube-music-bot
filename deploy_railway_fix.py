#!/usr/bin/env python3
"""
🚂 GiglioTube Bot - Railway Fix Deploy Script
Script per committare e deployare le correzioni per Railway
"""

import os
import sys
import subprocess
import webbrowser

def print_banner():
    """Stampa il banner del bot"""
    print("""
🚂✨ ================================================ ✨🚂
🚀        GIGLIOTUBE BOT - RAILWAY FIX DEPLOY        🚀
🚂✨ ================================================ ✨🚂

🎯 Deploy delle correzioni per Railway in 3 semplici passi!
    """)

def check_git():
    """Controlla se git è configurato"""
    print("🔍 Controllo Git...")
    
    try:
        # Controlla se siamo in un repository git
        subprocess.run(['git', 'status'], capture_output=True, check=True)
        print("✅ Repository Git trovato")
        return True
    except subprocess.CalledProcessError:
        print("❌ Non sei in un repository Git!")
        print("   Esegui: git init && git add . && git commit -m 'Initial commit'")
        return False

def commit_changes():
    """Committa le modifiche"""
    print("📝 Commit modifiche...")
    
    try:
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Fix Railway deployment - no dotenv dependency'], check=True)
        print("✅ Modifiche committate")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore durante commit: {e}")
        return False

def push_to_github():
    """Push su GitHub"""
    print("🚀 Push su GitHub...")
    
    try:
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("✅ Push su GitHub completato")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Errore durante push: {e}")
        return False

def open_railway():
    """Apre Railway nel browser"""
    print("🌐 Apertura Railway...")
    webbrowser.open('https://railway.app/dashboard')
    print("✅ Railway aperto nel browser")

def print_instructions():
    """Stampa le istruzioni per il deploy"""
    print("""
🎯 ISTRUZIONI DEPLOY SU RAILWAY:

1. 🌐 Vai su https://railway.app (già aperto nel browser)
2. 🔐 Fai login con GitHub
3. ➕ Clicca "New Project" → "Deploy from GitHub repo"
4. 🔗 Seleziona il tuo repository
5. ⚙️  Railway userà automaticamente:
   - railway.json per la configurazione
   - requirements-railway.txt per le dipendenze
   - start_railway.py per avviare il bot
6. 🔑 Environment Variables (su Railway Dashboard):
   - BOT_TOKEN: [il tuo token]
   - PYTHONUNBUFFERED: 1
   - TZ: Europe/Rome
   - RAILWAY: true
7. 🚀 Deploy automatico!
8. ⏳ Aspetta 2-3 minuti per il deploy
9. 🎉 Il bot sarà online!

🔍 Monitoraggio:
- Dashboard Railway → Logs per vedere i log in tempo reale
- Dovresti vedere: "🚂 Running on Railway platform"
- Dovresti vedere: "✅ Using Railway configuration"

❓ Problemi?
- Controlla i logs su Railway
- Verifica che le environment variables siano impostate
- Il bot ora usa config_railway.py (senza dotenv!)
    """)

def main():
    """Funzione principale"""
    print_banner()
    
    # Controlla Git
    if not check_git():
        print("\n❌ Git non configurato. Risolvi il problema e riprova.")
        return
    
    # Commit modifiche
    if not commit_changes():
        print("\n❌ Errore durante commit. Deploy annullato.")
        return
    
    # Push su GitHub
    if not push_to_github():
        print("\n❌ Errore durante push. Deploy annullato.")
        return
    
    # Apri Railway
    open_railway()
    
    # Istruzioni
    print_instructions()
    
    print("\n🎉 Fix Railway completato!")
    print("📚 Per maggiori dettagli, leggi RAILWAY_FIX.md")
    print("🚂 Il tuo bot ora funziona perfettamente su Railway! 🚂")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Deploy annullato dall'utente.")
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")
        print("Contatta il supporto se il problema persiste.")
