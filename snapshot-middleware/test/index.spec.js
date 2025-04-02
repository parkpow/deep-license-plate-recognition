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

const WORKER_REQUEST_INPUT = "http://snapshot-middleware.platerecognizer.com";

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

  it("No Expected Content-Type - Expected Content-Type application/json and Content-Length > 0", async () => {
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

  test.each([
    ["genetec", GenetecSamplePayload, {}, GenetecSnapshotResponse],
    [
      "survision",
      SurvisionSamplePayload,
      { "survision-serial-number": "sv1-searial-1" },
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
      expect(await response.text()).toBe("Success");

      // TODO by default the response should be Snapshot response
      //  unless manually forwarded to ParkPow then it's ParkPow response
      expect(await response.text()).toBe(mockSnapshotResponse);
    },
  );

  it("Retries Rate Limits", async () => {
    // Fake Timers https://github.com/cloudflare/workers-sdk/blob/main/fixtures/vitest-pool-workers-examples/misc/test/fake-timers.test.ts
    throw new Error("Not Implemented");
  });

  it("Forwards Back Response", async () => {
    throw new Error("Not Implemented");
  });

  it("Invalid Request has Error Response", async () => {
    throw new Error("Not Implemented");
  });
});

describe("ParkPow Upload", () => {
  /**
   * ParkPow API should now also be called
   * Response cotnains ParkPow Response
   */
  it("ParkPow Forwarding Param", async () => {
    throw new Error("Not Implemented");
  });

  it("Forwards Image and snapshot response to ParkPow", async () => {
    throw new Error("Not Implemented");
  });

  it("retries rate limits", async () => {
    throw new Error("Not Implemented");
  });

  it("Forwards Back Response To User", async () => {
    throw new Error("Not Implemented");
  });

  it("Overwrite Params", async () => {
    throw new Error("Not Implemented");
  });

  it("Invalid Request has Error Response", async () => {
    throw new Error("Not Implemented");
  });
});
