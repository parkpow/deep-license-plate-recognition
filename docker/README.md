# Automatic License Plate Recognition SDK

Accurate, fast and easy to use API for license plate recognition. Trained on data from over 100 countries and regions around the world. The core of our license plate detection system is based on state of the art deep neural networks architectures.

<p align="center">
  <img src="../assets/demo.jpg">
</p>

## SDK Guide

We have launched our [On-Premise LPR SDK](https://platerecognizer.com/) that lets you run license plate recognition **locally** (no internet connection needed). Once you have [installed the SDK](https://platerecognizer.com/sdk/). You can use this command line script to interface with it. This script is a good starting point to interface the SDK with the rest of your application.

### Interfacing with the SDK

Make sure that the Docker container is running. That's the last step of the [SDK installation](https://platerecognizer.com/sdk/).

For convenience let's start by downloading a vehicle image.

```
curl -o /tmp/car.jpg https://platerecognizer.com/static/demo.jpg
```

Now let's clone the repository and read that image.

```
git clone git@github.com:marcbelmont/deep-license-plate-recognition.git
pip install requests
cd docker
python sdk_integration.py /tmp/car.jpg
```

The script outputs the license plates found in the picture as a JSON object. Feel free to edit it to your needs. If you are running the container with a different port, you can use the `--url` to set a different address. For example `--url=http://localhost:8000`.

You may also read **all the images** in a directory with: `python sdk_integration.py "/tmp/*jpg"`

---
Have questions?  [Let us know](https://platerecognizer.com/contact) how we can help.

Provided by Plate Recognizer, a subsidiary of [ParkPow](https://parkpow.com/).
