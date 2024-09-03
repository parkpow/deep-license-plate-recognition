FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY consumer.py ./
COPY middlewares ./middlewares

# Set the entrypoint to the common webhook consumer
ENTRYPOINT ["python", "consumer.py"]
