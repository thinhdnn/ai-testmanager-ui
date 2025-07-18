import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiClient } from "@/lib/apiClient"

interface UserDetailModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  user: any | null
  onUserUpdated?: () => void
}

export function UserDetailModal({ open, onOpenChange, user, onUserUpdated }: UserDetailModalProps) {
  const [editMode, setEditMode] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    username: "",
    email: "",
    role: "user"
  })
  const [loading, setLoading] = useState(false)
  const [showChangePassword, setShowChangePassword] = useState(false)
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [passwordError, setPasswordError] = useState("")
  const [passwordSuccess, setPasswordSuccess] = useState("")

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || "",
        username: user.username || user.name || "",
        email: user.email || "",
        role: user.role || "user"
      })
      setEditMode(false)
    }
  }, [user])

  const handleSave = async () => {
    setLoading(true)
    try {
      await apiClient(`/users/${user.id}`, {
        method: "PUT",
        body: JSON.stringify(formData),
        headers: { 'Content-Type': 'application/json' }
      })
      setEditMode(false)
      if (onUserUpdated) onUserUpdated()
    } catch (err) {
      alert("Update failed!")
    } finally {
      setLoading(false)
    }
  }

  const handleChangePassword = async (e: any) => {
    e.preventDefault()
    setPasswordError("")
    setPasswordSuccess("")
    if (!newPassword || !confirmPassword) {
      setPasswordError("Please enter both fields")
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("Passwords do not match")
      return
    }
    setLoading(true)
    try {
      await apiClient(`/users/${user.id}`, {
        method: "PUT",
        body: JSON.stringify({ password: newPassword }),
        headers: { 'Content-Type': 'application/json' }
      })
      setPasswordSuccess("Password changed successfully!")
      setNewPassword("")
      setConfirmPassword("")
      setTimeout(() => {
        setShowChangePassword(false)
        setPasswordSuccess("")
      }, 1200)
    } catch (err) {
      setPasswordError("Change password failed!")
    } finally {
      setLoading(false)
    }
  }

  if (!user) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] p-6">
        <DialogHeader className="pb-4 text-left">
          <DialogTitle className="text-xl font-semibold">User Detail</DialogTitle>
        </DialogHeader>
        <form className="px-4" onSubmit={e => { e.preventDefault(); if (editMode) handleSave() }}>
          <div className="grid grid-cols-2 gap-8">
            <div className="space-y-4">
              <div>
                <Label className="text-sm font-medium">Name</Label>
                <Input value={formData.name} disabled={!editMode} className="h-10 mt-2" onChange={e => setFormData(f => ({ ...f, name: e.target.value }))} />
              </div>
              <div>
                <Label className="text-sm font-medium">Username</Label>
                <Input value={formData.username} disabled={!editMode} className="h-10 mt-2" onChange={e => setFormData(f => ({ ...f, username: e.target.value }))} />
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <Label className="text-sm font-medium">Email</Label>
                <Input value={formData.email} disabled={!editMode} className="h-10 mt-2" onChange={e => setFormData(f => ({ ...f, email: e.target.value }))} />
              </div>
              <div>
                <Label className="text-sm font-medium">Role</Label>
                <Input value={formData.role} disabled={!editMode} className="h-10 mt-2" onChange={e => setFormData(f => ({ ...f, role: e.target.value }))} />
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-6 mt-4">
            {!editMode && (
              <Button type="button" variant="secondary" onClick={() => setShowChangePassword(true)} className="h-10 px-4">Change Password</Button>
            )}
            {editMode ? (
              <>
                <Button type="button" variant="outline" onClick={() => { setEditMode(false); setFormData({
                  name: user.name || "",
                  username: user.username || user.name || "",
                  email: user.email || "",
                  role: user.role || "user"
                }) }} className="h-10 px-4">Cancel</Button>
                <Button type="submit" disabled={loading} className="h-10 px-4">{loading ? "Saving..." : "Save"}</Button>
              </>
            ) : (
              <Button type="button" onClick={() => setEditMode(true)} className="h-10 px-4">Edit</Button>
            )}
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} className="h-10 px-4">Close</Button>
          </div>
        </form>
      </DialogContent>
      {/* Change Password Modal */}
      <Dialog open={showChangePassword} onOpenChange={setShowChangePassword}>
        <DialogContent className="max-w-xs p-6">
          <DialogHeader>
            <DialogTitle className="text-base">Change Password</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <Label>New Password</Label>
              <Input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required className="h-9 mt-1" />
            </div>
            <div>
              <Label>Confirm Password</Label>
              <Input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required className="h-9 mt-1" />
            </div>
            {passwordError && <div className="text-red-600 text-xs">{passwordError}</div>}
            {passwordSuccess && <div className="text-green-600 text-xs">{passwordSuccess}</div>}
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowChangePassword(false)} className="h-9 px-3">Cancel</Button>
              <Button type="submit" disabled={loading} className="h-9 px-3">{loading ? "Saving..." : "Save"}</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </Dialog>
  )
} 