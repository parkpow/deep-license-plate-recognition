# Api Token
Get your API key from [Plate Recognizer](https://platerecognizer.com/). Replace **MY_API_KEY** with your API key.

# PlateRecognizer Java Client
This java client uses the [unirest](http://kong.github.io/unirest-java/) library.

If you are using maven, it is very easy to setup, Just add following line in your pom.xml

```
<dependency>
    <groupId>com.konghq</groupId>
    <artifactId>unirest-java</artifactId>
    <version>3.1.00</version>
    <classifier>standalone</classifier>
</dependency>

```

and run your project, it will automatically download library!

```java
import java.io.File;
import java.io.FileWriter;
import kong.unirest.Unirest;
import kong.unirest.HttpResponse;

public class recognize {
    public static void main(String[] args){
        String token = "MY_API_KEY";
        String file = "C:\\assets\\demo.jpg";
        
        try{
            HttpResponse<String> response = Unirest.post("https://api.platerecognizer.com/v1/plate-reader/")
            .header("Authorization", "Token "+token)
            .field("upload", new File(file))
            .asString();
            System.out.println("Recognize:");
            System.out.println(response.getBody().toString());
        }
        catch(Exception e){
            System.out.println(e);
        }
        
        try{
            HttpResponse<String> response = Unirest.get("https://api.platerecognizer.com/v1/statistics/")
            .header("Authorization", "Token "+token)
            .asString();
            System.out.println("Usage:");
            System.out.println(response.getBody().toString());
        }
        catch(Exception e){
            System.out.println(e);
        }
    }
}

```

<p align="center">
  <img src="CaptureNumberPlateJava.png">
</p>
