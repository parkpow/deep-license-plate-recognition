# Introduction

This middleware receives Stream events via webhooks, creates a `.xml` file with a specific format, populates it with Stream event information, and send the file to a sFTP Server folder.

# Set Stream

## Run Stream

Follow the instructions to run Stream: https://guides.platerecognizer.com/docs/stream/manual-install#start-stream

## Set Webhook URL

Follow the instructions to run set webhook URL in Stream `config.ini` file: https://guides.platerecognizer.com/docs/stream/configuration#webhook-parameters

Set this `webhook_to_xml_ftp` container webhook endpoint in URL parameter.

## Format

`http://<WEBHOOK_RECEIVER_IP_ADDRESS>:<WEBHOOK_RECEIVER_PORT>/webhook`

## Example

```
# ...
# the rest of your config.ini file
# ...
[webhooks]
  caching = yes
  [[webhook_receiver]]
    url = http://0.0.0.0:8002/webhook
    image = yes
    video = no
    image_type = vehicle
    request_timeout = 30
# ...
# the rest of your config.ini file
# ...
```

## Set user data in Stream

To tell Stream to send custom data like GPS information and LPRCameraName, it need to be specified in the following format:

`'{LPRCameraName: str, LatitudeDegreeValue: int, LatitudeMinuteValue: int, LatitudeSecondValue: int, LongitudeDegreeValue: int, LongitudeMinuteValue: int, LongitudeSecondValue: int}'`

use `curl` to send the custom information registration to stream container.

### Format

`curl -d "id=<CAMERA_NAME>&data='<CUSTOM_DATA>'" http://<STREAM_IP>:<STREAM_PORT>/user-data/`

### Example

`curl -d "id=camera-1&data='{LPRCameraName: Camera 1 NY, LatitudeDegreeValue: 37,LatitudeMinuteValue: 25, LatitudeSecondValue: 19, LongitudeDegreeValue: 122, LongitudeMinuteValue: 5, LongitudeSecondValue: 4}'" http://localhost:8001/user-data/`

# Build Middleware Image

Move to `webhook_to_xml_ftp` folder and run command.

`sudo docker build -t stream_to_xml_Sftp:latest .`

# Run Middleware Container

```
sudo docker run -p 8002:8002 \
-e HOST=0.0.0.0 \
-e HOST_PORT=8002 \
-e SFTP_HOST=192.168.0.59 \
-e SFTP_HOST_PORT=22 \
-e SFTP_REMOTE_PATH='/path/to/ftp/folder/' \
-e SFTP_USERNAME=<YOUR_SFTP_USER> \
-e SFTP_PASSWORD=<YOUR_SFTP_PASS> \
dea_middleware:1
```
ℹ️ If running on Windows OS replace "\\" break line character with "^" character.

## Parameters

### Required

- SFTP_HOST: SFTP server IP
- SFTP_REMOTE_PATH: Path to FTP folder to save xml files
- SFTP_USERNAME
- SFTP_PASSWORD

### Optional

- HOST: Host IP (default 0.0.0.0)
- HOST_PORT: Host Port (default 5000)
- SFTP_HOST_PORT: SFTP server Port (default 22)
- DEBUG: set to 1 to activate debug mode

### XML System Parameters

This data will be populated on eache xml field respectively.

| config.ini variable | xml file field         |
|----------------------|-----------------------|
|lpr_sys_id            |LPRSystemID            |
|ori_id                |OrganizationORIID      |
|id_issuing_authority  |IDIssuingAuthorityText |
|document_country_code |DocumentCountryCode    |

Parameters to be read at container starting moment from `config.ini` file.

:warning: **These fields are required**, the absence of any of them will result in an exception.
