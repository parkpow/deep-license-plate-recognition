
## Middlewares

Refer to [this guide](https://guides.platerecognizer.com/docs/stream/integrations/middleware) to get started with the middlewares.

## How to Run

1. **Build the Docker Image**:
   ```bash
   docker build -t webhook-middleware .

2. **Run the Docker Container**:
   ```bash
   docker run --env-file .env -p 8002:8002 webhook-middleware
   ```