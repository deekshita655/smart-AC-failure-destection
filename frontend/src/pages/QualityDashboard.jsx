import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import Layout from '../components/Layout'
import { BarChart, LineChart, DonutChart } from '../components/AnalyticsCharts'

export default function QualityDashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => { api('/analytics/quality/fix-history').then(setData).catch(e=>setError(e.message)) }, [])
  if (error) return <Layout><div className="error-box">{error}</div></Layout>
  if (!data) return <Layout><p>Loading quality analytics…</p></Layout>
  return <Layout>
    <h1>Quality Analytics</h1><p className="subtitle">Repair quality, recurring fixes, severity and failure-to-fix patterns.</p>
    <div className="chart-grid"><BarChart data={data.most_common_fixes} labelKey="fix_text" title="Most Common Fixes" /><BarChart data={data.components_requiring_frequent_repair} labelKey="component" title="Components Requiring Repair" /></div>
    <div className="chart-grid"><LineChart data={data.repair_trend} xKey="date" title="Repair Trend Over Time" /><DonutChart data={data.severity_distribution} labelKey="severity" title="Severity Distribution" /></div>
    <div className="card"><h2>Repair Records</h2><table><thead><tr><th>Fix</th><th>Count</th></tr></thead><tbody>{data.most_common_fixes.map((r,i)=><tr key={i}><td>{r.fix_text}</td><td>{r.count}</td></tr>)}</tbody></table></div>
  </Layout>
}
