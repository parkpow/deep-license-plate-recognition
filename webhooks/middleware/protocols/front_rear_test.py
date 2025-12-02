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


def close_coroutine(coro):
    """Helper to close a coroutine and prevent 'never awaited' warnings."""
    try:
        coro.close()
    except Exception:
        pass


TEST_CONFIG = {
    "parkpow": {
        "alert_endpoint": "https://test.example.com/alerts",
        "webhook_endpoint": "https://test.example.com/webhook",
        "token": "test-token",
    },
    "thresholds": {"make_model_confidence": 0.2},
    "pairing": {"time_window_seconds": 30, "cleanup_interval_seconds": 60},
    "alerts": {
        "plate_mismatch": {
            "enabled": True,
            "name": "Test Plate Mismatch",
            "alert_template_id": 1,
        },
        "no_rear_plate": {
            "enabled": True,
            "name": "Test No Rear Plate",
            "alert_template_id": 2,
        },
        "make_model_mismatch": {
            "enabled": True,
            "name": "Test Make/Model Mismatch",
            "alert_template_id": 3,
        },
        "camera_offline": {
            "enabled": True,
            "name": "Test Camera Offline",
            "alert_template_id": 4,
        },
    },
}


@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("STREAM_API_TOKEN", "test-stream-token")
    monkeypatch.setenv("PARKPOW_TOKEN", "test-parkpow-token")


@pytest.fixture
def create_camera_event():
    """Factory fixture to create CameraEvent instances with default values."""

    def _create(
        camera_id="camera-front",
        plate="ABC123",
        timestamp=None,
        timestamp_unix=None,
        original_json_data=None,
        original_files=None,
        model_make=None,
    ):
        results = [{"plate": plate}]
        if model_make:
            results[0]["model_make"] = model_make

        return front_rear.CameraEvent(
            camera_id=camera_id,
            results=results,
            timestamp=timestamp or "2025-11-24T10:00:00Z",
            timestamp_local=None,
            timestamp_unix=timestamp_unix or time.time(),
            original_json_data=original_json_data or {},
            original_files=original_files,
        )

    return _create


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
            "token": "test-parkpow-token",
        },
        "alerts": {
            "plate_mismatch": {
                "enabled": True,
                "name": "Test Plate Mismatch",
                "alert_template_id": 1,
            },
            "no_rear_plate": {
                "enabled": True,
                "name": "Test No Rear Plate",
                "alert_template_id": 2,
            },
            "make_model_mismatch": {
                "enabled": True,
                "name": "Test Make/Model Mismatch",
                "alert_template_id": 3,
            },
            "camera_offline": {
                "enabled": True,
                "name": "Test Camera Offline",
                "alert_template_id": 4,
            },
        },
    }
    config_dir = tmp_path / "protocols" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "front_rear_config.json"
    config_file.write_text(json.dumps(config_data, indent=2))

    return str(config_file)


@pytest.fixture
def mock_asyncio_for_alerts():
    """Mock asyncio components for tests that use _send_alert."""
    with patch("protocols.front_rear._loop"), patch(
        "protocols.front_rear._aiohttp_session"
    ), patch("protocols.front_rear.asyncio.run_coroutine_threadsafe") as mock_run:

        def run_coro_side_effect(coro, loop):
            close_coroutine(coro)
            mock_future = Mock()
            mock_future.result.return_value = None
            return mock_future

        mock_run.side_effect = run_coro_side_effect
        yield


@pytest.fixture
def reset_front_rear_state():
    front_rear.csv_vehicles = {}
    front_rear.camera_pairs = []
    front_rear.config = {}
    front_rear._config_cache = None
    front_rear._config_last_load = 0.0
    yield

    front_rear.csv_vehicles = {}
    front_rear.camera_pairs = []
    front_rear.config = {}
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
        front_rear._load_vehicles_csv()

        assert len(front_rear.csv_vehicles) == 3
        assert "ABC123" in front_rear.csv_vehicles
        assert front_rear.csv_vehicles["ABC123"]["make"] == "TOYOTA"
        assert front_rear.csv_vehicles["ABC123"]["model"] == "CAMRY"

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
            front_rear._load_vehicles_csv()

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
            front_rear._load_vehicles_csv()


class TestCameraPairLookup:
    pairs = [
        {"front": "cam1", "rear": "cam2", "description": "Gate 1"},
        {"front": "cam3", "rear": "cam4", "description": "Gate 2"},
    ]

    @pytest.mark.parametrize("camera_id", ["cam1", "cam2"])
    def test_get_camera_pair(self, reset_front_rear_state, camera_id):
        front_rear.camera_pairs = [
            front_rear.CameraPair(
                front=p["front"], rear=p["rear"], description=p["description"]
            )
            for p in self.pairs
        ]
        pair = front_rear._get_camera_pair(camera_id)

        assert pair is not None
        assert pair.front == "cam1"
        assert pair.rear == "cam2"

    def test_get_camera_pair_not_found(self, reset_front_rear_state):
        front_rear.camera_pairs = [
            front_rear.CameraPair(
                front=p["front"], rear=p["rear"], description=p["description"]
            )
            for p in self.pairs
        ]
        pair = front_rear._get_camera_pair("cam5")

        assert pair is None

    def test_get_camera_pair_multiple_pairs(self, reset_front_rear_state):
        front_rear.camera_pairs = [
            front_rear.CameraPair(
                front=p["front"], rear=p["rear"], description=p["description"]
            )
            for p in self.pairs
        ]
        pair = front_rear._get_camera_pair("cam3")

        assert pair is not None
        assert pair.description == "Gate 2"


class TestPlateExtraction:
    @pytest.mark.parametrize(
        "input_plate,expected", [("abc123", "ABC123"), ("  xyz789  ", "XYZ789")]
    )
    def test_extract_plate_valid_cases(
        self, reset_front_rear_state, input_plate, expected
    ):
        result = {"plate": input_plate}
        plate = front_rear._extract_plate(result)

        assert plate == expected

    @pytest.mark.parametrize(
        "result",
        [
            {},  # missing field
            {"plate": None},  # none value
            {"plate": 12345},  # invalid type
        ],
    )
    def test_extract_plate_invalid_cases(self, reset_front_rear_state, result):
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
        front_rear.csv_vehicles = {"ABC123": {"make": "TOYOTA", "model": "CAMRY"}}
        found, vehicle_info = front_rear._check_plate_in_vehicles_db("ABC123")

        assert found is True
        assert vehicle_info is not None
        assert vehicle_info["make"] == "TOYOTA"
        assert vehicle_info["model"] == "CAMRY"

    @pytest.mark.parametrize("search_plate", ["XYZ999", None])
    def test_check_plate_in_db_not_found(self, reset_front_rear_state, search_plate):
        front_rear.csv_vehicles = {"ABC123": {"make": "TOYOTA", "model": "CAMRY"}}
        found, vehicle_info = front_rear._check_plate_in_vehicles_db(search_plate)

        assert found is False
        assert vehicle_info is None

    def test_check_plate_in_db_case_insensitive(self, reset_front_rear_state):
        front_rear.csv_vehicles = {"ABC123": {"make": "TOYOTA", "model": "CAMRY"}}
        found, vehicle_info = front_rear._check_plate_in_vehicles_db("abc123")

        assert found is True
        assert vehicle_info is not None


class TestAlertSending:
    def test_send_alert_success(self, reset_front_rear_state):
        """Test that _send_alert schedules the async task (non-blocking)."""
        with patch("protocols.front_rear._loop") as mock_loop, patch(
            "protocols.front_rear._aiohttp_session"
        ), patch("protocols.front_rear.asyncio.run_coroutine_threadsafe") as mock_run:
            mock_run.side_effect = lambda coro, loop: close_coroutine(coro) or Mock()

            front_rear.config = TEST_CONFIG

            front_rear._send_alert(
                alert_type="plate_mismatch",
                visit_id=456,
                plate="ABC123",
                camera_id="camera-front",
                message="Test message",
            )

            mock_run.assert_called_once()
            assert mock_run.call_args[0][1] == mock_loop

    def test_send_alert_with_make_model(self, reset_front_rear_state):
        """Test that _send_alert works with make/model data."""
        with patch("protocols.front_rear._loop"), patch(
            "protocols.front_rear._aiohttp_session"
        ), patch("protocols.front_rear.asyncio.run_coroutine_threadsafe") as mock_run:
            mock_run.side_effect = lambda coro, loop: close_coroutine(coro) or Mock()

            front_rear.config = TEST_CONFIG

            front_rear._send_alert(
                alert_type="plate_mismatch",
                visit_id=456,
                plate="ABC123",
                camera_id="camera-front",
                message="Test message",
                detected_make_model="TOYOTA CAMRY",
                make_model_score=0.85,
            )

            mock_run.assert_called_once()

    def test_send_alert_disabled(self, reset_front_rear_state):
        """Test that disabled alerts are scheduled but return early in async function."""
        config_with_disabled = TEST_CONFIG.copy()
        config_with_disabled["alerts"] = {
            "plate_mismatch": {
                "enabled": False,
                "name": "Test Alert",
                "alert_template_id": 1,
            }
        }
        front_rear.config = config_with_disabled

        with patch("protocols.front_rear._loop"), patch(
            "protocols.front_rear._aiohttp_session"
        ), patch("protocols.front_rear.asyncio.run_coroutine_threadsafe") as mock_run:
            mock_run.side_effect = lambda coro, loop: close_coroutine(coro) or Mock()

            front_rear._send_alert(
                alert_type="plate_mismatch",
                visit_id=456,
                plate="ABC123",
                camera_id="camera-front",
                message="Test message",
            )

            mock_run.assert_called_once()


class TestWebhookProcessing:
    def test_process_request_authentication_success(
        self, reset_front_rear_state, mock_env_vars
    ):
        front_rear.config = TEST_CONFIG
        pair = front_rear.CameraPair(
            front="camera-front", rear="camera-rear", description="Gate 1"
        )
        front_rear.camera_pairs = [pair]
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
        assert pair.front_event is not None
        assert pair.front_event.camera_id == "camera-front"

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

    def test_process_request_authentication_not_configured(
        self, reset_front_rear_state, monkeypatch
    ):
        monkeypatch.delenv("STREAM_API_TOKEN", raising=False)
        webhook_data = {
            "webhook_header": {"Authorization": "any-token"},
            "data": {"camera_id": "camera-front"},
        }
        response, status = front_rear.process_request(webhook_data)

        assert status == 401
        assert "not configured" in response

    def test_process_request_authentication_malformed_header(
        self, reset_front_rear_state, mock_env_vars
    ):
        webhook_data = {
            "webhook_header": {"Authorization": "Token "},
            "data": {"camera_id": "camera-front"},
        }
        response, status = front_rear.process_request(webhook_data)

        assert status == 401
        assert "Malformed" in response

    def test_process_request_authentication_token_with_prefix(
        self, reset_front_rear_state, mock_env_vars
    ):
        front_rear.config = TEST_CONFIG
        front_rear.camera_pairs = [
            front_rear.CameraPair(
                front="camera-front", rear="camera-rear", description="Gate 1"
            )
        ]
        webhook_data = {
            "webhook_header": {"Authorization": "Token test-stream-token"},
            "data": {
                "camera_id": "camera-front",
                "results": [{"plate": "ABC123"}],
                "timestamp": "2025-11-24T10:00:00Z",
            },
        }
        _response, status = front_rear.process_request(webhook_data)

        assert status == 200

    def test_process_request_camera_not_in_pair(
        self, reset_front_rear_state, mock_env_vars
    ):
        front_rear.camera_pairs = [
            front_rear.CameraPair(
                front="camera-front", rear="camera-rear", description="Gate 1"
            )
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

    def test_process_request_buffering(self, reset_front_rear_state, mock_env_vars):
        front_rear.config = TEST_CONFIG
        pair = front_rear.CameraPair(
            front="camera-front", rear="camera-rear", description="Gate 1"
        )
        front_rear.camera_pairs = [pair]
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
        assert pair.front_event is not None

    @patch("protocols.front_rear._process_camera_pair")
    def test_process_request_pair_processing(
        self,
        mock_process_pair,
        reset_front_rear_state,
        mock_env_vars,
        create_camera_event,
    ):
        front_rear.config = TEST_CONFIG
        pair = front_rear.CameraPair(
            front="camera-front", rear="camera-rear", description="Gate 1"
        )
        front_rear.camera_pairs = [pair]
        current_time = time.time()
        pair.front_event = create_camera_event(
            timestamp="2024-11-24T10:00:00Z", timestamp_unix=current_time
        )

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

    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._process_camera_pair")
    @patch("protocols.front_rear._send_alert")
    def test_process_request_overwrite_unpaired_event(
        self,
        mock_send_alert,
        mock_process_pair,
        mock_forward,
        reset_front_rear_state,
        mock_env_vars,
        create_camera_event,
        mock_asyncio_for_alerts,
    ):
        """Test that overwriting an unpaired event processes it before replacement."""
        mock_forward.return_value = 123
        with patch(
            "protocols.front_rear._process_events", return_value=123
        ) as mock_process_events:
            front_rear.config = TEST_CONFIG
            pair = front_rear.CameraPair(
                front="camera-front", rear="camera-rear", description="Gate 1"
            )
            front_rear.camera_pairs = [pair]
            old_time = time.time() - 20
            pair.front_event = create_camera_event(
                plate="OLD123",
                timestamp="2024-11-24T10:00:00Z",
                timestamp_unix=old_time,
            )

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
            mock_process_events.assert_called_once()
            alert_types = [
                call[1]["alert_type"] for call in mock_send_alert.call_args_list
            ]
            assert "camera_offline" in alert_types
            if mock_send_alert.call_args_list:
                for call in mock_send_alert.call_args_list:
                    assert call[1]["visit_id"] == 123

    @patch("protocols.front_rear._process_camera_pair")
    @patch("protocols.front_rear._send_alert")
    def test_process_request_same_plate_update_no_overwrite_alert(
        self,
        mock_send_alert,
        mock_process_pair,
        reset_front_rear_state,
        mock_env_vars,
        create_camera_event,
        mock_asyncio_for_alerts,
    ):
        """Test that updating with same plate does not trigger overwrite alert."""
        front_rear.config = TEST_CONFIG
        pair = front_rear.CameraPair(
            front="camera-front", rear="camera-rear", description="Gate 1"
        )
        front_rear.camera_pairs = [pair]
        old_time = time.time() - 5
        pair.front_event = create_camera_event(
            plate="ABC123", timestamp="2024-11-24T10:00:00Z", timestamp_unix=old_time
        )

        webhook_data = {
            "webhook_header": {"Authorization": "test-stream-token"},
            "data": {
                "camera_id": "camera-front",
                "results": [{"plate": "ABC123"}],
                "timestamp": "2024-11-24T10:00:05Z",
            },
        }
        response, status = front_rear.process_request(webhook_data)

        assert status == 200
        mock_process_pair.assert_not_called()
        mock_send_alert.assert_not_called()
        assert pair.front_event is not None


class TestCameraPairProcessing:
    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_plate_not_in_db(
        self,
        mock_send_alert,
        mock_forward,
        reset_front_rear_state,
        create_camera_event,
        mock_asyncio_for_alerts,
    ):
        mock_forward.return_value = 123
        front_rear.csv_vehicles = {}
        front_rear.config = TEST_CONFIG
        front_event = create_camera_event(camera_id="camera-front", plate="UNKNOWN123")
        rear_event = create_camera_event(
            camera_id="camera-rear",
            plate="UNKNOWN123",
            timestamp="2025-11-24T10:00:05Z",
        )
        pair = front_rear.CameraPair(
            front="camera-front",
            rear="camera-rear",
            description="Gate 1",
            front_event=front_event,
            rear_event=rear_event,
        )
        front_rear._process_camera_pair(pair)

        mock_forward.assert_called_once()
        assert mock_send_alert.call_count >= 2
        for call in mock_send_alert.call_args_list:
            assert call[1]["visit_id"] == 123
        alert_calls = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "plate_mismatch" in alert_calls

    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_no_rear_plate(
        self,
        mock_send_alert,
        mock_forward,
        reset_front_rear_state,
        create_camera_event,
        mock_asyncio_for_alerts,
    ):
        mock_forward.return_value = 123
        front_rear.config = TEST_CONFIG
        front_event = create_camera_event()
        rear_event = create_camera_event(
            camera_id="camera-rear", plate=None, timestamp="2025-11-24T10:00:05Z"
        )
        pair = front_rear.CameraPair(
            front="camera-front",
            rear="camera-rear",
            description="Gate 1",
            front_event=front_event,
            rear_event=rear_event,
        )
        front_rear._process_camera_pair(pair)

        mock_forward.assert_called_once()
        alert_calls = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "no_rear_plate" in alert_calls
        for call in mock_send_alert.call_args_list:
            assert call[1]["visit_id"] == 123

    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_make_model_mismatch(
        self,
        mock_send_alert,
        mock_forward,
        reset_front_rear_state,
        create_camera_event,
        mock_asyncio_for_alerts,
    ):
        mock_forward.return_value = 123
        front_rear.csv_vehicles = {"ABC123": {"make": "TOYOTA", "model": "CAMRY"}}
        front_rear.config = TEST_CONFIG
        front_event = create_camera_event(
            model_make=[{"make": "HONDA", "model": "ACCORD", "score": 0.85}]
        )
        rear_event = create_camera_event(
            camera_id="camera-rear", timestamp="2025-11-24T10:00:05Z"
        )
        pair = front_rear.CameraPair(
            front="camera-front",
            rear="camera-rear",
            description="Gate 1",
            front_event=front_event,
            rear_event=rear_event,
        )
        front_rear._process_camera_pair(pair)

        mock_forward.assert_called_once()
        alert_calls = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "make_model_mismatch" in alert_calls
        for call in mock_send_alert.call_args_list:
            assert call[1]["visit_id"] == 123

    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_forwards_rear_data(
        self,
        mock_send_alert,
        mock_forward,
        reset_front_rear_state,
        create_camera_event,
        mock_asyncio_for_alerts,
    ):
        mock_forward.return_value = 123
        front_rear.csv_vehicles = {"ABC123": {"make": "TOYOTA", "model": "CAMRY"}}
        front_rear.config = TEST_CONFIG
        front_event = create_camera_event()
        rear_event = create_camera_event(
            camera_id="camera-rear",
            timestamp="2025-11-24T10:00:05Z",
            original_json_data={"test": "rear_data"},
        )
        pair = front_rear.CameraPair(
            front="camera-front",
            rear="camera-rear",
            description="Gate 1",
            front_event=front_event,
            rear_event=rear_event,
        )
        front_rear._process_camera_pair(pair)

        mock_forward.assert_called_once()
        call_args = mock_forward.call_args[0]
        assert call_args[0].original_json_data == {"test": "rear_data"}

    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_forwards_front_data_when_rear_unavailable(
        self,
        mock_send_alert,
        mock_forward,
        reset_front_rear_state,
        create_camera_event,
        mock_asyncio_for_alerts,
    ):
        """Test that front camera data is forwarded when rear camera is unavailable."""
        mock_forward.return_value = 123
        front_rear.csv_vehicles = {"ABC123": {"make": "TOYOTA", "model": "CAMRY"}}
        front_rear.config = TEST_CONFIG
        front_event = create_camera_event(original_json_data={"test": "front_data"})
        pair = front_rear.CameraPair(
            front="camera-front",
            rear="camera-rear",
            description="Gate 1",
            front_event=front_event,
            rear_event=None,
        )
        front_rear._process_camera_pair(pair)

        mock_forward.assert_called_once()
        call_args = mock_forward.call_args[0]
        assert call_args[0].original_json_data == {"test": "front_data"}

    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_single_front_camera_validates_db(
        self,
        mock_send_alert,
        mock_forward,
        reset_front_rear_state,
        create_camera_event,
        mock_asyncio_for_alerts,
    ):
        mock_forward.return_value = 123
        front_rear.csv_vehicles = {}
        front_rear.config = TEST_CONFIG
        front_event = create_camera_event(
            plate="UNKNOWN123", original_json_data={"test": "front_data"}
        )
        pair = front_rear.CameraPair(
            front="camera-front",
            rear="camera-rear",
            description="Gate 1",
            front_event=front_event,
            rear_event=None,
        )
        front_rear._process_camera_pair(pair)

        alert_types = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "no_rear_plate" not in alert_types
        assert "plate_mismatch" in alert_types
        mock_forward.assert_called_once()
        for call in mock_send_alert.call_args_list:
            assert call[1]["visit_id"] == 123

    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_single_rear_camera_validates_db(
        self,
        mock_send_alert,
        mock_forward,
        reset_front_rear_state,
        create_camera_event,
        mock_asyncio_for_alerts,
    ):
        """Test that single rear camera event validates against database."""
        mock_forward.return_value = 123
        front_rear.csv_vehicles = {}
        front_rear.config = TEST_CONFIG
        rear_event = create_camera_event(
            camera_id="camera-rear",
            plate="UNKNOWN123",
            timestamp="2025-11-24T10:00:05Z",
            original_json_data={"test": "rear_data"},
        )
        pair = front_rear.CameraPair(
            front="camera-front",
            rear="camera-rear",
            description="Gate 1",
            front_event=None,
            rear_event=rear_event,
        )
        front_rear._process_camera_pair(pair)

        alert_types = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "plate_mismatch" in alert_types

        mock_forward.assert_called_once()
        call_args = mock_forward.call_args[0]
        assert call_args[0].original_json_data == {"test": "rear_data"}
        for call in mock_send_alert.call_args_list:
            assert call[1]["visit_id"] == 123

    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_pair_rear_camera_online_no_plate(
        self,
        mock_send_alert,
        mock_forward,
        reset_front_rear_state,
        create_camera_event,
        mock_asyncio_for_alerts,
    ):
        """Test that no_rear_plate alert is sent when rear camera is online but detects no plate."""
        mock_forward.return_value = 123
        front_rear.csv_vehicles = {"ABC123": {"make": "TOYOTA", "model": "CAMRY"}}
        front_rear.config = TEST_CONFIG
        front_event = create_camera_event()
        rear_event = create_camera_event(
            camera_id="camera-rear",
            plate=None,
            timestamp="2025-11-24T10:00:05Z",
            original_json_data={"test": "rear_data"},
        )
        pair = front_rear.CameraPair(
            front="camera-front",
            rear="camera-rear",
            description="Gate 1",
            front_event=front_event,
            rear_event=rear_event,
        )
        front_rear._process_camera_pair(pair)

        mock_forward.assert_called_once()
        alert_types = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "no_rear_plate" in alert_types
        for call in mock_send_alert.call_args_list:
            assert call[1]["visit_id"] == 123


class TestCleanupExpiredEvents:
    @patch("protocols.front_rear._load_vehicles_csv")
    @patch("protocols.front_rear._load_config")
    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._process_camera_pair")
    @patch("protocols.front_rear._send_alert")
    def test_cleanup_processes_expired_events(
        self,
        mock_send_alert,
        mock_process_pair,
        mock_forward,
        mock_load_config,
        mock_load_csv,
        reset_front_rear_state,
        create_camera_event,
        mock_asyncio_for_alerts,
    ):
        mock_forward.return_value = 123
        mock_process_pair.return_value = 123
        mock_load_config.return_value = TEST_CONFIG
        front_rear.config = TEST_CONFIG
        old_pair = front_rear.CameraPair(
            front="camera-old", rear="camera-old-rear", description="Gate 1"
        )
        new_pair = front_rear.CameraPair(
            front="camera-new", rear="camera-new-rear", description="Gate 2"
        )
        front_rear.camera_pairs = [old_pair, new_pair]

        old_pair.front_event = create_camera_event(
            camera_id="camera-old", timestamp_unix=time.time() - 100
        )
        new_pair.front_event = create_camera_event(
            camera_id="camera-new", plate="XYZ789", timestamp_unix=time.time() - 10
        )
        front_rear._cleanup_expired_events()

        mock_process_pair.assert_called_once()
        alert_types = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        assert "camera_offline" in alert_types
        if mock_send_alert.call_args_list:
            for call in mock_send_alert.call_args_list:
                assert call[1]["visit_id"] == 123
        assert old_pair.front_event is None
        assert new_pair.front_event is not None


class TestInitialization:
    @patch("protocols.front_rear.asyncio.run_coroutine_threadsafe")
    @patch("protocols.front_rear.threading.Thread")
    def test_initialize(
        self,
        mock_thread,
        mock_run_coro,
        reset_front_rear_state,
        sample_config,
        monkeypatch,
    ):
        """Test initialization with mocked asyncio components."""
        monkeypatch.chdir(Path(sample_config).parent.parent.parent)

        mock_future = Mock()
        mock_session = Mock()
        mock_future.result.return_value = mock_session

        def mock_run_side_effect(coro, loop):
            close_coroutine(coro)
            return mock_future

        mock_run_coro.side_effect = mock_run_side_effect

        front_rear.initialize()

        assert len(front_rear.csv_vehicles) > 0
        assert len(front_rear.camera_pairs) > 0
        assert mock_thread.call_count == 2
        for call in mock_thread.call_args_list:
            assert call[1]["daemon"] is True

        assert front_rear._aiohttp_session == mock_session


class TestSoloCameras:
    """Test solo camera functionality (front-only or rear-only)."""

    @pytest.mark.parametrize(
        "front,rear,expected_camera_id,expected_id",
        [
            ("cam1", None, "cam1", "solo:cam1"),  # Front only
            (None, "cam2", "cam2", "solo:cam2"),  # Rear only
            ("cam1", "", "cam1", "solo:cam1"),  # Empty rear string
            ("", "cam2", "cam2", "solo:cam2"),  # Empty front string
        ],
    )
    def test_solo_camera_properties(
        self, reset_front_rear_state, front, rear, expected_camera_id, expected_id
    ):
        """Test solo camera properties for different configurations."""
        pair = front_rear.CameraPair(front=front, rear=rear, description="Solo")
        assert pair.is_solo is True
        assert pair.solo_camera_id == expected_camera_id
        assert pair.id == expected_id

    def test_paired_camera_not_solo(self, reset_front_rear_state):
        """Test paired camera is not solo."""
        pair = front_rear.CameraPair(front="cam1", rear="cam2", description="Paired")
        assert pair.is_solo is False
        assert pair.solo_camera_id is None
        assert pair.id == "cam1:cam2"

    @pytest.mark.parametrize(
        "front,rear,camera_id",
        [
            ("solo-front", None, "solo-front"),  # Front only
            (None, "solo-rear", "solo-rear"),  # Rear only
        ],
    )
    def test_get_camera_pair_solo(self, reset_front_rear_state, front, rear, camera_id):
        """Test finding solo cameras in either position."""
        front_rear.camera_pairs = [
            front_rear.CameraPair(front=front, rear=rear, description="Solo")
        ]
        pair = front_rear._get_camera_pair(camera_id)
        assert pair is not None
        assert pair.is_solo is True

    @pytest.mark.parametrize(
        "front,rear,camera_id,plate,visit_id,should_have_plate_in_db,expected_plate_mismatch",
        [
            ("solo-front", None, "solo-front", "SOLO123", 456, False, True),
            (None, "solo-rear", "solo-rear", "REAR456", 789, True, False),
        ],
    )
    @patch("protocols.front_rear._forward_to_parkpow")
    @patch("protocols.front_rear._send_alert")
    def test_process_solo_camera_immediate(
        self,
        mock_send_alert,
        mock_forward,
        reset_front_rear_state,
        mock_env_vars,
        create_camera_event,
        mock_asyncio_for_alerts,
        front,
        rear,
        camera_id,
        plate,
        visit_id,
        should_have_plate_in_db,
        expected_plate_mismatch,
    ):
        """Test solo cameras process immediately without waiting for pairing."""
        mock_forward.return_value = visit_id

        if should_have_plate_in_db:
            front_rear.csv_vehicles = {plate: {"make": "TOYOTA", "model": "CAMRY"}}
        else:
            front_rear.csv_vehicles = {}

        front_rear.config = TEST_CONFIG
        pair = front_rear.CameraPair(front=front, rear=rear, description="Solo")
        front_rear.camera_pairs = [pair]

        webhook_data = {
            "webhook_header": {"Authorization": "test-stream-token"},
            "data": {
                "camera_id": camera_id,
                "results": [{"plate": plate}],
                "timestamp": "2024-11-24T10:00:00Z",
            },
        }

        response, status = front_rear.process_request(webhook_data)

        assert status == 200
        assert "Processed" in response
        mock_forward.assert_called_once()

        alert_types = [call[1]["alert_type"] for call in mock_send_alert.call_args_list]
        if expected_plate_mismatch:
            assert "plate_mismatch" in alert_types
        else:
            assert "plate_mismatch" not in alert_types

    @patch("protocols.front_rear._forward_to_parkpow")
    def test_solo_camera_no_rear_plate_alert(
        self,
        mock_forward,
        reset_front_rear_state,
        mock_env_vars,
        create_camera_event,
        mock_asyncio_for_alerts,
    ):
        """Test solo camera does not trigger no_rear_plate alert."""
        mock_forward.return_value = 999
        front_rear.csv_vehicles = {}
        front_rear.config = TEST_CONFIG
        pair = front_rear.CameraPair(front="solo-cam", rear=None, description="Solo")
        front_rear.camera_pairs = [pair]

        with patch("protocols.front_rear._send_alert") as mock_alert:
            webhook_data = {
                "webhook_header": {"Authorization": "test-stream-token"},
                "data": {
                    "camera_id": "solo-cam",
                    "results": [{"plate": "TEST123"}],
                    "timestamp": "2024-11-24T10:00:00Z",
                },
            }

            front_rear.process_request(webhook_data)

            alert_types = [call[1]["alert_type"] for call in mock_alert.call_args_list]
            assert "no_rear_plate" not in alert_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
