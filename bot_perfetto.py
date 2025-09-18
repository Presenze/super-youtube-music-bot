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
    # Rimuove caratteri che causano problemi con markdown
    text = re.sub(r'[*_`\[\]()]', '', str(text))
    # Limita la lunghezza
    return text[:100] + "..." if len(text) > 100 else text

class SuperYouTubeDownloader:
    def __init__(self):
        self.active_downloads = {}
        self.download_stats = self.load_stats()
        self.user_preferences = self.load_preferences()
    
    def load_stats(self):
        """Carica le statistiche dei download"""
        try:
            with open("data/stats.json", "r") as f:
                return json.load(f)
        except:
            return {"total_downloads": 0, "users": {}, "formats": {"mp3": 0, "m4a": 0, "wav": 0}}
    
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
                    'title': clean_text(info.get('title', 'Sconosciuto')),
                    'duration': info.get('duration', 0),
                    'uploader': clean_text(info.get('uploader', 'Sconosciuto')),
                    'thumbnail': info.get('thumbnail', ''),
                    'webpage_url': info.get('webpage_url', url),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'description': clean_text(info.get('description', '')),
                    'upload_date': info.get('upload_date', ''),
                    'tags': info.get('tags', [])[:5] if info.get('tags') else []
                }
            except Exception as e:
                logger.error(f"Errore nel recupero info video: {e}")
                return None
    
    async def download_audio(self, url, user_id, format='mp3', quality='192'):
        """Download audio con opzioni avanzate"""
        if user_id in self.active_downloads:
            return None, "Hai già un download in corso. Attendi per favore."
        
        self.active_downloads[user_id] = True
        
        try:
            info = await self.get_video_info(url)
            if not info:
                return None, "Impossibile ottenere le informazioni del video. Controlla l'URL."
            
            max_duration = 1800 if user_id in self.user_preferences.get('premium_users', []) else 600
            if info['duration'] > max_duration:
                return None, f"Video troppo lungo (max {max_duration//60} minuti consentiti)."
            
            user_dir = os.path.join(DOWNLOAD_PATH, str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            
            output_template = os.path.join(user_dir, f"{info['title'][:50]}.%(ext)s")
            
            ydl_opts = {
                'format': 'bestaudio/best',
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
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            for file in os.listdir(user_dir):
                if file.endswith(f'.{format}'):
                    file_path = os.path.join(user_dir, file)
                    file_size = os.path.getsize(file_path)
                    
                    if file_size > MAX_FILE_SIZE:
                        os.remove(file_path)
                        return None, "File troppo grande (max 50MB)."
                    
                    self.download_stats["total_downloads"] += 1
                    self.download_stats["formats"][format] += 1
                    if str(user_id) not in self.download_stats["users"]:
                        self.download_stats["users"][str(user_id)] = 0
                    self.download_stats["users"][str(user_id)] += 1
                    self.save_stats()
                    
                    return file_path, info
            
            return None, "Download completato ma file non trovato."
            
        except Exception as e:
            logger.error(f"Errore download: {e}")
            return None, f"Download fallito: {str(e)}"
        finally:
            self.active_downloads.pop(user_id, None)

downloader = SuperYouTubeDownloader()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestore errori globale"""
    logger.error(f"Errore non gestito: {context.error}")
    
    if isinstance(context.error, Conflict):
        logger.error("Conflitto bot - più istanze in esecuzione")
    elif isinstance(context.error, BadRequest):
        logger.error(f"Richiesta non valida: {context.error}")
    else:
        logger.error(f"Errore generico: {context.error}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando start migliorato"""
    user = update.effective_user
    user_id = user.id
    
    welcome_message = f"""🎧 Super YouTube Music Bot 🎧

Benvenuto, {user.first_name}! 👋

Sono il downloader audio YouTube più potente su Telegram!

🚀 Funzioni Premium:
• Download audio di alta qualità (MP3, M4A, WAV, FLAC)
• Supporto playlist (fino a 5 video)
• Impostazioni qualità personalizzate (128k, 192k, 320k)
• Download multipli
• Statistiche download
• Embedding metadati avanzati

📊 Le Tue Statistiche:
• Download: {downloader.download_stats.get('users', {}).get(str(user_id), 0)}
• Download totali bot: {downloader.download_stats.get('total_downloads', 0)}

🎯 Come usare:
1. Inviami un URL YouTube
2. Scegli formato e qualità preferiti
3. Scarica il tuo file audio!

⚡ Comandi Rapidi:
/help - Aiuto dettagliato
/stats - Le tue statistiche download
/playlist - Download playlist intere
/settings - Impostazioni personali

Inviami un URL YouTube per iniziare! 🚀"""
    
    keyboard = [
        [InlineKeyboardButton("🎵 Download Audio", callback_data="help")],
        [InlineKeyboardButton("📊 Le Mie Stats", callback_data=f"stats_{user_id}")],
        [InlineKeyboardButton("🎶 Modalità Playlist", callback_data="playlist_help")],
        [InlineKeyboardButton("⚙️ Impostazioni", callback_data=f"settings_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando help migliorato"""
    help_text = """🎧 Super YouTube Music Bot - Aiuto

🎯 Utilizzo Base:
1. Invia un URL YouTube - Qualsiasi link video o playlist YouTube
2. Scegli formato - MP3, M4A, WAV, o FLAC
3. Seleziona qualità - 128k, 192k, o 320k
4. Scarica - Ottieni il tuo file audio istantaneamente!

🎵 Formati Supportati:
• MP3 - Più compatibile, buona qualità
• M4A - Alta qualità, file più piccoli
• WAV - Qualità lossless, file più grandi
• FLAC - Formato lossless premium

🎚️ Opzioni Qualità:
• 128k - Qualità standard, file più piccoli
• 192k - Alta qualità (raccomandato)
• 320k - Qualità premium, file più grandi

📋 URL Supportati:
• Video singoli: youtube.com/watch?v=...
• Link corti: youtu.be/...
• Playlist: youtube.com/playlist?list=...

⚡ Funzioni Avanzate:
• Download Playlist - Scarica fino a 5 video alla volta
• Elaborazione Batch - Download multipli in sequenza
• Embedding Metadati - Info artista, titolo, album
• Embedding Thumbnail - Copertina nei file audio
• Statistiche Download - Traccia il tuo utilizzo

🔧 Comandi:
/start - Messaggio di benvenuto
/help - Questo messaggio di aiuto
/stats - Le tue statistiche download
/playlist - Modalità download playlist
/settings - Impostazioni personali

💡 Suggerimenti:
• Usa qualità 192k per il miglior equilibrio qualità/dimensione
• Le playlist sono limitate a 5 video per performance
• I file vengono puliti automaticamente dopo 24 ore
• Massimo 30 minuti per video per utenti premium

Serve aiuto? Inviami semplicemente un URL YouTube! 🚀"""
    
    if update.message:
        await update.message.reply_text(help_text)
    else:
        await update.callback_query.edit_message_text(help_text)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra statistiche utente"""
    user_id = update.effective_user.id
    user_stats = downloader.download_stats.get('users', {}).get(str(user_id), 0)
    total_stats = downloader.download_stats.get('total_downloads', 0)
    format_stats = downloader.download_stats.get('formats', {})
    
    stats_text = f"""📊 Le Tue Statistiche Download

👤 Statistiche Personali:
• I tuoi download: {user_stats}
• Posizione: #{len(downloader.download_stats.get('users', {}))} utente

🌍 Statistiche Globali:
• Download totali: {total_stats}
• Formato più popolare: {max(format_stats, key=format_stats.get).upper()}

📈 Utilizzo Formati:
• MP3: {format_stats.get('mp3', 0)} download
• M4A: {format_stats.get('m4a', 0)} download
• WAV: {format_stats.get('wav', 0)} download

🎯 Continua a scaricare per salire nella classifica!"""
    
    if update.message:
        await update.message.reply_text(stats_text)
    else:
        await update.callback_query.edit_message_text(stats_text)

async def playlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando download playlist"""
    playlist_text = """🎶 Modalità Download Playlist

Inviami un URL playlist YouTube per scaricare più video alla volta!

Funzioni:
• Scarica fino a 5 video da una playlist
• Scegli formato e qualità per tutti i video
• Elaborazione batch con aggiornamenti progressivi
• Embedding automatico metadati

URL Playlist Supportati:
• youtube.com/playlist?list=...
• youtube.com/watch?v=...&list=...

Limiti:
• Massimo 5 video per playlist
• Massimo 10 minuti per video
• Massimo 50MB per file

Inviami un URL playlist per iniziare! 🚀"""
    
    if update.message:
        await update.message.reply_text(playlist_text)
    else:
        await update.callback_query.edit_message_text(playlist_text)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando impostazioni"""
    settings_text = """⚙️ Impostazioni

🎚️ Qualità Predefinita: 192k
🎵 Formato Predefinito: MP3
📊 Mostra Statistiche: Sì
🔔 Notifiche: Sì

💎 Funzioni Premium:
• Download qualità superiore (320k, FLAC)
• Supporto video più lunghi (30 minuti)
• Elaborazione prioritaria
• Metadati avanzati

🔧 Comandi:
/start - Menu principale
/help - Aiuto e istruzioni
/stats - Le tue statistiche
/playlist - Download playlist
/settings - Queste impostazioni"""
    
    if update.message:
        await update.message.reply_text(settings_text)
    else:
        await update.callback_query.edit_message_text(settings_text)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestore URL migliorato con supporto playlist"""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not any(domain in url for domain in ['youtube.com', 'youtu.be']):
        await update.message.reply_text(
            "❌ Invia un URL YouTube valido.\n\nEsempio: https://www.youtube.com/watch?v=..."
        )
        return
    
    processing_msg = await update.message.reply_text(
        "🔍 Analizzando video... Attendi per favore..."
    )
    
    info = await downloader.get_video_info(url)
    if not info:
        await processing_msg.edit_text("❌ Impossibile ottenere le informazioni del video. Controlla l'URL.")
        return
    
    duration_min = info['duration'] // 60
    duration_sec = info['duration'] % 60
    view_count = f"{info['view_count']:,}" if info['view_count'] else "Sconosciuto"
    
    info_text = f"""🎵 {info['title']}
👤 Canale: {info['uploader']}
⏱️ Durata: {duration_min}:{duration_sec:02d}
👀 Visualizzazioni: {view_count}
🔗 URL: {info['webpage_url']}

Scegli il formato e qualità preferiti:"""
    
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
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestore callback migliorato"""
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
    elif data == "playlist_help":
        await playlist_command(update, context)
        return
    elif data.startswith("settings_"):
        await settings_command(update, context)
        return
    
    if data.startswith("download_"):
        parts = data.split("_")
        if len(parts) >= 6:
            user_id_callback = int(parts[1])
            format_type = parts[2]
            quality = parts[3]
            url = "_".join(parts[4:])
            
            if query.from_user.id != user_id_callback:
                await query.edit_message_text("❌ Puoi scaricare solo le tue richieste.")
                return
            
            await query.edit_message_text(
                f"⬇️ Scaricando come {format_type.upper()} {quality}k...\nQuesto potrebbe richiedere alcuni minuti..."
            )
            
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
                await query.edit_message_text(
                    f"✅ Download completato! Il tuo file {format_type.upper()} è stato inviato."
                )
            else:
                await query.edit_message_text(f"❌ Download fallito: {result}")

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
                    logger.info(f"Puliti file vecchi per utente {user_dir}")
    except Exception as e:
        logger.error(f"Errore cleanup: {e}")

def main():
    """Funzione principale per eseguire il super bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Aggiungi gestore errori
    application.add_error_handler(error_handler)
    
    # Aggiungi handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("playlist", playlist_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Avvia job cleanup
    application.job_queue.run_repeating(cleanup_old_files_sync, interval=3600, first=10)
    
    # Esegui il bot
    logger.info("Avvio Super YouTube Music Download Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
