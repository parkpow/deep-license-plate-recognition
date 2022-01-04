
1. Create Config
 ```ini
[settings]
parkpow_base_url = https://app.parkpow.com
parkpow_api_token = 8003dfa697f08f07d108c10de6f7cf17d86707a5

[tag-update]
OLD = NEW
SILVER = SILVERPROC
NO_TAGS = NEWCLIENT

```


2. Build the image
```bash
docker build --tag platerecognizer/parkpow-tag-updater .
```

3. Run Image
Development
```bash

docker run --rm -i -v ${PWD}:/app -p 3000:8001 platerecognizer/parkpow-tag-updater

# Verbose logging add -e LOGGING=DEBUG
docker run --rm -i -v ${PWD}:/app -p 3000:8001 -e LOGGING=DEBUG  platerecognizer/parkpow-tag-updater

# Custom Config add -v /tmp/config.ini:/app/config.ini
docker run --rm -i  -v ${PWD}:/app -p 3000:8001 -v /tmp/config.ini:/app/config.ini  platerecognizer/parkpow-tag-updater

```

Production
```bash

docker run --rm -i -p 3000:8001 platerecognizer/parkpow-tag-updater

# Verbose logging add -e LOGGING=DEBUG
docker run --rm -i -p 3000:8001 -e LOGGING=DEBUG  platerecognizer/parkpow-tag-updater

# Custom Config add -v /tmp/config.ini:/app/config.ini
docker run --rm -i  -p 3000:8001 -v /tmp/config.ini:/app/config.ini  platerecognizer/parkpow-tag-updater

```

5. Send a MANUAL Alert
Empty Tags
```bash
curl -X 'POST' 'http://localhost:3000'\
    -H 'connection: close' \
    -H 'content-type: application/x-www-form-urlencoded' \
    -H 'content-length: 438' \
    -H 'accept: */*' \
    -H 'accept-encoding: gzip, deflate' \
    -H 'user-agent: python-requests/2.26.0' \
    -H 'host: webhook.site' \
    -d 'alert_name=Test&time=3+January+2022+at+10%3A28&timezone=UTC&site=Default+Site&camera=4958&license_plate=nhk552&visits=69&confidence_level=0.84&vehicle_id=1204911&vehicle_type=Sedan&vehicle_tag=&vehicle_make=Riley&vehicle_model=RMF&vehicle_url=http%3A%2F%2Fapp.parkpow.com%2Fvehicle%2F1204911&vehicle_color=Black&message=Test&photo=https%3A%2F%2Fus-east-1.linodeobjects.com%2Fparkpow-web%2F4958%2F2022-01-03%2F1028_XSQ82_1028_oHqIZ_car.jpg'

```


Single Tag SILVER
```bash

curl -X 'POST' 'http://localhost:3000'\
    -H 'connection: close' \
    -H 'content-type: application/x-www-form-urlencoded' \
    -H 'content-length: 456' \
    -H 'accept: */*' \
    -H 'accept-encoding: gzip, deflate' \
    -H 'user-agent: python-requests/2.26.0' \
    -H 'host: webhook.site' \
    -d 'alert_name=Test&alert_tags=&time=4+January+2022+at+07%3A10&timezone=UTC&site=Default+Site&camera=4958&license_plate=nhk552&visits=72&confidence_level=0.84&vehicle_id=1204911&vehicle_type=Sedan&vehicle_tag=SILVER&vehicle_make=Riley&vehicle_model=RMF&vehicle_url=http%3A%2F%2Fapp.parkpow.com%2Fvehicle%2F1204911&vehicle_color=Black&message=Test&photo=https%3A%2F%2Fus-east-1.linodeobjects.com%2Fparkpow-web%2F4958%2F2022-01-04%2F0710_rrhg4_0710_gjBAP_car.jpg'


```

Multiple Tags SILVER, OLD
```bash
# TODO


```


6. Confirm ParkPow is Updated

Visit vehicle details page, Example:
https://app.parkpow.com/vehicle/1204911
