FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy python dependecies file
COPY requirements.txt .

RUN pip install -r requirements.txt

# Copy source code
COPY . /app/

ENTRYPOINT ["python3", "main.py"]
