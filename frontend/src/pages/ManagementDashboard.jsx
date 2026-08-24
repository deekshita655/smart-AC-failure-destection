import React, { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import Layout from '../components/Layout'
import { BarChart, LineChart, DonutChart, HealthChart } from '../components/AnalyticsCharts'

export default function ManagementDashboard() {
  const [overview, setOverview] = useState(null)
  const [trend, setTrend] = useState([])
  const [serialRanges, setSerialRanges] = useState([])
  const [predictive, setPredictive] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      api('/analytics/manufacturer/overview'),
      api('/analytics/manufacturer/failure-trend'),
      api('/analytics/manufacturer/serial-range-analysis'),
      api('/predictive/overview'),
    ]).then(([o, t, s, p]) => {
      setOverview(o); setTrend(t); setSerialRanges(s); setPredictive(p)
    }).catch(e => setError(e.message))
  }, [])

  const criticalCount = useMemo(() =>
    (overview?.severity_distribution || []).find(x => String(x.severity).toUpperCase() === 'CRITICAL')?.count || 0,
    [overview]
  )
  const highRiskCount = useMemo(() =>
    (predictive?.risk_distribution || []).filter(x => ['HIGH', 'CRITICAL'].includes(String(x.risk_level).toUpperCase()))
      .reduce((sum, x) => sum + Number(x.count || 0), 0),
    [predictive]
  )

  if (error) return <Layout><div className="error-box">{error}</div></Layout>
  if (!overview || !predictive) return <Layout><p>Loading analytics…</p></Layout>
  const pm = overview.predictive_maintenance

  return <Layout>
    <div className="dashboard-head">
      <div><h1>Reliability Overview</h1><p className="subtitle">Manufacturer reliability intelligence, failure trends and predictive maintenance.</p></div>
      <span className="live-pill">● LIVE DATA</span>
    </div>

    <div className="grid stat-grid">
      <div className="card"><div className="stat">{overview.total_service_tickets}</div><div className="stat-label">Service tickets</div></div>
      <div className="card"><div className="stat">{overview.total_devices}</div><div className="stat-label">Devices</div></div>
      <div className="card"><div className="stat">{overview.avg_ai_confidence != null ? `${(overview.avg_ai_confidence * 100).toFixed(0)}%` : '—'}</div><div className="stat-label">Avg AI confidence</div></div>
      <div className="card"><div className="stat">{criticalCount}</div><div className="stat-label">Critical failures</div></div>
      <div className="card"><div className="stat">{highRiskCount}</div><div className="stat-label">High / critical risk</div></div>
    </div>

    <div className="chart-grid">
      <LineChart data={trend} xKey="date" title="Failure Trend · Last 7 Days" />
      <BarChart data={[...(overview.model_x_ticket_count || [])].sort((a,b)=>b.ticket_count-a.ticket_count)} labelKey="product_model" valueKey="ticket_count" title="Failures by AC Model" />
    </div>

    <div className="chart-grid">
      <BarChart data={overview.failure_mode_distribution} labelKey="failure_mode" valueKey="count" title="Failure Modes" />
      <BarChart data={overview.component_distribution} labelKey="component" valueKey="count" title="Components" />
    </div>

    <div className="chart-grid">
      <DonutChart data={overview.severity_distribution} labelKey="severity" valueKey="count" title="Severity Distribution" />
      <DonutChart data={overview.department_distribution} labelKey="department" valueKey="count" title="Department Distribution" />
    </div>

    <div className="card predictive-card">
      <div><h2>Predictive Maintenance</h2><p className="subtitle">Early-warning signals from the predictive pipeline.</p></div>
      <div className="mini-stats">
        <div><b>{pm.anomalies_detected}</b><span>Anomalies</span></div>
        <div><b>{pm.predicted_failures_confirmed}</b><span>Confirmed</span></div>
        <div><b>{pm.predictions_pending}</b><span>Pending</span></div>
        <div><b>{pm.false_positive_alerts}</b><span>False positives</span></div>
        <div><b>{pm.preventive_tickets_generated}</b><span>Preventive tickets</span></div>
      </div>
    </div>

    <div className="chart-grid">
      <HealthChart data={predictive.health} title="Current Device Health" />
      <BarChart data={predictive.risk_distribution} labelKey="risk_level" valueKey="count" title="Predictive Risk Distribution" />
    </div>

    <div className="card">
      <h2>Device Health & Risk</h2>
      <table><thead><tr><th>Device</th><th>Health</th><th>Anomaly</th><th>Status</th></tr></thead>
        <tbody>{predictive.health.map(r => <tr key={r.device_id}>
          <td>{r.device_id}</td><td>{Number(r.health_score).toFixed(0)}%</td><td>{Number(r.anomaly_score).toFixed(2)}</td>
          <td><span className={`badge ${String(r.status).includes('CRITICAL') ? 'danger' : String(r.status).includes('RISK') ? 'warn' : 'ok'}`}>{r.status}</span></td>
        </tr>)}</tbody>
      </table>
    </div>

    <div className="card">
      <h2>Prediction Outcomes</h2>
      <div className="outcome-grid">{predictive.outcome_distribution.map(r => <div className="outcome-item" key={r.outcome}><b>{r.count}</b><span>{r.outcome}</span></div>)}</div>
    </div>

    <div className="card">
      <h2>Serial Range Risk</h2>
      <table><thead><tr><th>Serial range</th><th>Tickets</th><th>Devices</th><th>Tickets/device</th><th>Signal</th></tr></thead>
        <tbody>{serialRanges.map(r => <tr key={r.serial_range}><td>{r.serial_range}</td><td>{r.ticket_count}</td><td>{r.device_count}</td><td>{r.tickets_per_device}</td><td>{r.tickets_per_device > 1.5 ? <span className="badge warn">investigate</span> : <span className="badge ok">normal</span>}</td></tr>)}</tbody>
      </table>
    </div>
  </Layout>
}
