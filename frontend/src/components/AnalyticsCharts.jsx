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
  const width = 720, height = 250, left = 44, right = 18, top = 20, bottom = 38
  const plotWidth = width - left - right
  const plotHeight = height - top - bottom
  const max = Math.max(...rows.map(r => Number(r[yKey])), 1)
  const points = rows.map((r, i) => {
    const x = left + (rows.length <= 1 ? plotWidth / 2 : (i / (rows.length - 1)) * plotWidth)
    const y = top + plotHeight - (Number(r[yKey]) / max) * plotHeight
    return { x, y, value: Number(r[yKey]), label: String(r[xKey]).slice(5, 10) }
  })
  const polyline = points.map(p => `${p.x},${p.y}`).join(' ')
  const area = points.length > 1
    ? `${points[0].x},${top + plotHeight} ${polyline} ${points[points.length - 1].x},${top + plotHeight}`
    : ''

  return <div className="chart-card">
    {title && <h3>{title}</h3>}
    {rows.length ? <div className="line-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title || 'Trend chart'}>
        {[0, 0.5, 1].map((ratio, i) => {
          const y = top + plotHeight - ratio * plotHeight
          const value = Math.round(max * ratio)
          return <g key={i}>
            <line x1={left} y1={y} x2={width-right} y2={y} className="chart-gridline" />
            <text x={left-8} y={y+4} textAnchor="end" className="chart-y-label">{value}</text>
          </g>
        })}
        {area && <polygon points={area} className="line-area" />}
        <polyline points={polyline} className="line-path" fill="none" />
        {points.map((p, i) => <g key={i}>
          <circle cx={p.x} cy={p.y} r="5" className="line-dot" />
          {p.value > 0 && <text x={p.x} y={p.y-10} textAnchor="middle" className="chart-point-label">{p.value}</text>}
          <text x={p.x} y={height-14} textAnchor="middle" className="chart-x-label">{p.label}</text>
        </g>)}
      </svg>
    </div> : <div className="empty-chart">No trend data available</div>}
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
  return <div className="chart-card"><h3>{title}</h3><div className="matrix-scroll"><table className="matrix"><thead><tr><th>{rowKey}</th>{cols.map(c=><th key={c}>{c ?? 'UNKNOWN'}</th>)}</tr></thead><tbody>{rows.map(row=><tr key={row}><th>{row ?? 'UNKNOWN'}</th>{cols.map(col=>{const hit=data.find(r => r[rowKey]===row&&r[columnKey]===col);return <td key={col}>{hit?.[valueKey] ?? 0}</td>})}</tr>)}</tbody></table></div></div>
}
