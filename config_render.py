# Configurazione Bot Telegram per Render
import os

# Token del bot Telegram (da variabile d'ambiente su Render)
BOT_TOKEN = os.getenv('BOT_TOKEN', '8237710386:AAF9MmADLR0PfihDtK8ZTmeDRi884MbV8HM')

# Percorso per i download
DOWNLOAD_PATH = "downloads"

# Impostazioni download
MAX_DURATION = 3600  # 60 minuti in secondi
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes

# Impostazioni qualità
DEFAULT_QUALITY = "320"
DEFAULT_FORMAT = "mp3"

# Impostazioni pulizia file
CLEANUP_INTERVAL = 3600  # 1 ora in secondi
FILE_RETENTION = 24  # 24 ore

# Impostazioni playlist
MAX_PLAYLIST_ITEMS = 5

# Impostazioni anti-blocco
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# Impostazioni logging
LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"

# Impostazioni database
DATABASE_URL = "sqlite:///bot.db"

# Impostazioni cache
CACHE_SIZE = 1000
CACHE_TTL = 3600  # 1 ora

# Impostazioni rate limiting
RATE_LIMIT = 10  # Richieste per minuto
RATE_WINDOW = 60  # Finestra in secondi

# Impostazioni sicurezza
ALLOWED_USERS = []  # Lista vuota = tutti gli utenti
BLOCKED_USERS = []  # Lista utenti bloccati

# Impostazioni notifiche
ENABLE_NOTIFICATIONS = True
NOTIFICATION_CHAT_ID = None  # ID chat per notifiche admin

# Impostazioni backup
BACKUP_ENABLED = True
BACKUP_INTERVAL = 86400  # 24 ore
BACKUP_PATH = "backups"

# Impostazioni statistiche
STATS_ENABLED = True
STATS_RETENTION = 30  # Giorni

# Impostazioni multilingua
DEFAULT_LANGUAGE = "it"
SUPPORTED_LANGUAGES = ["it", "en"]

# Impostazioni premium
PREMIUM_FEATURES = True
PREMIUM_USERS = []  # Lista utenti premium

# Impostazioni API
API_ENABLED = False
API_KEY = None
API_RATE_LIMIT = 100  # Richieste per ora

# Impostazioni webhook (per produzione)
WEBHOOK_URL = None
WEBHOOK_PORT = 8443
WEBHOOK_CERT = None
WEBHOOK_KEY = None

# Impostazioni proxy (se necessario)
PROXY_URL = None
PROXY_USERNAME = None
PROXY_PASSWORD = None

# Impostazioni debug
DEBUG = False
VERBOSE_LOGGING = False
