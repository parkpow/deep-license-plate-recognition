import os
import sys

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import UPLOAD_FOLDER, INPUT_COLUMN_MAPPING, STATIC_MAPPING
from src.converter import HEADERS, detect_delimiter

def test_mapping(lines_to_test=10):
    """
    Tests the column mapping configuration by showing how the first few lines
    of an input file will be transformed.
    """
    print("--- Starting Mapping Test ---")

    # Find the first file in the upload folder
    try:
        files_in_upload = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f)) and not f.startswith('.')]
        if not files_in_upload:
            print(f"Error: No files found in '{UPLOAD_FOLDER}/'. Please add a file to test.")
            return
        input_file = os.path.join(UPLOAD_FOLDER, files_in_upload[0])
        print(f"Testing with file: {input_file}\n")
    except FileNotFoundError:
        print(f"Error: Upload folder not found at '{UPLOAD_FOLDER}/'.")
        return

    # Read the first few lines of the file
    try:
        with open(input_file, 'r') as f:
            # Skip header and read next lines
            next(f, None)
            lines = [line.strip() for _, line in zip(range(lines_to_test), f) if line.strip()]
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    if not lines:
        print("No data lines found in the file to test.")
        return

    # --- Print Mapping Configuration ---
    print("--- Current Mapping Configuration ---")
    print(f"Input Column Mapping (SourceIndex:DestinationHeader): {INPUT_COLUMN_MAPPING}")
    print(f"Static Value Mapping (DestinationHeader:Value):     {STATIC_MAPPING}")
    print("-------------------------------------\n")

    # --- Detect Delimiter ---
    delimiter = detect_delimiter(lines[0])
    print("-------------------------------------\n")

    # --- Process and Print Line-by-Line ---
    for i, line in enumerate(lines):
        print(f"--- Processing Input Line {i+1} ---")
        print(f"Original Data: {line}")
        parts = [p.strip() for p in line.split(delimiter)]

        # Simulate the row creation
        final_row = {header: "-" for header in HEADERS}
        print("Applied Mappings:")

        # 1. Static Mappings
        for dest_header, static_value in STATIC_MAPPING.items():
            final_row[dest_header] = static_value
            print(f"  - Static: '{static_value}' -> ['{dest_header}']")

        # 2. Column Mappings
        for source_index, dest_header in INPUT_COLUMN_MAPPING.items():
            if source_index < len(parts):
                value = parts[source_index]
                final_row[dest_header] = value
                print(f"  - Mapped: Input Column {source_index} ('{value}') -> ['{dest_header}']")
            else:
                print(f"  - Mapped: Input Column {source_index} (Index out of bounds) -> ['{dest_header}']")

        print("\nResulting CSV Row:")
        for header, value in final_row.items():
            if value != '-':
                print(f"  {header:<15}: {value}")
        print("-------------------------------------\n")

if __name__ == "__main__":
    test_mapping()