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

Make sure to have this remove_images.py script inside the Stream folder.

_Note: Don't forget to update the --threshold (time duration in hours) to remove images older than xx hours._

### Schedule running of script

For Linux: 

_Note: Make sure cron is installed._

```bash
sudo sh -c 'echo "0 0 * * * root <path_to_python_interpreter> <path_to_script> --threshold 23" >> /etc/crontab'

# Example: This runs the script daily at midnight and removes images older than 23 hours.
sudo sh -c 'echo "0 0 * * * root /usr/bin/python3 /home/user/stream/remove_images.py --threshold 23" >> /etc/crontab'
```

For Windows:

1. Run this in a command promt or powershell to add the script to Windows Task Scheduler.

```ps
schtasks /create /sc <frequency> /tn RemoveStreamImages /tr "<path_to_python_interpreter> <path_to_script> --threshold 10" /st <start_time>

# Example: This runs the script daily at midnight and removes images older than 10 hours.
schtasks /create /sc daily /tn RemoveStreamImages /tr "C:\Users\User\AppData\Local\Microsoft\WindowsApps\python.exe C:\PlateRecognizer\Stream\remove_images.py --threshold 10" /st 00:00

```

2. Lastly, to make sure this runs on the Stream directory. Open Task Scheduler, click on the newly created scheduler task, then choose Properties. Go to the Actions tab, then click on Edit. Set the Start in (optional) to be the path of your Stream Directory then click Ok. 


### Uninstall

To uninstall the service, just remove the script from the Stream directory. 

To remove the scheduled running of the script, 

For Linux, run this in the terminal:
```bash
sudo sed -i '/remove_images/d' /etc/crontab
```

For Windows, run this in command promt or powershell:
```ps
schtasks /delete /tn RemoveStreamImages /f
```
