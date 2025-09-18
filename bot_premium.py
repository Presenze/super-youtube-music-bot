import asyncio
import os
import logging
import yt_dlp
import json
import time
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
from telegram.error import Conflict, BadRequest
import aiofiles
import shutil
from config import *

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create directories
os.makedirs(DOWNLOAD_PATH, exist_ok=True)
os.makedirs("data", exist_ok=True)

def clean_text(text):
    """Pulisce il testo per evitare errori di parsing markdown"""
    if not text:
        return ""
    text = re.sub(r'[*_`\[\]()]', '', str(text))
    return text[:100] + "..." if len(text) > 100 else text

class PremiumYouTubeDownloader:
    def __init__(self):
        self.active_downloads = {}
        self.download_stats = self.load_stats()
        self.user_preferences = self.load_preferences()
        self.user_languages = self.load_languages()
    
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
    
    async def get_video_info(self, url):
        """Ottiene informazioni complete del video"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
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
                logger.error(f"Error getting video info: {e}")
                return None
    
    async def download_audio(self, url, user_id, format='mp3', quality='320'):
        """Download audio PREMIUM VELOCISSIMO"""
        if user_id in self.active_downloads:
            return None, "You already have a download in progress. Please wait." if self.get_user_language(user_id) == 'en' else "Hai già un download in corso. Attendi per favore."
        
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
            
            # Configurazione PREMIUM per download VELOCISSIMO
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
                # Ottimizzazioni PREMIUM per velocità massima
                'concurrent_fragment_downloads': 8,  # Download paralleli massimi
                'fragment_retries': 5,
                'retries': 5,
                'socket_timeout': 60,
                'http_chunk_size': 20971520,  # 20MB chunks
                'extractor_retries': 3,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
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

downloader = PremiumYouTubeDownloader()

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
    'unauthorized': "❌ Puoi scaricare solo le tue richieste."
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
    'unauthorized': "❌ You can only download your own requests."
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
    else:
        logger.error(f"Generic error: {context.error}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando start con tema PREMIUM BELLISSIMO"""
    user = update.effective_user
    user_id = user.id
    
    welcome_message = get_text(user_id, 'welcome',
        name=user.first_name,
        user_downloads=downloader.download_stats.get('users', {}).get(str(user_id), 0),
        total_downloads=downloader.download_stats.get('total_downloads', 0)
    )
    
    # PULSANTI COLORATI E BELLISSIMI
    keyboard = [
        [InlineKeyboardButton("🎵 Download Audio", callback_data="help")],
        [InlineKeyboardButton("📊 My Stats", callback_data=f"stats_{user_id}")],
        [InlineKeyboardButton("⚙️ Settings", callback_data=f"settings_{user_id}")],
        [InlineKeyboardButton("🌍 Language", callback_data=f"language_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

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
        [InlineKeyboardButton("🇮🇹 Italiano", callback_data=f"set_lang_{user_id}_it")],
        [InlineKeyboardButton("🇺🇸 English", callback_data=f"set_lang_{user_id}_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(language_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(language_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestore URL con tema PREMIUM BELLISSIMO e pulsanti colorati"""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not any(domain in url for domain in ['youtube.com', 'youtu.be']):
        await update.message.reply_text(get_text(user_id, 'invalid_url'))
        return
    
    processing_msg = await update.message.reply_text(get_text(user_id, 'processing'))
    
    info = await downloader.get_video_info(url)
    if not info:
        await processing_msg.edit_text(get_text(user_id, 'video_info_error'))
        return
    
    duration_min = info['duration'] // 60
    duration_sec = info['duration'] % 60
    view_count = f"{info['view_count']:,}" if info['view_count'] else "Unknown" if downloader.get_user_language(user_id) == 'en' else "Sconosciuto"
    
    info_text = f"""🎵✨ **{info['title']}** ✨🎵

👤 **Channel:** {info['uploader']}
⏱️ **Duration:** {duration_min}:{duration_sec:02d}
👀 **Views:** {view_count}
🔗 **URL:** {info['webpage_url']}

{get_text(user_id, 'choose_format')}"""
    
    # PULSANTI COLORATI E BELLISSIMI PREMIUM
    keyboard = [
        [
            InlineKeyboardButton("🎵 MP3 128k", callback_data=f"download_{user_id}_mp3_128_{url}"),
            InlineKeyboardButton("🎵 MP3 192k", callback_data=f"download_{user_id}_mp3_192_{url}"),
            InlineKeyboardButton("🎵 MP3 320k", callback_data=f"download_{user_id}_mp3_320_{url}")
        ],
        [
            InlineKeyboardButton("🎶 M4A 192k", callback_data=f"download_{user_id}_m4a_192_{url}"),
            InlineKeyboardButton("🎼 WAV 320k", callback_data=f"download_{user_id}_wav_320_{url}"),
            InlineKeyboardButton("🎹 FLAC", callback_data=f"download_{user_id}_flac_320_{url}")
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
    
    if data == "help":
        await help_command(update, context)
        return
    elif data.startswith("stats_"):
        await stats_command(update, context)
        return
    elif data.startswith("settings_"):
        await settings_command(update, context)
        return
    elif data.startswith("language_"):
        await language_command(update, context)
        return
    elif data.startswith("set_lang_"):
        parts = data.split("_")
        if len(parts) >= 4:
            target_user_id = int(parts[2])
            language = parts[3]
            
            if query.from_user.id != target_user_id:
                await query.edit_message_text(get_text(user_id, 'unauthorized'))
                return
            
            downloader.set_user_language(user_id, language)
            language_name = "Italiano" if language == 'it' else "English"
            await query.edit_message_text(get_text(user_id, 'language_changed', language=language_name), parse_mode=ParseMode.MARKDOWN)
        return
    
    if data.startswith("download_"):
        parts = data.split("_")
        if len(parts) >= 6:
            user_id_callback = int(parts[1])
            format_type = parts[2]
            quality = parts[3]
            url = "_".join(parts[4:])
            
            if query.from_user.id != user_id_callback:
                await query.edit_message_text(get_text(user_id, 'unauthorized'))
                return
            
            await query.edit_message_text(get_text(user_id, 'downloading', format=format_type.upper(), quality=quality))
            
            file_path, result = await downloader.download_audio(url, user_id_callback, format_type, quality)
            
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
        cutoff_time = datetime.now() - timedelta(hours=CLEANUP_AFTER_HOURS)
        
        for user_dir in os.listdir(DOWNLOAD_PATH):
            user_path = os.path.join(DOWNLOAD_PATH, user_dir)
            if os.path.isdir(user_path):
                dir_time = datetime.fromtimestamp(os.path.getctime(user_path))
                if dir_time < cutoff_time:
                    shutil.rmtree(user_path, ignore_errors=True)
                    logger.info(f"Cleaned up old files for user {user_dir}")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

def main():
    """Funzione principale per eseguire il bot premium"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Aggiungi gestore errori
    application.add_error_handler(error_handler)
    
    # Aggiungi handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Avvia job cleanup
    application.job_queue.run_repeating(cleanup_old_files_sync, interval=3600, first=10)
    
    # Esegui il bot
    logger.info("Starting Premium YouTube Music Download Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
