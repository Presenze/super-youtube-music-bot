import os

# Railway configuration - No external dependencies
# This file is designed specifically for Railway deployment

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    # Fallback token for testing (replace with your actual token)
    BOT_TOKEN = "8237710386:AAF9MmADLR0PfihDtK8ZTmeDRi884MbV8HM"
    print("⚠️  Using fallback BOT_TOKEN. Please set BOT_TOKEN environment variable for production.")

# Download settings
DOWNLOAD_PATH = "downloads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit (PREMIUM)
SUPPORTED_FORMATS = ['mp3', 'm4a', 'wav', 'flac']

# Bot settings
MAX_CONCURRENT_DOWNLOADS = 5  # Increased for Railway
CLEANUP_AFTER_HOURS = 24

# Railway specific settings
RAILWAY_ENV = True
PLATFORM = 'railway'
LOG_LEVEL = "INFO"

print(f"🚂 Running on Railway platform")
