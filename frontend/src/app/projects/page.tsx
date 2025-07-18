"use client"

import { useEffect, useState } from "react"
import { ProjectCard } from "@/components/ui/project-card"
import { AppLayout } from "@/components/app-layout"
import { Button } from "@/components/ui/button"
import { CreateProjectModal } from "@/components/create-project-modal"
import { apiClient } from "@/lib/apiClient"

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
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)

    const fetchProjects = async () => {
      setLoading(true)
      try {
      // Use the new optimized endpoint that returns projects with stats in one call
      const projectsWithStats = await apiClient("/projects/with-stats")
      
            // Map backend fields to frontend fields
      const mappedProjects = projectsWithStats.map((proj: any) => ({
              id: proj.id,
              title: proj.name,
              description: proj.description || "",
        status: "active" as const, // Default to active, adjust if backend provides status
              progress: 0, // No progress field in backend, set to 0 or calculate if possible
        testCases: proj.test_cases_count || 0,
        passRate: proj.success_rate || 0,
      }))
      
      setProjects(mappedProjects)
      } catch {
        // Handle error (could show a message)
        setProjects([])
      } finally {
        setLoading(false)
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
      <div className="container mx-auto p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Projects</h1>
          <Button 
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg transition-all duration-200 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create New Project
          </Button>
        </div>
        
        {loading ? (
          <div>Loading projects...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <ProjectCard key={project.id} {...project} />
            ))}
          </div>
        )}

        <CreateProjectModal
          open={showCreateModal}
          onOpenChange={setShowCreateModal}
          onProjectCreated={handleProjectCreated}
        />
      </div>
    </AppLayout>
  )
} 