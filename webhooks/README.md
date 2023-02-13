# Webhooks

Plate Recognizer lets you forward the inference results to a third party. Here are examples for how to use our [webhook API](http://docs.platerecognizer.com/#webhooks).

## Starting the Webhook Server

Here are some webhook server examples. **Pick one** of the options below.

- **Python and the standard library:**

Start the server

```bash
python3 webhook_reader.py
```

- **Python and Flask:**

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

- **Javascript / Node:**

Install dependencies

```bash
npm install
```

Start the server

```bash
node server.js
```

- **C# / .Net Framework v4.8:**

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

### Connect Stream to Home Assistant

[This project](https://github.com/adamjernst/plate-handler) uses Stream webhooks to send license plate data to a home automation server. Form there, it will send a notification.

### Connect Stream to OpenEye

This project uses Stream webhooks to send license plate data to a OpenEye.

To realize the integration, it is necessary that [Camera-ID](https://guides.platerecognizer.com/docs/stream/configuration#hierarchical-configuration), present in the stream configuration in config.ini, is equal to the parameter Camera External_ID provided by OpenEye.

After modifying the config.ini, the procedures below can be executed.

**Python and Flask:**

Install flask

```bash
pip install Flask
```

Start the server

```bash
python3 file_name.py <parameter>

example:
python3 webhook_alerts_OpenEye.py --port=8001 --debug --host==0.0.0.0 --aki_token=abcdefg --aks_token=abcdefghijklmnopqrstuvxz
```

Optional parameters:

- --port
- --debug

Required parameters:

- --aki_token
- --aks_token

For external access

- --host=0.0.0.0
