FROM python:3.11-slim

WORKDIR /app

# Install cron and other dependencies
RUN apt-get update && apt-get install -y --no-install-recommends cron && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Give execution rights to the entrypoint script
RUN chmod +x /app/entrypoint.sh



# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
