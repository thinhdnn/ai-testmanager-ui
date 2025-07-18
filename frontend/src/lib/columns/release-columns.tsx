"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export type Release = {
  id: string
  version: string
  name: string
  status: "active" | "archived" | "draft"
  date: string
  author: string
}

export const columns: ColumnDef<Release>[] = [
  {
    accessorKey: "version",
    header: ({ column }) => (
      <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Version</Button>
    ),
  },
  {
    accessorKey: "name",
    header: ({ column }) => (
      <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Name</Button>
    ),
  },
  {
    accessorKey: "status",
    header: ({ column }) => (
      <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Status</Button>
    ),
    cell: ({ row }) => {
      const status = row.getValue("status") as string
      const getStatusColor = (status: string) => {
        switch (status) {
          case "active": return "bg-emerald-500/10 text-emerald-500"
          case "archived": return "bg-gray-500/10 text-gray-500"
          case "draft": return "bg-amber-500/10 text-amber-500"
          default: return "bg-gray-500/10 text-gray-500"
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
    accessorKey: "date",
    header: ({ column }) => (
      <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Date</Button>
    ),
  },
  {
    accessorKey: "author",
    header: ({ column }) => (
      <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>Author</Button>
    ),
  },
] 