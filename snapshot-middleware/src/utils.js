import {
  Error429,
  Error5xx,
  InvalidIntValue,
  RetryLimit,
  UnexpectedApiResponse,
} from "./exceptions";
import { AwsClient } from "aws4fetch";

const wait = (delay) => new Promise((resolve) => setTimeout(resolve, delay));

export function fetchWithRetry(url, init, tries = 3, delay = 2000) {
  return fetch(url, init)
    .then(async (response) => {
      if (response.ok) {
        return response;
      } else {
        const responseText = await response.text();
        // 1. throw a new exception
        if (response.status === 429) throw new Error429(responseText);
        if (response.status >= 500 && response.status <= 599)
          throw new Error5xx(responseText, response.status);
        // console.error(responseText);
        // 2. reject instead of throw, preferred
        return Promise.reject(
          new UnexpectedApiResponse(responseText, response.status),
        );
      }
    })
    .catch((error) => {
      // Retry network error or 5xx errors
      if (error instanceof Error429 || error instanceof Error5xx) {
        if (tries <= 0) {
          throw new RetryLimit(error.message, error.status);
        }
        //console.log(`Retrying request: ${tries}`);
        // if the rate limit is reached or exceeded,
        return wait(delay).then(() => fetchWithRetry(url, init, tries - 1));
      } else {
        throw error;
      }
    });
}

export function validInt(i, fallBack = null) {
  if (i === null || i === "" || i === undefined || isNaN(i)) {
    if (fallBack != null) {
      return fallBack;
    }
    throw new InvalidIntValue(`Invalid int value - ${i}`);
  }
  return parseInt(i, 10);
}

function generateRandomString(length) {
  const characters =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < length; i++) {
    const randomIndex = Math.floor(Math.random() * characters.length);
    result += characters[randomIndex];
  }
  return result;
}

export async function uploadToS3(dataStr, env, processorId, cameraId) {
  const milliseconds = Date.now();

  const key = `${cameraId}-${milliseconds}-${generateRandomString(10)}.json`;
  // Build a signer for S3 (Linode) requests
  const aws = new AwsClient({
    accessKeyId: env.S3_ACCESS_KEY,
    secretAccessKey: env.S3_SECRET_KEY,
    service: "s3",
    region: env.S3_REGION,
  });
  const s3Url = `https://${env.S3_BUCKET}.${
    env.S3_ENDPOINT
  }/snapshot-middleware/${encodeURI(key)}`;
  const putRes = await aws.fetch(s3Url, {
    method: "PUT",
    headers: {
      "content-type": "application/json",
      // Optional: set ACL if you want the object to be public
      // 'x-amz-acl': 'public-read'
    },
    body: dataStr,
  });
  if (!putRes.ok) {
    const t = await putRes.text().catch(() => "");
    console.error(`S3 PUT failed: ${putRes.status} ${t}`);
  }
}
