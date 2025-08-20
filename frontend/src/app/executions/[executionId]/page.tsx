"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { apiClient } from "@/lib/apiClient"
import { AppLayout } from "@/components/app-layout"
import { ArrowLeft, Clock, User, Monitor, Play, CheckCircle, XCircle, AlertTriangle, SkipForward, FileText, Settings, BarChart3, Copy, Check } from "lucide-react"

interface TestCaseExecution {
  id: string
  test_result_id: string
  test_case_id: string
  status: string
  duration: number | null
  error_message: string | null
  output: string | null
  start_time: string | null
  end_time: string | null
  retries: number
  created_at: string
  updated_at: string
}

interface TestResultHistory {
  id: string
  project_id: string
  name: string
  test_result_file_name: string | null
  success: boolean
  status: string
  execution_time: number | null
  output: string | null
  error_message: string | null
  result_data: string | null
  created_by: string | null
  last_run_by: string | null
  browser: string | null
  video_url: string | null
  created_at: string
  updated_at: string
}

interface TestCase {
  id: string
  name: string
  description: string | null
  status: string
  created_by: string
  updated_by: string
  last_run_by: string
}

export default function ExecutionDetailPage() {
  const params = useParams<{ executionId: string }>()
  const router = useRouter()
  const [execution, setExecution] = useState<TestCaseExecution | null>(null)
  const [testResult, setTestResult] = useState<TestResultHistory | null>(null)
  const [testCase, setTestCase] = useState<TestCase | null>(null)
  const [relatedExecutions, setRelatedExecutions] = useState<Array<TestCaseExecution & { test_case_name?: string }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [outputExpanded, setOutputExpanded] = useState(false)
  const [errorExpanded, setErrorExpanded] = useState(false)
  const [outputCopied, setOutputCopied] = useState(false)
  const [errorCopied, setErrorCopied] = useState(false)

  const copyToClipboard = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text)
      console.log(`${type} copied to clipboard`)
      
      // Set copied state based on type
      if (type === 'Output') {
        setOutputCopied(true)
        setTimeout(() => setOutputCopied(false), 2000)
      } else if (type === 'Error') {
        setErrorCopied(true)
        setTimeout(() => setErrorCopied(false), 2000)
      }
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
  }

  useEffect(() => {
    if (!params.executionId) return

    const fetchExecutionData = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch execution details
        const executionData = await apiClient(`/test-results/executions/${params.executionId}`)
        console.log("Execution data:", executionData)
        console.log("Duration from API:", executionData?.duration, "type:", typeof executionData?.duration)
        setExecution(executionData)

        if (executionData) {
          // Fetch test result details
          const resultData = await apiClient(`/test-results/${executionData.test_result_id}`)
          setTestResult(resultData)

          // Fetch test case details
          const testCaseData = await apiClient(`/test-cases/${executionData.test_case_id}`)
          setTestCase(testCaseData)

                      // Fetch all executions under the same test run (worklist)
            try {
              const execList: TestCaseExecution[] = await apiClient(`/test-results/${executionData.test_result_id}/executions`)
              console.log("Related executions:", execList)
              console.log("Duration values:", execList.map(e => ({ id: e.id, duration: e.duration, type: typeof e.duration })))
              
              // Fetch names for involved test cases
              const uniqueTestCaseIds = Array.from(new Set(execList.map(e => e.test_case_id)))
              const nameMap: Record<string, string> = {}
              await Promise.all(
                uniqueTestCaseIds.map(async (tcId) => {
                  try {
                    const tc = await apiClient(`/test-cases/${tcId}`)
                    nameMap[tcId] = tc?.name || tcId
                  } catch {
                    nameMap[tcId] = tcId
                  }
                })
              )
              setRelatedExecutions(execList.map(e => ({ ...e, test_case_name: nameMap[e.test_case_id] })))
            } catch (e) {
              // ignore silently; still show page without worklist
            }
        }
      } catch (err) {
        console.error("Error fetching execution data:", err)
        setError("Failed to load execution details")
      } finally {
        setLoading(false)
      }
    }

    fetchExecutionData()
  }, [params.executionId])

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "passed":
      case "success":
        return <CheckCircle className="h-4 w-4" />
      case "failed":
      case "failure":
        return <XCircle className="h-4 w-4" />
      case "skipped":
        return <SkipForward className="h-4 w-4" />
      case "running":
        return <Play className="h-4 w-4" />
      default:
        return <AlertTriangle className="h-4 w-4" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "passed":
      case "success":
        return "bg-emerald-500/10 text-emerald-500 border-emerald-200 dark:border-emerald-800"
      case "failed":
      case "failure":
        return "bg-red-500/10 text-red-500 border-red-200 dark:border-red-800"
      case "skipped":
        return "bg-amber-500/10 text-amber-500 border-amber-200 dark:border-amber-800"
      case "running":
        return "bg-blue-500/10 text-blue-500 border-blue-200 dark:border-blue-800"
      default:
        return "bg-gray-500/10 text-gray-500 border-gray-200 dark:border-gray-800"
    }
  }

  const formatDuration = (duration: number | null) => {
    if (!duration) return "N/A"
    // Debug logging
    console.log("formatDuration input:", duration, "type:", typeof duration)
    
    // Handle both number and string inputs
    const durationNum = typeof duration === 'string' ? parseFloat(duration) : duration
    if (isNaN(durationNum)) return "N/A"
    
    const seconds = Math.floor(durationNum / 1000)
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`
    }
    return `${remainingSeconds}s`
  }

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return "N/A"
    return new Date(dateString).toLocaleString()
  }

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading execution details...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !execution) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Execution Not Found</h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">{error || "The requested execution could not be found."}</p>
          <Button onClick={() => window.history.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Go Back
          </Button>
        </div>
      </div>
    )
  }

  const shortId = (id: string | null | undefined) => {
    if (!id) return ""
    return id.length > 13 ? `${id.slice(0, 8)}…${id.slice(-4)}` : id
  }

  return (
    <AppLayout title={`Execution - ${shortId(execution.id)}`}>
      <div className="space-y-6">
        {/* Breadcrumb Navigation */}
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => testResult?.project_id && router.push(`/projects/${testResult.project_id}`)}
            className="hover:bg-gray-100 dark:hover:bg-gray-700 px-2 py-1 h-auto"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Project
          </Button>
          <span>/</span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => testResult?.project_id && router.push(`/projects/${testResult.project_id}?tab=executions`)}
            className="hover:bg-gray-100 dark:hover:bg-gray-700 px-2 py-1 h-auto"
          >
            Executions
          </Button>
          <span>/</span>
          <span className="text-gray-900 dark:text-gray-100 font-medium">{shortId(execution.id)}</span>
        </div>

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Execution {shortId(execution.id)}
            </h1>
          </div>
        </div>

        {/* Main Content with Sidebar Navigation */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {/* Execution Overview */}
            <Card>
              <CardHeader>
                <CardTitle>Execution Overview</CardTitle>
                <CardDescription>Key information about this test execution</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Status</p>
                    <Badge className={getStatusColor(execution.status)}>
                      {getStatusIcon(execution.status)}
                      <span className="ml-2">{execution.status}</span>
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Duration</p>
                    <p className="flex items-center text-sm">
                      <Clock className="h-4 w-4 mr-2" />
                      {formatDuration(execution.duration)}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Start Time</p>
                    <p className="text-sm">{formatDateTime(execution.start_time)}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">End Time</p>
                    <p className="text-sm">{formatDateTime(execution.end_time)}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Retries</p>
                    <p className="text-sm">{execution.retries}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Created</p>
                    <p className="text-sm">{formatDateTime(execution.created_at)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Removed Test Run Information section per request */}

            {/* Test Cases and Log */}
            <Tabs defaultValue="testcases" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="testcases">Test Cases</TabsTrigger>
                <TabsTrigger value="log">Log</TabsTrigger>
              </TabsList>
              <TabsContent value="testcases" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Test Cases</CardTitle>
                    <CardDescription>All test cases executed in this run</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {relatedExecutions.length === 0 ? (
                      <p className="text-gray-500 dark:text-gray-400 text-center py-8">No test cases found for this run</p>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-left text-gray-500 dark:text-gray-400">
                              <th className="py-2 pr-4">Name</th>
                              <th className="py-2 pr-4">Status</th>
                              <th className="py-2 pr-4">Duration</th>
                              <th className="py-2 pr-4">Started</th>
                            </tr>
                          </thead>
                          <tbody>
                            {relatedExecutions.map(e => (
                              <tr key={e.id} className="border-t border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/40">
                                <td className="py-2 pr-4">
                                  <Button variant="link" className="p-0 h-auto" onClick={() => router.push(`/projects/${testResult?.project_id}/test-cases/${e.test_case_id}`)}>
                                    {e.test_case_name || e.test_case_id}
                                  </Button>
                                </td>
                                <td className="py-2 pr-4">
                                  <Badge className={`${getStatusColor(e.status)} capitalize`} variant="secondary">
                                    {e.status}
                                  </Badge>
                                </td>
                                <td className="py-2 pr-4">
                                  {e.duration ? formatDuration(e.duration) : "-"}
                                </td>
                                <td className="py-2 pr-4">
                                  {e.start_time ? new Date(e.start_time).toLocaleString() : "-"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="log" className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Execution Log</CardTitle>
                    <CardDescription>Output and errors from this execution</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium">Output</h3>
                        <div className="flex items-center gap-2">
                          {execution.output && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => copyToClipboard(execution.output!, 'Output')}
                                className="h-6 px-2 text-xs"
                                title="Copy output to clipboard"
                                disabled={outputCopied}
                              >
                                {outputCopied ? (
                                  <>
                                    <Check className="h-3 w-3 mr-1" />
                                    Copied!
                                  </>
                                ) : (
                                  <Copy className="h-3 w-3" />
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setOutputExpanded(!outputExpanded)}
                                className="h-6 px-2 text-xs"
                              >
                                {outputExpanded ? "Collapse" : "Expand"}
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                      {execution.output ? (
                        <div className={`bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden ${outputExpanded ? '' : 'max-h-32'}`}>
                          <pre className={`p-4 text-sm overflow-x-auto whitespace-pre-wrap ${outputExpanded ? '' : 'overflow-y-hidden'}`}>
                            {execution.output}
                          </pre>
                          {!outputExpanded && (
                            <div className="bg-gradient-to-t from-gray-50 to-transparent dark:from-gray-900 dark:to-transparent h-8 flex items-center justify-center">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setOutputExpanded(true)}
                                className="h-6 px-2 text-xs"
                              >
                                Click to expand full output
                              </Button>
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="text-gray-500 dark:text-gray-400">No output available</p>
                      )}
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium">Error</h3>
                        <div className="flex items-center gap-2">
                          {execution.error_message && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => copyToClipboard(execution.error_message!, 'Error')}
                                className="h-6 px-2 text-xs"
                                title="Copy error to clipboard"
                                disabled={errorCopied}
                              >
                                {errorCopied ? (
                                  <>
                                    <Check className="h-3 w-3 mr-1" />
                                    Copied!
                                  </>
                                ) : (
                                  <Copy className="h-3 w-3" />
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setErrorExpanded(!errorExpanded)}
                                className="h-6 px-2 text-xs"
                              >
                                {errorExpanded ? "Collapse" : "Expand"}
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                      {execution.error_message ? (
                        <div className={`bg-red-50 dark:bg-red-950 rounded-lg overflow-hidden ${errorExpanded ? '' : 'max-h-32'}`}>
                          <pre className={`p-4 text-sm overflow-x-auto whitespace-pre-wrap text-red-700 dark:text-red-300 ${errorExpanded ? '' : 'overflow-y-hidden'}`}>
                            {execution.error_message}
                          </pre>
                          {!errorExpanded && (
                            <div className="bg-gradient-to-t from-red-50 to-transparent dark:from-red-950 dark:to-transparent h-8 flex items-center justify-center">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setErrorExpanded(true)}
                                className="h-6 px-2 text-xs"
                              >
                                Click to expand full error
                              </Button>
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="text-gray-500 dark:text-gray-400">No errors occurred</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Sidebar Navigation */}
          <div className="space-y-6">
            {/* Quick Navigation */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Navigation</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  variant="ghost" 
                  className="w-full justify-start"
                  onClick={() => {
                    if (testResult?.project_id) {
                      window.open(`/projects/${testResult.project_id}`, '_blank')
                    }
                  }}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Project Details
                </Button>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start"
                  onClick={() => {
                    if (execution.test_case_id) {
                      window.open(`/projects/${testResult?.project_id}/test-cases/${execution.test_case_id}`, '_blank')
                    }
                  }}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Test Case Details
                </Button>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start"
                  onClick={() => {
                    if (testResult?.project_id) {
                      window.open(`/projects/${testResult.project_id}?tab=executions`, '_blank')
                    }
                  }}
                >
                  <BarChart3 className="h-4 w-4 mr-2" />
                  All Executions
                </Button>
              </CardContent>
            </Card>

            {/* Test Case Information removed per request */}

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full" variant="outline">
                  <Play className="h-4 w-4 mr-2" />
                  Re-run Test
                </Button>
                <Button className="w-full" variant="outline">
                  <Monitor className="h-4 w-4 mr-2" />
                  View in Browser
                </Button>
                {testResult?.video_url && (
                  <Button className="w-full" variant="outline">
                    <Play className="h-4 w-4 mr-2" />
                    Watch Recording
                  </Button>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
