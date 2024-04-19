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

### WORKERS DEFAULT
CPU Usage: 85.2%

| Mode    | Resolution | Speed  | l_min  | l_max   |
|---------|------------|--------|--------|---------|
| regular | 800x600    | 413.9  | 402.5  | 1770.7  |
| regular | 1280x720   | 701.0  | 753.7  | 2897.4  |
| regular | 1920x1080  | 1461.3 | 1526.8 | 5913.5  |
| regular | 2560x1440  | 3054.6 | 3004.0 | 12324.6 |

### WORKERS = 2
CPU Usage: 97.8%

| Mode    | Resolution | Speed  | l_min  | l_max   |
|---------|------------|--------|--------|---------|
| regular | 800x600    | 358.9  | 579.1  | 2577.1  |
| regular | 1280x720   | 622.2  | 1199.0 | 4391.7  |
| regular | 1920x1080  | 1301.9 | 2426.6 | 9264.1  |
| regular | 2560x1440  | 2695.7 | 5176.0 | 19023.1 |

## AWS Instance Type - t3-xlarge 4-vCPU(2 core) 16 GiB Memory
Processor: Intel Xeon Platinum 8259CL CPU @ 2.50GHz
NumSockets: 1
Manufacturer: GenuineIntel
NumCores: 2
NumLogicals: 4
CPUFrequency: 2499
Passmark: 4039.57

### WORKERS DEFAULT
CPU Usage: 71.0%

| Mode    | Resolution | Speed  | l_min  | l_max   |
|---------|------------|--------|--------|---------|
| regular | 800x600    | 377.7  | 350.4  | 1684.6  |
| regular | 1280x720   | 617.3  | 681.2  | 2699.2  |
| regular | 1920x1080  | 1254.5 | 1193.9 | 5333.4  |
| regular | 2560x1440  | 2712.3 | 2757.5 | 11427.4 |

### WORKERS = 2
CPU: 88.5%

| Mode    | Resolution | Speed  | l_min  | l_max   |
|---------|------------|--------|--------|---------|
| regular | 800x600    | 303.9  | 560.4  | 2205.1  |
| regular | 1280x720   | 524.6  | 936.0  | 3800.8  |
| regular | 1920x1080  | 1058.6 | 2011.6 | 7336.0  |
| regular | 2560x1440  | 2163.3 | 4125.9 | 15787.5 |

### WORKERS = 4
CPU: 92.9%

| Mode    | Resolution | Speed  | l_min  | l_max   |
|---------|------------|--------|--------|---------|
| regular | 800x600    | 305.1  | 579.6  | 2389.2  |
| regular | 1280x720   | 499.1  | 969.5  | 4548.2  |
| regular | 1920x1080  | 1017.4 | 1677.2 | 7214.8  |
| regular | 2560x1440  | 2068.8 | 4215.1 | 17267.5 |

