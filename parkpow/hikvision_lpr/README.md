# Hikvision LPR Camera EVENTS to ParkPow
Forward LPR data from Hikvision camera to ParkPow

1. Build the image
```bash
docker build --tag parkpow-hikvision-lpr .
```

2. Run the image
```bash
 docker run --rm -t -p 5000:5000 -e PP_URL=https://myparkpow.com -e TOKEN=1234 parkpow-hikvision-lpr
```

3. Enable **SDK Listening** on camera
Set IP address and Port to point to this server by following below guide on page 35
https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000013642/S000000180/S000000181/OFR000261/M000078840/User_Manual/UD35644B_Baseline_Intelligent-Entrance-ANPR-Camera_User-Manual_V5.0.4_20231106.PDF

4. Running Tests
```bash
export PP_URL=https://myparkpow.com
export TOKEN=1234
python -m pytest

```