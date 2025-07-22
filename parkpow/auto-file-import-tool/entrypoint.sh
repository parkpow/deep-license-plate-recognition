#!/bin/bash
set -euo pipefail
CONFIG_FILE="/app/data/config.ini"

# Function to read a value from the .ini file
get_config_value() {
    python -c "import configparser; config = configparser.ConfigParser(); config.read('${CONFIG_FILE}'); print(config.get('$1', '$2', fallback='$3'))"
}

# First, run the Python script to ensure config and directories are created
PYTHONPATH=/app python -c "import src.config; src.config.load_config()" || exit 1

# Read paths from config.ini
CRON_SCHEDULE_FROM_INI=$(get_config_value 'CRON' 'CRON_SCHEDULE' '0 2 * * *')
UPLOAD_FOLDER=$(get_config_value 'PATHS' 'UPLOAD_FOLDER' 'data/upload')
PROCESSED_FOLDER=$(get_config_value 'PATHS' 'PROCESSED_FOLDER' 'data/processed')
OUTPUT_FOLDER=$(get_config_value 'PATHS' 'OUTPUT_FOLDER' 'data/output')
LOGS_FOLDER=$(get_config_value 'PATHS' 'LOGS_FOLDER' 'data/logs')
CRON_LOG_FILE="/app/${LOGS_FOLDER}/cron.log"

# Ensure all necessary directories exist
mkdir -p "/app/${UPLOAD_FOLDER}" "/app/${PROCESSED_FOLDER}" "/app/${OUTPUT_FOLDER}" "/app/${LOGS_FOLDER}"

echo "--------------------------------------------------"
echo "  ParkPow Auto File Import Tool Container Started!"
echo "--------------------------------------------------"
echo "  Cron Schedule: ${CRON_SCHEDULE_FROM_INI}"
echo "  Monitoring logs in ${CRON_LOG_FILE}"
echo "--------------------------------------------------"

# Create a temporary crontab file
CRON_FILE="/tmp/crontab_entry"

# The command to be executed by cron
# It changes to /app, sets PYTHONPATH, and then runs the Python script
CRON_COMMAND="cd /app && export PYTHONPATH=/app:${PYTHONPATH:-} && /usr/local/bin/python -m src.main >> ${CRON_LOG_FILE} 2>&1"

echo "${CRON_SCHEDULE_FROM_INI} ${CRON_COMMAND}" > "${CRON_FILE}"

# Install the new crontab, replacing any existing one
crontab "${CRON_FILE}"

# Start the cron daemon
cron

# Clear the cron log file at startup to avoid old messages
> "${CRON_LOG_FILE}"

# Create the cron log file if it doesn't exist (redundant after > but good for safety)
touch "${CRON_LOG_FILE}"

# Tail the log file to keep the container running and see logs
tail -f "${CRON_LOG_FILE}"
