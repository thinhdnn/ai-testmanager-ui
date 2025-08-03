"use client"

import React, { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { apiClient } from "@/lib/apiClient"
import { useAuth } from "@/contexts/AuthContext"

interface CreateTestCaseModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onTestCaseCreated: () => void
  projectId: string
}

interface TestCaseFormData {
  name: string
  status: string
  isManual: boolean
  tags: string
}

export function CreateTestCaseModal({ open, onOpenChange, onTestCaseCreated, projectId }: CreateTestCaseModalProps) {
  const { user } = useAuth()
  const [formData, setFormData] = useState<TestCaseFormData>({
    name: "",
    status: "pending",
    isManual: false,
    tags: ""
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>("")
  const [globalTags, setGlobalTags] = useState<{ value: string; label?: string }[]>([])
  const [tagInput, setTagInput] = useState("");
  // Always show dropdown, so no need for showTagDropdown state

  useEffect(() => {
    console.log("use efect", open);
    if (open) {
      console.log("About to fetch tags...");
      apiClient("/tags/")
        .then(data => {
          console.log("Fetched tags:", data);
          const tags = Array.isArray(data) ? data.map((t: any) => ({ value: t.value, label: t.label })) : []
          setGlobalTags(tags)
        })
        .catch((err) => {
          setGlobalTags([])
          console.error("Fetch tags error:", err)
        })
    }
  }, [open])

  useEffect(() => {
    const selected = formData.tags.split(",").map(t => t.trim());
    const filtered = globalTags.filter(tag => {
      if (!tagInput) return !selected.includes(tag.value);
      return !selected.includes(tag.value) && (tag.value.toLowerCase().includes(tagInput.toLowerCase()) || (tag.label && tag.label.toLowerCase().includes(tagInput.toLowerCase())));
    });
    console.log("Filtered tags:", filtered);
  }, [tagInput, formData.tags, globalTags]);

  const handleInputChange = (field: keyof TestCaseFormData, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.name.trim()) {
      setError("Test case name is required")
      return
    }

    setIsLoading(true)
    setError("")

    try {
      await apiClient("/test-cases/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: formData.name.trim(),
          project_id: projectId,
          status: formData.status,
          is_manual: formData.isManual,
          tags: formData.tags.trim() || null,
          created_by: user?.id // You can replace this with actual user ID
        })
      })

      // Reset form and close modal
      setFormData({
        name: "",
        status: "pending",
        isManual: false,
        tags: ""
      })
      onOpenChange(false)
      onTestCaseCreated()
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to create test case")
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "passed":
        return "text-green-600 dark:text-green-400"
      case "failed":
        return "text-red-600 dark:text-red-400"
      case "blocked":
        return "text-orange-600 dark:text-orange-400"
      case "not-run":
        return "text-gray-600 dark:text-gray-400"
      default:
        return "text-blue-600 dark:text-blue-400"
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-full max-w-4xl max-h-[90vh] overflow-y-auto" style={{ width: '100%', maxWidth: '896px' }}>
        <DialogHeader className="space-y-4">
          <DialogTitle className="flex items-center gap-3 text-2xl">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/50">
              <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            Create New Test Case
          </DialogTitle>
          <DialogDescription className="text-base">
            Set up a new test case with automated testing capabilities.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-8 pt-6">
          <div className="space-y-6">
            {/* Test Case Name Field */}
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-medium inline-flex items-center gap-2 text-gray-700 dark:text-gray-300">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
                Test Case Name *
              </Label>
              <div className="relative">
                <textarea
                  id="name"
                  value={formData.name}
                  onChange={(e) => handleInputChange("name", e.target.value)}
                  placeholder="Enter test case name"
                  disabled={isLoading}
                  required
                  rows={2}
                  className="pl-10 pr-3 py-2 transition-all duration-200 focus:ring-2 focus:ring-green-500 hover:border-green-400 border border-input bg-background rounded-md w-full resize-y min-h-[40px] max-h-[120px] text-sm break-words"
                  style={{lineHeight: '1.5'}}
                />
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Status Field */}
            <div className="space-y-2">
              <Label htmlFor="status" className="text-sm font-medium inline-flex items-center gap-2 text-gray-700 dark:text-gray-300">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Status
              </Label>
              <div className="relative">
                <select
                  id="status"
                  value={formData.status}
                  onChange={(e) => handleInputChange("status", e.target.value)}
                  disabled={isLoading}
                  className={`w-full h-10 pl-10 pr-4 py-2 text-sm border border-input bg-background rounded-md transition-all duration-200 focus:ring-2 focus:ring-green-500 hover:border-green-400 appearance-none ${getStatusColor(formData.status)}`}
                >
                  <option value="pending">⏳ Pending</option>
                  <option value="passed">✅ Passed</option>
                  <option value="failed">❌ Failed</option>
                  <option value="blocked">🚫 Blocked</option>
                  <option value="not-run">⭕ Not Run</option>
                </select>
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Tags Field */}
            <div className="space-y-2">
              <Label htmlFor="tags" className="text-sm font-medium inline-flex items-center gap-2 text-gray-700 dark:text-gray-300">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                Tags
              </Label>
              <div className="relative">
                <div className="flex flex-wrap gap-2 items-center pl-10">
                  {formData.tags.split(",").filter(Boolean).map((tag, idx) => (
                    <span key={tag+idx} className="bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 px-2 py-0.5 rounded text-xs flex items-center gap-1">
                      {tag.trim()}
                      <button type="button" className="ml-1 text-green-500 hover:text-red-500" onClick={() => {
                        const tags = formData.tags.split(",").map(t => t.trim()).filter(Boolean)
                        tags.splice(idx, 1)
                        handleInputChange("tags", tags.join(", "))
                      }}>&times;</button>
                    </span>
                  ))}
                  <div className="relative min-w-[120px] flex-1">
                    <input
                      type="text"
                      placeholder="Add tag..."
                      className="border-none bg-transparent outline-none text-sm py-1 flex-1 min-w-[80px]"
                      value={tagInput}
                      disabled={isLoading}
                      onChange={e => {
                        setTagInput(e.target.value)
                      }}
                      onKeyDown={e => {
                        if (e.key === "Enter" || e.key === ",") {
                          e.preventDefault()
                          const val = tagInput.trim()
                          if (!val) return
                          const tags = formData.tags.split(",").map(t => t.trim()).filter(Boolean)
                          if (!tags.includes(val)) {
                            handleInputChange("tags", tags.concat(val).join(", "))
                          }
                          setTagInput("")
                        }
                      }}
                    />
                  </div>
                </div>
                {/* Show all global tags as clickable badges below input */}
                <div className="flex flex-wrap gap-2 mt-2 pl-10">
                  {globalTags.filter(tag => {
                    const selected = formData.tags.split(",").map(t => t.trim())
                    return !selected.includes(tag.value)
                  }).map(tag => (
                    <span
                      key={tag.value}
                      className="cursor-pointer bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 px-2 py-1 rounded text-xs border border-gray-300 dark:border-gray-700 hover:bg-green-100 hover:text-green-700 transition-colors duration-150"
                      onClick={() => {
                        const tags = formData.tags.split(",").map(t => t.trim()).filter(Boolean)
                        if (!tags.includes(tag.value)) {
                          handleInputChange("tags", tags.concat(tag.value).join(", "))
                        }
                      }}
                    >
                      {tag.label || tag.value}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Manual Test Case Checkbox */}
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div className="relative flex items-center">
                  <input
                    type="checkbox"
                    id="isManual"
                    checked={formData.isManual}
                    onChange={(e) => handleInputChange("isManual", e.target.checked)}
                    disabled={isLoading}
                    className="h-5 w-5 text-green-600 focus:ring-green-500 focus:ring-offset-0 border-gray-300 rounded transition-all duration-200 hover:border-green-400 cursor-pointer"
                  />
                </div>
                <Label 
                  htmlFor="isManual" 
                  className="text-sm font-medium inline-flex items-center gap-2 text-gray-700 dark:text-gray-300 select-none cursor-pointer"
                >
                  <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                  Manual Test Case
                </Label>
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
                    status: "pending",
                    isManual: false,
                    tags: ""
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
              className="min-w-[100px] transition-all duration-200 bg-green-600 hover:bg-green-700 text-white shadow-sm hover:shadow-md"
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
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Create Test Case
                </div>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
} 