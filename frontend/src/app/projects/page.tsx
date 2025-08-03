"use client"

import { useEffect, useState } from "react"
import { ProjectCard } from "@/components/ui/project-card"
import { AppLayout } from "@/components/app-layout"
import { Button } from "@/components/ui/button"
import { CreateProjectModal } from "@/components/create-project-modal"
import { PageContent } from "@/components/page-content"
import { Plus } from "lucide-react"
import { useApi } from "@/hooks/useApi"

// Define the Project type expected by the UI
interface Project {
  id: string
  title: string
  description: string
  status: 'active' | 'completed' | 'on-hold'
  progress: number
  testCases: number
  passRate: number
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)

  const { callApi, loading, error } = useApi({
    onSuccess: (data) => {
      // Map backend fields to frontend fields
      const mappedProjects = data.map((proj: any) => ({
        id: proj.id,
        title: proj.name,
        description: proj.description || "",
        status: "active" as const, // Default to active, adjust if backend provides status
        progress: 0, // No progress field in backend, set to 0 or calculate if possible
        testCases: proj.test_cases_count || 0,
        passRate: proj.success_rate || 0,
      }))
      setProjects(mappedProjects)
    },
    onError: (error) => {
      console.error('Failed to fetch projects:', error)
      setProjects([])
    },
    on401: () => {
      // 401 is handled by apiClient redirect, just clear projects
      setProjects([])
    }
  })

  const fetchProjects = async () => {
    try {
      await callApi("/projects/with-stats")
    } catch {
      // Error is handled by useApi hook
    }
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  const handleProjectCreated = () => {
    // Refresh the projects list after creating a new project
    fetchProjects()
  }

  return (
    <AppLayout title="Projects">
      <PageContent 
        loading={loading}
        error={error}
        maxWidth="full"
      >
        {/* Description + Icon Button Row */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
          <div className="text-muted-foreground text-base">
            Manage your projects, create new ones, and collaborate with your team.
          </div>
          <Button
            variant="outline"
            className="group flex items-center gap-2 px-3 py-2"
            onClick={() => setShowCreateModal(true)}
          >
            <Plus className="h-5 w-5" />
            <span className="hidden md:inline group-hover:inline transition-all duration-200">Create New Project</span>
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {projects.map((project) => (
            <ProjectCard key={project.id} {...project} />
          ))}
        </div>

        <CreateProjectModal
          open={showCreateModal}
          onOpenChange={setShowCreateModal}
          onProjectCreated={handleProjectCreated}
        />
      </PageContent>
    </AppLayout>
  )
} 