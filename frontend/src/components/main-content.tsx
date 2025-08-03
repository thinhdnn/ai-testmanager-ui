"use client"

import React from "react"
import { cn } from "@/lib/utils"

interface MainContentProps {
  children: React.ReactNode
  className?: string
  maxWidth?: "full" | "centered" | "compact"
  spacing?: "sm" | "md" | "lg"
}

export function MainContent({ 
  children, 
  className, 
  maxWidth = "full",
  spacing = "lg"
}: MainContentProps) {
  const maxWidthClasses = {
    full: "",
    centered: "max-w-7xl mx-auto",
    compact: "max-w-4xl mx-auto"
  }

  const spacingClasses = {
    sm: "space-y-4",
    md: "space-y-5", 
    lg: "space-y-6"
  }

  return (
    <div className={cn("flex-1 flex flex-col", className)}>
      {/* Main content area with standard layout */}
      <div className="flex-1">
        <div className={cn(
          "main-content-area",
          maxWidthClasses[maxWidth],
          spacingClasses[spacing]
        )}>
          {children}
        </div>
      </div>
    </div>
  )
} 