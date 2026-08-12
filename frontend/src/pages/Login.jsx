import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [username, setUsername] = useState('tech1')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    try {
      const user = await login(username, password)
      const roleRoutes = {
        TECHNICIAN: '/technician',
        OVERALL_MANAGEMENT: '/management',
        QUALITY: '/quality',
        DESIGN: '/design',
        ADMIN: '/management',
      }
      navigate(roleRoutes[user.role] || '/technician')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="login-shell">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="brand">Smart AC // Failure Intelligence</div>
        <h1 style={{ marginBottom: 6 }}>Sign in</h1>
        <p className="subtitle">Predictive maintenance & reliability platform</p>
        {error && <div className="error-box">{error}</div>}
        <label>Username</label>
        <input value={username} onChange={e => setUsername(e.target.value)} />
        <label>Password</label>
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
        <button type="submit" style={{ width: '100%', marginTop: 8 }}>Sign in</button>
        <p style={{ fontSize: 11, color: '#8a9aa3', marginTop: 16 }}>
          Demo accounts (seeded): tech1 / mgmt1 / quality1 / design1 / admin1 — password: Password123!
        </p>
      </form>
    </div>
  )
}
