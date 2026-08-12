import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import Layout from '../components/Layout'
import { BarChart, LineChart, Matrix } from '../components/AnalyticsCharts'

export default function DesignDashboard() {
  const [data, setData] = useState(null)
  const [serialRanges, setSerialRanges] = useState([])
  const [error, setError] = useState(null)
  useEffect(() => { Promise.all([api('/analytics/design/failure-trends'), api('/analytics/manufacturer/serial-range-analysis')]).then(([d,s])=>{setData(d);setSerialRanges(s)}).catch(e=>setError(e.message)) }, [])
  if (error) return <Layout><div className="error-box">{error}</div></Layout>
  if (!data) return <Layout><p>Loading design analytics…</p></Layout>
  return <Layout>
    <h1>Design Analytics</h1><p className="subtitle">Engineering trends that reveal recurring model, component and failure-mode problems.</p>
    <div className="chart-grid"><LineChart data={data.failure_trend} xKey="date" title="Failure Trend Over Time" /><BarChart data={data.model_distribution} labelKey="product_model" title="Failures by AC Model" /></div>
    <div className="chart-grid"><BarChart data={data.component_trends} labelKey="component" title="Component Distribution" /><BarChart data={data.failure_mode_distribution} labelKey="failure_mode" title="Failure Mode Distribution" /></div>
    <Matrix data={data.model_x_failure_mode_matrix} rowKey="product_model" columnKey="failure_mode" title="Model × Failure Mode" />
    <div className="card"><h2>Serial Range Patterns</h2><table><thead><tr><th>Serial range</th><th>Tickets</th><th>Devices</th><th>Tickets/device</th></tr></thead><tbody>{serialRanges.map(r=><tr key={r.serial_range}><td>{r.serial_range}</td><td>{r.ticket_count}</td><td>{r.device_count}</td><td>{r.tickets_per_device}</td></tr>)}</tbody></table></div>
  </Layout>
}
