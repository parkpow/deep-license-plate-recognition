# Parkpow Tags Updater

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
    > **NO_TAGS** will be added to vehicles without any tags

2. Build the server image
    ```bash
    cd webhooks/tags-updater # Navigate into the tags-updater folder
    docker build --tag platerecognizer/parkpow-tag-updater .
    ```

3. Run the built image, assuming the config folder path is `/home/user1/tags-updater`, this would be the run command:
    ```bash
    docker run --rm --net=host -i -v /home/user1/tags-updater:/user-data -p 3000:8001 platerecognizer/parkpow-tag-updater
    ```
    > The server listens on port 8001, For more verbose logging add `-e LOGGING=DEBUG`

5. Send alerts from ParkPow to the server
    1. Add `http://DOCKER_HOST_IP:3000` as Webhook on ParkPow by visiting this page  `http://PARKPOW_IP/settings/webhook/list`
    2. Use the Webhook to create Alerts on ParkPow by visiting this page `http://PARKPOW_IP/settings/alert/create`
        Make sure to select the previous Webhook and triggers.
    3. Send detections to ParkPow to trigger the alerts, Check [this link](https://guides.platerecognizer.com/docs/parkpow/integrations) for more details

    ParkPow should now be able to send alerts to the container which will perfom the tag updates.
    > Note that any edits to the config.ini or addition of new vehicle tags to ParkPow requires a restart of the container

6. Confirm ParkPow is Updated by visiting a vehicle details page.
   Example: https://app.parkpow.com/vehicle/1204911
