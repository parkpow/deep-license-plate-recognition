# Blur SDK Benchmark

The results are obtained using [benchmark_snapshot.py](benchmark_snapshot.py).

- The images used are `assets/car-4k.jpg` and `assets/cars-4k.jpg` resized to target resolution.
- API is called 50 times for each configuration.
- API calls are parallelized. The client code makes **4 calls concurrently**.
- Default config with blur enabled by setting **PLATES=10** and **FACES=10**

```shell
git clone https://github.com/parkpow/deep-license-plate-recognition.git
cd deep-license-plate-recognition
python3 -m benchmark.benchmark_snapshot --blur --sdk-url http://localhost:8001
```

#### Notes
- **Speed** is duration / number_of_calls.
- All numbers are in **milliseconds**.

## Current Version Benchmarks
**PlateRecognizer Blur**: v1.0.8  
**PlateRecognizer Snapshot**: v1.54.0

## Local Machine Benchmark - 12th Gen Intel Core i3-1215U (6 Cores, 8 Threads, 16 GiB RAM)
Processor: Intel Core i3-1215U @ 1.20GHz  
Manufacturer: GenuineIntel  
NumCores: 6  
NumLogicals: 8  
CPUFrequency: 4400  
Passmark: 10432  

### WORKERS = 1 
Image: `assets/car-4k.jpg`

| Resolution | Speed | Peak CPU% (Blur, Snapshot) | Peak MEM in MiB (Blur, Snapshot) |
|------------|-------|----------------------------|----------------------------------|
| 800x600    | 185.2 | 57.04, 7.51                | 529.71, 508.80                   |
| 1280x720   | 180.4 | 45.23, 8.20                | 426.93, 510.40                   |
| 1920x1080  | 241.5 | 46.40, 9.40                | 430.35, 520.90                   |
| 2560x1440  | 353.3 | 45.86, 8.45                | 489.37, 529.97                   |
| 3840x2160  | 598.4 | 60.96, 8.65                | 510.27, 580.17                   |


### WORKERS = 1
Image: `assets/cars-4k.jpg`

| Resolution | Speed | Peak CPU% (Blur, Snapshot) | Peak MEM in MiB (Blur, Snapshot) |
|------------|-------|----------------------------|----------------------------------|
| 800x600    | 388.0 | 45.84, 7.52                | 289.65, 338.73                   |
| 1280x720   | 377.6 | 40.62, 9.11                | 346.34, 340.29                   |
| 1920x1080  | 400.1 | 41.80, 9.82                | 295.51, 350.61                   |
| 2560x1440  | 447.4 | 42.29, 10.08               | 303.67, 370.47                   |
| 3840x2160  | 631.3 | 54.01, 8.31                | 375.21, 410.12                   |


### WORKERS = 2
Image: `assets/cars-4k.jpg`

| Resolution | Speed | Peak CPU% (Blur, Snapshot) | Peak MEM in MiB (Blur, Snapshot) |
|------------|-------|----------------------------|----------------------------------|
| 800x600    | 744.0 | 45.21, 8.79                | 396.69, 338.70                   |
| 1280x720   | 742.7 | 40.71, 9.52                | 359.91, 338.91                   |
| 1920x1080  | 779.9 | 40.22, 9.63                | 323.12, 350.52                   |
| 2560x1440  | 878.3 | 43.36, 10.31                | 372.47, 370.47                   |
| 3840x2160  | 1237.2 | 52.9, 8.71                | 375.41, 410.03                   |


## Previous Version Benchmarks

## AWS Instance Type - t2-large 2-vCPU(2 core) 8 GiB Memory
Processor: Intel Xeon CPU E5-2686 v4 @ 2.30GHz  
NumSockets: 1  
Manufacturer: GenuineIntel  
NumCores: 2  
NumLogicals: 2  
CPUFrequency: 2300  
Passmark: 2420.9990  

### WORKERS = 1
Image: `assets/car-4k.jpg`

| Resolution | Speed | Peak CPU% (Blur, Snapshot) | Peak MEM in MiB (Blur, Snapshot) |
|------------|-------|----------------------------|----------------------------------|
| 800x600    | 406.9 | 144.84, 28.51              | 705.61, 235.30                   |
| 1280x720   | 426.6 | 125.23, 48.10              | 681.43, 235.30                   |
| 1920x1080  | 528.0 | 115.30, 46.70              | 692.35, 236.80                   |
| 2560x1440  | 975.7 | 112.86, 46.75              | 746.27, 235.77                   |

### WORKERS = 2
Image: `assets/car-4k.jpg`

| Resolution | Speed | Peak CPU% (Blur, Snapshot) | Peak MEM in MiB (Blur, Snapshot) |
|------------|-------|----------------------------|----------------------------------|
| 800x600    | 350.0 | 177.74, 35.43              | 851.23, 378.21                   |
| 1280x720   | 350.7 | 155.78,  66.82             | 765.73, 382.18                   |
| 1920x1080  | 435.9 | 149.61, 61.38              | 781.14, 390.07                   |
| 2560x1440  | 786.3 | 194.81, 83.06              | 868.37, 441.07                   |

## AWS Instance Type - t3-xlarge 4-vCPU(2 core) 16 GiB Memory
Processor: Intel Xeon Platinum 8259CL @ 2.50GHz  
NumSockets: 1  
Manufacturer: GenuineIntel  
NumCores: 2  
NumLogicals: 4  
CPUFrequency: 2499  
Passmark: 4039.57  

### WORKERS = 1
Image: `assets/car-4k.jpg`

| Resolution | Speed | Peak CPU% (Blur, Snapshot) | Peak MEM in MiB (Blur, Snapshot) |
|------------|-------|----------------------------|----------------------------------|
| 800x600    | 375.0 | 265.66, 29.75              | 499.87, 222.80                   |
| 1280x720   | 384.7 | 225.70, 41.67              | 519.84, 226.04                   |
| 1920x1080  | 519.1 | 212.69,57.34               | 497.72, 227.89                   |
| 2560x1440  | 964.2 | 209.77, 47.42              | 568.27, 238.00                   |

### WORKERS = 2
Image: `assets/car-4k.jpg`

| Resolution | Speed | Peak CPU% (Blur, Snapshot) | Peak MEM in MiB (Blur, Snapshot) |
|------------|-------|----------------------------|----------------------------------|
| 800x600    | 306.2 | 356.95, 39.76              | 1319.49, 387.57                  |
| 1280x720   | 303.5 | 333.44, 73.56              | 1273.29, 392.47                  |
| 1920x1080  | 387.6 | 303.41, 83.80              | 1297.73, 404.14                  |
| 2560x1440  | 717.5 | 338.79, 104.97             | 1362.45, 448.89                  |

### WORKERS = 4
Image: `assets/car-4k.jpg`

| Resolution | Speed | Peak CPU% (Blur, Snapshot) | Peak MEM in MiB (Blur, Snapshot) |
|------------|-------|----------------------------|----------------------------------|
| 800x600    | 295.1 | 378.88, 41.19              | 1665.84, 661.40                  |
| 1280x720   | 291.8 | 396.42, 68.414             | 1630.47, 690.65                  |
| 1920x1080  | 360.1 | 371.16, 93.14              | 1711.66, 715.22                  |
| 2560x1440  | 614.7 | 402.30, 164.91             | 1800.31, 790.79                  |