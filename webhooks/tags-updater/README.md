# Parkpow Tags Updater

## Quick Setup
1. Create a folder with a `config.ini` with these content, remember to update the file with your relevant details
    ```ini
    [settings]
    parkpow_base_url = https://app.parkpow.com
    parkpow_api_token = ...

    [tag-update]
    OLD = NEW
    SILVER = SILVERPROC
    NO_TAGS = NEWCLIENT

    ```
    > All later steps assume the created folder path is `/home/user1/tags-updater`

2. Download and Run the image
    ```bash
    docker run --rm --net=host -i -v /home/user1/tags-updater:/user-data -p 3000:8001 platerecognizer/parkpow-tag-updater
    ```
    After the server starts successfully, add `http://DOCKER_HOST_IP:3000` as Webhook on ParkPow and use it to create Alerts.
    ParkPow should now be able to send alerts to the container and perfom updates.
    > Note that any edits to the config.ini or addition of new tags to ParkPow requires a restart of the container

## Advanced Setup

1. Create config.ini in /tmp/config
    ```ini
    [settings]
    parkpow_base_url = https://app.parkpow.com
    parkpow_api_token = ...

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

    docker run --rm -i -v ${PWD}:/app -v /tmp/config:/user-data -p 3000:8001 platerecognizer/parkpow-tag-updater

    # Verbose logging add -e LOGGING=DEBUG
    docker run --rm -i -v ${PWD}:/app -v /tmp/config:/user-data -p 3000:8001 -e LOGGING=DEBUG  platerecognizer/parkpow-tag-updater

    # Custom Config add -v /tmp/config.ini:/app/config.ini
    docker run --rm -i  -v ${PWD}:/app -p 3000:8001 -v /tmp/config:/user-data  platerecognizer/parkpow-tag-updater

    ```

    Production
    ```bash

    docker run --rm -i -v /tmp/config:/user-data -p 3000:8001 platerecognizer/parkpow-tag-updater

    # Verbose logging add -e LOGGING=DEBUG
    docker run --rm -i -v /tmp/config:/user-data -p 3000:8001 -e LOGGING=DEBUG  platerecognizer/parkpow-tag-updater

    # Custom Config add -v /tmp/config.ini:/app/config.ini
    docker run --rm -i -p 3000:8001 -v /tmp/config:/user-data  platerecognizer/parkpow-tag-updater

    ```

5. Send an Alert Manualy
    Empty Tags
    ```bash
    curl -X 'POST' 'http://localhost:3000'\
        -H 'connection: close' \
        -H 'content-type: application/x-www-form-urlencoded' \
        -H 'content-length: 451' \
        -H 'accept: */*' \
        -H 'accept-encoding: gzip, deflate' \
        -H 'user-agent: python-requests/2.26.0' \
        -H 'host: webhook.site' \
        -d 'alert_name=Test&alert_tags=&time=10+January+2022+at+09%3A06&timezone=UTC&site=Default+Site&camera=4958&license_plate=nhk552&visits=76&confidence_level=0.84&vehicle_id=1204911&vehicle_type=Sedan&vehicle_tag=&vehicle_make=Riley&vehicle_model=RMF&vehicle_url=http%3A%2F%2Fapp.parkpow.com%2Fvehicle%2F1204911&vehicle_color=Black&message=Test&photo=https%3A%2F%2Fus-east-1.linodeobjects.com%2Fparkpow-web%2F4958%2F2022-01-10%2F0906_78Uei_0906_EcraK_car.jpg'

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
        -d 'alert_name=Test&alert_tags=&time=9+January+2022+at+07%3A00&timezone=UTC&site=Default+Site&camera=4958&license_plate=nhk552&visits=73&confidence_level=0.84&vehicle_id=1204911&vehicle_type=Sedan&vehicle_tag=SILVER&vehicle_make=Riley&vehicle_model=RMF&vehicle_url=http%3A%2F%2Fapp.parkpow.com%2Fvehicle%2F1204911&vehicle_color=Black&message=Test&photo=https%3A%2F%2Fus-east-1.linodeobjects.com%2Fparkpow-web%2F4958%2F2022-01-09%2F0700_Gxqv2_0700_ioteZ_car.jpg'

    ```

    Multiple Tags SILVERPROC, Resident
    ```bash

    curl -X 'POST' 'http://localhost:3000'\
        -H 'connection: close' \
        -H 'content-type: application/x-www-form-urlencoded' \
        -H 'content-length: 473' \
        -H 'accept: */*' \
        -H 'accept-encoding: gzip, deflate' \
        -H 'user-agent: python-requests/2.26.0' \
        -H 'host: webhook.site' \
        -d 'alert_name=Test&alert_tags=&time=10+January+2022+at+08%3A51&timezone=UTC&site=Default+Site&camera=4958&license_plate=nhk552&visits=75&confidence_level=0.84&vehicle_id=1204911&vehicle_type=Sedan&vehicle_tag=Resident%2C+SILVERPROC&vehicle_make=Riley&vehicle_model=RMF&vehicle_url=http%3A%2F%2Fapp.parkpow.com%2Fvehicle%2F1204911&vehicle_color=Black&message=Test&photo=https%3A%2F%2Fus-east-1.linodeobjects.com%2Fparkpow-web%2F4958%2F2022-01-10%2F0851_gfj4q_0851_uHbzW_car.jpg'

    ```

6. Confirm ParkPow is Updated by Visiting vehicle details page
   Example: https://app.parkpow.com/vehicle/1204911
