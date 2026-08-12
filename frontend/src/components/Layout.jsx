import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const NAV = {
  TECHNICIAN: [{ to: '/technician', label: 'Service Console' }],
  OVERALL_MANAGEMENT: [{ to: '/management', label: 'Reliability Overview' }],
  QUALITY: [{ to: '/quality', label: 'Quality Analytics' }],
  DESIGN: [{ to: '/design', label: 'Design Analytics' }],
  ADMIN: [{ to: '/management', label: 'Reliability Overview' }],
}

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const location = useLocation()
  const items = user ? NAV[user.role] || [] : []

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">Smart AC // FI</div>
        <nav>
          {items.map(item => (
            <Link key={item.to} to={item.to} className={location.pathname === item.to ? 'active' : ''}>
              {item.label}
            </Link>
          ))}
        </nav>
        {user && (
          <div style={{ marginTop: 40, fontSize: 12, color: '#9fb4bf' }}>
            <div>{user.username}</div>
            <div style={{ color: '#5c7480' }}>{user.role}</div>
            <button className="secondary" style={{ marginTop: 10, color: '#cfe0e8', borderColor: '#3a5563' }} onClick={logout}>
              Sign out
            </button>
          </div>
        )}
      </aside>
      <main className="main">{children}</main>
    </div>
  )
}
