#!/usr/bin/env python3
"""
Smart Marketing Automation System
نظام التسويق الآلي الذكي

Main application runner
سكريپت التشغيل الرئيسي
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import create_app

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv('LOG_FILE', 'logs/app.log')),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    try:
        # Create Flask application
        app = create_app()
        
        # Get configuration from environment
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_ENV') == 'development'
        
        logger.info(f"Starting Smart Marketing Automation System...")
        logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Debug: {debug}")
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Create uploads directory if it doesn't exist
        os.makedirs(os.getenv('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
        
        # Create backups directory if it doesn't exist
        if os.getenv('BACKUP_ENABLED', 'True').lower() == 'true':
            os.makedirs(os.getenv('BACKUP_LOCATION', 'backups'), exist_ok=True)
        
        # Start the application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()

