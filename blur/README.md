# Blur

View the [documentation](https://guides.platerecognizer.com/docs/blur/video-utils).

# Persons Detector
Detect person in video file or live camera feed.
When a person is detected, send a webhook similar to Snapshot Cloud in real time.

## Setup
1. Build the image
First [download weights](https://drive.google.com/file/d/1liPJnM2MAVhdzlUpJjm8xfZ99Gk_Nokl/view?usp=sharing) into this directory then build docker image.
```bash
docker build --tag platerecognizer/blur .

```

2. Run Image
Example usage of processing platerecognizer demo rtsp and sending events to webhook.site
```
docker run --rm --net=host -t -v /tmp/test-images:/images platerecognizer/blur --images=/images --blur-url=http://localhost:5000

```
