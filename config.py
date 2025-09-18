import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN') or "8237710386:AAF9MmADLR0PfihDtK8ZTmeDRi884MbV8HM"
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Download settings
DOWNLOAD_PATH = "downloads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
SUPPORTED_FORMATS = ['mp3', 'm4a', 'wav']

# Bot settings
MAX_CONCURRENT_DOWNLOADS = 3
CLEANUP_AFTER_HOURS = 24
