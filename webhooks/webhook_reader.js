/**
 * # Install dependecies
 *
 * npm install
 *
 * # Run
 * node webhook_reader.js
 */

const fs = require("node:fs");
const http = require("node:http");
const multer = require("multer");

const uploadsDir = "./uploads";

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => {
    if (!fs.existsSync(uploadsDir)) {
      fs.mkdirSync(uploadsDir);
    }
    cb(null, uploadsDir);
  },
  filename: (_req, file, cb) => {
    cb(null, file.originalname);
  },
});

const filesParser = multer({ storage }).any();

const server = http.createServer((req, res) => {
  if (req.method === "POST") {
    collectRequestData(req, res);
  } else {
    res.end(`Send a POST request instead.`);
  }
});

server.listen(8001, () => {
  console.log("Server listening on port 8001");
});

const CONTENT_TYPE_MULTIPART_FORM_DATA = "multipart/form-data";

function collectRequestData(request, response) {
  const contentType = request.headers["content-type"];
  // console.log(`Content type: ${contentType}`);
  if (!contentType) {
    response.end("OK!");
  } else if (contentType.indexOf(CONTENT_TYPE_MULTIPART_FORM_DATA) > -1) {
    filesParser(request, response, (err) => {
      if (err) {
        // A Multer error occurred when uploading.
        // An unknown error occurred when uploading.
        console.error(err);
        response.writeHead(500);
        response.end("Error");
      } else {
        jsonData = request.body.json;
        console.log(jsonData);
        response.end("OK!");
      }
    });
  } else {
    let rawData = "";
    request.on("data", (data) => {
      rawData += data;
    });
    request.on("end", () => {
      let decodedData = decodeURIComponent(rawData);
      if (decodedData.includes("json=")) {
        decodedData = decodedData.split("+").join(" ");
        const jsonData = decodedData.split("json=")[1];
        console.log(jsonData);
        response.end("OK!");
      }
    });
  }
}
