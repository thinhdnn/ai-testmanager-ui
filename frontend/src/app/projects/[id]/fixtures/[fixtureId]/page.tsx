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

interface FixtureDetail {
  id: string
  name: string
  type: 'data' | 'config' | 'mock'
  status: 'active' | 'inactive' | 'draft'
  playwright_script: string
  created_at: string
  updated_at: string
  created_by: string
  updated_by: string
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
  created_at: string
  updated_at: string
  created_by: string
  updated_by: string
}

interface Version {
  id: string
  version: string
  name: string
  playwright_script: string
  created_at: string
  updated_at: string
}

export default function FixtureDetailPage() {
  const params = useParams<{ id: string; fixtureId: string }>()
  const router = useRouter()
  const { id: projectId, fixtureId } = params
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [fixture, setFixture] = useState<FixtureDetail | null>(null)
  const [steps, setSteps] = useState<Step[]>([])
  const [versions, setVersions] = useState<Version[]>([])

  useEffect(() => {
    if (!fixtureId) return
    
    const fetchFixtureData = async () => {
      setLoading(true)
      setError(null)
      
      try {
        const [fixtureData, stepsData, versionsData] = await Promise.all([
          apiClient(`/fixtures/${fixtureId}`),
          apiClient(`/steps/fixtures/${fixtureId}/steps`),
          apiClient(`/fixtures/${fixtureId}/versions`)
        ])
        
        if (!fixtureData) {
          notFound()
          return
        }
        
        setFixture(fixtureData)
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
    
    fetchFixtureData()
  }, [fixtureId])

  if (loading) {
    return <div className="p-8">Loading fixture...</div>
  }
  if (error) {
    return <div className="p-8 text-red-600">{error}</div>
  }
  if (!fixture) {
    return notFound()
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case "data":
        return "bg-blue-500/10 text-blue-500"
      case "config":
        return "bg-purple-500/10 text-purple-500"
      case "mock":
        return "bg-orange-500/10 text-orange-500"
      default:
        return "bg-gray-500/10 text-gray-500"
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-emerald-500/10 text-emerald-500"
      case "inactive":
        return "bg-red-500/10 text-red-500"
      case "draft":
        return "bg-amber-500/10 text-amber-500"
      default:
        return "bg-gray-500/10 text-gray-500"
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <AppLayout title={fixture.name}>
      <div className="container mx-auto p-6 space-y-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{fixture.name}</h1>
              <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                <Badge className={getTypeColor(fixture.type)} variant="secondary">
                  {fixture.type.charAt(0).toUpperCase() + fixture.type.slice(1)}
                </Badge>
                <Badge className={getStatusColor(fixture.status)} variant="secondary">
                  {fixture.status.charAt(0).toUpperCase() + fixture.status.slice(1)}
                </Badge>
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  {fixture.created_by || "Unknown"}
                </span>
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {formatDate(fixture.updated_at || fixture.created_at)}
                </span>
              </div>
            </div>
          </div>
        </div>

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
              value="versions" 
              className="data-[state=active]:bg-white dark:data-[state=active]:bg-gray-800 data-[state=active]:shadow-sm rounded-lg transition-all duration-200 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
              </svg>
              Versions
            </TabsTrigger>
          </TabsList>

          <TabsContent value="details" className="space-y-4 mt-0">
            <Card className="border-0 shadow-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900/20 rounded-md flex items-center justify-center">
                    <svg className="w-3 h-3 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  Fixture Details
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Playwright Script</h3>
                    <pre className="text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap">{fixture.playwright_script}</pre>
                  </div>
                </div>
              </CardContent>
            </Card>
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
                  Fixture Steps
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
                      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">No Fixture Steps</h3>
                      <p className="text-gray-500 dark:text-gray-400">This fixture has no defined steps.</p>
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
                  <div className="w-6 h-6 bg-purple-100 dark:bg-purple-900/20 rounded-md flex items-center justify-center">
                    <svg className="w-3 h-3 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                    </svg>
                  </div>
                  Version History
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {versions.length > 0 ? (
                    versions.map((version, index) => (
                      <div key={version.id} className="group p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-all duration-200 hover:border-purple-300 dark:hover:border-purple-600">
                        <div className="flex items-start gap-4">
                          <div className="flex-shrink-0 w-8 h-8 bg-purple-100 dark:bg-purple-900/20 rounded-full flex items-center justify-center">
                            <span className="text-sm font-semibold text-purple-600 dark:text-purple-400">{version.version}</span>
                          </div>
                          <div className="flex-1 space-y-2">
                            <div className="flex items-center justify-between">
                              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                {version.name}
                              </h4>
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {formatDate(version.created_at)}
                              </span>
                            </div>
                            
                            {version.playwright_script && (
                              <div className="p-2 bg-gray-900 dark:bg-gray-950 rounded-md">
                                <label className="text-xs font-medium text-gray-400 uppercase tracking-wide">Playwright Script</label>
                                <pre className="text-xs text-gray-100 mt-1 overflow-x-auto">{version.playwright_script}</pre>
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
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                        </svg>
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-1">No Version History</h3>
                      <p className="text-gray-500 dark:text-gray-400">This fixture has no version history.</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  )
} 