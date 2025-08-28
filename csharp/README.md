# PlateRecognizer CSharp Example

Plate Recognizer .Net example as a console application.

This project does not use any external dependencies.

## Prerequisites
 - .Net SDK 9.0
> Easiest way to edit is to use Github codespaces

## Usage

### Upload Method signature:
```csharp
makeRequest(String url, String token, String filePath, String regions, String cameraId, bool uploadBase64)
```

### Command Line:
```shell
# Get help
dotnet run

# Uplod to cloud API
dotnet run --token=4805bee122### --file=../assets/demo.jpg

# Upload the image as Base64
dotnet run --token=4805bee122### --file=../assets/demo.jpg --base64
```

### Quick build and run using dotnet cli
```
dotnet run --token=4805bee122### --file=../assets/demo.jpg --camera=camera46363

```


