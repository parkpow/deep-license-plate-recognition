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

2. Update the application env variables with the following values
> This will redeploy the worker and persist any future deployments
> For added security, Click on the Encrypt button on each variable

```shell
# Snapshot Cloud Token - Find it here https://app.platerecognizer.com/service/snapshot-cloud/
SNAPSHOT_TOKEN=
# Snapshot API URL - Optional (You don't need to define it if you use Snapshot Cloud
SNAPSHOT_URL=
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
  	curl -vX POST http://localhost:8787/ -d @test/Survision.txt --header "Content-Type: application/json" --header "survision-serial-number: sv1-searial-1"
    curl -vX POST http://localhost:8787/ -d @test/Genetec.txt --header "Content-Type: application/json"
    ```
