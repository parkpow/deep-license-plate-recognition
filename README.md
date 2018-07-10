# Automatic License Plate Recognition API

Accurate, fast and easy to use API for license plate recognition. Trained on data from over 100 countries and regions around the world. The core of our license plate detection system is based on state of the art deep neural networks architectures.

Integrate with our ALPR API in a few lines of code and get an easy to use JSON response with the number plate value of vehicles.

### Getting started

Get your API key from [Plate recognizer](https://platerecognizer.com/). Replace MY_API_KEY with your API key and run the following command:


```
pip install requests
python plate_recognition.py --api MY_API_KEY /path/to/vehicle.jpg
```

The result includes the bounding boxes (rectangle around object) and the `plate` value for each detected plate.

```python
{'filename': '11_17_00007_110610.jpg',
 'results': [{'box': {'xmax': 355,
                        'xmin': 69,
                        'ymax': 209,
                        'ymin': 79},
               'dscore': 0.623,
               'plate': 'ABC123',
               'score': 0.903}],
 'version': 1}
```
