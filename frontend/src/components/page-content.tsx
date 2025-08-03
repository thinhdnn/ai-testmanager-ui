"use client"

import React from "react"
import { cn } from "@/lib/utils"

interface PageContentProps {
  children: React.ReactNode
  className?: string
  title?: string
  actions?: React.ReactNode
  maxWidth?: "full" | "centered" | "compact"
  spacing?: "sm" | "md" | "lg"
  loading?: boolean
  error?: string | null
}

export function PageContent({ 
  children, 
  className,
  title,
  actions,
  maxWidth = "full",
  spacing = "lg",
  loading = false,
  error = null
}: PageContentProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="text-red-500 mb-2">⚠️</div>
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    )
  }

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
    <div className={cn(
      "page-content",
      maxWidthClasses[maxWidth],
      spacingClasses[spacing],
      className
    )}>
      {/* Page Header - only show if title or actions provided */}
      {(title || actions) && (
        <div className="flex justify-between items-center">
          {title && (
            <h1 className="text-2xl font-bold text-foreground">{title}</h1>
          )}
          {actions && (
            <div className="flex items-center gap-3">
              {actions}
            </div>
          )}
        </div>
      )}
      
      {/* Page Content */}
      {children}
    </div>
  )
}

// Predefined layouts for common use cases
export function FullWidthPage({ children, ...props }: Omit<PageContentProps, 'maxWidth'>) {
  return <PageContent maxWidth="full" {...props}>{children}</PageContent>
}

export function CenteredPage({ children, ...props }: Omit<PageContentProps, 'maxWidth'>) {
  return <PageContent maxWidth="centered" {...props}>{children}</PageContent>
}

export function CompactPage({ children, ...props }: Omit<PageContentProps, 'maxWidth'>) {
  return <PageContent maxWidth="compact" {...props}>{children}</PageContent>
} 