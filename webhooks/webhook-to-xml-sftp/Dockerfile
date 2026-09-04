FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

COPY config.ini /app/

EXPOSE 5000

ENV FLASK_APP=webhook_to_xml.py

CMD ["sh", "-c", "python webhook_to_xml.py", "config.ini"]
