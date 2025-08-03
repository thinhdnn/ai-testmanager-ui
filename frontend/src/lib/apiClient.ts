// Simple API client for the frontend
// Usage: apiClient('/projects') or apiClient('/projects', { method: 'POST', body: ... })

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000') + '/api/v1'

export async function apiClient(endpoint: string, options?: RequestInit) {
  // Prepend the base API URL
  const url = `${API_BASE_URL}${endpoint}`
  
  // Get token from localStorage
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
  
  // Prepare headers
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> || {}),
  }
  
  // Add authorization header if token exists
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  const res = await fetch(url, {
    ...options,
    headers,
  })

  // Handle 401 Unauthorized - redirect to login
  if (res.status === 401) {
    // Clear invalid token
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      // Redirect to login page
      window.location.href = '/login'
    }
    throw new Error('Unauthorized - Please login again')
  }

  // Throw if not ok (other errors)
  if (!res.ok) {
    // Try to parse error message from response
    let errorMsg = `API error: ${res.status}`
    try {
      const data = await res.json()
      errorMsg = data.detail || data.message || errorMsg
    } catch {}
    throw new Error(errorMsg)
  }

  // Try to parse JSON, fallback to text
  try {
    return await res.json()
  } catch {
    return await res.text()
  }
} 