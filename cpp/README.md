# Plate Recognizer Client in C++

## Step 1

Get your API key from [Plate Recognizer](https://platerecognizer.com/). Replace **MY_API_KEY** with your API key in the file [numberPlate.cpp](linux/numberPlate.cpp) if you are using `Linux` or in the file [ConsoleApplication2.cpp](windows/ConsoleApplication2/ConsoleApplication2.cpp) if you are on `Windows`.

## Step 2

### On Windows

Open [ConsoleApplication2.sln](cpp/windows/ConsoleApplication2.sln) with Visual Studio and click compile.

### On Linux

- Install Libcurl:`sudo apt-get install libcurl3-dev libcurl4-gnutls-dev`
- Compile: `gcc -Wall -g -o output numberPlate.cpp -lcurl -lstdc++`
- Run: `./output car.jpg`

