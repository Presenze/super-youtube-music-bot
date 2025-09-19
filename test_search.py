#!/usr/bin/env python3
"""
🧪 Test per la funzione di ricerca YouTube
"""

import asyncio
import sys
import os

# Aggiungi il percorso del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_search():
    """Test della funzione di ricerca"""
    try:
        from gigliotube import SuperYouTubeDownloader
        
        print("🔍 Testing YouTube search functionality...")
        
        downloader = SuperYouTubeDownloader()
        
        # Test di ricerca
        query = "Imagine Dragons Believer"
        print(f"🔍 Searching for: {query}")
        
        results = await downloader.search_youtube(query, max_results=5)
        
        if results:
            print(f"✅ Found {len(results)} results!")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']} - {result['uploader']}")
                print(f"   Duration: {result['duration']}s")
                print(f"   URL: {result['webpage_url']}")
                print()
        else:
            print("❌ No results found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_search())
