import { SnapshotApi, SnapshotResponse } from "./snapshot";
import { ENABLED_CAMERAS } from "./cameras";
import { InvalidIntValue, UnexpectedApiResponse } from "./exceptions";
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
      const cntLength = validInt(request.headers.get("content-length"));

      if (contentType?.includes("application/json") && cntLength > 0) {
        const data = await request.json();
        const snapshot = new SnapshotApi(env.SNAPSHOT_TOKEN, env.SNAPSHOT_URL);
        const params = requestParams(request);
        console.debug(`Params: ${JSON.stringify(params)}`);
        const processorSelection = validInt(params.processorSelection, -1);
        console.debug(`Processor Selection: ${processorSelection}`);
        const CameraClass = findProcessor(processorSelection, request, data);
        console.debug(`CameraClass: ${CameraClass}`);
        if (CameraClass) {
          const processorInstance = new CameraClass(request, data);
          console.debug(`processorInstance: ${processorInstance}`);
          return snapshot
            .uploadBase64(
              processorInstance.imageBase64,
              processorInstance.cameraId,
              processorInstance.createdDate,
              params,
            )
            .then(
              async (response) => new SnapshotResponse(await response.json()),
            )
            .then(async (snapshotResponse) => {
              console.debug(
                `snapshotResponse.results: ${snapshotResponse.results}`,
              );
              // check config to forward to ParkPow
              let parkPowForwardingEnabled = false;
              if (params.parkpowForwarding) {
                parkPowForwardingEnabled = true;
              }
              if (params.overwritePlate) {
                parkPowForwardingEnabled = true;
                snapshotResponse.overwritePlate(processorInstance.plate);
              }
              if (params.overwriteOrientation) {
                parkPowForwardingEnabled = true;
                snapshotResponse.overwriteOrientation(
                  processorInstance.orientation,
                  processorInstance.plate,
                );
              }
              if (params.overwriteDirection) {
                parkPowForwardingEnabled = true;
                snapshotResponse.overwriteDirection(
                  processorInstance.direction,
                  processorInstance.plate,
                );
              }

              const res = { snapshot: snapshotResponse.result };
              if (parkPowForwardingEnabled) {
                const parkPow = new ParkPowApi(
                  env.PARKPOW_TOKEN,
                  env.PARKPOW_URL,
                );
                // include ParkPow response in final response
                res["parkPow"] = await parkPow.logVehicle(
                  processorInstance.imageBase64,
                  snapshotResponse.result,
                  snapshotResponse.cameraId,
                  snapshotResponse.timestamp,
                );
              }
              return new Response(JSON.stringify(res), {
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
