import asyncio
import os
import logging
try:
    import yt_dlp
    HAS_YT_DLP = True
except ImportError:
    HAS_YT_DLP = False
    print("Warning: yt-dlp not available, download functionality will be limited")
import json
import time
import re
import hashlib
import subprocess
import sys
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.error import Conflict, BadRequest
# Try to import optional dependencies
try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False
    print("Warning: aiofiles not available, using standard file operations")

import shutil

# Platform-specific configuration loading
import os

# Check if we're on Railway
if os.getenv('RAILWAY') or os.getenv('RAILWAY_ENVIRONMENT'):
    try:
        from config_railway import *
        print("✅ Using Railway configuration")
    except ImportError:
        print("⚠️  Railway config not found, trying production config")
        try:
            from config_production import *
        except ImportError:
            from config_render import *
else:
    # Try production config first, then fallback
    try:
        from config_production import *
    except ImportError:
        try:
            from config import *
        except ImportError:
            from config_render import *

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create directories
os.makedirs(DOWNLOAD_PATH, exist_ok=True)
os.makedirs("data", exist_ok=True)

def check_ffmpeg():
    """Controlla se FFmpeg è installato"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def clean_text(text):
    """Pulisce il testo per evitare errori di parsing markdown"""
    if not text:
        return ""
    # Rimuovi tutti i caratteri speciali che possono causare errori di parsing
    text = re.sub(r'[*_`\[\]()~>#+=|{}.!-]', '', str(text))
    # Rimuovi anche emoji e caratteri speciali
    text = re.sub(r'[^\w\s]', '', text)
    return text[:100] + "..." if len(text) > 100 else text

def create_callback_data(user_id, action, format_type=None, quality=None, url_hash=None):
    """Crea callback data sicuro e corto (max 64 byte) - VERSIONE ULTRA-ROBUSTA"""
    if action == "download":
        # Usa hash più lungo ma sicuro
        short_hash = url_hash[:6] if url_hash else "000000"
        # Abbrevia format_type e quality in modo più sicuro
        fmt_map = {"mp3": "m3", "m4a": "m4", "wav": "wv", "flac": "fl"}
        qual_map = {"128": "12", "192": "19", "320": "32", "64": "64"}
        
        fmt_short = fmt_map.get(format_type, "m3")
        qual_short = qual_map.get(quality, "32")
        
        # Usa solo le ultime 3 cifre dell'user_id per lasciare più spazio all'hash
        user_short = str(user_id)[-3:] if len(str(user_id)) > 3 else str(user_id)
        callback_data = f"dl_{user_short}_{fmt_short}_{qual_short}_{short_hash}"
        
        # Verifica lunghezza massima
        if len(callback_data) > 64:
            # Fallback con hash più corto
            short_hash = url_hash[:4] if url_hash else "0000"
            user_short = str(user_id)[-2:] if len(str(user_id)) > 2 else str(user_id)
            callback_data = f"dl_{user_short}_{fmt_short}_{qual_short}_{short_hash}"
        
        logger.info(f"Created callback data: {callback_data} (length: {len(callback_data)})")
        return callback_data
    elif action == "stats":
        return f"st_{user_id}"
    elif action == "settings":
        return f"se_{user_id}"
    elif action == "language":
        return f"lg_{user_id}"
    elif action == "search":
        return f"sr_{user_id}"
    elif action == "set_lang":
        return f"sl_{user_id}_{format_type}"  # format_type = language
    return f"cb_{user_id}_{action}"

def parse_callback_data(data):
    """Parsa callback data - VERSIONE ULTRA-ROBUSTA CON VALIDAZIONE"""
    if not data or not isinstance(data, str):
        logger.error(f"Invalid callback data type: {type(data)}")
        return None
        
    parts = data.split("_")
    if len(parts) < 2:
        logger.error(f"Invalid callback data format: {data}")
        return None
    
    try:
        if parts[0] == "dl" and len(parts) >= 5:
            # Espandi le abbreviazioni con mappa corretta
            format_map = {"m3": "mp3", "m4": "m4a", "wv": "wav", "fl": "flac"}
            quality_map = {"32": "320", "19": "192", "12": "128", "64": "64"}
            
            format_type = format_map.get(parts[2], "mp3")
            quality = quality_map.get(parts[3], "320")
            
            # Gestisci user_id - usa quello dal contesto della callback query
            user_id_short = parts[1]
            user_id = int(user_id_short) if user_id_short.isdigit() else 0
            
            # L'hash può essere più lungo ora
            url_hash = parts[4]
            
            logger.info(f"Parsed callback data: user_id={user_id}, format={format_type}, quality={quality}, hash={url_hash}")
            
            return {
                "action": "download",
                "user_id": user_id,
                "format": format_type,
                "quality": quality,
                "url_hash": url_hash
            }
        elif parts[0] == "st":
            return {"action": "stats", "user_id": int(parts[1])}
        elif parts[0] == "se":
            return {"action": "settings", "user_id": int(parts[1])}
        elif parts[0] == "lg":
            return {"action": "language", "user_id": int(parts[1])}
        elif parts[0] == "sr":
            return {"action": "search", "user_id": int(parts[1])}
        elif parts[0] == "sl" and len(parts) >= 3:
            return {"action": "set_lang", "user_id": int(parts[1]), "language": parts[2]}
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing callback data '{data}': {e}")
        return None
    
    logger.error(f"Unknown callback data format: {data}")
    return None

class SuperYouTubeDownloader:
    def __init__(self):
        self.active_downloads = {}
        self.download_stats = self.load_stats()
        self.user_preferences = self.load_preferences()
        self.user_languages = self.load_languages()
        self.url_cache = {}  # Cache per URL hash
        self.ffmpeg_available = check_ffmpeg()
        self.cookies_file = self.find_cookies_file()
    
    def find_cookies_file(self):
        """Cerca file di cookies per YouTube"""
        possible_paths = [
            "cookies.txt",
            "youtube_cookies.txt",
            "cookies.json",
            os.path.expanduser("~/.config/youtube-dl/cookies.txt"),
            os.path.expanduser("~/.config/yt-dlp/cookies.txt"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found cookies file: {path}")
                return path
        
        # Prova a generare cookies automaticamente
        try:
            self.generate_cookies_automatically()
            if os.path.exists("cookies.txt"):
                logger.info("Generated cookies automatically")
                return "cookies.txt"
        except Exception as e:
            logger.warning(f"Could not generate cookies: {e}")
        
        logger.info("No cookies file found - using without authentication")
        return None
    
    def generate_cookies_automatically(self):
        """Genera cookies automaticamente usando yt-dlp"""
        try:
            import subprocess
            # Prova a generare cookies dal browser
            cmd = [
                "yt-dlp", 
                "--cookies-from-browser", "chrome",
                "--cookies", "cookies.txt",
                "--no-download",
                "https://youtube.com"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and os.path.exists("cookies.txt"):
                logger.info("Successfully generated cookies from Chrome")
                return True
        except Exception as e:
            logger.warning(f"Chrome cookies generation failed: {e}")
        
        try:
            # Prova con Firefox
            cmd = [
                "yt-dlp", 
                "--cookies-from-browser", "firefox",
                "--cookies", "cookies.txt",
                "--no-download",
                "https://youtube.com"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and os.path.exists("cookies.txt"):
                logger.info("Successfully generated cookies from Firefox")
                return True
        except Exception as e:
            logger.warning(f"Firefox cookies generation failed: {e}")
        
        return False
    
    def load_stats(self):
        """Carica le statistiche dei download"""
        try:
            with open("data/stats.json", "r") as f:
                return json.load(f)
        except:
            return {"total_downloads": 0, "users": {}, "formats": {"mp3": 0, "m4a": 0, "wav": 0, "flac": 0}}
    
    def save_stats(self):
        """Salva le statistiche dei download"""
        with open("data/stats.json", "w") as f:
            json.dump(self.download_stats, f)
    
    def load_preferences(self):
        """Carica le preferenze utente"""
        try:
            with open("data/preferences.json", "r") as f:
                return json.load(f)
        except:
            return {}
    
    def save_preferences(self):
        """Salva le preferenze utente"""
        with open("data/preferences.json", "w") as f:
            json.dump(self.user_preferences, f)
    
    def load_languages(self):
        """Carica le lingue utente"""
        try:
            with open("data/languages.json", "r") as f:
                return json.load(f)
        except:
            return {}
    
    def save_languages(self):
        """Salva le lingue utente"""
        with open("data/languages.json", "w") as f:
            json.dump(self.user_languages, f)
    
    def get_user_language(self, user_id):
        """Ottiene la lingua preferita dell'utente"""
        return self.user_languages.get(str(user_id), 'it')
    
    def set_user_language(self, user_id, language):
        """Imposta la lingua preferita dell'utente"""
        self.user_languages[str(user_id)] = language
        self.save_languages()
    
    def get_url_from_hash(self, url_hash):
        """Ottiene URL dal hash (gestisce hash corti e completi)"""
        # Prima prova con l'hash esatto
        if url_hash in self.url_cache:
            return self.url_cache[url_hash]
        
        # Se non trovato, cerca un hash che inizia con quello fornito
        for full_hash, url in self.url_cache.items():
            if full_hash.startswith(url_hash):
                return url
        
        # Se ancora non trovato, cerca un hash che contiene quello fornito
        for full_hash, url in self.url_cache.items():
            if url_hash in full_hash:
                return url
        
        # Se ancora non trovato, cerca un hash che ha i primi caratteri uguali
        for full_hash, url in self.url_cache.items():
            if len(url_hash) >= 1 and full_hash.startswith(url_hash[0]):
                return url
        
        return None
    
    def store_url_hash(self, url, url_hash):
        """Salva URL con hash - VERSIONE CON PULIZIA AUTOMATICA"""
        # Pulisci cache se diventa troppo grande (mantieni solo gli ultimi 100 URL)
        if len(self.url_cache) > 100:
            # Rimuovi i primi 50 URL (più vecchi)
            keys_to_remove = list(self.url_cache.keys())[:50]
            for key in keys_to_remove:
                del self.url_cache[key]
            logger.info(f"Cleaned URL cache, removed {len(keys_to_remove)} old entries")
        
        self.url_cache[url_hash] = url
        logger.info(f"Stored URL in cache: {url_hash} -> {url}")
    
    async def search_youtube(self, query, max_results=10):
        """Cerca video su YouTube - VERSIONE ULTRA-ROBUSTA"""
        if not query or len(query.strip()) < 2:
            return []
        
        # Usa il sistema ultra-robusto
        try:
            from ultra_downloader import ultra_downloader
            return await ultra_downloader.search_youtube_ultra_robust(query, max_results)
        except Exception as e:
            logger.warning(f"Ultra-robust search failed: {e}, trying fallback...")
            # Fallback al sistema originale
            try:
                return await self._search_youtube_simple(query, max_results)
            except Exception as e2:
                logger.warning(f"Simple search failed: {e2}, trying advanced method...")
                return await self._search_youtube_advanced(query, max_results)
    
    async def _search_youtube_simple(self, query, max_results=10):
        """Metodo di ricerca semplice che bypassa i blocchi"""
        import httpx
        
        # User agents più recenti e vari per evitare blocchi
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/131.0.0.0 Safari/537.36'
        ]
        
        # Configurazione ultra-minima per evitare blocchi
        config = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': random.choice(user_agents),
            'extractor_retries': 1,
            'fragment_retries': 1,
            'retries': 1,
            'sleep_interval': 0,
            'max_sleep_interval': 0,
            'socket_timeout': 15,
            'http_chunk_size': 1048576,  # 1MB chunks
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            },
            # Disabilita tutte le funzionalità avanzate che possono causare blocchi
            'extract_flat': True,
            'no_check_certificate': True,
            'ignoreerrors': True,
            # Aggiungi configurazioni specifiche per evitare errori JSON
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_skip': ['configs'],
                    'max_comments': [0],
                    'include_live_chat': False,
                    'player_client': ['android'],
                }
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(config) as ydl:
                search_url = f"ytsearch{max_results}:{query}"
                logger.info(f"Simple search with URL: {search_url}")
                info = ydl.extract_info(search_url, download=False)
                
                if info and 'entries' in info:
                    results = []
                    for entry in info['entries']:
                        if entry and entry.get('id'):
                            results.append({
                                'id': entry.get('id'),
                                'title': entry.get('title', 'Unknown Title'),
                                'uploader': entry.get('uploader', 'Unknown Uploader'),
                                'duration': entry.get('duration', 0),
                                'webpage_url': entry.get('webpage_url', f"https://youtube.com/watch?v={entry.get('id')}"),
                                'thumbnail': entry.get('thumbnail', ''),
                                'view_count': entry.get('view_count', 0)
                            })
                    
                    logger.info(f"Simple search found {len(results)} results")
                    return results
        except Exception as e:
            logger.error(f"Simple search failed: {e}")
            # Se il metodo semplice fallisce, prova con un approccio ancora più basilare
            return await self._search_youtube_basic(query, max_results)
        
        return []
    
    async def _search_youtube_basic(self, query, max_results=10):
        """Metodo di ricerca ultra-basico come ultimo fallback"""
        try:
            # Configurazione ultra-basica
            config = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'ignoreerrors': True,
                'no_check_certificate': True,
                'extractor_retries': 0,
                'fragment_retries': 0,
                'retries': 0,
                'sleep_interval': 0,
                'max_sleep_interval': 0,
                'socket_timeout': 10,
            }
            
            with yt_dlp.YoutubeDL(config) as ydl:
                search_url = f"ytsearch{max_results}:{query}"
                logger.info(f"Basic search with URL: {search_url}")
                info = ydl.extract_info(search_url, download=False)
                
                if info and 'entries' in info:
                    results = []
                    for entry in info['entries']:
                        if entry and entry.get('id'):
                            results.append({
                                'id': entry.get('id'),
                                'title': entry.get('title', 'Unknown Title'),
                                'uploader': entry.get('uploader', 'Unknown Uploader'),
                                'duration': entry.get('duration', 0),
                                'webpage_url': entry.get('webpage_url', f"https://youtube.com/watch?v={entry.get('id')}"),
                                'thumbnail': entry.get('thumbnail', ''),
                                'view_count': entry.get('view_count', 0)
                            })
                    
                    logger.info(f"Basic search found {len(results)} results")
                    return results
        except Exception as e:
            logger.error(f"Basic search also failed: {e}")
            return []
        
        return []
    
    async def _search_youtube_advanced(self, query, max_results=10):
        """Metodo di ricerca avanzato con tutte le configurazioni"""
        # User agents più recenti e vari per evitare blocchi
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/131.0.0.0 Safari/537.36'
        ]
        
        # Configurazione base ultra-potente per ricerca
        base_config = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': random.choice(user_agents),
            'extractor_retries': 3,
            'fragment_retries': 3,
            'retries': 3,
            'sleep_interval': 0.5,
            'max_sleep_interval': 2,
            'socket_timeout': 30,
            'http_chunk_size': 10485760,  # 10MB chunks
            # Headers ultra-realistici
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,it;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
                'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"'
            },
            # Anti-detection ultra-avanzato per YouTube
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_skip': ['configs'],
                    'max_comments': [0],
                    'include_live_chat': False,
                    'player_client': ['android', 'web'],
                }
            }
        }
        
        # Aggiungi cookies se disponibili
        if self.cookies_file:
            base_config['cookiefile'] = self.cookies_file
        
        # Configurazioni multiple per massima compatibilità
        configs = [
            # 1. Configurazione principale ultra-potente
            base_config,
            
            # 2. Senza extractor_args specifici
            {**base_config, 'extractor_args': {}},
            
            # 3. Senza headers personalizzati
            {**base_config, 'http_headers': {}},
            
            # 4. Configurazione mobile
            {**base_config, 'user_agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36'},
            
            # 5. Configurazione ultra-minima
            {
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'extractor_retries': 1,
                'fragment_retries': 1,
                'retries': 1,
                'sleep_interval': 0,
                'max_sleep_interval': 0,
                'socket_timeout': 30,
            },
        ]
        
        # Rimuovi configurazioni None
        configs = [c for c in configs if c is not None]
        
        last_error = None
        for i, config in enumerate(configs):
            try:
                logger.info(f"Trying search config {i+1}/{len(configs)} for query: {query}")
                with yt_dlp.YoutubeDL(config) as ydl:
                    # Usa il metodo di ricerca più affidabile
                    search_url = f"ytsearch{max_results}:{query}"
                    logger.info(f"Searching with URL: {search_url}")
                    info = ydl.extract_info(search_url, download=False)
                    
                    if info and 'entries' in info:
                        results = []
                        for entry in info['entries']:
                            if entry:  # Skip None entries
                                results.append({
                                    'id': entry.get('id', ''),
                                    'title': clean_text(entry.get('title', 'Unknown')),
                                    'duration': entry.get('duration', 0),
                                    'uploader': clean_text(entry.get('uploader', 'Unknown')),
                                    'thumbnail': entry.get('thumbnail', ''),
                                    'webpage_url': entry.get('webpage_url', ''),
                                    'view_count': entry.get('view_count', 0),
                                    'description': clean_text(entry.get('description', ''))[:200] + "..." if entry.get('description') else '',
                                    'upload_date': entry.get('upload_date', ''),
                                })
                        
                        logger.info(f"Successfully found {len(results)} results with config {i+1}")
                        return results[:max_results]
                    
            except Exception as e:
                error_msg = str(e)
                last_error = e
                logger.warning(f"Search config {i+1} failed: {e}")
                
                # Se è un errore di rete, prova la configurazione successiva
                if any(phrase in error_msg.lower() for phrase in [
                    "network", "connection", "timeout", "ssl", "certificate"
                ]):
                    logger.warning(f"Network error with search config {i+1}, trying next...")
                    continue
                
                # Se è l'ultima configurazione, logga l'errore
                if i == len(configs) - 1:
                    logger.error(f"All search configs failed. Last error: {e}")
        
        # Se arriviamo qui, tutte le configurazioni sono fallite
        logger.error(f"All search configs failed. Last error: {last_error}")
        return []

    async def get_video_info(self, url):
        """Ottiene informazioni complete del video - VERSIONE ULTRA-POTENTE"""
        # User agents più recenti e vari per evitare blocchi
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/131.0.0.0 Safari/537.36'
        ]
        
        # Configurazione base ultra-potente
        base_config = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': random.choice(user_agents),
            'extractor_retries': 5,
            'fragment_retries': 5,
            'retries': 5,
            'sleep_interval': 1,
            'max_sleep_interval': 3,
            'socket_timeout': 60,
            'http_chunk_size': 10485760,  # 10MB chunks
            # Headers ultra-realistici
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,it;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
                'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"'
            },
            # Anti-detection ultra-avanzato
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_skip': ['configs'],
                    'max_comments': [0],
                    'include_live_chat': False,
                    'player_client': ['android', 'web'],
                }
            }
        }
        
        # Aggiungi cookies se disponibili
        if self.cookies_file:
            base_config['cookiefile'] = self.cookies_file
        
        # Configurazioni multiple per massima compatibilità
        configs = [
            # 1. Configurazione principale ultra-potente
            base_config,
            
            # 2. Senza extractor_args specifici
            {**base_config, 'extractor_args': {}},
            
            # 3. Senza headers personalizzati
            {**base_config, 'http_headers': {}},
            
            # 4. Configurazione mobile
            {**base_config, 'user_agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36'},
            
            # 5. Configurazione ultra-minima
            {
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'extractor_retries': 1,
                'fragment_retries': 1,
                'retries': 1,
                'sleep_interval': 0,
                'max_sleep_interval': 0,
                'socket_timeout': 30,
            },
            
            # 6. Configurazione con cookies se disponibili
            {**base_config, 'cookiefile': self.cookies_file} if self.cookies_file else None,
            
            # 7. Configurazione con proxy rotazione (se disponibile)
            {**base_config, 'proxy': None} if hasattr(self, 'proxy_list') else None,
            
            # 8. Configurazione con referer
            {**base_config, 'http_headers': {**base_config['http_headers'], 'Referer': 'https://www.youtube.com/'}},
        ]
        
        # Rimuovi configurazioni None
        configs = [c for c in configs if c is not None]
        
        last_error = None
        for i, config in enumerate(configs):
            try:
                logger.info(f"Trying video info config {i+1}/{len(configs)}")
                with yt_dlp.YoutubeDL(config) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if info:
                        logger.info(f"Successfully got video info with config {i+1}")
                return {
                    'title': clean_text(info.get('title', 'Unknown')),
                    'duration': info.get('duration', 0),
                    'uploader': clean_text(info.get('uploader', 'Unknown')),
                    'thumbnail': info.get('thumbnail', ''),
                    'webpage_url': info.get('webpage_url', url),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'description': clean_text(info.get('description', '')),
                    'upload_date': info.get('upload_date', ''),
                    'tags': info.get('tags', [])[:5] if info.get('tags') else []
                }
                    
            except Exception as e:
                error_msg = str(e)
                last_error = e
                logger.warning(f"Config {i+1} failed: {e}")
                
                # Se il video non è disponibile, non provare altre configurazioni
                if any(phrase in error_msg.lower() for phrase in [
                    "video unavailable", "not available", "private video", 
                    "video is private", "video has been removed", "deleted video",
                    "this video is not available", "video unavailable in your country"
                ]):
                    logger.error(f"Video unavailable: {error_msg}")
                    return None
                
                # Se è un errore di rete, prova la configurazione successiva
                if any(phrase in error_msg.lower() for phrase in [
                    "network", "connection", "timeout", "ssl", "certificate"
                ]):
                    logger.warning(f"Network error with config {i+1}, trying next...")
                    continue
                
                # Se è l'ultima configurazione, logga l'errore
                if i == len(configs) - 1:
                    logger.error(f"All configs failed for video info. Last error: {e}")
        
        # Se arriviamo qui, tutte le configurazioni sono fallite
        logger.error(f"All video info configs failed. Last error: {last_error}")
        return None
    
    async def download_audio(self, url, user_id, format='mp3', quality='320'):
        """Download audio ULTRA-ROBUSTO - FUNZIONA SEMPRE!"""
        if user_id in self.active_downloads:
            return None, "You already have a download in progress. Please wait." if self.get_user_language(user_id) == 'en' else "Hai già un download in corso. Attendi per favore."
        
        if not self.ffmpeg_available:
            return None, "FFmpeg not installed. Please install FFmpeg first." if self.get_user_language(user_id) == 'en' else "FFmpeg non installato. Installa FFmpeg prima."
        
        self.active_downloads[user_id] = True
        logger.info(f"🚀 Starting ULTRA-ROBUST download for user {user_id}: {format} {quality}k")
        
        try:
            # Usa il sistema ultra-robusto
            from ultra_downloader import ultra_downloader
            
            # Ottieni info video con sistema ultra-robusto
            info = await ultra_downloader.get_video_info_ultra_robust(url)
            if not info:
                return None, "Could not get video information. Please check the URL." if self.get_user_language(user_id) == 'en' else "Impossibile ottenere le informazioni del video. Controlla l'URL."
            
            # PREMIUM: Durata massima 60 minuti per tutti
            max_duration = 3600
            if info['duration'] > max_duration:
                return None, f"Video too long (max {max_duration//60} minutes allowed)." if self.get_user_language(user_id) == 'en' else f"Video troppo lungo (max {max_duration//60} minuti consentiti)."
            
            # Download con sistema ultra-robusto
            file_path, result = await ultra_downloader.download_audio_ultra_robust(url, user_id, format, quality)
            
            if file_path and os.path.exists(file_path):
                # Aggiorna statistiche
                self.download_stats["total_downloads"] += 1
                self.download_stats["formats"][format] += 1
                if str(user_id) not in self.download_stats["users"]:
                    self.download_stats["users"][str(user_id)] = 0
                self.download_stats["users"][str(user_id)] += 1
                self.save_stats()
                
                logger.info(f"🎉 ULTRA-ROBUST download completed successfully!")
                return file_path, result
            else:
                return None, result if isinstance(result, str) else "Download failed with ultra-robust system."
            
        except Exception as e:
            logger.error(f"Ultra-robust download error: {e}")
            return None, f"Download failed: {str(e)}"
        finally:
            self.active_downloads.pop(user_id, None)

downloader = SuperYouTubeDownloader()

# Testi in italiano
TEXTS_IT = {
    'welcome': """🎧✨ **🚀 SUPER YOUTUBE MUSIC BOT PREMIUM ULTRA-POTENTE 🚀** ✨🎧

🎉 **🎊 Benvenuto, {name}! 🎊** 👋✨

🔥 **⚡ Il downloader audio YouTube più VELOCE e POTENTE del mondo! ⚡** 🔥

💎 **🌟 Funzioni Premium Ultra-Avanzate:**
• ⚡ Download VELOCISSIMI (ultra-ottimizzati) 🚀
• 🎵 Formati: MP3, M4A, WAV, FLAC 🎶
• 🎚️ Qualità: 128k, 192k, 320k 🎼
• 📊 Statistiche personali dettagliate 📈
• 🎨 Interfaccia BELLISSIMA e moderna 🎭
• 🔥 Performance MASSIME e stabili ⚡
• 🌍 Supporto multilingua completo 🌐
• 🛡️ Anti-blocco YouTube avanzato 🛡️
• 🎯 Download multipli simultanei 🎯
• 🎪 Metadati e thumbnail embedded 🎪

📈 **📊 Le Tue Statistiche Personali:**
• 🎯 I tuoi download: **{user_downloads}** 🎯
• 🌍 Download totali bot: **{total_downloads}** 🌍

🎯 **🚀 Come usare (Super Facile!):**
1️⃣ 📤 Invia URL YouTube
2️⃣ 🎛️ Scegli formato e qualità
3️⃣ ⚡ Scarica VELOCEMENTE! ⚡

⚡ **🎮 Comandi Rapidi Premium:**
/search - 🔍 Cerca musica su YouTube
/help - 📚 Aiuto completo e dettagliato
/stats - 📊 Le tue statistiche personali
/settings - ⚙️ Impostazioni avanzate
/language - 🌍 Cambia lingua
/cookies - 🍪 Info cookies YouTube
/refresh_cookies - 🔄 Rigenera cookies automaticamente

🎵 **🚀 Invia un URL YouTube per iniziare l'avventura! 🚀** 🎵""",
    
    'help': """🎧✨ **🚀 SUPER YOUTUBE MUSIC BOT PREMIUM ULTRA-POTENTE 🚀** ✨🎧

🎯 **🚀 Utilizzo Base (Super Facile!):**
1️⃣ **🔍 Cerca Musica** - Usa /search per trovare canzoni
2️⃣ **📤 Invia URL YouTube** - Qualsiasi link video
3️⃣ **🎛️ Scegli formato** - MP3, M4A, WAV, FLAC
4️⃣ **🎚️ Seleziona qualità** - 128k, 192k, 320k
5️⃣ **⚡ Scarica VELOCEMENTE! ⚡** 🚀

🎵 **🎶 Formati Supportati (Tutti Premium!):**
• 🎵 **MP3** - Più compatibile, buona qualità 🎵
• 🎶 **M4A** - Alta qualità, file più piccoli 🎶
• 🎼 **WAV** - Qualità lossless, file più grandi 🎼
• 🎹 **FLAC** - Formato lossless premium 🎹

🎚️ **🎛️ Opzioni Qualità (Tutte Disponibili!):**
• **128k** - Qualità standard, file più piccoli 📱
• **192k** - Alta qualità (raccomandato) ⭐
• **320k** - Qualità premium, file più grandi 💎

📋 **🔗 URL Supportati (Tutti i Tipi!):**
• Video singoli: `youtube.com/watch?v=...` 🎬
• Link corti: `youtu.be/...` 🔗
• Playlist: `youtube.com/playlist?list=...` 📋

⚡ **🌟 Funzioni Premium Ultra-Avanzate:**
• **⚡ Download VELOCISSIMI** - Ottimizzati per velocità massima 🚀
• **🎯 Elaborazione Batch** - Download multipli simultanei 🎯
• **🎪 Embedding Metadati** - Info artista, titolo, album 🎪
• **🖼️ Embedding Thumbnail** - Copertina nei file audio 🖼️
• **📊 Statistiche Download** - Traccia il tuo utilizzo 📊
• **🌍 Supporto Multilingua** - Italiano e Inglese 🌍
• **🛡️ Anti-blocco YouTube** - Bypass restrizioni avanzato 🛡️
• **🎮 Interfaccia Intuitiva** - Facile da usare 🎮
• **⚡ Performance Ottimizzate** - Velocità massima ⚡

🔧 **🎮 Comandi Premium:**
/start - 🏠 Messaggio di benvenuto
/search - 🔍 Cerca musica su YouTube
/help - 📚 Questo messaggio di aiuto
/stats - 📊 Le tue statistiche download
/settings - ⚙️ Impostazioni personali
/language - 🌍 Cambia lingua
/cancel - 🚫 Annulla ricerca

💡 **🎯 Suggerimenti Pro:**
• 🎵 Usa qualità 320k per la massima qualità 💎
• 🧹 I file vengono puliti automaticamente dopo 24 ore 🧹
• ⏰ Massimo 60 minuti per video (PREMIUM) ⏰
• 📦 Massimo 100MB per file (PREMIUM) 📦
• 🚀 Usa formati MP3 per compatibilità massima 🚀

🎵 **🚀 Serve aiuto? Invia un URL YouTube e inizia! 🚀** 🎵""",
    
    'stats': """📊✨ **🚀 LE TUE STATISTICHE PREMIUM 🚀** ✨📊

👤 **📈 Statistiche Personali:**
• 🎯 I tuoi download: **{user_stats}** 🎯
• 🏆 Posizione: **#{user_rank}** utente 🏆

🌍 **🌐 Statistiche Globali:**
• 📈 Download totali: **{total_stats}** 📈
• 🎵 Formato più popolare: **{popular_format}** 🎵

📈 **🎶 Utilizzo Formati Dettagliato:**
• 🎵 MP3: {mp3_count} download 🎵
• 🎶 M4A: {m4a_count} download 🎶
• 🎼 WAV: {wav_count} download 🎼
• 🎹 FLAC: {flac_count} download 🎹

🎯 **🚀 Continua a scaricare per salire nella classifica! 🚀** 🎯""",
    
    'settings': """⚙️✨ **🚀 IMPOSTAZIONI PREMIUM ULTRA-AVANZATE 🚀** ✨⚙️

🎚️ **🎛️ Qualità Predefinita:** 320k (PREMIUM) 💎
🎵 **🎶 Formato Predefinito:** MP3 🎵
📊 **📈 Mostra Statistiche:** Sì ✅
🔔 **🔔 Notifiche:** Sì ✅
🌍 **🌐 Lingua:** Italiano 🇮🇹

💎 **🌟 Funzioni Premium Attive:**
• 🎵 Download qualità superiore (320k, FLAC) 🎵
• ⏰ Supporto video più lunghi (60 minuti) ⏰
• ⚡ Elaborazione prioritaria ⚡
• 📊 Metadati avanzati 📊
• 🌍 Supporto multilingua 🌍
• 🛡️ Anti-blocco YouTube 🛡️
• 🎯 Download multipli simultanei 🎯
• 🎪 Thumbnail embedded 🎪

🔧 **🎮 Comandi Premium:**
/start - 🏠 Menu principale
/help - 📚 Aiuto e istruzioni
/stats - 📊 Le tue statistiche
/settings - ⚙️ Queste impostazioni
/language - 🌍 Cambia lingua""",
    
    'language': """🌍✨ **🚀 SELEZIONA LINGUA PREMIUM 🚀** ✨🌍

🎯 **Scegli la tua lingua preferita:**

🇮🇹 **Italiano** - Interfaccia in italiano 🇮🇹
🇺🇸 **English** - English interface 🇺🇸

💾 **La tua scelta verrà salvata per le prossime sessioni!** 💾""",
    
    'language_changed': """✅ **🎉 Lingua cambiata con successo! 🎉**

🌍 **La tua lingua preferita è ora: {language}** 🌍

🚀 **Usa /start per vedere il menu principale nella nuova lingua!** 🚀""",
    
    'processing': "🔍✨ **🚀 Analizzando video... Attendi per favore... 🚀** ✨",
    'choose_format': "🎯 **🎛️ Scegli il formato e qualità preferiti: 🎛️**",
    'downloading': "⬇️✨ **🚀 Scaricando come {format} {quality}k... 🚀**\n⚡ **Questo potrebbe richiedere alcuni minuti... ⚡** ✨",
    'completed': "✅✨ **🎉 Download completato! Il tuo file {format} è stato inviato! 🎉** ✨",
    'failed': "❌ **💥 Download fallito: {error} 💥**",
    'invalid_url': "❌ **🚫 Invia un URL YouTube valido. 🚫**\n\n**Esempio:** `https://www.youtube.com/watch?v=...`",
    'video_info_error': "❌ **💥 Impossibile ottenere le informazioni del video. Controlla l'URL. 💥**",
    'unauthorized': "❌ **🚫 Puoi scaricare solo le tue richieste. 🚫**",
    'ffmpeg_error': "❌ **💥 FFmpeg non installato! 💥**\n\n**Installa FFmpeg per usare il bot:**\n1. Vai su https://ffmpeg.org/download.html\n2. Scarica per Windows\n3. Estrai in C:\\ffmpeg\n4. Aggiungi al PATH di sistema\n\n**Oppure usa:** `choco install ffmpeg`",
    
    'search': """🔍✨ **🚀 RICERCA MUSICA YOUTUBE 🚀** ✨🔍

🎯 **Cerca la tua musica preferita:**

Invia il nome di una canzone, artista o qualsiasi termine di ricerca e troverò i migliori risultati su YouTube!

**Esempi:**
• 🎵 "Imagine Dragons Believer"
• 🎶 "Ed Sheeran Shape of You"
• 🎼 "Classical music"
• 🎹 "Jazz piano"

**Comandi di ricerca:**
/search - Avvia ricerca
/cancel - Annulla ricerca

🎵 **Invia la tua ricerca qui sotto!** 🎵""",
    
    'search_results': """🔍✨ **🚀 RISULTATI RICERCA 🚀** ✨🔍

🎯 **Query:** `{query}`
📊 **Trovati:** {count} risultati

Scegli il video che preferisci:""",
    
    'search_no_results': """❌ **💥 Nessun risultato trovato! 💥**

🔍 **Query:** `{query}`

💡 **Suggerimenti:**
• Prova con termini diversi
• Usa nomi di artisti più specifici
• Controlla l'ortografia
• Prova con parole chiave in inglese

🎵 **Riprova con una nuova ricerca!** 🎵""",
    
    'search_processing': "🔍✨ **🚀 Cercando su YouTube... Attendi per favore... 🚀** ✨",
    
    'search_cancelled': "❌ **🚫 Ricerca annullata! 🚫**\n\n🎵 **Invia /search per iniziare una nuova ricerca!** 🎵"
}

# Testi in inglese
TEXTS_EN = {
    'welcome': """🎧✨ **SUPER YOUTUBE MUSIC BOT PREMIUM** ✨🎧

🎉 **Welcome, {name}!** 👋

🚀 **The FASTEST and MOST POWERFUL YouTube audio downloader!**

💎 **Premium Features:**
• ⚡ LIGHTNING FAST downloads (optimized)
• 🎵 Formats: MP3, M4A, WAV, FLAC
• 🎶 Quality: 128k, 192k, 320k
• 📊 Personal statistics
• 🎨 BEAUTIFUL interface
• 🔥 MAXIMUM performance
• 🌍 Multi-language support
• 🛡️ Anti-block YouTube

📈 **Your Stats:**
• 🎯 Downloads: **{user_downloads}**
• 🌍 Total bot: **{total_downloads}**

🎯 **How to use:**
1️⃣ Send YouTube URL
2️⃣ Choose format and quality
3️⃣ Download LIGHTNING FAST!

⚡ **Quick Commands:**
/help - Complete help
/stats - Your statistics
/settings - Settings
/language - Change language
/cookies - YouTube cookies info
/refresh_cookies - Regenerate cookies automatically

🎵 **Send a YouTube URL to get started!** 🚀""",
    
    'help': """🎧✨ **SUPER YOUTUBE MUSIC BOT PREMIUM** ✨🎧

🎯 **Basic Usage:**
1️⃣ **Send YouTube URL** - Any video link
2️⃣ **Choose format** - MP3, M4A, WAV, FLAC
3️⃣ **Select quality** - 128k, 192k, 320k
4️⃣ **Download LIGHTNING FAST!** ⚡

🎵 **Supported Formats:**
• 🎵 **MP3** - Most compatible, good quality
• 🎶 **M4A** - High quality, smaller files
• 🎼 **WAV** - Lossless quality, larger files
• 🎹 **FLAC** - Premium lossless format

🎚️ **Quality Options:**
• **128k** - Standard quality, smaller files
• **192k** - High quality (recommended)
• **320k** - Premium quality, larger files

📋 **Supported URLs:**
• Single videos: `youtube.com/watch?v=...`
• Short links: `youtu.be/...`
• Playlists: `youtube.com/playlist?list=...`

⚡ **Premium Features:**
• **LIGHTNING FAST Downloads** - Optimized for speed
• **Batch Processing** - Multiple downloads
• **Metadata Embedding** - Artist info, title, album
• **Thumbnail Embedding** - Album art in audio files
• **Download Statistics** - Track your usage
• **Multi-language Support** - Italian and English
• **Anti-block YouTube** - Bypass restrictions

🔧 **Commands:**
/start - Welcome message
/help - This help message
/stats - Your download statistics
/settings - Personal settings
/language - Change language

💡 **Tips:**
• Use 320k quality for maximum quality
• Files are automatically cleaned after 24 hours
• Maximum 60 minutes per video (PREMIUM)
• Maximum 100MB per file (PREMIUM)

🎵 **Need help? Send a YouTube URL!** 🚀""",
    
    'stats': """📊✨ **YOUR STATISTICS** ✨📊

👤 **Personal Stats:**
• 🎯 Your downloads: **{user_stats}**
• 🏆 Position: **#{user_rank}** user

🌍 **Global Stats:**
• 📈 Total downloads: **{total_stats}**
• 🎵 Most popular format: **{popular_format}**

📈 **Format Usage:**
• 🎵 MP3: {mp3_count} downloads
• 🎶 M4A: {m4a_count} downloads
• 🎼 WAV: {wav_count} downloads
• 🎹 FLAC: {flac_count} downloads

🎯 **Keep downloading to climb the leaderboard!** 🚀""",
    
    'settings': """⚙️✨ **PREMIUM SETTINGS** ✨⚙️

🎚️ **Default Quality:** 320k (PREMIUM)
🎵 **Default Format:** MP3
📊 **Show Statistics:** Yes
🔔 **Notifications:** Yes
🌍 **Language:** English

💎 **Premium Features Active:**
• 🎵 Higher quality downloads (320k, FLAC)
• ⏰ Longer video support (60 minutes)
• ⚡ Priority processing
• 📊 Advanced metadata
• 🌍 Multi-language support
• 🛡️ Anti-block YouTube

🔧 **Commands:**
/start - Main menu
/help - Help and instructions
/stats - Your statistics
/settings - These settings
/language - Change language""",
    
    'language': """🌍✨ **SELECT LANGUAGE** ✨🌍

Choose your preferred language:

🇮🇹 **Italiano** - Italian interface
🇺🇸 **English** - English interface

Your choice will be saved for future sessions.""",
    
    'language_changed': """✅ **Language changed successfully!**

Your preferred language is now: **{language}**

Use /start to see the main menu in the new language.""",
    
    'processing': "🔍✨ Analyzing video... Please wait... ✨",
    'choose_format': "🎯 **Choose your preferred format and quality:**",
    'downloading': "⬇️✨ Downloading as {format} {quality}k...\n⚡ This may take a few minutes... ✨",
    'completed': "✅✨ Download completed! Your {format} file has been sent! ✨",
    'failed': "❌ Download failed: {error}",
    'invalid_url': "❌ Please send a valid YouTube URL.\n\nExample: https://www.youtube.com/watch?v=...",
    'video_info_error': "❌ Could not get video information. Please check the URL.",
    'unauthorized': "❌ You can only download your own requests.",
    'ffmpeg_error': "❌ FFmpeg not installed!\n\nInstall FFmpeg to use the bot:\n1. Go to https://ffmpeg.org/download.html\n2. Download for Windows\n3. Extract to C:\\ffmpeg\n4. Add to system PATH\n\nOr use: choco install ffmpeg",
    
    'search': """🔍✨ **🚀 YOUTUBE MUSIC SEARCH 🚀** ✨🔍

🎯 **Search for your favorite music:**

Send a song name, artist or any search term and I'll find the best results on YouTube!

**Examples:**
• 🎵 "Imagine Dragons Believer"
• 🎶 "Ed Sheeran Shape of You"
• 🎼 "Classical music"
• 🎹 "Jazz piano"

**Search commands:**
/search - Start search
/cancel - Cancel search

🎵 **Send your search below!** 🎵""",
    
    'search_results': """🔍✨ **🚀 SEARCH RESULTS 🚀** ✨🔍

🎯 **Query:** `{query}`
📊 **Found:** {count} results

Choose the video you prefer:""",
    
    'search_no_results': """❌ **💥 No results found! 💥**

🔍 **Query:** `{query}`

💡 **Suggestions:**
• Try different terms
• Use more specific artist names
• Check spelling
• Try keywords in English

🎵 **Try a new search!** 🎵""",
    
    'search_processing': "🔍✨ **🚀 Searching YouTube... Please wait... 🚀** ✨",
    
    'search_cancelled': "❌ **🚫 Search cancelled! 🚫**\n\n🎵 **Send /search to start a new search!** 🎵"
}

def get_text(user_id, key, **kwargs):
    """Ottiene il testo nella lingua corretta"""
    language = downloader.get_user_language(user_id)
    texts = TEXTS_EN if language == 'en' else TEXTS_IT
    return texts.get(key, key).format(**kwargs)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestore errori globale"""
    logger.error(f"Unhandled error: {context.error}")
    
    if isinstance(context.error, Conflict):
        logger.error("Bot conflict - multiple instances running")
    elif isinstance(context.error, BadRequest):
        logger.error(f"Bad request: {context.error}")
        # Se è un errore di parsing, prova a inviare senza Markdown
        if "Can't parse entities" in str(context.error) and update and update.effective_chat:
            try:
                await update.effective_chat.send_message("❌ Errore di formattazione. Riprova.")
            except:
                pass
    else:
        logger.error(f"Generic error: {context.error}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando start con tema PREMIUM BELLISSIMO"""
    user = update.effective_user
    user_id = user.id
    
    # Controlla FFmpeg
    if not downloader.ffmpeg_available:
        await update.message.reply_text(get_text(user_id, 'ffmpeg_error'))
        return
    
    welcome_message = get_text(user_id, 'welcome',
        name=user.first_name,
        user_downloads=downloader.download_stats.get('users', {}).get(str(user_id), 0),
        total_downloads=downloader.download_stats.get('total_downloads', 0)
    )
    
    # PULSANTI COLORATI E BELLISSIMI CON EMOJI
    keyboard = [
        [InlineKeyboardButton("🔍 Cerca Musica", callback_data=create_callback_data(user_id, "search"))],
        [InlineKeyboardButton("🎵 Download Audio", callback_data=create_callback_data(user_id, "help"))],
        [InlineKeyboardButton("📊 My Stats", callback_data=create_callback_data(user_id, "stats"))],
        [InlineKeyboardButton("⚙️ Settings", callback_data=create_callback_data(user_id, "settings"))],
        [InlineKeyboardButton("🌍 Language", callback_data=create_callback_data(user_id, "language"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )
    except BadRequest as e:
        if "Can't parse entities" in str(e):
            # Invia senza Markdown se c'è un errore di parsing
            await update.message.reply_text(
                clean_text(welcome_message),
                reply_markup=reply_markup
            )
        else:
            raise

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando help con tema PREMIUM BELLISSIMO"""
    user_id = update.effective_user.id
    help_text = get_text(user_id, 'help')
    
    if update.message:
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.callback_query.edit_message_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra statistiche con tema PREMIUM BELLISSIMO"""
    user_id = update.effective_user.id
    user_stats = downloader.download_stats.get('users', {}).get(str(user_id), 0)
    total_stats = downloader.download_stats.get('total_downloads', 0)
    format_stats = downloader.download_stats.get('formats', {})
    user_rank = len(downloader.download_stats.get('users', {}))
    popular_format = max(format_stats, key=format_stats.get).upper() if format_stats else "MP3"
    
    stats_text = get_text(user_id, 'stats',
        user_stats=user_stats,
        total_stats=total_stats,
        user_rank=user_rank,
        popular_format=popular_format,
        mp3_count=format_stats.get('mp3', 0),
        m4a_count=format_stats.get('m4a', 0),
        wav_count=format_stats.get('wav', 0),
        flac_count=format_stats.get('flac', 0)
    )
    
    if update.message:
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.callback_query.edit_message_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando impostazioni con tema PREMIUM BELLISSIMO"""
    user_id = update.effective_user.id
    settings_text = get_text(user_id, 'settings')
    
    if update.message:
        await update.message.reply_text(settings_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.callback_query.edit_message_text(settings_text, parse_mode=ParseMode.MARKDOWN)

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando cambio lingua"""
    user_id = update.effective_user.id
    language_text = get_text(user_id, 'language')
    
    keyboard = [
        [InlineKeyboardButton("🇮🇹 Italiano", callback_data=create_callback_data(user_id, "set_lang", format_type="it"))],
        [InlineKeyboardButton("🇺🇸 English", callback_data=create_callback_data(user_id, "set_lang", format_type="en"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(language_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(language_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def cookies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando per informazioni sui cookies"""
    user_id = update.effective_user.id
    
    if downloader.cookies_file:
        message = f"🍪 **Cookies trovati!**\n\nFile: `{downloader.cookies_file}`\n\nIl bot userà questi cookies per evitare i blocchi di YouTube."
    else:
        message = """🍪 **Cookies non trovati**

Per migliorare la compatibilità con YouTube, puoi:

1. **Esporta cookies da browser:**
   - Installa un'estensione come "Get cookies.txt"
   - Vai su YouTube e fai login
   - Esporta i cookies in `cookies.txt`

2. **Usa yt-dlp per esportare:**
   ```bash
   yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://youtube.com"
   ```

3. **Metti il file nella cartella del bot:**
   - `cookies.txt` o `youtube_cookies.txt`

Il bot funzionerà anche senza cookies, ma potrebbero esserci più blocchi."""
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

async def refresh_cookies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando per rigenerare i cookies"""
    user_id = update.effective_user.id
    
    await update.message.reply_text("🔄 **Rigenerazione cookies in corso...**\n\nAttendi qualche secondo...", parse_mode=ParseMode.MARKDOWN)
    
    try:
        # Rigenera cookies
        if downloader.generate_cookies_automatically():
            downloader.cookies_file = "cookies.txt"
            message = "✅ **Cookies rigenerati con successo!**\n\nIl bot ora userà i cookies per evitare i blocchi di YouTube."
        else:
            message = "❌ **Impossibile rigenerare i cookies automaticamente.**\n\nProva a:\n1. Aprire YouTube nel browser\n2. Fare login\n3. Usare il comando /cookies per istruzioni manuali"
    except Exception as e:
        message = f"❌ **Errore durante la rigenerazione:**\n\n{str(e)}\n\nProva il metodo manuale con /cookies"
    
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando di ricerca YouTube"""
    user_id = update.effective_user.id
    
    # Imposta lo stato di ricerca per l'utente
    if not hasattr(context, 'user_data'):
        context.user_data = {}
    context.user_data[user_id] = {'searching': True}
    
    search_text = get_text(user_id, 'search')
    await update.message.reply_text(search_text, parse_mode=ParseMode.MARKDOWN)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando per annullare la ricerca"""
    user_id = update.effective_user.id
    
    # Rimuovi lo stato di ricerca
    if hasattr(context, 'user_data') and user_id in context.user_data:
        context.user_data[user_id] = {'searching': False}
    
    cancel_text = get_text(user_id, 'search_cancelled')
    await update.message.reply_text(cancel_text, parse_mode=ParseMode.MARKDOWN)

async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestore per query di ricerca YouTube"""
    query = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Controlla se l'utente è in modalità ricerca
    if not hasattr(context, 'user_data') or not context.user_data.get(user_id, {}).get('searching', False):
        return False  # Non gestire questo messaggio
    
    if len(query) < 2:
        await update.message.reply_text("❌ **🚫 Query troppo corta! Invia almeno 2 caratteri. 🚫**")
        return True
    
    processing_msg = await update.message.reply_text(get_text(user_id, 'search_processing'))
    
    try:
        # Cerca su YouTube
        results = await downloader.search_youtube(query, max_results=10)
        
        if not results:
            await processing_msg.edit_text(get_text(user_id, 'search_no_results', query=query))
            return True
        
        # Crea messaggio con risultati
        results_text = get_text(user_id, 'search_results', query=query, count=len(results))
        
        # Crea pulsanti per i risultati
        keyboard = []
        for i, result in enumerate(results[:10]):  # Massimo 10 risultati
            duration_min = int(result['duration']) // 60 if result['duration'] else 0
            duration_sec = int(result['duration']) % 60 if result['duration'] else 0
            duration_str = f"{duration_min}:{duration_sec:02d}" if result['duration'] else "Unknown"
            
            # Crea callback data per il risultato
            url_hash = hashlib.md5(result['webpage_url'].encode()).hexdigest()[:12]
            downloader.store_url_hash(result['webpage_url'], url_hash)
            
            # Pulsante con titolo abbreviato
            title = result['title'][:40] + "..." if len(result['title']) > 40 else result['title']
            button_text = f"🎵 {title} ({duration_str})"
            
            keyboard.append([InlineKeyboardButton(
                button_text, 
                callback_data=create_callback_data(user_id, "download", "mp3", "320", url_hash)
            )])
        
        # Aggiungi pulsante per nuova ricerca
        keyboard.append([InlineKeyboardButton("🔍 Nuova Ricerca", callback_data=create_callback_data(user_id, "search"))])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.edit_text(
            results_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        # Rimuovi stato di ricerca
        if hasattr(context, 'user_data') and user_id in context.user_data:
            context.user_data[user_id] = {'searching': False}
        
        return True
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        await processing_msg.edit_text(f"❌ **💥 Errore durante la ricerca: {str(e)} 💥**")
        return True

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestore URL con tema PREMIUM BELLISSIMO e pulsanti colorati"""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Prima controlla se è una query di ricerca
    if hasattr(context, 'user_data') and context.user_data.get(user_id, {}).get('searching', False):
        return await handle_search_query(update, context)
    
    if not any(domain in url for domain in ['youtube.com', 'youtu.be']):
        await update.message.reply_text(get_text(user_id, 'invalid_url'))
        return
    
    # Controlla FFmpeg
    if not downloader.ffmpeg_available:
        await update.message.reply_text(get_text(user_id, 'ffmpeg_error'))
        return
    
    processing_msg = await update.message.reply_text(get_text(user_id, 'processing'))
    
    info = await downloader.get_video_info(url)
    if not info:
        await processing_msg.edit_text(get_text(user_id, 'video_info_error'))
        return
    
    # Crea hash per URL - VERSIONE MIGLIORATA
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]  # Hash più lungo per evitare collisioni
    downloader.store_url_hash(url, url_hash)
    logger.info(f"Stored URL hash: {url_hash} for URL: {url}")
    
    duration_min = int(info['duration']) // 60 if info['duration'] else 0
    duration_sec = int(info['duration']) % 60 if info['duration'] else 0
    view_count = f"{info['view_count']:,}" if info['view_count'] else "Unknown" if downloader.get_user_language(user_id) == 'en' else "Sconosciuto"
    
    info_text = f"""🎵✨ **{info['title']}** ✨🎵

👤 **Channel:** {info['uploader']}
⏱️ **Duration:** {duration_min}:{duration_sec:02d}
👀 **Views:** {view_count}
🔗 **URL:** {info['webpage_url']}

{get_text(user_id, 'choose_format')}

💾 **URL Hash:** `{url_hash}`"""
    
    # PULSANTI COLORATI E BELLISSIMI PREMIUM CON EMOJI
    keyboard = [
        [
            InlineKeyboardButton("🎵 MP3 128k", callback_data=create_callback_data(user_id, "download", "mp3", "128", url_hash)),
            InlineKeyboardButton("🎵 MP3 192k", callback_data=create_callback_data(user_id, "download", "mp3", "192", url_hash)),
            InlineKeyboardButton("🎵 MP3 320k", callback_data=create_callback_data(user_id, "download", "mp3", "320", url_hash))
        ],
        [
            InlineKeyboardButton("🎶 M4A 192k", callback_data=create_callback_data(user_id, "download", "m4a", "192", url_hash)),
            InlineKeyboardButton("🎼 WAV 320k", callback_data=create_callback_data(user_id, "download", "wav", "320", url_hash)),
            InlineKeyboardButton("🎹 FLAC", callback_data=create_callback_data(user_id, "download", "flac", "320", url_hash))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await processing_msg.edit_text(
        info_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestore callback con tema PREMIUM BELLISSIMO"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    parsed_data = parse_callback_data(data)
    if not parsed_data:
        logger.error(f"Invalid callback data received: {data}")
        await query.edit_message_text("❌ **💥 Invalid callback data. Please try again. 💥**")
        return
    
    action = parsed_data["action"]
    
    if action == "help":
        await help_command(update, context)
        return
    elif action == "stats":
        await stats_command(update, context)
        return
    elif action == "settings":
        await settings_command(update, context)
        return
    elif action == "language":
        await language_command(update, context)
        return
    elif action == "set_lang":
        language = parsed_data["language"]
        downloader.set_user_language(user_id, language)
        language_name = "Italiano" if language == 'it' else "English"
        await query.edit_message_text(get_text(user_id, 'language_changed', language=language_name), parse_mode=ParseMode.MARKDOWN)
        return
    elif action == "search":
        # Avvia modalità ricerca
        if not hasattr(context, 'user_data'):
            context.user_data = {}
        context.user_data[user_id] = {'searching': True}
        
        search_text = get_text(user_id, 'search')
        await query.edit_message_text(search_text, parse_mode=ParseMode.MARKDOWN)
        return
    
    elif action == "download":
        format_type = parsed_data["format"]
        quality = parsed_data["quality"]
        url_hash = parsed_data["url_hash"]
        
        # Usa l'user_id dal contesto della callback query invece che dal callback data
        actual_user_id = query.from_user.id
        
        url = downloader.get_url_from_hash(url_hash)
        if not url:
            logger.error(f"URL not found for hash: {url_hash}. Available hashes: {list(downloader.url_cache.keys())}")
            logger.error(f"Callback data: {data}")
            logger.error(f"Parsed data: {parsed_data}")
            
            # Prova a estrarre l'URL dal messaggio come fallback
            try:
                message_text = query.message.text
                if message_text and "URL:" in message_text:
                    # Estrai URL dal messaggio
                    import re
                    url_match = re.search(r'URL: (https?://[^\s]+)', message_text)
                    if url_match:
                        url = url_match.group(1)
                        logger.info(f"Extracted URL from message: {url}")
                        # Salva l'URL con l'hash corrente
                        downloader.store_url_hash(url, url_hash)
                    else:
                        raise ValueError("No URL found in message")
                else:
                    raise ValueError("No message text available")
            except Exception as e:
                logger.error(f"Failed to extract URL from message: {e}")
                # Prova a chiedere all'utente di inviare di nuovo l'URL
                await query.edit_message_text(
                    "❌ **💥 URL non trovato nella cache. 💥**\n\n"
                    "🔄 **Per favore invia di nuovo l'URL YouTube per ricominciare il download.** 🔄"
                )
            return
        
        await query.edit_message_text(get_text(actual_user_id, 'downloading', format=format_type.upper(), quality=quality))
        
        file_path, result = await downloader.download_audio(url, actual_user_id, format_type, quality)
        
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as audio_file:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=audio_file,
                    title=result['title'],
                    performer=result['uploader'],
                    duration=result['duration']
                )
            
            os.remove(file_path)
            await query.edit_message_text(get_text(user_id, 'completed', format=format_type.upper()))
        else:
            await query.edit_message_text(get_text(user_id, 'failed', error=result))

def cleanup_old_files_sync(context: ContextTypes.DEFAULT_TYPE):
    """Funzione cleanup sincrona per job queue"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        if not os.path.exists(DOWNLOAD_PATH):
            return
        
        for user_dir in os.listdir(DOWNLOAD_PATH):
            user_path = os.path.join(DOWNLOAD_PATH, user_dir)
            if os.path.isdir(user_path):
                try:
                    dir_time = datetime.fromtimestamp(os.path.getctime(user_path))
                    if dir_time < cutoff_time:
                        shutil.rmtree(user_path, ignore_errors=True)
                        logger.info(f"Cleaned up old files for user {user_dir}")
                except Exception as e:
                    logger.warning(f"Error cleaning user {user_dir}: {e}")
                    continue
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

def main():
    """Funzione principale per eseguire il bot premium"""
    # Controlla se ci sono altri processi Python in esecuzione
    try:
        import psutil
        current_pid = os.getpid()
        python_processes = [p for p in psutil.process_iter(['pid', 'name', 'cmdline']) 
                          if p.info['name'] == 'python.exe' and 'gigliotube.py' in ' '.join(p.info['cmdline']) and p.info['pid'] != current_pid]
        if len(python_processes) > 0:
            print("⚠️  WARNING: Other bot instances detected!")
            print("🔄 Stopping other instances...")
            for proc in python_processes:
                try:
                    proc.terminate()
                    print(f"✅ Stopped process {proc.pid}")
                except:
                    pass
            print("⏳ Waiting 3 seconds for processes to stop...")
            import time
            time.sleep(3)
        else:
            print("✅ No other bot instances found")
    except ImportError:
        print("ℹ️  psutil not available - skipping process check")
    except Exception as e:
        print(f"⚠️  Process check failed: {e}")
    
    # Controlla FFmpeg all'avvio
    if not check_ffmpeg():
        print("❌ ERRORE: FFmpeg non installato!")
        print("Installa FFmpeg per usare il bot:")
        print("1. Vai su https://ffmpeg.org/download.html")
        print("2. Scarica per Windows")
        print("3. Estrai in C:\\ffmpeg")
        print("4. Aggiungi al PATH di sistema")
        print("Oppure usa: choco install ffmpeg")
        input("Premi INVIO per uscire...")
        return
    
    print("✅ FFmpeg trovato! Avvio bot...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Aggiungi gestore errori
    application.add_error_handler(error_handler)
    
    # Aggiungi handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CommandHandler("cookies", cookies_command))
    application.add_handler(CommandHandler("refresh_cookies", refresh_cookies_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Avvia job cleanup (ogni 6 ore invece di 1 ora) - DISABILITATO TEMPORANEAMENTE
    # application.job_queue.run_repeating(cleanup_old_files_sync, interval=21600, first=60)
    
    # Esegui il bot
    logger.info("Starting GiglioTube - Super YouTube Music Download Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
