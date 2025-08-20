import { fetchWithRetry } from "./utils";

const ORIENTATION_FRONT = "Front";
const ORIENTATION_REAR = "Rear";
const ORIENTATION_UNKNOWN = "Unknown";

export class ParkPowApi {
  constructor(token, sdkUrl = null, retryLimit = 5, retryDelay = 2000) {
    this.retryLimit = retryLimit;
    this.retryDelay = retryDelay;
    if (token === null) {
      throw new Error("ParkPow API token is required for authentication.");
    } else {
      this.token = token;
    }
    if (sdkUrl) {
      this.apiBase = sdkUrl;
    } else {
      this.apiBase = "https://app.parkpow.com";
    }
    // Include API VERSION
    this.apiBase = `${this.apiBase}/api/v1/`;
    // console.debug("Api Base: " + this.apiBase);
  }

  /**
   * Use Log Vehicle API because image is already in base64 from camera
   * https://app.parkpow.com/documentation/#tag/Visits/operation/Create%20Visit%20(Send%20Camera%20Images%20and%20License%20Plate%20Data)
   * @param encodedImage
   * @param result
   * @param timestamp
   * @param cameraId
   * @returns {Promise<*>}
   */
  async logVehicle(encodedImage, result, cameraId, timestamp) {
    console.debug(JSON.stringify(result));
    const endpoint = "log-vehicle/";
    const data = {
      camera: cameraId,
      image: encodedImage,
      results: [result], // TODO Add handling of multiple results
      time: timestamp,
    };
    let init = {
      body: JSON.stringify(data),
      method: "POST",
      headers: {
        "Content-type": "application/json",
        Authorization: "Token " + this.token,
      },
    };
    const url = this.apiBase + endpoint;
    return fetchWithRetry(url, init, this.retryLimit, this.retryDelay).then(
      (res) => res.json(),
    );
  }
}

export const PARKPOW_ORIENTATION_FRONT = ORIENTATION_FRONT;
export const PARKPOW_ORIENTATION_REAR = ORIENTATION_REAR;
export const PARKPOW_ORIENTATION_UNKNOWN = ORIENTATION_UNKNOWN;
