# FROM nvcr.io/nvidia/pytorch:20.12-py3
FROM python:3.8.5-slim as cpu

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install linux packages
RUN apt update\
    && apt install --no-install-recommends -y libgl1-mesa-glx libglib2.0-0\
    && rm -rf /var/lib/apt/lists/*\
    && pip install --no-cache-dir --upgrade pip

COPY requirements-base.txt .
COPY requirements-cpu.txt .
RUN pip install --no-cache-dir -f https://download.pytorch.org/whl/torch_stable.html -r requirements-cpu.txt

# Copy source code
COPY models ./models
COPY utils ./utils
COPY main.py ./main.py
COPY webhook.py ./webhook.py
COPY crowdhuman_yolov5m.pt ./crowdhuman_yolov5m.pt

ENTRYPOINT ["python", "main.py"]


# Start FROM Nvidia PyTorch image https://ngc.nvidia.com/catalog/containers/nvidia:pytorch
FROM nvcr.io/nvidia/pytorch:20.12-py3 as gpu

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install linux packages
RUN apt update\
    && apt install --no-install-recommends  -y libgl1-mesa-glx\
    && rm -rf /var/lib/apt/lists/*\
    && pip install --no-cache-dir --upgrade pip

COPY requirements-base.txt .
COPY requirements-gpu.txt .
RUN pip install --no-cache-dir -r requirements-gpu.txt

# Copy source code
COPY models ./models
COPY utils ./utils
COPY main.py ./main.py
COPY webhook.py ./webhook.py
COPY crowdhuman_yolov5m.pt ./crowdhuman_yolov5m.pt

ENTRYPOINT ["python", "main.py"]