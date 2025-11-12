import type React from "react"

interface LayoutProps {
  header: React.ReactNode
  sidebar: React.ReactNode
  main: React.ReactNode
}

export function Layout({ header, sidebar, main }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <div className="bg-white shadow z-10">{header}</div>

      {/* Main content with sidebar */}
      <div className="flex flex-1 overflow-hidden">
        {/* Main content area - not scrollable */}
        <div className="flex-1 p-6 overflow-y-auto">{main}</div>

        {/* Right sidebar - only internal content is scrollable */}
        <div className="w-80 border-l bg-white flex flex-col overflow-hidden">{sidebar}</div>
      </div>
    </div>
  )
}
