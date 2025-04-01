import { fetchWithRetry } from "./utils";

export class SnapshotResponse {
  constructor(data) {
    this._data = data;
    console.log(data);
  }

  overwritePlate(plate) {
    this.result["plate"] = plate;
    this.result["candidates"][0]["plate"] = plate;

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

  overwriteDirection(direction) {
    this.result["direction"] = direction;
    // TODO Overwrite plate scores
    //this.result['direction_score'] = null
  }

  overwriteOrientation(orientation) {
    this.result["orientation"][0]["orientation"] = orientation;
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
