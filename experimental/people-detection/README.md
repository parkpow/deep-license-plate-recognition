# Persons Detector
Detect person in video file or live camera feed.
When a person is detected, send a webhook similar to Snapshot Cloud in real time.

## Setup
### 1. Build Docker image
First [download weights](https://drive.google.com/file/d/1liPJnM2MAVhdzlUpJjm8xfZ99Gk_Nokl/view?usp=sharing) into this directory then build docker image.
1. Build CPU only image. Is smaller, builds faster but is slower
    ```bash
    docker build --target cpu --tag platerecognizer/persons-detector .
    ```
2. Build GPU image. Is larger, builds slower but is faster. Also requires [setting up authentication to nvcr.io](https://forums.developer.nvidia.com/t/are-nvidia-docker-images-available-publicly/54619/4)
    ```bash
    docker build --target gpu --tag platerecognizer/persons-detector .
    ```

### 2. Run Built Image
Example usage of processing platerecognizer demo rtsp and sending events to [webhook.site](https://webhook.site)  
1. Run With CPU only:
```shell
docker run --rm -t platerecognizer/persons-detector\
  -url rtsp://platerec:8S5AZ7YasGc3m4@video.platerecognizer.com:8554/demo\
  -webhook https://webhook.site/06e632d8-db10-44c1-a066-b8df3c2ca1de\
  -image -heads -sample 10
```

2. Run With GPU support:
```shell
docker run --rm --gpus=all -t platerecognizer/persons-detector\
  -url rtsp://platerec:8S5AZ7YasGc3m4@video.platerecognizer.com:8554/demo\
  -webhook https://webhook.site/06e632d8-db10-44c1-a066-b8df3c2ca1de\
  -image -heads -sample 10 -device 0
```

### 3. Get Output
The webhook payload format is similar to [the one sent by Snapshot Cloud SDK](https://guides.platerecognizer.com/docs/snapshot/api-reference/#webhooks)

### 3. View Help on Usage
```
docker run --rm -t platerecognizer/persons-detector -h
```
Help output of command options
```
usage: main.py [-h] -url URL [-device DEVICE] -webhook WEBHOOK [-image] [-heads] [-weights WEIGHTS] [-sample SAMPLE]

Detect persons in live camera feed or video file

optional arguments:
  -h, --help        show this help message and exit
  -url URL          Video URL, rtsp://, rtmp://, http:// or File path in a mounted volume
  -device DEVICE    Use GPU or CPU, cpu or a cuda device i.e. 0 or 0,1,2,3
  -webhook WEBHOOK  Webhook target URL
  -image            Include image in webhook payload
  -heads            Detect heads and include in results
  -weights WEIGHTS  Model weights file path
  -sample SAMPLE    Sample rate
```
### 4. Troubleshooting
Enable debug logging to preview the bounding boxes on the images sent out in the webhooks by adding:
```
 -e LOGGING=DEBUG
```
