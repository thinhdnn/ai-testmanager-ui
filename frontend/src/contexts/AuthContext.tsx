"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { apiClient } from '@/lib/apiClient'

export interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  is_superuser: boolean
  is_verified: boolean
  created_by?: string
  updated_by?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (credentials: { username: string; password: string }) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check for existing token on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token')
    if (savedToken) {
      setToken(savedToken)
      fetchUser(savedToken)
    } else {
      setIsLoading(false)
    }
  }, [])

  const fetchUser = async (authToken: string) => {
    try {
      const userData = await apiClient('/auth/me', {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      })
      setUser(userData)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      // Token might be invalid or expired, clear it
      localStorage.removeItem('auth_token')
      setToken(null)
      setUser(null)
      
      // Don't redirect here as apiClient will handle 401 redirects
      // Only redirect if it's not a 401 error
      if (error instanceof Error && !error.message.includes('Unauthorized')) {
        console.error('Non-401 error during user fetch:', error)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (credentials: { username: string; password: string }) => {
    try {
      const formData = new URLSearchParams()
      formData.append('username', credentials.username)
      formData.append('password', credentials.password)

      const response = await apiClient('/auth/jwt/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString()
      })

      const { access_token } = response
      
      // Save token
      localStorage.setItem('auth_token', access_token)
      setToken(access_token)
      
      // Fetch user data
      await fetchUser(access_token)
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setToken(null)
    setUser(null)
  }

  const value = {
    user,
    token,
    login,
    logout,
    isLoading
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
} 