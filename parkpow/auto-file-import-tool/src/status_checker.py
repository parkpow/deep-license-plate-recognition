import os
import requests
import logging
import json
import time
from src.config import load_config

# Get loggers as configured in logger_setup.py
logger = logging.getLogger(__name__)
checker_errors_logger = logging.getLogger('checker_errors_logger')



def monitor_task_status(task_id: str, filename: str, filepath: str, max_retries: int = 180):
    retries = 0
    config = load_config()
    error_folder = config['ERROR_FOLDER']
    task_status_api_url = config['TASK_STATUS_API_URL']
    auth_token = config['AUTH_TOKEN']
    
    headers = {"Authorization": f"Token {auth_token}"}
    params = {"task_id": task_id}
    
    logger.info(f"Monitoring task {task_id} (file: {filename})...")

    while True:
        try:
            response = requests.get(task_status_api_url, headers=headers, params=params)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            if "info" in data:
                logger.info(f"Task {task_id} (file: {filename}) completed successfully. Deleting file.")
                os.remove(filepath)
                break  # Exit loop on success
            elif "error" in data:
                error_message = data.get("error", "Unknown error")
                checker_errors_logger.error(f"Task {task_id} (file: {filename}) failed: {error_message}. Moving to error folder.")
                os.rename(filepath, os.path.join(error_folder, filename))
                break  # Exit loop on error
            elif not data:  # Empty JSON, task is pending
                logger.info(f"Task {task_id} (file: {filename}) is still pending. Retrying in 15 seconds.")
            else:
                checker_errors_logger.warning(f"Unexpected API response for task {task_id} (file: {filename}): {json.dumps(data)}. Retrying in 15 seconds.")

        except requests.exceptions.RequestException as e:
            checker_errors_logger.error(f"API request failed for task {task_id} (file: {filename}): {e}. Retrying in 15 seconds.")
        except json.JSONDecodeError:
            checker_errors_logger.error(f"Failed to decode JSON response for task {task_id} (file: {filename}). Response: {response.text}. Retrying in 15 seconds.")
        except Exception as e:
            checker_errors_logger.error(f"An unexpected error occurred while checking task {task_id} (file: {filename}): {e}. Retrying in 15 seconds.")
        
        time.sleep(15)
        retries += 1
        if retries >= max_retries:
            checker_errors_logger.error(f"Task {task_id} (file: {filename}) reached maximum retries ({max_retries}) and is still pending. Moving to error folder.")
            os.rename(filepath, os.path.join(error_folder, filename))
            break # Exit loop after max retries