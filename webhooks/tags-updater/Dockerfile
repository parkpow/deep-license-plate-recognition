FROM python:3.9.7
ENV PYTHONUNBUFFERED=1
WORKDIR /code
# Copy python dependecies file
COPY requirements.txt .
RUN pip install -r requirements.txt
EXPOSE 8001
COPY . /code/

CMD ["python3", "main.py"]
