"use client"

import React, { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { apiClient } from "@/lib/apiClient"

interface CreatePageModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onPageCreated?: () => void
  projectId: string
}

export function CreatePageModal({ open, onOpenChange, onPageCreated, projectId }: CreatePageModalProps) {
  const [name, setName] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [nameError, setNameError] = useState("")

  // Validate page name - only letters and spaces allowed
  const validatePageName = (value: string) => {
    if (!value.trim()) {
      return "Page name is required"
    }
    if (!/^[A-Za-z\s]+$/.test(value)) {
      return "Page name can only contain letters and spaces"
    }
    if (value.trim().length < 2) {
      return "Page name must be at least 2 characters long"
    }
    if (value.trim().length > 50) {
      return "Page name must be less than 50 characters"
    }
    return ""
  }

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setName(value)
    
    // Clear error when user starts typing
    if (nameError) {
      setNameError("")
    }
  }

  const canSubmit = name.trim().length > 0 && !nameError

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!projectId || !canSubmit) return
    
    // Final validation before submission
    const error = validatePageName(name)
    if (error) {
      setNameError(error)
      return
    }
    
    setSubmitting(true)
    try {
      await apiClient(`/pages/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: projectId, name: name.trim() }),
      })
      setName("")
      setNameError("")
      onOpenChange(false)
      if (onPageCreated) {
        onPageCreated()
      }
    } catch (err) {
      console.error("Failed to create page", err)
    } finally {
      setSubmitting(false)
    }
  }

  const handleClose = () => {
    setName("")
    setNameError("")
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 mb-4">
            <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <DialogTitle className="text-xl font-semibold text-gray-900">Create New Page</DialogTitle>
          <DialogDescription className="text-gray-600 mt-2">
            Add a new page to organize your test locators and elements
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <Card className="border-0 shadow-none bg-gray-50/50">
            <CardContent className="p-4">
              <div className="space-y-3">
                <Label htmlFor="page-name" className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <svg className="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                  Page Name
                </Label>
                <Input
                  id="page-name"
                  value={name}
                  onChange={handleNameChange}
                  placeholder="e.g., Login Page, Dashboard, User Profile"
                  className={`h-11 text-base transition-colors ${
                    nameError 
                      ? 'border-red-300 focus:border-red-500 focus:ring-red-500' 
                      : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
                  }`}
                  autoFocus
                />
                {nameError ? (
                  <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                    <svg className="h-3 w-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {nameError}
                  </p>
                ) : (
                  <p className="text-xs text-gray-500 mt-1">
                    Only letters and spaces allowed (2-50 characters)
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          <div className="flex flex-col sm:flex-row gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              className="flex-1 h-11 border-gray-300 text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!canSubmit || submitting}
              className="flex-1 h-11 bg-blue-600 hover:bg-blue-700 text-white shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <div className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Creating...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Create Page
                </div>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}


