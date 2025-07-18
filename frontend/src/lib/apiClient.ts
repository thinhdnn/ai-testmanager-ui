// Simple API client for the frontend
// Usage: apiClient('/projects') or apiClient('/projects', { method: 'POST', body: ... })

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL + '/api/v1'

export async function apiClient(endpoint: string, options?: RequestInit) {
  // Prepend the base API URL
  const url = `${API_BASE_URL}${endpoint}`
  const res = await fetch(url, options)

  // Throw if not ok
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