## Batch Video Processing

Upload Videos from a folder to Stream via [file-upload](https://guides.platerecognizer.com/docs/stream/video-files#file-upload-api). 

```shell
python video_upload.py
```

## Stream Monitor
Monitor Stream HEALTH through it's logs.
This script exposes a single API endpoint that returns responses in this format:

```json
{"active": true, "cameras": {"camera-1": {"status": "running"}}}
```

```json
{"active": true, "cameras": {"camera-1": {"status": "offline"}}}
```

`active` is true if the stream container is running, so you need to check it before checking `cameras`.


## Requirements
- Python3


## Quick Setup
### 1. Run Script
```bash
git clone https://github.com/parkpow/deep-license-plate-recognition.git
cd stream
python stream_monitor.py

```

Available arguments

```bash
  -c CONTAINER, --container CONTAINER
                        Stream Container Name or ID
  -l LISTEN, --listen LISTEN
                        Server listen address
  -p PORT, --port PORT  Server listen port
  -i INTERVAL, --interval INTERVAL
                        Interval between reading logs in seconds
  -d DURATION, --duration DURATION
                        Duration to use in considering a camera as offline in seconds

```


### 2. Make calls to API endpoint
```bash
 curl localhost:8001

 # {"active": false, "cameras": {}}

```
