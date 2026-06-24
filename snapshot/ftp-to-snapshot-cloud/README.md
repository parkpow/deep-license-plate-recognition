# FTP to Snapshot Cloud Bridge

A small, self-contained FTP server that receives snapshot uploads from
[Hikvision](https://www.hikvision.com/) ANPR/LPR cameras and forwards the matching
images to the [Plate Recognizer Snapshot](https://platerecognizer.com/snapshot/)
plate-reader API (`/v1/plate-reader/`).

The bridge supports **both** Snapshot Cloud and the **on-premise Snapshot SDK**:

* **Cloud** (default) — uploads to
  `https://api.platerecognizer.com/v1/plate-reader/` and authenticates with an
  API token (`PLATE_RECOGNIZER_TOKEN`, **required**).
* **SDK** — set `USE_SDK=true` to upload to
  `http://localhost:8080/v1/plate-reader/` (or your own URL via
  `SNAPSHOT_URL`). No token is required.

When a Hikvision camera is configured to upload on ANPR detection, it typically
sends three files per event:

| File                              | Purpose                                 |
| --------------------------------- | --------------------------------------- |
| `...VEHICLE_DETECTION.jpg`        | Full-frame image of the detected vehicle |
| `...VEHICLE_DETECTION_PLATE.jpg`  | Cropped close-up of the license plate    |
| `anpr.xml`                        | ANPR event metadata                      |

By default the bridge forwards only the full-frame image
(`VEHICLE_DETECTION.jpg`) to the Snapshot endpoint and ignores the cropped plate
image and the XML. Received files are kept on disk under the configured upload
root.

---

## Table of contents

1. [How it works](#how-it-works)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Network / firewall notes](#network--firewall-notes)
6. [Running the server](#running-the-server)
7. [Configuring the Hikvision camera](#configuring-the-hikvision-camera)
8. [Operation guide](#operation-guide)
9. [Logs and troubleshooting](#logs-and-troubleshooting)
10. [Project layout](#project-layout)

---

## How it works

```
+--------------------+   FTP upload   +-------------------------+   HTTP(S) POST  +-------------------------+
|  Hikvision camera   |  ----------->  |  ftp-to-snapshot-cloud  |  ------------>  |  Snapshot Cloud or SDK |
|  (ANPR triggers)    |  data + ports  |  (pyftpdlib)            |  /plate-reader/ |  (Plate Recognizer)    |
+--------------------+                +-------------------------+                 +-------------------------+
                                                |
                                                v
                                       ./uploads/  (local disk)
```

* `pyftpdlib` accepts FTP uploads from the camera on the configured port.
* The handler inspects each received filename:
  * Files whose name **ends with** the configured `MATCH_SUFFIX`
    (default: `VEHICLE_DETECTION.jpg`) are uploaded to the Snapshot Cloud
    plate-reader endpoint in a background thread.
  * Empty matching files are skipped.
  * Non-matching files are either kept on disk (`KEEP_NON_MATCHING=true`, the
    default) or deleted after receipt.
* A small `ThreadPoolExecutor` is used to forward files concurrently, so FTP
  STOR commands are not blocked on the HTTP upload.

---

## Snapshot Cloud vs Snapshot SDK

The bridge can forward to either Snapshot backend:

| Backend            | When to use                                                | Default URL                                            | `PLATE_RECOGNIZER_TOKEN` |
| ------------------ | ---------------------------------------------------------- | ------------------------------------------------------ | ------------------------ |
| **Snapshot Cloud** | Managed service. Just need an API token.                   | `https://api.platerecognizer.com/v1/plate-reader/`     | **Required** |
| **Snapshot SDK**   | Self-hosted on-premise. No outbound traffic to PR.         | `http://localhost:8080/v1/plate-reader/`               | _Not required_ |

Switch with `USE_SDK`:

* `USE_SDK=false` (default) → Cloud mode. `PLATE_RECOGNIZER_TOKEN` is
  **required**; the URL defaults to the Cloud endpoint.
* `USE_SDK=true` → SDK mode. `PLATE_RECOGNIZER_TOKEN` is **not required**;
  the URL defaults to the local SDK endpoint.

Override the URL with `SNAPSHOT_URL`. This is useful when the SDK runs on a
different host/port, behind a reverse proxy, or when you want to forward to
the [Plate Recognizer webhook receiver](https://guides.platerecognizer.com/docs/snapshot/results/).

Resolution order at startup:

1. If `SNAPSHOT_URL` is set → use it.
2. Else if `USE_SDK=true` → use `http://localhost:8080/v1/plate-reader/`.
3. Else → use `https://api.platerecognizer.com/v1/plate-reader/` (Cloud).

Validation:

* `USE_SDK=false` and no token → exits with
  `PLATE_RECOGNIZER_TOKEN environment variable is required when USE_SDK is not set`.
* `USE_SDK=true` → starts fine regardless of token; the token is simply not
  sent as an `Authorization` header.

---

## Requirements

* **Python 3.13 or newer** (declared in `pyproject.toml`).
* Either **[uv](https://docs.astral.sh/uv/)** (recommended, a `uv.lock` is
  shipped) or **pip** + a virtual environment.
* Network access to your target Snapshot endpoint:
  * **Cloud** — outbound HTTPS to `api.platerecognizer.com`.
  * **SDK** — outbound HTTP to the host where the SDK is running (default
    `localhost:8080`; override with `SNAPSHOT_URL`).
* Inbound FTP access from the camera. See
  [Network / firewall notes](#network--firewall-notes) — **passive ports must be
  reachable**, not just the control port.
* For Cloud mode only: a Plate Recognizer API token with the Snapshot Cloud
  feature enabled
  (<https://app.platerecognizer.com/service/snapshot-cloud/>). Not required
  for SDK mode.

Python dependencies (installed automatically):

* `pyftpdlib` — FTP server.
* `python-dotenv` — loads the `.env` file.
* `requests` — HTTPS client for the Snapshot Cloud API.

---

## Installation

### Option A — `uv` (recommended)

```bash
cd snapshot/ftp-to-snapshot-cloud
uv sync                # creates .venv/ and installs locked deps
cp .env.example .env   # then edit .env (see Configuration)
```

### Option B — `pip` + venv

```bash
cd snapshot/ftp-to-snapshot-cloud
python3.13 -m venv .venv
source .venv/bin/activate
pip install pyftpdlib "python-dotenv>=1.2.2" requests
cp .env.example .env   # then edit .env (see Configuration)
```

### Verify the install

```bash
python main.py --help     # main.py has no CLI flags; you should see no error
                          # and a "Starting FTP server on ..." log line.
```

> The project uses `python-dotenv` to load environment variables from a `.env`
> file in the working directory automatically. You can skip `cp .env.example
> .env` and export the variables in your shell instead, but a `.env` file is the
> easiest path.

---

## Configuration

All configuration is done via environment variables (loaded from `.env` if
present). The table below lists every variable, its default, and what it does.

### Snapshot endpoint

| Variable                | Required        | Default               | Description                                                                                              |
| ----------------------- | --------------- | --------------------- | -------------------------------------------------------------------------------------------------------- |
| `USE_SDK`               | No              | `false`               | When `true`, the bridge forwards to the on-premise Snapshot SDK and does **not** require an API token.   |
| `SNAPSHOT_URL`          | No              | Cloud or SDK default  | Full `plate-reader` URL. Overrides the `USE_SDK`-driven default. Use to point at a custom SDK host/port or the Plate Recognizer webhook receiver. |
| `PLATE_RECOGNIZER_TOKEN` | When `USE_SDK=false` | —               | API token from <https://app.platerecognizer.com/service/snapshot-cloud/>. Sent as `Authorization: Token …`. Ignored in SDK mode. |
| `REGIONS`               | No              | _(empty)_             | Comma-separated region codes forwarded as the `regions` parameter, e.g. `mx,us-ca`.                      |
| `CAMERA_ID`             | No              | _(empty)_             | Optional camera identifier forwarded as `camera_id`.                                                     |
| `MMC`                   | No              | `false`               | When `true`, forwards `mmc=true` to enable make/model/color (requires the feature on your account).     |
| `CONFIG_JSON`           | No              | _(empty)_             | Raw JSON string for engine config, e.g. `{"mode":"fast","threshold_d":0.2}`.                             |

Defaults:

* `USE_SDK=false` → `SNAPSHOT_URL=https://api.platerecognizer.com/v1/plate-reader/`
* `USE_SDK=true`  → `SNAPSHOT_URL=http://localhost:8080/v1/plate-reader/`

### FTP server

| Variable             | Default     | Description                                                                                                          |
| -------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------- |
| `FTP_HOST`           | `""`        | Interface to bind. Leave empty (or set `0.0.0.0`) to listen on all interfaces.                                      |
| `FTP_PORT`           | `2121`      | Control-channel port. Open this in your firewall.                                                                    |
| `FTP_USER`           | `camera`    | FTP username.                                                                                                        |
| `FTP_PASSWORD`       | `camera`    | FTP password. **Change this** before pointing a camera at the server.                                                |
| `FTP_ROOT`           | `./uploads` | Local directory where received files are stored. Created on startup.                                                 |
| `FTP_MAX_CONS`       | `64`        | Maximum concurrent FTP connections to the server.                                                                    |
| `FTP_MAX_CONS_PER_IP`| `8`         | Maximum concurrent connections from a single IP.                                                                     |
| `FTP_PASSIVE_PORTS`  | `50000-50100` | **Passive-mode data-channel port range** — see [Network / firewall notes](#network--firewall-notes). |
| `FTP_MASQUERADE_ADDRESS` | _(empty)_ | Public IP the server advertises in the `PASV` reply. Set this if the server is behind NAT.                         |

### Upload filtering

| Variable            | Default                 | Description                                                                                                                            |
| ------------------- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `MATCH_SUFFIX`      | `VEHICLE_DETECTION.jpg` | Only files whose **name ends with** this suffix are forwarded to Snapshot Cloud.                                                       |
| `KEEP_NON_MATCHING` | `true`                  | If `false`, files that don't match `MATCH_SUFFIX` are deleted after receipt (use `false` for storage-constrained deployments).       |

### Misc

| Variable         | Default | Description                                                                 |
| ---------------- | ------- | --------------------------------------------------------------------------- |
| `LOG_LEVEL`      | `INFO`  | Standard Python log level (`DEBUG`, `INFO`, `WARNING`, …).                  |
| `REQUEST_TIMEOUT`| `30`    | Seconds to wait for the Snapshot Cloud HTTP response.                       |
| `MAX_WORKERS`    | `4`     | Size of the thread pool that forwards matching files to Snapshot Cloud.     |

Boolean values accept any of `1`, `true`, `yes`, `on` (case-insensitive).

---

## Network / firewall notes

> **IMPORTANT — passive-mode data ports.**
>
> FTP in **passive mode** (which every modern Hikvision camera uses, including
> behind NAT) does **not** use the control port (`FTP_PORT`) for the actual file
> transfer. The client connects to the server's control port, then connects to a
> second, ephemeral **data port** in the `FTP_PASSIVE_PORTS` range to send the
> file. If that range is not reachable from the camera, uploads will hang and
> eventually time out — even though the control port is open.
>
> Make sure your firewall / cloud security group allows **inbound TCP** from the
> camera to **every port in `FTP_PASSIVE_PORTS`** (default `50000–50100`,
> 101 ports). It is not enough to open only `FTP_PORT`.

Concrete checklist:

1. **Inbound TCP `FTP_PORT`** (default `2121`) from the camera / camera subnet.
2. **Inbound TCP `FTP_PASSIVE_PORTS`** (default `50000–50100`) from the camera /
   camera subnet — **required for passive-mode data transfer**.
3. **Outbound TCP 443** to `api.platerecognizer.com`.
4. If the server is behind NAT / has a private IP:
   * Set `FTP_MASQUERADE_ADDRESS` to the **public IP** the camera reaches.
     Without this, the server tells the camera to connect back to its private
     address in the `PASV` response, which the camera cannot route to.
5. If you tighten the passive range, remember that **concurrent uploads from the
   same camera can each consume one data port**. The default range of 101 ports
   is comfortable for up to ~8 concurrent connections per camera with
   `FTP_MAX_CONS_PER_IP=8`; lower the upper bound only if you understand the
   trade-off.

---

## Running the server

### Foreground (development / quick test)

```bash
python main.py
```

You should see something like:

```
… INFO ftp-to-snapshot Starting FTP server on 0.0.0.0:2121 (root=…/uploads, match_suffix=VEHICLE_DETECTION.jpg, regions=None, mmc=False, passive_ports=50000-50100, masquerade=None)
```

Stop with `Ctrl+C`; the handler thread pool shuts down cleanly.

### As a systemd service (Linux)

Create `/etc/systemd/system/ftp-to-snapshot-cloud.service`:

```ini
[Unit]
Description=Hikvision -> Plate Recognizer Snapshot Cloud bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ftp-snapshot
WorkingDirectory=/opt/ftp-to-snapshot-cloud
ExecStart=/opt/ftp-to-snapshot-cloud/.venv/bin/python main.py
Restart=on-failure
RestartSec=5
EnvironmentFile=/opt/ftp-to-snapshot-cloud/.env

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ftp-to-snapshot-cloud
sudo journalctl -u ftp-to-snapshot-cloud -f
```

Make sure your firewall (and any cloud security group) opens
`FTP_PORT` **and** `FTP_PASSIVE_PORTS`.

### In Docker

A minimal `Dockerfile` (Python 3.13, uv) would look like:

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv \
 && uv sync --frozen --no-dev
COPY main.py ./
ENV PYTHONUNBUFFERED=1
EXPOSE 2121 50000-50100
CMD ["uv", "run", "python", "main.py"]
```

```bash
docker build -t ftp-to-snapshot-cloud .
docker run --rm -d \
  --name ftp-snapshot \
  -p 2121:2121 \
  -p 50000-50100:50000-50100 \
  --env-file .env \
  -v "$PWD/uploads:/app/uploads" \
  ftp-to-snapshot-cloud
```

> Remember to publish the **whole passive-port range** with `-p`, not just the
> control port — see [Network / firewall notes](#network--firewall-notes).

---

## Configuring the Hikvision camera

The exact menu paths vary by firmware, but the general idea is:

1. **Network → FTP**: configure an FTP server pointing at this bridge.
   * Server address: IP of the bridge (or its public IP if the camera is
     remote).
   * Port: `FTP_PORT` (default `2121`).
    * Username / password: `FTP_USER` / `FTP_PASSWORD`.  <!-- pragma: allowlist secret -->
   * **Passive mode** should be enabled (this is the camera's default for most
     Hikvision firmwares). It must reach `FTP_PASSIVE_PORTS`.
2. **Event → ANPR / LPR**: enable ANPR and configure **upload on event**.
3. The camera will then upload three files per detection:
   * `<timestamp>_VEHICLE_DETECTION.jpg`
   * `<timestamp>_VEHICLE_DETECTION_PLATE.jpg`
   * `anpr.xml`

The bridge will forward only the `VEHICLE_DETECTION.jpg` (configurable via
`MATCH_SUFFIX`).

---

## Operation guide

### What gets stored locally

Everything the camera uploads is written under `FTP_ROOT` (default
`./uploads`), preserving the camera's filenames. Override with `FTP_ROOT` if
you prefer a different path or want to mount a volume.

### What gets forwarded

Files whose name ends with `MATCH_SUFFIX` (default `VEHICLE_DETECTION.jpg`):

* Are **only** uploaded if their size is > 0 bytes.
* Are uploaded in a background thread via `POST /v1/plate-reader/` using the
  `upload` multipart field, plus any of `regions`, `camera_id`, `mmc`, `config`
  you have set.
* Have their HTTP response logged: `Snapshot OK <name> -> <payload>` on
  success, `Snapshot API error <status> for <name>: <body>` on failure.

Files that do not match are either kept on disk (`KEEP_NON_MATCHING=true`,
default) or deleted after receipt (`KEEP_NON_MATCHING=false`).

### Tuning throughput

* `MAX_WORKERS` controls how many concurrent Snapshot Cloud uploads are in
  flight. Snapshot Cloud has per-account rate limits; if you see
  `429`-class errors, lower this.
* `REQUEST_TIMEOUT` caps how long the HTTP call is allowed to take before it
  is abandoned.
* `FTP_MAX_CONS` / `FTP_MAX_CONS_PER_IP` cap concurrent FTP clients. Match
  these to the number of cameras and their upload bursts.

### Rotation / cleanup

The bridge does **not** delete matched files from `FTP_ROOT` — it just uploads
them. Add a cron job or a small logrotate-style script to clean up old files:

```bash
# Remove received files older than 7 days
find /opt/ftp-to-snapshot-cloud/uploads -type f -mtime +7 -delete
```

### Graceful shutdown

`Ctrl+C` (or `systemctl stop`) triggers `server.close_all()` plus a clean
`ThreadPoolExecutor.shutdown(wait=True)`, so in-flight HTTP uploads complete
before the process exits.

---

## Logs and troubleshooting

| Symptom                                              | Likely cause                                                                                                                                                              |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Camera uploads hang and then time out                | `FTP_PASSIVE_PORTS` not reachable from the camera. Open the range in your firewall / cloud SG — see [Network / firewall notes](#network--firewall-notes).               |
| Camera gets "Connection refused" on the data port    | `FTP_MASQUERADE_ADDRESS` is wrong / not set; the camera is being told to connect to a private IP it can't route to.                                                       |
| `RuntimeError: PLATE_RECOGNIZER_TOKEN environment variable is required when USE_SDK is not set` | You're in Cloud mode but didn't set a token. Set `PLATE_RECOGNIZER_TOKEN`, or switch to SDK mode with `USE_SDK=true`.                          |
| `RuntimeError: FTP_PASSIVE_PORTS must be in the form START-END`         | The passive-ports env var is malformed. Use e.g. `50000-50100`.                                                                                          |
| Files appear under `FTP_ROOT` but nothing reaches Snapshot Cloud | Filename suffix doesn't match `MATCH_SUFFIX` (e.g. your firmware names them differently), or `KEEP_NON_MATCHING=true` keeps the wrong files but does not forward them. |
| `Snapshot API error 401`                            | Token is wrong, revoked, or doesn't have the Snapshot Cloud feature enabled.                                                                                             |
| `Snapshot API error 429`                            | Snapshot Cloud rate limit hit — lower `MAX_WORKERS` or upgrade your plan.                                                                                                |
| `Ignoring empty matching file: …`                   | The camera wrote a 0-byte file; usually a transient network issue. Check your firewall and disk.                                                                        |

Set `LOG_LEVEL=DEBUG` for verbose pyftpdlib logs.

---

## Project layout

```
ftp-to-snapshot-cloud/
├── main.py          # FTP server + Snapshot Cloud forwarder
├── pyproject.toml   # Project metadata + dependencies
├── uv.lock          # Locked dependency versions (uv)
├── .env.example     # Sample environment file — copy to .env and edit
└── README.md        # This file
```
