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
  vi,
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

import { ParkPowApi } from "../src/parkpow";

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
  let logVehicleSpy;

  beforeEach(() => {
    logVehicleSpy = vi
      .spyOn(ParkPowApi.prototype, "logVehicle")
      .mockResolvedValue({});
  });

  afterEach(() => {
    logVehicleSpy.mockRestore();
  });

  const overwriteParamEmpty = [
    // param, input
    ["overwrite_plate", 1],
    ["overwrite_direction", 1],
    ["overwrite_orientation", 1],
  ];
  test.each(overwriteParamEmpty)(
    "Empty results Param: %s ",
    async (param, input) => {
      fetchMock
        .get(import.meta.env.SNAPSHOT_BASE_URL)
        .intercept({ path: "/v1/plate-reader/", method: "POST" })
        .reply(200, GenetecSnapshotResponse);

      const url = `${WORKER_REQUEST_INPUT}?${param}=${input}`;
      let req = createJsonUploadRequest(url, GenetecSamplePayload, {});
      let ctx = createExecutionContext();

      let response = await worker.fetch(req, env, ctx);
      await waitOnExecutionContext(ctx);
      expect(response.status).toBe(200);
      const responseJson = await response.json();
      expect(responseJson["results"].length).toBe(0);

      // ParkPow API call should not happen because of empty Snapshot results
      expect(logVehicleSpy).not.toHaveBeenCalled();
    },
  );

  const overwrittenPlateResult = { plate: "MW818WM" };
  const overwrittenDirectionResult = {
    direction: null,
  };
  const overwrittenOrientationResult = {
    orientation: [
      { orientation: "Unknown", score: 0.685 },
      { orientation: "Unknown", score: 0.246 },
      { orientation: "Front", score: 0.07 },
    ],
  };

  const overwriteParamNonEmpty = [
    // param, input, expectedResult
    ["overwrite_plate", overwrittenPlateResult],

    ["overwrite_direction", overwrittenDirectionResult],
    ["overwrite_orientation", overwrittenOrientationResult],
  ];
  test.each(overwriteParamNonEmpty)(
    "Non-Empty results Param: %s",
    async (param, modifiedProp) => {
      let mockedSnapshotResponse = SurvisionSnapshotResponse;
      if (param === "overwrite_plate") {
        const deepCopy = JSON.parse(JSON.stringify(SurvisionSnapshotResponse));
        deepCopy["results"][0]["plate"] = "DIFFPLATE";
        deepCopy["results"][0]["candidates"][0]["plate"] = "DIFFPLATE";
        mockedSnapshotResponse = deepCopy;
      }

      fetchMock
        .get(import.meta.env.SNAPSHOT_BASE_URL)
        .intercept({ path: "/v1/plate-reader/", method: "POST" })
        .reply(200, mockedSnapshotResponse);

      const url = `${WORKER_REQUEST_INPUT}?${param}=1`;
      let req = createJsonUploadRequest(
        url,
        SurvisionSamplePayload,
        SURVISION_HEADERS_DEFAULT,
      );

      let ctx = createExecutionContext();
      let response = await worker.fetch(req, env, ctx);
      await waitOnExecutionContext(ctx);

      expect(response.status).toBe(200);
      expect(await response.json()).toStrictEqual(mockedSnapshotResponse);

      expect(logVehicleSpy).toHaveBeenCalled();

      expect(logVehicleSpy).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining(modifiedProp),
        expect.any(String),
        expect.any(String),
      );
    },
  );
});
