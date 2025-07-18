"use client"

import React from "react"
import { 
  LayoutDashboard, 
  FolderKanban, 
  Rocket, 
  Users, 
  Settings,
  Menu
} from "lucide-react"
import { cn } from "@/lib/utils"

interface SidebarProps {
  className?: string
  isCollapsed?: boolean
  onToggle?: () => void
}

const menuItems = [
  {
    title: "Dashboard",
    icon: LayoutDashboard,
    href: "/dashboard"
  },
  {
    title: "Projects",
    icon: FolderKanban,
    href: "/projects"
  },
  {
    title: "Releases",
    icon: Rocket,
    href: "/releases"
  },
  {
    title: "Users",
    icon: Users,
    href: "/users"
  },
  {
    title: "Settings",
    icon: Settings,
    href: "/settings"
  }
]

export function Sidebar({ className, isCollapsed = false, onToggle }: SidebarProps) {
  return (
    <div 
      className={cn(
        "sidebar-container",
        isCollapsed ? "sidebar-collapsed" : "",
        className
      )}
    >
      {/* Sidebar Header */}
      <div className="flex items-center h-16 border-b border-border/10">
        {!isCollapsed ? (
          // Expanded state - show logo and button
          <div className="flex items-center justify-between gap-3 flex-1 px-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">AI</span>
              </div>
              <span className="font-semibold text-foreground">Test Manager</span>
            </div>
            <button
              onClick={onToggle}
              className="p-2 rounded-lg hover:bg-accent transition-colors flex items-center justify-center"
            >
              <Menu className="h-5 w-5" />
            </button>
          </div>
        ) : (
          // Collapsed state - center the button
          <div className="flex items-center justify-center w-full px-2">
            <button
              onClick={onToggle}
              className="w-full h-10 rounded-lg hover:bg-accent transition-colors flex items-center justify-center"
            >
              <Menu className="h-5 w-5" />
            </button>
          </div>
        )}
      </div>

      {/* Navigation Menu */}
      <nav className={cn(
        "flex-1",
        isCollapsed ? "px-2" : "px-4",
        "py-4"
      )}>
        <ul className="space-y-2">
          {menuItems.map((item) => (
            <li key={item.href}>
              <a
                href={item.href}
                className={cn(
                  "group relative flex items-center rounded-[20px] px-4 py-3 text-sm font-medium transition-all",
                  "hover:bg-accent hover:border hover:border-border text-foreground",
                  "focus:outline-none focus:bg-accent focus:border focus:border-border",
                  isCollapsed && "justify-center h-10 px-2"
                )}
              >
                <item.icon className={cn(
                  "h-6 w-6 shrink-0",
                  !isCollapsed && "mr-3",
                  isCollapsed && "mx-auto"
                )} />
                <span className={cn(
                  "transition-opacity duration-300",
                  isCollapsed ? "opacity-0 w-0 overflow-hidden" : "opacity-100"
                )}>
                  {item.title}
                </span>
                
                {/* Tooltip for collapsed state */}
                {isCollapsed && (
                  <div className="absolute left-full ml-3 px-3 py-2 bg-popover text-popover-foreground text-xs rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
                    {item.title}
                  </div>
                )}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
} 