import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import Layout from '../components/Layout'

export default function ManagementDashboard() {
  const [overview, setOverview] = useState(null)
  const [serialRanges, setSerialRanges] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    api('/analytics/manufacturer/overview').then(setOverview).catch(e => setError(e.message))
    api('/analytics/manufacturer/serial-range-analysis').then(setSerialRanges).catch(() => {})
  }, [])

  if (error) return <Layout><div className="error-box">{error}</div></Layout>
  if (!overview) return <Layout><p>Loading…</p></Layout>

  return (
    <Layout>
      <h1>Reliability Overview</h1>
      <p className="subtitle">Overall manufacturer analytics & predictive maintenance summary.</p>

      <div className="grid">
        <div className="card"><div className="stat">{overview.total_service_tickets}</div><div className="stat-label">Total service tickets</div></div>
        <div className="card"><div className="stat">{overview.total_devices}</div><div className="stat-label">Total devices</div></div>
        <div className="card"><div className="stat">{overview.avg_ai_confidence != null ? (overview.avg_ai_confidence * 100).toFixed(0) + '%' : '—'}</div><div className="stat-label">Avg AI confidence</div></div>
        <div className="card"><div className="stat">{overview.predictive_maintenance.preventive_tickets_generated}</div><div className="stat-label">Preventive tickets</div></div>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Predictive Maintenance</h2>
        <div className="grid">
          <div><div className="stat">{overview.predictive_maintenance.anomalies_detected}</div><div className="stat-label">Anomalies detected</div></div>
          <div><div className="stat">{overview.predictive_maintenance.predicted_failures_confirmed}</div><div className="stat-label">Confirmed predictions</div></div>
          <div><div className="stat">{overview.predictive_maintenance.predictions_pending}</div><div className="stat-label">Pending</div></div>
          <div><div className="stat">{overview.predictive_maintenance.false_positive_alerts}</div><div className="stat-label">False positives</div></div>
        </div>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Tickets by Model</h2>
        <table>
          <thead><tr><th>Product model</th><th>Ticket count</th></tr></thead>
          <tbody>{overview.model_x_ticket_count.map(r => (
            <tr key={r.product_model}><td>{r.product_model}</td><td>{r.ticket_count}</td></tr>
          ))}</tbody>
        </table>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Serial Ranges — Tickets per Device</h2>
        <table>
          <thead><tr><th>Serial range</th><th>Tickets</th><th>Devices</th><th>Tickets/device</th></tr></thead>
          <tbody>{serialRanges.map(r => (
            <tr key={r.serial_range}>
              <td>{r.serial_range}</td><td>{r.ticket_count}</td><td>{r.device_count}</td>
              <td>{r.tickets_per_device}{r.tickets_per_device > 1.5 && <span className="badge warn" style={{ marginLeft: 6 }}>investigate</span>}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </Layout>
  )
}
