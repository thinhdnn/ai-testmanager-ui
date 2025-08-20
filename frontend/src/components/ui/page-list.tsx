"use client"

import React from "react"
import { DataTable } from "@/components/ui/data-table"
import { columns, PageItem } from "@/lib/columns/page-columns"

export function PageList({ data }: { data: PageItem[] }) {
  return (
    <DataTable
      columns={columns}
      data={data}
      searchKey="name"
      searchPlaceholder="Filter pages by name..."
    />
  )
}


