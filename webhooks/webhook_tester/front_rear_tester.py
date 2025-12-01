import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests

"""
Expected output when running the tester against properly configured middleware:

--- Scenario 1: Normal pair (front then rear, plate in DB, correct make/model) ---
Response: {"message":"Event buffered, waiting for pair"}
Response: {"message":"Processed camera pair"}

--- Scenario 2: Solo front camera (plate in DB, correct make/model) ---
Response: {"message":"Processed camera pair"}

--- Scenario 3: Solo rear camera (plate in DB, correct make/model) ---
Response: {"message":"Processed camera pair"}

--- Scenario 4: Failed front camera (front fails, rear works, plate in DB, correct make/model) ---
Response: {"message":"Event buffered, waiting for pair"}

--- Scenario 5: Failed rear camera (front works, rear fails, plate in DB, correct make/model) ---
Response: {"message":"Event buffered, waiting for pair"}

--- Scenario 6: Overwrite unpaired event (not in DB) ---
Response: {"message":"Event buffered, waiting for pair"}
Response: {"message":"Event buffered, waiting for pair"}

--- Scenario 7: Plate not in DB ---
Response: {"message":"Event buffered, waiting for pair"}

--- Scenario 8: Make/model mismatch (plate in DB, wrong make/model) ---
Response: {"message":"Event buffered, waiting for pair"}

--- Scenario 9: Camera not configured (plate in DB, correct make/model) ---
Response: {"message":"Camera not configured in any pair"}
"""

CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "../middleware/protocols/config/front_rear_config.json"
)

# Plates known to be in the DB (from user-provided CSV)
IN_DB_PLATES = [
    ("34A23126", "TOYOTA", "YARIS"),
    ("34A36837", "MITSUBISHI", "LANCER"),
    ("89C20339", "ISUZU", "GIGA"),
]

DEFAULT_REGION = "us-ca"


@dataclass
class TestConfig:
    """Test configuration and camera pairs."""

    endpoint: str
    token: str
    normal_pair: dict[str, str] | None
    solo_front: dict[str, str] | None
    solo_rear: dict[str, str] | None
    failed_front: dict[str, str] | None
    failed_rear: dict[str, str] | None
    in_db_plate: str
    in_db_make: str
    in_db_model: str
    region: str = DEFAULT_REGION


def load_config() -> dict[str, Any]:
    """Load middleware configuration from JSON file."""
    with open(CONFIG_PATH) as f:
        return json.load(f)


def find_camera_pairs(config: dict[str, Any]) -> dict[str, dict[str, str] | None]:
    """Find and return all configured camera pairs."""
    pairs = config.get("camera_pairs", [])

    return {
        "normal_pair": next(
            (
                p
                for p in pairs
                if p.get("front") == "camera-front" and p.get("rear") == "camera-rear"
            ),
            None,
        ),
        "solo_front": next(
            (
                p
                for p in pairs
                if p.get("front") == "camera-solo-front" and not p.get("rear")
            ),
            None,
        ),
        "solo_rear": next(
            (
                p
                for p in pairs
                if not p.get("front") and p.get("rear") == "camera-solo-rear"
            ),
            None,
        ),
        "failed_front": next(
            (
                p
                for p in pairs
                if p.get("front") == "camera-failed-front"
                and p.get("rear") == "camera-working-rear"
            ),
            None,
        ),
        "failed_rear": next(
            (
                p
                for p in pairs
                if p.get("front") == "camera-working-front"
                and p.get("rear") == "camera-failed-rear"
            ),
            None,
        ),
    }


def format_timestamp(dt: datetime) -> str:
    """Format datetime as ISO8601 timestamp string."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def build_event(
    camera_id: str,
    plate: str,
    region_code: str,
    timestamp: str,
    endpoint: str,
    make: str = "Porsche",
    model: str = "911",
    orientation: str = "Front",
) -> dict[str, Any]:
    """Build a front_rear event payload matching stream structure."""
    filename = f"{camera_id}_screenshots/image.jpg"
    return {
        "hook": {
            "target": endpoint,
            "id": camera_id,
            "event": "recognition",
            "filename": filename,
        },
        "data": {
            "camera_id": camera_id,
            "filename": filename,
            "timestamp": timestamp,
            "timestamp_local": timestamp,
            "timestamp_camera": None,
            "results": [
                {
                    "box": {"xmax": 412, "xmin": 337, "ymax": 305, "ymin": 270},
                    "candidates": [
                        {"plate": plate, "score": 0.902},
                        {"plate": "plbrec", "score": 0.758},
                    ],
                    "color": [
                        {"color": "red", "score": 0.699},
                        {"color": "black", "score": 0.134},
                        {"color": "blue", "score": 0.03},
                    ],
                    "dscore": 0.757,
                    "model_make": [{"make": make, "model": model, "score": 0.43}],
                    "orientation": [
                        {"orientation": orientation, "score": 0.883},
                        {
                            "orientation": "Rear"
                            if orientation == "Front"
                            else "Front",
                            "score": 0.07,
                        },
                        {"orientation": "Unknown", "score": 0.047},
                    ],
                    "plate": plate,
                    "region": {"code": region_code, "score": 0.179},
                    "score": 0.902,
                    "vehicle": {
                        "box": {"xmax": 590, "xmin": 155, "ymax": 373, "ymin": 71},
                        "score": 0.709,
                        "type": "Sedan",
                    },
                    "direction": 210,
                    "source_url": "/user-data/video.mp4",
                    "position_sec": 23.47,
                }
            ],
        },
    }


def send_event(url: str, token: str, event: dict[str, Any]) -> requests.Response:
    """Send event to middleware endpoint with optional image attachment."""
    files = {}
    image_path = "./small.jpg"
    if os.path.exists(image_path):
        files["upload"] = ("small.jpg", open(image_path, "rb"), "image/jpeg")

    data = {"json": json.dumps(event)}
    headers = {"Authorization": f"Token {token}"} if token else {}

    try:
        resp = requests.post(url, data=data, files=files, headers=headers, timeout=30)
        return resp
    finally:
        if "upload" in files:
            files["upload"][1].close()


def print_result(
    resp: requests.Response,
    plate: str | None = None,
    make: str | None = None,
    model: str | None = None,
    camera: str | None = None,
) -> None:
    """Print test result with event metadata."""
    if plate or make or model or camera:
        print(f"[camera={camera} plate={plate} make={make} model={model}]")
    print(f"Status code: {resp.status_code}")
    print(f"Response: {resp.text}")


def send_and_print(
    test_cfg: TestConfig,
    camera_id: str,
    plate: str,
    timestamp: str,
    orientation: str,
    make: str | None = None,
    model: str | None = None,
    description: str | None = None,
) -> None:
    """Helper to build, send event, and print result."""
    if description:
        print(description)

    event = build_event(
        camera_id=camera_id,
        plate=plate,
        region_code=test_cfg.region,
        timestamp=timestamp,
        endpoint=test_cfg.endpoint,
        make=make or "Porsche",
        model=model or "911",
        orientation=orientation,
    )

    resp = send_event(test_cfg.endpoint, test_cfg.token, event)
    print_result(resp, plate, make, model, camera_id)


def run_scenarios(args: argparse.Namespace, config: dict[str, Any]) -> None:
    """Execute all test scenarios against the middleware."""
    now = datetime.now(timezone.utc)
    timestamp = format_timestamp(now)
    in_db_plate, in_db_make, in_db_model = IN_DB_PLATES[0]

    camera_pairs = find_camera_pairs(config)
    test_cfg = TestConfig(
        endpoint=args.endpoint,
        token=args.token,
        in_db_plate=in_db_plate,
        in_db_make=in_db_make,
        in_db_model=in_db_model,
        region=DEFAULT_REGION,
        normal_pair=camera_pairs["normal_pair"],
        solo_front=camera_pairs["solo_front"],
        solo_rear=camera_pairs["solo_rear"],
        failed_front=camera_pairs["failed_front"],
        failed_rear=camera_pairs["failed_rear"],
    )

    # Scenario 1: Normal pair (front then rear, plate in DB, correct make/model)
    if test_cfg.normal_pair:
        print(
            "\n--- Scenario 1: Normal pair (front then rear, plate in DB, correct make/model) ---"
        )
        print("Sending front event...")
        send_and_print(
            test_cfg,
            test_cfg.normal_pair["front"],
            test_cfg.in_db_plate,
            timestamp,
            "Front",
            test_cfg.in_db_make,
            test_cfg.in_db_model,
        )
        print("Sending rear event...")
        send_and_print(
            test_cfg,
            test_cfg.normal_pair["rear"],
            test_cfg.in_db_plate,
            timestamp,
            "Rear",
            test_cfg.in_db_make,
            test_cfg.in_db_model,
        )

    # Scenario 2: Solo front (in DB plate, correct make/model)
    if test_cfg.solo_front:
        print(
            "\n--- Scenario 2: Solo front camera (plate in DB, correct make/model) ---"
        )
        print("Sending solo front event...")
        send_and_print(
            test_cfg,
            test_cfg.solo_front["front"],
            test_cfg.in_db_plate,
            timestamp,
            "Front",
            test_cfg.in_db_make,
            test_cfg.in_db_model,
        )

    # Scenario 3: Solo rear (in DB plate, correct make/model)
    if test_cfg.solo_rear:
        print(
            "\n--- Scenario 3: Solo rear camera (plate in DB, correct make/model) ---"
        )
        print("Sending solo rear event...")
        send_and_print(
            test_cfg,
            test_cfg.solo_rear["rear"],
            test_cfg.in_db_plate,
            timestamp,
            "Rear",
            test_cfg.in_db_make,
            test_cfg.in_db_model,
        )

    # Scenario 4: Failed front (in DB plate, correct make/model)
    if test_cfg.failed_front:
        print(
            "\n--- Scenario 4: Failed front camera (front fails, rear works, plate in DB, correct make/model) ---"
        )
        print("Sending rear event only...")
        send_and_print(
            test_cfg,
            test_cfg.failed_front["rear"],
            test_cfg.in_db_plate,
            timestamp,
            "Rear",
            test_cfg.in_db_make,
            test_cfg.in_db_model,
        )

    # Scenario 5: Failed rear (in DB plate, correct make/model)
    if test_cfg.failed_rear:
        print(
            "\n--- Scenario 5: Failed rear camera (front works, rear fails, plate in DB, correct make/model) ---"
        )
        print("Sending front event only...")
        send_and_print(
            test_cfg,
            test_cfg.failed_rear["front"],
            test_cfg.in_db_plate,
            timestamp,
            "Front",
            test_cfg.in_db_make,
            test_cfg.in_db_model,
        )

    # Scenario 6: Overwrite event (new plate before pair completes, not in DB)
    if test_cfg.normal_pair:
        print("\n--- Scenario 6: Overwrite unpaired event (not in DB) ---")
        print("Sending front event with OLD123...")
        send_and_print(
            test_cfg, test_cfg.normal_pair["front"], "OLD123", timestamp, "Front"
        )
        print("Sending front event with NEW456 (should overwrite)...")
        send_and_print(
            test_cfg, test_cfg.normal_pair["front"], "NEW456", timestamp, "Front"
        )

    # Scenario 7: Plate not in DB
    if test_cfg.normal_pair:
        print("\n--- Scenario 7: Plate not in DB ---")
        print("Sending front event with unknown plate...")
        send_and_print(
            test_cfg, test_cfg.normal_pair["front"], "NOTINDB", timestamp, "Front"
        )

    # Scenario 8: Make/model mismatch (in DB plate, wrong make/model)
    if test_cfg.normal_pair:
        print(
            "\n--- Scenario 8: Make/model mismatch (plate in DB, wrong make/model) ---"
        )
        print("Sending front event with mismatched make/model...")
        send_and_print(
            test_cfg,
            test_cfg.normal_pair["front"],
            test_cfg.in_db_plate,
            timestamp,
            "Front",
            "Toyota",
            "Corolla",
        )

    # Scenario 9: Camera not configured (in DB plate, correct make/model)
    print(
        "\n--- Scenario 9: Camera not configured (plate in DB, correct make/model) ---"
    )
    print("Sending event from unknown camera...")
    send_and_print(
        test_cfg,
        "unknown-camera",
        test_cfg.in_db_plate,
        timestamp,
        "Front",
        test_cfg.in_db_make,
        test_cfg.in_db_model,
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test front-rear middleware event scenarios (config-driven)"
    )
    parser.add_argument("--endpoint", required=True, help="Webhook endpoint URL")
    parser.add_argument("--token", required=True, help="Authorization token (required)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    config = load_config()
    try:
        run_scenarios(args, config)
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"\n--> An error occurred: {e}")
        print("--> The test failed.")
