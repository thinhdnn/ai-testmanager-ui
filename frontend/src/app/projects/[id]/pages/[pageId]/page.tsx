"use client"

import React, { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { AppLayout } from "@/components/app-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { apiClient } from "@/lib/apiClient"

interface PageLocatorItem {
  id: string
  locator_key: string
  locator_value: string
  created_at?: string
  updated_at?: string
}

export default function PageDetail() {
  const params = useParams<{ id: string; pageId: string }>()
  const router = useRouter()
  const projectId = params?.id
  const pageId = params?.pageId

  const [locators, setLocators] = useState<PageLocatorItem[]>([])
  const [pageName, setPageName] = useState("")
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newKey, setNewKey] = useState("")
  const [newVal, setNewVal] = useState("")
  const [filter, setFilter] = useState("")
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editKey, setEditKey] = useState("")
  const [editVal, setEditVal] = useState("")
  const [pageAuthor, setPageAuthor] = useState<string | undefined>(undefined)
  const [pageUpdatedAt, setPageUpdatedAt] = useState<string | undefined>(undefined)

  useEffect(() => {
    if (!pageId) return
    setLoading(true)
    Promise.all([
      apiClient(`/pages/${pageId}`),
      apiClient(`/pages/${pageId}/locators`),
    ])
      .then(([page, locs]) => {
        setPageName(page?.name || "")
        setPageAuthor(page?.author_name || page?.created_by)
        setPageUpdatedAt(page?.updated_at || page?.created_at)
        setLocators(locs as any[])
      })
      .finally(() => setLoading(false))
  }, [pageId])

  async function addLocator(e: React.FormEvent) {
    e.preventDefault()
    if (!pageId || !newKey.trim() || !newVal.trim()) return
    setCreating(true)
    try {
      await apiClient(`/pages/${pageId}/locators`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ page_id: pageId, locator_key: newKey, locator_value: newVal }),
      })
      setNewKey("")
      setNewVal("")
      setCreateOpen(false)
      const refreshed = await apiClient(`/pages/${pageId}/locators`)
      setLocators(refreshed as any[])
    } finally {
      setCreating(false)
    }
  }

  async function removeLocator(locatorId: string) {
    if (!pageId) return
    await apiClient(`/pages/${pageId}/locators/${locatorId}`, { method: "DELETE" })
    const refreshed = await apiClient(`/pages/${pageId}/locators`)
    setLocators(refreshed as any[])
    setDeletingId(null)
  }

  function startEdit(loc: PageLocatorItem) {
    setEditingId(loc.id)
    setEditKey(loc.locator_key)
    setEditVal(loc.locator_value)
  }

  function cancelEdit() {
    setEditingId(null)
    setEditKey("")
    setEditVal("")
  }

  async function saveEdit(locatorId: string) {
    if (!pageId) return
    await apiClient(`/pages/${pageId}/locators/${locatorId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ locator_key: editKey, locator_value: editVal })
    })
    const refreshed = await apiClient(`/pages/${pageId}/locators`)
    setLocators(refreshed as any[])
    cancelEdit()
  }

  async function copyToClipboard(text: string) {
    try {
      await navigator.clipboard.writeText(text)
    } catch {}
  }

  const filtered = locators.filter(loc => {
    if (!filter.trim()) return true
    const q = filter.toLowerCase()
    return loc.locator_key.toLowerCase().includes(q) || loc.locator_value.toLowerCase().includes(q)
  })

  if (loading) {
    return <div className="p-8">Loading page...</div>
  }

  return (
    <AppLayout title={pageName || "Page Detail"}>
      <div className="space-y-6">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push(`/projects/${projectId}`)}
            className="hover:bg-gray-100 px-2 py-1 h-auto"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Project
          </Button>
          <span>/</span>
          <span>Pages</span>
          <span>/</span>
          <span className="text-gray-900 font-medium truncate max-w-[40ch]" title={pageName}>{pageName}</span>
        </div>

        {/* Page Header */}
        <div className="bg-white rounded-xl shadow border p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h1 className="text-2xl font-bold text-gray-900">{pageName || "Untitled Page"}</h1>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                {pageAuthor && (
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    {pageAuthor}
                  </span>
                )}
                {pageUpdatedAt && (
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {new Date(pageUpdatedAt).toLocaleString()}
                  </span>
                )}
                <Badge variant="outline">{locators.length} locators</Badge>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold">Locators</h2>
            <Badge variant="secondary">{locators.length} items</Badge>
          </div>
          <div className="flex items-center gap-3">
            <Input
              placeholder="Search key or value..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-[240px]"
            />
            <Button onClick={() => setCreateOpen(true)}>New Locator</Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">Manage selectors used on this page</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="rounded-md border overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/30">
                    <th className="text-left p-3 font-medium">Key</th>
                    <th className="text-left p-3 font-medium">Value</th>
                    <th className="text-right p-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((loc) => (
                    <tr key={loc.id} className="border-b">
                      <td className="p-3 align-top w-[30%]">
                        {editingId === loc.id ? (
                          <Input value={editKey} onChange={(e) => setEditKey(e.target.value)} />
                        ) : (
                          <code className="text-xs bg-muted px-2 py-1 rounded">{loc.locator_key}</code>
                        )}
                      </td>
                      <td className="p-3">
                        {editingId === loc.id ? (
                          <Input value={editVal} onChange={(e) => setEditVal(e.target.value)} />
                        ) : (
                          <div className="whitespace-pre-wrap text-sm text-gray-800">{loc.locator_value}</div>
                        )}
                      </td>
                      <td className="p-3 text-right space-x-2">
                        {editingId === loc.id ? (
                          <>
                            <Button size="sm" onClick={() => saveEdit(loc.id)} disabled={!editKey.trim() || !editVal.trim()}>Save</Button>
                            <Button size="sm" variant="outline" onClick={cancelEdit}>Cancel</Button>
                          </>
                        ) : (
                          <>
                            <Button size="sm" variant="outline" onClick={() => copyToClipboard(loc.locator_value)}>Copy</Button>
                            <Button size="sm" variant="outline" onClick={() => startEdit(loc)}>Edit</Button>
                            <Button size="sm" variant="destructive" onClick={() => setDeletingId(loc.id)}>Delete</Button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr>
                      <td colSpan={3} className="p-6 text-center text-muted-foreground">No locators found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Create Locator Modal */}
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogContent className="w-full sm:w-[720px]">
            <DialogHeader>
              <DialogTitle>New Locator</DialogTitle>
            </DialogHeader>
            <form onSubmit={addLocator} className="space-y-4">
              <div>
                <Label className="mb-1 block">Key</Label>
                <Input placeholder="buttonSignIn" value={newKey} onChange={(e) => setNewKey(e.target.value)} />
              </div>
              <div>
                <Label className="mb-1 block">Value</Label>
                <Input placeholder="//a/sign ..." value={newVal} onChange={(e) => setNewVal(e.target.value)} />
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={!newKey.trim() || !newVal.trim() || creating}>Create</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Delete Confirm Modal */}
        <Dialog open={!!deletingId} onOpenChange={(open) => !open && setDeletingId(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete locator?</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">This action cannot be undone.</p>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setDeletingId(null)}>Cancel</Button>
                <Button variant="destructive" onClick={() => deletingId && removeLocator(deletingId)}>Delete</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </AppLayout>
  )
}


