"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { notFound } from "next/navigation"
import { AppLayout } from "@/components/app-layout"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { apiClient } from "@/lib/apiClient"

interface TestCaseDetail {
  id: string
  name: string
  project_id: string
  order: number
  status: string
  version: string
  is_manual: boolean
  tags: string
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
  created_at: string
  updated_at: string
  created_by: string
  updated_by: string
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

  useEffect(() => {
    if (!testCaseId) return
    
    const fetchTestCaseData = async () => {
      setLoading(true)
      setError(null)
      
      try {
        const [testCaseData, executionsData, statsData, stepsData] = await Promise.all([
          apiClient(`/test-cases/${testCaseId}`),
          apiClient(`/test-results/test-cases/${testCaseId}/executions?limit=20`),
          apiClient(`/test-results/test-cases/${testCaseId}/stats`),
          apiClient(`/steps/test-cases/${testCaseId}/steps`)
        ])
        
        if (!testCaseData) {
          notFound()
          return
        }
        
        setTestCase(testCaseData)
        setExecutions(executionsData)
        setStats(statsData)
        setSteps(stepsData)
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
    
    fetchTestCaseData()
  }, [testCaseId])

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
            <span>Test Cases</span>
            <span>/</span>
            <span className="text-gray-900 dark:text-gray-100 font-medium">{testCase.name}</span>
          </div>

          {/* Enhanced Header */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{testCase.name}</h1>
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
                <Badge className={`${getStatusColor(testCase.status)} px-3 py-1.5 text-sm font-medium flex items-center gap-2`} variant="secondary">
                  {getStatusIcon(testCase.status)}
                  {testCase.status.charAt(0).toUpperCase() + testCase.status.slice(1)}
                </Badge>
                <Badge variant="outline" className="px-3 py-1.5 text-sm">
                  {testCase.is_manual ? "Manual" : "Automated"}
                </Badge>
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
            <Tabs defaultValue="details" className="w-full">
              <TabsList className="w-full bg-gray-50 dark:bg-gray-700/50 rounded-t-xl p-1 grid grid-cols-3">
                <TabsTrigger 
                  value="details" 
                  className="data-[state=active]:bg-white dark:data-[state=active]:bg-gray-800 data-[state=active]:shadow-sm rounded-lg transition-all duration-200 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Details
                </TabsTrigger>
                <TabsTrigger 
                  value="steps" 
                  className="data-[state=active]:bg-white dark:data-[state=active]:bg-gray-800 data-[state=active]:shadow-sm rounded-lg transition-all duration-200 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  Steps
                </TabsTrigger>
                <TabsTrigger 
                  value="executions" 
                  className="data-[state=active]:bg-white dark:data-[state=active]:bg-gray-800 data-[state=active]:shadow-sm rounded-lg transition-all duration-200 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  History
                </TabsTrigger>
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
                            {typeof testCase.tags === 'string' && testCase.tags.length > 0 ? testCase.tags.split(',').map((tag, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {tag.trim()}
                              </Badge>
                            )) : <span className="text-sm text-gray-500 dark:text-gray-400">No tags</span>}
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
                  <Card className="border-0 shadow-md">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-lg">
                        <div className="w-6 h-6 bg-indigo-100 dark:bg-indigo-900/20 rounded-md flex items-center justify-center">
                          <svg className="w-3 h-3 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                        Test Steps
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
                                <div className="flex-1 space-y-2">
                                  <div className="flex items-center justify-between">
                                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                      {step.action.charAt(0).toUpperCase() + step.action.slice(1)}
                                    </h4>
                                    {step.disabled && (
                                      <Badge variant="outline" className="text-xs text-red-600 border-red-300">Disabled</Badge>
                                    )}
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
                                  
                                  {step.playwright_script && (
                                    <div className="p-2 bg-gray-900 dark:bg-gray-950 rounded-md">
                                      <label className="text-xs font-medium text-gray-400 uppercase tracking-wide">Playwright Script</label>
                                      <pre className="text-xs text-gray-100 mt-1 overflow-x-auto">{step.playwright_script}</pre>
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
              </div>
            </Tabs>
          </div>
        </div>
      </div>
    </AppLayout>
  )
} 