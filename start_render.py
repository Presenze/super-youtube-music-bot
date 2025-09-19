#!/usr/bin/env python3
"""
GiglioTube - Super YouTube Music Bot
Start script for Render deployment
"""

import os
import sys
import logging

# Set up logging for Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for Render deployment"""
    logger.info("🚀 Starting GiglioTube - Super YouTube Music Bot on Render...")
    
    # Check if we're on Render
    if os.getenv('RENDER'):
        logger.info("✅ Running on Render platform")
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