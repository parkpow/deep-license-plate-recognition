# SDK Benchmark

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
| regular | 800x600    | 34.9  | 87.6  | 182.1 |
| fast    | 800x600    | 24.8  | 68.9  | 193.6 |
| regular | 1280x720   | 47.0  | 131.4 | 333.8 |
| fast    | 1280x720   | 26.9  | 81.2  | 198.1 |
| regular | 1920x1080  | 51.6  | 163.3 | 250.1 |
| fast    | 1920x1080  | 31.6  | 83.9  | 234.9 |
| regular | 2560x1440  | 57.5  | 139.6 | 269.2 |
| fast    | 2560x1440  | 36.1  | 90.3  | 168.3 |

### n2-standard-8 (8 vCPUs, 32 GB memory) 
| Mode    | Resolution | Speed | l_min | l_max |
| ------- | ---------- | ----- | ----- | ----- |
| regular | 800x600    | 64.4  | 186.2 | 293.8 |
| fast    | 800x600    | 37.8  | 110.4 | 264.9 |
| regular | 1280x720   | 99.2  | 283.0 | 442.7 |
| fast    | 1280x720   | 43.2  | 128.7 | 312.3 |
| regular | 1920x1080  | 101.5 | 290.2 | 706.3 |
| fast    | 1920x1080  | 45.2  | 125.6 | 307.1 |
| regular | 2560x1440  | 107.0 | 258.7 | 464.4 |
| fast    | 2560x1440  | 48.5  | 146.4 | 211.9 |

### c2-standard-4 (4 vCPUs, 16 GB memory) 
| Mode    | Resolution | Speed | l_min | l_max  |
| ------- | ---------- | ----- | ----- | ------ |
| regular | 800x600    | 100.3 | 262.9 | 627.1  |
| fast    | 800x600    | 55.5  | 150.0 | 271.5  |
| regular | 1280x720   | 153.0 | 427.0 | 1030.0 |
| fast    | 1280x720   | 62.6  | 178.1 | 456.4  |
| regular | 1920x1080  | 156.8 | 399.6 | 1097.1 |
| fast    | 1920x1080  | 67.2  | 139.5 | 408.2  |
| regular | 2560x1440  | 164.4 | 413.3 | 1065.9 |
| fast    | 2560x1440  | 72.5  | 163.1 | 609.3  |

### n2-standard-4 (4 vCPUs, 16 GB memory)
| Mode    | Resolution | Speed | l_min | l_max  |
| ------- | ---------- | ----- | ----- | ------ |
| regular | 800x600    | 116.9 | 309.7 | 815.1  |
| fast    | 800x600    | 65.7  | 130.4 | 464.8  |
| regular | 1280x720   | 175.2 | 399.0 | 763.8  |
| fast    | 1280x720   | 74.0  | 185.1 | 479.7  |
| regular | 1920x1080  | 183.4 | 528.3 | 1310.4 |
| fast    | 1920x1080  | 77.9  | 220.8 | 402.7  |
| regular | 2560x1440  | 192.1 | 490.8 | 858.6  |
| fast    | 2560x1440  | 84.9  | 182.9 | 781.1  |

### n1-standard-4 (4 vCPUs, 15 GB memory)
| Mode    | Resolution | Speed | l_min | l_max  |
| ------- | ---------- | ----- | ----- | ------ |
| regular | 800x600    | 132.9 | 375.6 | 939.2  |
| fast    | 800x600    | 73.6  | 189.4 | 558.7  |
| regular | 1280x720   | 201.1 | 548.2 | 1402.5 |
| fast    | 1280x720   | 83.8  | 165.1 | 575.6  |
| regular | 1920x1080  | 208.6 | 605.7 | 1437.3 |
| fast    | 1920x1080  | 88.2  | 270.6 | 400.9  |
| regular | 2560x1440  | 214.8 | 502.1 | 923.9  |
| fast    | 2560x1440  | 95.5  | 250.0 | 629.3  |

### n2-standard-2 (2 vCPUs, 8 GB memory)
| Mode    | Resolution | Speed | l_min | l_max   |
| ------- | ---------- | ----- | ----- | ------- |
| regular | 800x600    | 212.7 | 427.7 | 878.6   |
| fast    | 800x600    | 116.9 | 235.4 | 690.4   |
| regular | 1280x720   | 318.1 | 643.8 | 1329.6  |
| fast    | 1280x720   | 129.5 | 228.6 | 572.3   |
| regular | 1920x1080  | 327.1 | 654.9 | 1335.1  |
| fast    | 1920x1080  | 138.0 | 276.3 | 566.3   |
| regular | 2560x1440  | 347.4 | 656.2 | 15310.4 |
| fast    | 2560x1440  | 153.1 | 287.1 | 6593.0  |

### e2-standard-2 (2 vCPUs, 8 GB memory) 
| Mode    | Resolution | Speed | l_min | l_max   |
| ------- | ---------- | ----- | ----- | ------- |
| regular | 800x600    | 248.0 | 500.2 | 1062.3  |
| fast    | 800x600    | 134.6 | 259.8 | 2987.9  |
| regular | 1280x720   | 369.6 | 744.4 | 18477.0 |
| fast    | 1280x720   | 151.5 | 310.4 | 652.0   |
| regular | 1920x1080  | 385.9 | 737.8 | 11641.0 |
| fast    | 1920x1080  | 160.8 | 296.0 | 4500.8  |
| regular | 2560x1440  | 399.5 | 781.1 | 11212.7 |
| fast    | 2560x1440  | 178.7 | 310.6 | 4029.6  |

## Bare Metal

### Intel(R) Core(TM) i7-8550U CPU @ 1.80GHz
| Mode    | Resolution | Speed | l_min | l_max  |
| ------- | ---------- | ----- | ----- | ------ |
| regular | 800x600    | 62.9  | 125.9 | 263.0  |
| fast    | 800x600    | 36.2  | 74.9  | 153.8  |
| regular | 1280x720   | 103.5 | 210.6 | 442.3  |
| fast    | 1280x720   | 45.9  | 93.5  | 192.4  |
| regular | 1920x1080  | 125.4 | 232.9 | 759.7  |
| fast    | 1920x1080  | 57.5  | 113.5 | 438.4  |
| regular | 2560x1440  | 139.3 | 259.4 | 2299.9 |
| fast    | 2560x1440  | 65.0  | 126.7 | 499.2  |
