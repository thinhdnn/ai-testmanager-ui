"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useParams, useRouter } from "next/navigation"

export type TestCase = {
  id: string
  title: string
  status: "passed" | "failed" | "blocked" | "not-run" | "pending"
  author: string
  lastRun: string
  tag: string[]
}

export const columns: ColumnDef<TestCase>[] = [
  {
    accessorKey: "title",
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
      const title = row.getValue("title") as string
      const testCase = row.original
      
      return (
        <TestCaseNameCell title={title} testCase={testCase} />
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
      const status = row.getValue("status") as string
      const getStatusColor = (status: string) => {
        switch (status) {
          case "passed":
            return "bg-emerald-500/10 text-emerald-500"
          case "failed":
            return "bg-red-500/10 text-red-500"
          case "blocked":
            return "bg-amber-500/10 text-amber-500"
          case "not-run":
          case "pending":
            return "bg-gray-500/10 text-gray-500"
          default:
            return "bg-gray-500/10 text-gray-500"
        }
      }
      return (
        <Badge className={getStatusColor(status)} variant="secondary">
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </Badge>
      )
    },
  },
  {
    accessorKey: "tag",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Tag
        </Button>
      )
    },
    cell: ({ row }) => {
      const tags = row.getValue("tag") as string[] | undefined;
      return (
        <div className="flex flex-wrap gap-1">
          {Array.isArray(tags) && tags.length > 0
            ? tags.map((tag, idx) => (
                <Badge key={tag + idx} variant="outline">
                  {tag.charAt(0).toUpperCase() + tag.slice(1)}
                </Badge>
              ))
            : null}
        </div>
      )
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
  {
    accessorKey: "lastRun",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Last Run
        </Button>
      )
    },
  },
] 

// Separate component for test case name cell with navigation
function TestCaseNameCell({ title, testCase }: { title: string; testCase: TestCase }) {
  const router = useRouter()
  const params = useParams<{ id: string }>()
  const projectId = params?.id

  const handleClick = () => {
    if (projectId) {
      router.push(`/projects/${projectId}/test-cases/${testCase.id}`)
    }
  }

  return (
    <button
      onClick={handleClick}
      className="text-left hover:text-blue-600 hover:underline cursor-pointer transition-colors"
    >
      {title}
    </button>
  )
} 