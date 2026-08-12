import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import Layout from '../components/Layout'

export default function QualityDashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api('/analytics/quality/fix-history').then(setData).catch(e => setError(e.message))
  }, [])

  if (error) return <Layout><div className="error-box">{error}</div></Layout>
  if (!data) return <Layout><p>Loading…</p></Layout>

  return (
    <Layout>
      <h1>Quality Analytics</h1>
      <p className="subtitle">Fix history, repeated repairs, and severity distribution.</p>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Most Common Fixes</h2>
        <table>
          <thead><tr><th>Fix</th><th>Count</th></tr></thead>
          <tbody>{data.most_common_fixes.map((r, i) => (
            <tr key={i}><td>{r.fix_text}</td><td>{r.count}</td></tr>
          ))}</tbody>
        </table>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Components Requiring Frequent Repair</h2>
        <table>
          <thead><tr><th>Component</th><th>Count</th></tr></thead>
          <tbody>{data.components_requiring_frequent_repair.map((r, i) => (
            <tr key={i}><td>{r.component}</td><td>{r.count}</td></tr>
          ))}</tbody>
        </table>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Severity Distribution</h2>
        <div className="grid">
          {data.severity_distribution.map((r, i) => (
            <div key={i}><div className="stat">{r.count}</div><div className="stat-label">{r.severity}</div></div>
          ))}
        </div>
      </div>
    </Layout>
  )
}
