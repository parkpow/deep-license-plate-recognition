# Serve USB Camera Streaming for Windows OS

This script allows you to create a server to access a USB camera from a Stream.

You serve your camera streaming from the host OS, which a Stream Docker container can then access.

# Requirements

To create the HTTP server:
**Flask==3.0.1**

To serve the Flask app feed:
**waitress==2.1.2**

To handle the camera feed:
**opencv-python==4.9.0.80**

To list all the USB cameras connected and let you decide what you want to use (in case you have more than one):
**pygrabber==0.2**

# Running the Server

`waitress-serve --host=0.0.0.0 --port=5000 http_video_server:app`

### Console output example:
```
ID | Name
---|--------------------------------
 0 | c922 Pro Stream Webcam
 1 | screen-capture-recorder
 2 | AMD Privacy View camera
 3 | OBS Virtual Camera

Introduce the ID of the device camera you want to serve video from:
```

Once you introduce the device ID it will be served.

```
selected id: 0
INFO:waitress:Serving on http://0.0.0.0:5000
```

### Testing

Use a media player to see your USB camera transmission, select a connect to a network location option and introduce the server url: http://0.0.0.0:5000/video_feed

To connect to Stream, introduce this server url in the `config.ini` file camera configuration, i.e.:

```
...
[[camera-1]]
    active = yes
    url = http://0.0.0.0:5000/video_feed
    # Save to CSV file. The corresponding frame is stored as an image in the same directory.
    # See more formats on https://guides.platerecognizer.com/docs/stream/configuration#output-formats
    csv_file = $(camera)_%y-%m-%d.csv
...
```

