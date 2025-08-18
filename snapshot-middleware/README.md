# Snapshot Middleware
Format external requests into expected format by Snapshot then forward

Supported Source:
- Survision Camera
- Genetec Camera

## Deployment steps
1. Deploy the worker by running below command
> this will prompt you to login using your web browser the first time.

A url will be generated to be used as the webhook target on source such as a camera settings page
```shell
npm run deploy
# Deploy with a custom name
npm run deploy -- --name reimaginedparking-middleware
```
To login again `wrangler login`, Logout using `wrangler logout` or delete `.wrangler` folder
> Login command if wrangler is not installed globally `./node_modules/.bin/wrangler login`

2. Update the application env variables with the following values
> This will redeploy the worker and persist any future deployments
> For added security, Click on the Encrypt button on each variable


### Secrets
```shell
# Snapshot Cloud Token - Find it here https://app.platerecognizer.com/service/snapshot-cloud/
SNAPSHOT_TOKEN=
PARKPOW_TOKEN=
```

### Texts
```shell
# Snapshot API URL - Optional (You don't need to define it if you use Snapshot Cloud
SNAPSHOT_URL=
PARKPOW_URL=
SNAPSHOT_RETRY_LIMIT=5
PARKPOW_RETRY_LIMIT=5
RETRY_DELAY=2000

```

The worker can also be controlled using GET params
- `processor_selection` - Specify **source camera ID** that will be used for processing instead of detecting from request format
- `overwrite_plate` - Overwrite Snapshot `plate` with camera response before forwarding to ParkPow
- `overwrite_direction` - Overwrite Snapshot `direction` with camera response before forwarding
- `overwrite_orientation` - Overwrite Snapshot `orientation` with camera response before forwarding
- `parkpow_forwarding` - Enable ParkPow forwarding. This is also automatically enabled if you use any `overwrite_*` params or `parkpow_camera_ids`.
- `parkpow_camera_ids` - Duplicate same Snapshot results on ParkPow using different cameraIds. E.g `parkpow_camera_ids=camera_out,camera2_in`

**Source Camera IDs**:
```plaintext
SURVISION = 1
GENETEC = 2
```

3. To log errors with Rollbar, Deploy the tail worker
```shell
npm run deploy:rollbar
```
The set this env variable
```shell
# Rollbar Token for Error logging
ROLLBAR_TOKEN=
```

4. Run below command to get realtime logs
```shell
npm run logs
```

## Local development
- Create a `.dev.vars` with the env variables required:
```dotenv
SNAPSHOT_TOKEN=
SNAPSHOT_URL= # Optional
ROLLBAR_TOKEN= # optional
```
- Run `npm run dev` in your terminal to start a development server
- Open a browser tab at http://localhost:8787/ to see your worker in action
- Test with curl
    ```shell
  	curl -vX POST http://localhost:8787/ -d @test/assets/Survision.json --header "Content-Type: application/json" --header "survision-serial-number: sv1-searial-1"
    curl -vX POST http://localhost:8787/ -d @test/assets/Genetec.json --header "Content-Type: application/json"
    ```
