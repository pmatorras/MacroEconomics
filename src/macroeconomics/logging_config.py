import logging
import os
from logging.handlers import RotatingFileHandler
from macroeconomics.common import LOG_DIR

def setup_logging():
    """Configure logging for production and development environments."""
    
    # Get log level from environment variable (default to INFO for production)
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Create logger
    logger = logging.getLogger('macroeconomics')
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler (for Render.com logs)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation (optional, for local development)
    if os.getenv('ENVIRONMENT') != 'production':
        file_handler = RotatingFileHandler(
            LOG_DIR/ 'app.log', maxBytes=10485760, backupCount=5  # 10MB files, keep 5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

# Module-level logger
logger = setup_logging()
