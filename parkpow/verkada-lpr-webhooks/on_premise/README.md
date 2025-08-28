# ParkPow Verkada Integration
Forward Verkada Webhook Events to ParkPow

## Setup
1. Build the image
    ```bash
    docker build --tag platerecognizer/verkada-parkpow .

    ```

2. Run Image
    ```bash

    docker run --rm -t \
       --net=host \
       -e LOGGING=DEBUG \
       platerecognizer/verkada-parkpow \
       --api-key=user \
       --token=pass \
       --pp-url='http://localhost:8000'
    ```
    **api-key**: Verkada API Key
    **token**: ParkPow token
    **pp-url**: ParkPow URL, Optional for ParkPow cloud.

3. Add internet accessible URL to the container to your Verkada Webhooks settings](https://command.verkada.com/admin/org-settings/verkada-api)


