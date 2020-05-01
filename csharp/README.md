# PlateRecognizer CSharp Client

Plate Recognizer .Net client as a console application.

This project does not use any external dependencies.

## Prerequisites

 - Microsoft Visual studio 2017
 - .Net Framework 4.6.1

## Usage
- C# Method:
```csharp
PlateReader.Read("Web Api Url", "File path", "Regions", "Token");
```
- Command Line:
```
PlateRecognizer.exe /F:/tmp/car.jpg /T:MY_TOKEN /R:fr,it
PlateRecognizer.exe /T:MY_TOKEN /F:"S:\DEV\PR\PlateRecognizer\PlateRecognizer\car.jpg"
```
