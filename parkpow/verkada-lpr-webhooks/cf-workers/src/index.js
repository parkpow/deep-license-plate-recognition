import { Buffer } from "node:buffer";

class Error429 extends Error {
  constructor({ message, response }) {
    super(message);
    this.name = "429Error";
    this.data = response;
  }
}

class Error5xx extends Error {
  constructor({ message, response }) {
    super(message);
    this.name = "5xxError";
    this.data = response;
  }
}

const wait = (delay) => new Promise((resolve) => setTimeout(resolve, delay));

const fetchWithRetry = (url, init, tries = 2) =>
  fetch(url, init)
    .then((response) => {
      if (response.ok) {
        return response;
      } else {
        // 1. throw a new exception
        if (response.status === 429)
          throw new Error429("Rate Limited", response);
        if (response.status >= 500 && response.status <= 599)
          throw new Error5xx(`Server Error`, response);
        // 2. reject instead of throw, peferred
        return Promise.reject(response);
      }
    })
    .catch((error) => {
      console.error(`fetchWithRetry error: ${error}`);
      if (error instanceof Error429 || error instanceof Error5xx || tries < 1) {
        throw error;
      } else {
        //Retry network error or 5xx errors
        const delay = 1000;
        return wait(delay).then(() => fetchWithRetry(url, init, tries - 1));
      }
    });

class ParkPowApi {
  constructor(token, sdkUrl = null) {
    if (token === null) {
      throw new Error("ParkPow TOKEN is required if using Cloud API");
    } else {
      this.token = token;
    }
    if (sdkUrl) {
      this.apiBase = sdkUrl + "/api/v1/";
    } else {
      this.apiBase = "https://app.parkpow.com/api/v1/";
    }
    console.debug("Api Base: " + this.apiBase);
  }

  async logVehicle(
    encodedImage,
    licensePlateNumber,
    confidence,
    camera,
    timestamp,
  ) {
    const endpoint = "log-vehicle/";
    const pTime = new Date(timestamp * 1000).toISOString();
    const data = {
      camera: camera,
      image: encodedImage,
      results: [
        {
          plate: licensePlateNumber,
          score: confidence,
          // box: { xmin: 0, ymin: 0, ymax: 0, xmax: 0 },
        },
      ],
      time: pTime,
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
    return fetchWithRetry(url, init, 5).then((response) => response.json());
  }
}
class VerkadaApi {
  constructor(apiKey) {
    this.apiKey = apiKey;
  }

  static async downloadImage(url) {
    return fetchWithRetry(url, {}).then(async (res) => {
      const buffer = await res.arrayBuffer();
      return Buffer.from(buffer).toString("base64");
    });
  }

  async getSeenLicensePlateImage(cameraId, timestamp, plate) {
    const params = {
      page_size: 5,
      camera_id: cameraId,
      license_plate: plate,
      start_time: timestamp - 1,
      end_time: timestamp + 1,
    };
    const endpoint = "https://api.verkada.com/cameras/v1/analytics/lpr/images";
    let init = {
      headers: {
        accept: "application/json",
        "x-api-key": this.apiKey,
      },
    };
    const url = `${endpoint}?${new URLSearchParams(params)}`;
    console.log(`LPR Images url : ${url}`);
    return fetchWithRetry(url, init).then(async (res) => {
      const data = await res.json();
      console.log(`Data: ${JSON.stringify(data)}`);
      for (const detection of data["detections"]) {
        if (
          detection["timestamp"] === timestamp &&
          detection["license_plate"] === plate
        ) {
          return detection["image_url"];
        }
      }
      return Promise.reject("Detection not found");
    });
  }
}

async function processWebhook(data, verkada, parkpow) {
  let cameraId = data["camera_id"];
  let createdAt = data["created"];
  let confidence = data["confidence"];
  let licensePlateNumber = data["license_plate_number"];

  return verkada
    .getSeenLicensePlateImage(cameraId, createdAt, licensePlateNumber)
    .then((imageUrl) => {
      console.log("Download Image from URL: " + imageUrl);
      return VerkadaApi.downloadImage(imageUrl);
    })
    .then((imageBase64) => {
      console.log("Log vehicle");
      return parkpow.logVehicle(
        imageBase64,
        licensePlateNumber,
        confidence,
        cameraId,
        createdAt,
      );
    });
}

export default {
  // Our fetch handler is invoked on a HTTP request: we can send a message to a queue
  // during (or after) a request.
  // https://developers.cloudflare.com/queues/platform/javascript-apis/#producer
  async fetch(request, env, ctx) {
    if (request.method === "POST") {
      const contentType = request.headers.get("content-type");
      if (contentType.includes("application/json")) {
        const data = await request.json();
        const webhookType = data["webhook_type"];
        if (webhookType !== "lpr") {
          return new Response(`Unexpected webhook type: ${webhookType}`, {
            status: 400,
          });
        }
        await env.LPR_WEBHOOKS.send(data);
        return new Response("OK!");
      } else {
        return new Response("Error - Required application/json ", {
          status: 400,
        });
      }
    } else {
      return new Response("Error - Required POST", { status: 400 });
    }
  },

  // The queue handler is invoked when a batch of messages is ready to be delivered
  // https://developers.cloudflare.com/queues/platform/javascript-apis/#messagebatch
  async queue(batch, env) {
    const verkada = new VerkadaApi(env.VERKADA_API_KEY);
    const parkpow = new ParkPowApi(env.PARKPOW_TOKEN, env.PARKPOW_URL);

    // A queue consumer can make requests to other endpoints on the Internet,
    // write to R2 object storage, query a D1 Database, and much more.
    for (const message of batch.messages) {
      // Process each message (we'll just log these)
      console.log(`Message: ${JSON.stringify(message.body)}`);
      const data = message.body["data"];
      const result = await processWebhook(data, verkada, parkpow);
      console.info(`Logged Vehicle: ${JSON.stringify(result)}`);
      // Explicitly acknowledge the message as delivered
      message.ack();
    }
  },
};
