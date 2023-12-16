## Batch Video Processing

Upload Videos from a folder to Stream via [file-upload](https://guides.platerecognizer.com/docs/stream/video-files#file-upload-api).

```shell
python video_upload.py
```

## Stream Monitor
Monitor Stream HEALTH through it's logs. This script exposes a single API endpoint that returns responses in this format:

```json
{"active": true, "cameras": {"camera-1": {"status": "running"}}}
```

```json
{"active": true, "cameras": {"camera-1": {"status": "offline"}}}
```

`active` is true if the stream container is running, so you need to check it before checking `cameras`.

### 1. Installation

```bash
git clone https://github.com/parkpow/deep-license-plate-recognition.git
cd stream
python stream_monitor.py --help
```

Optional arguments:
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

For example, you can start the script with:
```bash
python stream_monitor.py -c stream -i 30 -d 120
```

### 2. Calling the API endpoint
In another terminal, you can query Stream status.

```bash
 curl localhost:8001
 # {"active": false, "cameras": {}}
```

## Remove Stream Images

This script runs nightly to remove images that are over xx hours in Stream folder. However, if you wouldn't want to save images locally at all, you may refer to this [guide](https://guides.platerecognizer.com/docs/stream/faq#how-do-i-not-save-vehicle-or-plates-images-in-my-localstreamfolder-when-forwarding-webhook-data).

Make sure to enter this command inside the Stream folder.


```bash
 wget -q 'https://raw.githubusercontent.com/parkpow/deep-license-plate-recognition/master/stream/remove-images.sh' && chmod +x remove-images.sh && ./remove-images.sh
```
_Note: This script must be run as a root user._