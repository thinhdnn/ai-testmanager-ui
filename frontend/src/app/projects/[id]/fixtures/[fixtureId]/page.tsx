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
import { apiClient } from "@/lib/apiClient"
import { GripVertical, ListOrdered, MoreHorizontal } from "lucide-react"

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
  author_name: string
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
  const [moveStepOpen, setMoveStepOpen] = useState(false)
  const [movingStepId, setMovingStepId] = useState<string | null>(null)
  const [targetPosition, setTargetPosition] = useState<number>(1)
  const [moving, setMoving] = useState(false)

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

      // Reload steps
      const stepsData = await apiClient(`/steps/fixtures/${fixtureId}/steps`)
      setSteps(stepsData)
      
      setMoveStepOpen(false)
    } catch (err) {
      console.error('Error moving step:', err)
      alert('Failed to move step. Please try again.')
    } finally {
      setMoving(false)
    }
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
                  {fixture.author_name || fixture.created_by || "Unknown"}
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
                  {steps.length > 0 && (
                    <Button size="icon" variant="outline" onClick={async () => {
                      try {
                        await apiClient(`/steps/fixtures/${fixtureId}/steps/auto-reorder`, {
                          method: "PATCH"
                        })
                        // Reload steps
                        const stepsData = await apiClient(`/steps/fixtures/${fixtureId}/steps`)
                        setSteps(stepsData)
                      } catch (err) {
                        console.error('Error reordering steps:', err)
                      }
                    }} title="Auto Reorder Steps" className="ml-auto">
                      <ListOrdered className="w-4 h-4" />
                    </Button>
                  )}
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
                                {step.action.charAt(0).toUpperCase() + step.action.slice(1)}
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
    </AppLayout>
  )
} 