# Video Editor Utility

Below are utilities for processing video with Snapshot and Blur.

## Prerequisites

### Run Blur

```
docker run -it \
  --net=host \
  -p 8001:8001 \
  -e SDK_URL='http://localhost:8080' \
  -e LOGGING=DEBUG \
  -e TOKEN=<YOUR_TOKEN> \
  -e LICENSE_KEY=<YOUR_API_KEY> \
  -e SERVER=1 \
  -e BLUR=1 \
  platerecognizer/skew-correction
```

Click [here](/docs/blur/configuration.md) for additional Blur configurations.

### Run Snapshot SDK

```
docker run --restart="unless-stopped" -t \
  -p 8080:8080 \
  -v license:/license \
  -e TOKEN=<YOUR_TOKEN> \
  -e LICENSE_KEY=<YOUR_API_KEY> \
  platerecognizer/alpr
```

Click [here](/docs/snapshot/getting-started) for additional Snapshot configurations.

### Build Video-Editor Image

The source code for the utilities is available [here](https://github.com/parkpow/deep-license-plate-recognition/tree/master/video-editor), make sure you are in your working directory and download all files. Once you downloaded the video-editor files, you are ready to build the docker image from inside your working directory like below:

```bash
git clone --depth 1 https://github.com/parkpow/deep-license-plate-recognition.git
cd deep-license-plate-recognition/video-editor
docker build --tag platerecognizer/video-editor .
```

## Features

The utilities work by creating a `config.ini` in your working directory, which must have a [similar format](/docs/stream/configuration) to the one used by Stream.

### Extract Frames as Images
Add `[[[frames]]]` under a camera section
```ini
[cameras]
    [[camera-1]]
        active = yes
        url = /user-data/test.mp4
        # Extracting Frames
        [[[frames]]]
```
The extracted frames will be saved in a folder named **{camera_id}_frames** in the folder containing your **config.ini**.

### Draw Vehicle and Plate Bounding Boxes
This works by uploading every frame in the video to [Snapshot](/docs/snapshot/getting-started).  
Visualize plates and vehicles on a video, add `[[[visualization]]]` under a camera section
```ini
[cameras]
    [[camera-1]]
        active = yes
        url = /user-data/test.mp4
        # Visualization
        [[[visualization]]]
        token = 'ddjjdkdkfjjf22333############'
        sdk_url = 'http://localhost:8080'
```
A new video named **{camera_id}_visualization.avi** will be created in your Stream folder.
> Token is optional if using the Snapshot SDK.

### Blur Plates and Faces 
This works by uploading every frame in the video to the [Blur](/docs/blur/getting-started).  
To blur plates and faces in a video, add `[[[blur]]]` under a camera section
```ini
[cameras]
    [[camera-1]]
        active = yes
        url = /user-data/test.mp4
        # Blur
        [[[blur]]]
        blur_url = 'http://localhost:8080'
```
A new video named **{camera_id}_blur.avi** will be created in your Stream folder.

## Processing The Video File

Once you adapted your `config.ini` file according to the video editing feature you want to use, run the following command:

```
docker run --rm -t --net=host -v /home/username/stream:/user-data platerecognizer/video-editor
```
#### Command Parameters

| Argument | Default | Description |
| -------- | ----------- | --------- |
| -v | **Required** | User data dir, the mount point is `/user-data/` |
| -e | LOGGING=INFO | Enable more verbose logging by adding `LOGGING=DEBUG` |

