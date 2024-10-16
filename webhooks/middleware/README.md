
## Middlewares

### REST Protocol Middleware

**Description**: Forwards webhook data to a REST service.

**Required Environment Variables**:
- `MIDDLEWARE_NAME=synology_rest`
- `REST_SERVICE_URL`: The URL of the REST service.

### Crop Plate and Forward Middleware

**Description**: Crops an image from webhook data and forwards the original and cropped images to another webhook endpoint.

**Required Environment Variables**:
- `MIDDLEWARE_NAME=crop_plate`
- `WEBHOOK_URL`: The URL of the webhook endpoint where data is forwarded.

### Salient/CompleteView VMS Middleware

**Description**: Forwards Stream Webhook Events to a CompleteView/Salient VMS as Events.

**Required Environment Variables**:
- `MIDDLEWARE_NAME=salient`
- `VMS_USERNAME`: Username for Salient VMS.
- `VMS_PASSWORD`: Password for Salient VMS.
- `VMS_API_URL`: API endpoint for Salient VMS.
- `CAMERA_UID`: UID of the camera used as the source of events.

### OpenEye Middleware

**Description**: Forwards parsed JSON data to the OpenEye monitoring API.

**Required Environment Variables**:
- `MIDDLEWARE_NAME=openeye`
- `AKI_TOKEN`: AKI token for authentication.
- `AKS_TOKEN`: AKS token for authentication.

### NX Middleware

**Description**: Manages a session with NX server, retrieves tags from the Parkpow API, and creates bookmarks in a server using the REST API.

**Required Environment Variables**:
- `MIDDLEWARE_NAME=nx`
- `SERVER_HOST`: Host URL of the server.
- `LOGIN`: Username for server login.
- `PASSWORD`: Password for server login.
- `SSL`: Boolean value for enabling SSL verification (e.g., `True` or `False`).
- `PARKPOW_TOKEN`: Token for accessing Parkpow API.
- `TAG`: Tag used for filtering in Parkpow API.

`list.csv` file should be present in the root directory of the project.

### SOAP Protocol Middleware

**Description**: Forwards webhook data to a SOAP service.

**Required Environment Variables**:
- `MIDDLEWARE_NAME=soap`
- `SOAP_SERVICE_URL`: The URL of the SOAP service.
- `SOAP_USER`: Username for SOAP service authentication.
- `SOAP_SERVICE_KEY`: Key for SOAP service authentication.

## How to Run

1. **Build the Docker Image**:
   ```bash
   docker build -t webhook-middleware .

2. **Run the Docker Container**:
   ```bash
   docker run --env-file .env -p 8002:8002 webhook-middleware
   ```