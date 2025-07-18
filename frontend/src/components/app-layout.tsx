"use client"

import React, { useState } from "react"
import { Sidebar } from "./sidebar"
import { MainContent } from "./main-content"
import { UserProfile } from "./user-profile"
import { useUser } from "@/contexts/UserContext"

interface AppLayoutProps {
  children: React.ReactNode
  title?: string
}

export function AppLayout({ children, title }: AppLayoutProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const user = useUser();

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
        <header className="header-container">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-4">
              {title && (
                <h1 className="text-xl font-semibold text-foreground">
                  {title}
                </h1>
              )}
            </div>
            <div className="flex items-center gap-4">
              <UserProfile user={user ?? undefined} />
            </div>
          </div>
        </header>
        
        {/* Main content */}
        <MainContent>
          {children}
        </MainContent>
      </div>
    </div>
  )
}

export default AppLayout 