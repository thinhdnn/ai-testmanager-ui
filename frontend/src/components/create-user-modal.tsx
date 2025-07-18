import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { apiClient } from "@/lib/apiClient"

interface CreateUserModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onUserCreated: () => void
}

export function CreateUserModal({ open, onOpenChange, onUserCreated }: CreateUserModalProps) {
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    username: "",
    email: "",
    role: "user",
    password: ""
  })
  const [confirmPassword, setConfirmPassword] = useState("")
  const [passwordError, setPasswordError] = useState("")
  const [usernameError, setUsernameError] = useState("")

  const validateUsername = (username: string) => {
    if (username.length < 4) return "Username must be at least 4 characters"
    if (!/^[a-zA-Z0-9_]+$/.test(username)) return "Only letters, numbers, and underscores allowed"
    if (username.includes(" ")) return "Username cannot contain spaces"
    return ""
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError("")
    setUsernameError("")
    const usernameValidation = validateUsername(formData.username)
    if (usernameValidation) {
      setUsernameError(usernameValidation)
      return
    }
    if (formData.password !== confirmPassword) {
      setPasswordError("Passwords do not match")
      return
    }
    setLoading(true)
    try {
      await apiClient("/users/", {
        method: "POST",
        body: JSON.stringify(formData),
        headers: {
          'Content-Type': 'application/json'
        }
      })
      setFormData({
        name: "",
        username: "",
        email: "",
        role: "user",
        password: ""
      })
      setConfirmPassword("")
      onOpenChange(false)
      onUserCreated()
    } catch (error) {
      console.error("Failed to create user:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[1200px] p-6">
        <DialogHeader className="pb-4 text-left">
          <DialogTitle className="text-xl font-semibold">Create New User</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="px-4">
          <div className="grid grid-cols-2 gap-8">
            <div className="space-y-4">
              <div>
                <Label htmlFor="name" className="text-sm font-medium">Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter full name"
                  required
                  className="h-10 mt-2"
                />
              </div>
              <div>
                <Label htmlFor="username" className="text-sm font-medium">Username</Label>
                <Input
                  id="username"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  placeholder="Enter username"
                  required
                  className="h-10 mt-2"
                />
                {usernameError && (
                  <div className="text-red-600 text-xs mt-1">{usernameError}</div>
                )}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="password" className="text-sm font-medium">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="Enter password"
                    required
                    className="h-10 mt-2"
                  />
                </div>
                <div>
                  <Label htmlFor="confirmPassword" className="text-sm font-medium">Confirm Password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter password"
                    required
                    className="h-10 mt-2"
                  />
                  {passwordError && (
                    <div className="text-red-600 text-xs mt-1">{passwordError}</div>
                  )}
                </div>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <Label htmlFor="email" className="text-sm font-medium">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="Enter email address"
                  required
                  className="h-10 mt-2"
                />
              </div>
              <div>
                <Label htmlFor="role" className="text-sm font-medium">Role</Label>
                <select
                  className="w-full rounded-md border border-input bg-background px-2 h-8 mt-2 text-sm"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-6 mt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
              className="h-10 px-4"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading} className="h-10 px-4">
              {loading ? "Creating..." : "Create User"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
} 