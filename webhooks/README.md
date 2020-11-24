# Webhooks

Plate Recognizer lets you forward the inference results to a third party. Here are examples for how to use our [webhook API](http://docs.platerecognizer.com/#webhooks).

## Instructions

First start your desired webhook server:

## 1. webhook_reader.py
### Start the server
```bash
python3 webhook_reader.py
```

## 2. webhook_reader_flask.py
### Install flask
```bash
pip install Flask==1.1.2
```
### Start Server
```bash
export FLASK_APP=app.py
export FLASK_DEBUG=1
python3 -m flask run -h 0.0.0.0 -p 8001
```

## 3. webhook_reader.js
### Install dependecies
```bash
npm install
```
### Start Server
```bash
node server.js
```

## Testing

1. Try the command below to check if the server is running correctly. Change car.jpg to a local file:
   - `curl -F 'json={"field": "value"}' -F 'upload=@car.jpg' http://localhost:8001/`

2. Find your machine local IP for example 192.1.0.206. You can use `ifconfig` to get it.
3. Configure the webhook on Platerecognizer.
   - In Stream, edit your `config.ini`, add the following to a camera: `webhook_target = http://MY_IP_ADDRESS:8001/`
   - For Snapshot, open [Webhooks Configuration](https://app.platerecognizer.com/accounts/webhooks/).
