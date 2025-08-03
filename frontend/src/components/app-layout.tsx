"use client"

import React, { useState } from "react"
import { Sidebar } from "./sidebar"
import { MainContent } from "./main-content"
import { UserProfile } from "./user-profile"

interface AppLayoutProps {
  children: React.ReactNode
  title?: string
  actions?: React.ReactNode
  maxWidth?: "full" | "centered" | "compact"
  spacing?: "sm" | "md" | "lg"
}

export function AppLayout({ 
  children, 
  title, 
  actions,
  maxWidth = "full",
  spacing = "lg"
}: AppLayoutProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed)
  }

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <Sidebar 
        isCollapsed={isSidebarCollapsed} 
        onToggle={toggleSidebar}
      />
      
      {/* Main content area */}
      <div className={`main-content-container ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        {/* Top header with user profile */}
        <header className="header-container py-8 mb-6 border-b border-border/10 px-6">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-4">
              {title && (
                <h1 className="text-xl font-semibold text-foreground mb-2">
                  {title}
                </h1>
              )}
              {actions && (
                <div className="flex items-center gap-3">
                  {actions}
                </div>
              )}
            </div>
            <div className="flex items-center gap-4">
              <UserProfile />
            </div>
          </div>
        </header>
        
        {/* Main content with standard layout */}
        <MainContent 
          maxWidth={maxWidth}
          spacing={spacing}
        >
          {children}
        </MainContent>
      </div>
    </div>
  )
}

export default AppLayout 