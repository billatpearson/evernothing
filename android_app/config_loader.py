"""Configuration loader for EverNothing Android"""
import os
import secrets
import configparser

def load_config():
    """Load configuration from config.ini or environment variables.
    SECRET_KEY must be set — raises ValueError if missing.
    """
    config = {}

    # Try to load from config.ini first
    config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
    if os.path.exists(config_file):
        parser = configparser.ConfigParser()
        parser.read(config_file)

        if 'AWS' in parser:
            config['S3_BUCKET_NAME'] = parser['AWS'].get('S3_BUCKET_NAME', '')
            config['AWS_REGION'] = parser['AWS'].get('AWS_REGION', 'us-east-1')
            config['AWS_ACCESS_KEY_ID'] = parser['AWS'].get('AWS_ACCESS_KEY_ID', '')
            config['AWS_SECRET_ACCESS_KEY'] = parser['AWS'].get('AWS_SECRET_ACCESS_KEY', '')

        if 'APP' in parser:
            config['SECRET_KEY']         = parser['APP'].get('SECRET_KEY', '')
            config['ENCRYPTION_ENABLED'] = parser['APP'].get('ENCRYPTION_ENABLED', 'true')
            config['DB_FILE'] = parser['APP'].get('DB_FILE', 'evernothing.db')
            config['HOST']    = parser['APP'].get('HOST', '127.0.0.1')
            config['PORT']    = parser['APP'].getint('PORT', 5000)

    # Environment variables override config.ini
    config['S3_BUCKET_NAME'] = os.environ.get('S3_BUCKET_NAME', config.get('S3_BUCKET_NAME', ''))
    config['AWS_REGION'] = os.environ.get('AWS_REGION', config.get('AWS_REGION', 'us-east-1'))
    config['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY_ID', config.get('AWS_ACCESS_KEY_ID', ''))
    config['AWS_SECRET_ACCESS_KEY'] = os.environ.get('AWS_SECRET_ACCESS_KEY', config.get('AWS_SECRET_ACCESS_KEY', ''))
    config['SECRET_KEY']         = os.environ.get('SECRET_KEY',         config.get('SECRET_KEY', ''))
    config['ENCRYPTION_ENABLED'] = os.environ.get('ENCRYPTION_ENABLED', config.get('ENCRYPTION_ENABLED', 'true'))
    config['DB_FILE'] = os.environ.get('DB_FILE', config.get('DB_FILE', 'evernothing.db'))
    config['HOST'] = os.environ.get('HOST', config.get('HOST', '127.0.0.1'))
    config['PORT'] = int(os.environ.get('PORT', config.get('PORT', 5000)))

    # Warn if SECRET_KEY is not set — generate ephemeral key so app still starts
    if not config['SECRET_KEY']:
        import logging
        logging.warning("SECRET_KEY not set — using ephemeral key. Sessions will not persist across restarts.")
        config['SECRET_KEY'] = secrets.token_hex(32)

    return config
