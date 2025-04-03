export const WORKER_REQUEST_INPUT =
  "http://snapshot-middleware.platerecognizer.com";
export const SURVISION_HEADERS_DEFAULT = {
  "survision-serial-number": "sv1-searial-1",
};
/**
 * Create Expected Request from cameras with relevant headers and payload
 * @param input
 * @param jsonData
 * @param extraHeaders
 * @returns {Request}
 */
export function createJsonUploadRequest(input, jsonData, extraHeaders = {}) {
  const bodyJson = JSON.stringify(jsonData);
  return new Request(input, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "content-length": bodyJson.length,
      ...extraHeaders,
    },
    body: bodyJson,
  });
}
