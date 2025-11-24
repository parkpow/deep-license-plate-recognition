"""
Pytest tests for Front-Rear Stream Middleware Protocol.

Run with:
    pytest tests/test_front_rear.py -vx
    pytest tests/test_front_rear.py -v --watch  (with pytest-watcher)
    ptw tests/test_front_rear.py  (with pytest-watch)
"""

import json
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import protocols.front_rear as front_rear

TEST_CONFIG = {
    "parkpow": {
        "alert_endpoint": "https://test.example.com/alerts",
        "webhook_endpoint": "https://test.example.com/webhook",
        "token": "test-token",
    },
    "thresholds": {"make_model_confidence": 0.2},
    "pairing": {"time_window_seconds": 30, "cleanup_interval_seconds": 60},
    "alerts": {
        "plate_mismatch": {"enabled": True, "name": "Test Plate Mismatch"},
        "no_rear_plate": {"enabled": True, "name": "Test No Rear Plate"},
        "make_model_mismatch": {"enabled": True, "name": "Test Make/Model Mismatch"},
        "camera_offline": {"enabled": True, "name": "Test Camera Offline"},
    },
}


@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("STREAM_API_TOKEN", "test-stream-token")
    monkeypatch.setenv("PARKPOW_TOKEN", "test-parkpow-token")


@pytest.fixture
def sample_front_rear_csv(tmp_path):
    csv_content = """LICENSE_PLATE,MAKE,MODEL
ABC123,TOYOTA,CAMRY
XYZ789,HONDA,ACCORD
TEST001,FORD,FOCUS
"""
    csv_file = tmp_path / "front_rear.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


@pytest.fixture
def sample_config(tmp_path, sample_front_rear_csv):
    config_data = {
        "camera_pairs": [
            {
                "front": "camera-front",
                "rear": "camera-rear",
                "description": "Entry Gate 1",
            }
        ],
        "thresholds": {"make_model_confidence": 0.2},
        "pairing": {"time_window_seconds": 30, "cleanup_interval_seconds": 60},
        "front_rear_csv_path": sample_front_rear_csv,
        "parkpow": {
            "alert_endpoint": "https://test.example.com/alerts",
            "webhook_endpoint": "https://test.example.com/webhook",
            "token": "${PARKPOW_TOKEN}",
        },
        "alerts": {
            "plate_mismatch": {"enabled": True, "name": "Test Plate Mismatch"},
            "no_rear_plate": {"enabled": True, "name": "Test No Rear Plate"},
            "make_model_mismatch": {
                "enabled": True,
                "name": "Test Make/Model Mismatch",
            },
            "camera_offline": {"enabled": True, "name": "Test Camera Offline"},
        },
    }
    config_dir = tmp_path / "protocols" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "front_rear_config.json"
    config_file.write_text(json.dumps(config_data, indent=2))

    return str(config_file)


@pytest.fixture
def reset_front_rear_state():
    front_rear.front_rear_vehicles = {}
    front_rear.camera_pairs = []
    front_rear.config = {}
    front_rear.event_buffer = {}
    front_rear._config_cache = None
    front_rear._config_last_load = 0.0
    yield

    front_rear.front_rear_vehicles = {}
    front_rear.camera_pairs = []
    front_rear.config = {}
    front_rear.event_buffer = {}
    front_rear._config_cache = None
    front_rear._config_last_load = 0.0


class TestConfigLoading:
    def test_load_config_success(
        self, reset_front_rear_state, sample_config, monkeypatch
    ):
        monkeypatch.chdir(Path(sample_config).parent.parent.parent)
        config = front_rear._load_config()

        assert "camera_pairs" in config
        assert len(config["camera_pairs"]) == 1
        assert config["camera_pairs"][0]["front"] == "camera-front"
        assert config["thresholds"]["make_model_confidence"] == 0.2

    def test_load_config_with_env_substitution(
        self, reset_front_rear_state, sample_config, mock_env_vars, monkeypatch
    ):
        monkeypatch.chdir(Path(sample_config).parent.parent.parent)
        config = front_rear._load_config()

        assert config["parkpow"]["token"] == "test-parkpow-token"

    def test_load_config_caching(
        self, reset_front_rear_state, sample_config, monkeypatch
    ):
        monkeypatch.chdir(Path(sample_config).parent.parent.parent)

        config1 = front_rear._load_config()
        config2 = front_rear._load_config()

        assert config1 is config2

    def test_load_config_file_not_found(
        self, reset_front_rear_state, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)

        with patch("protocols.front_rear.logging.error") as mock_log:
            config = front_rear._load_config()

            assert config == {}
            mock_log.assert_called_once()
            assert "Configuration file not found" in mock_log.call_args[0][0]


class TestCSVLoading:
    def test_load_front_rear_csv_success(
        self, reset_front_rear_state, sample_config, monkeypatch
    ):
        monkeypatch.chdir(Path(sample_config).parent.parent.parent)
        front_rear.load_front_rear_csv()

        assert len(front_rear.front_rear_vehicles) == 3
        assert "ABC123" in front_rear.front_rear_vehicles
        assert front_rear.front_rear_vehicles["ABC123"]["make"] == "TOYOTA"
        assert front_rear.front_rear_vehicles["ABC123"]["model"] == "CAMRY"

    def test_load_front_rear_csv_empty_file(
        self, reset_front_rear_state, tmp_path, monkeypatch
    ):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("LICENSE_PLATE,MAKE,MODEL\n")
        config_data = {
            "front_rear_csv_path": str(csv_file),
            "camera_pairs": [],
            "thresholds": {},
            "pairing": {},
        }
        config_dir = tmp_path / "protocols" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "front_rear_config.json"
        config_file.write_text(json.dumps(config_data))
        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValueError, match="Front-Rear database is empty"):
            front_rear.load_front_rear_csv()

    def test_load_front_rear_csv_file_not_found(
        self, reset_front_rear_state, tmp_path, monkeypatch
    ):
        config_data = {
            "front_rear_csv_path": "nonexistent.csv",
            "camera_pairs": [],
            "thresholds": {},
            "pairing": {},
        }
        config_dir = tmp_path / "protocols" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "front_rear_config.json"
        config_file.write_text(json.dumps(config_data))
        monkeypatch.chdir(tmp_path)

        with pytest.raises(FileNotFoundError):
            front_rear.load_front_rear_csv()


class TestCameraPairLookup:
    pairs = [
        {"front": "cam1", "rear": "cam2", "description": "Gate 1"},
        {"front": "cam3", "rear": "cam4", "description": "Gate 2"},
    ]

    def test_get_camera_pair_front_camera(self, reset_front_rear_state):
        front_rear.camera_pairs = self.pairs
        pair = front_rear._get_camera_pair("cam1")

        assert pair is not None
        assert pair["front"] == "cam1"
        assert pair["rear"] == "cam2"

    def test_get_camera_pair_rear_camera(self, reset_front_rear_state):
        front_rear.camera_pairs = self.pairs
        pair = front_rear._get_camera_pair("cam2")

        assert pair is not None
        assert pair["front"] == "cam1"
        assert pair["rear"] == "cam2"

    def test_get_camera_pair_not_found(self, reset_front_rear_state):
        front_rear.camera_pairs = self.pairs
        pair = front_rear._get_camera_pair("cam5")

        assert pair is None

    def test_get_camera_pair_multiple_pairs(self, reset_front_rear_state):
        front_rear.camera_pairs = self.pairs
        pair = front_rear._get_camera_pair("cam3")

        assert pair is not None
        assert pair["description"] == "Gate 2"


class TestPlateExtraction:
    def test_extract_plate_valid_string(self, reset_front_rear_state):
        result = {"plate": "abc123"}
        plate = front_rear._extract_plate(result)

        assert plate == "ABC123"

    def test_extract_plate_with_whitespace(self, reset_front_rear_state):
        result = {"plate": "  xyz789  "}
        plate = front_rear._extract_plate(result)

        assert plate == "XYZ789"

    def test_extract_plate_missing_field(self, reset_front_rear_state):
        result = {}
        plate = front_rear._extract_plate(result)

        assert plate is None

    def test_extract_plate_none_value(self, reset_front_rear_state):
        result = {"plate": None}
        plate = front_rear._extract_plate(result)

        assert plate is None

    def test_extract_plate_invalid_type(self, reset_front_rear_state):
        result = {"plate": 12345}
        plate = front_rear._extract_plate(result)

        assert plate is None


class TestMakeModelExtraction:
    def test_extract_best_make_model_single_result(self, reset_front_rear_state):
        results = [
            {"model_make": [{"make": "TOYOTA", "model": "CAMRY", "score": 0.85}]}
        ]
        make_model, score = front_rear._extract_best_make_model(results)

        assert make_model == "TOYOTA CAMRY"
        assert score == 0.85

    def test_extract_best_make_model_multiple_detections(self, reset_front_rear_state):
        results = [
            {
                "model_make": [
                    {"make": "TOYOTA", "model": "CAMRY", "score": 0.65},
                    {"make": "HONDA", "model": "ACCORD", "score": 0.85},
                    {"make": "FORD", "model": "FOCUS", "score": 0.45},
                ]
            }
        ]
        make_model, score = front_rear._extract_best_make_model(results)

        assert make_model == "HONDA ACCORD"
        assert score == 0.85

    def test_extract_best_make_model_multiple_results(self, reset_front_rear_state):
        results = [
            {"model_make": [{"make": "TOYOTA", "model": "CAMRY", "score": 0.65}]},
            {"model_make": [{"make": "HONDA", "model": "ACCORD", "score": 0.85}]},
        ]
        make_model, score = front_rear._extract_best_make_model(results)

        assert make_model == "HONDA ACCORD"
        assert score == 0.85

    def test_extract_best_make_model_empty_results(self, reset_front_rear_state):
        results = []
        make_model, score = front_rear._extract_best_make_model(results)

        assert make_model is None
        assert score == 0.0

    def test_extract_best_make_model_no_detections(self, reset_front_rear_state):
        results = [{"model_make": []}]
        make_model, score = front_rear._extract_best_make_model(results)

        assert make_model is None
        assert score == 0.0

    def test_extract_best_make_model_missing_fields(self, reset_front_rear_state):
        results = [
            {"model_make": [{"make": "TOYOTA", "score": 0.85}]}  # Missing model
        ]
        make_model, score = front_rear._extract_best_make_model(results)

        assert make_model == "TOYOTA"
        assert score == 0.85


class TestPlateDatabase:
    def test_check_plate_in_db_found(self, reset_front_rear_state):
        front_rear.front_rear_vehicles = {
            "ABC123": {"make": "TOYOTA", "model": "CAMRY"}
        }
        found, vehicle_info = front_rear._check_plate_in_front_rear_db("ABC123")

        assert found is True
        assert vehicle_info is not None
        assert vehicle_info["make"] == "TOYOTA"
        assert vehicle_info["model"] == "CAMRY"

    def test_check_plate_in_db_not_found(self, reset_front_rear_state):
        front_rear.front_rear_vehicles = {
            "ABC123": {"make": "TOYOTA", "model": "CAMRY"}
        }
        found, vehicle_info = front_rear._check_plate_in_front_rear_db("XYZ999")

        assert found is False
        assert vehicle_info is None

    def test_check_plate_in_db_case_insensitive(self, reset_front_rear_state):
        front_rear.front_rear_vehicles = {
            "ABC123": {"make": "TOYOTA", "model": "CAMRY"}
        }
        found, vehicle_info = front_rear._check_plate_in_front_rear_db("abc123")

        assert found is True
        assert vehicle_info is not None

    def test_check_plate_in_db_none_plate(self, reset_front_rear_state):
        front_rear.front_rear_vehicles = {
            "ABC123": {"make": "TOYOTA", "model": "CAMRY"}
        }
        found, vehicle_info = front_rear._check_plate_in_front_rear_db(None)

        assert found is False
        assert vehicle_info is None


class TestAlertSending:
    @patch("protocols.front_rear.requests.post")
    def test_send_alert_success(self, mock_post, reset_front_rear_state):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        front_rear.config = TEST_CONFIG
        front_rear._send_alert(
            alert_type="plate_mismatch",
            plate="ABC123",
            camera_id="camera-front",
            message="Test message",
        )

        mock_post.assert_called_once()
        call_args = mock_post.call_args

        assert call_args[0][0] == "https://test.example.com/alerts"
        assert "Authorization" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Authorization"] == "Token test-token"

        payload = call_args[1]["json"]
        assert payload["alert_type"] == "plate_mismatch"
        assert payload["license_plate"] == "ABC123"
        assert payload["camera_id"] == "camera-front"

    @patch("protocols.front_rear.requests.post")
    def test_send_alert_with_make_model(self, mock_post, reset_front_rear_state):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        front_rear.config = TEST_CONFIG
        front_rear._send_alert(
            alert_type="plate_mismatch",
            plate="ABC123",
            camera_id="camera-front",
            message="Test message",
            detected_make_model="TOYOTA CAMRY",
            make_model_score=0.85,
        )

        payload = mock_post.call_args[1]["json"]
        assert "detected_vehicle" in payload
        assert payload["detected_vehicle"]["make_model"] == "TOYOTA CAMRY"
        assert payload["detected_vehicle"]["score"] == 0.85

    def test_send_alert_disabled(self, reset_front_rear_state):
        config_with_disabled = TEST_CONFIG.copy()
        config_with_disabled["alerts"] = {
            "plate_mismatch": {"enabled": False, "name": "Test Alert"}
        }
        front_rear.config = config_with_disabled

        with patch("protocols.front_rear.requests.post") as mock_post:
            front_rear._send_alert(
                alert_type="plate_mismatch",
                plate="ABC123",
                camera_id="camera-front",
                message="Test message",
            )

            mock_post.assert_not_called()


class TestWebhookProcessing:
    def test_process_request_authentication_success(
        self, reset_front_rear_state, mock_env_vars
    ):
        front_rear.config = TEST_CONFIG
        front_rear.camera_pairs = [
            {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        ]
        webhook_data = {
            "webhook_header": {"Authorization": "test-stream-token"},
            "data": {
                "camera_id": "camera-front",
                "results": [{"plate": "ABC123"}],
                "timestamp": "2025-11-24T10:00:00Z",
            },
        }
        _response, status = front_rear.process_request(webhook_data)

        assert status == 200
        assert "camera-front" in front_rear.event_buffer

    def test_process_request_authentication_missing(
        self, reset_front_rear_state, mock_env_vars
    ):
        webhook_data = {"webhook_header": {}, "data": {"camera_id": "camera-front"}}
        response, status = front_rear.process_request(webhook_data)

        assert status == 401
        assert "Unauthorized" in response

    def test_process_request_authentication_invalid(
        self, reset_front_rear_state, mock_env_vars
    ):
        webhook_data = {
            "webhook_header": {"Authorization": "wrong-token"},
            "data": {"camera_id": "camera-front"},
        }
        response, status = front_rear.process_request(webhook_data)

        assert status == 403
        assert "Forbidden" in response

    def test_process_request_missing_camera_id(
        self, reset_front_rear_state, mock_env_vars
    ):
        webhook_data = {
            "webhook_header": {"Authorization": "test-stream-token"},
            "data": {},
        }
        response, status = front_rear.process_request(webhook_data)

        assert status == 400
        assert "camera_id" in response

    def test_process_request_camera_not_in_pair(
        self, reset_front_rear_state, mock_env_vars
    ):
        front_rear.camera_pairs = [
            {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        ]
        webhook_data = {
            "webhook_header": {"Authorization": "test-stream-token"},
            "data": {
                "camera_id": "camera-unknown",
                "results": [{"plate": "ABC123"}],
                "timestamp": "2025-11-24T10:00:00Z",
            },
        }

        response, status = front_rear.process_request(webhook_data)

        assert status == 200
        assert "not configured" in response

    def test_process_request_no_results(self, reset_front_rear_state, mock_env_vars):
        front_rear.camera_pairs = [
            {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        ]
        webhook_data = {
            "webhook_header": {"Authorization": "test-stream-token"},
            "data": {
                "camera_id": "camera-front",
                "results": [],
                "timestamp": "2025-11-24T10:00:00Z",
            },
        }
        response, status = front_rear.process_request(webhook_data)

        assert status == 200
        assert "No results" in response

    def test_process_request_buffering(self, reset_front_rear_state, mock_env_vars):
        front_rear.config = TEST_CONFIG
        front_rear.camera_pairs = [
            {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        ]
        webhook_data = {
            "webhook_header": {"Authorization": "test-stream-token"},
            "data": {
                "camera_id": "camera-front",
                "results": [{"plate": "ABC123"}],
                "timestamp": "2025-11-24T10:00:00Z",
            },
        }
        response, status = front_rear.process_request(webhook_data)

        assert status == 200
        assert "buffered" in response.lower()
        assert "camera-front" in front_rear.event_buffer

    @patch("protocols.front_rear._process_camera_pair")
    def test_process_request_pair_processing(
        self, mock_process_pair, reset_front_rear_state, mock_env_vars
    ):
        front_rear.config = TEST_CONFIG
        front_rear.camera_pairs = [
            {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        ]
        current_time = time.time()
        front_rear.event_buffer["camera-front"] = {
            "camera_id": "camera-front",
            "results": [{"plate": "ABC123"}],
            "timestamp": "2024-11-24T10:00:00Z",
            "timestamp_unix": current_time,
        }

        from datetime import datetime

        timestamp_str = datetime.fromtimestamp(current_time).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        webhook_data = {
            "webhook_header": {"Authorization": "test-stream-token"},
            "data": {
                "camera_id": "camera-rear",
                "results": [{"plate": "ABC123"}],
                "timestamp": timestamp_str,
            },
        }
        _response, status = front_rear.process_request(webhook_data)

        assert status == 200
        mock_process_pair.assert_called_once()

    @patch("protocols.front_rear._process_camera_pair")
    @patch("protocols.front_rear._send_alert")
    def test_process_request_overwrite_unpaired_event(
        self, mock_send_alert, mock_process_pair, reset_front_rear_state, mock_env_vars
    ):
        """Test that overwriting an unpaired event processes it before replacement."""
        front_rear.config = TEST_CONFIG
        front_rear.camera_pairs = [
            {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        ]
        old_time = time.time() - 20
        front_rear.event_buffer["camera-front"] = {
            "camera_id": "camera-front",
            "results": [{"plate": "OLD123"}],
            "timestamp": "2024-11-24T10:00:00Z",
            "timestamp_unix": old_time,
        }

        webhook_data = {
            "webhook_header": {"Authorization": "test-stream-token"},
            "data": {
                "camera_id": "camera-front",
                "results": [{"plate": "NEW456"}],
                "timestamp": "2024-11-24T10:00:20Z",
            },
        }
        response, status = front_rear.process_request(webhook_data)

        assert status == 200
        mock_process_pair.assert_called_once()
        alert_types = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "camera_offline" in alert_types


class TestCameraPairProcessing:
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_plate_not_in_db(
        self, mock_send_alert, reset_front_rear_state
    ):
        front_rear.front_rear_vehicles = {}
        front_rear.config = TEST_CONFIG
        front_event = {
            "results": [{"plate": "UNKNOWN123"}],
            "timestamp": "2025-11-24T10:00:00Z",
        }
        rear_event = {
            "results": [{"plate": "UNKNOWN123"}],
            "timestamp": "2025-11-24T10:00:05Z",
        }
        pair = {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        front_rear._process_camera_pair(front_event, rear_event, pair)

        assert mock_send_alert.call_count >= 2
        alert_calls = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "plate_mismatch" in alert_calls

    @patch("protocols.front_rear._send_alert")
    def test_process_pair_no_rear_plate(self, mock_send_alert, reset_front_rear_state):
        front_rear.config = TEST_CONFIG
        front_event = {
            "results": [{"plate": "ABC123"}],
            "timestamp": "2025-11-24T10:00:00Z",
        }
        rear_event = {
            "results": [{"plate": None}],  # No plate detected
            "timestamp": "2025-11-24T10:00:05Z",
        }
        pair = {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        front_rear._process_camera_pair(front_event, rear_event, pair)

        alert_calls = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "no_rear_plate" in alert_calls

    @patch("protocols.front_rear._send_alert")
    def test_process_pair_make_model_mismatch(
        self, mock_send_alert, reset_front_rear_state
    ):
        front_rear.front_rear_vehicles = {
            "ABC123": {"make": "TOYOTA", "model": "CAMRY"}
        }
        front_rear.config = TEST_CONFIG
        front_event = {
            "results": [
                {
                    "plate": "ABC123",
                    "model_make": [{"make": "HONDA", "model": "ACCORD", "score": 0.85}],
                }
            ],
            "timestamp": "2025-11-24T10:00:00Z",
        }
        rear_event = {
            "results": [{"plate": "ABC123"}],
            "timestamp": "2025-11-24T10:00:05Z",
        }
        pair = {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        front_rear._process_camera_pair(front_event, rear_event, pair)

        alert_calls = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "make_model_mismatch" in alert_calls

    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_forwards_rear_data(
        self, mock_send_alert, mock_forward, reset_front_rear_state
    ):
        front_rear.front_rear_vehicles = {
            "ABC123": {"make": "TOYOTA", "model": "CAMRY"}
        }
        front_rear.config = TEST_CONFIG
        front_event = {
            "results": [{"plate": "ABC123"}],
            "timestamp": "2025-11-24T10:00:00Z",
        }
        rear_event = {
            "results": [{"plate": "ABC123"}],
            "timestamp": "2025-11-24T10:00:05Z",
            "original_json_data": {"test": "rear_data"},
            "original_files": None,
        }
        pair = {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        front_rear._process_camera_pair(front_event, rear_event, pair)

        mock_forward.assert_called_once()
        call_args = mock_forward.call_args[0]
        assert call_args[0] == {"test": "rear_data"}

    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_forwards_front_data_when_rear_unavailable(
        self, mock_send_alert, mock_forward, reset_front_rear_state
    ):
        """Test that front camera data is forwarded when rear camera is unavailable."""
        front_rear.front_rear_vehicles = {
            "ABC123": {"make": "TOYOTA", "model": "CAMRY"}
        }
        front_rear.config = TEST_CONFIG
        front_event = {
            "results": [{"plate": "ABC123"}],
            "timestamp": "2025-11-24T10:00:00Z",
            "original_json_data": {"test": "front_data"},
            "original_files": None,
        }
        rear_event = None
        pair = {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        front_rear._process_camera_pair(front_event, rear_event, pair)

        mock_forward.assert_called_once()
        call_args = mock_forward.call_args[0]
        assert call_args[0] == {"test": "front_data"}

    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_single_front_camera_validates_db(
        self, mock_send_alert, mock_forward, reset_front_rear_state
    ):
        front_rear.front_rear_vehicles = {}
        front_rear.config = TEST_CONFIG
        front_event = {
            "results": [{"plate": "UNKNOWN123"}],
            "timestamp": "2025-11-24T10:00:00Z",
            "original_json_data": {"test": "front_data"},
            "original_files": None,
        }
        rear_event = None
        pair = {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        front_rear._process_camera_pair(
            front_event, rear_event, pair, camera_offline="camera-rear"
        )

        alert_types = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "no_rear_plate" not in alert_types
        assert "plate_mismatch" in alert_types
        mock_forward.assert_called_once()

    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_single_rear_camera_validates_db(
        self, mock_send_alert, mock_forward, reset_front_rear_state
    ):
        """Test that single rear camera event validates against database."""
        front_rear.front_rear_vehicles = {}
        front_rear.config = TEST_CONFIG
        front_event = None
        rear_event = {
            "results": [{"plate": "UNKNOWN123"}],
            "timestamp": "2025-11-24T10:00:05Z",
            "original_json_data": {"test": "rear_data"},
            "original_files": None,
        }
        pair = {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        front_rear._process_camera_pair(front_event, rear_event, pair)

        alert_types = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "plate_mismatch" in alert_types

        mock_forward.assert_called_once()
        call_args = mock_forward.call_args[0]
        assert call_args[0] == {"test": "rear_data"}

    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_rear_camera_online_no_plate(
        self, mock_send_alert, mock_forward, reset_front_rear_state
    ):
        """Test that no_rear_plate alert is sent when rear camera is online but detects no plate."""
        front_rear.front_rear_vehicles = {
            "ABC123": {"make": "TOYOTA", "model": "CAMRY"}
        }
        front_rear.config = TEST_CONFIG
        front_event = {
            "results": [{"plate": "ABC123"}],
            "timestamp": "2025-11-24T10:00:00Z",
        }
        rear_event = {
            "results": [{"plate": None}],
            "timestamp": "2025-11-24T10:00:05Z",
            "original_json_data": {"test": "rear_data"},
            "original_files": None,
        }
        pair = {"front": "camera-front", "rear": "camera-rear", "description": "Gate 1"}
        front_rear._process_camera_pair(front_event, rear_event, pair)

        alert_types = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "no_rear_plate" in alert_types


class TestCleanupExpiredEvents:
    @patch("protocols.front_rear._process_camera_pair")
    @patch("protocols.front_rear._send_alert")
    def test_cleanup_processes_expired_events(
        self, mock_send_alert, mock_process_pair, reset_front_rear_state
    ):
        front_rear.config = TEST_CONFIG
        front_rear.camera_pairs = [
            {"front": "camera-old", "rear": "camera-old-rear", "description": "Gate 1"},
            {"front": "camera-new", "rear": "camera-new-rear", "description": "Gate 2"},
        ]
        front_rear.event_buffer["camera-old"] = {
            "camera_id": "camera-old",
            "timestamp_unix": time.time() - 100,  # 100 seconds ago (expired)
            "results": [{"plate": "ABC123"}],
        }
        front_rear.event_buffer["camera-new"] = {
            "camera_id": "camera-new",
            "timestamp_unix": time.time() - 10,  # 10 seconds ago (not expired)
            "results": [{"plate": "XYZ789"}],
        }
        front_rear._cleanup_expired_events()

        mock_process_pair.assert_called_once()
        alert_types = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "camera_offline" in alert_types
        assert "camera-old" not in front_rear.event_buffer
        assert "camera-new" in front_rear.event_buffer


class TestInitialization:
    @patch("protocols.front_rear.threading.Thread")
    def test_initialize_front_rear_middleware(
        self, mock_thread, reset_front_rear_state, sample_config, monkeypatch
    ):
        monkeypatch.chdir(Path(sample_config).parent.parent.parent)
        front_rear.initialize_front_rear_middleware()

        assert len(front_rear.front_rear_vehicles) > 0
        assert len(front_rear.camera_pairs) > 0
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
        assert mock_thread.call_args[1]["daemon"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
