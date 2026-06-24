"""FTP server that forwards Hikvision ANPR snapshots to the Plate Recognizer Snapshot Cloud API.

Hikvision cameras configured to upload on ANPR detection typically send three files per
event: a full-frame image ending in ``VEHICLE_DETECTION.jpg``, a cropped plate image
ending in ``VEHICLE_DETECTION_PLATE.jpg``, and an ``anpr.xml`` metadata file. Only the
matching images (default suffix: ``VEHICLE_DETECTION.jpg``) are forwarded to the Snapshot
Cloud API. All received files are kept on disk by default.

Configuration is done via environment variables (see ``main`` for the full list).
"""

from __future__ import annotations

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from dotenv import load_dotenv
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer

SNAPSHOT_URL = "https://api.platerecognizer.com/v1/plate-reader/"

log = logging.getLogger("ftp-to-snapshot")
session = requests.Session()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _env_str(name: str, default: str) -> str:
    raw = os.environ.get(name)
    return default if raw is None else raw


def forward_to_snapshot(
    file_path: Path,
    *,
    token: str,
    regions: list[str] | None,
    camera_id: str | None,
    mmc: bool,
    config: dict | None,
    timeout: float,
) -> None:
    """Upload ``file_path`` to the Snapshot Cloud plate-reader endpoint."""
    headers = {"Authorization": f"Token {token}"}
    data: dict = {}
    if regions:
        data["regions"] = regions
    if camera_id:
        data["camera_id"] = camera_id
    if mmc:
        data["mmc"] = "true"
    if config:
        data["config"] = json.dumps(config)

    try:
        with file_path.open("rb") as fp:
            files = {"upload": (file_path.name, fp, "image/jpeg")}
            response = session.post(
                SNAPSHOT_URL,
                headers=headers,
                data=data,
                files=files,
                timeout=timeout,
            )
    except requests.RequestException as exc:
        log.error("Snapshot API request failed for %s: %s", file_path.name, exc)
        return

    if response.ok:
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        log.info("Snapshot OK %s -> %s", file_path.name, payload)
    else:
        log.warning(
            "Snapshot API error %s for %s: %s",
            response.status_code,
            file_path.name,
            response.text,
        )


class SnapshotFTPHandler(FTPHandler):
    """FTPHandler that forwards matching uploads to the Snapshot Cloud API."""

    # Set by main() before the server starts.
    api_token: str
    match_suffix: str
    keep_non_matching: bool
    regions: list[str]
    camera_id: str | None
    mmc: bool
    config: dict | None
    request_timeout: float
    _executor: ThreadPoolExecutor

    def on_file_received(self, file: str) -> None:
        path = Path(file)
        name = path.name
        if name.endswith(self.match_suffix):
            log.info("Forwarding %s to Snapshot Cloud", name)
            try:
                self._executor.submit(
                    forward_to_snapshot,
                    path,
                    token=self.api_token,
                    regions=self.regions or None,
                    camera_id=self.camera_id or None,
                    mmc=self.mmc,
                    config=self.config,
                    timeout=self.request_timeout,
                )
            except RuntimeError as exc:
                log.error("Could not schedule Snapshot upload for %s: %s", name, exc)
        else:
            log.info("Ignoring non-matching upload: %s", name)
            if not self.keep_non_matching:
                try:
                    path.unlink()
                except OSError as exc:
                    log.warning("Failed to remove %s: %s", name, exc)


def main() -> None:
    load_dotenv()

    logging.basicConfig(
        level=_env_str("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    host = _env_str("FTP_HOST", "")
    port = _env_int("FTP_PORT", 2121)
    user = _env_str("FTP_USER", "camera")
    password = _env_str("FTP_PASSWORD", "camera")
    root = Path(_env_str("FTP_ROOT", "./uploads")).resolve()
    root.mkdir(parents=True, exist_ok=True)

    passive_range_raw = _env_str("FTP_PASSIVE_PORTS", "50000-50100")
    try:
        pstart, pend = (int(x) for x in passive_range_raw.split("-", 1))
    except ValueError as exc:
        raise RuntimeError(
            f"FTP_PASSIVE_PORTS must be in the form START-END, got {passive_range_raw!r}"
        ) from exc
    if not (0 < pstart < pend <= 65535):
        raise RuntimeError(
            f"FTP_PASSIVE_PORTS out of range: {passive_range_raw!r}"
        )
    masquerade_address = _env_str("FTP_MASQUERADE_ADDRESS", "") or None

    token = _env_str("PLATE_RECOGNIZER_TOKEN", "")
    if not token:
        raise RuntimeError("PLATE_RECOGNIZER_TOKEN environment variable is required")

    match_suffix = _env_str("MATCH_SUFFIX", "VEHICLE_DETECTION.jpg")
    keep_non_matching = _env_bool("KEEP_NON_MATCHING", True)
    regions = [
        r.strip() for r in _env_str("REGIONS", "").split(",") if r.strip()
    ]
    camera_id = _env_str("CAMERA_ID", "") or None
    mmc = _env_bool("MMC", False)
    config_raw = _env_str("CONFIG_JSON", "")
    config = json.loads(config_raw) if config_raw.strip() else None
    request_timeout = float(_env_str("REQUEST_TIMEOUT", "30"))
    max_workers = _env_int("MAX_WORKERS", 4)

    authorizer = DummyAuthorizer()
    authorizer.add_user(user, password, str(root), perm="elradfmwMT")

    SnapshotFTPHandler.authorizer = authorizer
    SnapshotFTPHandler.api_token = token
    SnapshotFTPHandler.match_suffix = match_suffix
    SnapshotFTPHandler.keep_non_matching = keep_non_matching
    SnapshotFTPHandler.regions = regions
    SnapshotFTPHandler.camera_id = camera_id
    SnapshotFTPHandler.mmc = mmc
    SnapshotFTPHandler.config = config
    SnapshotFTPHandler.request_timeout = request_timeout
    SnapshotFTPHandler.banner = "Hikvision -> Snapshot Cloud bridge ready."
    SnapshotFTPHandler.passive_ports = range(pstart, pend + 1)
    if masquerade_address:
        SnapshotFTPHandler.masquerade_address = masquerade_address
    SnapshotFTPHandler._executor = ThreadPoolExecutor(
        max_workers=max_workers, thread_name_prefix="snapshot"
    )

    address = (host, port)
    server = ThreadedFTPServer(address, SnapshotFTPHandler)
    server.max_cons = _env_int("FTP_MAX_CONS", 64)
    server.max_cons_per_ip = _env_int("FTP_MAX_CONS_PER_IP", 8)

    log.info(
        "Starting FTP server on %s:%d (root=%s, match_suffix=%s, regions=%s, mmc=%s, "
        "passive_ports=%d-%d, masquerade=%s)",
        host or "0.0.0.0",
        port,
        root,
        match_suffix,
        regions or None,
        mmc,
        pstart,
        pend,
        masquerade_address,
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down")
    finally:
        server.close_all()
        SnapshotFTPHandler._executor.shutdown(wait=True)


if __name__ == "__main__":
    main()
