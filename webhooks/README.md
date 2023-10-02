# Webhooks Receiver

Plate Recognizer lets you forward the inference results to a third party. Here are examples for how to use our [webhook API](http://docs.platerecognizer.com/#webhooks).

- [Webhooks Receiver](#webhooks-receiver)
  - [Sample Code](#sample-code)
    - [Python Without Dependencies](#python-without-dependencies)
    - [Python and Flask](#python-and-flask)
    - [Javascript / Node](#javascript--node)
    - [C# / .Net Framework v4.8:](#c--net-framework-v48)
  - [Sending Data to the Webhook Receiver](#sending-data-to-the-webhook-receiver)
  - [Home Assistant](#home-assistant)
  - [Stream and OpenEye](#stream-and-openeye)
    - [Start the Webhook Server](#start-the-webhook-server)
    - [Start Stream](#start-stream)
  - [Receive and Forward Webhook data to a SOAP service](#receive-and-forward-webhook-data-to-a-soap-service)
    - [Required Parameters](#required-parameters)
    - [Command Excecution Format](#command-excecution-format)
    - [Stream Webhook Configuration](#stream-webhook-configuration)
    - [Snapshot Webhook Configuration](#snapshot-webhook-configuration)


## Sample Code

After starting the receiver, configure Snapshot or Stream webhooks in Plate Recognizer with the URL http://<your-machine-ip>:8001/.

### Python Without Dependencies

```shell
python3 webhook_reader.py
```

### Python and Flask

```shell
pip install Flask==1.1.2
python3 webhook_reader_flask.py
```

### Javascript / Node

```shell
npm install
node webhook_reader.js
```

### C# / .Net Framework v4.8:

Install [this NuGet package](https://github.com/Http-Multipart-Data-Parser/Http-Multipart-Data-Parser) required for MultiPart Parsing

```shell
Install-Package HttpMultipartParser
```

Build Solution and Run WebhookReader.exe as a Console Application

## Sending Data to the Webhook Receiver

1. Find your machine local IP for example 192.168.0.206. You can use `ifconfig` to get it.
2. Send an example webhook to the server. If it is running correctly, it should exit without an error.
3. Optionally, you can send an authentication token with `-e TOKEN=XXX` or a camera with `-e CAMERA=XXX` to identify the webhook source.

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

## Receive and Forward Webhook data to a SOAP service

[This middleware example](https://github.com/parkpow/deep-license-plate-recognition/blob/master/webhooks/webhook_soap/middleware_webhook_soap.py) forwards the data coming from Stream or Snapshot SDK to a SOAP service that waits for `date`, `plate`, `score`, `image` fields and `user`/`password` for service authentication.

### Required Parameters

- `--soap-service-url`
- `--user` (service authentication user name)
- `--service-key` (service authentication user key)

### Command Excecution Format

```
python3 /path/to/script/middleware_webhook_soap.py \
--soap-service-url https://<SOAP_SERVICE_URL>?WSDL \
--user <SOAP_SERVICE_ACCESS_USER_NAME> \
--service-key <SOAP_SERVICE_KEY>
```

[Note that the webhook receiver listens on port 8002.](https://github.com/parkpow/deep-license-plate-recognition/blob/b2eca9ea39ab73ea6d49328bbde4f44a59c1e2e8/webhooks/webhook_soap/middleware_webhook_soap.py#L135C30-L135C34)

### Stream Webhook Configuration

- Set the parameter `webhook_targets` in `config.ini` to the host and port of your webhook.

```
# List of TZ names on https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
timezone = UTC
[cameras]
  #...
  # your global cameras configuration
  #...
  [[camera-1]]
    active = yes
    url = rtsp://192.168.0.108:8080/video/h264
    webhook_targets = webhook-to-SOAP
    #...
    # your camera configuration
    #...

  # Webhook targets and their parameters
    [webhooks]
    caching = yes
    [[webhook-to-SOAP]]
      url = http://192.168.0.180:8002
      image = yes
      image_type = vehicle, plate
      request_timeout = 30
  ```
### Snapshot Webhook Configuration

Follow the steps shown [here](https://guides.platerecognizer.com/docs/snapshot/api-reference#webhooks) to register this middleware url.
