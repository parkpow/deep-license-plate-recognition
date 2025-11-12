"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ChevronDown, ChevronUp, Car } from "lucide-react"
import {
  formatDate,
  getPlateNumber,
  getVehicleType,
  getVehicleMake,
  getVehicleModel,
  getVehicleColor,
  getCameraId,
  getTimestamp,
} from "@/lib/utils"
import type { WebhookData } from "@/types/webhook"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"

interface LicensePlateCardProps {
  data: WebhookData
}

export function LicensePlateCard({ data }: LicensePlateCardProps) {
  const [expanded, setExpanded] = useState(false)

  // Add defensive checks for data access
  const plateNumber = getPlateNumber(data)
  const vehicleType = getVehicleType(data)
  const vehicleMake = getVehicleMake(data)
  const vehicleModel = getVehicleModel(data)
  const vehicleColor = getVehicleColor(data)
  const cameraId = getCameraId(data)
  const timestamp = formatDate(getTimestamp(data))

  // Check if we have valid results to display
  const hasValidResults = data?.data?.results?.[0]

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-xl font-mono uppercase">{plateNumber}</CardTitle>
          <Badge variant="outline">{vehicleType}</Badge>
        </div>
        <CardDescription>{timestamp}</CardDescription>
      </CardHeader>
      <CardContent className="pb-2">
        <div className="flex items-center gap-2">
          <Car className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">
            {vehicleColor} {vehicleMake} {vehicleModel}
          </span>
        </div>
        <div className="text-xs text-muted-foreground mt-1">Camera: {cameraId}</div>
      </CardContent>
      <CardFooter className="pt-0 flex justify-between">
        <Button variant="ghost" size="sm" onClick={() => setExpanded(!expanded)} className="text-xs">
          {expanded ? (
            <>
              <ChevronUp className="h-4 w-4 mr-1" /> Less
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4 mr-1" /> More
            </>
          )}
        </Button>
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              View JSON
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto">
            <DialogHeader>
              <DialogTitle>Raw JSON Data</DialogTitle>
            </DialogHeader>
            <pre className="bg-muted p-4 rounded-md overflow-auto text-xs">{JSON.stringify(data, null, 2)}</pre>
          </DialogContent>
        </Dialog>
      </CardFooter>

      {expanded && hasValidResults && (
        <div className="px-6 pb-4">
          <div className="border-t pt-2 space-y-2">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="text-muted-foreground">Direction</div>
              <div>
                {data.data.results[0].direction !== null && data.data.results[0].direction !== undefined
                  ? `${data.data.results[0].direction}°`
                  : "N/A"}
              </div>

              <div className="text-muted-foreground">Speed</div>
              <div>
                {data.data.results[0].speed !== null && data.data.results[0].speed !== undefined
                  ? `${data.data.results[0].speed} km/h`
                  : "N/A"}
              </div>

              <div className="text-muted-foreground">Source</div>
              <div className="truncate">
                {(typeof data.data.results[0].source_url === "string" && data.data.results[0].source_url) || "N/A"}
              </div>

              <div className="text-muted-foreground">Event</div>
              <div>{data.hook?.event || "N/A"}</div>
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}
