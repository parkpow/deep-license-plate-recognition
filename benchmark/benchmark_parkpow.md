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

## 20 cameras, 5000 reads/camera/day, 365 days, total 36,500,500 visits
### Dashboard
|   Range   |    No filter    | License plate search | Filter 1 camera |
| --------- | --------------- | -------------------- | --------------- |
|  1 day(s) |     9.996ms     |      170.443ms       |    279.254ms    |
|  7 day(s) |     9.219ms     |      176.996ms       |    251.912ms    |
| 14 day(s) |    17.165ms     |      169.897ms       |    251.664ms    |
| 30 day(s) |    13.375ms     |      300.092ms       |    250.853ms    |
| 60 day(s) |     7.645ms     |      171.984ms       |    253.802ms    |

### Alerts
|   Range   |    No filter    | License plate search | Filter 1 camera |
| --------- | --------------- | -------------------- | --------------- |
|  1 day(s) |    133.365ms    |       68.908ms       |    68.877ms     |
|  7 day(s) |    130.285ms    |        68.7ms        |    68.101ms     |
| 14 day(s) |    130.563ms    |       66.629ms       |    68.817ms     |
| 30 day(s) |    128.659ms    |       67.013ms       |    99.468ms     |
| 60 day(s) |    136.773ms    |       67.515ms       |    68.564ms     |


## 200 cameras, 5000 reads/camera/day, 365 days total 365,000,000 visits
### Dashboard
|   Range   | Without filter  | License plate search | Filter 1 camera |
| --------- | --------------- | -------------------- | --------------- |
|  1 day(s) |    504.242ms    |      464.442ms       |    146.553ms    |
|  7 day(s) |    688.454ms    |      249.828ms       |    466.07ms     |
| 14 day(s) |    653.907ms    |      253.636ms       |    443.533ms    |
| 30 day(s) |    679.647ms    |       249.63ms       |    442.983ms    |
| 60 day(s) |    672.647ms    |      249.587ms       |    440.628ms    |

### Alerts
|   Range   | Without filter  | License plate search | Filter 1 camera |
| --------- | --------------- | -------------------- | --------------- |
|  1 day(s) |    143.341ms    |       95.467ms       |    125.873ms    |
|  7 day(s) |    123.991ms    |       94.953ms       |    126.311ms    |
| 14 day(s) |    123.456ms    |       94.989ms       |    252.457ms    |
| 30 day(s) |    123.929ms    |       94.457ms       |    125.598ms    |
| 60 day(s) |    122.937ms    |       94.775ms       |    125.489ms    |
