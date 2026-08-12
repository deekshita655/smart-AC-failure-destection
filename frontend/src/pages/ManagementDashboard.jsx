import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import Layout from '../components/Layout'
import { BarChart, LineChart, DonutChart } from '../components/AnalyticsCharts'

export default function ManagementDashboard() {
  const [overview, setOverview] = useState(null)
  const [trend, setTrend] = useState([])
  const [serialRanges, setSerialRanges] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      api('/analytics/manufacturer/overview'),
      api('/analytics/manufacturer/failure-trend'),
      api('/analytics/manufacturer/serial-range-analysis'),
    ]).then(([o,t,s]) => { setOverview(o); setTrend(t); setSerialRanges(s) }).catch(e => setError(e.message))
  }, [])

  if (error) return <Layout><div className="error-box">{error}</div></Layout>
  if (!overview) return <Layout><p>Loading analytics…</p></Layout>
  const pm = overview.predictive_maintenance
  return <Layout>
    <div className="dashboard-head"><div><h1>Reliability Overview</h1><p className="subtitle">Manufacturer reliability intelligence, failure trends and predictive maintenance.</p></div><span className="live-pill">● LIVE DATA</span></div>
    <div className="grid stat-grid">
      <div className="card"><div className="stat">{overview.total_service_tickets}</div><div className="stat-label">Service tickets</div></div>
      <div className="card"><div className="stat">{overview.total_devices}</div><div className="stat-label">Devices</div></div>
      <div className="card"><div className="stat">{overview.avg_ai_confidence != null ? `${(overview.avg_ai_confidence * 100).toFixed(0)}%` : '—'}</div><div className="stat-label">Avg AI confidence</div></div>
      <div className="card"><div className="stat">{pm.preventive_tickets_generated}</div><div className="stat-label">Preventive tickets</div></div>
    </div>
    <div className="chart-grid"><LineChart data={trend} xKey="date" title="Failure Trend Over Time" /><BarChart data={overview.model_x_ticket_count.sort((a,b)=>b.ticket_count-a.ticket_count)} labelKey="product_model" valueKey="ticket_count" title="Failures by AC Model" /></div>
    <div className="chart-grid"><BarChart data={overview.failure_mode_distribution} labelKey="failure_mode" title="Failure Modes" /><DonutChart data={overview.department_distribution} labelKey="department" title="Department Distribution" /></div>
    <div className="card predictive-card"><div><h2>Predictive Maintenance</h2><p className="subtitle">Early-warning signals from the predictive pipeline.</p></div><div className="mini-stats"><div><b>{pm.anomalies_detected}</b><span>Anomalies</span></div><div><b>{pm.predicted_failures_confirmed}</b><span>Confirmed</span></div><div><b>{pm.predictions_pending}</b><span>Pending</span></div><div><b>{pm.false_positive_alerts}</b><span>False positives</span></div></div></div>
    <div className="card"><h2>Serial Range Risk</h2><table><thead><tr><th>Serial range</th><th>Tickets</th><th>Devices</th><th>Tickets/device</th></tr></thead><tbody>{serialRanges.map(r=><tr key={r.serial_range}><td>{r.serial_range}</td><td>{r.ticket_count}</td><td>{r.device_count}</td><td>{r.tickets_per_device}{r.tickets_per_device > 1.5 && <span className="badge warn" style={{marginLeft:6}}>investigate</span>}</td></tr>)}</tbody></table></div>
  </Layout>
}
