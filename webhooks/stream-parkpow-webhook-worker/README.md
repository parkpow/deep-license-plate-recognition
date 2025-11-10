# Stream → ParkPow Webhook Proxy (Cloudflare Worker)

Cloudflare Worker that acts as a proxy for forwarding webhooks from Hertz's Stream to ParkPow system.

---

## Development

### 1. Install Dependencies

```sh
pnpm install
```

### 2. Configure Environment Variables

Set the following in your [wrangler.jsonc](./wrangler.jsonc):

```jsonc
  "env": {
    "STREAM_TOKEN": "your_stream_token",
    "PARKPOW_TOKEN": "your_parkpow_token",
    "PARKPOW_ENDPOINT": "https://app.parkpow.com/api/v1/webhook-receiver/"
  }
```

### 3. Development

Start a local worker:

```sh
wrangler dev
```

### 4. TDD

Run the test suite (watch mode):

```sh
vitest
```

### 5. Deployment

Deploy to Cloudflare Workers:

```sh
wrangler deploy
```

Edit the secrets on cloudlflare dashboard or use:

```sh
wrangler secret put STREAM_TOKEN
wrangler secret put PARKPOW_TOKEN
```

### 6. Testing

Use the webhook with stream:

```ini
    webhook_targets = cloudflare

[webhooks]

  [[cloudflare]]
    url = https://stream-parkpow-webhook-worker.ky-c08.workers.dev/
    header = Authorization: Token <YOUR_STREAM_TOKEN>
    caching = no
    image = yes
    image_type = vehicle
    request_timeout = 20
```

---

## How It Works

- **Incoming Request**: The worker listens for POST requests from Stream.
- **Authentication**: Validates the `Authorization` header against `STREAM_TOKEN`.
- **Forwarding**: Forwards the request to ParkPow, replacing the authorization header with `PARKPOW_TOKEN`.
- **Multipart Support**: Handles both JSON and multipart/form-data bodies, preserving binary data integrity.
- **Error Handling**: Returns clear error responses for authentication failures, missing configuration, or network issues.

---

## 📦 Tooling & Configuration

- **biome.json**: Code formatting and linting.
- **tsconfig.json**: TypeScript configuration.
- **vitest.config.mts**: Vitest setup for Cloudflare Workers.
- **wrangler.jsonc**: Cloudflare deployment config.
- **.vscode/settings.json**: Editor enhancements.

---

## 📚 References

- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [ParkPow Webhook Docs](https://guides.platerecognizer.com/docs/parkpow/integrations#webhook)
- [Hono Framework](https://hono.dev/)
