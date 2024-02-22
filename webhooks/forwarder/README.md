# Webhook Forwarder
Modify and Forward Webhook Events from Stream or Snapshot to a Destination such as VMS(Video Management Systems)

### Supported Destination
| Destination                                                               | Command   |
|---------------------------------------------------------------------------|-----------|
| [Salient CompleteView](https://www.salientsys.com/products/completeview/) | `salient` |
| NX VMS                                                                    | `nx`      |

## Setup
1. Build the image
    ```bash
    docker build --tag platerecognizer/webhook-forwarder .
    ```

2. Create container from Image and start
    ```bash
    docker run --rm -t --net=host platerecognizer/webhook-forwarder [destination] [destination arguments]
    ```
   Add `-h` and `--help` for info on arguments

3. Configure Stream to forward Webhook events:
    ```text
    webhook_targets = http://localhost:8001
    ```
    > Restart Stream after config changes,
    You might need to run Stream with `--net=host` too for the Webhook target to be reachable

   You can also test with [Webhook Tester](/)

5. Configuration examples
   1. Forwarding to **NX VMS**
   ```shell
   docker run --rm -t --net=host platerecognizer/webhook-forwarder nx --username=admin --password=39393jdhhdiisu2 --vms='http://192.168.100.6:4502' --camera="9ee7046b-0ab3-49cd-908f-eb293fdc1e3f"
   ```
   2. Forwarding to **Salient CompleteView**
   ```shell
    docker run --rm -t --net=host platerecognizer/webhook-forwarder salient --username=admin --password=39393jdhhdiisu2 --vms='http://192.168.100.6:4502' --camera="9ee7046b-0ab3-49cd-908f-eb293fdc1e3f"
   ```

> Enable Debug logging by including `-e LOGGING=DEBUG` when starting the container