"use client"

import React from "react"
import { cn } from "@/lib/utils"

interface MainContentProps {
  children: React.ReactNode
  className?: string
  title?: string
}

export function MainContent({ children, className, title }: MainContentProps) {
  return (
    <div className={cn("flex-1 flex flex-col", className)}>
      {/* Header area for title if provided */}
      {title && (
        <div className="border-b border-border/10 p-6">
          <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
        </div>
      )}
      
      {/* Main content area with custom styling */}
      <div className="flex-1">
        <div className="main-content-area">
          {children}
        </div>
      </div>
    </div>
  )
} 