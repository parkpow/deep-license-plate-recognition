"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
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
import { Car, Camera, Map, Info } from "lucide-react";

interface PlateDetailsModalProps {
  data: WebhookData;
  isOpen: boolean;
  onClose: () => void;
}

export function PlateDetailsModal({
  data,
  isOpen,
  onClose,
}: PlateDetailsModalProps) {
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
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            License Plate Details
            <Badge variant="outline" className="ml-2 uppercase">
              {plateNumber}
            </Badge>
            {plateScore && (
              <Badge variant="secondary" className="ml-1">
                Score: {(plateScore * 100).toFixed(1)}%
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>

        <Tabs
          defaultValue="details"
          className="flex-1 overflow-hidden flex flex-col"
        >
          <TabsList>
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="image">Image</TabsTrigger>
            <TabsTrigger value="json">Raw JSON</TabsTrigger>
          </TabsList>

          <TabsContent value="details" className="flex-1 overflow-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Vehicle Information */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <Car className="h-4 w-4 mr-2" />
                    Vehicle Information
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Type:</dt>
                      <dd>{vehicleType}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Make:</dt>
                      <dd>{vehicleMake}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Model:</dt>
                      <dd>{vehicleModel}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Color:</dt>
                      <dd>{vehicleColor}</dd>
                    </div>
                  </dl>
                </CardContent>
              </Card>

              {/* Detection Information */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <Camera className="h-4 w-4 mr-2" />
                    Detection Information
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Camera ID:</dt>
                      <dd>{cameraId}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Timestamp:</dt>
                      <dd>{timestamp}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Region:</dt>
                      <dd>{region || "N/A"}</dd>
                    </div>
                    {regionScore && (
                      <div className="flex justify-between">
                        <dt className="text-muted-foreground">Region Score:</dt>
                        <dd>{(regionScore * 100).toFixed(1)}%</dd>
                      </div>
                    )}
                  </dl>
                </CardContent>
              </Card>

              {/* Movement Information */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <Map className="h-4 w-4 mr-2" />
                    Movement Information
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Direction:</dt>
                      <dd>{direction}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Speed:</dt>
                      <dd>{speed}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Source:</dt>
                      <dd className="truncate max-w-[200px]">
                        {(hasValidResults &&
                          typeof data.data.results[0].source_url === "string" &&
                          data.data.results[0].source_url) ||
                          "N/A"}
                      </dd>
                    </div>
                  </dl>
                </CardContent>
              </Card>

              {/* Additional Information */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <Info className="h-4 w-4 mr-2" />
                    Additional Information
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Confidence:</dt>
                      <dd>
                        {hasValidResults &&
                        data.data.results[0].score !== undefined
                          ? `${(data.data.results[0].score * 100).toFixed(1)}%`
                          : "N/A"}
                      </dd>
                    </div>
                    {orientation && (
                      <div className="flex justify-between">
                        <dt className="text-muted-foreground">Orientation:</dt>
                        <dd>{orientation}</dd>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Event:</dt>
                      <dd>{data.hook?.event || "N/A"}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Received:</dt>
                      <dd>
                        {data.receivedAt ? formatDate(data.receivedAt) : "N/A"}
                      </dd>
                    </div>
                  </dl>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="json" className="flex-1 overflow-auto">
            <pre className="bg-muted p-4 rounded-md overflow-auto text-xs h-full">
              {JSON.stringify(data, null, 2)}
            </pre>
          </TabsContent>
          <TabsContent value="image" className="flex-1 overflow-auto">
            <div className="flex justify-center items-center">
              {imageurl ? (
                <img
                  src={imageurl}
                  alt={`Vehicle for plate ${plateNumber}`}
                  className="rounded-lg shadow-lg w-full h-auto max-h-[500px] object-contain"
                />
              ) : (
                <div className="border-2 border-dashed border-gray-300 rounded-lg w-full h-[300px] flex items-center justify-center text-gray-500 italic">
                  No image available
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
