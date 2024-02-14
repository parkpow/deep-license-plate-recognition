# CSV Upload Utility

Add upload configs for each camera


```shell
export -e LOGGING=DEBUG
docker build --tag platerecognizer/stream-csv-upload .

docker run --rm -t --net=host -e LOGGING=DEBUG -v /home/danleyb2/stream-PCSXNrwwbF:/user-data platerecognizer/stream-csv-upload

-a http://localhost:8000 -t 4b52bd5b7099bda158a608bb33edf0ecfdf5f160 -c camera1 /home/danleyb2/stream-PCSXNrwwbF


docker run --rm --net=host -t -e LOGGING=DEBUG -v $(pwd):/app  -v /home/danleyb2/stream-PCSXNrwwbF:/user-data platerecognizer/stream-csv-upload

```

View the [documentation](https://guides.platerecognizer.com/docs/parkpow/csv-upload).
