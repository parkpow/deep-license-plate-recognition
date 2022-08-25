# Webhooks

Plate Recognizer lets you forward the inference results to a third party. Here are examples for how to use our [webhook API](http://docs.platerecognizer.com/#webhooks).

## Starting the Webhook Server

Here are some webhook server examples. **Pick one** of the options below.

- __Python and the standard library:__

Start the server
```bash
python3 webhook_reader.py
```

- __Python and Flask:__

Install flask
```bash
pip install Flask==1.1.2
```
Start the server
```bash
export FLASK_APP=app.py
export FLASK_DEBUG=1
python3 -m flask run -h 0.0.0.0 -p 8001
```

- __Javascript / Node:__

Install dependencies
```bash
npm install
```
Start the server
```bash
node server.js
```

- __C# / .Net Framework v4.8:__

Install [this NuGet package](https://github.com/Http-Multipart-Data-Parser/Http-Multipart-Data-Parser) required for MultiPart Parsing
```shell
PM> Install-Package HttpMultipartParser
```
Build Solution and Run WebhookReader.exe as a Console Application

## Sending Data to the Webhook Server

1. Find your machine local IP for example 192.168.0.206. You can use `ifconfig` to get it.
2. Send an example webhook to the server. If it is running correctly, it should exit without an error.

```shell
docker run -e URL=http://MY_IP_ADDRESS:8001 platerecognizer/webhook-tester
```
1. Configure the webhook on Platerecognizer.
   - In Stream, edit your `config.ini`, add the following to a camera: `webhook_target = http://MY_IP_ADDRESS:8001/`
   - For Snapshot, open [Webhooks Configuration](https://app.platerecognizer.com/accounts/webhooks/).

## Integrations

- [Connect Stream to Home Assistant](https://github.com/adamjernst/plate-handler). This project uses Stream webhooks to send license plate data to a home automation server. Form there, it will send a notification.
