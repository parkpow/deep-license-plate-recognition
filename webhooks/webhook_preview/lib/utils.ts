import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { WebhookData, isType1, isType2 } from "@/types/webhook";

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

export function getPlateNumber(data: WebhookData): string {
  try {
    // Check if data has the expected structure
    if (!data?.data?.results?.[0]) {
      return "Unknown Plate";
    }

    if (isType1(data)) {
      const result = data.data.results[0];
      if (result.plate && typeof result.plate === "string") {
        return result.plate.trim() === "" ? "NO PLATE" : result.plate;
      }
    }

    if (isType2(data)) {
      const result = data.data.results[0];
      if (result.plate?.props?.plate?.[0]?.value) {
        const plateValue = result.plate.props.plate[0].value;
        return plateValue.trim() === "" ? "NO PLATE" : plateValue;
      }
    }

    // If we get here, there's no valid plate
    return "NO PLATE";
  } catch (error) {
    console.error("Error getting plate number:", error);
    return "Unknown Plate";
  }
}

export function getPlateScore(data: WebhookData): number | null {
  try {
    if (isType1(data)) {
      const result = data.data.results[0];
      return result.score ?? null;
    }

    if (isType2(data)) {
      const result = data.data.results[0];
      return result.plate?.score ?? null;
    }

    return null;
  } catch (error) {
    console.error("Error getting plate score:", error);
    return null;
  }
}

export function getRegion(data: WebhookData): string | null {
  try {
    if (isType1(data)) {
      const firstResult = data.data.results[0];
      return firstResult.region?.code?.toUpperCase() ?? null;
    }

    if (isType2(data)) {
      const firstResult = data.data.results[0];
      return (
        firstResult.plate?.props?.region?.[0]?.value?.toUpperCase() ?? null
      );
    }

    return null;
  } catch (error) {
    console.error("Error getting region:", error);
    return null;
  }
}

export function getRegionScore(data: WebhookData): number | null {
  try {
    if (isType1(data)) {
      const firstResult = data.data.results[0];
      return firstResult.region?.score ?? null;
    }

    if (isType2(data)) {
      const firstResult = data.data.results[0];
      return firstResult.plate?.props?.region?.[0]?.score ?? null;
    }

    return null;
  } catch (error) {
    console.error("Error getting region score:", error);
    return null;
  }
}

export function getDirection(data: WebhookData): number | null {
  try {
    if (isType1(data)) {
      const firstResult = data.data.results[0];
      return firstResult.direction ?? null;
    }

    if (isType2(data)) {
      const firstResult = data.data.results[0];
      return firstResult.direction ?? null;
    }

    return null;
  } catch (error) {
    console.error("Error getting direction:", error);
    return null;
  }
}

export function getVehicleOrientation(data: WebhookData): string | null {
  try {
    if (isType1(data)) {
      const firstResult = data.data.results[0];
      if (firstResult.orientation?.[0]?.orientation) {
        return firstResult.orientation[0].orientation;
      }
    }

    if (isType2(data)) {
      const firstResult = data.data.results[0];
      if (firstResult.vehicle?.props?.orientation?.[0]?.value) {
        return firstResult.vehicle.props.orientation[0].value;
      }
    }

    return null;
  } catch (error) {
    console.error("Error getting vehicle orientation:", error);
    return null;
  }
}

export function getVehicleType(data: WebhookData): string {
  try {
    if (isType1(data)) {
      const firstResult = data.data.results[0];
      if (firstResult.vehicle?.type) {
        return firstResult.vehicle.type;
      }
    }

    if (isType2(data)) {
      const firstResult = data.data.results[0];
      if (firstResult.vehicle?.type) {
        return firstResult.vehicle.type;
      }
    }

    return "Unknown Vehicle";
  } catch (error) {
    console.error("Error getting vehicle type:", error);
    return "Unknown Vehicle";
  }
}

export function getVehicleMake(data: WebhookData): string {
  try {
    if (isType1(data)) {
      const firstResult = data.data.results[0];
      if (firstResult.model_make?.[0]?.make) {
        return firstResult.model_make[0].make;
      }
    }

    if (isType2(data)) {
      const firstResult = data.data.results[0];
      if (firstResult.vehicle?.props?.make_model?.[0]?.make) {
        return firstResult.vehicle.props.make_model[0].make;
      }
    }

    return "Unknown Make";
  } catch (error) {
    console.error("Error getting vehicle make:", error);
    return "Unknown Make";
  }
}

export function getVehicleModel(data: WebhookData): string {
  try {
    if (isType1(data)) {
      const firstResult = data.data.results[0];
      if (firstResult.model_make?.[0]?.model) {
        return firstResult.model_make[0].model;
      }
    }

    if (isType2(data)) {
      const firstResult = data.data.results[0];
      if (firstResult.vehicle?.props?.make_model?.[0]?.model) {
        return firstResult.vehicle.props.make_model[0].model;
      }
    }

    return "Unknown Model";
  } catch (error) {
    console.error("Error getting vehicle model:", error);
    return "Unknown Model";
  }
}

export function getVehicleColor(data: WebhookData): string {
  try {
    if (isType1(data)) {
      const firstResult = data.data.results[0];
      if (firstResult.color?.[0]?.color) {
        return firstResult.color[0].color;
      }
    }

    if (isType2(data)) {
      const firstResult = data.data.results[0];
      if (firstResult.vehicle?.props?.color?.[0]?.value) {
        return firstResult.vehicle.props.color[0].value;
      }
    }

    return "Unknown Color";
  } catch (error) {
    console.error("Error getting vehicle color:", error);
    return "Unknown Color";
  }
}

export function getCameraId(data: WebhookData): string {
  try {
    return data?.data?.camera_id || "Unknown Camera";
  } catch (error) {
    console.error("Error getting camera ID:", error);
    return "Unknown Camera";
  }
}

export function getTimestamp(data: WebhookData): string {
  try {
    return data?.data?.timestamp || "Unknown Time";
  } catch (error) {
    console.error("Error getting timestamp:", error);
    return "Unknown Time";
  }
}

export function getImageurl(data: WebhookData): string | null {
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
