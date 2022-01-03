
1. Create Config
 ```ini
[tag-update]
OLD = NEW
SILVER = SILVERPROC
NO_TAGS = NEWCLIENT

```


2. Build the image
```bash
docker build --tag platerecognizer/tags-updater .
```

3. Run Image
> Configure ParkPow API TOKEN and BASE_URL
```bash

docker run --rm -i -v ${PWD}:/code -p 3000:8001 -e TOKEN=8003########################## -e BASE_URL=https://app.parkpow.com platerecognizer/tags-updater

# Verbose logging
docker run --rm -i -v ${PWD}:/code -p 3000:8001 -e TOKEN=8003########################## -e BASE_URL=https://app.parkpow.com -e LOGGING=DEBUG  platerecognizer/tags-updater

# Custom Config
docker run --rm -i -v /tmp/config.ini:/code/config.ini -v ${PWD}:/code -p 3000:8001 -e TOKEN=8003########################## -e BASE_URL=https://app.parkpow.com -e LOGGING=DEBUG  platerecognizer/tags-updater

```


5. Send a MANUAL Alert

```json

{
"alert_name": "Test",
"time": "3 January 2022 at 10:28",
"timezone": "UTC",
"site": "Default Site",
"camera": "4958",
"license_plate": "nhk552",
"visits":69,
"confidence_level": 0.84,
"vehicle_id": 1204911,
"vehicle_type": "Sedan",
"vehicle_tag": "(empty)",
"vehicle_make": "Riley",
"vehicle_model": "RMF",
"vehicle_url":"http://app.parkpow.com/vehicle/1204911",
"vehicle_color": "Black",
"message": "Test",
"photo": "https://us-east-1.linodeobjects.com/parkpow-web/4958/2022-01-03/1028_XSQ82_1028_oHqIZ_car.jpg"
}

```

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
    -H 'content-length: 438' \
    -H 'accept: */*' \
    -H 'accept-encoding: gzip, deflate' \
    -H 'user-agent: python-requests/2.26.0' \
    -H 'host: webhook.site' \
    -d 'alert_name=Test&time=3+January+2022+at+13%3A24&timezone=UTC&site=Default+Site&camera=4958&license_plate=nhk552&visits=70&confidence_level=0.84&vehicle_id=1204911&vehicle_type=Sedan&vehicle_tag=&vehicle_make=Riley&vehicle_model=RMF&vehicle_url=http%3A%2F%2Fapp.parkpow.com%2Fvehicle%2F1204911&vehicle_color=Black&message=Test&photo=https%3A%2F%2Fus-east-1.linodeobjects.com%2Fparkpow-web%2F4958%2F2022-01-03%2F1324_XL5Py_1324_nLq7Q_car.jpg'


```

Multiple Tags SILVER, OLD
```bash
# TODO


```


6. Confirm ParkPow is Updated

Visit vehicle details page, Example:
https://app.parkpow.com/vehicle/1204911
