import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import TechnicianDashboard from './pages/TechnicianDashboard'
import ManagementDashboard from './pages/ManagementDashboard'
import QualityDashboard from './pages/QualityDashboard'
import DesignDashboard from './pages/DesignDashboard'

function Protected({ roles, children }) {
  const { user, loading } = useAuth()
  if (loading) return <p style={{ padding: 40 }}>Loading…</p>
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/login" replace />
  return children
}

function Root() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/technician" element={<Protected roles={['TECHNICIAN']}><TechnicianDashboard /></Protected>} />
      <Route path="/management" element={<Protected roles={['OVERALL_MANAGEMENT', 'ADMIN']}><ManagementDashboard /></Protected>} />
      <Route path="/quality" element={<Protected roles={['QUALITY']}><QualityDashboard /></Protected>} />
      <Route path="/design" element={<Protected roles={['DESIGN']}><DesignDashboard /></Protected>} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Root />
    </AuthProvider>
  )
}
