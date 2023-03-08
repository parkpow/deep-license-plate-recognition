# Connect Stream to OpenEye

This project uses Stream webhooks to send license plate data to a OpenEye.

Follow the procedure below to start the webhook:

## **Manual Installation:**

Install flask and requests

```bash
pip install Flask
```

```bash
pip install requests
```

Start the server

```bash
python3 file_name.py <parameter>

example:
python3 main.py --port=8001 --debug --host==0.0.0.0 --aki_token=abcdefg --aks_token=abcdefghijklmnopqrstuvxz

```

Optional parameters:

- --port
- --debug

Required parameters:

- --aki_token
- --aks_token

For external access

- --host=0.0.0.0

Next, configure and start Stream:

- Set the [Camera-ID](https://guides.platerecognizer.com/docs/stream/configuration#hierarchical-configuration), present in the config.ini configuration file, equal to the Camera External_ID parameter provided by OpenEye.
- Set the parameter webhook_targets in config.ini to the host and port of your webhook.

```ini
# List of TZ names on https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
timezone = UTC

[cameras]
  # Full list of regions: http://docs.platerecognizer.com/#countries
  regions = gb
  image_format = $(camera)_screenshots/%y-%m-%d/%H-%M-%S.%f.jpg

  webhook_targets = http://192.168.5.10:5000

  [[ExternalCameraId-OpenEye01]]
    active = yes
    url = rtsp://192.168.0.110:8080/video/h264
  [[ExternalCameraId-OpenEye...N]]
    active = yes
    url = rtsp://192.168.0.120:8080/video/h264
```

The example above shows the config.ini set up with the previously running webhook and two cameras with their respective RTSP links and their External camera ID. This same configuration can be used for N_Cameras.

After modifying the config.ini, restarts the Stream container.

## Docker Setup

To run the script in a docker container, use the procedure below:

1. Build the image

   ```bash
   docker build --tag platerecognizer/webhook-openeye .

   ```

2. Run the image

   ```bash
   docker run --rm -t -p 5000:5000 -e AKI_TOKEN=XXXXXXXXXXXX -e AKS_TOKEN=YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY platerecognizer/webhook-openeye

   ```
