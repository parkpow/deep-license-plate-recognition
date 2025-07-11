# ParkPow Auto File Import Tool

This project is an automated solution for importing data from files and adding or removing vehicles in Parkpow by adding a reference Tag. It monitors an upload folder, processes files, applies configurable mappings, and sends the data, managing logs and processed files.

## Features

- **Folder Monitoring:** Observes an upload folder for new CSV files.
- **Data Processing:** Reads CSV files, applies column and static data mappings.
- **API Integration:** Sends processed data to a configurable API endpoint.
- **Flexible Configuration:** All configurations are managed via an external `config.ini` file.
- **Automated Scheduling:** Uses `cron` to execute the import process at defined intervals.
- **Log Management:** Records operations in dedicated log files.
- **Centralized Data Structure:** All input, output, and log data are stored in a single `data` folder for easy management.

## Configuration

The system's configuration is done through the `config.ini` file. This file is **automatically created** with default values the first time the Docker container is run, inside the `data` folder on your host.

You can edit this file to adjust the ParkPow Auto File Import Tool's behavior.

### Example `config.ini`

```ini
[CRON]
CRON_SCHEDULE = */2 * * * *

[API]
API_URL = http://YOUR_PARKPOW_IP:8000/api/v1/import-vehicles/
AUTH_TOKEN = YOU_PARKPOW_TOKEN

[COLUMN_MAPPING]
source_col0 = license_plate

[EXTRA_COLUMNS]
Vehicle Tags = Block

```

### Section Details

- **[DEFAULT]**

  - `CRON_SCHEDULE`: Defines the `cron` schedule in the standard format (minute hour day_of_month month day_of_week). Ex: `*/2 * * * *` (every 2 minutes). For a suitable configuration, you can visit https://crontab.guru/ to get the appropriate execution schedule.

- **[API]**

  - `API_URL`: [Parkpow API URL](https://app.parkpow.com/documentation/#tag/Vehicles/operation/Import%20Vehicles) for vehicle import.
  - `AUTH_TOKEN`: The authentication token required to access the Parkpow API.

- **[COLUMN_MAPPING]**

  - Mapping of input file columns to desired field names for the API. Format: `source_col<index> = <taget_field_name>`. Ex: `source_col0 = license_plate`.

- **[EXTRA_COLUMNS]**
  - It is used to map columns in the destination spreadsheet that require fixed values. Format: `target_field_name = <value>`.
  - Example: `Vehicle Tags = Block`
    - This modification should only be made if there is a change in the TAG. It is important to remember that the modification will only affect new inclusions in Parkpow.

> You can check the template header by downloading the import template from your [Parkpow Cloud](<(https://app.parkpow.com/vehicles/export/template)>). For Parkpow On-Premise, go to the Vehicles menu, click on the Actions button, select Import, and then choose Download template.

## How to Use

### Prerequisites

- **Docker** (installed and running)

### Usage Steps

1.  **Clone the repository:**

    ```bash
    git clone <YOUR_REPOSITORY_URL>
    cd parkpow/auto-file-import-tool
    ```

2.  **Build the Docker image:**
    This command will build the Docker image for your project.

    ```bash
    docker build -t parkpow-auto-file-import-tool .
    ```

3.  **Create the `data` folder on your host (if it doesn't exist yet):**
    This folder will be used to persist configurations, logs, and data.

    ```bash
    mkdir -p data
    ```

4.  **Run the Docker container:**
    This command will start the container in the background (`-d`), map the `data` folder from your host to `/app/data` inside the container (`-v ./data:/app/data`), and name the container `parkpow-auto-file-import-tool`. On the first run, `data/config.ini` will be automatically created inside the `data` folder on your host.

    ```bash
    docker run -d --name parkpow-auto-file-import-tool -v ./data:/app/data parkpow-auto-file-import-tool
    ```

5.  **Check container logs:**
    To view the container output and `cron` logs in real-time:

    ```bash
    docker logs -f parkpow-auto-file-import-tool
    ```

6.  **To stop the container:**

    ```bash
    docker stop parkpow-auto-file-import-tool
    ```

7.  **To restart the container in case of `config.ini` changes:**

    ```bash
    docker restart parkpow-auto-file-import-tool
    ```

## Logs

All application and `cron` logs are stored in the `data/logs` folder on your host.

- `data/logs/app.log`: Contains detailed logs of the Python script execution.
- `data/logs/cron.log`: Contains standard output and errors from `cron` and the `main.py` script when executed by `cron`.

## Column and Static Data Mapping

The application allows flexibility in data mapping:

- **`COLUMN_MAPPING`**: If your input file has columns like `column_a`, `column_b`, but the API CSV expects `field_x`, `field_y`, you can map them using column indices (starting from 0).

  - Example:
    ```ini
    [COLUMN_MAPPING]
    source_col0 = license_plate
    source_col2 = region
    ```
    - The first file column (index 0) will be mapped to `license_plate`.
    - The second file column (index 1) will be mapped to `region`.

- **`EXTRA_COLUMNS`**: Allows adding fixed fields and values to each record sent to the API, regardless of the CSV content.

  - Example:

    ```ini
    [EXTRA_COLUMNS]
    Vehicle Tags = Block
    ```

    - This modification should only be made if there is a change in the TAG. It is important to remember that the modification will only affect new inclusions in Parkpow.

## Troubleshooting

- **`config.ini` not found / Read error:**

  - Ensure that the `data/config.ini` file exists. If not, it should have been automatically created on the first container run. Check the permissions of the `data` folder on your host.
  - If you manually edited `config.ini`, check that there are no quotes (`"`) around the values, as `configparser` reads quotes as part of the value.

- **Docker container does not start or exits immediately:**

  - Check the container logs (`docker logs parkpow-auto-file-import-tool`) for error messages.
  - This might be a permissions issue with the `data` folder on your host.

- **CSV files are not processed:**
  - Check if the files are in the `data/upload` folder on your host.
  - Check the `CRON_SCHEDULE` in `data/config.ini` to ensure `cron` is scheduled to run.
  - Check the logs in `data/logs/app.log` and `data/logs/cron.log` for any errors during processing.
  - **Note:** The system currently processes only the first file found in the `data/upload` folder during each run. If multiple files are present, only the oldest one will be processed.

---
