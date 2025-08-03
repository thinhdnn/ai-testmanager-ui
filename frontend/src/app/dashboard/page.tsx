"use client"

import { AuthGuard } from "@/components/auth-guard"
import { AppLayout } from "@/components/app-layout"
import { DashboardContent } from "@/components/dashboard-content"

function DashboardPageContent() {
  return (
    <AppLayout title="Dashboard">
      <DashboardContent />
    </AppLayout>
  )
}

export default function DashboardPage() {
  return (
    <AuthGuard requireAuth={true}>
      <DashboardPageContent />
    </AuthGuard>
  )
} 