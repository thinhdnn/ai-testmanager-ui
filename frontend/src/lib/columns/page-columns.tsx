"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Button } from "@/components/ui/button"
import { useParams, useRouter } from "next/navigation"

export interface PageItem {
  id: string
  name: string
  author?: string
  lastModified?: string
}

export const columns: ColumnDef<PageItem>[] = [
  {
    accessorKey: "name",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Page Name
        </Button>
      )
    },
    cell: ({ row }) => {
      const name = row.getValue("name") as string
      const router = useRouter()
      const params = useParams<{ id: string }>()
      const projectId = params?.id
      const handleClick = () => {
        if (projectId) {
          router.push(`/projects/${projectId}/pages/${row.original.id}`)
        }
      }
      return (
        <button onClick={handleClick} className="text-left hover:text-blue-600 hover:underline cursor-pointer transition-colors">
          {name}
        </button>
      )
    }
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
]
