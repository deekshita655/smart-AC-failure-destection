import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import Layout from '../components/Layout'

function BarChart({ data, labelKey, valueKey, height = 220 }) {
  if (!data?.length) return <div className="empty-chart">No data available</div>
  const max = Math.max(...data.map(d => Number(d[valueKey]) || 0), 1)
  const width = 560
  const barWidth = Math.max(18, Math.min(52, (width - 40) / data.length - 10))
  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} className="chart" role="img" aria-label="Bar chart">
        {data.map((d, i) => {
          const value = Number(d[valueKey]) || 0
          const x = 30 + i * ((width - 50) / data.length) + 4
          const h = ((height - 48) * value) / max
          return <g key={i}>
            <rect x={x} y={height - 28 - h} width={barWidth} height={h} rx="4" className="chart-bar" />
            <text x={x + barWidth / 2} y={height - 10} textAnchor="middle" className="chart-label">{String(d[labelKey]).slice(0, 10)}</text>
            <text x={x + barWidth / 2} y={height - 34 - h} textAnchor="middle" className="chart-value">{value}</text>
          </g>
        })}
      </svg>
    </div>
  )
}

function TrendChart({ data }) {
  if (!data?.length) return <div className="empty-chart">No historical data available</div>
  const width = 640, height = 240, max = Math.max(...data.map(d => Number(d.count) || 0), 1)
  const points = data.map((d, i) => {
    const x = 35 + (i * (width - 60)) / Math.max(data.length - 1, 1)
    const y = height - 35 - ((Number(d.count) || 0) / max) * (height - 65)
    return `${x},${y}`
  }).join(' ')
  return <div className="chart-wrap"><svg viewBox={`0 0 ${width} ${height}`} className="chart" role="img" aria-label="Failure trend">
    <polyline points={points} fill="none" className="chart-line" />
    {data.map((d, i) => {
      const x = 35 + (i * (width - 60)) / Math.max(data.length - 1, 1)
      const y = height - 35 - ((Number(d.count) || 0) / max) * (height - 65)
      return <g key={i}><circle cx={x} cy={y} r="4" className="chart-point" /><text x={x} y={height - 12} textAnchor="middle" className="chart-label">{d.period}</text><text x={x} y={y - 9} textAnchor="middle" className="chart-value">{d.count}</text></g>
    })}
  </svg></div>
}

export default function ManagementDashboard() {
  const [overview, setOverview] = useState(null)
  const [serialRanges, setSerialRanges] = useState([])
  const [trends, setTrends] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      api('/analytics/manufacturer/overview'),
      api('/analytics/manufacturer/serial-range-analysis'),
      api('/analytics/manufacturer/trends'),
    ]).then(([o, s, t]) => { setOverview(o); setSerialRanges(s); setTrends(t) }).catch(e => setError(e.message))
  }, [])

  if (error) return <Layout><div className="error-box">{error}</div></Layout>
  if (!overview) return <Layout><p>Loading…</p></Layout>

  return <Layout>
    <h1>Reliability Overview</h1>
    <p className="subtitle">Overall manufacturer analytics, failure trends and predictive-maintenance summary.</p>

    <div className="grid">
      <div className="card"><div className="stat">{overview.total_service_tickets}</div><div className="stat-label">Total service tickets</div></div>
      <div className="card"><div className="stat">{overview.total_devices}</div><div className="stat-label">Total devices</div></div>
      <div className="card"><div className="stat">{overview.avg_ai_confidence != null ? (overview.avg_ai_confidence * 100).toFixed(0) + '%' : '—'}</div><div className="stat-label">Avg AI confidence</div></div>
      <div className="card"><div className="stat">{overview.predictive_maintenance.preventive_tickets_generated}</div><div className="stat-label">Preventive tickets</div></div>
    </div>

    <div className="card"><h2>Failure Trend</h2><TrendChart data={trends?.failure_trends} /></div>

    <div className="grid">
      <div className="card"><h2>Tickets by Product Model</h2><BarChart data={overview.model_x_ticket_count} labelKey="product_model" valueKey="ticket_count" /></div>
      <div className="card"><h2>Failure Mode Distribution</h2><BarChart data={overview.failure_mode_distribution} labelKey="failure_mode" valueKey="count" /></div>
    </div>

    <div className="card">
      <h2>Predictive Maintenance</h2>
      <div className="grid">
        <div><div className="stat">{overview.predictive_maintenance.anomalies_detected}</div><div className="stat-label">Anomalies detected</div></div>
        <div><div className="stat">{overview.predictive_maintenance.predicted_failures_confirmed}</div><div className="stat-label">Confirmed predictions</div></div>
        <div><div className="stat">{overview.predictive_maintenance.predictions_pending}</div><div className="stat-label">Pending</div></div>
        <div><div className="stat">{overview.predictive_maintenance.false_positive_alerts}</div><div className="stat-label">False positives</div></div>
      </div>
    </div>

    <div className="card"><h2>Serial Ranges — Tickets per Device</h2>
      <table><thead><tr><th>Serial range</th><th>Tickets</th><th>Devices</th><th>Tickets/device</th></tr></thead>
        <tbody>{serialRanges.map(r => <tr key={r.serial_range}><td>{r.serial_range}</td><td>{r.ticket_count}</td><td>{r.device_count}</td><td>{r.tickets_per_device}{r.tickets_per_device > 1.5 && <span className="badge warn" style={{ marginLeft: 6 }}>investigate</span>}</td></tr>)}</tbody>
      </table>
    </div>
  </Layout>
}
