import os
import re
import requests
import logging
import json
from config import load_config

# Setup loggers
main_logger = logging.getLogger('main_logger')
checker_errors_logger = logging.getLogger('checker_errors_logger')

def check_task_status():
    config = load_config()
    output_folder = config['OUTPUT_FOLDER']
    error_folder = config['ERROR_FOLDER']
    task_status_api_url = config['TASK_STATUS_API_URL']
    auth_token = config['AUTH_TOKEN']

    main_logger.info(f"Starting task status check in {output_folder}")

    if not os.path.exists(output_folder):
        main_logger.warning(f"Output folder {output_folder} does not exist. Skipping status check.")
        return

    for filename in os.listdir(output_folder):
        filepath = os.path.join(output_folder, filename)
        if os.path.isfile(filepath):
            task_id = extract_task_id(filename)
            if task_id:
                check_single_task(task_id, filename, filepath, task_status_api_url, error_folder, auth_token)
            else:
                checker_errors_logger.info(f"Could not extract task ID from filename: {filename}")

def extract_task_id(filename: str) -> str | None:
    # This regex extracts the part between the last underscore and the file extension
    # Example: 'to_remove023_7660bbd2d1154b3993256d5d9fdeedd1.csv' -> '7660bbd2d1154b3993256d5d9fdeedd1'
    match = re.search(r'_([^_.]+)\.[^.]+$', filename)
    if match:
        return match.group(1)
    return None

def check_single_task(task_id: str, filename: str, filepath: str, api_url: str, error_folder: str, auth_token: str):
    headers = {"Authorization": f"Token {auth_token}"}
    params = {"task_id": task_id}
    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        if "info" in data:
            main_logger.info(f"Task {task_id} (file: {filename}) completed successfully. Deleting file.")
            os.remove(filepath)
        elif "error" in data:
            error_message = data.get("error", "Unknown error")
            checker_errors_logger.error(f"Task {task_id} (file: {filename}) failed: {error_message}. Moving to error folder.")
            os.rename(filepath, os.path.join(error_folder, filename))
        elif not data:  # Empty JSON, task is pending
            main_logger.info(f"Task {task_id} (file: {filename}) is still pending.")
        else:
            checker_errors_logger.warning(f"Unexpected API response for task {task_id} (file: {filename}): {json.dumps(data)}")

    except requests.exceptions.RequestException as e:
        checker_errors_logger.error(f"API request failed for task {task_id} (file: {filename}): {e}")
    except json.JSONDecodeError:
        checker_errors_logger.error(f"Failed to decode JSON response for task {task_id} (file: {filename}). Response: {response.text}")
    except Exception as e:
        checker_errors_logger.error(f"An unexpected error occurred while checking task {task_id} (file: {filename}): {e}")

if __name__ == '__main__':
    # This block is for testing purposes only and won't be used in the cron job
    # In a real scenario, logger_setup would be called from run_checker.py
    logging.basicConfig(level=logging.INFO)
    check_task_status()