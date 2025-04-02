import { fetchWithRetry } from "./utils";

export class SnapshotResponse {
  constructor(data) {
    this._data = data;
    console.log(JSON.stringify(data));
  }

  /**
   * Handle missing results from snapshot by creating a minimal result
   * Incase forwarding is needed
   */
  ensureResultsNotEmpty(plate) {
    if (this.results.length === 0) {
      this.results.push({
        plate: plate,
        score: 0.9,
        // box: { xmin: 0, ymin: 0, ymax: 0, xmax: 0 },
      });
    }
  }

  overwritePlate(plate) {
    this.ensureResultsNotEmpty(plate);
    this.result["plate"] = plate;
    if (
      this.result["candidates"] === undefined ||
      this.result["candidates"].length === 0
    ) {
      this.result["candidates"] = [
        {
          plate: plate,
          score: 0.9,
        },
      ];
    } else {
      this.result["candidates"][0]["plate"] = plate;
    }

    // TODO Overwrite plate scores
    //this.result['score'] = null
    //this.result['dscore'] = null
    // this.result['candidates'][0]['score'] = score
  }

  /**
   * Default result is the first result
   * @returns {*}
   */
  get result() {
    return this.results[0];
  }

  overwriteDirection(direction, licensePlateNumber) {
    this.ensureResultsNotEmpty(licensePlateNumber);
    this.result["direction"] = direction;
    // TODO Overwrite plate scores
    //this.result['direction_score'] = null
  }

  overwriteOrientation(orientation, licensePlateNumber) {
    this.ensureResultsNotEmpty(licensePlateNumber);

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
  constructor(token, sdkUrl = null) {
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
    console.debug("Api Base: " + this.apiBase);
  }

  async uploadBase64(encodedImage, camera, timestamp, params) {
    console.debug(params);
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
    return fetchWithRetry(url, init);
  }
}
