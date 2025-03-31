import { fetchWithRetry } from "./utils";
import { UnexpectedApiResponse } from "./exceptions";

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

  overwritePlate(responseJson, cameraPlate) {
    throw new Error("Not Implemented");
  }

  overwriteDirection(responseJson, cameraOrientation) {
    throw new Error("Not Implemented");
  }

  overwriteOrientation(responseJson, cameraOrientation) {
    throw new Error("Not Implemented");
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
