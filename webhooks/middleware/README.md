
## Middlewares

Refer to [this guide](https://guides.platerecognizer.com/docs/stream/integrations/middleware) to get started with the middlewares.

## How to Run

1. **Build the Docker Image**:
   ```bash
   docker build -t webhook-middleware .

2. **Run the Middleware**:
   - If your stream service is already running and you want just the middleware to run:

   ```bash
   docker run --env-file .env -p 8002:8002 webhook-middleware
   ```

   - If your stream service is not running and you want to run both the middleware and the stream service:
   ```bash
   docker-compose up
   ```
   **Environment Variables Setup:**
   Make sure to set the required environment variables in the `.env` file. A sample `.env` file is provided in the repository.

   In addition to the standard variables, you need to set these specific variables for the middleware to run using docker-compose:
   ```
   STREAM_LICENSE_KEY=your_license_key_here
   STREAM_API_TOKEN=your_api_token_here
   ```
