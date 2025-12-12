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
