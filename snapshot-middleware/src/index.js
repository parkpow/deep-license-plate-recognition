import { SnapshotApi, SnapshotResponse } from "./snapshot";
import { ENABLED_CAMERAS } from "./cameras";
import { UnexpectedApiResponse } from "./exceptions";
import { ParkPowApi } from "./parkpow";
import { validInt } from "./utils";

function requestParams(request, parkpowForwardingDefault) {
  const { searchParams } = new URL(request.url);
  return {
    mmc: searchParams.get("mmc"),
    camera_id: searchParams.get("camera_id"),
    regions: searchParams.get("regions"),
    config: searchParams.get("config"),
    processorSelection: searchParams.get("processor_selection"),
    overwritePlate: searchParams.get("overwrite_plate"),
    overwriteDirection: searchParams.get("overwrite_direction"),
    overwriteOrientation: searchParams.get("overwrite_orientation"),
    parkpowForwarding:
      searchParams.get("parkpow_forwarding") ||
      validInt(parkpowForwardingDefault),
    parkpowCameraIds: searchParams.get("parkpow_camera_ids"),
  };
}

/**
 * Select a processor automatically or as specified
 * @param selection
 * @param request
 * @param data
 * @returns {Survision | Genetec}
 */
function findProcessor(selection, request, data) {
  return ENABLED_CAMERAS.find((element, index) => {
    if (selection > -1) {
      // Fixed Selection by ID
      return element.selectionId === selection;
    } else {
      // Automated selection from the request formats
      return element.validRequest(request, data);
    }
  });
}

/**
 * Utility function to log error responses to console
 * @param data
 * @param status
 * @returns {Response}
 */
function loggedResponse(data, status = 400) {
  console.log(`${status}-${data}`);
  return new Response(data, { status: status });
}

/**
 * Perform ParkPow overwrite operations and turn on forwarding
 * @param forwardingEnabled
 * @param ssRes
 * @param cameraData
 * @param params
 * @returns {boolean}
 */
function overwriteOps(forwardingEnabled, ssRes, cameraData, params) {
  // Create camera result to forward if Snapshot empty
  if (forwardingEnabled && ssRes.isEmpty()) {
    ssRes.overwritePlate(cameraData.plate);
    ssRes.overwriteOrientation(cameraData.orientation, cameraData.plate);
    ssRes.overwriteDirection(cameraData.direction, cameraData.plate);
  } else {
    if (params.overwritePlate) {
      forwardingEnabled = true;
      ssRes.overwritePlate(cameraData.plate);
    }
    if (params.overwriteOrientation) {
      forwardingEnabled = true;
      ssRes.overwriteOrientation(cameraData.orientation, cameraData.plate);
    }
    if (params.overwriteDirection) {
      forwardingEnabled = true;
      ssRes.overwriteDirection(cameraData.direction, cameraData.plate);
    }
    if (params.parkpowCameraIds) {
      forwardingEnabled = true;
    }
  }

  return forwardingEnabled;
}

/**
 * Integration URL will configure processor, if not then fallback to the checking of headers
 */
export default {
  async fetch(request, env, ctx) {
    if (request.method === "POST") {
      const contentType = request.headers.get("content-type");
      const contentLength = request.headers.get("content-length");
      const cntLength = validInt(contentLength, -1);
      if (contentType?.includes("application/json") && cntLength > 0) {
        let data;
        try {
          data = await request.json();
        } catch (e) {
          return loggedResponse("Error - Could not parse submitted JSON body.");
        }
        const snapshot = new SnapshotApi(
          env.SNAPSHOT_TOKEN,
          env.SNAPSHOT_URL,
          validInt(env.SNAPSHOT_RETRY_LIMIT, 5),
          validInt(env.RETRY_DELAY, 2000),
        );
        const params = requestParams(request, env.PARKPOW_FORWARDING);
        //console.debug(`Params: ${JSON.stringify(params)}`);
        const processorSelection = validInt(params.processorSelection, -1);
        //console.debug(`Processor Selection: ${processorSelection}`);
        const CameraClass = findProcessor(processorSelection, request, data);
        if (CameraClass) {
          let cameraData;
          try {
            cameraData = new CameraClass(request, data);
            console.debug(JSON.stringify(cameraData.debugLog));
          } catch (e) {
            const errMsg =
              processorSelection > -1
                ? "Specified Processor Unable Process Camera Data"
                : "Invalid Camera Data";
            console.debug(JSON.stringify(data));
            return loggedResponse(
              `Processor Error - ${processorSelection} - ${errMsg}`,
            );
          }
          return snapshot
            .uploadBase64(
              cameraData.imageBase64,
              cameraData.cameraId,
              cameraData.createdDate,
              params,
            )
            .then(
              async (response) => new SnapshotResponse(await response.json()),
            )
            .then(async (ssRes) => {
              // console.debug(`Snapshot results: ${ssRes.results}`);
              // check config to forward to ParkPow
              let parkPowForwardingEnabled = overwriteOps(
                !!params.parkpowForwarding,
                ssRes,
                cameraData,
                params,
              );

              let resData;
              // By default, the response should be Snapshot response
              //  unless manually forwarded to ParkPow then it's ParkPow response
              if (parkPowForwardingEnabled) {
                let parkPow = new ParkPowApi(
                  env.PARKPOW_TOKEN,
                  env.PARKPOW_URL,
                  validInt(env.PARKPOW_RETRY_LIMIT, 5),
                  validInt(env.RETRY_DELAY, 2000),
                );
                let parkPowCameraIds = [ssRes.cameraId];
                if (params.parkpowCameraIds) {
                  parkPowCameraIds = params.parkpowCameraIds.split(",");
                }
                const promises = parkPowCameraIds.map((parkPowCameraId) =>
                  parkPow
                    .logVehicle(
                      cameraData.imageBase64,
                      ssRes.result,
                      parkPowCameraId,
                      ssRes.timestamp,
                    )
                    .catch((error) => {
                      return { error: error.message };
                    }),
                );
                resData = await Promise.all(promises);
              } else {
                resData = ssRes.data;
              }
              const resString = JSON.stringify(resData);
              console.log(resString);
              return new Response(resString, {
                headers: { "Content-Type": "application/json" },
              });
            })
            .catch((error) => {
              if (error instanceof UnexpectedApiResponse) {
                return loggedResponse(error.message, error.status);
              } else {
                throw error;
              }
            });
        } else {
          return loggedResponse(
            "Error - Invalid Request Content or Wrong Processor",
          );
        }
      } else {
        return loggedResponse(
          "Error - Expected Content-Type application/json and Content-Length > 0",
        );
      }
    } else {
      return loggedResponse("Error - Required POST");
    }
  },
};
