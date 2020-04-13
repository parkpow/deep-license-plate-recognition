# SDK 1.3.17 Benchmark

The results are obtained using [benchmark.py](benchmark.py).
- SDK is started with one worker per vCPU.
- The image used is `assets/car-4k.jpg` resized to target resolution.
- API is called 50 times.
- API calls are parallelized with 4 threads.

**Notes**
- Speed is duration / number_of_calls.
- All numbers are in milliseconds.
- l_min is the fastest API call and l_max is the slowest API call (measured in a thread).
- In fast mode, number of detection steps is always 1. May result in lower accuracy when using images with small vehicles.

## Google Cloud Instance

###  n1-standard-4 (4 vCPUs, 15 GB memory), 1 x NVIDIA Tesla T4
| Mode    | Resolution | Speed | l_min | l_max |
| ------- | ---------- | ----- | ----- | ----- |
| regular | 800x600    | 31.5  | 91.7  | 224.1 |
| fast    | 800x600    | 21.5  | 55.5  | 95.3  |
| regular | 1280x720   | 43.7  | 73.0  | 301.4 |
| fast    | 1280x720   | 23.7  | 76.2  | 172.4 |
| regular | 1920x1080  | 45.6  | 107.5 | 312.4 |
| fast    | 1920x1080  | 27.0  | 71.8  | 148.4 |
| regular | 2560x1440  | 49.7  | 141.6 | 362.5 |
| fast    | 2560x1440  | 29.9  | 85.9  | 224.1 |


### n2-standard-8 (8 vCPUs, 32 GB memory)
| Mode    | Resolution | Speed | l_min | l_max |
| ------- | ---------- | ----- | ----- | ----- |
| regular | 800x600    | 27.1  | 62.4  | 213.4 |
| fast    | 800x600    | 16.9  | 41.0  | 92.3  |
| regular | 1280x720   | 40.8  | 107.7 | 290.9 |
| fast    | 1280x720   | 21.1  | 51.6  | 143.1 |
| regular | 1920x1080  | 50.2  | 150.2 | 360.2 |
| fast    | 1920x1080  | 28.2  | 83.5  | 210.9 |
| regular | 2560x1440  | 49.9  | 155.8 | 369.9 |
| fast    | 2560x1440  | 27.7  | 80.6  | 130.1 |

### c2-standard-4 (4 vCPUs, 16 GB memory)
| Mode    | Resolution | Speed | l_min | l_max |
| ------- | ---------- | ----- | ----- | ----- |
| regular | 800x600    | 37.4  | 82.7  | 275.4 |
| fast    | 800x600    | 23.8  | 53.3  | 186.4 |
| regular | 1280x720   | 57.7  | 68.9  | 416.7 |
| fast    | 1280x720   | 30.0  | 81.2  | 218.9 |
| regular | 1920x1080  | 69.3  | 183.3 | 500.7 |
| fast    | 1920x1080  | 40.9  | 83.1  | 305.5 |
| regular | 2560x1440  | 67.5  | 137.8 | 620.5 |
| fast    | 2560x1440  | 38.7  | 94.0  | 337.1 |

### n2-standard-4 (4 vCPUs, 16 GB memory)
| Mode    | Resolution | Speed | l_min | l_max |
| ------- | ---------- | ----- | ----- | ----- |
| regular | 800x600    | 42.0  | 84.8  | 357.6 |
| fast    | 800x600    | 26.8  | 53.1  | 190.7 |
| regular | 1280x720   | 63.9  | 183.3 | 455.8 |
| fast    | 1280x720   | 33.1  | 80.1  | 256.6 |
| regular | 1920x1080  | 75.7  | 210.5 | 528.1 |
| fast    | 1920x1080  | 45.5  | 98.4  | 348.5 |
| regular | 2560x1440  | 74.7  | 150.8 | 662.3 |
| fast    | 2560x1440  | 42.9  | 102.4 | 429.8 |

### n1-standard-4 (4 vCPUs, 15 GB memory)
| Mode    | Resolution | Speed | l_min | l_max |
| ------- | ---------- | ----- | ----- | ----- |
| regular | 800x600    | 61.4  | 124.7 | 427.6 |
| fast    | 800x600    | 37.8  | 77.3  | 262.0 |
| regular | 1280x720   | 93.8  | 179.0 | 672.9 |
| fast    | 1280x720   | 47.3  | 108.4 | 332.0 |
| regular | 1920x1080  | 111.1 | 148.5 | 817.7 |
| fast    | 1920x1080  | 64.4  | 128.6 | 529.0 |
| regular | 2560x1440  | 110.3 | 327.4 | 750.3 |
| fast    | 2560x1440  | 59.4  | 175.9 | 396.3 |

### n2-standard-2 (2 vCPUs, 8 GB memory)
| Mode    | Resolution | Speed | l_min | l_max  |
| ------- | ---------- | ----- | ----- | ------ |
| regular | 800x600    | 72.1  | 133.0 | 3604.9 |
| fast    | 800x600    | 46.9  | 95.6  | 211.7  |
| regular | 1280x720   | 107.8 | 218.4 | 457.0  |
| fast    | 1280x720   | 58.2  | 113.9 | 2659.8 |
| regular | 1920x1080  | 136.4 | 253.7 | 1920.7 |
| fast    | 1920x1080  | 86.0  | 150.3 | 2601.5 |
| regular | 2560x1440  | 131.3 | 253.3 | 1050.9 |
| fast    | 2560x1440  | 82.8  | 158.3 | 2018.1 |

### e2-standard-2 (2 vCPUs, 8 GB memory)
| Mode    | Resolution | Speed | l_min | l_max  |
| ------- | ---------- | ----- | ----- | ------ |
| regular | 800x600    | 94.2  | 196.0 | 391.9  |
| fast    | 800x600    | 61.0  | 119.8 | 1235.1 |
| regular | 1280x720   | 145.0 | 282.7 | 5218.4 |
| fast    | 1280x720   | 76.8  | 159.5 | 323.5  |
| regular | 1920x1080  | 179.7 | 368.0 | 754.8  |
| fast    | 1920x1080  | 108.6 | 221.3 | 456.5  |
| regular | 2560x1440  | 171.0 | 322.2 | 3413.4 |
| fast    | 2560x1440  | 98.8  | 188.2 | 1176.1 |

## Bare Metal

### Intel(R) Core(TM) i7-8550U CPU @ 1.80GHz
| Mode    | Resolution | Speed | l_min | l_max |
| ------- | ---------- | ----- | ----- | ----- |
| regular | 800x600    | 38.3  | 91.0  | 297.5 |
| fast    | 800x600    | 21.8  | 32.7  | 108.5 |
| regular | 1280x720   | 55.3  | 144.7 | 366.8 |
| fast    | 1280x720   | 33.0  | 66.3  | 167.5 |
| regular | 1920x1080  | 73.0  | 170.4 | 501.2 |
| fast    | 1920x1080  | 37.4  | 112.1 | 260.9 |
| regular | 2560x1440  | 79.6  | 189.6 | 362.3 |
| fast    | 2560x1440  | 46.7  | 118.4 | 219.9 |

### Raspberry Pi 3/4 (estimates)
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 1280x720   | 1300  |
| fast    | 1280x720   | 1000  |

### Jetson Nano (estimates)
| Mode    | Resolution | Speed |
| ------- | ---------- | ----- |
| regular | 1280x720   | 300   |
| fast    | 1280x720   | 250   |

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
