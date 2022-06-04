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
       -e USERNAME='user' \   # VMS username
       -e PASSWORD='pass' \  # VMS password
       -e VMS_API='https://localhost:7001' \  # VMS API Endpoint
       -e CAMERA_UID="########" \  # UID for camera to receive the events       
       platerecognizer/stream-nx-notifier
    
    
    # Example 
    docker run --rm -t \
       --net=host \
       -e LOGGING=DEBUG \ 
       -e USERNAME='admin' \ 
       -e PASSWORD='39393jdhhdiisu2' \ 
       -e VMS_API='https://192.168.100.6:7001' \ 
       -e CAMERA_UID="420f37f6-8875-6885-9200-11504e61f485" \ 
       platerecognizer/stream-nx-notifier
    
    
    ```
    
3. Configure Stream Webhook Targets:
    ```text
    
        webhook_targets = http://localhost:8001
    
    ```
    > Restart Stream after config changes, 
    You might need to run Stream with `--net=host` too for the Webhook target to be reachable


## TODO
-[ ] I think user might need to direct specific events to specific Cameras in the VMS, i.e multiple `-e CAMERA_UID`