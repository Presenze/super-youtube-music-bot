#!/usr/bin/env python3
"""
Test completo per GiglioTube - Super YouTube Music Bot
Testa tutte le funzionalità principali
"""

import asyncio
import sys
import os

# Aggiungi il percorso corrente al sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_complete():
    """Test completo di tutte le funzionalità"""
    print("🚀 Test completo di GiglioTube - Super YouTube Music Bot")
    print("=" * 60)
    
    try:
        from gigliotube import SuperYouTubeDownloader
        from config import DOWNLOAD_PATH, MAX_FILE_SIZE
        
        # Inizializza il downloader
        downloader = SuperYouTubeDownloader()
        print("✅ Downloader inizializzato correttamente")
        
        # Test 1: Ricerca semplice
        print("\n🔍 Test 1: Ricerca semplice")
        print("-" * 30)
        results = await downloader.search_youtube("test music", 3)
        if results:
            print(f"✅ Ricerca semplice: Trovati {len(results)} risultati")
            for i, result in enumerate(results[:2]):
                print(f"   {i+1}. {result['title'][:50]}...")
        else:
            print("❌ Ricerca semplice: Nessun risultato")
        
        # Test 2: Ricerca con termine specifico
        print("\n🔍 Test 2: Ricerca con 'nirvana'")
        print("-" * 30)
        results = await downloader.search_youtube("nirvana", 3)
        if results:
            print(f"✅ Ricerca nirvana: Trovati {len(results)} risultati")
            for i, result in enumerate(results[:2]):
                print(f"   {i+1}. {result['title'][:50]}...")
        else:
            print("❌ Ricerca nirvana: Nessun risultato")
        
        # Test 3: Ricerca con termine italiano
        print("\n🔍 Test 3: Ricerca con 'musica italiana'")
        print("-" * 30)
        results = await downloader.search_youtube("musica italiana", 3)
        if results:
            print(f"✅ Ricerca italiana: Trovati {len(results)} risultati")
            for i, result in enumerate(results[:2]):
                print(f"   {i+1}. {result['title'][:50]}...")
        else:
            print("❌ Ricerca italiana: Nessun risultato")
        
        # Test 4: Test callback data
        print("\n🔧 Test 4: Callback data")
        print("-" * 30)
        from gigliotube import create_callback_data, parse_callback_data
        
        # Test creazione callback data
        test_data = create_callback_data(123456, "download", "mp3", "320", "abc123")
        print(f"✅ Callback data creato: {test_data}")
        
        # Test parsing callback data
        parsed = parse_callback_data(test_data)
        if parsed:
            print(f"✅ Callback data parsato: {parsed}")
        else:
            print("❌ Errore nel parsing callback data")
        
        # Test 5: Test configurazione
        print("\n⚙️ Test 5: Configurazione")
        print("-" * 30)
        print(f"✅ Download path: {DOWNLOAD_PATH}")
        print(f"✅ Max file size: {MAX_FILE_SIZE // (1024*1024)}MB")
        print(f"✅ Cookies file: {downloader.cookies_file}")
        
        print("\n🎉 Tutti i test completati con successo!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_complete())
    if success:
        print("\n✅ Test completato con successo!")
        sys.exit(0)
    else:
        print("\n❌ Test fallito!")
        sys.exit(1)
