#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import argparse
import csv
import io
import json
import os
import time

import cv2
import requests
from PIL import Image
import uuid
from datetime import datetime




def parse_arguments():
    parser = argparse.ArgumentParser(
        description=
        'Read license plates from a RTSP stream and save the result in a CSV file.',
        epilog=
        'For example: anpr_camera_stream.py --camera rtsp://192.168.1.2:8080/out.h264 --api-key TOKEN --regions fr --output /path/to/output.csv'
    )
    parser.add_argument('--api-key', help='Your API key.', required=True)
    parser.add_argument('--camera', help='RTSP stream url.', required=True)
    parser.add_argument('--regions', help='Regions e.g fr.', required=False)
    parser.add_argument('--output', help='csv output file ', required=True)
    
    return parser.parse_args()

def main():
    args = parse_arguments()


    cap = cv2.VideoCapture(args.camera)
    
    with open(args.output, 'w') as output:
        fields = ['date', 'license_plate', 'score', 'dscore', 'vehicle_type']
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        while(cap.isOpened()):
            
            ret, frame = cap.read()
            print("frame")
            print(frame)

            imgByteArr = io.BytesIO()
            im = Image.fromarray(frame)
            im.save(imgByteArr, 'JPEG')
            cv2.waitKey(1)
            imgByteArr.seek(0)
            response = requests.post(
                'https://api.platerecognizer.com/v1/plate-reader/',
                files=dict(upload=imgByteArr),
                data=dict(regions=args.regions or ''),
                headers={'Authorization': 'Token ' + args.api_key})  
            res = response.json()
            if len(res['results']) > 0:
                for result in res['results']:
                        data = dict(
                            date=datetime.today().strftime('%x %X'),
                            license_plate = result['plate'],
                            score = result['score'],
                            dscore = result['dscore'],
                            vehicle_type = result['vehicle']['type']
                        )
                        writer.writerow(data)
        cap.release()
        cv2.destroyAllWindows()    


if __name__ == "__main__":
    main()