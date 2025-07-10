import requests
import os
import glob
import time
import logging

from src.config import load_config 

config_values = load_config()

API_URL = config_values['API_URL']
AUTH_TOKEN = config_values['AUTH_TOKEN']
OUTPUT_FOLDER = config_values['OUTPUT_FOLDER']

logger = logging.getLogger(__name__)

def upload_file(filepath: str, remove: bool) -> dict:
    try:
        with open(filepath, 'rb') as f:
            files = {
                "import_file": (os.path.basename(filepath), f, "text/csv")
            }
            data = {
                "remove": str(remove).lower()
            }
            headers = {
                "Authorization": f"Token {AUTH_TOKEN}"
            }

            response = requests.post(API_URL, files=files, data=data, headers=headers, timeout=60)

        # Check for non-2xx status codes
        if not response.ok:
            error_message = f"API request failed for {filepath}. Status: {response.status_code}. Response: {response.text[:500]}"
            logger.error(error_message)
            try:
                error_data = response.json()
                logger.error(f"API Error Details (JSON): {error_data}")
                return {
                    "file": filepath,
                    "status": "api_error",
                    "http_code": response.status_code,
                    "error_details": error_data
                }
            except requests.exceptions.JSONDecodeError:
                # If it's not JSON, the initial error_message is sufficient
                return {
                    "file": filepath,
                    "status": "api_error",
                    "http_code": response.status_code,
                    "raw_response": response.text
                }

        # If response.ok is True, proceed with success handling
        try:
            data = response.json()
            task_id = data.get("task_id")
            logger.info(f"Successfully uploaded: {filepath} -> task_id={task_id}")
            return {
                "file": filepath,
                "status": "success",
                "task_id": task_id,
                "http_code": response.status_code
            }

        except requests.exceptions.JSONDecodeError:
            # This case should ideally not happen if response.ok is True and API returns JSON
            # But keeping it for robustness if API returns non-JSON 2xx response
            logger.warning(f"File {filepath} uploaded, but response is not valid JSON (even with 2xx status).")
            logger.warning(f"  - Status code: {response.status_code}")
            logger.warning(f"  - Response content: {response.text[:200]}")
            return {
                "file": filepath,
                "status": "invalid_json_2xx", # New status for clarity
                "http_code": response.status_code,
                "raw_response": response.text
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Network/API error while uploading {filepath}: {e}")
        return {"file": filepath, "status": "network_error", "error": str(e)}

    except Exception as e:
        logger.error(f"Unexpected error while uploading {filepath}: {e}")
        return {"file": filepath, "status": "unexpected_error", "error": str(e)}

def upload_all_parts(pattern: str, remove_flag: bool) -> list:
    files = sorted(glob.glob(os.path.join(OUTPUT_FOLDER, pattern)))
    results = []

    if not files:
        logger.info(f"No files found matching pattern '{pattern}' to upload.")
        return results

    logger.info(f"Found {len(files)} file(s) matching '{pattern}' to upload...")

    for file in files:
        result = upload_file(file, remove=remove_flag)
        results.append(result)
        time.sleep(1) # Delay between uploads

    logger.info(f"Final upload report for pattern '{pattern}':")
    for r in results:
        status = r.get("status")
        task = r.get("task_id", "-")
        logger.info(f"{r['file']}: {status} (task_id: {task})")

    return results
