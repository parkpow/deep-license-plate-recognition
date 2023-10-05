
FROM python:3.10

WORKDIR /usr/src/app

COPY ./middleware_webhook_rest.py ./requirements.txt ./

RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["python3",  "middleware_webhook_rest.py"]