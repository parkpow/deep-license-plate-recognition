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
- In **fast** mode, number of detection steps is always 1. May result in lower accuracy when using images with small vehicles.

## AWS Instance Type - t2-large 2-vCPU(2 core) 8 GiB Memory
## WORKERS DEFAULT
CPU Usage: 85.2%

| Mode    | Resolution | Speed  | l_min  | l_max   |
|---------|------------|--------|--------|---------|
| regular | 800x600    | 413.9  | 402.5  | 1770.7  |
| fast    | 800x600    | 414.5  | 425.5  | 1732.0  |
| regular | 1280x720   | 701.0  | 753.7  | 2897.4  |
| fast    | 1280x720   | 703.0  | 691.0  | 2868.2  |
| regular | 1920x1080  | 1461.3 | 1526.8 | 5913.5  |
| fast    | 1920x1080  | 1413.4 | 1433.7 | 5884.8  |
| regular | 2560x1440  | 3054.6 | 3004.0 | 12324.6 |
| fast    | 2560x1440  | 3064.4 | 3094.5 | 12365.1 |


## WORKERS = 2
CPU Usage: 97.8%

| Mode    | Resolution | Speed  | l_min  | l_max   |
|---------|------------|--------|--------|---------|
| regular | 800x600    | 358.9  | 579.1  | 2577.1  |
| fast    | 800x600    | 362.7  | 664.1  | 2332.9  |
| regular | 1280x720   | 622.2  | 1199.0 | 4391.7  |
| fast    | 1280x720   | 619.2  | 1189.5 | 4381.9  |
| regular | 1920x1080  | 1301.9 | 2426.6 | 9264.1  |
| fast    | 1920x1080  | 1294.6 | 2503.4 | 8764.3  |
| regular | 2560x1440  | 2695.7 | 5176.0 | 19023.1 |
| fast    | 2560x1440  | 2674.9 | 5086.1 | 19267.1 |



## AWS Instance Type - t3-xlarge 4-vCPU(4 core) 16 GiB Memory

## WORKERS DEFAULT
CPU Usage: 71.0%

| Mode    | Resolution | Speed  | l_min  | l_max   |
|---------|------------|--------|--------|---------|
| regular | 800x600    | 377.7  | 350.4  | 1684.6  |
| fast    | 800x600    | 364.9  | 382.6  | 1702.2  |
| regular | 1280x720   | 617.3  | 681.2  | 2699.2  |
| fast    | 1280x720   | 626.3  | 700.5  | 2731.2  |
| regular | 1920x1080  | 1254.5 | 1193.9 | 5333.4  |
| fast    | 1920x1080  | 1254.2 | 1314.6 | 5589.6  |
| regular | 2560x1440  | 2712.3 | 2757.5 | 11427.4 |
| fast    | 2560x1440  | 2694.7 | 2586.2 | 11768.8 |

## WORKERS = 2
CPU: 88.5%

| Mode    | Resolution | Speed  | l_min  | l_max   |
|---------|------------|--------|--------|---------|
| regular | 800x600    | 303.9  | 560.4  | 2205.1  |
| fast    | 800x600    | 307.7  | 560.8  | 2149.7  |
| regular | 1280x720   | 524.6  | 936.0  | 3800.8  |
| fast    | 1280x720   | 517.7  | 974.4  | 3327.6  |
| regular | 1920x1080  | 1058.6 | 2011.6 | 7336.0  |
| fast    | 1920x1080  | 1065.5 | 2015.2 | 7447.4  |
| regular | 2560x1440  | 2163.3 | 4125.9 | 15787.5 |
| fast    | 2560x1440  | 2207.7 | 4241.1 | 15504.9 |

## WORKERS = 4
CPU: 92.9%

| Mode    | Resolution | Speed  | l_min  | l_max   |
|---------|------------|--------|--------|---------|
| regular | 800x600    | 305.1  | 579.6  | 2389.2  |
| fast    | 800x600    | 298.4  | 575.9  | 2199.9  |
| regular | 1280x720   | 499.1  | 969.5  | 4548.2  |
| fast    | 1280x720   | 491.3  | 1011.6 | 4066.2  |
| regular | 1920x1080  | 1017.4 | 1677.2 | 7214.8  |
| fast    | 1920x1080  | 1017.7 | 1233.6 | 8976.2  |
| regular | 2560x1440  | 2068.8 | 4215.1 | 17267.5 |
| fast    | 2560x1440  | 2089.1 | 4154.8 | 16377.4 |
