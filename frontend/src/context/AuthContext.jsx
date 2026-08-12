import React, { createContext, useContext, useState, useEffect } from 'react'
import { api, setTokens, clearTokens } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) { setLoading(false); return }
    api('/auth/me').then(setUser).catch(() => clearTokens()).finally(() => setLoading(false))
  }, [])

  async function login(username, password) {
    const data = await api('/auth/login', { method: 'POST', body: { username, password } })
    setTokens(data.access_token, data.refresh_token)
    const me = await api('/auth/me')
    setUser(me)
    return me
  }

  function logout() {
    clearTokens()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
