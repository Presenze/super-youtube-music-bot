import asyncio
import os
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode
import aiofiles
from datetime import datetime, timedelta
import shutil
from config import *

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create downloads directory
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

class YouTubeDownloader:
    def __init__(self):
        self.active_downloads = {}
    
    async def get_video_info(self, url):
        """Get video information without downloading"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'thumbnail': info.get('thumbnail', ''),
                    'webpage_url': info.get('webpage_url', url)
                }
            except Exception as e:
                logger.error(f"Error getting video info: {e}")
                return None
    
    async def download_audio(self, url, user_id, format='mp3'):
        """Download audio from YouTube URL"""
        if user_id in self.active_downloads:
            return None, "You already have a download in progress. Please wait."
        
        self.active_downloads[user_id] = True
        
        try:
            # Get video info first
            info = await self.get_video_info(url)
            if not info:
                return None, "Could not get video information. Please check the URL."
            
            # Check duration (max 10 minutes)
            if info['duration'] > 600:
                return None, "Video is too long (max 10 minutes allowed)."
            
            # Create user-specific download directory
            user_dir = os.path.join(DOWNLOAD_PATH, str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            
            # Configure yt-dlp options
            output_template = os.path.join(user_dir, f"{info['title'][:50]}.%(ext)s")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format,
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find the downloaded file
            for file in os.listdir(user_dir):
                if file.endswith(f'.{format}'):
                    file_path = os.path.join(user_dir, file)
                    file_size = os.path.getsize(file_path)
                    
                    if file_size > MAX_FILE_SIZE:
                        os.remove(file_path)
                        return None, "File is too large (max 50MB)."
                    
                    return file_path, info
            
            return None, "Download completed but file not found."
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None, f"Download failed: {str(e)}"
        finally:
            self.active_downloads.pop(user_id, None)

downloader = YouTubeDownloader()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    welcome_message = """
🎧 **YouTube Music Download Bot** 🎧

Welcome! I can help you download audio from YouTube videos.

**How to use:**
1. Send me a YouTube URL
2. Choose your preferred format (MP3, M4A, WAV)
3. Download your audio file!

**Features:**
• High quality audio downloads
• Multiple format support
• Fast and reliable
• Free to use

**Limits:**
• Max video length: 10 minutes
• Max file size: 50MB

Send me a YouTube URL to get started! 🚀
"""
    
    keyboard = [
        [InlineKeyboardButton("📱 Start Download", callback_data="help")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    help_text = """
🎧 **How to use this bot:**

1. **Send a YouTube URL** - Just paste any YouTube video link
2. **Choose format** - Select MP3, M4A, or WAV
3. **Download** - Get your audio file instantly!

**Supported URLs:**
• youtube.com/watch?v=...
• youtu.be/...
• youtube.com/playlist?list=...

**Audio Formats:**
• 🎵 MP3 (recommended)
• 🎶 M4A (high quality)
• 🎼 WAV (lossless)

**Tips:**
• Works with music videos, podcasts, and any YouTube audio
• Files are automatically cleaned up after 24 hours
• Maximum 10 minutes per video
• Maximum 50MB file size

Need help? Just send me a YouTube URL! 🚀
"""
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle YouTube URL messages"""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Validate URL
    if not any(domain in url for domain in ['youtube.com', 'youtu.be']):
        await update.message.reply_text(
            "❌ Please send a valid YouTube URL.\n\nExample: https://www.youtube.com/watch?v=..."
        )
        return
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        "🔍 Analyzing video... Please wait..."
    )
    
    # Get video info
    info = await downloader.get_video_info(url)
    if not info:
        await processing_msg.edit_text("❌ Could not get video information. Please check the URL.")
        return
    
    # Show video info and format selection
    duration_min = info['duration'] // 60
    duration_sec = info['duration'] % 60
    
    info_text = f"""
🎵 **{info['title']}**
👤 **Channel:** {info['uploader']}
⏱️ **Duration:** {duration_min}:{duration_sec:02d}
🔗 **URL:** {info['webpage_url']}

Choose your preferred audio format:
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🎵 MP3", callback_data=f"download_{user_id}_mp3_{url}"),
            InlineKeyboardButton("🎶 M4A", callback_data=f"download_{user_id}_m4a_{url}")
        ],
        [InlineKeyboardButton("🎼 WAV", callback_data=f"download_{user_id}_wav_{url}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await processing_msg.edit_text(
        info_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "help":
        await help_command(update, context)
        return
    elif data == "about":
        about_text = """
🎧 **YouTube Music Download Bot**

**Version:** 1.0
**Developer:** AI Assistant
**Language:** Python

**Technologies:**
• python-telegram-bot
• yt-dlp
• FFmpeg

**Features:**
• High-quality audio extraction
• Multiple format support
• User-friendly interface
• Automatic cleanup

**Privacy:** Files are automatically deleted after 24 hours.

Made with ❤️ for music lovers!
"""
        await query.edit_message_text(about_text, parse_mode=ParseMode.MARKDOWN)
        return
    
    # Handle download callbacks
    if data.startswith("download_"):
        parts = data.split("_")
        if len(parts) >= 5:
            user_id = int(parts[1])
            format_type = parts[2]
            url = "_".join(parts[3:])
            
            # Check if user is authorized
            if query.from_user.id != user_id:
                await query.edit_message_text("❌ You can only download your own requests.")
                return
            
            # Start download
            await query.edit_message_text(
                f"⬇️ Downloading as {format_type.upper()}...\nThis may take a few moments..."
            )
            
            file_path, result = await downloader.download_audio(url, user_id, format_type)
            
            if file_path and os.path.exists(file_path):
                # Send the audio file
                with open(file_path, 'rb') as audio_file:
                    await context.bot.send_audio(
                        chat_id=query.message.chat_id,
                        audio=audio_file,
                        title=result['title'],
                        performer=result['uploader'],
                        duration=result['duration']
                    )
                
                # Clean up file
                os.remove(file_path)
                
                await query.edit_message_text(
                    "✅ Download completed! Your audio file has been sent."
                )
            else:
                await query.edit_message_text(f"❌ Download failed: {result}")

async def cleanup_old_files():
    """Clean up old download files"""
    while True:
        try:
            cutoff_time = datetime.now() - timedelta(hours=CLEANUP_AFTER_HOURS)
            
            for user_dir in os.listdir(DOWNLOAD_PATH):
                user_path = os.path.join(DOWNLOAD_PATH, user_dir)
                if os.path.isdir(user_path):
                    # Check if directory is older than cutoff time
                    dir_time = datetime.fromtimestamp(os.path.getctime(user_path))
                    if dir_time < cutoff_time:
                        shutil.rmtree(user_path, ignore_errors=True)
                        logger.info(f"Cleaned up old files for user {user_dir}")
            
            # Sleep for 1 hour
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            await asyncio.sleep(3600)

def main():
    """Main function to run the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("playlist", playlist_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Start cleanup task in the application's event loop
    application.job_queue.run_repeating(cleanup_old_files_sync, interval=3600, first=10)
    
    # Run the bot
    logger.info("Starting YouTube Music Download Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
