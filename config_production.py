import os

# Production configuration - No external dependencies
# This file is designed to work without python-dotenv

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
MAX_CONCURRENT_DOWNLOADS = 5  # Increased for production
CLEANUP_AFTER_HOURS = 24

# Production specific settings
PRODUCTION_ENV = True
LOG_LEVEL = "INFO"

# Platform detection
PLATFORM = os.getenv('PLATFORM', 'unknown')
if os.getenv('RENDER'):
    PLATFORM = 'render'
elif os.getenv('RAILWAY'):
    PLATFORM = 'railway'
elif os.getenv('REPL_ID'):
    PLATFORM = 'replit'
elif os.getenv('VERCEL'):
    PLATFORM = 'vercel'
elif os.getenv('HEROKU'):
    PLATFORM = 'heroku'
elif os.getenv('CYCLIC'):
    PLATFORM = 'cyclic'

print(f"🚀 Running on platform: {PLATFORM}")
