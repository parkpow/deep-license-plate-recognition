FROM python:3.9.9
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# Copy python dependecies file
COPY requirements.txt .
RUN pip install -r requirements.txt
EXPOSE 8001
COPY . /app/

CMD ["python3", "webhook_tester.py"]
