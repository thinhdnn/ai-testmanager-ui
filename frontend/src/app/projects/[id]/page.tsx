"use client"

import React, { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { notFound } from "next/navigation"
import { AppLayout } from "@/components/app-layout"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { apiClient } from "@/lib/apiClient"
import { TestCaseList } from "@/components/ui/test-case-list"
import { TestExecutionList } from "@/components/ui/test-execution-list"
import { FixtureList } from "@/components/ui/fixture-list"
import { ReleaseList } from "@/components/ui/release-list"
import { PageList } from "@/components/ui/page-list"
import { Button } from "@/components/ui/button"
import { CreateTestCaseModal } from "@/components/create-test-case-modal"
import { CreateFixtureModal } from "@/components/create-fixture-modal"
import { CreatePageModal } from "@/components/create-page-modal"
import { DeleteConfirmationModal } from "@/components/ui/delete-confirmation-modal"
import type { TestCase } from "@/lib/columns/test-case-columns"
import type { Fixture } from "@/lib/columns/fixture-columns"
import type { TestExecution } from "@/lib/columns/test-execution-columns"
import type { Release } from "@/lib/columns/release-columns"
import { useAuth } from '@/contexts/AuthContext'
import { Trash2 } from "lucide-react"

// Define a type for the project object
interface ProjectDetail {
  id: string;
  name: string;
  description?: string;
  test_cases_count?: number;
}

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>()
  const id = params?.id
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [project, setProject] = useState<ProjectDetail | null>(null)
  const [stats, setStats] = useState<Record<string, unknown> | null>(null)
  const [testCases, setTestCases] = useState<TestCase[]>([])
  const [executions, setExecutions] = useState<TestExecution[]>([])
  const [fixtures, setFixtures] = useState<Fixture[]>([])
  const [releases, setReleases] = useState<Release[]>([])
  const [pages, setPages] = useState<{ id: string; name: string; author?: string; lastModified?: string }[]>([])
  const [activeTab, setActiveTab] = useState("test-cases")
  const [showCreateTestCaseModal, setShowCreateTestCaseModal] = useState(false)
  const [showCreateFixtureModal, setShowCreateFixtureModal] = useState(false)
  const [showCreatePageModal, setShowCreatePageModal] = useState(false)
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const router = useRouter()

  useEffect(() => {
    if (!id) return
    setLoading(true)
    setError(null)
    Promise.all([
      apiClient(`/projects/${id}`),
      apiClient(`/test-results/projects/${id}/stats`),
      apiClient(`/test-cases/?project_id=${id}&skip=0&limit=100`),
      apiClient(`/test-results/projects/${id}/executions?limit=50`),
      apiClient(`/fixtures/?project_id=${id}`),
      apiClient(`/projects/${id}/releases`),
      apiClient(`/pages/?project_id=${id}`)
    ])
      .then(([project, stats, testCases, executions, fixtures, releases, pages]) => {
        if (!project) {
          notFound()
          return
        }
        setProject(project as ProjectDetail)
        setStats(stats)
        
        // Map backend test cases to frontend format
        setTestCases((testCases as any[]).map(tc => ({
          id: String(tc.id),
          title: tc.name,
          status: tc.status,
          author: tc.author_name || tc.created_by || "Unknown",
          lastRun: tc.last_run || "",
          tag: Array.isArray(tc.tags) ? tc.tags : (typeof tc.tags === 'string' ? tc.tags.split(',').map((tag: string) => tag.trim()) : []),
        })))
        
        // Map backend test case executions to frontend executions format
        setExecutions((executions as any[]).map(exec => {
          // Handle cases where related data might not be loaded
          const testCaseName = exec.test_case?.name || "Unknown Test Case"
          const status = exec.status || "unknown"
          const startTime = exec.start_time || exec.created_at || ""
          const duration = exec.duration ? `${(exec.duration / 1000).toFixed(2)}s` : "0s"
          const executor = exec.test_result?.created_by || "System"
          const environment = exec.test_result?.browser || "Unknown"
          
          return {
            id: String(exec.id),
            testCase: testCaseName,
            status: status,
            startTime: startTime,
            duration: duration,
            executor: executor,
            environment: environment,
          }
        }))
        
        // Map backend fixtures to frontend format
        setFixtures((fixtures as any[]).map(f => ({
          id: String(f.id),
          name: f.name,
          type: f.type,
          status: "active" as const, // Backend doesn't have status field, default to active
          lastModified: f.updated_at || f.created_at || new Date().toISOString(),
          author: f.author_name || f.created_by || "Unknown",
          environment: "development" as const, // Backend doesn't have environment, default
        })))
        
        // Map backend releases to frontend format
        setReleases((releases as any[]).map(r => ({
          id: String(r.id),
          name: r.name,
          version: r.version,
          status: r.status || "active",
          date: r.release_date || r.created_at || new Date().toISOString(),
          author: r.author_name || r.created_by || "Unknown",
        })))
        
        // Map backend pages to frontend format
        setPages((pages as any[]).map(p => ({
          id: String(p.id),
          name: p.name,
          lastModified: p.updated_at || p.created_at || new Date().toISOString(),
          author: p.author_name || p.created_by || "Unknown",
        })))
        
        setLoading(false)
      })
      .catch((err) => {
        console.error("Failed to load project data:", err)
        setError("Failed to load project data")
        setLoading(false)
      })
  }, [id])

  if (loading) {
    return <div className="p-8">Loading project...</div>
  }
  if (error) {
    return <div className="p-8 text-red-600">{error}</div>
  }
  if (!project) {
    return notFound()
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20"
      case "completed":
        return "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20"
      case "on-hold":
        return "bg-amber-500/10 text-amber-500 hover:bg-amber-500/20"
      default:
        return "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20"
    }
  }

  const handleAddNew = (type: string) => {
    // Handle add new functionality based on type
    switch (type) {
      case "test-case":
        setShowCreateTestCaseModal(true)
        break
      case "fixture":
        setShowCreateFixtureModal(true)
        break
      case "execution":
        console.log("Add new execution")
        // TODO: Navigate to add execution page or open modal
        break
      case "release":
        console.log("Add new release")
        // TODO: Navigate to add release page or open modal
        break
      default:
        break
    }
  }

  const handleTestCaseCreated = () => {
    // Refresh test cases data after creating a new test case
    if (!id) return
    apiClient(`/test-cases/?project_id=${id}&skip=0&limit=100`)
      .then((testCases) => {
        setTestCases((testCases as any[]).map(tc => ({
          id: String(tc.id),
          title: tc.name,
          status: tc.status,
          author: tc.author_name || tc.created_by || "Unknown",
          lastRun: tc.last_run || "",
          tag: Array.isArray(tc.tags) ? tc.tags : (typeof tc.tags === 'string' ? tc.tags.split(',').map((tag: string) => tag.trim()) : []),
        })))
      })
      .catch((err) => {
        console.error("Failed to refresh test cases:", err)
      })
  }

  const handleFixtureCreated = () => {
    // Refresh fixtures data after creating a new fixture
    if (!id) return
    apiClient(`/fixtures/?project_id=${id}`)
      .then((fixtures) => {
        setFixtures((fixtures as any[]).map(f => ({
          id: String(f.id),
          name: f.name,
          type: f.type,
          status: "active" as const, // Backend doesn't have status field, default to active
          lastModified: f.updated_at || f.created_at || new Date().toISOString(),
          author: f.author_name || f.created_by || "Unknown",
          environment: "development" as const, // Backend doesn't have environment, default
        })))
      })
      .catch((err) => {
        console.error("Failed to refresh fixtures:", err)
      })
  }

  const handlePageCreated = () => {
    if (!id) return
    apiClient(`/pages/?project_id=${id}`)
      .then((pages) => {
        setPages((pages as any[]).map(p => ({
          id: String(p.id),
          name: p.name,
          lastModified: p.updated_at || p.created_at || new Date().toISOString(),
          author: p.author_name || p.created_by || "Unknown",
        })))
      })
      .catch((err) => {
        console.error("Failed to refresh pages:", err)
      })
  }

  const handleDeleteProject = async () => {
    if (!id) return
    
    setIsDeleting(true)
    try {
      await apiClient(`/projects/${id}`, { method: 'DELETE' })
      // Redirect to projects list after successful deletion
      router.push('/projects')
    } catch (err) {
      console.error('Failed to delete project:', err)
      // You might want to show a toast notification here
    } finally {
      setIsDeleting(false)
    }
  }

  const getAddButtonText = (tab: string) => {
    switch (tab) {
      case "test-cases":
        return "Add Test Case"
      case "fixtures":
        return "Add Fixture"
      case "executions":
        return "Add Execution"
      case "release":
        return "Add Release"
      case "pages":
        return "Add Page"
      default:
        return "Add New"
    }
  }

  const getAddButtonType = (tab: string) => {
    switch (tab) {
      case "test-cases":
        return "test-case"
      case "fixtures":
        return "fixture"
      case "executions":
        return "execution"
      case "release":
        return "release"
      case "pages":
        return "page"
      default:
        return ""
    }
  }

  return (
    <AppLayout title={project.name}>
      <div className="space-y-6">
        {/* Project Overview Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <CardTitle className="text-2xl">{project.name}</CardTitle>
                <p className="text-muted-foreground">{project.description}</p>
              </div>
              <div className="flex items-center gap-3">
                <Badge className={getStatusColor("active")} variant="secondary">
                  Active
                </Badge>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setShowDeleteConfirmation(true)}
                  className="flex items-center gap-2"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete Project
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-2">
              <Card className="bg-card/50 shadow-sm">
                <CardHeader className="p-2">
                  <CardTitle className="text-xs font-medium">Progress</CardTitle>
                </CardHeader>
                <CardContent className="p-2 pt-0">
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-lg font-bold">0%</span>
                    </div>
                    <Progress value={0} className="h-1" />
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-card/50 shadow-sm">
                <CardHeader className="p-2">
                  <CardTitle className="text-xs font-medium">Test Cases</CardTitle>
                </CardHeader>
                <CardContent className="p-2 pt-0">
                  <div className="text-lg font-bold">{project.test_cases_count || 0}</div>
                </CardContent>
              </Card>
              <Card className="bg-card/50 shadow-sm">
                <CardHeader className="p-2">
                  <CardTitle className="text-xs font-medium">Pass Rate</CardTitle>
                </CardHeader>
                <CardContent className="p-2 pt-0">
                  <div className="text-lg font-bold">{typeof stats?.success_rate === 'number' ? stats.success_rate : 0}%</div>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs defaultValue="test-cases" className="space-y-4" onValueChange={setActiveTab}>
          <div className="flex items-center justify-between">
            <TabsList className="bg-background border-b rounded-none p-0">
            <TabsTrigger value="test-cases" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-6 py-3">Test Cases</TabsTrigger>
            <TabsTrigger value="fixtures" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-6 py-3">Fixtures</TabsTrigger>
            <TabsTrigger value="pages" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-6 py-3">Pages</TabsTrigger>
            <TabsTrigger value="executions" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-6 py-3">Executions</TabsTrigger>
            <TabsTrigger value="release" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-6 py-3">Release</TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-6 py-3">Settings</TabsTrigger>
          </TabsList>
            {activeTab !== "settings" && (
              <Button 
                onClick={() => {
                  const type = getAddButtonType(activeTab)
                  if (type === 'page') {
                    setShowCreatePageModal(true)
                  } else {
                    handleAddNew(type)
                  }
                }}
                className="flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                {getAddButtonText(activeTab)}
              </Button>
            )}
          </div>
          <TabsContent value="test-cases" className="space-y-4">
            <Card>
              <CardContent className="pt-6">
                <TestCaseList data={testCases} />
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="fixtures" className="space-y-4">
            <Card>
              <CardContent className="pt-6">
                <FixtureList data={fixtures} />
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="pages" className="space-y-4">
            <Card>
              <CardContent className="pt-6">
                <PageList data={pages} />
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="executions" className="space-y-4">
            <Card>
              <CardContent className="pt-6">
                <TestExecutionList data={executions} />
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="release" className="space-y-4">
            <Card>
              <CardContent className="pt-6">
                <ReleaseList data={releases} />
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="settings" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Project Settings</CardTitle>
                <p className="text-sm text-muted-foreground">
                  Configure Playwright test settings for this project. Changes are automatically applied to the generated configuration files.
                </p>
              </CardHeader>
              <CardContent className="pt-6">
                <ConfigurationForm />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      <CreateTestCaseModal
        open={showCreateTestCaseModal}
        onOpenChange={setShowCreateTestCaseModal}
        onTestCaseCreated={handleTestCaseCreated}
        projectId={id || ""}
        // Debug log for modal render
        key={showCreateTestCaseModal ? "testcase-open" : "testcase-closed"}
      />
      <CreateFixtureModal
        open={showCreateFixtureModal}
        onOpenChange={setShowCreateFixtureModal}
        onFixtureCreated={handleFixtureCreated}
        projectId={id || ""}
        // Debug log for modal render
        key={showCreateFixtureModal ? "fixture-open" : "fixture-closed"}
      />
      <CreatePageModal
        open={showCreatePageModal}
        onOpenChange={setShowCreatePageModal}
        onPageCreated={handlePageCreated}
        projectId={id || ""}
        key={showCreatePageModal ? "page-open" : "page-closed"}
      />
      <DeleteConfirmationModal
        open={showDeleteConfirmation}
        onOpenChange={setShowDeleteConfirmation}
        onConfirm={handleDeleteProject}
        title="Delete Project"
        description={`Are you sure you want to delete the project "${project?.name}"? This action cannot be undone and will permanently remove the project and all its associated data.`}
        isLoading={isDeleting}
      />
    </AppLayout>
  )
}

function ConfigurationForm() {
  const params = useParams<{ id: string }>()
  const projectId = params?.id
  const { user } = useAuth()
  
  const [timeoutValue, setTimeoutValue] = useState(30000)
  const [expectTimeout, setExpectTimeout] = useState(10000)
  const [retries, setRetries] = useState(1)
  const [workers, setWorkers] = useState(1)
  const [fullyParallel, setFullyParallel] = useState(false)
  const [baseUrl, setBaseUrl] = useState("")
  const [headless, setHeadless] = useState(false)
  const [viewportWidth, setViewportWidth] = useState(1920)
  const [viewportHeight, setViewportHeight] = useState(1080)
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(true)
  const [screenshot, setScreenshot] = useState("off")
  const [video, setVideo] = useState("off")
  const [regenerating, setRegenerating] = useState(false)

  // Load settings from backend on component mount
  useEffect(() => {
    if (!projectId) return
    
    const loadSettings = async () => {
      try {
        const settings = await apiClient(`/projects/${projectId}/settings/dict`)
        
        // Map backend settings to state (convert milliseconds to seconds)
        if (settings.TIMEOUT) setTimeoutValue(Math.round(parseInt(settings.TIMEOUT) / 1000))
        if (settings.EXPECT_TIMEOUT) setExpectTimeout(Math.round(parseInt(settings.EXPECT_TIMEOUT) / 1000))
        if (settings.RETRIES) setRetries(parseInt(settings.RETRIES))
        if (settings.WORKERS) setWorkers(parseInt(settings.WORKERS))
        if (settings.FULLY_PARALLEL) setFullyParallel(settings.FULLY_PARALLEL === 'true')
        if (settings.BASE_URL) setBaseUrl(settings.BASE_URL)
        if (settings.HEADLESS_MODE) setHeadless(settings.HEADLESS_MODE === 'true')
        if (settings.VIEWPORT_WIDTH) setViewportWidth(parseInt(settings.VIEWPORT_WIDTH))
        if (settings.VIEWPORT_HEIGHT) setViewportHeight(parseInt(settings.VIEWPORT_HEIGHT))
        if (settings.SCREENSHOT) setScreenshot(settings.SCREENSHOT)
        if (settings.VIDEO) setVideo(settings.VIDEO)
      } catch (error) {
        console.error('Failed to load project settings:', error)
        // Use default values if loading fails
      } finally {
        setLoading(false)
      }
    }
    
    loadSettings()
  }, [projectId])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!projectId) return
    
    try {
      // Save each setting to backend
      const settingsToSave = [
        { key: 'TIMEOUT', value: timeoutValue.toString() },
        { key: 'EXPECT_TIMEOUT', value: expectTimeout.toString() },
        { key: 'RETRIES', value: retries.toString() },
        { key: 'WORKERS', value: workers.toString() },
        { key: 'FULLY_PARALLEL', value: fullyParallel.toString() },
        { key: 'BASE_URL', value: baseUrl },
        { key: 'HEADLESS_MODE', value: headless.toString() },
        { key: 'VIEWPORT_WIDTH', value: viewportWidth.toString() },
        { key: 'VIEWPORT_HEIGHT', value: viewportHeight.toString() },
        { key: 'SCREENSHOT', value: screenshot },
        { key: 'VIDEO', value: video },
      ]
      
      // Update each setting via API
      await Promise.all(
        settingsToSave.map(setting =>
          apiClient(`/projects/${projectId}/settings/${setting.key}?value=${encodeURIComponent(setting.value)}&updated_by=${user?.id}`, {
            method: 'PUT',
          })
        )
      )
      
      // Regenerate Playwright config after saving all settings
      await apiClient(`/projects/${projectId}/regenerate-config`, {
        method: 'POST',
      })
      
    setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (error) {
      console.error('Failed to save settings:', error)
      // Could show error message to user
    }
  }

  async function handleRegenerateConfig() {
    if (!projectId) return
    
    setRegenerating(true)
    try {
      await apiClient(`/projects/${projectId}/regenerate-config`, {
        method: 'POST',
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (error) {
      console.error('Failed to regenerate config:', error)
    } finally {
      setRegenerating(false)
    }
  }

  if (loading) {
    return <div className="p-6">Loading settings...</div>
  }

  return (
    <form onSubmit={handleSubmit} className="w-full p-6 space-y-8">
      {/* Base URL */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Project Configuration</h3>
        <label className="block text-sm font-semibold text-gray-600 mb-1">Base URL</label>
        <input
          type="text"
          className="w-full rounded-lg border px-3 py-2 focus:ring-2 focus:ring-primary focus:border-primary transition"
          value={baseUrl}
          onChange={e => setBaseUrl(e.target.value)}
          placeholder="https://example.com"
        />
      </div>
      {/* Row 2: Timeout, Expect Timeout, Retries, Workers */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Test Execution Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 gap-y-4">
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-1">Timeout (s)</label>
          <input type="number" className="w-full rounded-lg border h-10 px-3 py-2 text-base focus:ring-2 focus:ring-primary focus:border-primary transition" value={timeoutValue} onChange={e => setTimeoutValue(Number(e.target.value))} min={0} />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-1">Expect Timeout (s)</label>
          <input type="number" className="w-full rounded-lg border h-10 px-3 py-2 text-base focus:ring-2 focus:ring-primary focus:border-primary transition" value={expectTimeout} onChange={e => setExpectTimeout(Number(e.target.value))} min={0} />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-1">Retries</label>
          <input type="number" className="w-full rounded-lg border h-10 px-3 py-2 text-base focus:ring-2 focus:ring-primary focus:border-primary transition" value={retries} onChange={e => setRetries(Number(e.target.value))} min={0} />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-1">Workers</label>
          <input type="number" className="w-full rounded-lg border h-10 px-3 py-2 text-base focus:ring-2 focus:ring-primary focus:border-primary transition" value={workers} onChange={e => setWorkers(Number(e.target.value))} min={1} />
        </div>
        </div>
      </div>
      {/* Row 3: Viewport Width, Viewport Height */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Viewport Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 gap-y-4">
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-1">Viewport Width</label>
          <input type="number" className="w-full rounded-lg border h-10 px-3 py-2 text-base focus:ring-2 focus:ring-primary focus:border-primary transition" value={viewportWidth} onChange={e => setViewportWidth(Number(e.target.value))} min={0} />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-800 mb-1">Viewport Height</label>
          <input type="number" className="w-full rounded-lg border h-10 px-3 py-2 text-base focus:ring-2 focus:ring-primary focus:border-primary transition" value={viewportHeight} onChange={e => setViewportHeight(Number(e.target.value))} min={0} />
        </div>
        </div>
      </div>
      {/* Row 4: Fully Parallel, Headless Mode, Screenshot, Video */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Test Behavior Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 gap-y-4 w-full">
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-1">Fully Parallel</label>
          <button type="button" aria-pressed={fullyParallel} onClick={() => setFullyParallel(v => !v)} className={`w-10 h-6 rounded-full transition-colors duration-200 ${fullyParallel ? 'bg-primary' : 'bg-gray-300'} relative focus:outline-none`}>
            <span className={`absolute left-0 top-0 w-6 h-6 bg-white rounded-full shadow transform transition-transform duration-200 ${fullyParallel ? 'translate-x-4' : ''}`}></span>
          </button>
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-1">Headless Mode</label>
          <button type="button" aria-pressed={headless} onClick={() => setHeadless(v => !v)} className={`w-10 h-6 rounded-full transition-colors duration-200 ${headless ? 'bg-primary' : 'bg-gray-300'} relative focus:outline-none`}>
            <span className={`absolute left-0 top-0 w-6 h-6 bg-white rounded-full shadow transform transition-transform duration-200 ${headless ? 'translate-x-4' : ''}`}></span>
          </button>
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-1">Screenshot</label>
          <select className="w-full rounded-lg border h-10 px-3 py-2 text-base focus:ring-2 focus:ring-primary focus:border-primary transition" value={screenshot} onChange={e => setScreenshot(e.target.value)}>
            <option value="off">Off</option>
            <option value="on">On</option>
            <option value="only-on-failure">Only on failure</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-600 mb-1">Video</label>
          <select className="w-full rounded-lg border h-10 px-3 py-2 text-base focus:ring-2 focus:ring-primary focus:border-primary transition" value={video} onChange={e => setVideo(e.target.value)}>
            <option value="off">Off</option>
            <option value="on">On</option>
            <option value="retain-on-failure">Retain on failure</option>
          </select>
        </div>
        </div>
      </div>
      <div className="flex gap-4 mt-8">
        <button type="submit" className="flex-1 px-6 py-2 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition">
          Save Configuration
        </button>
        <button 
          type="button" 
          onClick={handleRegenerateConfig}
          disabled={regenerating}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-50"
        >
          {regenerating ? 'Regenerating...' : 'Regenerate Config'}
        </button>
      </div>
      {saved && <div className="text-green-600 mt-2 text-center">Configuration saved!</div>}
      {regenerating && <div className="text-blue-600 mt-2 text-center">Regenerating Playwright configuration...</div>}
    </form>
  )
}