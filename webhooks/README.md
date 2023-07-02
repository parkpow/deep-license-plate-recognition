# Webhooks

Plate Recognizer lets you forward the inference results to a third party. Here are examples for how to use our [webhook API](http://docs.platerecognizer.com/#webhooks).

  - [Generic Webhook Server](#generic-webhook-server)
    - [Sending Data to the Webhook Server](#sending-data-to-the-webhook-server)
  - [Home Assistant](#home-assistant)
  - [Stream and OpenEye](#stream-and-openeye)
    - [Start the Webhook Server](#start-the-webhook-server)
    - [Start Stream](#start-stream)


## Generic Webhook Server

Here are some webhook server examples. **Pick one** of the options below.

- **Python and the standard library:**

Start the server

```bash
python3 webhook_reader.py
```

- **Python and Flask:**

Install flask

```bash
pip install Flask==1.1.2
```

Start the server

```bash
python3 webhook_reader_flask.py
```

- **Javascript / Node:**

Install dependencies

```bash
npm install
```

Start the server

```bash
node webhook_reader.js
```

- **C# / .Net Framework v4.8:**

Install [this NuGet package](https://github.com/Http-Multipart-Data-Parser/Http-Multipart-Data-Parser) required for MultiPart Parsing

```shell
PM> Install-Package HttpMultipartParser
```

Build Solution and Run WebhookReader.exe as a Console Application

### Sending Data to the Webhook Server

1. Find your machine local IP for example 192.168.0.206. You can use `ifconfig` to get it.
2. Send an example webhook to the server. If it is running correctly, it should exit without an error.

```shell
docker run -e URL=http://MY_IP_ADDRESS:8001 platerecognizer/webhook-tester
```

3. Configure the webhook on Platerecognizer.
   - In Stream, edit your `config.ini`, add the following to a camera: `webhook_target = http://MY_IP_ADDRESS:8001/`
   - For Snapshot, open [Webhooks Configuration](https://app.platerecognizer.com/accounts/webhooks/).

## Home Assistant

[This project](https://github.com/adamjernst/plate-handler) uses Stream webhooks to send license plate data to a home automation server. Form there, it will send a notification.

## Stream and OpenEye

Use Stream webhooks to send license plate data to a OpenEye. Follow the procedure below to start the webhook.

### Start the Webhook Server

Install dependencies
```bash
pip install Flask
pip install requests
```

Start the server
```bash
python3 webhook_alerts_OpenEye.py --port=5000 --host==0.0.0.0 --aki_token=abcdefg --aks_token=abcdefghijklmnopqrstuvxz
```

Optional parameters:
- --port
- --debug

Required parameters:
- --aki_token
- --aks_token

For external access:
- --host=0.0.0.0

### Start Stream

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

After modifying the config.ini, restart the Stream container.
