#!/usr/bin/env python3
"""
Script per risolvere il conflitto del bot
"""

import requests
import time

def disable_webhook(token):
    """Disabilita webhook per il bot"""
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    try:
        response = requests.post(url)
        if response.status_code == 200:
            print(f"✅ Webhook disabilitato per bot {token}")
            return True
        else:
            print(f"❌ Errore nel disabilitare webhook: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Errore nella richiesta: {e}")
        return False

def get_bot_info(token):
    """Ottieni informazioni sul bot"""
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Bot trovato: {bot_info.get('first_name')} (@{bot_info.get('username')})")
                return True
            else:
                print(f"❌ Bot non valido: {data.get('description', 'Token non valido')}")
                return False
        else:
            print(f"❌ Errore API: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Errore nella richiesta: {e}")
        return False

def main():
    print("🔧 Risoluzione conflitto bot...")
    
    # Token problematico
    old_token = "7576082688:AAGJz-v5NG8QGKCezBA5qlhI3lYiatsgRd8"
    
    print(f"\n1. Verificando bot con token: {old_token}")
    if get_bot_info(old_token):
        print(f"\n2. Disabilitando webhook per {old_token}")
        if disable_webhook(old_token):
            print("✅ Webhook disabilitato! Il bot ora può essere usato su Railway.")
        else:
            print("❌ Impossibile disabilitare webhook. Prova a fermare il bot manualmente.")
    
    print(f"\n3. Verificando bot con token: 8237710386:AAF9MmADLR0PfihDtK8ZTmeDRi884MbV8HM")
    if get_bot_info("8237710386:AAF9MmADLR0PfihDtK8ZTmeDRi884MbV8HM"):
        print("✅ Il bot principale è disponibile!")
    
    print("\n🎯 SOLUZIONI:")
    print("1. Vai su Railway Dashboard")
    print("2. Imposta BOT_TOKEN = 8237710386:AAF9MmADLR0PfihDtK8ZTmeDRi884MbV8HM")
    print("3. Riavvia il servizio")
    print("4. Il bot funzionerà perfettamente!")

if __name__ == "__main__":
    main()
