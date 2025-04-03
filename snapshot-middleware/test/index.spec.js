import {
  env,
  createExecutionContext,
  waitOnExecutionContext,
  fetchMock,
} from "cloudflare:test";
import {
  afterAll,
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  vi,
  MockInstance,
  test,
} from "vitest";

import worker from "../src/index";

import GenetecSamplePayload from "./Genetec.json";
import GenetecSnapshotResponse from "./GenetecSnapshot.json";
import SurvisionSamplePayload from "./Survision.json";
import SurvisionSnapshotResponse from "./SurvisionSnapshot.json";
import { isMockActive, MockAgent, setDispatcher } from "cloudflare:mock-agent";

const WORKER_REQUEST_INPUT = "http://snapshot-middleware.platerecognizer.com";
const SURVISION_HEADERS_DEFAULT = {
  "survision-serial-number": "sv1-searial-1",
};

beforeAll(() => {
  // throw errors if an outbound request isn't mocked
  fetchMock.disableNetConnect();
});

beforeEach(() => fetchMock.activate());
afterEach(() => {
  fetchMock.assertNoPendingInterceptors();
  fetchMock.deactivate();
});

/**
 * Create Expected Request from cameras with relevant headers and payload
 * @param input
 * @param jsonData
 * @param extraHeaders
 * @returns {Request}
 */
function createJsonUploadRequest(input, jsonData, extraHeaders = {}) {
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

describe("Snapshot Upload", () => {
  it("GET Response Error - Required POST", async () => {
    const request = new Request(WORKER_REQUEST_INPUT);
    // Create an empty context to pass to `worker.fetch()`
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, env, ctx);

    // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
    await waitOnExecutionContext(ctx);
    expect(await response.status).toBe(400);
    expect(await response.text()).toBe("Error - Required POST");
  });

  it("No Content-Length Headers - Expected Content-Type application/json and Content-Length > 0", async () => {
    const request = new Request(WORKER_REQUEST_INPUT, {
      method: "POST",
    });
    // Create an empty context to pass to `worker.fetch()`
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, env, ctx);
    // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
    await waitOnExecutionContext(ctx);
    expect(await response.status).toBe(400);
    expect(await response.text()).toBe(
      "Error - Expected Content-Type application/json and Content-Length > 0",
    );
  });

  it("Unexpected Content-Type - Expected Content-Type application/json and Content-Length > 0", async () => {
    const request = new Request(WORKER_REQUEST_INPUT, {
      method: "POST",
      headers: {
        "content-Length": 10,
        "content-Type": "application/not-json",
      },
    });
    // Create an empty context to pass to `worker.fetch()`
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, env, ctx);
    // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
    await waitOnExecutionContext(ctx);
    expect(await response.status).toBe(400);
    expect(await response.text()).toBe(
      "Error - Expected Content-Type application/json and Content-Length > 0",
    );
  });

  // Parametrize tests https://www.the-koi.com/projects/parameterized-data-driven-tests-in-vitest-example/
  test.each([
    ["genetec", GenetecSamplePayload, {}, GenetecSnapshotResponse],
    [
      "survision",
      SurvisionSamplePayload,
      SURVISION_HEADERS_DEFAULT,
      SurvisionSnapshotResponse,
    ],
  ])(
    "Uploads Images In Request to Snapshot: - %s - ",
    async (camera, payload, headers, mockSnapshotResponse) => {
      fetchMock
        .get("https://api.platerecognizer.com")
        .intercept({ path: "/v1/plate-reader/", method: "POST" })
        .reply(200, mockSnapshotResponse);

      let req = createJsonUploadRequest(WORKER_REQUEST_INPUT, payload, headers);
      // Create an empty context to pass to `worker.fetch()`
      let ctx = createExecutionContext();
      let response = await worker.fetch(req, env, ctx);
      // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
      await waitOnExecutionContext(ctx);
      expect(await response.status).toBe(200);
      // By default, the response should be Snapshot response
      //  unless manually forwarded to ParkPow then it's ParkPow response
      expect(await response.json()).toStrictEqual(mockSnapshotResponse);
    },
  );

  it("Retries Rate Limits", async () => {
    const rateLimitResponse = {
      detail: "Request was throttled. Expected available in 1 second.",
      status_code: 429,
    };
    fetchMock
      .get("https://api.platerecognizer.com")
      .intercept({ path: "/v1/plate-reader/", method: "POST" })
      .reply(429, JSON.stringify(rateLimitResponse))
      .times(3);

    let req = createJsonUploadRequest(
      WORKER_REQUEST_INPUT,
      SurvisionSamplePayload,
      SURVISION_HEADERS_DEFAULT,
    );
    // Create an empty context to pass to `worker.fetch()`
    let ctx = createExecutionContext();
    let response = await worker.fetch(req, env, ctx);
    // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
    await waitOnExecutionContext(ctx);
    expect(await response.status).toBe(429);
    expect(await response.json()).toStrictEqual(rateLimitResponse);
  });

  const snapshotStatusCases = [
    [300, JSON.stringify({ detail: "Response 300" }), 1],
    [400, JSON.stringify({ detail: "Response 400" }), 1],
    [
      429,
      JSON.stringify({
        detail: "Request was throttled. Expected available in 1 second.",
        status_code: 429,
      }),
      3,
    ],
    [500, JSON.stringify({ detail: "Response 500" }), 3],
    [504, '<doc type="html">...', 3],
  ];
  test.each(snapshotStatusCases)(
    "Snapshot Status: %s is forwarded as worker response",
    async (status, mockSnapshotResponse, times) => {
      fetchMock
        .get("https://api.platerecognizer.com")
        .intercept({ path: "/v1/plate-reader/", method: "POST" })
        .reply(status, mockSnapshotResponse)
        .times(times);

      let req = createJsonUploadRequest(
        WORKER_REQUEST_INPUT,
        SurvisionSamplePayload,
        SURVISION_HEADERS_DEFAULT,
      ); // Create an empty context to pass to `worker.fetch()`
      let ctx = createExecutionContext();
      let response = await worker.fetch(req, env, ctx);
      // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
      await waitOnExecutionContext(ctx);
      expect(await response.status).toBe(status);
      // By default, the response should be Snapshot response
      //  unless manually forwarded to ParkPow then it's ParkPow response
      expect(await response.text()).toStrictEqual(mockSnapshotResponse);
    },
  );

  it("Overwrite Params", async () => {
    // TODO mock resData = await parkPow.logVehicle( and check params
    throw new Error("Not Implemented");
  });

  it("Generates Result from camera if Empty Snapshot Responses", async () => {
    // TODO mock resData = await parkPow.logVehicle( and check params

    throw new Error("Not Implemented");
  });
});

describe("ParkPow Forwarding", () => {
  /**
   * ParkPow API should now also be called
   * Response cotnains ParkPow Response
   */
  it("Forwards Normal(non-empty results) Snapshot Response", async () => {
    // 1. Normal Forwarding
    // 2. Blank Response from Snapshot

    throw new Error("Not Implemented");
  });

  it("Ignore Empty Snapshot Results", async () => {
    // 1. Normal Forwarding
    // 2. Blank Response from Snapshot

    throw new Error("Not Implemented");
  });

  // Parametrize tests https://www.the-koi.com/projects/parameterized-data-driven-tests-in-vitest-example/
  test.each([
    ["genetec", GenetecSamplePayload, {}, GenetecSnapshotResponse],
    [
      "survision",
      SurvisionSamplePayload,
      { "survision-serial-number": "sv1-searial-1" },
      SurvisionSnapshotResponse,
    ],
  ])(
    "Camera Overwrites Plate: - %s - ",
    async (camera, payload, headers, mockSnapshotResponse) => {
      fetchMock
        .get("https://api.platerecognizer.com")
        .request({ repeat: 1 })
        .intercept({ path: "/v1/plate-reader/", method: "POST" })

        .reply(200, mockSnapshotResponse);

      let req = createJsonUploadRequest(WORKER_REQUEST_INPUT, payload, headers);
      // Create an empty context to pass to `worker.fetch()`
      let ctx = createExecutionContext();
      let response = await worker.fetch(req, env, ctx);
      // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
      await waitOnExecutionContext(ctx);
      expect(await response.status).toBe(2400);
    },
  );

  it("retries rate limits", async () => {
    const rateLimitResponse = {
      detail: "TODO",
      status_code: 429,
    };
    fetchMock
      .get("https://api.platerecognizer.com")
      .intercept({ path: "/v1/plate-reader/", method: "POST" })
      .reply(200, SurvisionSamplePayload);

    fetchMock
      .get("https://app.parkpow.com")
      .intercept({ path: "/api/v1/log-vehicle/", method: "POST" })
      .reply(429, JSON.stringify(rateLimitResponse))
      .times(3);

    let req = createJsonUploadRequest(
      WORKER_REQUEST_INPUT + "?parkpow_forwarding=1",
      SurvisionSamplePayload,
      SURVISION_HEADERS_DEFAULT,
    );
    // Create an empty context to pass to `worker.fetch()`
    let ctx = createExecutionContext();
    let response = await worker.fetch(req, env, ctx);
    // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
    await waitOnExecutionContext(ctx);
    expect(await response.status).toBe(429);
    expect(await response.json()).toStrictEqual(rateLimitResponse);
  });

  it("ParkPow Response message and status is worker response", async () => {
    throw new Error("Not Implemented");
  });

  it("Invalid Request has Error Response", async () => {
    throw new Error("Not Implemented");
  });
});
