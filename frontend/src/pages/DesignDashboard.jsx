import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import Layout from '../components/Layout'

function BarChart({ data, labelKey, valueKey }) {
  if (!data?.length) return <div className="empty-chart">No data available</div>
  const max = Math.max(...data.map(d => Number(d[valueKey]) || 0), 1), width = 620, height = 230
  return <div className="chart-wrap"><svg viewBox={`0 0 ${width} ${height}`} className="chart" role="img" aria-label="Design analytics bar chart">
    {data.slice(0, 12).map((d, i) => {
      const x = 25 + i * ((width - 45) / Math.min(data.length, 12)) + 4
      const barWidth = Math.max(18, Math.min(42, (width - 60) / Math.min(data.length, 12) - 8))
      const h = ((height - 50) * (Number(d[valueKey]) || 0)) / max
      return <g key={i}><rect x={x} y={height - 30 - h} width={barWidth} height={h} rx="4" className="chart-bar" /><text x={x + barWidth / 2} y={height - 10} textAnchor="middle" className="chart-label">{String(d[labelKey]).slice(0, 9)}</text><text x={x + barWidth / 2} y={height - 35 - h} textAnchor="middle" className="chart-value">{d[valueKey]}</text></g>
    })}
  </svg></div>
}

export default function DesignDashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => { api('/analytics/design/failure-trends').then(setData).catch(e => setError(e.message)) }, [])
  if (error) return <Layout><div className="error-box">{error}</div></Layout>
  if (!data) return <Layout><p>Loading…</p></Layout>

  return <Layout>
    <h1>Design Analytics</h1>
    <p className="subtitle">Failure patterns, component concentration and model comparisons.</p>

    <div className="card"><h2>Component Failure Distribution</h2><BarChart data={data.component_trends} labelKey="component" valueKey="count" /></div>

    <div className="card"><h2>Model × Failure Mode Matrix</h2>
      <table><thead><tr><th>Product model</th><th>Failure mode</th><th>Count</th></tr></thead>
      <tbody>{data.model_x_failure_mode_matrix.map((r, i) => <tr key={i}><td>{r.product_model}</td><td>{r.failure_mode}</td><td>{r.count}</td></tr>)}</tbody></table>
    </div>

    <div className="card"><h2>Component Details</h2>
      <table><thead><tr><th>Component</th><th>Count</th></tr></thead>
      <tbody>{data.component_trends.map((r, i) => <tr key={i}><td>{r.component}</td><td>{r.count}</td></tr>)}</tbody></table>
    </div>
  </Layout>
}
