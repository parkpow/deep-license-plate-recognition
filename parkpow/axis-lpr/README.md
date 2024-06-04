# AXIS LPR Camera EVENTS to ParkPow
Forward LPR data from Axis camera to ParkPow

1. Build the image
    ```bash
    docker build --tag parkpow-axis-lpr .
    ```
2. Run the image with ParkPow url and token
    ```bash
     docker run --rm -t -p 5000:5000 -e PP_URL=https://myparkpow.com -e TOKEN=1234 parkpow-axis-lpr
    ```
