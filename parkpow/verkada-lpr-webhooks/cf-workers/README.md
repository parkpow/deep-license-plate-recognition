# verkada-lpr-webhooks

## Deployment steps
> The cloudflare account needs to have a paid plan for workers to be able to create queues

1. Create a [Cloudflare queue](https://developers.cloudflare.com/queues/get-started/#3-create-a-queue) that will hold webhook messages.
Can be done by using below command or manually in the dashboard
```shell
npx wrangler queues create <MY_FIRST_QUEUE>
```

2. Deploy the worker by running below command
> this will prompt you to login the first time

A url will be generated to be used as the webhook target on Verkada API settings page
```shell
npm run deploy
```

3. Update the application env variables with the following values
> This will redeploy the worker and persist any future deployments
> For added security, Click on the Encrypt button on each variable

```shell
# Verkada API Key
VERKADA_API_KEY=
# ParkPow Token - Find it here https://app.platerecognizer.com/products/parkpow/
PARKPOW_TOKEN=
# ParkPow Server URL - Optional (You don't need to define it if you use ParkPow Cloud; otherwise, declare it with the ParkPow On-Premise URL).
PARKPOW_URL=

```
4. Run below command to get realtime logs
```shell
npm run logs
```

## Local development
- Create a `.dev.vars` with the env variables required
- Run `npm run dev` in your terminal to start a development server
- Open a browser tab at http://localhost:8787/ to see your worker in action

