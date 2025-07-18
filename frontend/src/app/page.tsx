import { AppLayout } from "@/components/app-layout"
import { DashboardContent } from "@/components/dashboard-content"
import { UserProvider } from "@/contexts/UserContext"

export default function Home() {
  // Sample user data
  const user = {
    name: "Alex Johnson", 
    email: "alex.johnson@company.com",
    avatar: undefined // Will use initials
  }

  return (
    <UserProvider user={user}>
      <AppLayout title="Dashboard">
        <DashboardContent />
      </AppLayout>
    </UserProvider>
  )
}
