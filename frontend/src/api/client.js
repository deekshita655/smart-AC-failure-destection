const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

function getTokens() {
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  }
}

export function setTokens(access, refresh) {
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
}

export function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export async function api(path, { method = 'GET', body, isForm = false } = {}) {
  const { access } = getTokens()
  const headers = {}
  if (!isForm) headers['Content-Type'] = 'application/json'
  if (access) headers['Authorization'] = `Bearer ${access}`

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
  })
  const json = await res.json().catch(() => null)
  if (!res.ok || !json || json.success === false) {
    const message = json?.error?.message || `Request failed (${res.status})`
    const err = new Error(message)
    err.code = json?.error?.code
    throw err
  }
  return json.data
}
