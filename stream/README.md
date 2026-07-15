# Stream utilities

This directory contains companion utilities for a running Plate Recognizer
Stream installation. For Stream setup and configuration, see the
[Stream documentation](https://guides.platerecognizer.com/docs/stream/getting-started).

## Batch video processing

`video_upload.py` uploads every file in a directory to Stream's
[file-upload API](https://guides.platerecognizer.com/docs/stream/video-files#file-upload-api)
and appends successful responses to `output.jsonl`.

Install the directory's dependencies, then start the uploader:

```bash
python -m pip install -r requirements.txt
python video_upload.py /path/to/videos
```

The file-upload server defaults to `http://localhost:8081`. Use `--sdk-url` to
change it and `--mask` to select a camera mask.

## Stream monitor

`stream_monitor.py` reads a Stream container's Docker logs and exposes its
status over HTTP.

```bash
python stream_monitor.py --help
python stream_monitor.py --container stream --interval 30 --duration 120
```

The server listens on `localhost:8001` by default. Query it from another
terminal:

```bash
curl http://localhost:8001
```

Example response:

```json
{
  "active": true,
  "cameras": {
    "camera-1": {"status": "running"},
    "camera-2": {"status": "offline"}
  }
}
```

`active` reports whether the Stream container is running. A camera is marked
offline when it has not produced a recognized log entry within `--duration`
seconds.

## Remove Stream images

`remove_images.py` recursively deletes `.jpg` files and then removes empty
directories. It supports two mutually exclusive cleanup modes:

- Age mode deletes images older than 1–23 hours.
- Disk-usage mode deletes the oldest images first when disk usage reaches a
  trigger percentage, stopping when the target free-space percentage is met.

This utility permanently deletes files. Test the command against a disposable
directory before scheduling it against Stream data.

### Delete by age

Delete images older than 23 hours:

```bash
python remove_images.py --age --threshold 23 --directory /path/to/stream
```

### Delete by disk usage

When disk usage reaches 80%, delete the oldest images until at least 20% of the
disk is free:

```bash
python remove_images.py \
  --usage \
  --trigger_usage 80 \
  --target_free 20 \
  --directory /path/to/stream
```

Run `python remove_images.py --help` for the complete argument reference. If
you do not want Stream to save images at all, use the appropriate
[Stream configuration](https://guides.platerecognizer.com/docs/stream/faq#how-do-i-not-save-vehicle-or-plates-images-in-my-localstreamfolder-when-forwarding-webhook-data)
instead of periodically deleting them.

### Schedule cleanup

On Linux, add one selected cleanup command to cron. For example, this runs age
cleanup every night at midnight:

```cron
0 0 * * * /usr/bin/python3 /path/to/remove_images.py --age --threshold 23 --directory /path/to/stream
```

This example checks disk usage every ten minutes:

```cron
*/10 * * * * /usr/bin/python3 /path/to/remove_images.py --usage --trigger_usage 80 --target_free 20 --directory /path/to/stream
```

Use `crontab -e` for the account that owns the Stream files. If you edit
`/etc/crontab` instead, include the account name between the schedule and the
command.

On Windows, create a scheduled task in Command Prompt or PowerShell. The
following example runs age cleanup daily at midnight:

```powershell
schtasks /create /sc daily /tn RemoveStreamImages /tr "python C:\path\to\remove_images.py --age --threshold 23 --directory C:\PlateRecognizer\Stream" /st 00:00
```

For disk-usage cleanup, use a distinct task name and command:

```powershell
schtasks /create /sc minute /mo 10 /tn FreeUpStreamDiskSpace /tr "python C:\path\to\remove_images.py --usage --trigger_usage 80 --target_free 20 --directory C:\PlateRecognizer\Stream"
```

To remove these tasks later:

```powershell
schtasks /delete /tn RemoveStreamImages /f
schtasks /delete /tn FreeUpStreamDiskSpace /f
```
