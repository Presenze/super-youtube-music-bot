import asyncio
import os
import logging
import yt_dlp
import json
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaAudio
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, JobQueue
from telegram.constants import ParseMode
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

class SuperYouTubeDownloader:
    def __init__(self):
        self.active_downloads = {}
        self.download_stats = self.load_stats()
        self.user_preferences = self.load_preferences()
    
    def load_stats(self):
        """Load download statistics"""
        try:
            with open("data/stats.json", "r") as f:
                return json.load(f)
        except:
            return {"total_downloads": 0, "users": {}, "formats": {"mp3": 0, "m4a": 0, "wav": 0}}
    
    def save_stats(self):
        """Save download statistics"""
        with open("data/stats.json", "w") as f:
            json.dump(self.download_stats, f)
    
    def load_preferences(self):
        """Load user preferences"""
        try:
            with open("data/preferences.json", "r") as f:
                return json.load(f)
        except:
            return {}
    
    def save_preferences(self):
        """Save user preferences"""
        with open("data/preferences.json", "w") as f:
            json.dump(self.user_preferences, f)
    
    async def get_video_info(self, url):
        """Get comprehensive video information"""
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
                    'webpage_url': info.get('webpage_url', url),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'description': info.get('description', '')[:200] + '...' if info.get('description') else '',
                    'upload_date': info.get('upload_date', ''),
                    'tags': info.get('tags', [])[:5] if info.get('tags') else []
                }
            except Exception as e:
                logger.error(f"Error getting video info: {e}")
                return None
    
    async def get_playlist_info(self, url):
        """Get playlist information"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    return {
                        'title': info.get('title', 'Unknown Playlist'),
                        'uploader': info.get('uploader', 'Unknown'),
                        'entries': [entry for entry in info['entries'] if entry][:10],  # Limit to 10 videos
                        'total_entries': len(info['entries'])
                    }
                return None
            except Exception as e:
                logger.error(f"Error getting playlist info: {e}")
                return None
    
    async def download_audio(self, url, user_id, format='mp3', quality='192'):
        """Download audio with advanced options"""
        if user_id in self.active_downloads:
            return None, "You already have a download in progress. Please wait."
        
        self.active_downloads[user_id] = True
        
        try:
            # Get video info first
            info = await self.get_video_info(url)
            if not info:
                return None, "Could not get video information. Please check the URL."
            
            # Check duration (max 30 minutes for premium users)
            max_duration = 1800 if user_id in self.user_preferences.get('premium_users', []) else 600
            if info['duration'] > max_duration:
                return None, f"Video is too long (max {max_duration//60} minutes allowed)."
            
            # Create user-specific download directory
            user_dir = os.path.join(DOWNLOAD_PATH, str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            
            # Configure yt-dlp options with advanced settings
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
            
            # Find the downloaded file
            for file in os.listdir(user_dir):
                if file.endswith(f'.{format}'):
                    file_path = os.path.join(user_dir, file)
                    file_size = os.path.getsize(file_path)
                    
                    if file_size > MAX_FILE_SIZE:
                        os.remove(file_path)
                        return None, "File is too large (max 50MB)."
                    
                    # Update statistics
                    self.download_stats["total_downloads"] += 1
                    self.download_stats["formats"][format] += 1
                    if str(user_id) not in self.download_stats["users"]:
                        self.download_stats["users"][str(user_id)] = 0
                    self.download_stats["users"][str(user_id)] += 1
                    self.save_stats()
                    
                    return file_path, info
            
            return None, "Download completed but file not found."
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None, f"Download failed: {str(e)}"
        finally:
            self.active_downloads.pop(user_id, None)
    
    async def download_playlist(self, url, user_id, format='mp3', quality='192'):
        """Download entire playlist"""
        playlist_info = await self.get_playlist_info(url)
        if not playlist_info:
            return None, "Could not get playlist information."
        
        if len(playlist_info['entries']) > 5:
            return None, "Playlist too large (max 5 videos)."
        
        results = []
        for i, entry in enumerate(playlist_info['entries']):
            if entry and 'url' in entry:
                video_url = entry['url']
                title = entry.get('title', f'Video {i+1}')
                
                # Download each video
                file_path, info = await self.download_audio(video_url, user_id, format, quality)
                if file_path:
                    results.append((file_path, title, info))
        
        return results, playlist_info

downloader = SuperYouTubeDownloader()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced start command"""
    user = update.effective_user
    user_id = user.id
    
    # Welcome message with user info
    welcome_message = f"""
🎧 **Super YouTube Music Bot** 🎧

Welcome, **{user.first_name}**! 👋

I'm the most powerful YouTube audio downloader on Telegram!

**🚀 Premium Features:**
• High-quality audio downloads (MP3, M4A, WAV, FLAC)
• Playlist support (up to 5 videos)
• Custom quality settings (128k, 192k, 320k)
• Batch downloads
• Download statistics
• Advanced metadata embedding

**📊 Your Stats:**
• Downloads: {downloader.download_stats.get('users', {}).get(str(user_id), 0)}
• Total bot downloads: {downloader.download_stats.get('total_downloads', 0)}

**🎯 How to use:**
1. Send me a YouTube URL
2. Choose your preferred format and quality
3. Download your audio file!

**⚡ Quick Commands:**
/help - Detailed help
/stats - Your download statistics
/playlist - Download entire playlists

Send me a YouTube URL to get started! 🚀
"""
    
    keyboard = [
        [InlineKeyboardButton("🎵 Download Audio", callback_data="help")],
        [InlineKeyboardButton("📊 My Stats", callback_data=f"stats_{user_id}")],
        [InlineKeyboardButton("🎶 Playlist Mode", callback_data="playlist_help")],
        [InlineKeyboardButton("⚙️ Settings", callback_data=f"settings_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced help command"""
    help_text = """
🎧 **Super YouTube Music Bot - Help**

**🎯 Basic Usage:**
1. **Send a YouTube URL** - Any YouTube video or playlist link
2. **Choose format** - MP3, M4A, WAV, or FLAC
3. **Select quality** - 128k, 192k, or 320k
4. **Download** - Get your audio file instantly!

**🎵 Supported Formats:**
• 🎵 **MP3** - Most compatible, good quality
• 🎶 **M4A** - High quality, smaller file size
• 🎼 **WAV** - Lossless quality, larger file size
• 🎹 **FLAC** - Premium lossless format

**🎚️ Quality Options:**
• **128k** - Standard quality, smaller file
• **192k** - High quality (recommended)
• **320k** - Premium quality, larger file

**📋 Supported URLs:**
• Single videos: `youtube.com/watch?v=...`
• Short links: `youtu.be/...`
• Playlists: `youtube.com/playlist?list=...`

**⚡ Advanced Features:**
• **Playlist Downloads** - Download up to 5 videos at once
• **Batch Processing** - Multiple downloads in sequence
• **Metadata Embedding** - Artist, title, album info
• **Thumbnail Embedding** - Album art in audio files
• **Download Statistics** - Track your usage

**🔧 Commands:**
/start - Welcome message
/help - This help message
/stats - Your download statistics
/playlist - Playlist download mode

**💡 Tips:**
• Use 192k quality for best balance of quality and file size
• Playlists are limited to 5 videos for performance
• Files are automatically cleaned up after 24 hours
• Maximum 30 minutes per video for premium users

Need help? Just send me a YouTube URL! 🚀
"""
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    user_id = update.effective_user.id
    user_stats = downloader.download_stats.get('users', {}).get(str(user_id), 0)
    total_stats = downloader.download_stats.get('total_downloads', 0)
    format_stats = downloader.download_stats.get('formats', {})
    
    stats_text = f"""
📊 **Your Download Statistics**

👤 **Personal Stats:**
• Your downloads: **{user_stats}**
• Rank: **#{len(downloader.download_stats.get('users', {}))}** user

🌍 **Global Stats:**
• Total downloads: **{total_stats}**
• Most popular format: **{max(format_stats, key=format_stats.get).upper()}**

📈 **Format Usage:**
• MP3: {format_stats.get('mp3', 0)} downloads
• M4A: {format_stats.get('m4a', 0)} downloads
• WAV: {format_stats.get('wav', 0)} downloads

🎯 **Keep downloading to climb the leaderboard!**
"""
    
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def playlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Playlist download command"""
    playlist_text = """
🎶 **Playlist Download Mode**

Send me a YouTube playlist URL to download multiple videos at once!

**Features:**
• Download up to 5 videos from a playlist
• Choose format and quality for all videos
• Batch processing with progress updates
• Automatic metadata embedding

**Supported Playlist URLs:**
• `youtube.com/playlist?list=...`
• `youtube.com/watch?v=...&list=...`

**Limits:**
• Maximum 5 videos per playlist
• Maximum 10 minutes per video
• Maximum 50MB per file

Send me a playlist URL to get started! 🚀
"""
    
    await update.message.reply_text(playlist_text, parse_mode=ParseMode.MARKDOWN)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced URL handler with playlist support"""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Validate URL
    if not any(domain in url for domain in ['youtube.com', 'youtu.be']):
        await update.message.reply_text(
            "❌ Please send a valid YouTube URL.\n\nExample: https://www.youtube.com/watch?v=..."
        )
        return
    
    # Check if it's a playlist
    is_playlist = 'playlist' in url or 'list=' in url
    
    if is_playlist:
        # Handle playlist
        processing_msg = await update.message.reply_text(
            "🔍 Analyzing playlist... Please wait..."
        )
        
        playlist_info = await downloader.get_playlist_info(url)
        if not playlist_info:
            await processing_msg.edit_text("❌ Could not get playlist information. Please check the URL.")
            return
        
        info_text = f"""
🎶 **Playlist: {playlist_info['title']}**
👤 **Channel:** {playlist_info['uploader']}
📊 **Videos:** {len(playlist_info['entries'])} (showing first 5)
🔗 **URL:** {url}

Choose your preferred settings:
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🎵 MP3 192k", callback_data=f"playlist_{user_id}_mp3_192_{url}"),
                InlineKeyboardButton("🎶 M4A 192k", callback_data=f"playlist_{user_id}_m4a_192_{url}")
            ],
            [
                InlineKeyboardButton("🎼 WAV 320k", callback_data=f"playlist_{user_id}_wav_320_{url}"),
                InlineKeyboardButton("🎹 FLAC", callback_data=f"playlist_{user_id}_flac_320_{url}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.edit_text(
            info_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    else:
        # Handle single video
        processing_msg = await update.message.reply_text(
            "🔍 Analyzing video... Please wait..."
        )
        
        info = await downloader.get_video_info(url)
        if not info:
            await processing_msg.edit_text("❌ Could not get video information. Please check the URL.")
            return
        
        duration_min = info['duration'] // 60
        duration_sec = info['duration'] % 60
        view_count = f"{info['view_count']:,}" if info['view_count'] else "Unknown"
        
        info_text = f"""
🎵 **{info['title']}**
👤 **Channel:** {info['uploader']}
⏱️ **Duration:** {duration_min}:{duration_sec:02d}
👀 **Views:** {view_count}
🔗 **URL:** {info['webpage_url']}

Choose your preferred format and quality:
"""
        
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
    """Enhanced callback handler"""
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
        settings_text = """
⚙️ **Settings**

**🎚️ Default Quality:** 192k
**🎵 Default Format:** MP3
**📊 Show Statistics:** Yes
**🔔 Notifications:** Yes

**💎 Premium Features:**
• Higher quality downloads (320k, FLAC)
• Longer video support (30 minutes)
• Priority processing
• Advanced metadata

**🔧 Commands:**
/start - Main menu
/help - Help and instructions
/stats - Your statistics
/playlist - Playlist downloads
"""
        await query.edit_message_text(settings_text, parse_mode=ParseMode.MARKDOWN)
        return
    
    # Handle download callbacks
    if data.startswith("download_"):
        parts = data.split("_")
        if len(parts) >= 6:
            user_id_callback = int(parts[1])
            format_type = parts[2]
            quality = parts[3]
            url = "_".join(parts[4:])
            
            if query.from_user.id != user_id_callback:
                await query.edit_message_text("❌ You can only download your own requests.")
                return
            
            await query.edit_message_text(
                f"⬇️ Downloading as {format_type.upper()} {quality}k...\nThis may take a few moments..."
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
                    f"✅ Download completed! Your {format_type.upper()} file has been sent."
                )
            else:
                await query.edit_message_text(f"❌ Download failed: {result}")
    
    # Handle playlist download callbacks
    elif data.startswith("playlist_"):
        parts = data.split("_")
        if len(parts) >= 6:
            user_id_callback = int(parts[1])
            format_type = parts[2]
            quality = parts[3]
            url = "_".join(parts[4:])
            
            if query.from_user.id != user_id_callback:
                await query.edit_message_text("❌ You can only download your own requests.")
                return
            
            await query.edit_message_text(
                f"⬇️ Downloading playlist as {format_type.upper()} {quality}k...\nThis may take several minutes..."
            )
            
            results, playlist_info = await downloader.download_playlist(url, user_id_callback, format_type, quality)
            
            if results:
                # Send all files
                for i, (file_path, title, info) in enumerate(results):
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as audio_file:
                            await context.bot.send_audio(
                                chat_id=query.message.chat_id,
                                audio=audio_file,
                                title=title,
                                performer=info['uploader'],
                                duration=info['duration']
                            )
                        os.remove(file_path)
                
                await query.edit_message_text(
                    f"✅ Playlist download completed! {len(results)} files have been sent."
                )
            else:
                await query.edit_message_text(f"❌ Playlist download failed: {playlist_info}")

def cleanup_old_files_sync(context: ContextTypes.DEFAULT_TYPE):
    """Synchronous cleanup function for job queue"""
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
    """Main function to run the super bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("playlist", playlist_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Start cleanup job
    application.job_queue.run_repeating(cleanup_old_files_sync, interval=3600, first=10)
    
    # Run the bot
    logger.info("Starting Super YouTube Music Download Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
