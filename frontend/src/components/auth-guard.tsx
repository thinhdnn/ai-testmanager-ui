"use client"

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { Loader2 } from 'lucide-react'

interface AuthGuardProps {
  children: React.ReactNode
  requireAuth?: boolean
  redirectTo?: string
}

export function AuthGuard({ 
  children, 
  requireAuth = true, 
  redirectTo = '/login' 
}: AuthGuardProps) {
  const { user, isLoading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!isLoading) {
      if (requireAuth && !user) {
        // Store the current path to redirect back after login
        if (pathname !== '/login') {
          sessionStorage.setItem('redirectAfterLogin', pathname)
        }
        router.push(redirectTo)
      } else if (!requireAuth && user) {
        // If user is logged in and we're on a public page (like login), redirect to dashboard
        const redirectPath = sessionStorage.getItem('redirectAfterLogin') || '/dashboard'
        sessionStorage.removeItem('redirectAfterLogin')
        router.push(redirectPath)
      }
    }
  }, [user, isLoading, requireAuth, redirectTo, router, pathname])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    )
  }

  if (requireAuth && !user) {
    return null // Will redirect to login
  }

  if (!requireAuth && user) {
    return null // Will redirect to dashboard
  }

  return <>{children}</>
} 