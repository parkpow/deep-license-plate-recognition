# Stream NX VMS Notifier
Forward Stream Webhook Events to NX VMS as Alerts 

## Setup
1. Build the image
    ```bash
    docker build --tag platerecognizer/stream-nx-notifier .

    ```

2. Run Image
    ```bash
    
    docker run --rm -t \
       --net=host \
       -e LOGGING=DEBUG \  # Turn on debug logging
       platerecognizer/stream-nx-notifier \
       --username=user \  # VMS username
       --password=pass \  # VMS password
       --vms='https://localhost:7001' \  # VMS API Endpoint
       --camera="12345678-****-****-****-****-**********" # UID for camera to used as source of events
    
    
    # Example 
    docker run --rm -t \
       --net=host \
       -e LOGGING=DEBUG \
       platerecognizer/stream-nx-notifier \
       --username=admin \
       --password=39393jdhhdiisu2 \
       --vms='https://192.168.100.6:7001' \
       --camera="420f37f6-8875-6885-9200-11504e61f485"
    
    
    ```
    
3. Configure Stream Webhook Targets:
    ```text
    
        webhook_targets = http://localhost:8001
    
    ```
    > Restart Stream after config changes, 
    You might need to run Stream with `--net=host` too for the Webhook target to be reachable


## TODO
-[ ] I think user might need to direct specific events to specific Cameras in the VMS, i.e Pass multiple `--camera`