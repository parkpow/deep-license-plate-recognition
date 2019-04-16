# Automatic License Plate Recognition API

Accurate, fast and easy to use API for license plate recognition. Trained on data from over 100 countries and regions around the world. The core of our license plate detection system is based on state of the art deep neural networks architectures.

Integrate with our ALPR API in a few lines of code. Get an easy to use JSON response with the number plate value of vehicles and the bounding boxes.

<p align="center">
  <img src="assets/demo.jpg">
</p>

## Reading license plates from images

Get your API key from [Plate Recognizer](https://platerecognizer.com/). Replace **MY_API_KEY** with your API key and run the following command:

```
pip install requests
python plate_recognition.py --api MY_API_KEY /path/to/vehicle.jpg
```

The result includes the bounding `box`es (rectangle around object) and the `plate` value for each plate. The JSON output can easily be consumed by your application.

```javascript
[
  {
    "version": 1,
    "results": [
      {
        "box": {
          "xmin": 85,
          "ymin": 85,
          "ymax": 211,
          "xmax": 331
        },
        "plate": "ABC123",
        "score": 0.904,
        "dscore": 0.92
      }
    ],
    "filename": "car.jpg"
  }
]
```


### Process all the files in a directory, batch mode

You can also run the license plate reader on many files at once. To run the script on all the images of a directory, use:

`python plate_recognition.py --api MY_API_KEY "/path/to/car-*.jpg"`

Or to process multiple directories at once, do:
`python plate_recognition.py --api MY_API_KEY "/path/*/*.jpg"`


## [Running ALPR locally with the SDK](docker/)

## Number plate recognition on a video

To do ANPR on videos, you will also need to install OpenCV. Here are the [installation](https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_setup/py_setup_in_windows/py_setup_in_windows.html) instructions. Those 2 python packages are also needed:

```
pip install requests
pip install pillow
```

The script `alpr_video.py` lets you perform license plate recognition on a video file. It looks at each frame of the video and reads license plates. If you are only interested in one part of the video, you may use the `--start` and `--end` arguments. Additionally, you can use the `--skip` argument to read 1 in every N frames. It will speed up the analysis of large videos. Here's an example:

`python alpr_video.py --api MY_API_KEY --start 900 --end 2000 --skip 3 /path/to/cars.mp4`

OpenCV is also capable of reading live video streams. See this [page](https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_gui/py_video_display/py_video_display.html) for an example.

---
Have questions?  [Let us know](https://platerecognizer.com/contact) how we can help.

Provided by Plate Recognizer, a subsidiary of [ParkPow](https://parkpow.com/).
