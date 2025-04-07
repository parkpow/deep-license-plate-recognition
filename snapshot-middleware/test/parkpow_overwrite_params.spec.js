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

import GenetecSamplePayload from "./assets/Genetec.json";
import GenetecSnapshotResponse from "./assets/GenetecSnapshot.json";
import SurvisionSamplePayload from "./assets/Survision.json";
import SurvisionSnapshotResponse from "./assets/SurvisionSnapshot.json";
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

describe("Overwrite Parameters", async () => {
  const overwriteParamEmpty = [
    // param, input, expectedResult
    [
      "overwrite_plate",
      1,
      {
        plate: "9HKA742",
        score: 0.9,
        candidates: [{ plate: "9HKA742", score: 0.9 }],
      },
    ],
    ["overwrite_direction", 1, { direction: 90, plate: "9HKA742", score: 0.9 }],
    [
      "overwrite_orientation",
      1,
      {
        orientation: [{ orientation: "Rear", score: 0.9 }],
        plate: "9HKA742",
        score: 0.9,
      },
    ],
  ];
  test.each(overwriteParamEmpty)(
    "Empty results Param: %s ",
    async (param, input, modifiedResult) => {
      fetchMock
        .get(import.meta.env.SNAPSHOT_BASE_URL)
        .intercept({ path: "/v1/plate-reader/", method: "POST" })
        .reply(200, GenetecSnapshotResponse);

      fetchMock
        .get(import.meta.env.PARKPOW_BASE_URL)
        .intercept({ path: "/api/v1/log-vehicle/", method: "POST" })
        .reply(200, ({ body }) => {
          // throw new Error(body)
          return body;
        });
      const url = `${WORKER_REQUEST_INPUT}?${param}=${input}`;
      let req = createJsonUploadRequest(url, GenetecSamplePayload, {});
      let ctx = createExecutionContext();
      let response = await worker.fetch(req, env, ctx);
      await waitOnExecutionContext(ctx);
      expect(await response.status).toBe(200);
      const responseJson = await response.json();
      expect(responseJson["time"]).toBe("2024-10-24T17:29:26Z");
      expect(responseJson["camera"]).toBe("G637821011231200521C - Camera");
      expect(responseJson["results"]).toStrictEqual([modifiedResult]);
    },
  );

  const overwrittenPlateResult = {
    box: { xmin: 693, ymin: 681, xmax: 988, ymax: 759 },
    plate: "MW818WM",
    region: { code: "fr", score: 0.816 },
    score: 1,
    candidates: [
      { score: 1, plate: "MW818WM" },
      { score: 0.864, plate: "mw81bwm" },
      {
        score: 0.864,
        plate: "mw8i8wm",
      },
      { score: 0.864, plate: "mwb18wm" },
      { score: 0.728, plate: "mw8ibwm" },
      {
        score: 0.728,
        plate: "mwb1bwm",
      },
      { score: 0.728, plate: "mwbi8wm" },
      { score: 0.593, plate: "mwbibwm" },
    ],
    dscore: 0.883,
    vehicle: {
      score: 0.414,
      type: "Unknown",
      box: { xmin: 385, ymin: 142, xmax: 1446, ymax: 921 },
    },
    model_make: [
      { make: "generic", model: "Invalid", score: 0.761 },
      {
        make: "generic",
        model: "Unknown",
        score: 0.008,
      },
    ],
    color: [
      { color: "black", score: 0.426 },
      { color: "white", score: 0.385 },
      {
        color: "silver",
        score: 0.066,
      },
    ],
    orientation: [
      { orientation: "Rear", score: 0.685 },
      {
        orientation: "Unknown",
        score: 0.246,
      },
      { orientation: "Front", score: 0.07 },
    ],
    direction: 81,
    direction_score: 0.999,
  };
  const overwrittenDirectionResult = {
    box: { xmin: 693, ymin: 681, xmax: 988, ymax: 759 },
    plate: "mw818wm",
    region: { code: "fr", score: 0.816 },
    score: 1,
    candidates: [
      { score: 1, plate: "mw818wm" },
      { score: 0.864, plate: "mw81bwm" },
      {
        score: 0.864,
        plate: "mw8i8wm",
      },
      { score: 0.864, plate: "mwb18wm" },
      { score: 0.728, plate: "mw8ibwm" },
      {
        score: 0.728,
        plate: "mwb1bwm",
      },
      { score: 0.728, plate: "mwbi8wm" },
      { score: 0.593, plate: "mwbibwm" },
    ],
    dscore: 0.883,
    vehicle: {
      score: 0.414,
      type: "Unknown",
      box: { xmin: 385, ymin: 142, xmax: 1446, ymax: 921 },
    },
    model_make: [
      { make: "generic", model: "Invalid", score: 0.761 },
      {
        make: "generic",
        model: "Unknown",
        score: 0.008,
      },
    ],
    color: [
      { color: "black", score: 0.426 },
      { color: "white", score: 0.385 },
      {
        color: "silver",
        score: 0.066,
      },
    ],
    orientation: [
      { orientation: "Rear", score: 0.685 },
      {
        orientation: "Unknown",
        score: 0.246,
      },
      { orientation: "Front", score: 0.07 },
    ],
    direction: "Unknown",
    direction_score: 0.999,
  };
  const overwrittenOrientationResult = {
    box: { xmin: 693, ymin: 681, xmax: 988, ymax: 759 },
    plate: "mw818wm",
    region: { code: "fr", score: 0.816 },
    score: 1,
    candidates: [
      { score: 1, plate: "mw818wm" },
      { score: 0.864, plate: "mw81bwm" },
      { score: 0.864, plate: "mw8i8wm" },
      { score: 0.864, plate: "mwb18wm" },
      { score: 0.728, plate: "mw8ibwm" },
      { score: 0.728, plate: "mwb1bwm" },
      { score: 0.728, plate: "mwbi8wm" },
      { score: 0.593, plate: "mwbibwm" },
    ],
    dscore: 0.883,
    vehicle: {
      score: 0.414,
      type: "Unknown",
      box: { xmin: 385, ymin: 142, xmax: 1446, ymax: 921 },
    },
    model_make: [
      { make: "generic", model: "Invalid", score: 0.761 },
      { make: "generic", model: "Unknown", score: 0.008 },
    ],
    color: [
      { color: "black", score: 0.426 },
      { color: "white", score: 0.385 },
      { color: "silver", score: 0.066 },
    ],
    orientation: [
      { orientation: null, score: 0.685 },
      { orientation: "Unknown", score: 0.246 },
      { orientation: "Front", score: 0.07 },
    ],
    direction: 81,
    direction_score: 0.999,
  };

  const overwriteParamNonEmpty = [
    // param, input, expectedResult
    ["overwrite_plate", 1, overwrittenPlateResult],
    ["overwrite_direction", 1, overwrittenDirectionResult],
    ["overwrite_orientation", 1, overwrittenOrientationResult],
  ];
  test.each(overwriteParamNonEmpty)(
    "Non-Empty results Param: %s",
    async (param, input, modifiedResult) => {
      fetchMock
        .get(import.meta.env.SNAPSHOT_BASE_URL)
        .intercept({ path: "/v1/plate-reader/", method: "POST" })
        .reply(200, SurvisionSnapshotResponse);

      const client = fetchMock.get(import.meta.env.PARKPOW_BASE_URL);
      client
        .intercept({ path: "/api/v1/log-vehicle/", method: "POST" })
        .reply(200, ({ body }) => {
          return body;
        });
      const url = `${WORKER_REQUEST_INPUT}?${param}=${input}`;
      let req = createJsonUploadRequest(
        url,
        SurvisionSamplePayload,
        SURVISION_HEADERS_DEFAULT,
      );
      let ctx = createExecutionContext();
      let response = await worker.fetch(req, env, ctx);
      await waitOnExecutionContext(ctx);
      expect(await response.status).toBe(200);
      const responseJson = await response.json();
      expect(responseJson["time"]).toBe("2024-10-17T23:04:50.098000Z");
      expect(responseJson["camera"]).toBe("sv1-searial-1");
      expect(responseJson["results"]).toStrictEqual([modifiedResult]);
    },
  );
});
