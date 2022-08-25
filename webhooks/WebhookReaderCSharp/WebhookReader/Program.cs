using System;
using System.IO;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using HttpMultipartParser;

namespace WebhookReader
{
    internal class HttpServer
    {
        public static HttpListener listener;
        public static string url = "http://localhost:8000/";
        
        public static void ParseData(HttpListenerRequest request)
        {
            if (!request.HasEntityBody)
            {
                Console.WriteLine("No client data was sent with the request.");
                return;
            }

            System.IO.Stream body = request.InputStream;
            System.Text.Encoding encoding = request.ContentEncoding;
            System.IO.StreamReader reader = new System.IO.StreamReader(body, encoding);
            // Convert the data to a string and display it on the console.
            string s = reader.ReadToEnd();
            Console.WriteLine("Json:");
            Console.WriteLine(s);
            body.Close();
            reader.Close();
            // If you are finished with the request, it should be closed also.
        }
        public static async Task HandleIncomingConnections()
        {
            while (true)
            {
                // Will wait here until we hear from a connection
                HttpListenerContext ctx = await listener.GetContextAsync();

                // Peel out the requests and response objects
                HttpListenerRequest req = ctx.Request;
                HttpListenerResponse resp = ctx.Response;

                // Print out some info about the request
                Console.WriteLine();
                Console.WriteLine("Handling Request - {0}", req.HttpMethod);
                byte[] data;

                // If `shutdown` url requested w/ POST, then shutdown the server after serving the page
                if (req.HttpMethod == "POST")
                {
                    Console.WriteLine("Processing Webhook Event");
                    if (req.ContentType != null && req.ContentType.StartsWith("multipart/form-data"))
                    {
                        Console.WriteLine("Event Contains Image");
                        var parser = MultipartFormDataParser.Parse(req.InputStream);
                        // From this point the data is parsed, we can retrieve the
                        // form data using the GetParameterValue method.
                        var json = parser.GetParameterValue("json");
                        
                        Console.WriteLine("json:");
                        Console.WriteLine(json);
                        
                        // Files are stored in a list:
                        var upload = parser.Files[0];
                        var filename = upload.FileName;
                        // using (FileStream output = new FileStream(filename, FileMode.Create, FileAccess.Write))
                        using (Stream file = File.Create(filename))
                        {
                            upload.Data.CopyTo(file);
                        }
                        Console.WriteLine("Upload File saved to: {0}", filename);

                    }
                    else if (req.ContentType != null && req.ContentType.StartsWith("application/x-www-form-urlencoded"))
                    {
                        Console.WriteLine("Event Contains No Image");
                        ParseData(req);
                    }
                    else
                    {
                        Console.WriteLine("Invalid Request Content Type - {0}", req.ContentType);
                    }


                    data = Encoding.UTF8.GetBytes("OK");
                }
                else
                {
                    Console.WriteLine("Invalid request method");
                    data = Encoding.UTF8.GetBytes("Send a POST request instead.");
                }
                
                resp.ContentType = "text/html";
                resp.ContentEncoding = Encoding.UTF8;
                resp.ContentLength64 = data.LongLength;

                // Write out to the response stream (asynchronously), then close it
                await resp.OutputStream.WriteAsync(data, 0, data.Length);
                resp.Close();
            }
        }

        public static void Main(string[] args)
        {
            listener = new HttpListener();
            listener.Prefixes.Add(url);
            listener.Start();
            Console.WriteLine("Listening for connections on {0}", url);
            // Handle requests
            Task listenTask = HandleIncomingConnections();
            listenTask.GetAwaiter().GetResult();

            // Close the listener
            listener.Close();
        }
    }
}