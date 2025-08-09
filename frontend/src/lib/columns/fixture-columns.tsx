"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useParams, useRouter } from "next/navigation"

export interface Fixture {
  id: string
  name: string
  type: 'extend' | 'inline'
  status: 'active' | 'inactive' | 'draft'
  lastModified: string
  author: string
  environment: 'all' | 'development' | 'staging' | 'production'
}

function getTypeColor(type: string) {
  switch (type) {
    case "extend":
      return "bg-blue-500/10 text-blue-500"
    case "inline":
      return "bg-purple-500/10 text-purple-500"
    default:
      return "bg-gray-500/10 text-gray-500"
  }
}

function getStatusColor(status: string) {
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

// Separate component for fixture name cell with navigation
function FixtureNameCell({ name, fixture }: { name: string; fixture: Fixture }) {
  const router = useRouter()
  const params = useParams<{ id: string }>()
  const projectId = params?.id

  const handleClick = () => {
    if (projectId) {
      router.push(`/projects/${projectId}/fixtures/${fixture.id}`)
    }
  }

  return (
    <button
      onClick={handleClick}
      className="text-left hover:text-blue-600 hover:underline cursor-pointer transition-colors"
    >
      {name}
    </button>
  )
}

export const columns: ColumnDef<Fixture>[] = [
  {
    accessorKey: "name",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Name
        </Button>
      )
    },
    cell: ({ row }) => {
      const name = row.getValue("name") as string
      return <FixtureNameCell name={name} fixture={row.original} />
    },
  },
  {
    accessorKey: "type",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Type
        </Button>
      )
    },
    cell: ({ row }) => {
      const type = row.getValue("type") as Fixture['type']
      return (
        <Badge className={getTypeColor(type)} variant="secondary">
          {type.charAt(0).toUpperCase() + type.slice(1)}
        </Badge>
      )
    },
  },
  {
    accessorKey: "status",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Status
        </Button>
      )
    },
    cell: ({ row }) => {
      const status = row.getValue("status") as Fixture['status']
      return (
        <Badge className={getStatusColor(status)} variant="secondary">
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </Badge>
      )
    },
  },
  {
    accessorKey: "environment",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Environment
        </Button>
      )
    },
    cell: ({ row }) => {
      const env = row.getValue("environment") as string | undefined;
      return (
        <Badge variant="outline">
          {env ? env.charAt(0).toUpperCase() + env.slice(1) : ""}
        </Badge>
      )
    },
  },
  {
    accessorKey: "lastModified",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Last Modified
        </Button>
      )
    },
    cell: ({ row }) => {
      const date = row.getValue("lastModified") as string
      if (!date) return <div className="text-gray-500">-</div>
      
      try {
        const formattedDate = new Date(date).toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
        return <div className="text-sm text-gray-600">{formattedDate}</div>
      } catch {
        return <div className="text-gray-500">{date}</div>
      }
    },
  },
  {
    accessorKey: "author",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Author
        </Button>
      )
    },
  },
] 