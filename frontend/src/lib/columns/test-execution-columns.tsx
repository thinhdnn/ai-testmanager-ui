"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import Link from "next/link"

// Simple friendly date formatter: shows relative time for <24h, else local date/time
const formatFriendlyDate = (isoString: string) => {
  if (!isoString) return "-"
  const date = new Date(isoString)
  if (isNaN(date.getTime())) return "-"
  const now = new Date()
  const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
  if (diffSeconds < 60) return `${diffSeconds}s ago`
  const diffMinutes = Math.floor(diffSeconds / 60)
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  return date.toLocaleString()
}

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
    cell: ({ row }) => {
      const iso = row.getValue("startTime") as string
      const friendly = formatFriendlyDate(iso)
      const title = iso ? new Date(iso).toLocaleString() : ""
      return (
        <span title={title} className="text-foreground">
          {friendly}
        </span>
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