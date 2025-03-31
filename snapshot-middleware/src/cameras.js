const { SnapshotApi } = require("./snapshot");

const SURVISION = 1;
const GENETEC = 2;

class Camera {
  static PROCESSOR_ID = -1;

  constructor(cameraId, imageBase64, createdDate, data) {
    this.data = data;
    this.cameraId = cameraId;
    this.imageBase64 = imageBase64;
    this.createdDate = createdDate;
  }

  /**
   * Get Plate from this.data
   */
  get plate() {
    throw new Error("Not Implemented");
  }

  /**
   * Get Plate from this.data
   */
  get direction() {
    throw new Error("Not Implemented");
  }

  /**
   * Get Plate from this.data
   */
  get orientation() {
    throw new Error("Not Implemented");
  }

  /**
   * Checks if the request or data(JSON payload) should be processed by this camera
   * @param request
   * @param data
   */
  static validRequest(request, data) {
    throw Error("Not Implemented");
  }
}

class Survision extends Camera {
  static PROCESSOR_ID = SURVISION;
  static SERIAL_NUMBER_HEADER = "survision-serial-number";

  constructor(request, data) {
    let cameraId = request.headers.get(Survision.SERIAL_NUMBER_HEADER);
    let createdDate = new Date(validInt(data["anpr"]["@date"])).toISOString();
    let imageBase64 = data["anpr"]["decision"]["jpeg"];
    super(cameraId, imageBase64, createdDate, data);
  }

  static validRequest(request, data) {
    request.headers.get(Survision.SERIAL_NUMBER_HEADER);
  }

  get plate() {
    return this.data["anpr"]["decision"]["@plate"];
  }
  get orientation() {}

  get direction() {
    const direction = this.data["anpr"]["decision"]["@direction"];
    if (direction === "@direction") {
      return null;
    } else {
      throw new Error("Not Implemented");
    }
  }
}

class Genetec extends Camera {
  static PROCESSOR_ID = GENETEC;

  constructor(request, data) {
    let cameraId = data["CameraName"];
    // "10/01/2022", Format DD/MM/YYYY
    let dateUtc = data["DateUtc"];
    let year, month, day;
    if (dateUtc.indexOf("-") > -1) {
      [year, month, day] = dateUtc.split("-");
    } else {
      [month, day, year] = dateUtc.split("/");
    }
    //  "11:49:22", Format HH/MM/SS
    let [hours, minutes, seconds] = data["TimeUtc"].split(":");
    const createdDate = new Date(
      validInt(year),
      validInt(month) - 1,
      validInt(day),
      validInt(hours),
      validInt(minutes),
      validInt(seconds),
    ).toISOString();

    const imageBase64 = data["ContextImage"];
    super(cameraId, imageBase64, createdDate);
  }

  get plate() {
    return this.data["Plate"];
  }
  get orientation() {}

  get direction() {
    const relativeMotion = this.data["Attributes"]["Relative Motion"];
    if (relativeMotion === "Moving Away") {
    } else if (relativeMotion === "Approaching") {
    } else {
      throw new Error("Not Implemented");
    }
  }

  static validRequest(request, data) {
    return (
      "CameraName" in data &&
      "ContextImage" in data &&
      "DateUtc" in data &&
      "TimeUtc" in data
    );
  }
}

exports.ENABLED_CAMERAS = [Survision, Genetec];
exports.PROCESSOR_SURVISION = SURVISION;
exports.PROCESSOR_GENETEC = GENETEC;
