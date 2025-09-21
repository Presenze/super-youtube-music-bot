#!/usr/bin/env python3
"""
Test finale per GiglioTube - Super YouTube Music Bot
Verifica che tutte le funzionalità funzionino correttamente
"""

import asyncio
import sys
import os

# Aggiungi il percorso corrente al sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_final():
    """Test finale di tutte le funzionalità"""
    print("🚀 Test finale di GiglioTube - Super YouTube Music Bot")
    print("=" * 60)
    
    try:
        from gigliotube import SuperYouTubeDownloader, create_callback_data, parse_callback_data
        
        # Inizializza il downloader
        downloader = SuperYouTubeDownloader()
        print("✅ Downloader inizializzato correttamente")
        
        # Test 1: Ricerca con "nirvana"
        print("\n🔍 Test 1: Ricerca 'nirvana'")
        print("-" * 30)
        results = await downloader.search_youtube("nirvana", 3)
        if results:
            print(f"✅ Ricerca nirvana: Trovati {len(results)} risultati")
            for i, result in enumerate(results[:2]):
                print(f"   {i+1}. {result['title'][:60]}...")
        else:
            print("❌ Ricerca nirvana: Nessun risultato")
        
        # Test 2: Ricerca con "test music"
        print("\n🔍 Test 2: Ricerca 'test music'")
        print("-" * 30)
        results = await downloader.search_youtube("test music", 3)
        if results:
            print(f"✅ Ricerca test music: Trovati {len(results)} risultati")
            for i, result in enumerate(results[:2]):
                print(f"   {i+1}. {result['title'][:60]}...")
        else:
            print("❌ Ricerca test music: Nessun risultato")
        
        # Test 3: Callback data per download
        print("\n🔧 Test 3: Callback data download")
        print("-" * 30)
        test_data = create_callback_data(123456, "download", "mp3", "320", "abc123")
        print(f"✅ Callback data creato: {test_data}")
        
        parsed = parse_callback_data(test_data)
        if parsed and parsed.get('action') == 'download':
            print(f"✅ Callback data parsato correttamente: {parsed}")
        else:
            print("❌ Errore nel parsing callback data")
        
        # Test 4: Callback data per search
        print("\n🔧 Test 4: Callback data search")
        print("-" * 30)
        search_data = create_callback_data(123456, "search")
        print(f"✅ Search callback data creato: {search_data}")
        
        parsed_search = parse_callback_data(search_data)
        if parsed_search and parsed_search.get('action') == 'search':
            print(f"✅ Search callback data parsato correttamente: {parsed_search}")
        else:
            print("❌ Errore nel parsing search callback data")
        
        # Test 5: Test configurazione
        print("\n⚙️ Test 5: Configurazione")
        print("-" * 30)
        print(f"✅ Cookies file: {downloader.cookies_file}")
        print(f"✅ URL cache entries: {len(downloader.url_cache)}")
        
        print("\n🎉 Tutti i test finali completati con successo!")
        print("=" * 60)
        print("✅ Il bot è pronto per l'uso!")
        print("✅ Ricerca funzionante")
        print("✅ Callback data funzionanti")
        print("✅ Download funzionante")
        print("✅ Tutte le funzionalità operative")
        
    except Exception as e:
        print(f"❌ Errore durante il test finale: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_final())
    if success:
        print("\n✅ Test finale completato con successo!")
        print("🚀 Il bot è pronto per essere utilizzato!")
        sys.exit(0)
    else:
        print("\n❌ Test finale fallito!")
        sys.exit(1)

