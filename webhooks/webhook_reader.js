/**
 * # Install dependecies
 *
 * npm install
 *
 * # Run
 * node server.js
 */


const http = require('http');
var bodyParser = require('body-parser')
var multer = require('multer');


let storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, './webhook-files')
    },
    filename: function (req, file, cb) {
        cb(null, file.fieldname)
    }
});


var filesParser = multer({ storage }).any();
var jsonParser = bodyParser.json();


const server = http.createServer((req, res) => {
    if (req.method === 'POST') {
        collectRequestData(req, res);
    } else {
        res.end(`Send a POST request instead.`);
    }
});


server.listen(8001, function(){
 console.log("Server listening on port 3000");
});

const CONTENT_TYPE_MULTIPART_FORM_DATA = 'multipart/form-data';
const CONTENT_TYPE_JSON = 'application/json';

function collectRequestData(request,response) {
    const contentType = request.headers['content-type'];
    console.log(`Content type: ${contentType}`);
    if(!contentType){
        response.end('OK!')
    }else if(contentType.indexOf(CONTENT_TYPE_MULTIPART_FORM_DATA)>-1){
        console.log('parsing as multipart')
        filesParser(request, response, function (err) {
            if (err instanceof multer.MulterError) {
                // A Multer error occurred when uploading.
                console.error(err);
            } else if (err) {
                // An unknown error occurred when uploading.
                console.error(err);
            }

            // console.log('request files');
            // console.log(request.files);

            // console.log('request body');
            // console.log(request.body);

            json_data = JSON.parse(request.body['json'])
            console.log(json_data)
            response.end('OK!')

         });

    }else{
        console.log('parsing as json')
        jsonParser(request, response, function(){
            console.log('request body');
            console.log(request.body);
            response.end('OK!')
        });

    }
}
