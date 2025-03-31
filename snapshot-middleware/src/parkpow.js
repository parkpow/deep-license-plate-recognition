import { fetchWithRetry } from "./utils";

export class ParkPowApi {
  constructor(token, sdkUrl = null) {
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
    console.debug("Api Base: " + this.apiBase);
  }

  async webhookReceiver(encodedImage, data) {
    console.debug(params);
    const endpoint = "/api/v1/webhook-receiver/";

    const body = new FormData();
    body.set("upload", encodedImage);

    const payload = {
      hook: {
        target: "http://localhost:8081/",
        id: 2,
        event: "image.done",
      },
      data: data,
    };

    body.set("json", JSON.stringify(payload));

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
