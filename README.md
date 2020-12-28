# Automatic License Plate Recognition Software (ALPR, ANPR)

<p>Get high-accuracy, developer-friendly <strong>automatic license plate recognition</strong> (<a href="https://platerecognizer.com/?utm_source=github&amp;utm_medium=website">ALPR</a>) or automatic number plate recognition (<a href="https://platerecognizer.com/?utm_source=github&amp;utm_medium=website">ANPR</a>) software!&nbsp; The core of our ALPR, ANPR system is based on state of the art deep neural networks architectures.</p>
<p>Our machine-learning software:</p>
<ul>
<li>Works on <strong>dark, low-res, blurry images</strong> and tough angles, all vehicle types, etc.&nbsp; See our full <a href="https://platerecognizer.com/alpr-results/?utm_source=github&amp;utm_medium=website">ALPR results</a>.</li>
<li>Decodes <strong>license plate</strong>, vehicle type (e.g. SUV, van, pickup truck), <a href="https://platerecognizer.com/vehicle-make-model-recognition-with-color/?utm_source=github&amp;utm_medium=website"><strong>vehicle make model</strong></a> (e.g. Honda Accord), color, and orientation.&nbsp; Ignores bumper stickers, car signs, etc.</li>
<li>Is optimized for all <a href="https://platerecognizer.com/alpr-for-usa/?utm_source=github&amp;utm_medium=website">50 USA States</a>, <a href="https://platerecognizer.com/anpr-for-india?utm_source=github&amp;utm_medium=website">India</a>, <a href="https://platerecognizer.com/anpr-for-brazil/?utm_source=github&amp;utm_medium=website">Brazil</a> and <a href="https://platerecognizer.com/countries/?utm_source=github&amp;utm_medium=website"><strong>90+ countries worldwide</strong></a>.</li>
</ul>
<p><strong>Snapshot</strong>: Get license plate reader from images in under 60 minutes:</p>
<ul>
<li>Access a <strong>simple REST API</strong> for easy integration in <a href="http://docs.platerecognizer.com/?utm_source=github&amp;utm_medium=website">8 programming languages</a>.</li>
<li>Returns results via <strong>JSON Response</strong> or Webhooks.</li>
<li>Has <a href="https://platerecognizer.com/snapshot/#speeds">fast inference speed</a> up to 21 ms.</li>
<li>Runs on-premise on <strong>Linux, Windows</strong>, Mac, Jetson<strong>, </strong><a href="https://platerecognizer.com/anpr-on-kubernetes/?utm_source=github&amp;utm_medium=website"><strong>Kubernetes</strong></a>, <a href="https://platerecognizer.com/anpr-on-raspberry-pi/?utm_source=github&amp;utm_medium=website">Raspberry Pi</a>, <a href="https://platerecognizer.com/alpr-for-xilinx-zynq/?utm_source=github&amp;utm_medium=website">Zynq</a>, <a href="https://platerecognizer.com/alpr-for-96boards/?utm_source=github&amp;utm_medium=website">96Boards</a>, <a href="https://platerecognizer.com/anpr-on-lattepanda/?utm_source=github&amp;utm_medium=website">LattePanda</a> and more.</li>
</ul>
<p><strong>Stream</strong>: Get number plate recognition from camera or video feed:</p>
<ul>
<li>Returns license plate results via <strong>CSV file</strong> or <a href="https://platerecognizer.com/alpr-webhooks/?utm_source=github&amp;utm_medium=website"><strong>Webhooks</strong></a>.</li>
<li>Handles 4 cameras simultaneously on mid-range PC.</li>
<li>Runs on-premise on <strong>Linux, Windows</strong>, Mac and <a href="https://platerecognizer.com/alpr-on-nvidia-jetson-devices/?utm_source=github&amp;utm_medium=website"><strong>Jetson</strong></a>.</li>
</ul>
<p>ALPR, ANPR software is ideal for parking, highway monitoring, toll, police surveillance, community security, and other use cases.</p>
<p>Our <a href="https://platerecognizer.com/snapshot/?utm_source=github&amp;utm_medium=website">license plate recognition (LPR)</a> software can also forward results to our full <strong>ALPR Dashboard</strong> and <a href="https://parkpow.com/?utm_source=github&amp;utm_medium=website"><strong>Parking Management software</strong></a> solution, ParkPow.</p>
<p>Sign up for a <a href="https://app.platerecognizer.com/accounts/signup/?utm_source=github&amp;utm_medium=website"><strong>Free Trial</strong></a> now (no credit card required) or <strong>learn more</strong> at <a href="https://platerecognizer.com/?utm_source=github&amp;utm_medium=website">https://platerecognizer.com</a>. &nbsp; &nbsp;</p>
<p align="center">
  <img src="assets/plate-grid.jpeg">
</p>

  - [Reading License Plates from **Images**](#reading-license-plates-from-images)
    - [Process images from an FTP server](#process-images-from-an-ftp-server)
    - [Blurring License Plates and Redaction](#blurring-license-plates-and-redaction)
    - [Benchmark](benchmark.md)
  - [Number Plate Recognition on a **Video** or Camera Stream](https://platerecognizer.com/stream/?utm_source=github&utm_medium=website)
  - [Automatic Image Transfer](#automatic-image-transfer)
  - [**Code Samples**](#code-samples)


## Reading License Plates from Images

Get your API key from [Plate Recognizer](https://platerecognizer.com/?utm_source=github&utm_medium=website). Replace **MY_API_KEY** with your API key and run the command below.

```
# Getting started!
git clone https://github.com/marcbelmont/deep-license-plate-recognition.git
cd deep-license-plate-recognition
pip install requests pillow

python plate_recognition.py --api-key MY_API_KEY /path/to/vehicle.jpg
```

The **result** includes the bounding `box`es (rectangle around object) and the `plate` value for each plate. View the details of the results on our [documentation](http://docs.platerecognizer.com/#license-plate-recognition).

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


#### Lookups For a Specific Region

You can match the license plate patterns of a specific region.

`python plate_recognition.py --api-key MY_API_KEY --regions fr --regions it /path/to/car.jpg`



#### Process Multiple Files (Batch Mode)

You can also run the license plate reader on many files at once. To run the script on all the images of a directory, use:

`python plate_recognition.py --api-key MY_API_KEY /path/to/car1.jpg /path/to/car2.jpg /path/to/trucks*.jpg`


#### Running the ALPR Locally (SDK)

To use a locally hosted sdk, pass the url to the docker container as follows:

`python plate_recognition.py  --sdk-url http://localhost:8080 /path/to/vehicle.jpg`

<br><br><br>

### Blurring License Plates and Redaction

The script `number_plate_redaction.py` differs from the default prediction script because it also detects plates that are **barely readable** and/or very small. It returns the bounding boxes of all the license plates. They can be used to blur or mask the license plates.

In addition, it can **split the image** in smaller images to better deal with high resolution images. This will use **3 lookups** instead of just 1. To use this options add `--split-image`.

The option `--save-blurred` lets you save blurred images. They are saved to a new file with `_blurred` suffix.

The option `--ignore-regexp` lets you specify a regex of plates to ignore from blur. This option can be specified multiple times.

The option `--ignore-no-bb` lets you ignore recognitions without a vehicle bounding box from blur.

```
python number_plate_redaction.py --help
python number_plate_redaction.py --api-key API_KEY vehicels.jpg
python number_plate_redaction.py --sdk-url http://localhost:8080 --split-image vehicels.jpg

python number_plate_redaction.py --api-key 77c### 58C5A57_14965463.jpg --save-blurred --ignore-regexp ^58c5a57$ --ignore-regexp ^[0-9][0-9]c5a57$

```

<br><br><br>

### Process images from an FTP server

To process images from the FTP server run `ftp_processor` script:

`python ftp_processor.py --api-key MY_API_KEY --ftp-host hostname --ftp-user user --ftp-password password --folder /path/to/server_folder`

To remove images from FTP server after processing, add the argument `--delete`.

<br><br><br>

## Automatic Image Transfer

Automatic Image Transfer is a command line tool that runs our [ALPR Engine](https://platerecognizer.com). It **monitors a folder** and automatically process images (Cloud or SDK) as they are added. Once processed, images are moved to an archive directory. It can also **forward the results** to our parking management service [Parkpow](https://parkpow.com/?utm_source=github&utm_medium=website).

To get started: `python transfer.py --help`

<br><br><br>

## Code Samples

See our sample projects to easily get started with the API.
- Example program in [C++](cpp/).
- Example program in [C#](csharp/).
- Example program in [Java](java/).
- [Android App](https://github.com/parkpow/alpr-anpr-android). It lets you take a picture and send it to our API.
- View how to integrate with other languages in our [documentation](http://docs.platerecognizer.com/#introduction).
- A Node-RED node for [license plate recognition](https://github.com/parkpow/node-red-contrib-plate-recognizer).

<br><br><br>

---
Have questions?  [Let us know](https://platerecognizer.com/contact?utm_source=github&utm_medium=website) how we can help.

Provided by Plate Recognizer, a subsidiary of [ParkPow](https://parkpow.com/?utm_source=github&utm_medium=website).
