import configparser
import re
import os

CONFIG_FILE = 'data/config.ini'

_cached_config_values = None

def get_default_config_string(): 
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

def _initialize_config_file_if_not_exists(): # Made internal and more descriptive
    """
    Initializes the configuration file. If config.ini does not exist,
    it creates it with default values.
    """
    config_dir = os.path.dirname(CONFIG_FILE)
    if config_dir:
        os.makedirs(config_dir, exist_ok=True)

    if not os.path.exists(CONFIG_FILE):
        print(f"'{CONFIG_FILE}' not found. Creating a default configuration file.")
        with open(CONFIG_FILE, 'w') as f:
            f.write(get_default_config_string().strip())

def parse_static_mapping(mapping_str: str) -> dict:
    """Parses a string of key:value pairs into a dictionary."""
    if not mapping_str:
        return {}
    try:
        return {key.strip(): value.strip() for key, value in (item.split(':', 1) for item in mapping_str.split(','))}
    except ValueError:
        raise ValueError(f"Invalid static mapping format: {mapping_str}")

def parse_column_mapping(mapping_str: str) -> dict:
    """Parses a string of 'ColumnX:header' pairs into a dictionary mapping int index to header."""
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

def load_config() -> dict:
    """
    Loads configuration values from the config.ini file.
    Creates the default file if it does not exist.
    Caches and returns the loaded values for subsequent calls.
    """
    global _cached_config_values

    if _cached_config_values is not None:
        return _cached_config_values # Return cached values if already loaded

    _initialize_config_file_if_not_exists() # Ensure the file exists before trying to read

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    app_config = {}

    # Configuration sections
    app_config['CRON_SCHEDULE'] = config.get('DEFAULT', 'CRON_SCHEDULE', fallback='0 6 * * *')
    app_config['API_URL'] = config.get('API', 'API_URL')
    app_config['AUTH_TOKEN'] = config.get('API', 'AUTH_TOKEN')
    
    # Adding 'PATHS' as a valid section for fallback
    app_config['UPLOAD_FOLDER'] = config.get('PATHS', 'UPLOAD_FOLDER', fallback='data/upload')
    app_config['PROCESSED_FOLDER'] = config.get('PATHS', 'PROCESSED_FOLDER', fallback='data/processed')
    app_config['OUTPUT_FOLDER'] = config.get('PATHS', 'OUTPUT_FOLDER', fallback='data/output')
    app_config['LOGS_FOLDER'] = config.get('PATHS', 'LOGS_FOLDER', fallback='data/logs')

    app_config['MAX_ROWS_PER_FILE'] = config.getint('CSV', 'MAX_ROWS_PER_FILE', fallback=45000)

    # Dynamic mappings
    input_column_mapping_str = config.get('MAPPING', 'INPUT_COLUMN_MAPPING', fallback='')
    static_mapping_str = config.get('MAPPING', 'STATIC_MAPPING', fallback='')

    app_config['INPUT_COLUMN_MAPPING'] = parse_column_mapping(input_column_mapping_str)
    app_config['STATIC_MAPPING'] = parse_static_mapping(static_mapping_str)
    
    _cached_config_values = app_config 
    return app_config

