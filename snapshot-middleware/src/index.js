import { SnapshotApi, SnapshotResponse } from "./snapshot";
import { ENABLED_CAMERAS } from "./cameras";
import { UnexpectedApiResponse } from "./exceptions";
import { ParkPowApi } from "./parkpow";
import { validInt } from "./utils";

function requestParams(request) {
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
    parkpowForwarding: searchParams.get("parkpow_forwarding"),
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
 * Integration URL will configure processor, if not then fallback to the checking of headers
 */
export default {
  async fetch(request, env, ctx) {
    if (request.method === "POST") {
      const contentType = request.headers.get("content-type");
      const contentLength = request.headers.get("content-length");
      const cntLength = validInt(contentLength, -1);
      if (contentType?.includes("application/json") && cntLength > 0) {
        const data = await request.json();
        const snapshot = new SnapshotApi(
          env.SNAPSHOT_TOKEN,
          env.SNAPSHOT_URL,
          validInt(env.SNAPSHOT_RETRY_LIMIT, 5),
          validInt(env.RETRY_DELAY, 2000),
        );
        const params = requestParams(request);
        console.debug(`Params: ${JSON.stringify(params)}`);
        const processorSelection = validInt(params.processorSelection, -1);
        console.debug(`Processor Selection: ${processorSelection}`);
        const CameraClass = findProcessor(processorSelection, request, data);
        console.debug(`CameraClass: ${CameraClass}`);
        if (CameraClass) {
          let cameraData;
          try {
            cameraData = new CameraClass(request, data);
            console.debug(`CameraData Instance: ${cameraData}`);
          } catch (e) {
            const errMsg =
              processorSelection > -1
                ? "Specified Processor Unable Process Camera Data"
                : "Invalid Camera Data";
            return new Response(
              `Processor Error - ${processorSelection} - ${errMsg}`,
              { status: 400 },
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
              console.debug(`Snapshot results: ${ssRes.results}`);
              // check config to forward to ParkPow
              let parkPowForwardingEnabled = !!params.parkpowForwarding;
              // Create camera result to forward if Snapshot empty
              if (parkPowForwardingEnabled && ssRes.results.length === 0) {
                ssRes.overwritePlate(cameraData.plate);
                ssRes.overwriteOrientation(
                  cameraData.orientation,
                  cameraData.plate,
                );
                ssRes.overwriteDirection(
                  cameraData.direction,
                  cameraData.plate,
                );
              } else {
                if (params.overwritePlate) {
                  parkPowForwardingEnabled = true;
                  ssRes.overwritePlate(cameraData.plate);
                }
                if (params.overwriteOrientation) {
                  parkPowForwardingEnabled = true;
                  ssRes.overwriteOrientation(
                    cameraData.orientation,
                    cameraData.plate,
                  );
                }
                if (params.overwriteDirection) {
                  parkPowForwardingEnabled = true;
                  ssRes.overwriteDirection(
                    cameraData.direction,
                    cameraData.plate,
                  );
                }
                if (params.parkpowCameraIds) {
                  parkPowForwardingEnabled = true;
                }
              }

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
                if (params.parkpowCameraIds) {
                  const parkPowCameraIds = params.parkpowCameraIds.split(",");
                  const promises = parkPowCameraIds.map((parkPowCameraId) =>
                    parkPow.logVehicle(
                      cameraData.imageBase64,
                      ssRes.result,
                      parkPowCameraId,
                      ssRes.timestamp,
                    ),
                  );
                  resData = await Promise.all(promises);
                } else {
                  resData = await parkPow.logVehicle(
                    cameraData.imageBase64,
                    ssRes.result,
                    ssRes.cameraId,
                    ssRes.timestamp,
                  );
                }
              } else {
                resData = ssRes.data;
              }
              // console.debug(`resString: ${resString}`)
              return new Response(JSON.stringify(resData), {
                headers: { "Content-Type": "application/json" },
              });
            })
            .catch((error) => {
              if (error instanceof UnexpectedApiResponse) {
                return new Response(error.message, { status: error.status });
              } else {
                throw error;
              }
            });
        } else {
          return new Response(
            "Error - Invalid Request Content or Wrong Processor",
            {
              status: 400,
            },
          );
        }
      } else {
        return new Response(
          "Error - Expected Content-Type application/json and Content-Length > 0",
          { status: 400 },
        );
      }
    } else {
      return new Response("Error - Required POST", { status: 400 });
    }
  },
};
