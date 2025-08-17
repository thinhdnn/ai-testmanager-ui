"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { notFound } from "next/navigation"
import { AppLayout } from "@/components/app-layout"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { apiClient } from "@/lib/apiClient"
import { Zap, Database, CheckCircle, Code, ListOrdered, Ban, PlusCircle, XCircle, ChevronDown, ChevronUp, Edit, Trash2, RotateCcw, GripVertical, MoreHorizontal } from "lucide-react"

interface FixtureDetail {
  id: string
  name: string
  project_id: string
  type: string
  status: string
  version: string
  playwright_script: string
  created_at: string
  updated_at: string
  created_by: string
  updated_by: string
  author_name?: string
}



interface FixtureStats {
  total_executions: number
  total_test_cases_used: number
  success_rate: number
  avg_duration: number
  last_status: string
}

interface Step {
  id: string
  fixture_id: string
  action: string
  data: string
  expected: string
  playwright_script: string
  order: number
  disabled: boolean
  referenced_fixture_id?: string
  referenced_fixture_name?: string
  created_at: string
  updated_at: string
  created_by: string
  updated_by: string
}

export default function FixtureDetailPage() {
  const params = useParams<{ id: string; fixtureId: string }>()
  const router = useRouter()
  const { id: projectId, fixtureId } = params
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [fixture, setFixture] = useState<FixtureDetail | null>(null)
  const [stats, setStats] = useState<FixtureStats | null>(null)
  const [steps, setSteps] = useState<Step[]>([])
  const [versions, setVersions] = useState<any[]>([])
  const [viewVersionOpen, setViewVersionOpen] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<any>(null)
  const [versionSteps, setVersionSteps] = useState<Step[]>([])
  const [addStepOpen, setAddStepOpen] = useState(false)
  const [newStep, setNewStep] = useState({
    action: "",
    data: "",
    expected: "",
    playwright_script: "",
    order: 1,
    disabled: false,
    referenced_fixture_id: ""
  })
  const [availableFixtures, setAvailableFixtures] = useState<any[]>([])
  const [adding, setAdding] = useState(false)
  const [showPlaywrightScript, setShowPlaywrightScript] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [editingStepId, setEditingStepId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("details")
  const [moveStepOpen, setMoveStepOpen] = useState(false)
  const [movingStepId, setMovingStepId] = useState<string | null>(null)
  const [targetPosition, setTargetPosition] = useState<number>(1)
  const [moving, setMoving] = useState(false)
  const [editingFixtureName, setEditingFixtureName] = useState(false)
  const [newFixtureName, setNewFixtureName] = useState("")
  const [savingFixtureName, setSavingFixtureName] = useState(false)
  const [restoringVersion, setRestoringVersion] = useState(false)
  const [updatingStatus, setUpdatingStatus] = useState(false)

  // Filter available fixtures based on step order
  const getFilteredFixtures = () => {
    if (newStep.order === 1) {
      // Only show extend fixtures for step 1
      return availableFixtures.filter(fixture => fixture.type === "extend")
    } else {
      // Only show inline fixtures for step 2+
      return availableFixtures.filter(fixture => fixture.type === "inline")
    }
  }

  const fetchFixtureData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const [fixtureData, statsData, stepsData, versionsData] = await Promise.all([
        apiClient(`/fixtures/${fixtureId}`),
        apiClient(`/test-results/fixtures/${fixtureId}/stats`),
        apiClient(`/fixtures/${fixtureId}/steps`), // Changed to use fixture's own steps
        apiClient(`/fixtures/${fixtureId}/versions`)
      ])
      
      if (!fixtureData) {
        notFound()
        return
      }
      
      setFixture(fixtureData)
      setStats(statsData)
      setSteps(stepsData)
      setVersions(versionsData)
    } catch (err: any) {
      if (err.message?.includes("404")) {
        notFound()
        return
      }
      setError(err.message || "Failed to load fixture data")
    } finally {
      setLoading(false)
    }
  }

  const fetchAvailableFixtures = async () => {
    try {
      const fixturesData = await apiClient(`/fixtures/?project_id=${projectId}`)
      setAvailableFixtures(fixturesData)
    } catch (err: any) {
      console.error("Failed to load available fixtures:", err)
    }
  }

  useEffect(() => {
    if (!fixtureId) return
    fetchFixtureData()
  }, [fixtureId])

  useEffect(() => {
    if (!projectId) return
    fetchAvailableFixtures()
  }, [projectId])

  // Reload specific data when tab changes
  useEffect(() => {
    if (!fixtureId) return
    
    const reloadTabData = async () => {
      try {
        switch (activeTab) {
          case "versions":
            const versionsData = await apiClient(`/fixtures/${fixtureId}/versions`)
            setVersions(versionsData)
            break
          case "steps":
            const stepsData = await apiClient(`/fixtures/${fixtureId}/steps`) // Changed to use fixture's own steps
            setSteps(stepsData)
            break
          case "details":
            // Reload all data for details tab
            const [fixtureData, statsData] = await Promise.all([
              apiClient(`/fixtures/${fixtureId}`),
              apiClient(`/test-results/fixtures/${fixtureId}/stats`)
            ])
            setFixture(fixtureData)
            setStats(statsData)
            break
        }
      } catch (err: any) {
        console.error(`Failed to reload ${activeTab} data:`, err)
      }
    }
    
    reloadTabData()
  }, [activeTab, fixtureId])

  const handleAddStep = async () => {
    setAdding(true)
    try {
      if (editMode && editingStepId) {
        // Update existing step
        await apiClient(`/steps/${editingStepId}`, {
          method: "PUT",
          body: JSON.stringify(newStep),
          headers: { "Content-Type": "application/json" }
        })
        
        // Auto reorder all steps after edit
        await apiClient(`/steps/fixtures/${fixtureId}/steps/auto-reorder`, {
          method: "PATCH"
        })
        
        // Create version for fixture
        await apiClient(`/fixtures/${fixtureId}/versions/create?reason=Updated step: ${newStep.action}`, {
          method: "POST"
        })
      } else {
        const maxOrder = steps.length > 0 ? Math.max(...steps.map(s => s.order)) : 0
        const stepToCreate = { ...newStep, order: maxOrder + 1 }
        await apiClient(`/steps/fixtures/${fixtureId}/steps`, {
          method: "POST",
          body: JSON.stringify(stepToCreate),
          headers: { "Content-Type": "application/json" }
        })
        
        // Create version for fixture
        await apiClient(`/fixtures/${fixtureId}/versions/create?reason=Added new step: ${newStep.action}`, {
          method: "POST"
        })
      }
      setAddStepOpen(false)
      setNewStep({ 
        action: "", 
        data: "", 
        expected: "", 
        playwright_script: "", 
        order: steps.length > 0 ? Math.max(...steps.map(s => s.order)) + 1 : 1, 
        disabled: false 
      })
      setEditMode(false)
      setEditingStepId(null)
      setShowPlaywrightScript(false)
      // Reload steps and fixture data to get updated version
      const [stepsData, fixtureData] = await Promise.all([
        apiClient(`/fixtures/${fixtureId}/steps`), // Changed to use fixture's own steps
        apiClient(`/fixtures/${fixtureId}`)
      ])
      setSteps(stepsData)
      setFixture(fixtureData)
    } catch (err) {
      // TODO: handle error
    } finally {
      setAdding(false)
    }
  }

  const handleEditStep = (step: Step) => {
    setNewStep({
      action: step.action,
      data: step.data,
      expected: step.expected,
      playwright_script: step.playwright_script,
      order: step.order,
      disabled: step.disabled,
      referenced_fixture_id: step.referenced_fixture_id || ""
    })
    setEditMode(true)
    setEditingStepId(step.id)
    setShowPlaywrightScript(!!step.playwright_script)
    setAddStepOpen(true)
  }

  const handleDeleteStep = async (stepId: string) => {
    if (!window.confirm("Are you sure you want to delete this step?")) {
      return
    }
    try {
      // Get step info before delete for version reason
      const stepToDelete = steps.find(s => s.id === stepId)
      const stepAction = stepToDelete?.action || "Unknown step"
      
      await apiClient(`/steps/${stepId}`, { method: "DELETE" })
      
      // Auto reorder after delete
      await apiClient(`/steps/fixtures/${fixtureId}/steps/auto-reorder`, {
        method: "PATCH"
      })
      
      // Create version for fixture
      await apiClient(`/fixtures/${fixtureId}/versions/create?reason=Deleted step: ${stepAction}`, {
        method: "POST"
      })
      
      // Reload steps and fixture data to get updated version
      const [stepsData, fixtureData] = await Promise.all([
        apiClient(`/fixtures/${fixtureId}/steps`), // Changed to use fixture's own steps
        apiClient(`/fixtures/${fixtureId}`)
      ])
      setSteps(stepsData)
      setFixture(fixtureData)
    } catch (err) {
      // TODO: handle error
    }
  }

  const handleOpenMoveStep = (stepId: string) => {
    const step = steps.find(s => s.id === stepId)
    if (step) {
      setMovingStepId(stepId)
      setTargetPosition(step.order)
      setMoveStepOpen(true)
    }
  }

  const handleMoveStep = async () => {
    if (!movingStepId) return
    
    try {
      setMoving(true)
      const currentStep = steps.find(s => s.id === movingStepId)
      if (!currentStep) return

      // Validate target position
      if (targetPosition < 1 || targetPosition > steps.length) {
        alert(`Please enter a position between 1 and ${steps.length}`)
        return
      }

      // Check if already at target position
      if (currentStep.order === targetPosition) {
        setMoveStepOpen(false)
        return
      }

      // Send only step UUID and new order to backend
      await apiClient(`/steps/fixtures/${fixtureId}/steps/reorder`, {
        method: "PATCH",
        body: JSON.stringify({
          step_id: movingStepId,
          new_order: targetPosition
        }),
        headers: { "Content-Type": "application/json" }
      })

      // Create version for fixture
      await apiClient(`/fixtures/${fixtureId}/versions/create?reason=Moved step: ${currentStep.action} to position ${targetPosition}`, {
        method: "POST"
      })

      // Reload steps and fixture data to get updated version
      const [stepsData, fixtureData] = await Promise.all([
        apiClient(`/fixtures/${fixtureId}/steps`), // Changed to use fixture's own steps
        apiClient(`/fixtures/${fixtureId}`)
      ])
      setSteps(stepsData)
      setFixture(fixtureData)
      
      setMoveStepOpen(false)
    } catch (err) {
      console.error('Error moving step:', err)
      alert('Failed to move step. Please try again.')
    } finally {
      setMoving(false)
    }
  }

  const handleViewVersion = async (version: any) => {
    setSelectedVersion(version)
    setViewVersionOpen(true)
    
    try {
      // Get steps for this version
      const stepsData = await apiClient(`/fixtures/${fixtureId}/versions/${version.version}/steps`)
      setVersionSteps(stepsData)
    } catch (err) {
      console.error('Error loading version steps:', err)
      setVersionSteps([])
    }
  }

  const handleRestoreVersion = async (version: any) => {
    if (!window.confirm(`Are you sure you want to restore to version ${version.version}? This will create a backup of the current state and restore the fixture to this version.`)) {
      return
    }
    
    setRestoringVersion(true)
    try {
      // Restore to version
      await apiClient(`/fixtures/${fixtureId}/versions/${version.version}/restore`, {
        method: "POST"
      })
      
      // Reload all data
      await fetchFixtureData()
      
      // Close version detail dialog
      setViewVersionOpen(false)
      
      // Show success message
      alert(`Successfully restored to version ${version.version}!`)
    } catch (err) {
      console.error('Error restoring version:', err)
      alert('Failed to restore version. Please try again.')
    } finally {
      setRestoringVersion(false)
    }
  }

  const handleTabChange = (value: string) => {
    setActiveTab(value)
  }

  const handleEditFixtureName = () => {
    setEditingFixtureName(true)
    setNewFixtureName(fixture?.name || "")
  }

  const handleSaveFixtureName = async () => {
    if (!fixture || !newFixtureName.trim()) return
    
    setSavingFixtureName(true)
    try {
      await apiClient(`/fixtures/${fixtureId}?auto_version=true`, {
        method: "PUT",
        body: JSON.stringify({ name: newFixtureName.trim() }),
        headers: { "Content-Type": "application/json" }
      })
      
      // Reload fixture data
      const fixtureData = await apiClient(`/fixtures/${fixtureId}`)
      setFixture(fixtureData)
      
      setEditingFixtureName(false)
    } catch (err: any) {
      console.error('Error updating fixture name:', err)
    } finally {
      setSavingFixtureName(false)
    }
  }

  const handleCancelEditFixtureName = () => {
    setEditingFixtureName(false)
    setNewFixtureName("")
  }

  const handleUpdateStatus = async (newStatus: string) => {
    if (!fixture || newStatus === fixture.status) return
    
    setUpdatingStatus(true)
    try {
      await apiClient(`/fixtures/${fixtureId}/status?status=${newStatus}`, {
        method: "PATCH"
      })
      
      // Reload fixture data
      const fixtureData = await apiClient(`/fixtures/${fixtureId}`)
      setFixture(fixtureData)
    } catch (err: any) {
      console.error('Error updating fixture status:', err)
    } finally {
      setUpdatingStatus(false)
    }
  }



  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "active":
        return "bg-emerald-500/10 text-emerald-500 border-emerald-200 dark:border-emerald-800"
      case "draft":
        return "bg-gray-500/10 text-gray-500 border-gray-200 dark:border-gray-800"
      default:
        return "bg-blue-500/10 text-blue-500 border-blue-200 dark:border-blue-800"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "active":
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        )
      case "draft":
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      default:
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
    }
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return "Never"
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatDuration = (ms: number) => {
    if (!ms) return "0ms"
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading fixture...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Error Loading Fixture</h3>
            <p className="text-red-600 dark:text-red-400 mt-1">{error}</p>
          </div>
          <Button onClick={() => window.location.reload()} variant="outline">
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  if (!fixture) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 20.5a7.962 7.962 0 01-5.291-2.209m0 0A7.962 7.962 0 014.5 12.5a8.001 8.001 0 1115 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Fixture Not Found</h3>
            <p className="text-gray-600 dark:text-gray-400 mt-1">The requested fixture could not be found.</p>
          </div>
          <Button onClick={() => router.push(`/projects/${projectId}`)} variant="outline">
            Back to Project
          </Button>
        </div>
      </div>
    )
  }

  return (
    <AppLayout title={fixture.name}>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
        <div className="container mx-auto p-6 space-y-6">
          {/* Breadcrumb Navigation */}
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push(`/projects/${projectId}`)}
              className="hover:bg-gray-100 dark:hover:bg-gray-700 px-2 py-1 h-auto"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Project
            </Button>
            <span>/</span>
            <span>Fixtures</span>
            <span>/</span>
            <span className="text-gray-900 dark:text-gray-100 font-medium">{fixture.name}</span>
          </div>

          {/* Enhanced Header */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  {editingFixtureName ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={newFixtureName}
                        onChange={(e) => setNewFixtureName(e.target.value)}
                        className="text-3xl font-bold text-gray-900 dark:text-gray-100 bg-transparent border-b-2 border-blue-500 focus:outline-none focus:border-blue-600"
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleSaveFixtureName()
                          } else if (e.key === 'Escape') {
                            handleCancelEditFixtureName()
                          }
                        }}
                      />
                      <Button
                        size="sm"
                        onClick={handleSaveFixtureName}
                        disabled={savingFixtureName}
                        className="h-8 px-2"
                      >
                        {savingFixtureName ? (
                          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        ) : (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={handleCancelEditFixtureName}
                        disabled={savingFixtureName}
                        className="h-8 px-2"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </Button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{fixture.name}</h1>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={handleEditFixtureName}
                        className="h-8 w-8 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </Button>
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                    </svg>
                    Version {fixture.version}
                  </span>
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    {fixture.author_name || "Unknown"}
                  </span>
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {formatDate(fixture.updated_at || fixture.created_at)}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                                    <Button 
                  variant="outline" 
                  className={`${getStatusColor(fixture.status)} px-3 py-1.5 text-sm font-medium flex items-center gap-2 hover:opacity-80 transition-opacity`}
                  disabled={updatingStatus}
                >
                  {getStatusIcon(fixture.status)}
                  {fixture.status.charAt(0).toUpperCase() + fixture.status.slice(1)}
                  <ChevronDown className="w-4 h-4" />
                </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => handleUpdateStatus('draft')}>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                        Draft
                      </div>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleUpdateStatus('active')}>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        Active
                      </div>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>

              </div>
            </div>
          </div>

          {/* Enhanced Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-white dark:bg-gray-800 border-0 shadow-md hover:shadow-lg transition-all duration-300">
              <CardHeader className="pb-2 pt-3 px-3">
                <CardTitle className="text-xs font-medium text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                  <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900/20 rounded-md flex items-center justify-center">
                    <svg className="w-3 h-3 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  Total Test Cases Used
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0 px-3 pb-3">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats?.total_test_cases_used || 0}</div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Test cases using this fixture</p>
              </CardContent>
            </Card>

            <Card className="bg-white dark:bg-gray-800 border-0 shadow-md hover:shadow-lg transition-all duration-300">
              <CardHeader className="pb-2 pt-3 px-3">
                <CardTitle className="text-xs font-medium text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                  <div className="w-6 h-6 bg-emerald-100 dark:bg-emerald-900/20 rounded-md flex items-center justify-center">
                    <svg className="w-3 h-3 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  Success Rate
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0 px-3 pb-3">
                <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{stats?.success_rate || 0}%</div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Pass percentage</p>
              </CardContent>
            </Card>

            <Card className="bg-white dark:bg-gray-800 border-0 shadow-md hover:shadow-lg transition-all duration-300">
              <CardHeader className="pb-2 pt-3 px-3">
                <CardTitle className="text-xs font-medium text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                  <div className="w-6 h-6 bg-amber-100 dark:bg-amber-900/20 rounded-md flex items-center justify-center">
                    <svg className="w-3 h-3 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  Avg Duration
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0 px-3 pb-3">
                <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">{formatDuration(stats?.avg_duration || 0)}</div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Average runtime</p>
              </CardContent>
            </Card>

            <Card className="bg-white dark:bg-gray-800 border-0 shadow-md hover:shadow-lg transition-all duration-300">
              <CardHeader className="pb-2 pt-3 px-3">
                <CardTitle className="text-xs font-medium text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                  <div className="w-6 h-6 bg-purple-100 dark:bg-purple-900/20 rounded-md flex items-center justify-center">
                    <svg className="w-3 h-3 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  Last Run
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0 px-3 pb-3">
                <div className="text-lg font-bold text-purple-600 dark:text-purple-400">{formatDate(fixture.updated_at)}</div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Last modified</p>
              </CardContent>
            </Card>
          </div>

          {/* Enhanced Tabs */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700">
            <Tabs defaultValue="details" className="w-full" onValueChange={handleTabChange}>
              <TabsList className="w-full flex">
                <TabsTrigger value="details" className="flex-1">Overview</TabsTrigger>
                <TabsTrigger value="steps" className="flex-1">Steps</TabsTrigger>
                <TabsTrigger value="versions" className="flex-1">Versions</TabsTrigger>
              </TabsList>
              
              <div className="p-6">
                <TabsContent value="details" className="space-y-6 mt-0">
                  <div className="grid grid-cols-1 gap-6">
                    <Card className="border-0 shadow-md">
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-lg">
                          <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900/20 rounded-md flex items-center justify-center">
                            <svg className="w-3 h-3 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </div>
                          Fixture Information
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 gap-4">
                          <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                            <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Fixture Type</label>
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mt-1">
                              {fixture.type === "extend" ? "Extend" : "Inline"}
                            </p>
                          </div>
                          <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                            <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Status</label>
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mt-1">{fixture.status}</p>
                          </div>
                          <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                            <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Version</label>
                            <p className="text-sm font-mono text-gray-900 dark:text-gray-100 mt-1 break-all">
                              {fixture.version || "1.0.0"}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>


                  </div>
                </TabsContent>

                <TabsContent value="steps" className="space-y-4 mt-0">
                  <Dialog open={addStepOpen} onOpenChange={setAddStepOpen}>
                    <DialogContent className="min-w-4xl" style={{minWidth: '1200px'}}>
                      <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                          <PlusCircle className="w-6 h-6 text-blue-500" /> {editMode ? "Edit Step" : "Add New Step"}
                        </DialogTitle>
                      </DialogHeader>
                      <form onSubmit={(e: React.FormEvent) => { e.preventDefault(); handleAddStep(); }}>
                        <div className="grid gap-4">
                          <div className="flex items-center gap-3 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800">
                            <Zap className="w-5 h-5 text-yellow-500 flex-shrink-0" />
                            <label className="block text-sm font-semibold mb-0 w-32 flex-shrink-0">Action <span className="text-red-500">*</span></label>
                            <Input className="flex-1" placeholder="Action" value={newStep.action} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewStep(s => ({ ...s, action: e.target.value }))} required />
                          </div>
                          <div className="flex gap-3 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800">
                            <Database className="w-5 h-5 text-indigo-500 flex-shrink-0 mt-1" />
                            <label className="block text-sm font-semibold mb-0 w-32 flex-shrink-0">Data</label>
                            <Textarea 
                              className="flex-1 min-h-[60px] resize-y" 
                              placeholder="Data" 
                              value={newStep.data} 
                              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewStep(s => ({ ...s, data: e.target.value }))} 
                            />
                          </div>
                          <div className="flex gap-3 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800">
                            <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0 mt-1" />
                            <label className="block text-sm font-semibold mb-0 w-32 flex-shrink-0">Expected Result</label>
                            <Textarea 
                              className="flex-1 min-h-[60px] resize-y" 
                              placeholder="Expected Result" 
                              value={newStep.expected} 
                              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewStep(s => ({ ...s, expected: e.target.value }))} 
                            />
                          </div>
                          <div className="flex gap-3 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800">
                            <Code className="w-5 h-5 text-purple-500 flex-shrink-0 mt-1" />
                            <label className="block text-sm font-semibold mb-0 w-32 flex-shrink-0">Playwright Script</label>
                            <div className="flex-1">
                              <Button 
                                type="button" 
                                variant="ghost" 
                                size="sm" 
                                onClick={() => setShowPlaywrightScript(!showPlaywrightScript)}
                                className="mb-2 p-1 h-auto text-xs"
                              >
                                {showPlaywrightScript ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                              </Button>
                              {showPlaywrightScript && (
                                <Textarea 
                                  className="w-full min-h-[80px] resize-y" 
                                  placeholder="Playwright Script" 
                                  value={newStep.playwright_script} 
                                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewStep(s => ({ ...s, playwright_script: e.target.value }))} 
                                />
                              )}
                            </div>
                          </div>
                          <div className="flex gap-4 items-center">
                            <div className="flex items-center gap-3 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800 w-1/2">
                              <ListOrdered className="w-5 h-5 text-blue-400 flex-shrink-0" />
                              <label className="block text-sm font-semibold mb-0 w-16 flex-shrink-0">
                                Order {!editMode && "(Auto)"}
                              </label>
                              <Input 
                                className="flex-1" 
                                type="number" 
                                placeholder="Order" 
                                value={newStep.order} 
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewStep(s => ({ ...s, order: Number(e.target.value) }))} 
                                min={1} 
                                max={steps.length}
                                disabled={!editMode}
                              />
                            </div>
                            <div className="flex items-center gap-3 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800 h-full">
                              <Ban className="w-5 h-5 text-red-400 flex-shrink-0" />
                              <input type="checkbox" id="step-disabled" checked={newStep.disabled} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewStep(s => ({ ...s, disabled: e.target.checked }))} className="mr-2" />
                              <label htmlFor="step-disabled" className="text-sm font-semibold mb-0">Disabled</label>
                            </div>
                          </div>
                        </div>
                        <DialogFooter className="pt-6">
                          <Button type="button" variant="secondary" onClick={() => setAddStepOpen(false)}>
                            <XCircle className="w-4 h-4 mr-2" /> Cancel
                          </Button>
                          <Button type="submit" disabled={adding}>
                            <PlusCircle className="w-4 h-4 mr-2" />{adding ? (editMode ? "Updating..." : "Adding...") : (editMode ? "Update Step" : "Add Step")}
                          </Button>
                        </DialogFooter>
                      </form>
                    </DialogContent>
                  </Dialog>
                  <Card className="border-0 shadow-md">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-lg w-full justify-between">
                        <span className="flex items-center gap-2">
                          <div className="w-6 h-6 bg-indigo-100 dark:bg-indigo-900/20 rounded-md flex items-center justify-center">
                            <svg className="w-3 h-3 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                          Test Steps
                        </span>
                        <div className="flex items-center gap-2 ml-auto">
                          <Button size="icon" variant="outline" onClick={async () => {
                            try {
                              await apiClient(`/steps/fixtures/${fixtureId}/steps/auto-reorder`, {
                                method: "PATCH"
                              })
                              // Reload steps
                              const stepsData = await apiClient(`/fixtures/${fixtureId}/steps`) // Changed to use fixture's own steps
                              setSteps(stepsData)
                            } catch (err) {
                              console.error('Error reordering steps:', err)
                            }
                          }} title="Auto Reorder Steps">
                            <ListOrdered className="w-4 h-4" />
                          </Button>
                          <Button size="icon" variant="secondary" onClick={() => {
                            const nextOrder = steps.length > 0 ? Math.max(...steps.map(s => s.order)) + 1 : 1
                            setNewStep(prev => ({ ...prev, order: nextOrder }))
                            setAddStepOpen(true)
                          }} title="Add Step">
                            <PlusCircle className="w-5 h-5" />
                          </Button>
                        </div>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {steps.length > 0 ? (
                          steps.map((step, index) => (
                            <div key={step.id} className="group p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-all duration-200 hover:border-blue-300 dark:hover:border-blue-600">
                              <div className="flex items-start gap-4">
                                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center">
                                  <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">{step.order}</span>
                                </div>
                                <div className="flex-shrink-0 flex items-center opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing" title="Drag to reorder">
                                  <GripVertical className="w-4 h-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" />
                                </div>
                                <div className="flex-1 space-y-2">
                                  <div className="flex items-center justify-between">
                                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                      {step.referenced_fixture_id ? (
                                        <Badge 
                                          variant="outline" 
                                          className="text-xs text-orange-600 border-orange-300 flex items-center gap-1 cursor-pointer hover:bg-orange-50 dark:hover:bg-orange-900/20 transition-colors"
                                          onClick={() => router.push(`/projects/${projectId}/fixtures/${step.referenced_fixture_id}`)}
                                          title={`Click to view ${step.referenced_fixture_name || 'fixture'}`}
                                        >
                                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                          </svg>
                                          {step.referenced_fixture_name || "Fixture"}
                                        </Badge>
                                      ) : (
                                        step.action.charAt(0).toUpperCase() + step.action.slice(1)
                                      )}
                                    </h4>
                                    <div className="flex items-center gap-2">
                                      {step.disabled && (
                                        <Badge variant="outline" className="text-xs text-red-600 border-red-300">Disabled</Badge>
                                      )}
                                      <Button 
                                        size="icon" 
                                        variant="ghost" 
                                        onClick={() => handleOpenMoveStep(step.id)}
                                        className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                                        title="Move Step"
                                      >
                                        <MoreHorizontal className="w-3 h-3" />
                                      </Button>
                                      <Button 
                                        size="icon" 
                                        variant="ghost" 
                                        onClick={() => handleEditStep(step)}
                                        className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                                        title="Edit Step"
                                      >
                                        <Edit className="w-4 h-4" />
                                      </Button>
                                      <Button 
                                        size="icon" 
                                        variant="ghost" 
                                        onClick={() => handleDeleteStep(step.id)}
                                        className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity text-red-500 hover:text-red-700"
                                        title="Delete Step"
                                      >
                                        <Trash2 className="w-4 h-4" />
                                      </Button>
                                    </div>
                                  </div>
                                  
                                  {(step.data || step.expected) && (
                                    <div className={`grid gap-3 ${
                                      step.data && step.expected 
                                        ? 'grid-cols-1 md:grid-cols-2' 
                                        : 'grid-cols-1'
                                    }`}>
                                      {step.data && (
                                        <div className="p-2 bg-gray-50 dark:bg-gray-700 rounded-md">
                                          <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Data</label>
                                          <p className="text-sm text-gray-900 dark:text-gray-100 mt-1">{step.data}</p>
                                        </div>
                                      )}
                                      
                                      {step.expected && (
                                        <div className="p-2 bg-emerald-50 dark:bg-emerald-900/20 rounded-md">
                                          <label className="text-xs font-medium text-emerald-600 dark:text-emerald-400 uppercase tracking-wide">Expected Result</label>
                                          <p className="text-sm text-gray-900 dark:text-gray-100 mt-1">{step.expected}</p>
                                        </div>
                                      )}
                                    </div>
                                  )}
                                  

                                </div>
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="text-center py-12">
                            <div className="w-16 h-16 mx-auto bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                            </div>
                            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">No Test Steps</h3>
                            <p className="text-gray-500 dark:text-gray-400">This test case has no defined steps.</p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="versions" className="space-y-4 mt-0">
                  <Card className="border-0 shadow-md">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <div className="w-6 h-6 bg-green-100 dark:bg-green-900/20 rounded-md flex items-center justify-center">
                          <svg className="w-3 h-3 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        Version History
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {versions.length > 0 ? (
                          versions.map((version, index) => (
                            <div key={version.id} className="group p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-all duration-200 hover:border-green-300 dark:hover:border-green-600">
                              <div className="flex items-start gap-4">
                                <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center">
                                  <span className="text-sm font-semibold text-green-600 dark:text-green-400">v{version.version}</span>
                                </div>
                                <div className="flex-1 space-y-2">
                                  <div className="flex items-center justify-between">
                                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                      {version.name}
                                    </h4>
                                    <div className="flex items-center gap-2">
                                      <Button 
                                        size="sm" 
                                        variant="outline" 
                                        onClick={() => handleViewVersion(version)}
                                        className="text-xs"
                                      >
                                        View Detail
                                      </Button>

                                      <span className="text-xs text-gray-500 dark:text-gray-400">
                                        {new Date(version.created_at).toLocaleDateString()}
                                      </span>
                                    </div>
                                  </div>
                                  
                                  <div className="text-sm text-gray-600 dark:text-gray-400">
                                    {version.description && (
                                      <p><strong>Description:</strong> {version.description}</p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="text-center py-12">
                            <div className="w-16 h-16 mx-auto bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                            </div>
                            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">No Versions</h3>
                            <p className="text-gray-500 dark:text-gray-400">This test case has no version history.</p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>


              </div>
            </Tabs>
          </div>
        </div>
      </div>
      
      {/* Move Step Dialog */}
      <Dialog open={moveStepOpen} onOpenChange={setMoveStepOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
              </svg>
              Move Step
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Enter the target position for this step (1 - {steps.length}):
            </div>
            <div className="space-y-2">
              <label htmlFor="target-position" className="text-sm font-medium">
                Target Position
              </label>
              <Input
                id="target-position"
                type="number"
                min={1}
                max={steps.length}
                value={targetPosition}
                onChange={(e) => setTargetPosition(Number(e.target.value))}
                placeholder={`1 - ${steps.length}`}
                className="w-full"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setMoveStepOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleMoveStep}
              disabled={moving || targetPosition < 1 || targetPosition > steps.length}
            >
              {moving ? (
                <>
                  <svg className="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Moving...
                </>
              ) : (
                'Move Step'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Version Detail Modal */}
      <Dialog open={viewVersionOpen} onOpenChange={setViewVersionOpen}>
        <DialogContent className="max-w-[95vw] max-h-[95vh] w-[1200px] h-[800px] flex flex-col">
          <DialogHeader className="flex-shrink-0">
            <DialogTitle className="flex items-center gap-2">
              <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Version {selectedVersion?.version} - {selectedVersion?.name}
            </DialogTitle>
          </DialogHeader>
          
          <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
            {/* Version Info */}
            <div className="grid grid-cols-2 gap-4 p-4 border rounded-lg bg-gray-50 dark:bg-gray-800 flex-shrink-0 mb-6">
              <div>
                <label className="text-sm font-semibold text-gray-600 dark:text-gray-400">Version</label>
                <p className="text-lg font-medium">{selectedVersion?.version}</p>
              </div>
              <div>
                <label className="text-sm font-semibold text-gray-600 dark:text-gray-400">Created</label>
                <p className="text-sm">{selectedVersion?.created_at ? new Date(selectedVersion.created_at).toLocaleString() : ''}</p>
              </div>
              {selectedVersion?.description && (
                <div className="col-span-2">
                  <label className="text-sm font-semibold text-gray-600 dark:text-gray-400">Description</label>
                  <p className="text-sm">{selectedVersion.description}</p>
                </div>
              )}
            </div>
            
            {/* Version Steps with Scroll */}
            <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
              <h3 className="text-lg font-semibold mb-4 flex-shrink-0">Steps in this Version</h3>
              <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                {versionSteps.length > 0 ? (
                  versionSteps.map((step, index) => (
                    <div key={step.id} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <div className="flex items-start gap-4">
                        <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center">
                          <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">{step.order}</span>
                        </div>
                        <div className="flex-1 space-y-2">
                          <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {step.action.charAt(0).toUpperCase() + step.action.slice(1)}
                          </h4>
                          
                          {step.data && (
                            <div className="p-2 bg-gray-50 dark:bg-gray-700 rounded-md">
                              <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Data</label>
                              <p className="text-sm text-gray-900 dark:text-gray-100 mt-1">{step.data}</p>
                            </div>
                          )}
                          
                          {step.expected && (
                            <div className="p-2 bg-emerald-50 dark:bg-emerald-900/20 rounded-md">
                              <label className="text-xs font-medium text-emerald-600 dark:text-emerald-400 uppercase tracking-wide">Expected Result</label>
                              <p className="text-sm text-gray-900 dark:text-gray-100 mt-1">{step.expected}</p>
                            </div>
                          )}
                          

                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    No steps found in this version
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <DialogFooter className="flex-shrink-0 mt-6">
            <Button 
              variant="outline" 
              onClick={() => handleRestoreVersion(selectedVersion)}
              disabled={restoringVersion}
              className="text-orange-600 hover:text-orange-700 border-orange-200 hover:border-orange-300"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              {restoringVersion ? "Restoring..." : "Restore to this Version"}
            </Button>
            <Button variant="secondary" onClick={() => setViewVersionOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppLayout>
  )
} 