# common_webhook_consumer.py
import atexit
import importlib
import json
import logging
import os
import signal
import sys
from typing import Any

from flask import Flask, jsonify, request
from waitress import serve  # type: ignore

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)

middleware: Any | None = None


def cleanup_middleware():
    """Cleanup middleware resources on shutdown."""
    global middleware
    if middleware and hasattr(middleware, "shutdown"):
        logging.info("Shutting down middleware...")
        try:
            middleware.shutdown()
        except Exception as e:
            logging.error(f"Error during middleware shutdown: {e}")


def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    logging.info(f"Received signal {signum}, initiating graceful shutdown...")
    cleanup_middleware()
    sys.exit(0)


def load_middleware():
    middleware_name = os.getenv("MIDDLEWARE_NAME")
    if not middleware_name:
        logging.error("MIDDLEWARE_NAME environment variable is not set.")
        return None

    try:
        middleware = importlib.import_module(f"protocols.{middleware_name}")
        logging.info(f"Using middleware: {middleware_name}")

        if hasattr(middleware, "initialize"):
            middleware.initialize()

        return middleware
    except ModuleNotFoundError:
        logging.error(f"Middleware '{middleware_name}' not found.")
        return None


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for load balancers and monitoring (front_rear only)."""
    middleware_name = os.getenv("MIDDLEWARE_NAME")
    if middleware_name != "front_rear":
        return jsonify({"error": "Not found"}), 404

    global middleware
    if not middleware:
        return jsonify({"status": "unhealthy", "reason": "Middleware not loaded"}), 503
    return jsonify({"status": "healthy", "middleware": middleware_name}), 200


@app.route("/", methods=["POST"])
def handle_webhook():
    global middleware
    if not middleware:
        return jsonify({"error": "Middleware not found"}), 500

    if request.content_type.startswith("multipart/form-data"):
        json_data = request.form.get("json")
        if json_data:
            json_data = json.loads(json_data)
        else:
            return jsonify({"error": "Missing JSON data in multipart form"}), 400

        uploaded_files = request.files
    else:
        try:
            if request.content_type == "application/json":
                json_data = request.get_json()
            else:  # For application/x-www-form-urlencoded
                raw_data = request.form.get("json")
                if raw_data:
                    json_data = json.loads(raw_data)
                else:
                    return jsonify({"error": "Missing JSON data"}), 400
            uploaded_files = {}
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 400

    try:
        webhook_header = {
            "mac_address": request.headers.get("mac-address"),
            "camera_name": request.headers.get("camera-name"),
            "serial_number": request.headers.get("serial-number"),
            "camera_id": request.headers.get("camera-id"),
            "Authorization": request.headers.get("Authorization"),
        }

        webhook_header = {k: v for k, v in webhook_header.items() if v is not None}

        if webhook_header and isinstance(json_data, dict):
            json_data["webhook_header"] = webhook_header

        files = {}
        for file in uploaded_files:
            files[file] = uploaded_files[file].read()
        response, status_code = middleware.process_request(json_data, files)
        return jsonify({"message": response}), status_code
    except Exception as e:
        logging.error(f"Error processing the request: {e}")
        return jsonify({"error": "Error processing the request"}), 500


if __name__ == "__main__":
    middleware = load_middleware()

    if not middleware:
        logging.error("Failed to load middleware. Exiting..")
        exit(1)

    atexit.register(cleanup_middleware)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        serve(app, host="0.0.0.0", port=8002)
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
    finally:
        cleanup_middleware()
