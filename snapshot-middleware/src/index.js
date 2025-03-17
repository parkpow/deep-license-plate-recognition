import { SnapshotApi } from "./snapshot";

function validGenetecEvent(data) {
  return (
    "CameraName" in data &&
    "ContextImage" in data &&
    "DateUtc" in data &&
    "TimeUtc" in data
  );
}

function validInt(i) {
  if (isNaN(i)) {
    throw new Error(`Invalid value for time - ${i}`);
  }
  return parseInt(i, 10);
}

function requestParams(request) {
  const { searchParams } = new URL(request.url);
  return {
    mmc: searchParams.get("mmc"),
    camera_id: searchParams.get("camera_id"),
    regions: searchParams.get("regions"),
    config: searchParams.get("config"),
  };
}

export default {
  async fetch(request, env, ctx) {
    if (request.method === "POST") {
      const contentType = request.headers.get("content-type");
      const cntLength = validInt(request.headers.get("content-length"));
      if (contentType?.includes("application/json") && cntLength > 0) {
        const data = await request.json();
        let cameraId = null;
        let imageBase64 = null;
        let createdDate = null;
        const snapshot = new SnapshotApi(env.SNAPSHOT_TOKEN, env.SNAPSHOT_URL);
        const survisionSerialNumber = request.headers.get(
          "survision-serial-number",
        );
        if (survisionSerialNumber) {
          cameraId = survisionSerialNumber;
          // sample 1729206290098
          createdDate = new Date(validInt(data["anpr"]["@date"])).toISOString();
          imageBase64 = data["anpr"]["decision"]["jpeg"];

          return await snapshot.uploadBase64(
            imageBase64,
            cameraId,
            createdDate,
            requestParams(request),
          );
        } else if (validGenetecEvent(data)) {
          cameraId = data["CameraName"];
          imageBase64 = data["ContextImage"];
          // "10/01/2022", Format DD/MM/YYYY
          const dateUtc = data["DateUtc"];
          let year, month, day;
          if (dateUtc.indexOf("-") > -1) {
            [year, month, day] = dateUtc.split("-");
          } else {
            [month, day, year] = dateUtc.split("/");
          }
          //  "11:49:22", Format HH/MM/SS
          let [hours, minutes, seconds] = data["TimeUtc"].split(":");
          createdDate = new Date(
            validInt(year),
            validInt(month) - 1,
            validInt(day),
            validInt(hours),
            validInt(minutes),
            validInt(seconds),
          ).toISOString();

          // Genetec camera data is larger than the queue limit (128 KB), we send directly
          return await snapshot.uploadBase64(
            imageBase64,
            cameraId,
            createdDate,
            requestParams(request),
          );
        } else {
          return new Response("Error - Invalid Request Content", {
            status: 400,
          });
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
