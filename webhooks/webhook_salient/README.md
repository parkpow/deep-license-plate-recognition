# Stream CompleteView Notifier
Forward Stream Webhook Events to [Salient CompleteView](https://www.salientsys.com/products/completeview/) VMS as Events

## Setup
1. Build the image
    ```bash
    docker build --tag platerecognizer/stream-salient-notifier .

    ```

2. Run Image
    ```bash

    docker run --rm -t \
       --net=host \
       -e LOGGING=DEBUG \  # Turn on debug logging
       platerecognizer/stream-salient-notifier \
       --username=user \  # Recording server username
       --password=pass \  # Recording server password
       --vms='http://localhost:4502' \  # Recording server API Endpoint
       --camera="9ee7046b-0ab3-49cd-908f-eb293fdc1e3f" # GUID for camera to used as source of events


    # Example
    docker run --rm -t \
       --net=host \
       -e LOGGING=DEBUG \
       platerecognizer/stream-salient-notifier \
       --username=admin \
       --password=39393jdhhdiisu2 \
       --vms_api_url='http://192.168.100.6:4502' \
       --camera="9ee7046b-0ab3-49cd-908f-eb293fdc1e3f"

    ```

3. Configure Stream Webhook Targets:
    ```text

        webhook_targets = http://localhost:8001

    ```
    > Restart Stream after config changes,
    You might need to run Stream with `--net=host` too for the Webhook target to be reachable
