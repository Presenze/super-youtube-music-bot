import os

# Railway Ultra-Robust Configuration
# Configurazione ottimizzata per Railway con sistema ultra-robusto

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    # Fallback token per testing
    BOT_TOKEN = "8237710386:AAF9MmADLR0PfihDtK8ZTmeDRi884MbV8HM"
    print("⚠️  Using fallback BOT_TOKEN. Please set BOT_TOKEN environment variable for production.")

# Download settings - OTTIMIZZATI PER SISTEMA ULTRA-ROBUSTO
DOWNLOAD_PATH = "downloads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit (PREMIUM)
SUPPORTED_FORMATS = ['mp3', 'm4a', 'wav', 'flac']

# Bot settings - OTTIMIZZATI PER RAILWAY
MAX_CONCURRENT_DOWNLOADS = 10  # Aumentato per sistema ultra-robusto
CLEANUP_AFTER_HOURS = 24

# Railway specific settings
RAILWAY_ENV = True
LOG_LEVEL = "INFO"

# Platform detection
PLATFORM = 'railway'
RAILWAY = True

# Sistema ultra-robusto settings
ULTRA_ROBUST_MODE = True
MAX_DOWNLOAD_RETRIES = 10  # 10 metodi di fallback
MAX_SEARCH_RETRIES = 5     # 5 configurazioni di ricerca
ENABLE_COOKIES_AUTO = True  # Cookies automatici
ENABLE_USER_AGENT_ROTATION = True  # Rotazione user agents

print(f"🚀 Railway Ultra-Robust Configuration loaded!")
print(f"✅ Ultra-robust mode: {ULTRA_ROBUST_MODE}")
print(f"✅ Max download retries: {MAX_DOWNLOAD_RETRIES}")
print(f"✅ Max search retries: {MAX_SEARCH_RETRIES}")
print(f"✅ Cookies auto: {ENABLE_COOKIES_AUTO}")
print(f"✅ User agent rotation: {ENABLE_USER_AGENT_ROTATION}")
