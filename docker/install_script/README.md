## Automatic Stream installation script

The provided shell script (stream.sh) is tailored to facilitate the seamless setup and operation of an on-premise P Stream on your system. This script dynamically verifies the presence of Docker and installs it if it is not already available.

Subsequently, the script orchestrates the configuration and launch of Stream, incorporating defaults. By default, it designates the script execution location as the foundational directory, creating a dedicated "stream" folder to house default configuration files and the outputs of the Stream.

The Docker container instantiated by the script is denoted as "stream" and is configured to restart automatically unless intentionally halted. Additionally, the Stream is set up to commence automatically upon system boot, ensuring a seamless and persistent integration into your system environment.


### Prerequisites
 - Administrator permissions or membership in the docker group.
 - Supported system architectures: Linux Debian or Ubuntu (x86_64), Raspberry pi (armv7l, aarch64, armv7hf).

### Docker Image

The script pulls the Plate Recognizer Stream Docker image based on your system's architecture.

-  x86_64 architecture: platerecognizer/alpr-stream
-  ARM architectures (armv7l, aarch64, armv7hf): platerecognizer/alpr-stream:raspberry
Running the Stream


### Usage
Run the script with the following parameters:
```bash

./stream_setup.sh [-t=YOUR_TOKEN] [-l=YOUR_LICENSE_KEY]
```
#### Parameters:

- `-t, --token` - [Stream License Token](https://app.platerecognizer.com/products/stream/).
- `-l, --license_key` - [Stream License Key](https://app.platerecognizer.com/products/stream/).

If the parameters are not provided, the script will interactively prompt you to enter the token and license key.

#### Unique command:

Use the following command to download and run the script in one step. It facilitates the automation of installations in larger scripts or automated environments, such as virtual machine provisioning or containerized environments.

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/parkpow/deep-license-plate-recognition/script-Install-stream/docker/master/stream.sh)" -- -t=YOUR_TOKEN -l=YOUR_LICENSE_KEY
```

### Example Usage:


```bash 
bash ./stream_setup.sh 
```

```bash 
bash ./stream_setup.sh -t=YYYYYYYYYYYYY -l=XXXXXXXXXXXXXXX 
```

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/parkpow/deep-license-plate-recognition/script-Install-stream/docker/master/stream.sh)" -- -t=YYYYYYYYYYYYYYYYYYYYYYYYYYYYY -l=XXXXXXXXXX

```


