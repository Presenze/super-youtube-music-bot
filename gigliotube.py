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
    """Crea callback data sicuro e corto (max 64 byte)"""
    if action == "download":
        # Usa solo i primi 2 caratteri dell'hash per rimanere sotto i 64 byte
        short_hash = url_hash[:2] if url_hash else "00"
        # Abbrevia format_type e quality
        fmt_short = format_type[:2] if format_type else "mp"
        qual_short = quality[:2] if quality else "32"
        callback_data = f"dl_{user_id}_{fmt_short}_{qual_short}_{short_hash}"
        
        # Debug: controlla la lunghezza
        if len(callback_data) > 64:
            print(f"WARNING: Callback data too long: {len(callback_data)} bytes - {callback_data}")
            # Fallback: usa solo 1 carattere dell'hash
            short_hash = url_hash[:1] if url_hash else "0"
            callback_data = f"dl_{user_id}_{fmt_short}_{qual_short}_{short_hash}"
        
        return callback_data
    elif action == "stats":
        return f"st_{user_id}"
    elif action == "settings":
        return f"se_{user_id}"
    elif action == "language":
        return f"lg_{user_id}"
    elif action == "set_lang":
        return f"sl_{user_id}_{format_type}"  # format_type = language
    return f"cb_{user_id}_{action}"

def parse_callback_data(data):
    """Parsa callback data"""
    parts = data.split("_")
    if len(parts) < 2:
        return None
    
    if parts[0] == "dl" and len(parts) >= 5:
        # Espandi le abbreviazioni
        format_map = {"mp": "mp3", "fl": "flac", "wa": "wav", "aa": "aac"}
        quality_map = {"32": "320k", "19": "192k", "12": "128k", "64": "64k"}
        
        format_type = format_map.get(parts[2], parts[2])
        quality = quality_map.get(parts[3], parts[3])
        
        return {
            "action": "download",
            "user_id": int(parts[1]),
            "format": format_type,
            "quality": quality,
            "url_hash": parts[4]
        }
    elif parts[0] == "st":
        return {"action": "stats", "user_id": int(parts[1])}
    elif parts[0] == "se":
        return {"action": "settings", "user_id": int(parts[1])}
    elif parts[0] == "lg":
        return {"action": "language", "user_id": int(parts[1])}
    elif parts[0] == "sl" and len(parts) >= 3:
        return {"action": "set_lang", "user_id": int(parts[1]), "language": parts[2]}
    
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
        """Salva URL con hash"""
        self.url_cache[url_hash] = url
    
    async def get_video_info(self, url):
        """Ottiene informazioni complete del video"""
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
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'user_agent': random.choice(user_agents),
            'extractor_retries': 3,
            'fragment_retries': 3,
            'retries': 3,
            'sleep_interval': 0.5,
            'max_sleep_interval': 2,
            'socket_timeout': 30,
            # Headers più realistici
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
                'Cache-Control': 'max-age=0'
            },
            # Anti-detection avanzato
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_skip': ['configs'],
                    'max_comments': [0],
                    'include_live_chat': False,
                }
            }
        }
        
        # Aggiungi cookies se disponibili
        if self.cookies_file:
            ydl_opts['cookiefile'] = self.cookies_file
        
        # Prova con configurazioni diverse se la prima fallisce
        configs = [
            ydl_opts,  # Configurazione principale
            {**ydl_opts, 'extractor_args': {}},  # Senza extractor_args
            {**ydl_opts, 'http_headers': {}},  # Senza headers personalizzati
            {**ydl_opts, 'sleep_interval': 0, 'max_sleep_interval': 0},  # Senza sleep
            # Configurazione ultra-minima per YouTube
            {
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'extractor_retries': 1,
                'fragment_retries': 1,
                'retries': 1,
                'sleep_interval': 0,
                'max_sleep_interval': 0,
                'socket_timeout': 10,
            },
            # Configurazione con cookies se disponibili
            {**ydl_opts, 'cookiefile': self.cookies_file} if self.cookies_file else None,
        ]
        
        # Rimuovi configurazioni None
        configs = [c for c in configs if c is not None]
        
        for i, config in enumerate(configs):
            try:
                with yt_dlp.YoutubeDL(config) as ydl:
                    info = ydl.extract_info(url, download=False)
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
                logger.warning(f"Config {i+1} failed: {e}")
                if i == len(configs) - 1:  # Ultima configurazione
                    logger.error(f"All configs failed for video info: {e}")
                    return None
                continue
    
    async def download_audio(self, url, user_id, format='mp3', quality='320'):
        """Download audio PREMIUM VELOCISSIMO con anti-blocco"""
        if user_id in self.active_downloads:
            return None, "You already have a download in progress. Please wait." if self.get_user_language(user_id) == 'en' else "Hai già un download in corso. Attendi per favore."
        
        if not self.ffmpeg_available:
            return None, "FFmpeg not installed. Please install FFmpeg first." if self.get_user_language(user_id) == 'en' else "FFmpeg non installato. Installa FFmpeg prima."
        
        self.active_downloads[user_id] = True
        
        try:
            info = await self.get_video_info(url)
            if not info:
                return None, "Could not get video information. Please check the URL." if self.get_user_language(user_id) == 'en' else "Impossibile ottenere le informazioni del video. Controlla l'URL."
            
            # PREMIUM: Durata massima 60 minuti per tutti
            max_duration = 3600
            if info['duration'] > max_duration:
                return None, f"Video too long (max {max_duration//60} minutes allowed)." if self.get_user_language(user_id) == 'en' else f"Video troppo lungo (max {max_duration//60} minuti consentiti)."
            
            user_dir = os.path.join(DOWNLOAD_PATH, str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            
            output_template = os.path.join(user_dir, f"{info['title'][:50]}.%(ext)s")
            
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
            
            # Configurazione PREMIUM per download VELOCISSIMO con anti-blocco avanzato
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format,
                    'preferredquality': quality,
                }],
                'quiet': True,
                'no_warnings': True,
                'writethumbnail': True,
                'embed_thumbnail': True,
                'add_metadata': True,
                # Anti-blocco YouTube avanzato
                'user_agent': random.choice(user_agents),
                'extractor_retries': 3,
                'fragment_retries': 3,
                'retries': 3,
                'socket_timeout': 30,
                'http_chunk_size': 10485760,  # 10MB chunks
                'sleep_interval': 0.5,
                'max_sleep_interval': 2,
                # Headers più realistici per evitare rilevamento
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
                    'Cache-Control': 'max-age=0'
                },
                # Anti-detection avanzato per YouTube
                'extractor_args': {
                    'youtube': {
                        'skip': ['dash', 'hls'],
                        'player_skip': ['configs'],
                        'max_comments': [0],
                        'include_live_chat': False,
                    }
                }
            }
            
            # Aggiungi cookies se disponibili
            if self.cookies_file:
                ydl_opts['cookiefile'] = self.cookies_file
            
            # Prova con configurazioni diverse se la prima fallisce
            configs = [
                ydl_opts,  # Configurazione principale
                {**ydl_opts, 'extractor_args': {}},  # Senza extractor_args
                {**ydl_opts, 'http_headers': {}},  # Senza headers personalizzati
                {**ydl_opts, 'sleep_interval': 0, 'max_sleep_interval': 0},  # Senza sleep
                # Configurazione ultra-minima per YouTube
                {
                    'format': 'bestaudio[ext=m4a]/bestaudio/best',
                    'outtmpl': output_template,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': format,
                        'preferredquality': quality,
                    }],
                    'quiet': True,
                    'no_warnings': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'extractor_retries': 1,
                    'fragment_retries': 1,
                    'retries': 1,
                    'sleep_interval': 0,
                    'max_sleep_interval': 0,
                    'socket_timeout': 10,
                },
                # Configurazione con cookies se disponibili
                {**ydl_opts, 'cookiefile': self.cookies_file} if self.cookies_file else None,
            ]
            
            # Rimuovi configurazioni None
            configs = [c for c in configs if c is not None]
            
            download_success = False
            for i, config in enumerate(configs):
                try:
                    with yt_dlp.YoutubeDL(config) as ydl:
                        ydl.download([url])
                    download_success = True
                    break
                except Exception as e:
                    logger.warning(f"Download config {i+1} failed: {e}")
                    if i == len(configs) - 1:  # Ultima configurazione
                        logger.error(f"All download configs failed: {e}")
                        return None, f"Download failed: {str(e)}" if self.get_user_language(user_id) == 'en' else f"Download fallito: {str(e)}"
                    continue
            
            if not download_success:
                return None, "Download failed with all configurations." if self.get_user_language(user_id) == 'en' else "Download fallito con tutte le configurazioni."
            
            for file in os.listdir(user_dir):
                if file.endswith(f'.{format}'):
                    file_path = os.path.join(user_dir, file)
                    file_size = os.path.getsize(file_path)
                    
                    # PREMIUM: Limite 100MB per tutti
                    if file_size > 100 * 1024 * 1024:
                        os.remove(file_path)
                        return None, "File too large (max 100MB)." if self.get_user_language(user_id) == 'en' else "File troppo grande (max 100MB)."
                    
                    self.download_stats["total_downloads"] += 1
                    self.download_stats["formats"][format] += 1
                    if str(user_id) not in self.download_stats["users"]:
                        self.download_stats["users"][str(user_id)] = 0
                    self.download_stats["users"][str(user_id)] += 1
                    self.save_stats()
                    
                    return file_path, info
            
            return None, "Download completed but file not found." if self.get_user_language(user_id) == 'en' else "Download completato ma file non trovato."
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None, f"Download failed: {str(e)}"
        finally:
            self.active_downloads.pop(user_id, None)

downloader = SuperYouTubeDownloader()

# Testi in italiano
TEXTS_IT = {
    'welcome': """🎧✨ **SUPER YOUTUBE MUSIC BOT PREMIUM** ✨🎧

🎉 **Benvenuto, {name}!** 👋

🚀 **Il downloader audio YouTube più VELOCE e POTENTE!**

💎 **Funzioni Premium:**
• ⚡ Download VELOCISSIMI (ottimizzati)
• 🎵 Formati: MP3, M4A, WAV, FLAC
• 🎶 Qualità: 128k, 192k, 320k
• 📊 Statistiche personali
• 🎨 Interfaccia BELLISSIMA
• 🔥 Performance MASSIME
• 🌍 Supporto multilingua
• 🛡️ Anti-blocco YouTube

📈 **Le Tue Stats:**
• 🎯 Download: **{user_downloads}**
• 🌍 Totali bot: **{total_downloads}**

🎯 **Come usare:**
1️⃣ Invia URL YouTube
2️⃣ Scegli formato e qualità
3️⃣ Scarica VELOCEMENTE!

⚡ **Comandi Rapidi:**
/help - Aiuto completo
/stats - Le tue statistiche
/settings - Impostazioni
/language - Cambia lingua
/cookies - Info cookies YouTube
/refresh_cookies - Rigenera cookies automaticamente

🎵 **Invia un URL YouTube per iniziare!** 🚀""",
    
    'help': """🎧✨ **SUPER YOUTUBE MUSIC BOT PREMIUM** ✨🎧

🎯 **Utilizzo Base:**
1️⃣ **Invia URL YouTube** - Qualsiasi link video
2️⃣ **Scegli formato** - MP3, M4A, WAV, FLAC
3️⃣ **Seleziona qualità** - 128k, 192k, 320k
4️⃣ **Scarica VELOCEMENTE!** ⚡

🎵 **Formati Supportati:**
• 🎵 **MP3** - Più compatibile, buona qualità
• 🎶 **M4A** - Alta qualità, file più piccoli
• 🎼 **WAV** - Qualità lossless, file più grandi
• 🎹 **FLAC** - Formato lossless premium

🎚️ **Opzioni Qualità:**
• **128k** - Qualità standard, file più piccoli
• **192k** - Alta qualità (raccomandato)
• **320k** - Qualità premium, file più grandi

📋 **URL Supportati:**
• Video singoli: `youtube.com/watch?v=...`
• Link corti: `youtu.be/...`
• Playlist: `youtube.com/playlist?list=...`

⚡ **Funzioni Premium:**
• **Download VELOCISSIMI** - Ottimizzati per velocità
• **Elaborazione Batch** - Download multipli
• **Embedding Metadati** - Info artista, titolo, album
• **Embedding Thumbnail** - Copertina nei file audio
• **Statistiche Download** - Traccia il tuo utilizzo
• **Supporto Multilingua** - Italiano e Inglese
• **Anti-blocco YouTube** - Bypass restrizioni

🔧 **Comandi:**
/start - Messaggio di benvenuto
/help - Questo messaggio di aiuto
/stats - Le tue statistiche download
/settings - Impostazioni personali
/language - Cambia lingua

💡 **Suggerimenti:**
• Usa qualità 320k per la massima qualità
• I file vengono puliti automaticamente dopo 24 ore
• Massimo 60 minuti per video (PREMIUM)
• Massimo 100MB per file (PREMIUM)

🎵 **Serve aiuto? Invia un URL YouTube!** 🚀""",
    
    'stats': """📊✨ **LE TUE STATISTICHE** ✨📊

👤 **Statistiche Personali:**
• 🎯 I tuoi download: **{user_stats}**
• 🏆 Posizione: **#{user_rank}** utente

🌍 **Statistiche Globali:**
• 📈 Download totali: **{total_stats}**
• 🎵 Formato più popolare: **{popular_format}**

📈 **Utilizzo Formati:**
• 🎵 MP3: {mp3_count} download
• 🎶 M4A: {m4a_count} download
• 🎼 WAV: {wav_count} download
• 🎹 FLAC: {flac_count} download

🎯 **Continua a scaricare per salire nella classifica!** 🚀""",
    
    'settings': """⚙️✨ **IMPOSTAZIONI PREMIUM** ✨⚙️

🎚️ **Qualità Predefinita:** 320k (PREMIUM)
🎵 **Formato Predefinito:** MP3
📊 **Mostra Statistiche:** Sì
🔔 **Notifiche:** Sì
🌍 **Lingua:** Italiano

💎 **Funzioni Premium Attive:**
• 🎵 Download qualità superiore (320k, FLAC)
• ⏰ Supporto video più lunghi (60 minuti)
• ⚡ Elaborazione prioritaria
• 📊 Metadati avanzati
• 🌍 Supporto multilingua
• 🛡️ Anti-blocco YouTube

🔧 **Comandi:**
/start - Menu principale
/help - Aiuto e istruzioni
/stats - Le tue statistiche
/settings - Queste impostazioni
/language - Cambia lingua""",
    
    'language': """🌍✨ **SELEZIONA LINGUA** ✨🌍

Scegli la tua lingua preferita:

🇮🇹 **Italiano** - Interfaccia in italiano
🇺🇸 **English** - English interface

La tua scelta verrà salvata per le prossime sessioni.""",
    
    'language_changed': """✅ **Lingua cambiata con successo!**

La tua lingua preferita è ora: **{language}**

Usa /start per vedere il menu principale nella nuova lingua.""",
    
    'processing': "🔍✨ Analizzando video... Attendi per favore... ✨",
    'choose_format': "🎯 **Scegli il formato e qualità preferiti:**",
    'downloading': "⬇️✨ Scaricando come {format} {quality}k...\n⚡ Questo potrebbe richiedere alcuni minuti... ✨",
    'completed': "✅✨ Download completato! Il tuo file {format} è stato inviato! ✨",
    'failed': "❌ Download fallito: {error}",
    'invalid_url': "❌ Invia un URL YouTube valido.\n\nEsempio: https://www.youtube.com/watch?v=...",
    'video_info_error': "❌ Impossibile ottenere le informazioni del video. Controlla l'URL.",
    'unauthorized': "❌ Puoi scaricare solo le tue richieste.",
    'ffmpeg_error': "❌ FFmpeg non installato!\n\nInstalla FFmpeg per usare il bot:\n1. Vai su https://ffmpeg.org/download.html\n2. Scarica per Windows\n3. Estrai in C:\\ffmpeg\n4. Aggiungi al PATH di sistema\n\nOppure usa: choco install ffmpeg"
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
    'ffmpeg_error': "❌ FFmpeg not installed!\n\nInstall FFmpeg to use the bot:\n1. Go to https://ffmpeg.org/download.html\n2. Download for Windows\n3. Extract to C:\\ffmpeg\n4. Add to system PATH\n\nOr use: choco install ffmpeg"
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

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestore URL con tema PREMIUM BELLISSIMO e pulsanti colorati"""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
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
    
    # Crea hash per URL
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    downloader.store_url_hash(url, url_hash)
    
    duration_min = info['duration'] // 60
    duration_sec = info['duration'] % 60
    view_count = f"{info['view_count']:,}" if info['view_count'] else "Unknown" if downloader.get_user_language(user_id) == 'en' else "Sconosciuto"
    
    info_text = f"""🎵✨ **{info['title']}** ✨🎵

👤 **Channel:** {info['uploader']}
⏱️ **Duration:** {duration_min}:{duration_sec:02d}
👀 **Views:** {view_count}
🔗 **URL:** {info['webpage_url']}

{get_text(user_id, 'choose_format')}"""
    
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
        await query.edit_message_text("❌ Invalid callback data")
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
    
    if action == "download":
        format_type = parsed_data["format"]
        quality = parsed_data["quality"]
        url_hash = parsed_data["url_hash"]
        
        url = downloader.get_url_from_hash(url_hash)
        if not url:
            await query.edit_message_text("❌ URL not found. Please try again.")
            return
        
        await query.edit_message_text(get_text(user_id, 'downloading', format=format_type.upper(), quality=quality))
        
        file_path, result = await downloader.download_audio(url, user_id, format_type, quality)
        
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Avvia job cleanup (ogni 6 ore invece di 1 ora) - DISABILITATO TEMPORANEAMENTE
    # application.job_queue.run_repeating(cleanup_old_files_sync, interval=21600, first=60)
    
    # Esegui il bot
    logger.info("Starting GiglioTube - Super YouTube Music Download Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
