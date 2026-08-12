import React from 'react'

export function BarChart({ data = [], labelKey, valueKey = 'count', title, limit = 8 }) {
  const rows = [...data].filter(r => Number.isFinite(Number(r[valueKey]))).slice(0, limit)
  const max = Math.max(...rows.map(r => Number(r[valueKey])), 1)
  return <div className="chart-card">
    {title && <h3>{title}</h3>}
    <div className="bar-chart">
      {rows.map((r, i) => <div className="bar-row" key={`${r[labelKey]}-${i}`}>
        <span className="bar-label" title={r[labelKey]}>{r[labelKey] ?? 'UNKNOWN'}</span>
        <div className="bar-track"><div className="bar-fill" style={{ width: `${(Number(r[valueKey]) / max) * 100}%` }} /></div>
        <span className="bar-value">{r[valueKey]}</span>
      </div>)}
      {!rows.length && <div className="empty-chart">No data available</div>}
    </div>
  </div>
}

export function LineChart({ data = [], xKey, yKey = 'count', title }) {
  const rows = data.filter(r => Number.isFinite(Number(r[yKey]))).slice(-30)
  const width = 720, height = 220, pad = 28
  const max = Math.max(...rows.map(r => Number(r[yKey])), 1)
  const points = rows.map((r, i) => {
    const x = pad + (rows.length <= 1 ? 0 : (i / (rows.length - 1)) * (width - pad * 2))
    const y = height - pad - (Number(r[yKey]) / max) * (height - pad * 2)
    return `${x},${y}`
  }).join(' ')
  return <div className="chart-card">
    {title && <h3>{title}</h3>}
    {rows.length ? <div className="line-wrap"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title || 'Trend chart'}>
      <line x1={pad} y1={height-pad} x2={width-pad} y2={height-pad} className="chart-axis" />
      <polyline points={points} className="line-path" fill="none" />
      {rows.map((r, i) => { const [x,y] = points.split(' ')[i].split(','); return <circle key={i} cx={x} cy={y} r="3" className="line-dot" /> })}
    </svg><div className="line-labels"><span>{String(rows[0][xKey]).slice(0,10)}</span><span>{String(rows[rows.length-1][xKey]).slice(0,10)}</span></div></div> : <div className="empty-chart">No trend data available</div>}
  </div>
}

export function DonutChart({ data = [], labelKey, valueKey = 'count', title }) {
  const total = data.reduce((s, r) => s + Number(r[valueKey] || 0), 0)
  let offset = 0
  const radius = 42, circumference = 2 * Math.PI * radius
  return <div className="chart-card donut-card">
    {title && <h3>{title}</h3>}
    {total ? <div className="donut-layout"><svg viewBox="0 0 120 120" className="donut"><circle cx="60" cy="60" r={radius} className="donut-base" />{data.map((r,i) => { const pct=Number(r[valueKey]||0)/total; const dash=pct*circumference; const el=<circle key={i} cx="60" cy="60" r={radius} className="donut-segment" strokeDasharray={`${dash} ${circumference-dash}`} strokeDashoffset={-offset} />; offset += dash; return el })}<text x="60" y="64" textAnchor="middle" className="donut-total">{total}</text></svg><div className="legend">{data.map((r,i)=><div key={i}><span className="legend-dot" style={{ opacity: 1 - i*0.12 }} />{r[labelKey] ?? 'UNKNOWN'} <b>{r[valueKey]}</b></div>)}</div></div> : <div className="empty-chart">No distribution data</div>}
  </div>
}

export function Matrix({ data = [], rowKey, columnKey, valueKey = 'count', title }) {
  const rows = [...new Set(data.map(r => r[rowKey]))]
  const cols = [...new Set(data.map(r => r[columnKey]))]
  return <div className="chart-card"><h3>{title}</h3><div className="matrix-scroll"><table className="matrix"><thead><tr><th>{rowKey}</th>{cols.map(c=><th key={c}>{c ?? 'UNKNOWN'}</th>)}</tr></thead><tbody>{rows.map(row=><tr key={row}><th>{row ?? 'UNKNOWN'}</th>{cols.map(col=>{const hit=data.find(r=>r[rowKey]===row&&r[columnKey]===col);return <td key={col}>{hit?.[valueKey] ?? 0}</td>})}</tr>)}</tbody></table></div></div>
}
