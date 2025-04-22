"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getPlateNumber,
  getVehicleType,
  getVehicleMake,
  getVehicleModel,
  getVehicleColor,
  getCameraId,
  formatDate,
  getTimestamp,
  getRegion,
  getRegionScore,
  getPlateScore,
  getVehicleOrientation,
  getImageurl,
} from "@/lib/utils";
import type { WebhookData } from "@/types/webhook";
import { Car, Camera, Clock, Map, Tag } from "lucide-react";

interface LastVehicleDetailsProps {
  data: WebhookData;
}

export function LastVehicleDetails({ data }: LastVehicleDetailsProps) {
  const plateNumber = getPlateNumber(data);
  const plateScore = getPlateScore(data);
  const vehicleType = getVehicleType(data);
  const vehicleMake = getVehicleMake(data);
  const vehicleModel = getVehicleModel(data);
  const vehicleColor = getVehicleColor(data);
  const cameraId = getCameraId(data);
  const timestamp = formatDate(getTimestamp(data));
  const region = getRegion(data);
  const regionScore = getRegionScore(data);
  const orientation = getVehicleOrientation(data);
  const imageurl = getImageurl(data);

  // Check if we have valid results to display
  const hasValidResults = data?.data?.results?.[0];

  // Get direction and speed safely
  const direction =
    hasValidResults &&
    data.data.results[0].direction !== null &&
    data.data.results[0].direction !== undefined
      ? `${data.data.results[0].direction}°`
      : "N/A";

  const speed =
    hasValidResults &&
    data.data.results[0].speed !== null &&
    data.data.results[0].speed !== undefined
      ? `${data.data.results[0].speed} km/h`
      : "N/A";

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg">Last Vehicle Detected</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Coluna 1: Plate + Infos */}
          <div>
            {/* Plate Number centralizado */}
            <div className="mb-6 flex justify-center">
              <div className="bg-gray-800 text-white px-8 py-4 rounded-lg shadow-lg">
                <div className="text-xs text-gray-300 mb-1 text-center">
                  PLATE
                </div>
                <div className="font-mono font-bold text-4xl tracking-wider text-center uppercase">
                  {plateNumber}
                </div>
              </div>
            </div>

            {/* Grid dos blocos de info: 2 colunas */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Plate Info */}
              <div className="p-4 border rounded-lg shadow-sm bg-muted/50">
                <div className="flex items-start gap-2 mb-2">
                  <Tag className="h-5 w-5 text-primary mt-0.5" />
                  <div className="font-medium text-sm">Plate Info</div>
                </div>
                <div className="text-sm space-y-1">
                  {plateScore && (
                    <div>Score: {(plateScore * 100).toFixed(1)}%</div>
                  )}
                  {region && <div>Region: {region}</div>}
                  {regionScore && (
                    <div>Region Score: {(regionScore * 100).toFixed(1)}%</div>
                  )}
                </div>
              </div>

              {/* Vehicle Info */}
              <div className="p-4 border rounded-lg shadow-sm bg-muted/50">
                <div className="flex items-start gap-2 mb-2">
                  <Car className="h-5 w-5 text-primary mt-0.5" />
                  <div className="font-medium text-sm">Vehicle</div>
                </div>
                <div className="text-sm space-y-1">
                  <div>Type: {vehicleType}</div>
                  <div>Model: {vehicleModel}</div>
                  <div>Make: {vehicleMake}</div>
                  <div>Color: {vehicleColor}</div>
                  {orientation && <div>Orientation: {orientation}</div>}
                  <div>Speed: {speed}</div>
                  <div>Direction: {direction}</div>
                </div>
              </div>

              {/* Camera Info */}
              <div className="p-4 border rounded-lg shadow-sm bg-muted/50">
                <div className="flex items-start gap-2 mb-2">
                  <Camera className="h-5 w-5 text-primary mt-0.5" />
                  <div className="font-medium text-sm">Camera</div>
                </div>
                <div className="text-sm space-y-1">
                  <div>Camera: {cameraId}</div>
                  {/* <div>{data.hook?.event || "Standard event"}</div> */}
                </div>
              </div>

              {/* Time Info */}
              <div className="p-4 border rounded-lg shadow-sm bg-muted/50">
                <div className="flex items-start gap-2 mb-2">
                  <Clock className="h-5 w-5 text-primary mt-0.5" />
                  <div className="font-medium text-sm">Time</div>
                </div>
                <div className="text-sm">{timestamp}</div>
              </div>
            </div>
          </div>

          {/* Coluna 2: Imagem */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-2 w-full h-[445px] flex items-center justify-center bg-white">
            {imageurl ? (
              <img
                src={imageurl}
                alt={`Vehicle for plate ${plateNumber}`}
                className="max-h-full max-w-full object-contain"
              />
            ) : (
              <span className="text-gray-500 italic">No image available</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
