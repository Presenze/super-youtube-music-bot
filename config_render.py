import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Download settings
DOWNLOAD_PATH = "downloads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit (PREMIUM)
SUPPORTED_FORMATS = ['mp3', 'm4a', 'wav', 'flac']

# Bot settings
MAX_CONCURRENT_DOWNLOADS = 5  # Aumentato per Render
CLEANUP_AFTER_HOURS = 24

# Render specific settings
RENDER_ENV = True
LOG_LEVEL = "INFO"