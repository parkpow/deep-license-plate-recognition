# Genetec Integration
Forward Genetec Events to ParkPow or Platerecognizer Snapshot

## Setup
1. Build the image
    ```shell
    docker build --tag platerecognizer/genetec-integration .
    ```

2. Process Events
    1. Using ParkPow
    ```shell
    docker run --rm -t \
       --net=host \
       -e LOGGING=DEBUG \
       platerecognizer/genetec-integration \
       parkpow \
       --token=pass \
       --url='http://localhost:8000'
    ```

    **token**: ParkPow token
    **url**: ParkPow URL, Optional for ParkPow cloud.
   2. Using Snapshot
       ```shell
       docker run --rm -t \
          --net=host \
          -e LOGGING=DEBUG \
          platerecognizer/genetec-integration \
          snapshot \
          --token=pass \
          --url='http://localhost:8080'
       ```

       **token**: Platerecognizer token, Optional for Snapshot onPremise.
       **url**: Snapshot URL, Optional for Snapshot cloud.
        > you should not provide both args at the same time

3. URL to use for Genetec Webhooks settings is: `http://<machine-ip>:8001/` Test using CURL:
```shell
curl -vX POST http://localhost:8002/ -d @../../snapshot-middleware/test/Genetec.txt --header "Content-Type: application/json"
```
