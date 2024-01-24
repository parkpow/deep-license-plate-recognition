const http = require("https");
const FormData = require("form-data");

const CLOUD_API_BASE = "https://api.platerecognizer.com";

// Getting a stream directly from http.
const makeDownloadStream = (url) =>
  new Promise((resolve, reject) => {
    http
      .request(url, (res) => {
        // We can risk missing the first n bytes if we don't pause!
        res.pause();
        resolve(res);
      })
      .on("error", reject)
      .end();
  });

const uploadFile = async (z, bundle) => {
  const form = new FormData();
  // upload and upload_url
  if (bundle.inputData.hasOwnProperty("upload")) {
    // bundle.inputData.upload will in fact be a URL where the file data can be
    // downloaded from which we do via a stream
    const stream = await makeDownloadStream(bundle.inputData.upload, z);
    form.append("upload", stream);
    // form.append('filename', bundle.inputData.filename);
    // All set! Resume the stream
    stream.resume();
  } else if (bundle.inputData.hasOwnProperty("upload_url")) {
    form.append("upload_url", bundle.inputData.upload_url);
  } else {
    throw new Error("Upload or Upload URL required");
  }

  // regions
  if (bundle.inputData.hasOwnProperty("regions")) {
    for (const region of bundle.inputData.regions) {
      form.append("regions", region);
    }
  }

  // camera_id
  if (bundle.inputData.hasOwnProperty("camera")) {
    form.append("camera_id", bundle.inputData.upload_url);
  }

  // timestamp
  if (bundle.inputData.hasOwnProperty("timestamp")) {
    form.append("timestamp", bundle.inputData.timestamp);
  }
  // mmc
  if (bundle.inputData.hasOwnProperty("mmc")) {
    form.append("mmc", bundle.inputData.mmc);
  }
  // config
  if (bundle.inputData.hasOwnProperty("config")) {
    let config = bundle.inputData.config;
    form.append("config", JSON.stringify(config));
  }
  let url = CLOUD_API_BASE + "/v1/plate-reader/";
  if (bundle.inputData.hasOwnProperty("url")) {
    url = bundle.inputData.url;
  }

  const response = await z.request({
    url: url,
    method: "POST",
    body: form,
    headers: {
      Authorization: `Token ${bundle.authData.token}`,
    },
  });

  return response.data;
};

module.exports = {
  key: "createRecognition",
  noun: "Recognition",
  display: {
    description: "Runs a Recognition using Snapshot Cloud SDK",
    hidden: false,
    label: "Run Recognition",
  },
  operation: {
    inputFields: [
      {
        key: "upload",
        label: "Image File OR a base64 encoded image",
        type: "file",
        helpText:
          "This parameter is optional if upload_url parameter is present.",
        required: false,
        list: false,
        altersDynamicFields: false,
      },
      {
        key: "upload_url",
        label: "Upload Url",
        type: "string",
        helpText:
          "The url of file to be uploaded. " +
          "This parameter is to be used as an alternative to upload parameter.",
        required: false,
        list: false,
        altersDynamicFields: false,
      },
      {
        key: "regions",
        label: "Regions",
        type: "string",
        helpText:
          "Match the license plate pattern of specific regions. " +
          "[more info](https://guides.platerecognizer.com/docs/other/country-codes/)",
        required: false,
        list: true,
        altersDynamicFields: false,
      },
      {
        key: "camera",
        label: "Camera ID",
        type: "string",
        helpText: "Unique camera identifier.",
        required: false,
        list: false,
        altersDynamicFields: false,
      },
      {
        key: "timestamp",
        label: "ISO 8601 timestamp in UTC",
        type: "string",
        helpText: "For example, 2019-08-19T13:11:25",
        required: false,
        list: false,
        altersDynamicFields: false,
      },
      {
        key: "mmc",
        label: "MMC",
        type: "string",
        helpText: "Predict vehicle make, model, orientation and color.",
        required: false,
        list: false,
        altersDynamicFields: false,
        choices: { true: "Enable MMC", false: "Disable MMC" },
      },
      {
        key: "config",
        label: "Engine Configs",
        type: "string",
        helpText:
          "Additional engine configurations in quotes. " +
          "[more info](https://guides.platerecognizer.com/docs/snapshot/api-reference#engine-configuration)",
        required: false,
        list: false,
        altersDynamicFields: false,
        dict: true,
      },
      {
        key: "url",
        label: "Snapshot API URL",
        type: "string",
        helpText:
          "Use onPremise SDK." +
          "View(debug) the request sent out by sending to a custom site such as Webhook.site",
        required: false,
        list: false,
        altersDynamicFields: false,
      },
    ],
    perform: uploadFile,
    sample: {
      processing_time: 58.184,
      results: [
        {
          box: {
            xmin: 143,
            ymin: 481,
            xmax: 282,
            ymax: 575,
          },
          plate: "nhk552",
          region: {
            code: "gb",
            score: 0.747,
          },
          vehicle: {
            score: 0.798,
            type: "Sedan",
            box: {
              xmin: 67,
              ymin: 113,
              xmax: 908,
              ymax: 653,
            },
          },
          score: 0.904,
          candidates: [
            {
              score: 0.904,
              plate: "nhk552",
            },
          ],
          dscore: 0.99,
          model_make: [
            {
              make: "Riley",
              model: "RMF",
              score: 0.306,
            },
          ],
          color: [
            {
              color: "black",
              score: 0.937,
            },
          ],
          orientation: [
            {
              orientation: "Front",
              score: 0.937,
            },
          ],
        },
      ],
      filename: "1617_7M83K_car.jpg",
      version: 1,
      camera_id: null,
      timestamp: "2020-10-12T16:17:27.574008Z",
    },
    outputFields: [
      {
        key: "processing_time",
        type: "number",
        label: "Text of the license plate.",
      },
      {
        key: "results[]plate",
        type: "string",
        label: "Text of the license plate.",
      },
      {
        key: "results[]box",
        type: "string",
        label:
          "Bounding box for the license plate. " +
          "Coordinates in pixels of the top-left and bottom-right corners of the plate.",
      },
      {
        key: "results[]dscore",
        type: "string",
        label:
          "Confidence level for plate detection. See below for more details..",
      },
      {
        key: "results[]score",
        type: "string",
        label:
          "Confidence level for reading the license plate text. See below for more details.",
      },
      {
        key: "results[]vehicle__type",
        type: "string",
        label:
          "Vehicle type: Big Truck, Bus, Motorcycle, Pickup Truck, Sedan, SUV, Van, Unknown.",
      },
      {
        key: "results[]vehicle__score",
        type: "string",
        label:
          "Confidence level for vehicle type prediction. " +
          "If we cannot find a vehicle, the score is set to 0.",
      },
      {
        key: "results[]vehicle__box",
        type: "string",
        label:
          "Vehicle bounding box. If we cannot find a vehicle, the coordinates are all 0.",
      },
      {
        key: "results[]region__code",
        type: "string",
        label: "Region of license plate. Returns a code from the country list.",
      },
      {
        key: "results[]region__score",
        type: "string",
        label: "Confidence level for license plate region.",
      },
      {
        key: "results[]candidates",
        type: "string",
        label:
          "List of predictions for the license plate value. " +
          "The first element is the top prediction (same as results/plate).",
      },
      {
        key: "results[]model_make__make",
        type: "string",
        label: "Prediction of vehicle make.",
      },
      {
        key: "results[]model_make__model",
        type: "string",
        label: "Prediction of vehicle model.",
      },
      {
        key: "results[]model_make__score",
        type: "string",
        label: "Confidence level for vehicle make and model prediction.",
      },
      {
        key: "results[]color__color",
        type: "string",
        label:
          "Vehicle color. One of black, blue, brown, green, red, silver, white, yellow, unknown.",
      },
      {
        key: "results[]color__score",
        type: "string",
        label: "Confidence level for vehicle color prediction.",
      },
      {
        key: "results[]orientation__orientation",
        type: "string",
        label: "Vehicle orientation. One of Front, Rear, Unknown.",
      },
      {
        key: "results[]orientation__score",
        type: "string",
        label: "Confidence level for vehicle orientation prediction.",
      },
      {
        key: "filename",
        type: "string",
        label: "Text of the license plate.",
      },
      {
        key: "version",
        type: "integer",
        label: "Response version.",
      },
      {
        key: "camera_id",
        type: "string",
        label: "Camera ID.",
      },
      {
        key: "timestamp",
        type: "string",
        label: "Timestamp.",
      },
    ],
  },
};
