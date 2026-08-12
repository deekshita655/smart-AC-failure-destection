import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import Layout from '../components/Layout'

function BarChart({ data, labelKey, valueKey }) {
  if (!data?.length) return <div className="empty-chart">No data available</div>
  const max = Math.max(...data.map(d => Number(d[valueKey]) || 0), 1), width = 620, height = 230
  return <div className="chart-wrap"><svg viewBox={`0 0 ${width} ${height}`} className="chart" role="img" aria-label="Quality analytics bar chart">
    {data.slice(0, 12).map((d, i) => {
      const n = Math.min(data.length, 12), x = 25 + i * ((width - 45) / n) + 4
      const barWidth = Math.max(18, Math.min(42, (width - 60) / n - 8)), h = ((height - 50) * (Number(d[valueKey]) || 0)) / max
      return <g key={i}><rect x={x} y={height - 30 - h} width={barWidth} height={h} rx="4" className="chart-bar" /><text x={x + barWidth / 2} y={height - 10} textAnchor="middle" className="chart-label">{String(d[labelKey]).slice(0, 9)}</text><text x={x + barWidth / 2} y={height - 35 - h} textAnchor="middle" className="chart-value">{d[valueKey]}</text></g>
    })}
  </svg></div>
}

export default function QualityDashboard() {
  const [data, setData] = useState(null), [error, setError] = useState(null)
  useEffect(() => { api('/analytics/quality/fix-history').then(setData).catch(e => setError(e.message)) }, [])
  if (error) return <Layout><div className="error-box">{error}</div></Layout>
  if (!data) return <Layout><p>Loading…</p></Layout>

  return <Layout>
    <h1>Quality Analytics</h1>
    <p className="subtitle">Fix history, repeated repairs, and severity distribution.</p>

    <div className="card"><h2>Most Common Fixes</h2><BarChart data={data.most_common_fixes} labelKey="fix_text" valueKey="count" />
      <table><thead><tr><th>Fix</th><th>Count</th></tr></thead><tbody>{data.most_common_fixes.map((r, i) => <tr key={i}><td>{r.fix_text}</td><td>{r.count}</td></tr>)}</tbody></table>
    </div>

    <div className="card"><h2>Components Requiring Frequent Repair</h2><BarChart data={data.components_requiring_frequent_repair} labelKey="component" valueKey="count" />
      <table><thead><tr><th>Component</th><th>Count</th></tr></thead><tbody>{data.components_requiring_frequent_repair.map((r, i) => <tr key={i}><td>{r.component}</td><td>{r.count}</td></tr>)}</tbody></table>
    </div>

    <div className="card"><h2>Severity Distribution</h2><div className="grid">{data.severity_distribution.map((r, i) => <div key={i}><div className="stat">{r.count}</div><div className="stat-label">{r.severity}</div></div>)}</div></div>
  </Layout>
}
