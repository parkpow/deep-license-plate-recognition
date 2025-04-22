"use client"

import { useState, useEffect, useRef } from "react"
import { Input } from "@/components/ui/input"
import { UniversalPlateCard } from "@/components/universal-plate-card"
import { PlateDetailsModal } from "@/components/plate-details-modal"
import type { WebhookData } from "@/types/webhook"
import { Search } from "lucide-react"

interface LicensePlateSidebarProps {
  data: WebhookData[]
  searchTerm: string
  onSearchChange: (term: string) => void
}

export function LicensePlateSidebar({ data, searchTerm, onSearchChange }: LicensePlateSidebarProps) {
  const [selectedPlate, setSelectedPlate] = useState<WebhookData | null>(null)
  const [lastDataLength, setLastDataLength] = useState(data.length)
  const [newPlateId, setNewPlateId] = useState<string | null>(null)
  const prevDataRef = useRef<WebhookData[]>([])

  // Filter and sort plates (newest first)
  const filteredData = data
    .filter((item) => {
      // Check if item and item.data exist
      if (!item || !item.data) {
        return false
      }

      // Check if results array exists and has items
      if (!item.data.results || !Array.isArray(item.data.results) || item.data.results.length === 0) {
        return false
      }

      const firstResult = item.data.results[0]

      // Get plate number for filtering
      let plateText = "Unknown Plate"

      // Handle Type 1 format
      if (firstResult.plate && typeof firstResult.plate === "string") {
        plateText = firstResult.plate
      }
      // Handle Type 2 format
      else if (
        firstResult.plate &&
        typeof firstResult.plate === "object" &&
        firstResult.plate.props?.plate?.[0]?.value
      ) {
        plateText = firstResult.plate.props.plate[0].value
      }

      // If search term is empty, show all plates (including "Unknown Plate")
      if (!searchTerm) {
        return true
      }

      // Otherwise, filter by the search term
      return plateText.toLowerCase().includes(searchTerm.toLowerCase())
    })
    .sort((a, b) => {
      // Sort by receivedAt timestamp (newest first)
      const timeA = a.receivedAt ? new Date(a.receivedAt).getTime() : 0
      const timeB = b.receivedAt ? new Date(b.receivedAt).getTime() : 0
      return timeB - timeA
    })

  // Detect new plates and activate animation
  useEffect(() => {
    // If we have more data than before, a new plate was added
    if (data.length > lastDataLength && data.length > 0) {
      // Find the most recent plate
      const sortedData = [...data].sort((a, b) => {
        const timeA = a.receivedAt ? new Date(a.receivedAt).getTime() : 0
        const timeB = b.receivedAt ? new Date(b.receivedAt).getTime() : 0
        return timeB - timeA
      })

      // Generate a unique ID for the new plate (using timestamp)
      const newId = `plate-${Date.now()}`
      setNewPlateId(newId)

      // Remove highlight after 2 seconds
      setTimeout(() => {
        setNewPlateId(null)
      }, 2000)
    }

    setLastDataLength(data.length)
    prevDataRef.current = data
  }, [data, lastDataLength])

  return (
    <>
      <div className="flex flex-col h-full overflow-hidden">
        {/* Search bar fixed at top */}
        <div className="p-3 border-b sticky top-0 bg-white z-10 flex-shrink-0">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search plate..."
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-8"
            />
          </div>
          <div className="text-xs text-muted-foreground mt-1 text-right">
            {filteredData.length} {filteredData.length === 1 ? "plate" : "plates"}
          </div>
        </div>

        {/* Scrollable plate list - ONLY THIS PART IS SCROLLABLE */}
        <div className="flex-1 overflow-y-auto p-2">
          {filteredData.length === 0 ? (
            <div className="flex items-center justify-center h-full text-center p-4">
              <p className="text-muted-foreground">
                {data.length > 0 ? "No plates match your search" : "No plate data available"}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredData.map((item, index) => {
                // Generate a unique ID for each plate
                const plateId = `plate-${index}-${item.receivedAt || Date.now()}`
                // Check if this is the new plate
                const isNewPlate = index === 0 && newPlateId !== null

                return (
                  <UniversalPlateCard
                    key={plateId}
                    data={item}
                    onClick={() => setSelectedPlate(item)}
                    isNew={isNewPlate}
                  />
                )
              })}
            </div>
          )}
        </div>
      </div>

      {selectedPlate && (
        <PlateDetailsModal data={selectedPlate} isOpen={!!selectedPlate} onClose={() => setSelectedPlate(null)} />
      )}
    </>
  )
}
