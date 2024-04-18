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
    const pTime = new Date(timestamp).toISOString();
    const data = {
      camera: camera,
      image: encodedImage,
      results: [
        {
          plate: licensePlateNumber,
          score: confidence,
          box: { xmin: 0, ymin: 0, ymax: 0, xmax: 0 },
        },
      ],
      time: pTime,
    };

    let tries = 0;
    const maxTries = 5;
    const init = {
      body: JSON.stringify(data),
      method: "POST",
      headers: {
        "content-type": "application/json",
        Authorization: "Token " + this.token,
      },
    };
    while (tries < maxTries) {
      var response;
      try {
        response = await fetch(this.apiBase + endpoint, init);
        console.debug("Response: " + response.status);
        if (response.ok) {
          console.info(`Logged Vehicle: ${licensePlateNumber}`);
          break;
        } else if (response.status === 429) {
          tries++;
          setTimeout(() => {}, 1000);
        } else {
          console.error("Error logging vehicle");
        }
      } catch (error) {
        console.error("Error", error);
        tries++;
        setTimeout(() => {}, 1000);
        continue;
      }
    }
  }
}
class VerkadaApi {
  constructor(apiKey) {
    this.apiKey = apiKey;
  }

  static async downloadImage(url) {
    try {
      const res = await fetch(url);
      if (res.ok) {
        const blob = await res.blob();
        const reader = new FileReader();
        reader.readAsDataURL(blob);
        return new Promise((resolve) => {
          reader.onloadend = function () {
            resolve(reader.result.split(",")[1]);
          };
        });
      } else {
        console.debug("downloadImage res:", res);
      }
    } catch (error) {
      console.error("error", error);
    }
  }

  async getSeenLicensePlateImage(cameraId, timestamp, plate) {
    const params = {
      page_size: 5,
      camera_id: cameraId,
      license_plate: plate,
      start_time: timestamp - 1,
      end_time: timestamp + 1,
    };
    const url = "https://api.verkada.com/cameras/v1/analytics/lpr/images";
    const headers = {
      accept: "application/json",
      "x-api-key": this.apiKey,
    };
    try {
      const response = await fetch(`${url}?${new URLSearchParams(params)}`, {
        headers,
      });
      if (response.ok) {
        const data = await response.json();
        for (const detection of data.detections) {
          if (
            detection.timestamp === timestamp &&
            detection.license_plate === plate
          ) {
            return await VerkadaApi.downloadImage(detection.image_url);
          }
        }
      } else {
        console.error(response.statusText);
      }
    } catch (error) {
      console.error("error", error);
    }
  }
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
    for (let message of batch.messages) {
      // Process each message (we'll just log these)
      const data = message.body["data"];
      let cameraId = data["camera_id"];
      let createdAt = data["created"];
      let confidence = data["confidence"];
      let licensePlateNumber = data["license_plate_number"];

      let image = verkada.getSeenLicensePlateImage(
        cameraId,
        createdAt,
        licensePlateNumber,
      );
      if (image) {
        await parkpow.logVehicle(
          image,
          licensePlateNumber,
          confidence,
          cameraId,
          createdAt,
        );
      } else {
        console.error(
          `Skip webhook - [${licensePlateNumber}] at ${createdAt} - Missing image`,
        );
      }
    }
  },
};
