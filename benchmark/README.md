# SDK Benchmark

The results are obtained using [benchmark.py](benchmark.py).
- SDK is started with one worker per vCPU.
- The image used is `assets/car-4k.jpg` resized to target resolution.
- API is called 50 times for each configuration.
- API calls are parallelized. The client code makes **4 calls concurrently**.

#### Notes
- **Speed** is duration / number_of_calls.
- All numbers are in **milliseconds**.
- In **fast** mode, number of detection steps is always 1. May result in lower accuracy when using images with small vehicles.

## Google Cloud Instance - Snapshot 1.3.17

###  n1-standard-4 (4 vCPUs, 15 GB memory), 1 x NVIDIA Tesla T4
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 800x600    | 31.5  |
| fast    | 800x600    | 21.5  |
| regular | 1280x720   | 43.7  |
| fast    | 1280x720   | 23.7  |
| regular | 1920x1080  | 45.6  |
| fast    | 1920x1080  | 27.0  |
| regular | 2560x1440  | 49.7  |
| fast    | 2560x1440  | 29.9  |


### n2-standard-8 (8 vCPUs, 32 GB memory)
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 800x600    | 27.1  |
| fast    | 800x600    | 16.9  |
| regular | 1280x720   | 40.8  |
| fast    | 1280x720   | 21.1  |
| regular | 1920x1080  | 50.2  |
| fast    | 1920x1080  | 28.2  |
| regular | 2560x1440  | 49.9  |
| fast    | 2560x1440  | 27.7  |

### c2-standard-4 (4 vCPUs, 16 GB memory)
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 800x600    | 37.4  |
| fast    | 800x600    | 23.8  |
| regular | 1280x720   | 57.7  |
| fast    | 1280x720   | 30.0  |
| regular | 1920x1080  | 69.3  |
| fast    | 1920x1080  | 40.9  |
| regular | 2560x1440  | 67.5  |
| fast    | 2560x1440  | 38.7  |

### n2-standard-4 (4 vCPUs, 16 GB memory)
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 800x600    | 42.0  |
| fast    | 800x600    | 26.8  |
| regular | 1280x720   | 63.9  |
| fast    | 1280x720   | 33.1  |
| regular | 1920x1080  | 75.7  |
| fast    | 1920x1080  | 45.5  |
| regular | 2560x1440  | 74.7  |
| fast    | 2560x1440  | 42.9  |

### n1-standard-4 (4 vCPUs, 15 GB memory)
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 800x600    | 61.4  |
| fast    | 800x600    | 37.8  |
| regular | 1280x720   | 93.8  |
| fast    | 1280x720   | 47.3  |
| regular | 1920x1080  | 111.1 |
| fast    | 1920x1080  | 64.4  |
| regular | 2560x1440  | 110.3 |
| fast    | 2560x1440  | 59.4  |

### n2-standard-2 (2 vCPUs, 8 GB memory)
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 800x600    | 72.1  |
| fast    | 800x600    | 46.9  |
| regular | 1280x720   | 107.8 |
| fast    | 1280x720   | 58.2  |
| regular | 1920x1080  | 136.4 |
| fast    | 1920x1080  | 86.0  |
| regular | 2560x1440  | 131.3 |
| fast    | 2560x1440  | 82.8  |

### e2-standard-2 (2 vCPUs, 8 GB memory)
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 800x600    | 94.2  |
| fast    | 800x600    | 61.0  |
| regular | 1280x720   | 145.0 |
| fast    | 1280x720   | 76.8  |
| regular | 1920x1080  | 179.7 |
| fast    | 1920x1080  | 108.6 |
| regular | 2560x1440  | 171.0 |
| fast    | 2560x1440  | 98.8  |

## Bare Metal - Snapshot 1.3.17

### Intel(R) Core(TM) i7-8550U CPU @ 1.80GHz
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 800x600    | 38.3  |
| fast    | 800x600    | 21.8  |
| regular | 1280x720   | 55.3  |
| fast    | 1280x720   | 33.0  |
| regular | 1920x1080  | 73.0  |
| fast    | 1920x1080  | 37.4  |
| regular | 2560x1440  | 79.6  |
| fast    | 2560x1440  | 46.7  |

### Raspbery Pi 4 64 bits (1 worker)
| Mode    | Resolution | Speed  |
| ------- | ---------- | ------ |
| regular | 800x600    | 686.7  |
| fast    | 800x600    | 401.7  |
| regular | 1280x720   | 1181.0 |
| fast    | 1280x720   | 554.0  |
| regular | 1920x1080  | 1373.4 |
| fast    | 1920x1080  | 677.8  |
| regular | 2560x1440  | 1587.1 |
| fast    | 2560x1440  | 816.9  |

### Raspberry Pi 3/4 (estimates) 32 bits
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 1280x720   | 1300  |
| fast    | 1280x720   | 1000  |

### Jetson Nano (estimates)
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 1280x720   | 700   |
| fast    | 1280x720   | 350   |

### LattePanda Alpha (estimates)
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 1280x720   | 170   |
| fast    | 1280x720   | 119   |

### LattePanda V1 (estimates)
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 1280x720   | 1250  |
| fast    | 1280x720   | 875   |

### Jetson Orin Devkit - Snapshot 1.37

With 4 workers (`-e WORKERS=4`):

| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 800x600    | 57.8  |
| fast    | 800x600    | 38.7  |
| regular | 1280x720   | 78.2  |
| fast    | 1280x720   | 40.3  |
| regular | 1920x1080  | 82.9  |
| fast    | 1920x1080  | 43.7  |
| regular | 2560x1440  | 87.1  |
| fast    | 2560x1440  | 47.9  |

With 2 workers (`-e WORKERS=2`):

| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 800x600    | 74.1  |
| fast    | 800x600    | 49.2  |
| regular | 1280x720   | 103.4 |
| fast    | 1280x720   | 52.5  |
| regular | 1920x1080  | 112.1 |
| fast    | 1920x1080  | 59.6  |
| regular | 2560x1440  | 122.4 |
| fast    | 2560x1440  | 69.2  |

With 1 worker (`-e WORKERS=1`):

| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 800x600    | 119.8 |
| fast    | 800x600    | 83.0  |
| regular | 1280x720   | 170.5 |
| fast    | 1280x720   | 89.8  |
| regular | 1920x1080  | 190.9 |
| fast    | 1920x1080  | 108.8 |
| regular | 2560x1440  | 220.1 |
| fast    | 2560x1440  | 134.3 |

### Jetson Orin Devkit - Snapshot 1.38 (INFERENCE_ENGINE=tensorrt)

With 4 workers (`-e WORKERS=4`):

| Mode     | Resolution | Speed   |
| -------- | ---------- | ------- |
| regular  | 800x600    |    36.5 |
| fast     | 800x600    |    29.2 |
| regular  | 1280x720   |    42.1 |
| fast     | 1280x720   |    29.9 |
| regular  | 1920x1080  |    50.7 |
| fast     | 1920x1080  |    38.1 |
| regular  | 2560x1440  |    57.5 |
| fast     | 2560x1440  |    43.5 |

With 2 workers (`-e WORKERS=2`):

| Mode     | Resolution | Speed   |
| -------- | ---------- | ------- |
| regular  | 800x600    |    47.2 |
| fast     | 800x600    |    36.7 |
| regular  | 1280x720   |    57.2 |
| fast     | 1280x720   |    41.2 |
| regular  | 1920x1080  |    70.3 |
| fast     | 1920x1080  |    53.7 |
| regular  | 2560x1440  |    93.8 |
| fast     | 2560x1440  |    64.1 |

With 1 worker (`-e WORKERS=1`):

| Mode     | Resolution | Speed   |
| -------- | ---------- | ------- |
| regular  | 800x600    |    73.2 |
| fast     | 800x600    |    59.7 |
| regular  | 1280x720   |    90.2 |
| fast     | 1280x720   |    69.2 |
| regular  | 1920x1080  |   113.6 |
| fast     | 1920x1080  |    89.1 |
| regular  | 2560x1440  |   153.3 |
| fast     | 2560x1440  |   110.8 |