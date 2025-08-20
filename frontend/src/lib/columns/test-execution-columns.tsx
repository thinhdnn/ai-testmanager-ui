"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import Link from "next/link"

// Define the TestExecution type
export type TestExecution = {
  id: string
  testCase: string
  status: "passed" | "failed" | "skipped" | "running"
  startTime: string
  duration: string
  executor: string
  environment: string
}

// Create columns definition
export const columns: ColumnDef<TestExecution>[] = [
  {
    accessorKey: "id",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Execution ID
        </Button>
      )
    },
    cell: ({ row }) => {
      const execution = row.original
      const shortId = (id: string) => {
        if (!id) return "";
        return id.length > 13 ? `${id.slice(0, 8)}…${id.slice(-4)}` : id
      }
      const url = `/executions/${execution.id}`
      return (
        <Link
          href={url}
          className="font-mono text-sm text-foreground no-underline hover:text-primary cursor-pointer"
          title={execution.id}
        >
          {shortId(execution.id)}
        </Link>
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
          case "skipped":
            return "bg-amber-500/10 text-amber-500"
          case "running":
            return "bg-blue-500/10 text-blue-500"
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
    accessorKey: "startTime",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Start Time
        </Button>
      )
    },
  },
  {
    accessorKey: "duration",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Duration
        </Button>
      )
    },
  },
  {
    accessorKey: "executor",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Executor
        </Button>
      )
    },
  },
] 