# Blur SDK Benchmark

The results are obtained using [benchmark_snapshot.py](benchmark_snapshot.py).

- The image used is `assets/car-4k.jpg` resized to target resolution.
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

## AWS Instance Type - t2-large 2-vCPU(2 core) 8 GiB Memory
Processor: Intel Xeon CPU E5-2686 v4 @ 2.30GHz  
NumSockets: 1  
Manufacturer: GenuineIntel  
NumCores: 2  
NumLogicals: 2  
CPUFrequency: 2300  
Passmark: 2420.9990  

### WORKERS = 1 (DEFAULT)


| Resolution | Speed | Peak CPU% (Blur, Snapshot) | Peak MEM in MiB (Blur, Snapshot) |
|------------|-------|----------------------------|----------------------------------|
| 800x600    | 406.9 | 144.84, 28.51              | 705.61, 235.30                   |
| 1280x720   | 426.6 | 125.23, 48.10              | 681.43, 235.30                   |
| 1920x1080  | 528.0 | 115.30, 46.70              | 692.35, 236.80                   |
| 2560x1440  | 975.7 | 112.86, 46.75              | 746.27, 235.77                   |

### WORKERS = 2


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

### WORKERS = 1 (DEFAULT)

| Resolution | Speed | Peak CPU% (Blur, Snapshot) | Peak MEM in MiB (Blur, Snapshot) |
|------------|-------|----------------------------|----------------------------------|
| 800x600    | 375.0 | 265.66, 29.75              | 499.87, 222.80                   |
| 1280x720   | 384.7 | 225.70, 41.67              | 519.84, 226.04                   |
| 1920x1080  | 519.1 | 212.69,57.34               | 497.72, 227.89                   |
| 2560x1440  | 964.2 | 209.77, 47.42              | 568.27, 238.00                   |

### WORKERS = 2

| Resolution | Speed | Peak CPU% (Blur, Snapshot) | Peak MEM in MiB (Blur, Snapshot) |
|------------|-------|----------------------------|----------------------------------|
| 800x600    | 306.2 | 356.95, 39.76              | 1319.49, 387.57                  |
| 1280x720   | 303.5 | 333.44, 73.56              | 1273.29, 392.47                  |
| 1920x1080  | 387.6 | 303.41, 83.80              | 1297.73, 404.14                  |
| 2560x1440  | 717.5 | 338.79, 104.97             | 1362.45, 448.89                  |

### WORKERS = 4

| Resolution | Speed | Peak CPU% (Blur, Snapshot) | Peak MEM in MiB (Blur, Snapshot) |
|------------|-------|----------------------------|----------------------------------|
| 800x600    | 295.1 | 378.88, 41.19              | 1665.84, 661.40                  |
| 1280x720   | 291.8 | 396.42, 68.414             | 1630.47, 690.65                  |
| 1920x1080  | 360.1 | 371.16, 93.14              | 1711.66, 715.22                  |
| 2560x1440  | 614.7 | 402.30, 164.91             | 1800.31, 790.79                  |

## Local Machine Benchmark - 12th Gen Intel Core i3-1215U (6 Cores, 8 Threads, 16 GiB RAM)
Processor: Intel Core i3-1215U @ 1.20GHz  
Manufacturer: GenuineIntel  
NumCores: 6  
NumLogicals: 8  
CPUFrequency: 4400  
Passmark: 10432  

### 4K Images Benchmark

| Filename      | Avg Speed (ms) | Min Speed (ms) | Max Speed (ms) |
|---------------|----------------|----------------|----------------|
| [single-1.jpg](https://drive.google.com/file/d/19IafPgGJLawOn7fv4MbXFd1Wc4yt78-X/view?usp=drive_link)  | 1920.3         | 559.4          | 2129.1         |
| [single-2.jpg](https://drive.google.com/file/d/1ntqdpxi4cDSkTr14RaqUlKC8f9wnCs2M/view?usp=drive_link)  | 2442.6         | 691.4          | 2619.9         |
| [many-1.jpg](https://drive.google.com/file/d/126AphdZb6jqnUVjChmZRiRCdIk_1FuGN/view?usp=drive_link)    | 3266.8         | 817.3          | 3965.1         |
| [many-2.jpg](https://drive.google.com/file/d/16hfH_nGZ_omyfiQtT_U69NI3Ju5jQ3Aw/view?usp=drive_link)    | 4514.9         | 1092.2         | 5180.0         |
| [many-3.jpg](https://drive.google.com/file/d/1_r1w6Z5K9IJUWJJe9mzifpwZNU_Li9M0/view?usp=drive_link)    | 3687.1         | 989.0          | 4175.9         |