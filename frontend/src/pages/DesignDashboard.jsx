import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import Layout from '../components/Layout'
import { BarChart, LineChart, Matrix } from '../components/AnalyticsCharts'

export default function DesignDashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => { api('/analytics/design/failure-trends').then(setData).catch(e => setError(e.message)) }, [])

  if (error) return <Layout><div className="error-box">{error}</div></Layout>
  if (!data) return <Layout><p>Loading…</p></Layout>

  return <Layout>
    <h1>Design Analytics</h1>
    <p className="subtitle">Failure trends, component trends, and model comparisons.</p>
    <div className="analytics-grid">
      <Matrix data={data.model_x_failure_mode_matrix} rowKey="product_model" columnKey="failure_mode" title="Model × Failure Mode" />
      <BarChart data={data.component_trends} labelKey="component" valueKey="count" title="Component Failure Distribution" />
      {data.failure_trends && <LineChart data={data.failure_trends} xKey="period" yKey="failure_count" title="Failure Trend Over Time" />}
    </div>
    <div className="card"><h2 style={{ marginTop: 0 }}>Model × Failure Mode Detail</h2><table><thead><tr><th>Product model</th><th>Failure mode</th><th>Count</th></tr></thead><tbody>{data.model_x_failure_mode_matrix.map((r, i) => <tr key={i}><td>{r.product_model}</td><td>{r.failure_mode}</td><td>{r.count}</td></tr>)}</tbody></table></div>
  </Layout>
}
