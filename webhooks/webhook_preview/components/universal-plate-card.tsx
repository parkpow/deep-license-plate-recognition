"use client";

import { Card } from "@/components/ui/card";
import {
  getPlateNumber,
  getTimestamp,
  formatDate,
  getRegion,
  getVehicleOrientation,
} from "@/lib/utils";
import type { WebhookData } from "@/types/webhook";
import { cn } from "@/lib/utils";

interface UniversalPlateCardProps {
  data: WebhookData;
  onClick: () => void;
  isNew?: boolean;
}

export function UniversalPlateCard({
  data,
  onClick,
  isNew = false,
}: UniversalPlateCardProps) {
  const plateNumber = getPlateNumber(data);
  const timestamp = formatDate(getTimestamp(data));
  const region = getRegion(data);
  const orientation = getVehicleOrientation(data);

  // Determine if this is a vehicle without a plate
  const hasNoPlate =
    plateNumber === "Unknown Plate" || plateNumber === "NO PLATE";

  return (
    <Card
      className={cn(
        "overflow-hidden cursor-pointer hover:shadow-md transition-shadow border-2",
        isNew && "animate-plate-highlight",
        hasNoPlate && "border-amber-300",
      )}
      onClick={onClick}
    >
      {/* Universal plate style */}
      <div
        className={cn(
          "p-3 text-center",
          hasNoPlate
            ? "bg-amber-50"
            : "bg-gradient-to-b from-gray-200 to-white",
        )}
      >
        <div className="font-mono font-bold text-2xl tracking-wider text-black uppercase">
          {plateNumber}
        </div>
      </div>

      {/* Vehicle info */}
      <div className="p-2 bg-gray-50 text-xs">
        <div className="flex justify-between">
          <span className="font-medium">
            {region ? `Region: ${region}` : "Unknown Region"}
          </span>
          <span className="text-muted-foreground">{timestamp}</span>
        </div>
        <div className="text-muted-foreground mt-1 truncate">
          {orientation ? `Orientation: ${orientation}` : ""}
        </div>
      </div>
    </Card>
  );
}
