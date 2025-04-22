import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function generateUUID() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0,
      v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function getBaseUrl() {
  if (typeof window !== "undefined") {
    return window.location.origin;
  }

  // For server-side rendering
  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}`;
  }

  // Fallback for local development
  return "http://localhost:3000";
}

export function formatDate(dateString: string) {
  if (!dateString) return "Unknown Date";

  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("en-US", {
      dateStyle: "short",
      timeStyle: "short",
    }).format(date);
  } catch (error) {
    console.error("Error formatting date:", error);
    return "Invalid Date";
  }
}

export function getPlateNumber(data: any): string {
  try {
    // Check if data has the expected structure
    if (!data?.data?.results?.[0]) {
      return "Unknown Plate";
    }

    const firstResult = data.data.results[0];

    // Handle Type 1 format
    if (firstResult.plate && typeof firstResult.plate === "string") {
      // If plate is empty or null, return "NO PLATE"
      return firstResult.plate.trim() === "" ? "NO PLATE" : firstResult.plate;
    }

    // Handle Type 2 format
    if (firstResult.plate?.props?.plate?.[0]?.value) {
      const plateValue = firstResult.plate.props.plate[0].value;
      return plateValue.trim() === "" ? "NO PLATE" : plateValue;
    }

    // If we get here, there's no valid plate
    return "NO PLATE";
  } catch (error) {
    console.error("Error getting plate number:", error);
    return "Unknown Plate";
  }
}

export function getPlateScore(data: any): number | null {
  try {
    // Check if data has the expected structure
    if (!data?.data?.results?.[0]) {
      return null;
    }

    const firstResult = data.data.results[0];

    // Handle Type 1 format
    if (firstResult.score !== undefined) {
      return firstResult.score;
    }

    // Handle Type 2 format
    if (firstResult.plate?.score !== undefined) {
      return firstResult.plate.score;
    }

    return null;
  } catch (error) {
    console.error("Error getting plate score:", error);
    return null;
  }
}

export function getRegion(data: any): string | null {
  try {
    // Check if data has the expected structure
    if (!data?.data?.results?.[0]) {
      return null;
    }

    const firstResult = data.data.results[0];

    // Handle Type 1 format
    if (firstResult.region?.code) {
      return firstResult.region.code.toUpperCase();
    }

    // Handle Type 2 format
    if (firstResult.plate?.props?.region?.[0]?.value) {
      return firstResult.plate.props.region[0].value.toUpperCase();
    }

    return null;
  } catch (error) {
    console.error("Error getting region:", error);
    return null;
  }
}

export function getRegionScore(data: any): number | null {
  try {
    // Check if data has the expected structure
    if (!data?.data?.results?.[0]) {
      return null;
    }

    const firstResult = data.data.results[0];

    // Handle Type 1 format
    if (firstResult.region?.score !== undefined) {
      return firstResult.region.score;
    }

    // Handle Type 2 format
    if (firstResult.plate?.props?.region?.[0]?.score !== undefined) {
      return firstResult.plate.props.region[0].score;
    }

    return null;
  } catch (error) {
    console.error("Error getting region score:", error);
    return null;
  }
}

export function getDirection(data: any): number | null {
  try {
    // Check if data has the expected structure
    if (!data?.data?.results?.[0]) {
      return null;
    }

    const firstResult = data.data.results[0];

    // Handle both Type 1 and Type 2 formats
    if (firstResult.direction !== null && firstResult.direction !== undefined) {
      return firstResult.direction;
    }

    return null;
  } catch (error) {
    console.error("Error getting direction:", error);
    return null;
  }
}

export function getVehicleOrientation(data: any): string | null {
  try {
    // Check if data has the expected structure
    if (!data?.data?.results?.[0]) {
      return null;
    }

    const firstResult = data.data.results[0];

    // Handle Type 1 format
    if (firstResult.orientation?.[0]?.orientation) {
      return firstResult.orientation[0].orientation;
    }

    // Handle Type 2 format
    if (firstResult.vehicle?.props?.orientation?.[0]?.value) {
      return firstResult.vehicle.props.orientation[0].value;
    }

    return null;
  } catch (error) {
    console.error("Error getting vehicle orientation:", error);
    return null;
  }
}

export function getVehicleType(data: any): string {
  try {
    // Check if data has the expected structure
    if (!data?.data?.results?.[0]) {
      return "Unknown Vehicle";
    }

    const firstResult = data.data.results[0];

    // Handle both Type 1 and Type 2 formats
    if (firstResult.vehicle?.type) {
      return firstResult.vehicle.type;
    }

    return "Unknown Vehicle";
  } catch (error) {
    console.error("Error getting vehicle type:", error);
    return "Unknown Vehicle";
  }
}

export function getVehicleMake(data: any): string {
  try {
    // Check if data has the expected structure
    if (!data?.data?.results?.[0]) {
      return "Unknown Make";
    }

    const firstResult = data.data.results[0];

    // Handle Type 1 format
    if (firstResult.model_make?.[0]?.make) {
      return firstResult.model_make[0].make;
    }

    // Handle Type 2 format
    if (firstResult.vehicle?.props?.make_model?.[0]?.make) {
      return firstResult.vehicle.props.make_model[0].make;
    }

    return "Unknown Make";
  } catch (error) {
    console.error("Error getting vehicle make:", error);
    return "Unknown Make";
  }
}

export function getVehicleModel(data: any): string {
  try {
    // Check if data has the expected structure
    if (!data?.data?.results?.[0]) {
      return "Unknown Model";
    }

    const firstResult = data.data.results[0];

    // Handle Type 1 format
    if (firstResult.model_make?.[0]?.model) {
      return firstResult.model_make[0].model;
    }

    // Handle Type 2 format
    if (firstResult.vehicle?.props?.make_model?.[0]?.model) {
      return firstResult.vehicle.props.make_model[0].model;
    }

    return "Unknown Model";
  } catch (error) {
    console.error("Error getting vehicle model:", error);
    return "Unknown Model";
  }
}

export function getVehicleColor(data: any): string {
  try {
    // Check if data has the expected structure
    if (!data?.data?.results?.[0]) {
      return "Unknown Color";
    }

    const firstResult = data.data.results[0];

    // Handle Type 1 format
    if (firstResult.color?.[0]?.color) {
      return firstResult.color[0].color;
    }

    // Handle Type 2 format
    if (firstResult.vehicle?.props?.color?.[0]?.value) {
      return firstResult.vehicle.props.color[0].value;
    }

    return "Unknown Color";
  } catch (error) {
    console.error("Error getting vehicle color:", error);
    return "Unknown Color";
  }
}

export function getCameraId(data: any): string {
  try {
    return data?.data?.camera_id || "Unknown Camera";
  } catch (error) {
    console.error("Error getting camera ID:", error);
    return "Unknown Camera";
  }
}

export function getTimestamp(data: any): string {
  try {
    return data?.data?.timestamp || "Unknown Time";
  } catch (error) {
    console.error("Error getting timestamp:", error);
    return "Unknown Time";
  }
}

export function getImageurl(data: any): string {
  try {
    return data?.image?.url || null;
  } catch (error) {
    console.error("Error getting Image:", error);
    return "Unknown Image";
  }
}

export const setStoredUuid = (uuid: string) => {
  if (typeof window !== "undefined") {
    localStorage.setItem("webhookUuid", uuid);
  }
};
