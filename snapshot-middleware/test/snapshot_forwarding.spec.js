import {
  env,
  createExecutionContext,
  waitOnExecutionContext,
  fetchMock,
} from "cloudflare:test";
import {
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  test,
} from "vitest";

import worker from "../src/index";

import GenetecSamplePayload from "./Genetec.json";
import GenetecSnapshotResponse from "./GenetecSnapshot.json";
import SurvisionSamplePayload from "./Survision.json";
import SurvisionSnapshotResponse from "./SurvisionSnapshot.json";

import { PROCESSOR_GENETEC } from "../src/cameras";
import {
  WORKER_REQUEST_INPUT,
  SURVISION_HEADERS_DEFAULT,
  createJsonUploadRequest,
} from "./utils";

beforeAll(() => {
  // throw errors if an outbound request isn't mocked
  fetchMock.disableNetConnect();
});

beforeEach(() => fetchMock.activate());

afterEach(() => {
  fetchMock.assertNoPendingInterceptors();
  fetchMock.deactivate();
});

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

  describe("Uploads Images from camera to Snapshot", async () => {
    // Parametrize tests https://www.the-koi.com/projects/parameterized-data-driven-tests-in-vitest-example/
    const cameraSampleCases = [
      ["genetec", GenetecSamplePayload, {}, GenetecSnapshotResponse],
      [
        "survision",
        SurvisionSamplePayload,
        SURVISION_HEADERS_DEFAULT,
        SurvisionSnapshotResponse,
      ],
    ];
    test.each(cameraSampleCases)(
      "Uploads Images In Request to Snapshot: - %s - ",
      async (camera, payload, headers, mockSnapshotResponse) => {
        fetchMock
          .get(import.meta.env.SNAPSHOT_BASE_URL)
          .intercept({ path: "/v1/plate-reader/", method: "POST" })
          .reply(200, mockSnapshotResponse);

        let req = createJsonUploadRequest(
          WORKER_REQUEST_INPUT,
          payload,
          headers,
        );
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
  });

  it("Retries Rate Limits", async () => {
    const rateLimitResponse = {
      detail: "Request was throttled. Expected available in 1 second.",
      status_code: 429,
    };

    fetchMock
      .get(import.meta.env.SNAPSHOT_BASE_URL)
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

  it("Errors when GENETEC processor from GET `processor_selection` is used on Survision", async () => {
    const url = `${WORKER_REQUEST_INPUT}?processor_selection=${PROCESSOR_GENETEC}`;
    const req = createJsonUploadRequest(
      url,
      SurvisionSamplePayload,
      SURVISION_HEADERS_DEFAULT,
    );
    // Create an empty context to pass to `worker.fetch()`
    let ctx = createExecutionContext();
    let response = await worker.fetch(req, env, ctx);
    // Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
    await waitOnExecutionContext(ctx);
    expect(await response.status).toBe(400);
    expect(await response.text()).toStrictEqual(
      "Processor Error - 2 - Specified Processor Unable Process Camera Data",
    );
  });
});
