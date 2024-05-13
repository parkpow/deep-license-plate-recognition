namespace csharp;
using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;


class Program
{
    static async Task makeRequest(String url, String token, String filePath, String regions, String cameraId, bool uploadBase64)
    {
        using (var httpClient = new HttpClient())
        {
            var formData = new MultipartFormDataContent();
            string fileName = Path.GetFileName(filePath);
            byte[] fileBytes = File.ReadAllBytes(filePath);

            if(uploadBase64){
                string base64String = Convert.ToBase64String(fileBytes);
                formData.Add(new StringContent(base64String), "upload");
            }else{            
                formData.Add(new ByteArrayContent(fileBytes), "upload", fileName );
            }

            if (regions!=null)
            {
                formData.Add(new StringContent(regions), "regions");
                
            }

            // formData.Add(new StringContent("{\"region\":\"strict\"}"), "config");
            // formData.Add(new StringContent("true"), "mmc");
            if(cameraId!=null){
                formData.Add(new StringContent(cameraId), "camera_id");
            }
            if(token!=null){
                httpClient.DefaultRequestHeaders.Add("Authorization", $"Token {token}");
            }

            var response = await httpClient.PostAsync(url, formData);

            if (response.IsSuccessStatusCode)
            {
                Console.WriteLine("Upload success");
            }
            else
            {
                Console.WriteLine($"HTTP Error: {response.StatusCode}");
            }
            var responseBody = await response.Content.ReadAsStringAsync();
            Console.WriteLine(responseBody);
        }

    }
    static Dictionary<string, string> ParseArguments(string[] args)
    {
        var arguments = new Dictionary<string, string>();

        foreach (var arg in args)
        {
            // Split the argument by '=' to handle key/value pairs
            string[] parts = arg.Split('=');

            // Check if the argument is in the format "key=value"
            if (parts.Length == 2)
            {
                arguments[parts[0]] = parts[1];
            }
            // If not, assume it's just a named argument without a value
            else
            {
                arguments[arg] = null;
            }
        }

        return arguments;
    }

    static void PrintHelp()
    {
        Console.WriteLine("Help:");
        Console.WriteLine("------");
        Console.WriteLine("Usage: PlateRecognition [options]");
        Console.WriteLine();
        Console.WriteLine("Options:");
        Console.WriteLine("  --help             Display this help message");
        Console.WriteLine("  --base64           Encode Image as Base64");
        Console.WriteLine("  --token            Specify Token");
        Console.WriteLine("  --url              Specify SDK URL");
        Console.WriteLine("  --regions          Specify Regions");
        Console.WriteLine("  --camera           Specify camera ID");
        Console.WriteLine("  --file=<file>      Set file path to upload.");
    }

    static async Task Main(string[] args)
    {
        var arguments = ParseArguments(args);
        if (arguments.Count == 0 || arguments.ContainsKey("--help"))
        {
            PrintHelp();
            return; 
        }

        if(!arguments.ContainsKey("--file")){
            Console.WriteLine("--file Is required");
            PrintHelp();
            return; 
        }
        String filePath = arguments["--file"];

        string regions;
        string cameraId;
        string token;
        String sdkUrl = "https://api.platerecognizer.com/v1/plate-reader/";
        

        if(!arguments.TryGetValue("--token", out token)){
            if(!arguments.TryGetValue("--url", out sdkUrl)){
                Console.WriteLine("Please specify --token or onPremise --url");
                PrintHelp();
                return; 
            }
        }

        if(!arguments.TryGetValue("--regions", out regions)){
            Console.WriteLine("No regions specified");
        }
        
        if(!arguments.TryGetValue("--camera", out cameraId)){
            Console.WriteLine("No cameraId specified");
        }
        
        bool uploadBase64 = arguments.ContainsKey("--base64");


        await Program.makeRequest(
            sdkUrl,
            token,
            filePath,
            regions,
            cameraId,
            uploadBase64
        );

    }

}
