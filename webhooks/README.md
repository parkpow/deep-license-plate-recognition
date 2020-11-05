# Webhooks

Plate Recognizer lets you forward the inference results to a third party. Here are examples for how to use our [webhook API](http://docs.platerecognizer.com/#webhooks).

## Instructions

1. Start the server with: `python3 webhook_reader.py`
   - Try the command below to check if the server is running correctly. Change car.jpg to a local file:
   - `curl -F 'json={"field": "value"}' -F 'upload=@car.jpg' http://localhost:8001/`
2. Find your machine local IP for example 192.1.0.206. You can use `ifconfig` to get it.
3. Configure the webhook on Platerecognizer.
   - In Stream, edit your `config.ini`, add the following to a camera: `webhook_target = http://192.168.0.206:8001/`
   - For Snapshot, open [Webhooks Configuration](https://app.platerecognizer.com/accounts/webhooks/).
