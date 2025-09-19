#!/usr/bin/env python3
"""
Test script per verificare le funzioni di ricerca
"""

import asyncio
import sys
import os

# Aggiungi il percorso corrente al Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_search():
    """Test delle funzioni di ricerca"""
    try:
        from gigliotube import SuperYouTubeDownloader
        
        print("🔍 Testando le funzioni di ricerca...")
        
        # Crea istanza del downloader
        downloader = SuperYouTubeDownloader()
        
        # Test ricerca
        print("🔍 Cercando 'test music'...")
        results = await downloader.search_youtube("test music", max_results=3)
        
        if results:
            print(f"✅ Trovati {len(results)} risultati:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.get('title', 'N/A')} - {result.get('uploader', 'N/A')}")
        else:
            print("❌ Nessun risultato trovato")
            
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())