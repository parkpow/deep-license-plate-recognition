# Start FROM Nvidia PyTorch image https://ngc.nvidia.com/catalog/containers/nvidia:pytorch
FROM nvcr.io/nvidia/pytorch:20.12-py3
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install linux packages
RUN apt update\
    && apt install --no-install-recommends  -y libgl1-mesa-glx\
    && rm -rf /var/lib/apt/lists/*\
    && pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY models ./models
COPY utils ./utils
COPY main.py ./main.py
COPY webhook.py ./webhook.py
COPY crowdhuman_yolov5m.pt ./crowdhuman_yolov5m.pt

ENTRYPOINT ["python", "main.py"]