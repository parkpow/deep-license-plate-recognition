# ParkPow Perfomance Benchmark

The results are obtained using [benchmark_parkpow.py](benchmark_parkpow.py).

The specifications of the machine used:
- AWS EC2 c6i.8xlarge (32 vCPU, 64 GiB memory)
- Amazon EBS GP3, IOPS 3000, throughput 125 MiB/s

```shell
git clone https://github.com/parkpow/deep-license-plate-recognition.git
cd deep-license-plate-recognition
python -m benchmark.benchmark_parkpow
```

## Dashboard
### 20 cameras, 5000 reads/camera/day, 365 days 
|   Range   |    No filter    | License plate search | Filter 1 camera |
| --------- | --------------- | -------------------- | --------------- |
|  1 day(s) |    629.028ms    |      169.787ms       |    442.528ms    |
|  7 day(s) |    597.688ms    |      180.038ms       |    442.835ms    |
| 14 day(s) |    600.081ms    |      180.107ms       |    448.525ms    |
| 30 day(s) |    609.409ms    |      170.151ms       |    457.374ms    |
| 60 day(s) |    606.228ms    |       168.82ms       |    443.984ms    |


## Alert
### 20 cameras, 5000 reads/camera/day, 365 days 
|   Range   |    No filter    | License plate search | Filter 1 camera |
| --------- | --------------- | -------------------- | --------------- |
|  1 day(s) |    138.081ms    |       73.184ms       |    76.306ms     |
|  7 day(s) |    136.284ms    |       68.163ms       |    68.037ms     |
| 14 day(s) |    136.417ms    |       66.877ms       |    69.824ms     |
| 30 day(s) |    136.213ms    |       68.475ms       |    68.791ms     |
| 60 day(s) |    136.865ms    |       66.951ms       |    93.288ms     |
