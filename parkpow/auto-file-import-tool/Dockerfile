FROM python:3.11-slim

WORKDIR /app

# Install cron and other dependencies
RUN apt-get update && apt-get install -y cron

# Copy application code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Give execution rights to the entrypoint script
RUN chmod +x /app/entrypoint.sh



# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
