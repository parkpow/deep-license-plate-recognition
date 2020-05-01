using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace PlateRecognizer
{
    class Program
    {
        static void Main(string[] args)
        {
            try
            {
                Console.ForegroundColor = ConsoleColor.Green;
                List<string> filePaths = new List<string>();
                string regions = null;
                string token = null;
                foreach (string arg in args)
                {
                    if (arg.Length > 3 || arg.StartsWith("/?"))
                        switch (arg.Substring(0, 2).ToUpper())
                        {
                            case "/F":
                                filePaths.Add(arg.Substring(3).Replace("\"", ""));
                                break;
                            case "/R":
                                regions = arg.Substring(3);
                                break;
                            case "/T":
                                token = arg.Substring(3);
                                break;
                            case "/?":
                                Console.WriteLine("\t/F:<File Path>\t Set file path to upload.It can be set multiple time.");
                                Console.WriteLine("\t/R:<File Path>\t Set regions.");
                                Console.WriteLine("\t/T:MY_TOKEN\t Set token.");
                                Console.WriteLine("\t/?:<File Path>\t Help.");
                                Console.WriteLine("\tExamples\t /F:\"C:/Pictures/Car.jpg\"");
                                Console.WriteLine("\t        \t /F:\"C:/Pictures/Car1.jpg\" /F:\"C:/Pictures/Car2.jpg\"");
                                break;
                            default:
                                break;
                        }
                }
                if (filePaths.Count() == 0)
                {
                    Console.WriteLine("File path paramter cannot be empty.");
                    return;
                }
                Console.WriteLine("Uploading Plate(s)...");
                Console.WriteLine("-------------------");
                string postUrl = "https://api.platerecognizer.com/v1/plate-reader/";

                foreach (var file in filePaths)
                {
                    try
                    {
                        PlateReaderResult plateReaderResult = PlateReader.Read(postUrl, file, null, regions, token);
                        Console.WriteLine(string.Format("File [{0}] successfully uploaded.", file));
                        Console.WriteLine("-------------------");
                        Console.WriteLine(Utils.ObjectDumper.Dump(plateReaderResult));
                        Console.WriteLine("-------------------");
                    }
                    catch (Exception ex)
                    {
                        Console.ForegroundColor = ConsoleColor.Red;
                        Console.WriteLine(string.Format("Error occured when uploading [{0}].", file));
                        Console.WriteLine(ex.Message);
                        Console.WriteLine(ex.StackTrace);
                        Console.ForegroundColor = ConsoleColor.Green;
                    }
                }
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine(ex.Message);
                Console.WriteLine(ex.StackTrace);
                Console.ForegroundColor = ConsoleColor.Red;
            }
            Console.ResetColor();
        }
    }
}
