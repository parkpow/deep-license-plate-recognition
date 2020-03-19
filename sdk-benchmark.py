from PIL import Image
import psutil
import os
import timeit

imgSize = [[800, 600], [1280, 720], [1920, 1080], [2560, 1440]]
img = Image.open('/home/x1x0/Downloads/car.jpg')

counter = 0
for i in imgSize:
    img = img.resize((i[0], i[1]), Image.ANTIALIAS)
    img.save('/home/x1x0/Downloads/out/carout' + str(counter) + '.jpg')
    counter += 1

p = psutil.Process(os.getpid())

MY_API_KEY = input("Please enter your API key:")


def benchmark():
    for i in range(4):
        command = 'python3 /home/x1x0/deep-license-plate-recognition/plate_recognition.py --api-key '
        command += MY_API_KEY + ' /home/x1x0/Downloads/out/carout' + str(
            i) + '.jpg'
        os.system(command)

        # print(psutil.virtual_memory())
        # print(p.cpu_percent())


elapsed_time = timeit.timeit(
    benchmark, number=1) / 100  # number value should be set to 500
print("Elapsed time:", elapsed_time)
