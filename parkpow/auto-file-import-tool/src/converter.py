import csv
import logging
import re

from src.config import load_config

config_values = load_config()

COLUMN_MAPPING = config_values["COLUMN_MAPPING"]
EXTRA_COLUMNS = config_values["EXTRA_COLUMNS"]

logger = logging.getLogger(__name__)

HEADERS = [
    "timezone",
    "created_date",
    "created_time",
    "license_plate",
    "region",
    "make",
    "model",
    "color",
    "type",
    "payment_status",
    "field1",
    "field2",
    "field3",
    "field4",
    "field5",
    "field6",
    "Vehicle Tags",
]


def detect_delimiter(line: str) -> str | None:
    """
    Detects the delimiter in a line of text.
    Returns ',' for comma-delimited, or None for whitespace-delimited.
    """
    if "," in line:
        logger.info("Comma delimiter detected.")
        return ","
    logger.info("Whitespace delimiter detected.")
    return None  # Causes split() to use its default whitespace behavior


def process_input_file(input_filename: str) -> tuple[list, set]:
    formatted_rows = []
    license_plates_in_file = set()

    logger.info(f"Processing input file: {input_filename} for data extraction.")

    try:
        lower_headers = [h.lower() for h in HEADERS]
        lp_index = lower_headers.index("license_plate")

        with open(input_filename) as f:
            # Skip the first line (header or datetime line)
            next(f, None)

            delimiter = None
            first_run = True

            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Detect delimiter on the first valid data line
                if first_run:
                    delimiter = detect_delimiter(line)
                    first_run = False

                parts = [p.strip() for p in line.split(delimiter)]
                if not parts or (len(parts) == 1 and not parts[0]):
                    continue

                # Dynamic row creation
                new_row = [""] * len(HEADERS)

                for source_key, dest_header in COLUMN_MAPPING.items():
                    match = re.match(r"source_col(\d+)", source_key, re.IGNORECASE)
                    if not match:
                        logger.warning(
                            f"Skipping invalid key in [COLUMN_MAPPING]: {source_key}"
                        )
                        continue

                    source_index = int(match.group(1))

                    try:
                        # Case-insensitive check for destination header
                        dest_index = lower_headers.index(dest_header.lower())
                        if source_index < len(parts):
                            new_row[dest_index] = parts[source_index]
                    except ValueError:
                        logger.warning(
                            f"Header '{dest_header}' from [COLUMN_MAPPING] not found in target HEADERS."
                        )

                for dest_header, static_value in EXTRA_COLUMNS.items():
                    try:
                        # Case-insensitive check for destination header
                        dest_index = lower_headers.index(dest_header.lower())
                        new_row[dest_index] = static_value
                    except ValueError:
                        logger.warning(
                            f"Header '{dest_header}' from [EXTRA_COLUMNS] not found in target HEADERS."
                        )

                # --- License Plate Extraction and Row Saving ---
                license_plate = new_row[lp_index]

                if license_plate:
                    # Ensure we only add unique license plates to the formatted_rows
                    if license_plate not in license_plates_in_file:
                        license_plates_in_file.add(license_plate)
                        formatted_rows.append(new_row)
                    else:
                        logger.warning(
                            f"Duplicate license plate found in input file, skipping row: {license_plate}"
                        )
                else:
                    logger.warning(f"Skipping row due to missing license plate: {line}")

        logger.info(
            f"Finished processing input file. Found {len(license_plates_in_file)} unique license plates."
        )
        return formatted_rows, license_plates_in_file

    except FileNotFoundError:
        logger.error(f"Input file not found: {input_filename}")
        return [], set()
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during file processing: {e}", exc_info=True
        )
        return [], set()


def write_csv_parts(base_name: str, headers: list, rows: list, max_rows: int):
    part = 1
    for i in range(0, len(rows), max_rows):
        chunk = rows[i : i + max_rows]
        filename = f"{base_name}{part:03}.csv"
        try:
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(chunk)
            logger.info(f"File saved: {filename} ({len(chunk)} rows)")
            part += 1
        except OSError as e:
            logger.error(f"Could not write to file {filename}: {e}")
