# SDK 1.3.17 Benchmark

The results are obtained using [benchmark.py](benchmark.py).
- SDK is started with one worker per vCPU.
- The image used is `assets/car-4k.jpg` resized to target resolution.
- API is called 50 times for each configuration.
- API calls are parallelized. The client code makes **4 calls concurrently**.

#### Notes
- **Speed** is duration / number_of_calls.
- All numbers are in **milliseconds**.
- In **fast** mode, number of detection steps is always 1. May result in lower accuracy when using images with small vehicles.

## Google Cloud Instance

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

## Bare Metal

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

### Raspberry Pi 3/4 (estimates)
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
