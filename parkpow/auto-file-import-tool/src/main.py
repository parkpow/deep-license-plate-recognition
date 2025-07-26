import os
import logging
import shutil
from datetime import datetime
import csv
import glob

from src.logger_setup import setup_logging
from src.converter import process_input_file, HEADERS, write_csv_parts
from src.uploader import upload_all_parts
from src.config import load_config 

config_values = load_config()

UPLOAD_FOLDER = config_values['UPLOAD_FOLDER']
PROCESSED_FOLDER = config_values['PROCESSED_FOLDER']
OUTPUT_FOLDER = config_values['OUTPUT_FOLDER']
MAX_ROWS_PER_FILE = config_values['MAX_ROWS_PER_FILE']

setup_logging() # Configure the root logger
logger = logging.getLogger(__name__) # Get a logger for this module

STATE_FILE = os.path.join(PROCESSED_FOLDER, "last_run_state.txt")

def load_last_run_state() -> set:
    """
    Loads the set of license plates from the last successful run.
    """
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        with open(STATE_FILE, 'r') as f:
            return {line.strip() for line in f if line.strip()}
    except Exception as e:
        logger.error(f"Error loading last run state from {STATE_FILE}: {e}")
        return set()

def save_current_state(license_plates: set):
    """
    Saves the current set of license plates to the state file.
    """
    try:
        # Ensure the directory exists
        os.makedirs(PROCESSED_FOLDER, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            for plate in sorted(list(license_plates)): # Sort for consistent file content
                f.write(f"{plate}\n")
        logger.info(f"Current state saved to {STATE_FILE}")
    except Exception as e:
        logger.error(f"Error saving current state to {STATE_FILE}: {e}")

def main():
    logger.info("Starting synchronization cycle.")

    # Find the first file in the upload folder
    try:
        files_in_upload = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f)) and not f.startswith('.')]
        if not files_in_upload:
            logger.info("No new files to process in the upload folder.")
            return
        
        input_file = os.path.join(UPLOAD_FOLDER, files_in_upload[0])
        logger.info(f"Found file to process: {input_file}")

    except FileNotFoundError:
        logger.error(f"Upload folder not found: {UPLOAD_FOLDER}")
        return

    # 1. Load last run state
    last_run_plates = load_last_run_state()
    logger.info(f"Loaded {len(last_run_plates)} plates from last run state.")

    # 2. Process current input file to get current plates and formatted rows
    current_formatted_rows, current_plates_in_file = process_input_file(input_file)
    logger.info(f"Found {len(current_plates_in_file)} plates in current input file.")

    if not current_plates_in_file and not last_run_plates:
        logger.info("No plates to process or remove. Exiting.")
        # Move the processed file even if empty, to avoid re-processing
        try:
            processed_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(input_file)}"
            shutil.move(input_file, os.path.join(PROCESSED_FOLDER, processed_filename))
            logger.info(f"Moved empty processed file to: {processed_filename}")
        except Exception as e:
            logger.error(f"Could not move processed file: {e}")
        return

    # 3. Determine plates to add and to remove
    plates_to_add = current_plates_in_file - last_run_plates
    plates_to_remove = last_run_plates - current_plates_in_file

    logger.info(f"Plates to add: {len(plates_to_add)}")
    logger.info(f"Plates to remove: {len(plates_to_remove)}")

    # 4. Prepare CSVs for addition and removal
    add_csv_path = os.path.join(OUTPUT_FOLDER, "to_add.csv")
    remove_csv_path = os.path.join(OUTPUT_FOLDER, "to_remove.csv")

    # Filter rows for addition
    lp_index = HEADERS.index("license_plate")
    rows_to_add = [
        row for row in current_formatted_rows
        if len(row) > lp_index and row[lp_index] in plates_to_add
    ]
    
    # Create rows for removal (only license_plate is needed for removal API)
    rows_to_remove = []
    for plate in plates_to_remove:
        remove_row = [""] * len(HEADERS)
        remove_row[HEADERS.index("license_plate")] = plate
        rows_to_remove.append(remove_row)

    # Write CSVs
    if rows_to_add:
        write_csv_parts(os.path.join(OUTPUT_FOLDER, "to_add"), HEADERS, rows_to_add, MAX_ROWS_PER_FILE)
    else:
        logger.info("No new plates to add. Skipping to_add.csv creation.")

    if rows_to_remove:
        write_csv_parts(os.path.join(OUTPUT_FOLDER, "to_remove"), HEADERS, rows_to_remove, MAX_ROWS_PER_FILE)
    else:
        logger.info("No plates to remove. Skipping to_remove.csv creation.")

    # 5. Upload CSVs
    upload_success = True
    if rows_to_add:
        add_upload_results = upload_all_parts("to_add*.csv", remove_flag=False)
        if any(r["status"] != "success" for r in add_upload_results):
            upload_success = False
            logger.error("Failed to upload all 'to_add' files. State will not be updated.")

    if rows_to_remove and upload_success: # Only attempt removal if addition was successful
        remove_upload_results = upload_all_parts("to_remove*.csv", remove_flag=True)
        if any(r["status"] != "success" for r in remove_upload_results):
            upload_success = False
            logger.error("Failed to upload all 'to_remove' files. State will not be updated.")

    # 6. Update state and clean up only if all uploads were successful
    if upload_success:
        save_current_state(current_plates_in_file)
        logger.info("All uploads successful. State updated.")
        # logger.info("Temporarily suspending CSV cleanup for verification.")
        # # Clean up generated CSVs
        # for f in glob.glob(os.path.join(OUTPUT_FOLDER, "to_add*.csv")):
        #     os.remove(f)
        # for f in glob.glob(os.path.join(OUTPUT_FOLDER, "to_remove*.csv")):
        #     os.remove(f)
        # logger.info("Cleaned up temporary CSV files.")
    else:
        logger.error("Uploads failed. State file not updated. Please investigate and re-run.")

    # 7. Move the processed input file
    try:
        processed_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(input_file)}"
        shutil.move(input_file, os.path.join(PROCESSED_FOLDER, processed_filename))
        logger.info(f"Moved processed input file to: {processed_filename}")
    except Exception as e:
        logger.error(f"Could not move processed input file: {e}")

    logger.info("Synchronization cycle finished.")

if __name__ == "__main__":
    main()