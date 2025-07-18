"use client"

import { useState } from "react"
import { DataTable } from "@/components/ui/data-table"
import { columns } from "@/lib/columns/test-execution-columns"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import type { TestExecution } from "@/lib/columns/test-execution-columns"

interface TestExecutionListProps {
  data: TestExecution[]
}

export function TestExecutionList({ data }: TestExecutionListProps) {
  const [status, setStatus] = useState("")
  const [executor, setExecutor] = useState("")
  const [search, setSearch] = useState("")

  // Extract unique options from data
  const statusOptions = Array.from(new Set(data.map(e => e.status)))
  const executorOptions = Array.from(new Set(data.map(e => e.executor)))

  // Filtered data
  const filtered = data.filter(e =>
    (status ? e.status === status : true) &&
    (executor ? e.executor === executor : true) &&
    (search ? e.testCase.toLowerCase().includes(search.toLowerCase()) : true)
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 pb-2 items-center">
        <Input
          className="max-w-xs h-9 border rounded px-2 py-1 text-sm"
          placeholder="Search name..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select
          className="max-w-xs h-9 border rounded px-2 py-1 text-sm"
          value={status}
          onChange={e => setStatus(e.target.value)}
        >
          <option value="">All Status</option>
          {statusOptions.filter(Boolean).map(opt => (
            <option key={opt} value={opt}>{opt.charAt(0).toUpperCase() + opt.slice(1)}</option>
          ))}
        </select>
        <select
          className="max-w-xs h-9 border rounded px-2 py-1 text-sm"
          value={executor}
          onChange={e => setExecutor(e.target.value)}
        >
          <option value="">All Executor</option>
          {executorOptions.filter(Boolean).map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
        <Button variant="outline" className="h-9 px-3 text-sm" onClick={() => { setStatus(""); setExecutor(""); setSearch("") }}>Clear</Button>
      </div>
      <DataTable
        columns={columns}
        data={filtered}
      />
    </div>
  )
} 