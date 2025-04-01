import {
  Error429,
  Error5xx,
  InvalidIntValue,
  RetryLimit,
  UnexpectedApiResponse,
} from "./exceptions";

const wait = (delay) => new Promise((resolve) => setTimeout(resolve, delay));

export function fetchWithRetry(url, init, tries = 3) {
  return fetch(url, init)
    .then(async (response) => {
      if (response.ok) {
        return response;
      } else {
        // 1. throw a new exception
        if (response.status === 429)
          throw new Error429("Rate Limited", response);
        if (response.status >= 500 && response.status <= 599)
          throw new Error5xx(`Server Error - ${response.status}`, response);
        const responseText = await response.text();
        console.error(responseText);
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
          throw new RetryLimit("Rate Limited");
        }
        console.log(`Retrying request: ${tries}`);
        // if the rate limit is reached or exceeded,
        const delay = 2000;
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
    throw new InvalidIntValue(`Invalid value for time - ${i}`);
  }
  return parseInt(i, 10);
}
