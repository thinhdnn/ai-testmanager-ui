"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import Link from "next/link"

interface ProjectCardProps {
  id: string
  title: string
  description: string
  status: 'active' | 'completed' | 'on-hold'
  progress: number
  testCases: number
  passRate: number
}

export function ProjectCard({
  id,
  title,
  description,
  status,
  progress,
  testCases,
  passRate
}: ProjectCardProps) {
  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20'
      case 'completed':
        return 'bg-blue-500/10 text-blue-500 hover:bg-blue-500/20'
      case 'on-hold':
        return 'bg-amber-500/10 text-amber-500 hover:bg-amber-500/20'
      default:
        return 'bg-gray-500/10 text-gray-500 hover:bg-gray-500/20'
    }
  }

  return (
    <Link href={`/projects/${id}`} className="block">
      <Card className="hover:shadow-lg transition-shadow duration-200">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold">{title}</CardTitle>
            <Badge className={getStatusColor(status)} variant="secondary">
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </Badge>
          </div>
          <CardDescription className="line-clamp-2">{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Progress</span>
                <span className="font-medium">{progress}%</span>
              </div>
              <Progress value={progress} className="h-1" />
            </div>
            <div className="flex justify-between text-xs">
              <div>
                <p className="text-muted-foreground">Test Cases</p>
                <p className="font-medium">{testCases}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Pass Rate</p>
                <p className="font-medium">{passRate}%</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
} 