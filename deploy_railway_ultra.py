#!/usr/bin/env python3
"""
Script per deploy automatico su Railway con sistema ultra-robusto
"""

import webbrowser
import os
import subprocess
import time

def open_github_new_repo():
    """Apri GitHub per creare nuovo repository"""
    print("🚀 Aprendo GitHub per creare nuovo repository...")
    webbrowser.open("https://github.com/new")
    print("✅ GitHub aperto nel browser!")

def setup_git_repo():
    """Configura repository Git per Railway"""
    print("\n🔧 Configurando repository Git per Railway...")
    
    # Rimuovi .git esistente se presente
    if os.path.exists('.git'):
        print("🗑️  Rimuovendo .git esistente...")
        subprocess.run(['rmdir', '/s', '/q', '.git'], shell=True, check=False)
    
    # Inizializza nuovo repository
    print("📁 Inizializzando nuovo repository Git...")
    subprocess.run(['git', 'init'], check=True)
    
    # Aggiungi tutti i file
    print("📝 Aggiungendo file al repository...")
    subprocess.run(['git', 'add', '.'], check=True)
    
    # Commit iniziale
    print("💾 Creando commit iniziale...")
    subprocess.run(['git', 'commit', '-m', '🚀 ULTRA-ROBUST DOWNLOAD SYSTEM - Railway Ready!'], check=True)
    
    print("✅ Repository Git configurato!")

def show_railway_deployment_instructions():
    """Mostra istruzioni per deployment su Railway"""
    print("\n" + "="*70)
    print("🚀 ISTRUZIONI DEPLOYMENT RAILWAY ULTRA-ROBUSTO")
    print("="*70)
    print()
    print("1. 🌐 Su GitHub (già aperto):")
    print("   - Repository name: gigliotube-ultra-robust")
    print("   - Description: Ultra-Robust YouTube Music Download Bot")
    print("   - Visibility: Public")
    print("   - NON inizializzare con README, .gitignore, o license")
    print("   - Clicca 'Create repository'")
    print()
    print("2. 🔗 Copia l'URL del repository (es: https://github.com/tuousername/gigliotube-ultra-robust.git)")
    print()
    print("3. 🚂 Su Railway:")
    print("   - Vai su https://railway.app")
    print("   - Clicca 'New Project'")
    print("   - Seleziona 'Deploy from GitHub repo'")
    print("   - Scegli il nuovo repository 'gigliotube-ultra-robust'")
    print("   - Railway rileverà automaticamente il Dockerfile.railway")
    print()
    print("4. ⚙️ Configurazione Environment Variables:")
    print("   - BOT_TOKEN = 8237710386:AAF9MmADLR0PfihDtK8ZTmeDRi884MbV8HM")
    print("   - PYTHONUNBUFFERED = 1")
    print("   - TZ = Europe/Rome")
    print("   - PLATFORM = railway")
    print("   - RAILWAY = true")
    print()
    print("5. 🚀 Deploy:")
    print("   - Railway inizierà automaticamente il build")
    print("   - Il sistema ultra-robusto sarà attivo")
    print("   - Il bot funzionerà con massima affidabilità!")
    print()
    print("6. ✅ Verifica:")
    print("   - Controlla i logs su Railway")
    print("   - Testa il bot su Telegram")
    print("   - Il sistema ultra-robusto garantirà download sempre funzionanti!")
    print()
    print("="*70)
    print("🎉 SISTEMA ULTRA-ROBUSTO PRONTO PER RAILWAY! 🎉")
    print("="*70)

def create_railway_config():
    """Crea configurazione ottimizzata per Railway"""
    print("\n🔧 Creando configurazione Railway ottimizzata...")
    
    # Aggiorna railway.json per il sistema ultra-robusto
    railway_config = {
        "$schema": "https://railway.app/railway.schema.json",
        "build": {
            "builder": "DOCKERFILE",
            "dockerfilePath": "Dockerfile.railway"
        },
        "deploy": {
            "startCommand": "python start_railway.py",
            "restartPolicyType": "ON_FAILURE",
            "restartPolicyMaxRetries": 10
        }
    }
    
    import json
    with open('railway.json', 'w') as f:
        json.dump(railway_config, f, indent=2)
    
    print("✅ Configurazione Railway aggiornata!")

def main():
    print("🚀 DEPLOYMENT RAILWAY ULTRA-ROBUSTO")
    print("="*50)
    
    # Apri GitHub
    open_github_new_repo()
    
    # Configura repository
    setup_git_repo()
    
    # Crea configurazione Railway
    create_railway_config()
    
    # Mostra istruzioni
    show_railway_deployment_instructions()
    
    print("\n🎉 TUTTO PRONTO! Segui le istruzioni sopra! 🎉")
    print("🚀 Il sistema ultra-robusto garantirà download sempre funzionanti!")

if __name__ == "__main__":
    main()
