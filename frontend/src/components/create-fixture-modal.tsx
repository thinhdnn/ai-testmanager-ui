"use client"

import React, { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { apiClient } from "@/lib/apiClient"
import { useAuth } from "@/contexts/AuthContext"

interface CreateFixtureModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onFixtureCreated: () => void
  projectId: string
}

interface FixtureFormData {
  name: string
  type: string
}

export function CreateFixtureModal({ open, onOpenChange, onFixtureCreated, projectId }: CreateFixtureModalProps) {
  const { user } = useAuth()
  const [formData, setFormData] = useState<FixtureFormData>({
    name: "",
    type: "extend"
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>("")

  const handleInputChange = (field: keyof FixtureFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.name.trim()) {
      setError("Fixture name is required")
      return
    }

    setIsLoading(true)
    setError("")

    try {
      console.log("Creating fixture with user ID:", user?.id)
      await apiClient("/fixtures/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: formData.name.trim(),
          project_id: projectId,
          type: formData.type,
          playwright_script: null,
          created_by: user?.id
        })
      })

      // Reset form and close modal
      setFormData({
        name: "",
        type: "extend"
      })
      onOpenChange(false)
      onFixtureCreated()
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to create fixture")
    } finally {
      setIsLoading(false)
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case "extend":
        return "text-blue-600 dark:text-blue-400"
      case "inline":
        return "text-purple-600 dark:text-purple-400"
      default:
        return "text-gray-600 dark:text-gray-400"
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-full max-w-4xl max-h-[90vh] overflow-y-auto" style={{ width: '100%', maxWidth: '896px' }}>
        <DialogHeader className="space-y-4">
          <DialogTitle className="flex items-center gap-3 text-2xl">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/50">
              <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            Create New Fixture
          </DialogTitle>
          <DialogDescription className="text-base">
            Set up a new fixture with automated testing capabilities.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-8 pt-6">
          <div className="space-y-6">
            {/* Fixture Name Field */}
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-medium inline-flex items-center gap-2 text-gray-700 dark:text-gray-300">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
                Fixture Name *
              </Label>
              <div className="relative">
                <textarea
                  id="name"
                  value={formData.name}
                  onChange={(e) => handleInputChange("name", e.target.value)}
                  placeholder="Enter fixture name"
                  disabled={isLoading}
                  required
                  rows={2}
                  className="pl-10 pr-3 py-2 transition-all duration-200 focus:ring-2 focus:ring-blue-500 hover:border-blue-400 border border-input bg-background rounded-md w-full resize-y min-h-[40px] max-h-[120px] text-sm break-words"
                  style={{lineHeight: '1.5'}}
                />
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Type Field */}
            <div className="space-y-2">
              <Label htmlFor="type" className="text-sm font-medium inline-flex items-center gap-2 text-gray-700 dark:text-gray-300">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                Type
              </Label>
              <div className="relative">
                <select
                  id="type"
                  value={formData.type}
                  onChange={(e) => handleInputChange("type", e.target.value)}
                  disabled={isLoading}
                  className={`w-full h-10 pl-10 pr-4 py-2 text-sm border border-input bg-background rounded-md transition-all duration-200 focus:ring-2 focus:ring-blue-500 hover:border-blue-400 appearance-none ${getTypeColor(formData.type)}`}
                >
                  <option value="extend">🔗 Extend</option>
                  <option value="inline">📝 Inline</option>
                </select>
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-3 p-4 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400 rounded-lg border border-red-200 dark:border-red-800 shadow-sm">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="font-medium">{error}</span>
            </div>
          )}

          <DialogFooter className="gap-3 sm:gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                if (!isLoading) {
                  setFormData({
                    name: "",
                    type: "extend"
                  })
                  setError("")
                  onOpenChange(false)
                }
              }}
              disabled={isLoading}
              className="transition-all duration-200 hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={isLoading}
              className="min-w-[100px] transition-all duration-200 bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md"
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Create Fixture
                </div>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
