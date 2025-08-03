import { useState, useCallback } from 'react'
import { apiClient } from '@/lib/apiClient'

interface UseApiOptions {
  onSuccess?: (data: any) => void
  onError?: (error: Error) => void
  on401?: () => void
}

export function useApi(options: UseApiOptions = {}) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const callApi = useCallback(async (
    endpoint: string, 
    requestOptions?: RequestInit
  ) => {
    setLoading(true)
    setError(null)

    try {
      const data = await apiClient(endpoint, requestOptions)
      options.onSuccess?.(data)
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      setError(errorMessage)
      
      // Handle 401 specifically
      if (errorMessage.includes('Unauthorized')) {
        options.on401?.()
        // apiClient already handles redirect, so we don't need to do anything here
      } else {
        options.onError?.(err instanceof Error ? err : new Error(errorMessage))
      }
      
      throw err
    } finally {
      setLoading(false)
    }
  }, [options])

  return {
    callApi,
    loading,
    error,
    clearError: () => setError(null)
  }
} 