import { fetchWithRetry } from "./utils";

export const FORMAT_V1 = 1;
export const FORMAT_V2 = 2;

export class SnapshotResponse {
  constructor(data) {
    this._raw = data;
    // make a copy to avoid modifying original
    this._data = JSON.parse(JSON.stringify(this._raw));
    console.log(JSON.stringify(data));
    if (data["results"].length === 0) {
      this.format = FORMAT_V1;
    } else {
      if (this.isV2Format(data["results"][0])) {
        this.format = FORMAT_V2;
      } else {
        this.format = FORMAT_V1;
      }
    }
  }

  isV2Format(result) {
    return (
      ("plate" in result &&
        result["plate"] &&
        result["plate"].constructor === Object &&
        "props" in result["plate"]) ||
      ("vehicle" in result &&
        result["vehicle"] &&
        result["vehicle"].constructor === Object &&
        "props" in result["vehicle"])
    );
  }

  isEmpty() {
    return !this.findValidResult();
  }

  overwritePlate(plate) {
    const overwriteScore = 0.9;
    if (this.format === FORMAT_V1) {
      this.result["plate"] = plate;
      if (
        this.result["candidates"] === undefined ||
        this.result["candidates"].length === 0
      ) {
        this.result["candidates"] = [
          {
            plate: plate,
            score: overwriteScore,
          },
        ];
      } else {
        this.result["candidates"][0]["plate"] = plate;
      }
    } else if (this.format === FORMAT_V2) {
      let v2Plate = {
        value: plate,
        score: overwriteScore,
      };
      if (this.result["plate"]) {
        this.result["plate"]["props"]["plate"][0] = v2Plate;
      } else {
        this.result["plate"] = {
          type: "Plate",
          score: overwriteScore,
          box: { xmin: 0, ymin: 0, ymax: 0, xmax: 0 },
          props: {
            plate: [v2Plate],
            region: [
              // {
              //   "value": "gb",
              //   "score": 0.931
              // }
            ],
          },
        };
      }
    } else {
      throw new Error("Unexpected format");
    }
  }

  /**
   * Pick first result with vehicle
   * @returns {*}
   */
  findValidResult() {
    return this.results.find((el) => el["vehicle"]);
  }

  /**
   * Default result is the first result
   * @returns {*}
   */
  get result() {
    return this.findValidResult();
  }

  overwriteDirection(direction, licensePlateNumber) {
    this.result["direction"] = direction;
    // TODO Overwrite plate scores
    //this.result['direction_score'] = null
  }

  overwriteOrientation(orientation, licensePlateNumber) {
    if (
      this.result["orientation"] === undefined ||
      this.result["orientation"].length === 0
    ) {
      this.result["orientation"] = [
        {
          orientation: orientation,
          score: 0.9,
        },
      ];
    } else {
      this.result["orientation"][0]["orientation"] = orientation;
    }

    // TODO Overwrite orientation scores
    // this.result['orientation'][0]['score'] = null
  }

  get data() {
    return this._data;
  }

  get results() {
    return this._data["results"];
  }

  get cameraId() {
    return this._data["camera_id"];
  }

  get timestamp() {
    return this._data["timestamp"];
  }
}

export class SnapshotApi {
  constructor(token, sdkUrl = null, retryLimit = 3, retryDelay = 2000) {
    this.retryLimit = retryLimit;
    this.retryDelay = retryDelay;
    if (token === null) {
      throw new Error("Snapshot API token is required for authentication.");
    } else {
      this.token = token;
    }
    if (sdkUrl) {
      this.apiBase = sdkUrl;
    } else {
      this.apiBase = "https://api.platerecognizer.com";
    }
    //console.debug("Api Base: " + this.apiBase);
  }

  async uploadBase64(encodedImage, camera, timestamp, params) {
    console.log("Snapshot upload Params", params);
    const endpoint = "/v1/plate-reader/";
    const body = new FormData();
    body.set("upload", encodedImage);
    body.set("timestamp", timestamp);

    if (params["camera_id"]) {
      body.set("camera_id", params["camera_id"]);
    } else {
      body.set("camera_id", camera);
    }
    if (params["mmc"]) {
      body.set("mmc", params["mmc"]);
    } else {
      body.set("mmc", "true");
    }
    if (params["regions"]) {
      body.set("regions", params["regions"]);
    }
    if (params["config"]) {
      body.set("config", params["config"]);
    }

    let init = {
      body: body,
      method: "POST",
      headers: {
        Authorization: "Token " + this.token,
      },
    };
    const url = this.apiBase + endpoint;
    return fetchWithRetry(url, init, this.retryLimit, this.retryDelay);
  }
}
