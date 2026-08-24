import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import Layout from '../components/Layout'
import { BarChart, LineChart, DonutChart } from '../components/AnalyticsCharts'

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
  if (!overview || !trends) return <Layout><p>Loading…</p></Layout>

  const outcomeData = ['CONFIRMED', 'FALSE_POSITIVE', 'PENDING'].map(outcome => ({
    outcome, count: trends.prediction_outcome_trends.filter(r => r.outcome === outcome).reduce((sum, r) => sum + r.count, 0)
  })).filter(r => r.count > 0)

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

      <div className="analytics-grid">
        <LineChart data={trends.failure_trends} xKey="period" yKey="failure_count" title="Service Tickets Over Time" />
        <BarChart data={overview.model_x_ticket_count} labelKey="product_model" valueKey="ticket_count" title="Tickets by Product Model" />
        <DonutChart data={overview.failure_mode_distribution} labelKey="failure_mode" valueKey="count" title="Failure Mode Distribution" />
        <BarChart data={overview.department_distribution} labelKey="department" valueKey="count" title="Department Distribution" />
        <DonutChart data={outcomeData} labelKey="outcome" valueKey="count" title="Prediction Outcomes" />
        <BarChart data={serialRanges} labelKey="serial_range" valueKey="tickets_per_device" title="Serial Range — Tickets per Device" />
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
        <h2 style={{ marginTop: 0 }}>Serial Range Detail</h2>
        <table><thead><tr><th>Serial range</th><th>Tickets</th><th>Devices</th><th>Tickets/device</th></tr></thead>
          <tbody>{serialRanges.map(r => <tr key={r.serial_range}><td>{r.serial_range}</td><td>{r.ticket_count}</td><td>{r.device_count}</td><td>{r.tickets_per_device}</td></tr>)}</tbody>
        </table>
      </div>
    </Layout>
  )
}
