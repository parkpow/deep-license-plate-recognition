import {
  PARKPOW_ORIENTATION_REAR,
  PARKPOW_ORIENTATION_FRONT,
  PARKPOW_ORIENTATION_UNKNOWN,
} from "./parkpow";
import { validInt } from "./utils";

const SURVISION = 1;
const GENETEC = 2;

class Camera {
  constructor(cameraId, imageBase64, createdDate, data) {
    if (this.constructor === Camera) {
      throw new Error("Class is of abstract type and can't be instantiated");
    }
    this.data = data;
    this.cameraId = cameraId;
    this.imageBase64 = imageBase64;
    this.createdDate = createdDate;
  }

  static get selectionId() {
    throw new Error("selectionId must be implemented in a subclass");
  }

  /**
   * Get Plate from this.data
   */
  get plate() {
    throw new Error("plate getter must be implemented in a subclass");
  }
  /**
   * Get Plate from this.data
   */
  get direction() {
    throw new Error("direction getter must be implemented in a subclass");
  }
  /**
   * Get Plate from this.data
   */
  get orientation() {
    throw new Error("orientation getter must be implemented in a subclass");
  }
  /**
   * Checks if the request or data(JSON payload) should be processed by this camera
   * @param request
   * @param data
   */
  static validRequest(request, data) {
    throw new Error("validRequest must be implemented in a subclass");
  }
  /**
   * Log Camera data without image to keep it within log limits
   */
  get debugLog() {
    throw new Error("debugLog must be implemented in a subclass");
  }
}

function alertForImplementation(dataString) {
  // Throw error to capture payload for fixing
  throw new Error(`Not Implemented: ${dataString}`);
}

class Survision extends Camera {
  static SERIAL_NUMBER_HEADER = "survision-serial-number";

  constructor(request, data) {
    let cameraId = request.headers.get(Survision.SERIAL_NUMBER_HEADER);
    let createdDate = new Date(validInt(data["anpr"]["@date"])).toISOString();
    let imageBase64 = data["anpr"]["decision"]["jpeg"];
    super(cameraId, imageBase64, createdDate, data);
  }

  static get selectionId() {
    return SURVISION;
  }

  static validRequest(request, data) {
    return (
      !!request.headers.get(Survision.SERIAL_NUMBER_HEADER) &&
      "anpr" in data &&
      "decision" in data["anpr"]
    );
  }

  get debugLog() {
    let copy = { ...this.data };
    // Clear image
    copy["anpr"]["decision"]["jpeg"] = "";
    return JSON.stringify(copy);
  }

  get plate() {
    return this.data["anpr"]["decision"]["@plate"];
  }
  get orientation() {
    const direction = this.data["anpr"]["decision"]["@direction"];
    if (direction === "unknown") {
      return PARKPOW_ORIENTATION_UNKNOWN;
    } else if (direction === "rear") {
      return PARKPOW_ORIENTATION_REAR;
    } else if (direction === "front") {
      return PARKPOW_ORIENTATION_FRONT;
    } else {
      alertForImplementation(JSON.stringify(this.data));
    }
  }

  get direction() {
    const direction = this.data["anpr"]["decision"]["@direction"];
    if (direction === "unknown") {
      return PARKPOW_ORIENTATION_UNKNOWN;
    } else if (direction === "rear") {
      return 90;
    } else if (direction === "front") {
      return 270;
    } else {
      alertForImplementation(JSON.stringify(this.data));
    }
  }
}

class Genetec extends Camera {
  constructor(request, data) {
    const cameraId = data["CameraName"];
    // "10/01/2022", Format DD/MM/YYYY
    const dateUtc = data["DateUtc"];
    let year, month, day;
    if (dateUtc.indexOf("-") > -1) {
      [year, month, day] = dateUtc.split("-");
    } else {
      [month, day, year] = dateUtc.split("/");
    }
    //  "11:49:22", Format HH/MM/SS
    const [hours, minutes, seconds] = data["TimeUtc"].split(":");
    const createdDate = new Date(
      validInt(year),
      validInt(month) - 1,
      validInt(day),
      validInt(hours),
      validInt(minutes),
      validInt(seconds),
    ).toISOString();
    const imageBase64 = data["ContextImage"];
    super(cameraId, imageBase64, createdDate, data);
  }

  static get selectionId() {
    return GENETEC;
  }

  get debugLog() {
    let copy = { ...this.data };
    // Clear image
    copy["ContextImage"] = "";
    copy["PlateImage"] = "";
    return JSON.stringify(copy);
  }
  get plate() {
    return this.data["Plate"];
  }
  get orientation() {
    const orientation = this.data["Attributes"]["Vehicle Orientation"];
    if (orientation === "BackSide") {
      // Assume Car is facing where it's going
      return PARKPOW_ORIENTATION_REAR;
    } else if (orientation === "Approaching") {
      // Assume Car is facing where it's going
      return PARKPOW_ORIENTATION_FRONT;
    } else {
      alertForImplementation(JSON.stringify(this.data));
    }
  }

  get direction() {
    const relativeMotion = this.data["Attributes"]["Relative Motion"];
    if (relativeMotion === "Moving Away") {
      // Assume Car going upward. 90°
      return 90;
    } else if (relativeMotion === "Approaching") {
      // Assume Car going downward. 270°
      return 270;
    } else {
      alertForImplementation(JSON.stringify(this.data));
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

export const ENABLED_CAMERAS = [Survision, Genetec];
export const PROCESSOR_SURVISION = SURVISION;
export const PROCESSOR_GENETEC = GENETEC;
