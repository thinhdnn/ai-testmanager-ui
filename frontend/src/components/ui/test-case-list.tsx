"use client"

import { useState } from "react"
import { DataTable } from "@/components/ui/data-table"
import { columns } from "@/lib/columns/test-case-columns"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import type { TestCase } from "@/lib/columns/test-case-columns"

interface TestCaseListProps {
  data: TestCase[]
}

export function TestCaseList({ data }: TestCaseListProps) {
  const [status, setStatus] = useState("")
  const [author, setAuthor] = useState("")
  const [tag, setTag] = useState("")
  const [search, setSearch] = useState("")

  // Extract unique options from data
  const statusOptions = Array.from(new Set(data.map(tc => tc.status)))
  const authorOptions = Array.from(new Set(data.map(tc => tc.author)))
  const tagOptions = Array.from(new Set(data.flatMap(tc => tc.tag)))
  

  // Filtered data
  const filtered = data.filter(tc =>
    (status ? tc.status === status : true) &&
    (author ? tc.author === author : true) &&
    (tag ? (Array.isArray(tc.tag) ? tc.tag.includes(tag) : tc.tag === tag) : true) &&
    (search ? tc.title.toLowerCase().includes(search.toLowerCase()) : true)
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 pb-2 items-center">
        <Input
          className="max-w-xs h-9 border rounded px-2 py-1 text-sm"
          placeholder="Search test cases..."
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
          value={author}
          onChange={e => setAuthor(e.target.value)}
        >
          <option value="">All Author</option>
          {authorOptions.filter(Boolean).map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
        <select
          className="max-w-xs h-9 border rounded px-2 py-1 text-sm"
          value={tag}
          onChange={e => setTag(e.target.value)}
        >
          <option value="">All Tag</option>
          {tagOptions.filter(Boolean).map(opt => (
            <option key={opt} value={opt}>{opt.charAt(0).toUpperCase() + opt.slice(1)}</option>
          ))}
        </select>
        <Button variant="outline" className="h-9 px-3 text-sm" onClick={() => { setStatus(""); setAuthor(""); setTag(""); setSearch("") }}>Clear</Button>
      </div>
      <DataTable 
        columns={columns} 
        data={filtered} 
      />
    </div>
  )
} 