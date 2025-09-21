#!/usr/bin/env python3
"""
GiglioTube Bot - Start script for Railway deployment
"""

import os
import sys
import logging

# Set up logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def start_healthcheck():
    """Avvia server di healthcheck in background"""
    try:
        import threading
        from healthcheck import start_healthcheck_server
        healthcheck_thread = threading.Thread(target=start_healthcheck_server, daemon=True)
        healthcheck_thread.start()
        logger.info("🏥 Healthcheck server started")
    except Exception as e:
        logger.warning(f"⚠️  Healthcheck server failed to start: {e}")

def main():
    """Main entry point for Railway deployment"""
    logger.info("🚀 Starting GiglioTube - Super YouTube Music Bot on Railway...")
    
    # Set environment variables for Railway
    os.environ['RAILWAY'] = 'true'
    os.environ['RAILWAY_ENVIRONMENT'] = 'true'
    os.environ['PLATFORM'] = 'railway'
    
# Check if we're on Railway
if os.getenv('RAILWAY'):
    logger.info("✅ Running on Railway platform with ULTRA-ROBUST system")
    # Avvia healthcheck server per Railway
    start_healthcheck()
else:
    logger.info("ℹ️  Running locally")
    
    # Import and run the bot
    try:
        from gigliotube import main as bot_main
        logger.info("✅ Bot module imported successfully")
        bot_main()
    except ImportError as e:
        logger.error(f"❌ Failed to import bot module: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Bot startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
