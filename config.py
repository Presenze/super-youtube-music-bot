import os

# Try to load dotenv if available, but don't fail if it's not
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("ℹ️  python-dotenv not available, using environment variables only")

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
