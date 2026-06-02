# FRONT-REAR MIDDLEWARE PROTOCOL

## How to run

- SSH to the test server where the middleware is hosted.
- `cp .env.sample .env` and edit the `.env` file to include:

  ```ini
  MIDDLEWARE_NAME=front_rear
  STREAM_API_TOKEN=<stream_token>
  ```

- Configure [front_rear_config.json](./config/front_rear_config.json) as needed.
- Run `docker compose -f docker-compose.caddy.yml up -d --build` to start the middleware with Caddy server.
- check the logs with `docker compose -f docker-compose.caddy.yml logs -f`.
- When you see `"msg":"host is up"` in the caddy logs, the middleware is ready to accept requests.
- Stop with `docker compose -f docker-compose.caddy.yml down`.

Configuration changes are picked up automatically without needing to restart the middleware.

## Monitoring endpoints

All endpoints require an `Authorization: Token <ADMIN_TOKEN>` header (set `ADMIN_TOKEN` in `.env`), except `/health`.

### `GET /health`

Returns the middleware liveness status. No authentication required.

```json
{"status": "healthy", "middleware": "front_rear"}
```

Returns `503` if the middleware failed to load.

### `GET /logs`

Streams the middleware log file in real-time (like `tail -f`).

| Query param | Description |
|---|---|
| `?tail[=N]` | Return the last N lines (default 50) as a static response instead of streaming |
| `?lines=N` | Streaming only: replay the last N lines before following (default 50) |

```bash
# Live stream
curl -H "Authorization: Token <ADMIN_TOKEN>" https://<host>/logs

# Static snapshot of last 50 lines
curl -H "Authorization: Token <ADMIN_TOKEN>" https://<host>/logs?tail

# Static snapshot of last 100 lines
curl -H "Authorization: Token <ADMIN_TOKEN>" https://<host>/logs?tail=100
```
