import configparser
import re
import os
import sys

CONFIG_FILE = 'data/config.ini'
file_name = os.path.basename(CONFIG_FILE)

_cached_config_values = None


def _initialize_config_file_if_not_exists():
    """
    Initializes the configuration directory. If config.ini does not exist,
    it informs the user to create it and exits the program.
    """
    config_dir = os.path.dirname(CONFIG_FILE)
    if config_dir:
        os.makedirs(config_dir, exist_ok=True)

    if not os.path.exists(CONFIG_FILE):
        print(f"ERROR: The configuration file '{file_name}' was not found.")
        print("Please create this file with the necessary configurations.")
        print("Refer to the README.md file for a configuration example.")
        sys.exit(1) # Exits the program with an error code

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
    Requires the file to exist and validates required parameters.
    Caches and returns the loaded values for subsequent calls.
    """
    global _cached_config_values

    if _cached_config_values is not None:
        return _cached_config_values

    _initialize_config_file_if_not_exists()

    config = configparser.ConfigParser()
    try:
        config.read(CONFIG_FILE)
    except Exception as e:
        print(f"ERROR: Could not read the configuration file '{CONFIG_FILE}'. Please check its syntax or permissions.")
        print(f"Error details: {e}")
        sys.exit(1)

    app_config = {}
    missing_parameters = []

    expected_config_options = [
        ('CRON', 'CRON_SCHEDULE', str, '0 6 * * *', True),
        ('CRON', 'CRON_SCHEDULE_CHECKER', str, '*/5 * * * *', False),
        ('API', 'BASE_API_URL', str, None, True),
        ('API', 'AUTH_TOKEN', str, None, True),
        ('PATHS', 'UPLOAD_FOLDER', str, 'data/upload', False),
        ('PATHS', 'PROCESSED_FOLDER', str, 'data/processed', False),
        ('PATHS', 'OUTPUT_FOLDER', str, 'data/output', False),
        ('PATHS', 'LOGS_FOLDER', str, 'data/logs', False),
        ('PATHS', 'ERROR_FOLDER', str, 'data/error', False),
        ('CSV', 'MAX_ROWS_PER_FILE', int, 45000, False),
    ]

    for section, option, data_type, fallback_value, is_required in expected_config_options:
        # Main reading logic (remains the same)
        if config.has_option(section, option):
            try:
                if data_type == int:
                    value = config.getint(section, option)
                elif data_type == bool:
                    value = config.getboolean(section, option)
                else:
                    value = config.get(section, option)

                if is_required and isinstance(value, str) and not value.strip():
                    missing_parameters.append(f"[{section}] {option} (REQUIRED, but is empty)")
                else:
                    app_config[option] = value
            except ValueError as e:
                missing_parameters.append(f"[{section}] {option} (Invalid value or incorrect format: {e})")
        else:
            if is_required:
                missing_parameters.append(f"[{section}] {option} (REQUIRED, but not found in the file)")
            else:
                app_config[option] = fallback_value

    # Construct derived API URLs
    if 'BASE_API_URL' in app_config:
        base_url = app_config['BASE_API_URL'].rstrip('/') # Remove trailing slash if present
        app_config['API_URL'] = f"{base_url}/api/v1/import-vehicles/"
        app_config['TASK_STATUS_API_URL'] = f"{base_url}/api/v1/task-check/"
    else:
        missing_parameters.append("[API] BASE_API_URL (REQUIRED, but not found or empty)")

    if config.has_section('COLUMN_MAPPING'):
        app_config['COLUMN_MAPPING'] = dict(config.items('COLUMN_MAPPING'))
    else:
        app_config['COLUMN_MAPPING'] = {}

    if config.has_section('EXTRA_COLUMNS'):
        app_config['EXTRA_COLUMNS'] = dict(config.items('EXTRA_COLUMNS'))
    else:
        app_config['EXTRA_COLUMNS'] = {}

    if missing_parameters:
        print(f"ERROR: The configuration file '{CONFIG_FILE}' is missing or has incorrect values for the following parameters:")
        for param in missing_parameters:
            print(f"- {param}")
        sys.exit(1)

    _cached_config_values = app_config
    return app_config

