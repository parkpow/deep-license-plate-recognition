# Video Editor
Utilities for processing video with Snapshot and Blur

## Features
- [x] Extract frames as images
- [x] Visualize Plate locations and numbers (using Snapshot)
- [x] Blur Plates or Faces (using Snapshot and Platerecognizer Blur)


## Setup

1. Build the image
    ```bash
    docker build --tag platerecognizer/video-editor .

    ```
2. Update Configurations in config.ini
    Extract frames, add `[[[frames]]]` under a camera section
    ```text
    [cameras]
        [[camera-1]]
            active = yes
            url = /user-data/test.mp4
            # Extracting Frames
            [[[frames]]]


    ```
    The extracted frames will be saved in a folder named **{camera_id}_frames** in your stream folder.

    Display plates on video, add `[[[visualization]]]` under a camera section
    ```text
    [cameras]
        [[camera-1]]
            active = yes
            url = /user-data/test.mp4
            # Visualization
            [[[visualization]]]
            token = 'ddjjdkdkfjjf22333############'
            sdk_url = 'http://localhost:8080'

    ```
    A new video named **{camera_id}_visualization.avi** will be created in the folder containing your **config.ini**.
    > token is optional when using the Snapshot SDK
   
    Blur Plates and Faces in a video, add `[[[blur]]]` under a camera section
    ```text
    [cameras]
        [[camera-1]]
            active = yes
            url = /user-data/test.mp4
            # Blur
            [[[blur]]]
            blur_url = 'http://localhost:8080'

    ```
    A new video named **{camera_id}_blur.avi** will be created in your stream folder.


4. Run Image
    ```bash
    docker run --rm -t --net=host -e LOGGING=DEBUG -v /home/username/stream:/user-data platerecognizer/video-editor
   
    ```

## Run Parameters

| Arg | Default | Description |
| --- | ----------- | --------- |
| -v | **Required** | User data dir, mount point is `/user-data/` |
| -e | LOGGING=INFO | Enable more verbose logging with `DEBUG` |
