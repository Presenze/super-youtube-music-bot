#!/usr/bin/env python3
"""
GiglioTube Bot - Main file for Replit deployment
"""

import os
import sys
import logging

# Set up logging for Replit
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for Replit deployment"""
    logger.info("🚀 Starting GiglioTube Bot on Replit...")
    
    # Set environment variables for production
    os.environ['REPLIT'] = 'true'
    os.environ['PLATFORM'] = 'replit'
    
    # Check if we're on Replit
    if os.getenv('REPL_ID'):
        logger.info("✅ Running on Replit platform")
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
