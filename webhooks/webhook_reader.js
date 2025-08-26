/**
 * # Install dependecies
 *
 * npm install
 *
 * # Run
 * node webhook_reader.js
 */

var fs = require("fs");
const http = require("http");
var bodyParser = require("body-parser");
var multer = require("multer");

const uploadsDir = "./uploads";

let storage = multer.diskStorage({
  destination: function (req, file, cb) {
    if (!fs.existsSync(uploadsDir)) {
      fs.mkdirSync(uploadsDir);
    }
    cb(null, uploadsDir);
  },
  filename: function (req, file, cb) {
    cb(null, file.originalname);
  },
});

var filesParser = multer({ storage }).any();
var jsonParser = bodyParser.json();

const server = http.createServer((req, res) => {
  if (req.method === "POST") {
    collectRequestData(req, res);
  } else {
    res.end(`Send a POST request instead.`);
  }
});

server.listen(8001, function () {
  console.log("Server listening on port 8001");
});

const CONTENT_TYPE_MULTIPART_FORM_DATA = "multipart/form-data";
const CONTENT_TYPE_JSON = "application/json";

function collectRequestData(request, response) {
  const contentType = request.headers["content-type"];
  // console.log(`Content type: ${contentType}`);
  if (!contentType) {
    response.end("OK!");
  } else if (contentType.indexOf(CONTENT_TYPE_MULTIPART_FORM_DATA) > -1) {
    filesParser(request, response, function (err) {
      if (err) {
        // A Multer error occurred when uploading.
        // An unknown error occurred when uploading.
        console.error(err);
        response.writeHead(500);
        response.end("Error");
      } else {
        jsonData = request.body["json"];
        console.log(jsonData);
        response.end("OK!");
      }
    });
  } else {
    var rawData = "";
    request.on("data", (data) => {
      rawData += data;
    });
    request.on("end", () => {
      var decodedData = decodeURIComponent(rawData);
      if (decodedData.includes("json=")) {
        decodedData = decodedData.split("+").join(" ");
        const jsonData = decodedData.split("json=")[1];
        console.log(jsonData);
        response.end("OK!");
      }
    });
  }
}
