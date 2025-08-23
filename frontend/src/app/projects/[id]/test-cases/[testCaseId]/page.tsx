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
import { Zap, Database, CheckCircle, Code, ListOrdered, Ban, PlusCircle, XCircle, ChevronDown, ChevronUp, Edit, Trash2, RotateCcw, GripVertical, MoreHorizontal, Settings, Play } from "lucide-react"

interface TestCaseDetail {
  id: string
  name: string
  project_id: string
  order: number
  status: string
  version: string
  is_manual: boolean
  tags: string | string[]
  test_file_path: string
  playwright_script: string
  created_at: string
  updated_at: string
  last_run: string
  created_by: string
  updated_by: string
  last_run_by: string
}

interface TestCaseExecution {
  id: string
  status: string
  duration: number
  error_message: string
  output: string
  start_time: string
  end_time: string
  retries: number
  created_at: string
}

interface TestCaseStats {
  total_executions: number
  success_rate: number
  avg_duration: number
  last_status: string
}

interface Step {
  id: string
  test_case_id: string
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

interface TestCaseFixture {
  fixture_id: string
  order: number
  created_at: string
  created_by: string
  name: string
  type: string
  playwright_script: string
}

interface AvailableFixture {
  id: string
  name: string
  type: string
  playwright_script: string
  created_at: string
}

export default function TestCaseDetailPage() {
  const params = useParams<{ id: string; testCaseId: string }>()
  const router = useRouter()
  const { id: projectId, testCaseId } = params
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [testCase, setTestCase] = useState<TestCaseDetail | null>(null)
  const [executions, setExecutions] = useState<TestCaseExecution[]>([])
  const [stats, setStats] = useState<TestCaseStats | null>(null)
  const [steps, setSteps] = useState<Step[]>([])
  const [fixtures, setFixtures] = useState<TestCaseFixture[]>([])
  const [availableFixtures, setAvailableFixtures] = useState<AvailableFixture[]>([])
  const [versions, setVersions] = useState<any[]>([])
  const [viewVersionOpen, setViewVersionOpen] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<any>(null)
  const [versionSteps, setVersionSteps] = useState<Step[]>([])
  const [addStepOpen, setAddStepOpen] = useState(false)
  const [addFixtureOpen, setAddFixtureOpen] = useState(false)
  const [selectedFixtureId, setSelectedFixtureId] = useState<string>("")
  const [newStep, setNewStep] = useState({
    action: "",
    data: "",
    expected: "",
    playwright_script: "",
    order: 1,
    disabled: false,
    referenced_fixture_id: ""
  })
  const [adding, setAdding] = useState(false)
  const [addingFixture, setAddingFixture] = useState(false)
  const [showPlaywrightScript, setShowPlaywrightScript] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [editingStepId, setEditingStepId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("details")
  const [moveStepOpen, setMoveStepOpen] = useState(false)
  const [movingStepId, setMovingStepId] = useState<string | null>(null)
  const [targetPosition, setTargetPosition] = useState<number>(1)
  const [moving, setMoving] = useState(false)
  const [editingTestName, setEditingTestName] = useState(false)
  const [newTestName, setNewTestName] = useState("")
  const [savingTestName, setSavingTestName] = useState(false)
  const [restoringVersion, setRestoringVersion] = useState(false)
  const [updatingStatus, setUpdatingStatus] = useState(false)
  const [runningTest, setRunningTest] = useState(false)
  const [runSettingsOpen, setRunSettingsOpen] = useState(false)
  const [testResultOpen, setTestResultOpen] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [schedulingMessage, setSchedulingMessage] = useState("")
  const [activeResultTab, setActiveResultTab] = useState<'executions' | 'logs'>('executions')
  const [runSettings, setRunSettings] = useState({
    timeout: 30, // Default 30 seconds (for display only)
    expect_timeout: 10, // Default 10 seconds (for display only)
    headless: true,
    screenshot: 'off' as 'off' | 'on' | 'only-on-failure',
    video: 'off' as 'off' | 'on' | 'retain-on-failure' | 'on-first-retry',
    executionMode: 'wait' as 'wait' | 'background', // Default to wait for result
    browser: 'chromium' as 'chromium' | 'firefox' | 'webkit' // Default to chromium
  })

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

  const fetchTestCaseData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const [testCaseData, executionsData, statsData, stepsData, fixturesData, versionsData, projectSettings] = await Promise.all([
        apiClient(`/test-cases/${testCaseId}`),
        apiClient(`/test-results/test-cases/${testCaseId}/executions?limit=20`),
        apiClient(`/test-results/test-cases/${testCaseId}/stats`),
        apiClient(`/steps/test-cases/${testCaseId}/steps`),
        apiClient(`/test-cases/${testCaseId}/fixtures`),
        apiClient(`/test-cases/${testCaseId}/versions`),
        apiClient(`/projects/${projectId}/settings/dict`)
      ])
      
      if (!testCaseData) {
        notFound()
        return
      }
      
      setTestCase(testCaseData)
      setExecutions(executionsData)
      setStats(statsData)
      setSteps(stepsData)
      setFixtures(fixturesData)
      setVersions(versionsData)
      
      // Load project settings for run settings (convert milliseconds to seconds for display)
      if (projectSettings) {
        if (projectSettings.TIMEOUT) {
          setRunSettings(prev => ({ ...prev, timeout: Math.round(parseInt(projectSettings.TIMEOUT) / 1000) }))
        }
        if (projectSettings.EXPECT_TIMEOUT) {
          setRunSettings(prev => ({ ...prev, expect_timeout: Math.round(parseInt(projectSettings.EXPECT_TIMEOUT) / 1000) }))
        }
        if (projectSettings.HEADLESS_MODE) {
          setRunSettings(prev => ({ ...prev, headless: projectSettings.HEADLESS_MODE === 'true' }))
        }
        if (projectSettings.SCREENSHOT) {
          setRunSettings(prev => ({ ...prev, screenshot: projectSettings.SCREENSHOT as any }))
        }
        if (projectSettings.VIDEO) {
          setRunSettings(prev => ({ ...prev, video: projectSettings.VIDEO as any }))
        }
        if (projectSettings.BROWSER) {
          setRunSettings(prev => ({ ...prev, browser: projectSettings.BROWSER as 'chromium' | 'firefox' | 'webkit' }))
        }
      }
    } catch (err: any) {
      if (err.message?.includes("404")) {
        notFound()
        return
      }
      setError(err.message || "Failed to load test case data")
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
    if (!testCaseId) return
    fetchTestCaseData()
  }, [testCaseId])

  useEffect(() => {
    if (!projectId) return
    fetchAvailableFixtures()
  }, [projectId])

  // Reload specific data when tab changes
  useEffect(() => {
    if (!testCaseId) return
    
    const reloadTabData = async () => {
      try {
        switch (activeTab) {
          case "executions":
            const executionsData = await apiClient(`/test-results/test-cases/${testCaseId}/executions?limit=20`)
            setExecutions(executionsData)
            break
          case "versions":
            const versionsData = await apiClient(`/test-cases/${testCaseId}/versions`)
            setVersions(versionsData)
            break
          case "steps":
            const stepsData = await apiClient(`/steps/test-cases/${testCaseId}/steps`)
            setSteps(stepsData)
            break
          case "fixtures":
            const fixturesData = await apiClient(`/test-cases/${testCaseId}/fixtures`)
            setFixtures(fixturesData)
            break
          case "details":
            // Reload all data for details tab
            const [testCaseData, statsData] = await Promise.all([
              apiClient(`/test-cases/${testCaseId}`),
              apiClient(`/test-results/test-cases/${testCaseId}/stats`)
            ])
            setTestCase(testCaseData)
            setStats(statsData)
            break
        }
      } catch (err: any) {
        console.error(`Failed to reload ${activeTab} data:`, err)
      }
    }
    
    reloadTabData()
  }, [activeTab, testCaseId])

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
        await apiClient(`/steps/test-cases/${testCaseId}/steps/auto-reorder`, {
          method: "PATCH"
        })
        
        // Create version for test case
        await apiClient(`/test-cases/${testCaseId}/versions/create?reason=Updated step: ${newStep.action}`, {
          method: "POST"
        })
      } else {
        const maxOrder = steps.length > 0 ? Math.max(...steps.map(s => s.order)) : 0
        const stepToCreate = { ...newStep, order: maxOrder + 1 }
        await apiClient(`/steps/test-cases/${testCaseId}/steps`, {
          method: "POST",
          body: JSON.stringify(stepToCreate),
          headers: { "Content-Type": "application/json" }
        })
        
        // Create version for test case
        await apiClient(`/test-cases/${testCaseId}/versions/create?reason=Added new step: ${newStep.action}`, {
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
        disabled: false,
        referenced_fixture_id: ""
      })
      setEditMode(false)
      setEditingStepId(null)
      setShowPlaywrightScript(false)
      // Reload steps and test case data to get updated version
      const [stepsData, testCaseData] = await Promise.all([
        apiClient(`/steps/test-cases/${testCaseId}/steps`),
        apiClient(`/test-cases/${testCaseId}`)
      ])
      setSteps(stepsData)
      setTestCase(testCaseData)
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
      await apiClient(`/steps/test-cases/${testCaseId}/steps/auto-reorder`, {
        method: "PATCH"
      })
      
      // Create version for test case
      await apiClient(`/test-cases/${testCaseId}/versions/create?reason=Deleted step: ${stepAction}`, {
        method: "POST"
      })
      
      // Reload steps and test case data to get updated version
      const [stepsData, testCaseData] = await Promise.all([
        apiClient(`/steps/test-cases/${testCaseId}/steps`),
        apiClient(`/test-cases/${testCaseId}`)
      ])
      setSteps(stepsData)
      setTestCase(testCaseData)
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
      await apiClient(`/steps/test-cases/${testCaseId}/steps/reorder`, {
        method: "PATCH",
        body: JSON.stringify({
          step_id: movingStepId,
          new_order: targetPosition
        }),
        headers: { "Content-Type": "application/json" }
      })

      // Create version for test case
      await apiClient(`/test-cases/${testCaseId}/versions/create?reason=Moved step: ${currentStep.action} to position ${targetPosition}`, {
        method: "POST"
      })

      // Reload steps and test case data to get updated version
      const [stepsData, testCaseData] = await Promise.all([
        apiClient(`/steps/test-cases/${testCaseId}/steps`),
        apiClient(`/test-cases/${testCaseId}`)
      ])
      setSteps(stepsData)
      setTestCase(testCaseData)
      
      setMoveStepOpen(false)
    } catch (err) {
      console.error('Error moving step:', err)
      alert('Failed to move step. Please try again.')
    } finally {
      setMoving(false)
    }
  }

  // Fixture management functions
  const handleAddFixture = async () => {
    if (!selectedFixtureId) {
      alert("Please select a fixture to add")
      return
    }

    setAddingFixture(true)
    try {
      await apiClient(`/test-cases/${testCaseId}/fixtures`, {
        method: "POST",
        body: JSON.stringify({
          fixture_id: selectedFixtureId
        }),
        headers: { "Content-Type": "application/json" }
      })

      // Create version for test case
      await apiClient(`/test-cases/${testCaseId}/versions/create?reason=Added fixture: ${availableFixtures.find(f => f.id === selectedFixtureId)?.name}`, {
        method: "POST"
      })

      // Reload fixtures and test case data
      const [fixturesData, testCaseData] = await Promise.all([
        apiClient(`/test-cases/${testCaseId}/fixtures`),
        apiClient(`/test-cases/${testCaseId}`)
      ])
      setFixtures(fixturesData)
      setTestCase(testCaseData)
      
      setAddFixtureOpen(false)
      setSelectedFixtureId("")
    } catch (err: any) {
      console.error('Error adding fixture:', err)
      alert(err.message || 'Failed to add fixture. Please try again.')
    } finally {
      setAddingFixture(false)
    }
  }

  const handleRemoveFixture = async (fixtureId: string) => {
    if (!window.confirm("Are you sure you want to remove this fixture from the test case?")) {
      return
    }

    try {
      const fixtureToRemove = fixtures.find(f => f.fixture_id === fixtureId)
      const fixtureName = fixtureToRemove?.name || "Unknown fixture"
      
      await apiClient(`/test-cases/${testCaseId}/fixtures/${fixtureId}`, {
        method: "DELETE"
      })

      // Create version for test case
      await apiClient(`/test-cases/${testCaseId}/versions/create?reason=Removed fixture: ${fixtureName}`, {
        method: "POST"
      })

      // Reload fixtures and test case data
      const [fixturesData, testCaseData] = await Promise.all([
        apiClient(`/test-cases/${testCaseId}/fixtures`),
        apiClient(`/test-cases/${testCaseId}`)
      ])
      setFixtures(fixturesData)
      setTestCase(testCaseData)
    } catch (err: any) {
      console.error('Error removing fixture:', err)
      alert('Failed to remove fixture. Please try again.')
    }
  }

  const handleViewVersion = async (version: any) => {
    setSelectedVersion(version)
    setViewVersionOpen(true)
    
    try {
      // Get steps for this version
      const stepsData = await apiClient(`/test-cases/${testCaseId}/versions/${version.version}/steps`)
      setVersionSteps(stepsData)
    } catch (err) {
      console.error('Error loading version steps:', err)
      setVersionSteps([])
    }
  }

  const handleRestoreVersion = async (version: any) => {
    if (!window.confirm(`Are you sure you want to restore to version ${version.version}? This will create a backup of the current state and restore the test case to this version.`)) {
      return
    }
    
    setRestoringVersion(true)
    try {
      // Restore to version
      await apiClient(`/test-cases/${testCaseId}/versions/${version.version}/restore`, {
        method: "POST"
      })
      
      // Reload all data
      await fetchTestCaseData()
      
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

  const handleEditTestName = () => {
    setEditingTestName(true)
    setNewTestName(testCase?.name || "")
  }

  const handleSaveTestName = async () => {
    if (!testCase || !newTestName.trim()) return
    
    setSavingTestName(true)
    try {
      await apiClient(`/test-cases/${testCaseId}?auto_version=true`, {
        method: "PUT",
        body: JSON.stringify({ name: newTestName.trim() }),
        headers: { "Content-Type": "application/json" }
      })
      
      // Reload test case data
      const testCaseData = await apiClient(`/test-cases/${testCaseId}`)
      setTestCase(testCaseData)
      
      setEditingTestName(false)
    } catch (err: any) {
      console.error('Error updating test name:', err)
    } finally {
      setSavingTestName(false)
    }
  }

  const handleCancelEditTestName = () => {
    setEditingTestName(false)
    setNewTestName("")
  }

  const handleUpdateStatus = async (newStatus: string) => {
    if (!testCase || newStatus === testCase.status) return
    
    setUpdatingStatus(true)
    try {
      await apiClient(`/test-cases/${testCaseId}/status?status=${newStatus}`, {
        method: "PATCH"
      })
      
      // Reload test case data
      const testCaseData = await apiClient(`/test-cases/${testCaseId}`)
      setTestCase(testCaseData)
    } catch (err: any) {
      console.error('Error updating test case status:', err)
    } finally {
      setUpdatingStatus(false)
    }
  }

  const handleToggleTestType = async () => {
    if (!testCase) return
    
    setUpdatingStatus(true)
    try {
      const newIsManual = !testCase.is_manual
      await apiClient(`/test-cases/${testCaseId}?auto_version=true`, {
        method: "PUT",
        body: JSON.stringify({ is_manual: newIsManual }),
        headers: { "Content-Type": "application/json" }
      })
      
      // Reload test case data
      const testCaseData = await apiClient(`/test-cases/${testCaseId}`)
      setTestCase(testCaseData)
    } catch (err: any) {
      console.error('Error updating test case type:', err)
    } finally {
      setUpdatingStatus(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "passed":
        return "bg-emerald-500/10 text-emerald-500 border-emerald-200 dark:border-emerald-800"
      case "failed":
        return "bg-red-500/10 text-red-500 border-red-200 dark:border-red-800"
      case "pending":
        return "bg-amber-500/10 text-amber-500 border-amber-200 dark:border-amber-800"
      case "blocked":
        return "bg-gray-500/10 text-gray-500 border-gray-200 dark:border-gray-800"
      default:
        return "bg-blue-500/10 text-blue-500 border-blue-200 dark:border-blue-800"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "passed":
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        )
      case "failed":
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )
      case "pending":
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case "blocked":
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636" />
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

  const handleRunTest = async () => {
    if (!testCase || testCase.is_manual) {
      alert("Cannot run manual tests automatically")
      return
    }

    if (!testCase.test_file_path) {
      alert("No test file path specified for this test case")
      return
    }

    if (runSettings.executionMode === 'background') {
      // Background run - show scheduling message and close form
      setSchedulingMessage("Scheduling test execution...")
      setTimeout(() => {
        setSchedulingMessage("")
        setRunSettingsOpen(false)
      }, 2000)
      return
    }

    // Wait for result mode
    setRunningTest(true)
    try {
      // Call the backend API to run the test locally
      const response = await apiClient(`/test-cases/${testCaseId}/run`, {
        method: "POST",
        body: JSON.stringify({
          project_id: projectId,
          test_file_path: testCase.test_file_path,
          settings: {
            timeout: runSettings.timeout * 1000, // Convert seconds to milliseconds for backend
            expect_timeout: runSettings.expect_timeout * 1000, // Convert seconds to milliseconds for backend
            headless: runSettings.headless,
            screenshot: runSettings.screenshot,
            video: runSettings.video,
            browser: runSettings.browser // Add browser selection
          }
        }),
        headers: { "Content-Type": "application/json" }
      })

      if (response.success) {
        // Store test result and show result form
        setTestResult(response)
        setRunSettingsOpen(false)
        setTestResultOpen(true)
        // Refresh executions data
        const executionsData = await apiClient(`/test-results/test-cases/${testCaseId}/executions?limit=20`)
        setExecutions(executionsData)
        // Refresh stats
        const statsData = await apiClient(`/test-results/test-cases/${testCaseId}/stats`)
        setStats(statsData)
      } else {
        alert(`Test execution failed: ${response.error || 'Unknown error'}`)
      }
    } catch (err: any) {
      console.error('Error running test:', err)
      alert(`Failed to run test: ${err.message || 'Unknown error'}`)
    } finally {
      setRunningTest(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading test case...</p>
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
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Error Loading Test Case</h3>
            <p className="text-red-600 dark:text-red-400 mt-1">{error}</p>
          </div>
          <Button onClick={() => window.location.reload()} variant="outline">
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  if (!testCase) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 mx-auto bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 20.5a7.962 7.962 0 01-5.291-2.209m0 0A7.962 7.962 0 014.5 12.5a8.001 8.001 0 1115 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Test Case Not Found</h3>
            <p className="text-gray-600 dark:text-gray-400 mt-1">The requested test case could not be found.</p>
          </div>
          <Button onClick={() => router.push(`/projects/${projectId}`)} variant="outline">
            Back to Project
          </Button>
        </div>
      </div>
    )
  }

  return (
    <AppLayout title={testCase.name}>
      <div>
        <div className="space-y-6">
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
            <span>Test Cases</span>
            <span>/</span>
            <span className="text-gray-900 dark:text-gray-100 font-medium">{testCase.name}</span>
          </div>

          {/* Enhanced Header */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  {editingTestName ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={newTestName}
                        onChange={(e) => setNewTestName(e.target.value)}
                        className="text-3xl font-bold text-gray-900 dark:text-gray-100 bg-transparent border-b-2 border-blue-500 focus:outline-none focus:border-blue-600"
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleSaveTestName()
                          } else if (e.key === 'Escape') {
                            handleCancelEditTestName()
                          }
                        }}
                      />
                      <Button
                        size="sm"
                        onClick={handleSaveTestName}
                        disabled={savingTestName}
                        className="h-8 px-2"
                      >
                        {savingTestName ? (
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
                        onClick={handleCancelEditTestName}
                        disabled={savingTestName}
                        className="h-8 px-2"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </Button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{testCase.name}</h1>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={handleEditTestName}
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
                    Version {testCase.version}
                  </span>
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    {testCase.created_by || "Unknown"}
                  </span>
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {formatDate(testCase.updated_at || testCase.created_at)}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Button 
                  onClick={() => setRunSettingsOpen(true)}
                  disabled={runningTest || testCase.is_manual || !testCase.test_file_path}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 flex items-center gap-2"
                  title={testCase.is_manual ? "Cannot run manual tests" : !testCase.test_file_path ? "No test file path specified" : "Run this test locally"}
                >
                  {runningTest ? (
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  {runningTest ? "Running..." : "Run Test"}
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button 
                      variant="outline" 
                      className={`${getStatusColor(testCase.status)} px-3 py-1.5 text-sm font-medium flex items-center gap-2 hover:opacity-80 transition-opacity`}
                      disabled={updatingStatus}
                    >
                      {getStatusIcon(testCase.status)}
                      {testCase.status.charAt(0).toUpperCase() + testCase.status.slice(1)}
                      <ChevronDown className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => handleUpdateStatus('pending')}>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                        Pending
                      </div>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleUpdateStatus('passed')}>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        Passed
                      </div>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleUpdateStatus('failed')}>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                        Failed
                      </div>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleUpdateStatus('blocked')}>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                        Blocked
                      </div>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleUpdateStatus('not-run')}>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                        Not Run
                      </div>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                <Button 
                  variant="outline" 
                  className="px-3 py-1.5 text-sm flex items-center gap-2 hover:opacity-80 transition-opacity"
                  onClick={handleToggleTestType}
                  disabled={updatingStatus}
                >
                  {testCase.is_manual ? (
                    <>
                      <svg className="w-4 h-4 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      Manual
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      Automated
                    </>
                  )}
                </Button>
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
                  Total Executions
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0 px-3 pb-3">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats?.total_executions || 0}</div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Total test runs</p>
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
                <div className="text-lg font-bold text-purple-600 dark:text-purple-400">{formatDate(testCase.last_run)}</div>
                <p className="text-xs text-gray-500 dark:text-gray-400">Most recent execution</p>
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
                <TabsTrigger value="executions" className="flex-1">Executions</TabsTrigger>
                <TabsTrigger value="fixtures" className="flex-1">Fixtures</TabsTrigger>
              </TabsList>
              
              <div className="p-6">
                <TabsContent value="details" className="space-y-6 mt-0">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card className="border-0 shadow-md">
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-lg">
                          <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900/20 rounded-md flex items-center justify-center">
                            <svg className="w-3 h-3 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </div>
                          Test Information
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 gap-4">
                          <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                            <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Test Type</label>
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mt-1">
                              {testCase.is_manual ? "Manual Test" : "Automated Test"}
                            </p>
                          </div>
                          <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                            <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Execution Order</label>
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mt-1">#{testCase.order}</p>
                          </div>
                          <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                            <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">File Path</label>
                            <p className="text-sm font-mono text-gray-900 dark:text-gray-100 mt-1 break-all">
                              {testCase.test_file_path || "Not specified"}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="border-0 shadow-md">
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-lg">
                          <div className="w-6 h-6 bg-emerald-100 dark:bg-emerald-900/20 rounded-md flex items-center justify-center">
                            <svg className="w-3 h-3 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                            </svg>
                          </div>
                          Tags & Metadata
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Tags</label>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {(() => {
                              let tagsArray: string[] = []
                              if (Array.isArray(testCase.tags)) {
                                tagsArray = testCase.tags
                              } else if (typeof testCase.tags === 'string' && testCase.tags.length > 0) {
                                tagsArray = testCase.tags.split(',').map(tag => tag.trim())
                              }
                              
                              return tagsArray.length > 0 ? (
                                tagsArray.map((tag, idx) => (
                                  <Badge key={idx} variant="outline" className="text-xs">
                                    {tag}
                                  </Badge>
                                ))
                              ) : (
                                <span className="text-sm text-gray-500 dark:text-gray-400">No tags</span>
                              )
                            })()}
                          </div>
                        </div>
                        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Created By</label>
                          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mt-1">
                            {testCase.created_by || "Unknown"}
                          </p>
                        </div>
                        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <label className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Last Updated</label>
                          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mt-1">
                            {formatDate(testCase.updated_at)}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="steps" className="space-y-4 mt-0">
                  <Dialog open={addStepOpen} onOpenChange={setAddStepOpen}>
                    <DialogContent className="w-full max-w-6xl max-h-[90vh] overflow-y-auto" style={{minWidth: '1000px', width: 'min(1152px, 95vw)'}}>
                      <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                          <PlusCircle className="w-6 h-6 text-blue-500" /> {editMode ? "Edit Step" : "Add New Step"}
                        </DialogTitle>
                      </DialogHeader>
                      <form onSubmit={(e: React.FormEvent) => { e.preventDefault(); handleAddStep(); }}>
                        <div className="grid gap-4">
                          {/* Action Field */}
                          <div className="flex flex-col gap-3 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800">
                            <div className="flex items-center gap-3">
                              <Zap className="w-5 h-5 text-yellow-500 flex-shrink-0" />
                              <label className="text-sm font-semibold mb-0">
                                Action {!newStep.referenced_fixture_id && <span className="text-red-500">*</span>}
                              </label>
                            </div>
                            <Input 
                              className="w-full" 
                              placeholder={newStep.referenced_fixture_id ? "Action (optional when calling fixture)" : "Action"} 
                              value={newStep.action} 
                              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewStep(s => ({ ...s, action: e.target.value }))} 
                              required={!newStep.referenced_fixture_id}
                              disabled={!!newStep.referenced_fixture_id}
                            />
                          </div>

                          {/* Data Field */}
                          <div className="flex flex-col gap-3 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800">
                            <div className="flex items-center gap-3">
                              <Database className="w-5 h-5 text-indigo-500 flex-shrink-0" />
                              <label className="text-sm font-semibold mb-0">Data</label>
                            </div>
                            <Textarea 
                              className="w-full min-h-[60px] resize-y" 
                              placeholder="Data" 
                              value={newStep.data} 
                              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewStep(s => ({ ...s, data: e.target.value }))} 
                            />
                          </div>

                          {/* Expected Result Field */}
                          <div className="flex flex-col gap-3 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800">
                            <div className="flex items-center gap-3">
                              <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                              <label className="text-sm font-semibold mb-0">Expected Result</label>
                            </div>
                            <Textarea 
                              className="w-full min-h-[60px] resize-y" 
                              placeholder="Expected Result" 
                              value={newStep.expected} 
                              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewStep(s => ({ ...s, expected: e.target.value }))} 
                            />
                          </div>

                          {/* Playwright Script Field */}
                          <div className="flex flex-col gap-3 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800">
                            <div className="flex items-center gap-3">
                              <Code className="w-5 h-5 text-purple-500 flex-shrink-0" />
                              <label className="text-sm font-semibold mb-0">Playwright Script</label>
                              <Button 
                                type="button" 
                                variant="ghost" 
                                size="sm" 
                                onClick={() => setShowPlaywrightScript(!showPlaywrightScript)}
                                className="ml-auto p-1 h-auto text-xs"
                              >
                                {showPlaywrightScript ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                              </Button>
                            </div>
                            {showPlaywrightScript && (
                              <Textarea 
                                className="w-full min-h-[80px] resize-y" 
                                placeholder="Playwright Script" 
                                value={newStep.playwright_script} 
                                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewStep(s => ({ ...s, playwright_script: e.target.value }))} 
                              />
                            )}
                          </div>

                          {/* Call Fixture Field */}
                          <div className="flex flex-col sm:flex-row sm:items-center gap-3 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800">
                            <div className="flex items-center gap-3 sm:w-32 flex-shrink-0">
                              <svg className="w-5 h-5 text-orange-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                              </svg>
                              <label className="text-sm font-semibold mb-0">Call Fixture</label>
                            </div>
                            <select 
                              className="flex-1 p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                              value={newStep.referenced_fixture_id} 
                              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
                                const selectedFixture = availableFixtures.find(f => f.id === e.target.value);
                                setNewStep(s => ({ 
                                  ...s, 
                                  referenced_fixture_id: e.target.value,
                                  action: selectedFixture ? selectedFixture.name : s.action
                                }))
                              }}
                            >
                              <option value="">No fixture</option>
                              {getFilteredFixtures().map((fixture) => (
                                <option key={fixture.id} value={fixture.id}>
                                  {fixture.name} ({fixture.type})
                                </option>
                              ))}
                            </select>
                          </div>

                          {/* Order and Disabled Fields */}
                          <div className="flex flex-col sm:flex-row gap-4">
                            <div className="flex items-center gap-3 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800 flex-1">
                              <ListOrdered className="w-5 h-5 text-blue-400 flex-shrink-0" />
                              <label className="text-sm font-semibold mb-0 whitespace-nowrap">
                                Order {!editMode && "(Auto)"}
                              </label>
                              <Input 
                                className="flex-1 max-w-24" 
                                type="number" 
                                placeholder="Order" 
                                value={newStep.order} 
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                                  const newOrder = Number(e.target.value);
                                  setNewStep(s => {
                                    const updatedStep = { ...s, order: newOrder };
                                    
                                    // Clear referenced_fixture_id if it's not compatible with new order
                                    if (s.referenced_fixture_id) {
                                      const selectedFixture = availableFixtures.find(f => f.id === s.referenced_fixture_id);
                                      if (selectedFixture) {
                                        if ((newOrder === 1 && selectedFixture.type !== "extend") || 
                                            (newOrder > 1 && selectedFixture.type !== "inline")) {
                                          updatedStep.referenced_fixture_id = "";
                                          updatedStep.action = "";
                                        }
                                      }
                                    }
                                    
                                    return updatedStep;
                                  });
                                }} 
                                min={1} 
                                max={steps.length}
                                disabled={!editMode}
                              />
                            </div>
                            <div className="flex items-center gap-3 p-3 border rounded-lg bg-gray-50 dark:bg-gray-800">
                              <Ban className="w-5 h-5 text-red-400 flex-shrink-0" />
                              <input 
                                type="checkbox" 
                                id="step-disabled" 
                                checked={newStep.disabled} 
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewStep(s => ({ ...s, disabled: e.target.checked }))} 
                                className="mr-2" 
                              />
                              <label htmlFor="step-disabled" className="text-sm font-semibold mb-0 whitespace-nowrap">Disabled</label>
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
                              await apiClient(`/steps/test-cases/${testCaseId}/steps/auto-reorder`, {
                                method: "PATCH"
                              })
                              // Reload steps
                              const stepsData = await apiClient(`/steps/test-cases/${testCaseId}/steps`)
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
                                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 flex items-center gap-2">
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
                                      {/* Show icon when test case is not manual and step has no playwright script and no fixture reference */}
                                      {!testCase.is_manual && !step.playwright_script && !step.referenced_fixture_id && (
                                        <div 
                                          className="w-4 h-4 text-amber-500 cursor-help"
                                          title="Playwright script not available"
                                        >
                                          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                                          </svg>
                                        </div>
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

                <TabsContent value="executions" className="space-y-4 mt-0">
                  <Card className="border-0 shadow-md">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <div className="w-6 h-6 bg-purple-100 dark:bg-purple-900/20 rounded-md flex items-center justify-center">
                          <svg className="w-3 h-3 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        Execution History
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {executions.length > 0 ? (
                          executions.map((execution, index) => (
                            <div key={execution.id} className="group p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-all duration-200 hover:border-blue-300 dark:hover:border-blue-600">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                  <div className="flex-shrink-0">
                                    <Badge className={`${getStatusColor(execution.status)} px-2 py-1 text-xs flex items-center gap-1.5`} variant="secondary">
                                      {getStatusIcon(execution.status)}
                                      {execution.status}
                                    </Badge>
                                  </div>
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-4 text-sm">
                                      <span className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                        </svg>
                                        {formatDate(execution.created_at)}
                                      </span>
                                      <span className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        {formatDuration(execution.duration)}
                                      </span>
                                      {execution.retries > 0 && (
                                        <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                          </svg>
                                          {execution.retries} retries
                                        </span>
                                      )}
                                    </div>
                                    <div className="text-xs text-gray-500 dark:text-gray-400">
                                      Execution #{executions.length - index}
                                    </div>
                                  </div>
                                </div>
                                {execution.error_message && (
                                  <Button variant="outline" size="sm" className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                                    View Error
                                  </Button>
                                )}
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="text-center py-12">
                            <div className="w-16 h-16 mx-auto bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                            </div>
                            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">No Execution History</h3>
                            <p className="text-gray-500 dark:text-gray-400">This test case hasn't been executed yet.</p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                                 <TabsContent value="fixtures" className="space-y-4 mt-0">
                   <Card className="border-0 shadow-md">
                     <CardHeader>
                       <div className="flex items-center justify-between">
                         <CardTitle className="flex items-center gap-2 text-lg">
                           <div className="w-6 h-6 bg-yellow-100 dark:bg-yellow-900/20 rounded-md flex items-center justify-center">
                             <Settings className="w-3 h-3 text-yellow-600 dark:text-yellow-400" />
                           </div>
                           Fixtures
                         </CardTitle>
                         <Button 
                           onClick={() => setAddFixtureOpen(true)}
                           size="sm"
                           className="flex items-center gap-2"
                         >
                           <PlusCircle className="w-4 h-4" />
                           Add Fixture
                         </Button>
                       </div>
                     </CardHeader>
                     <CardContent>
                       <div className="space-y-3">
                         {fixtures.length > 0 ? (
                           fixtures.map((fixture, index) => (
                             <div key={fixture.fixture_id} className="group p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-all duration-200 hover:border-yellow-300 dark:hover:border-yellow-600">
                               <div className="flex items-start gap-4">
                                 <div className="flex-shrink-0 w-8 h-8 bg-yellow-100 dark:bg-yellow-900/20 rounded-full flex items-center justify-center">
                                   <span className="text-sm font-semibold text-yellow-600 dark:text-yellow-400">{fixture.order}</span>
                                 </div>
                                 <div className="flex-1 space-y-2">
                                   <div className="flex items-center justify-between">
                                     <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                       {fixture.name}
                                     </h4>
                                     <div className="flex items-center gap-2">
                                       <Button 
                                         size="sm" 
                                         variant="outline" 
                                         onClick={() => {
                                           setSelectedFixtureId(fixture.fixture_id)
                                           setAddFixtureOpen(true)
                                         }}
                                         className="text-xs"
                                       >
                                         View Detail
                                       </Button>
                                       <Button 
                                         size="sm" 
                                         variant="destructive" 
                                         onClick={() => handleRemoveFixture(fixture.fixture_id)}
                                         className="text-xs"
                                       >
                                         <Trash2 className="w-3 h-3" />
                                       </Button>
                                     </div>
                                   </div>
                                   
                                   <div className="text-sm text-gray-600 dark:text-gray-400">
                                     {fixture.type && (
                                       <p><strong>Type:</strong> {fixture.type}</p>
                                     )}
                                     <p><strong>Order:</strong> {fixture.order}</p>
                                   </div>
                                 </div>
                               </div>
                             </div>
                           ))
                         ) : (
                           <div className="text-center py-12">
                             <div className="w-16 h-16 mx-auto bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                               <Settings className="w-8 h-8 text-gray-400" />
                             </div>
                             <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">No Fixtures</h3>
                             <p className="text-gray-500 dark:text-gray-400">This test case has no fixtures. Click "Add Fixture" to get started.</p>
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
      
      {/* Run Settings Dialog */}
      <Dialog open={runSettingsOpen} onOpenChange={setRunSettingsOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Test Execution Settings</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Timeout (s)</label>
                <Input
                  type="number"
                  value={runSettings.timeout}
                  onChange={(e) => setRunSettings(s => ({ ...s, timeout: Number(e.target.value) }))}
                  min={0}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Expect Timeout (s)</label>
                <Input
                  type="number"
                  value={runSettings.expect_timeout}
                  onChange={(e) => setRunSettings(s => ({ ...s, expect_timeout: Number(e.target.value) }))}
                  min={0}
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input
                id="headless-toggle"
                type="checkbox"
                checked={runSettings.headless}
                onChange={(e) => setRunSettings(s => ({ ...s, headless: e.target.checked }))}
              />
              <label htmlFor="headless-toggle" className="text-sm font-medium">Headless Mode</label>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Screenshot</label>
                <select
                  className="w-full p-2 border rounded-md bg-white dark:bg-gray-800"
                  value={runSettings.screenshot}
                  onChange={(e) => setRunSettings(s => ({ ...s, screenshot: e.target.value as any }))}
                >
                  <option value="off">Off</option>
                  <option value="on">On</option>
                  <option value="only-on-failure">Only on failure</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Video</label>
                <select
                  className="w-full p-2 border rounded-md bg-white dark:bg-gray-800"
                  value={runSettings.video}
                  onChange={(e) => setRunSettings(s => ({ ...s, video: e.target.value as any }))}
                >
                  <option value="off">Off</option>
                  <option value="on">On</option>
                  <option value="retain-on-failure">Retain on failure</option>
                  <option value="on-first-retry">On first retry</option>
                </select>
              </div>
            </div>
            
            {/* Browser Selection */}
            <div className="space-y-3">
              <label className="text-sm font-medium">Browser</label>
              <div className="grid grid-cols-3 gap-3">
                <div className="flex items-center gap-2">
                  <input
                    id="browser-chromium"
                    type="radio"
                    name="browser"
                    value="chromium"
                    checked={runSettings.browser === 'chromium'}
                    onChange={(e) => setRunSettings(s => ({ ...s, browser: 'chromium' }))}
                  />
                  <label htmlFor="browser-chromium" className="text-sm">Chrome</label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    id="browser-firefox"
                    type="radio"
                    name="browser"
                    value="firefox"
                    checked={runSettings.browser === 'firefox'}
                    onChange={(e) => setRunSettings(s => ({ ...s, browser: 'firefox' }))}
                  />
                  <label htmlFor="browser-firefox" className="text-sm">Firefox</label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    id="browser-webkit"
                    type="radio"
                    name="browser"
                    value="webkit"
                    checked={runSettings.browser === 'webkit'}
                    onChange={(e) => setRunSettings(s => ({ ...s, browser: 'webkit' }))}
                  />
                  <label htmlFor="browser-webkit" className="text-sm">Safari</label>
                </div>
              </div>
            </div>
            
            {/* Execution Mode Options */}
            <div className="space-y-3">
              <label className="text-sm font-medium">Execution Mode</label>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <input
                    id="wait-for-result"
                    type="radio"
                    name="execution-mode"
                    value="wait"
                    checked={runSettings.executionMode === 'wait'}
                    onChange={(e) => setRunSettings(s => ({ ...s, executionMode: 'wait' }))}
                  />
                  <label htmlFor="wait-for-result" className="text-sm">Wait for Result</label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    id="background-run"
                    type="radio"
                    name="execution-mode"
                    value="background"
                    checked={runSettings.executionMode === 'background'}
                    onChange={(e) => setRunSettings(s => ({ ...s, executionMode: 'background' }))}
                  />
                  <label htmlFor="background-run" className="text-sm">Background Run</label>
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRunSettingsOpen(false)}>Cancel</Button>
            <Button onClick={handleRunTest} disabled={runningTest}>
              {runningTest ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Running...
                </>
              ) : (
                'Run'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Scheduling Message */}
      {schedulingMessage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-xl">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <span className="text-lg font-medium">{schedulingMessage}</span>
            </div>
          </div>
        </div>
      )}
      
      {/* Test Result Dialog */}
      <Dialog open={testResultOpen} onOpenChange={setTestResultOpen}>
        <DialogContent className="sm:max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              Test Result
            </DialogTitle>
          </DialogHeader>
          
          {/* Tabs */}
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveResultTab('executions')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeResultTab === 'executions'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                Test Case
              </button>
              <button
                onClick={() => setActiveResultTab('logs')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeResultTab === 'logs'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                Log Results
              </button>
            </nav>
          </div>
          
          {/* Tab Content */}
          <div className="mt-4">
            {activeResultTab === 'executions' ? (
              /* Tab 1: Test Case from Current Run */
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium">Test Case from Current Run</h3>
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {testResult ? `Execution ID: ${testResult.execution_id || 'N/A'}` : 'No execution data'}
                  </div>
                </div>
                
                {testResult ? (
                  <div className="space-y-3">
                    {/* Single test case result from current run */}
                    <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-4 h-4 rounded-full ${
                            testResult.status === 'passed' ? 'bg-green-500' : 'bg-red-500'
                          }`}></div>
                          <div>
                            <div className="font-medium text-sm">
                              {testCase?.name || 'Current Test Case'}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              Execution ID: {testResult.execution_id || 'N/A'}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium">
                            {testResult.duration ? `${(testResult.duration / 1000).toFixed(2)}s` : 'N/A'}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            Status: {testResult.status || 'N/A'}
                          </div>
                        </div>
                      </div>
                      
                      {/* Playwright test results summary */}
                      {testResult.output && (
                        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                          <div className="text-xs font-medium text-gray-600 mb-2">Playwright Test Results:</div>
                          <div className="grid grid-cols-4 gap-4 text-xs">
                            <div>
                              <span className="text-gray-500 dark:text-gray-400">Status:</span>
                              <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                                testResult.status === 'passed' 
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' 
                                  : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                              }`}>
                                {testResult.status === 'passed' ? '✅ Passed' : '❌ Failed'}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500 dark:text-gray-400">Browsers:</span>
                              <span className="ml-2">
                                {(() => {
                                  try {
                                    if (testResult.output) {
                                      const outputData = JSON.parse(testResult.output);
                                      if (outputData.config && outputData.config.projects) {
                                        const actualProjects = outputData.config.projects.filter((p: any) => 
                                          p.id === runSettings.browser || p.name === runSettings.browser
                                        );
                                        return `${actualProjects.length} (${actualProjects.map((p: any) => p.name).join(', ')})`;
                                      }
                                    }
                                    return 'N/A';
                                  } catch (e) {
                                    return 'N/A';
                                  }
                                })()}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500 dark:text-gray-400">Total Tests:</span>
                              <span className="ml-2">
                                {(() => {
                                  try {
                                    if (testResult.output) {
                                      const outputData = JSON.parse(testResult.output);
                                      if (outputData.stats) {
                                        const total = outputData.stats.expected || 0;
                                        const passed = outputData.stats.expected - (outputData.stats.unexpected || 0);
                                        return `${passed}/${total} passed`;
                                      }
                                    }
                                    return 'N/A';
                                  } catch (e) {
                                    return 'N/A';
                                  }
                                })()}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500 dark:text-gray-400">Total Duration:</span>
                              <span className="ml-2">
                                {(() => {
                                  try {
                                    if (testResult.output) {
                                      const outputData = JSON.parse(testResult.output);
                                      if (outputData.stats && outputData.stats.duration) {
                                        return `${(outputData.stats.duration / 1000).toFixed(1)}s`;
                                      }
                                    }
                                    return 'N/A';
                                  } catch (e) {
                                    return 'N/A';
                                  }
                                })()}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    <svg className="w-12 h-12 mx-auto mb-4 text-gray-300 dark:text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <p>No test execution data available</p>
                    <p className="text-xs mt-1">Run a test first to see execution results</p>
                  </div>
                )}
              </div>
            ) : (
              /* Tab 2: Log Results */
              <div className="space-y-4">
                {testResult && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-600">Status</label>
                        <div className={`mt-1 px-3 py-2 rounded-md text-sm font-medium ${
                          testResult.status === 'passed' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' 
                            : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                        }`}>
                          {testResult.status === 'passed' ? '✅ Passed' : '❌ Failed'}
                        </div>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600">Duration</label>
                        <div className="mt-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-md text-sm">
                          {testResult.duration ? `${(testResult.duration / 1000).toFixed(2)}s` : 'N/A'}
                        </div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-600">Execution ID</label>
                        <div className="mt-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-md text-sm font-mono">
                          {testResult.execution_id || 'N/A'}
                        </div>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600">Test Result ID</label>
                        <div className="mt-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-md text-sm font-mono">
                          {testResult.test_result_id || 'N/A'}
                        </div>
                      </div>
                    </div>
                    
                    {testResult.output && (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium text-gray-600">Output</label>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(testResult.output);
                              // Show temporary success message
                              const button = event?.target as HTMLButtonElement;
                              if (button) {
                                const originalText = button.innerHTML;
                                button.innerHTML = '✓ Copied!';
                                button.className = 'text-green-600 hover:text-green-700 text-xs font-medium px-2 py-1 rounded hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors';
                                setTimeout(() => {
                                  button.innerHTML = originalText;
                                  button.className = 'text-gray-600 hover:text-gray-700 text-xs font-medium px-2 py-1 rounded hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors';
                                }, 2000);
                              }
                            }}
                            className="text-gray-600 hover:text-gray-700 text-xs font-medium px-2 py-1 rounded hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors flex items-center gap-1"
                            title="Copy to clipboard"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                            Copy
                          </button>
                        </div>
                        <div className="mt-1 p-3 bg-gray-100 dark:bg-gray-800 rounded-md text-sm font-mono max-h-64 overflow-y-auto">
                          <pre className="whitespace-pre-wrap">{testResult.output}</pre>
                        </div>
                      </div>
                    )}
                    
                    {testResult.error && (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium text-gray-600">Error</label>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(testResult.error);
                              // Show temporary success message
                              const button = event?.target as HTMLButtonElement;
                              if (button) {
                                const originalText = button.innerHTML;
                                button.innerHTML = '✓ Copied!';
                                button.className = 'text-green-600 hover:text-green-700 text-xs font-medium px-2 py-1 rounded hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors';
                                setTimeout(() => {
                                  button.innerHTML = originalText;
                                  button.className = 'text-gray-600 hover:text-gray-700 text-xs font-medium px-2 py-1 rounded hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors';
                                }, 2000);
                              }
                            }}
                            className="text-gray-600 hover:text-gray-700 text-xs font-medium px-2 py-1 rounded hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors flex items-center gap-1"
                            title="Copy to clipboard"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 00-2-2v-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                            Copy
                          </button>
                        </div>
                        <div className="mt-1 p-3 bg-red-100 dark:bg-red-800 rounded-md text-sm font-mono max-h-64 overflow-y-auto">
                          <pre className="whitespace-pre-wrap text-red-700 dark:text-red-300">{testResult.error}</pre>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button onClick={() => setTestResultOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
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
                          <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 flex items-center gap-2">
                            {step.action.charAt(0).toUpperCase() + step.action.slice(1)}
                            {/* Show icon when test case is not manual and step has no playwright script and no fixture reference */}
                            {!testCase.is_manual && !step.playwright_script && !step.referenced_fixture_id && (
                              <div 
                                className="w-4 h-4 text-amber-500 cursor-help"
                                title="Playwright script not available"
                              >
                                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                                </svg>
                              </div>
                            )}
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

             {/* Add Fixture Modal */}
       <Dialog open={addFixtureOpen} onOpenChange={setAddFixtureOpen}>
         <DialogContent className="max-w-2xl">
           <DialogHeader>
             <DialogTitle className="flex items-center gap-2">
               <Settings className="w-6 h-6 text-yellow-500" />
               Add Fixture to Test Case
             </DialogTitle>
           </DialogHeader>
           
           <div className="space-y-4">
             <div>
               <label className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2 block">
                 Select Fixture
               </label>
               <select
                 value={selectedFixtureId}
                 onChange={(e) => setSelectedFixtureId(e.target.value)}
                 className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
               >
                 <option value="">Select a fixture...</option>
                 {availableFixtures
                   .filter(fixture => !fixtures.some(tcFixture => tcFixture.fixture_id === fixture.id))
                   .map(fixture => (
                     <option key={fixture.id} value={fixture.id}>
                       {fixture.name} ({fixture.type || 'extend'})
                     </option>
                   ))}
               </select>
             </div>
             
             {selectedFixtureId && (
               <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800">
                 <h4 className="font-medium mb-2">Selected Fixture Details</h4>
                 <div className="space-y-2 text-sm">
                   <p><strong>Name:</strong> {availableFixtures.find(f => f.id === selectedFixtureId)?.name}</p>
                   <p><strong>Type:</strong> {availableFixtures.find(f => f.id === selectedFixtureId)?.type || 'extend'}</p>

                 </div>
               </div>
             )}
           </div>
           
           <DialogFooter className="mt-6">
             <Button variant="secondary" onClick={() => {
               setAddFixtureOpen(false)
               setSelectedFixtureId("")
             }}>
               Cancel
             </Button>
             <Button 
               onClick={handleAddFixture}
               disabled={!selectedFixtureId || addingFixture}
               className="flex items-center gap-2"
             >
               {addingFixture ? "Adding..." : "Add Fixture"}
             </Button>
           </DialogFooter>
         </DialogContent>
       </Dialog>
    </AppLayout>
  )
} 