"use client"

import { useEffect, useState } from "react"
import { AppLayout } from "@/components/app-layout"
import { Button } from "@/components/ui/button"
import { UserCard } from "@/components/ui/user-card"
import { CreateUserModal } from "@/components/create-user-modal"
import { DataTable } from "@/components/ui/data-table"
import { userColumns } from "@/lib/columns/user-columns"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { apiClient } from "@/lib/apiClient"
import { UserDetailModal } from "@/components/user-detail-modal"

// Define the User type expected by the UI
interface User {
  id: string
  name: string
  email: string
  role: string
  status: 'active' | 'inactive'
  avatarUrl?: string
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [showUserDetailModal, setShowUserDetailModal] = useState(false)

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const response = await apiClient("/users/")
      
      // Map backend fields to frontend fields
      const mappedUsers = response.map((user: any) => ({
        id: user.id,
        name: user.username,
        email: user.email || "",
        role: "user", // TODO: Add role field in backend
        status: user.is_active ? "active" : "inactive",
        avatarUrl: undefined
      }))
      
      setUsers(mappedUsers)
    } catch {
      // Handle error (could show a message)
      setUsers([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  const handleRowClick = (user: User) => {
    setSelectedUser(user)
    setShowUserDetailModal(true)
  }

  return (
    <AppLayout title="Users">
      <div className="container mx-auto p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Users</h1>
          <Button 
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg transition-all duration-200 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Add New User
          </Button>
        </div>

        <Tabs defaultValue="table" className="mt-4">
          <TabsList>
            <TabsTrigger value="table">Table View</TabsTrigger>
            <TabsTrigger value="cards">Card View</TabsTrigger>
          </TabsList>

          <TabsContent value="table" className="mt-4">
            {loading ? (
              <div>Loading users...</div>
            ) : (
              <DataTable columns={userColumns} data={users} onRowClick={handleRowClick} />
            )}
          </TabsContent>

          <TabsContent value="cards" className="mt-4">
            {loading ? (
              <div>Loading users...</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {users.map((user) => (
                  <UserCard key={user.id} {...user} />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>

        <CreateUserModal
          open={showCreateModal}
          onOpenChange={setShowCreateModal}
          onUserCreated={fetchUsers}
        />
        <UserDetailModal
          open={showUserDetailModal}
          onOpenChange={setShowUserDetailModal}
          user={selectedUser}
          onUserUpdated={fetchUsers}
        />
      </div>
    </AppLayout>
  )
} 