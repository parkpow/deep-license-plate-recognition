import configparser
import re
import os

CONFIG_FILE = 'data/config.ini'

def get_default_config():
    """Returns the default configuration as a string."""
    return '''
[DEFAULT]
CRON_SCHEDULE = */60 * * * *

[API]
API_URL = http://YOUR_PARKPOW_IP:8000/api/v1/import-vehicles/
AUTH_TOKEN = YOU_PARKPOW_TOKEN

[MAPPING]
INPUT_COLUMN_MAPPING = Column0:license_plate
STATIC_MAPPING = Vehicle Tags:test01
'''

def initialize_config():
    """
    Initializes the configuration. If config.ini does not exist,
    it creates it with default values.
    """
    config_dir = os.path.dirname(CONFIG_FILE)
    if config_dir:
        os.makedirs(config_dir, exist_ok=True)

    if not os.path.exists(CONFIG_FILE):
        print(f"'{CONFIG_FILE}' not found. Creating a default configuration file.")
        with open(CONFIG_FILE, 'w') as f:
            f.write(get_default_config().strip())

# Initialize the config file if it doesn't exist
initialize_config()

# Initialize the parser and read the config file
config = configparser.ConfigParser()
config.read(CONFIG_FILE)

# Cron schedule
CRON_SCHEDULE = config.get('DEFAULT', 'CRON_SCHEDULE', fallback='0 6 * * *')

# API Configuration
API_URL = config.get('API', 'API_URL')
AUTH_TOKEN = config.get('API', 'AUTH_TOKEN')

# File paths
UPLOAD_FOLDER = config.get('PATHS', 'UPLOAD_FOLDER', fallback='data/upload')
PROCESSED_FOLDER = config.get('PATHS', 'PROCESSED_FOLDER', fallback='data/processed')
OUTPUT_FOLDER = config.get('PATHS', 'OUTPUT_FOLDER', fallback='data/output')
LOGS_FOLDER = config.get('PATHS', 'LOGS_FOLDER', fallback='data/logs')

# CSV Configuration
MAX_ROWS_PER_FILE = config.getint('CSV', 'MAX_ROWS_PER_FILE', fallback=45000)


# --- Dynamic Mappings ---

def parse_static_mapping(mapping_str: str) -> dict:
    if not mapping_str:
        return {}
    try:
        return {key.strip(): value.strip() for key, value in (item.split(':', 1) for item in mapping_str.split(','))}
    except ValueError:
        raise ValueError(f"Invalid static mapping format: {mapping_str}")

def parse_column_mapping(mapping_str: str) -> dict:
    if not mapping_str:
        return {}
    mapping = {}
    try:
        for item in mapping_str.split(','):
            source, dest = item.split(':', 1)
            source = source.strip()
            dest = dest.strip()
            
            # Extract index from "ColumnX"
            match = re.match(r'Column(\d+)', source, re.IGNORECASE)
            if not match:
                raise ValueError(f"Invalid source column format: '{source}'. Expected 'ColumnX'.")
            
            col_index = int(match.group(1))
            mapping[col_index] = dest
        return mapping
    except ValueError as e:
        raise ValueError(f"Invalid column mapping format: '{mapping_str}'. Details: {e}")

INPUT_COLUMN_MAPPING_STR = config.get('MAPPING', 'INPUT_COLUMN_MAPPING', fallback='')
STATIC_MAPPING_STR = config.get('MAPPING', 'STATIC_MAPPING', fallback='')

# Parsed mappings to be used by the application
INPUT_COLUMN_MAPPING = parse_column_mapping(INPUT_COLUMN_MAPPING_STR)
STATIC_MAPPING = parse_static_mapping(STATIC_MAPPING_STR)
