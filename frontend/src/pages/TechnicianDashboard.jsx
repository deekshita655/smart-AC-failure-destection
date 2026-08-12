import React, { useState } from 'react'
import { api } from '../api/client'
import Layout from '../components/Layout'

function LineChart({ data, valueKey, labelKey, label }) {
  if (!data?.length) return <div className="empty-chart">No historical {label?.toLowerCase() || 'data'} available</div>
  const width = 680, height = 230
  const values = data.map(d => Number(d[valueKey]) || 0), max = Math.max(...values, 1), min = Math.min(...values, 0)
  const range = Math.max(max - min, 1)
  const points = data.map((d, i) => {
    const x = 35 + (i * (width - 60)) / Math.max(data.length - 1, 1)
    const y = height - 35 - ((Number(d[valueKey]) - min) / range) * (height - 65)
    return { x, y, value: d[valueKey], label: d[labelKey] }
  })
  return <div className="chart-wrap"><svg viewBox={`0 0 ${width} ${height}`} className="chart" role="img" aria-label={`${label} history`}>
    <polyline points={points.map(p => `${p.x},${p.y}`).join(' ')} fill="none" className="chart-line" />
    {points.map((p, i) => <g key={i}><circle cx={p.x} cy={p.y} r="4" className="chart-point" /><text x={p.x} y={height - 12} textAnchor="middle" className="chart-label">{String(p.label).slice(0, 10)}</text><text x={p.x} y={p.y - 9} textAnchor="middle" className="chart-value">{Number(p.value).toFixed(1)}</text></g>)}
  </svg></div>
}

export default function TechnicianDashboard() {
  const [identifier, setIdentifier] = useState('DEV-90612')
  const [device, setDevice] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [error, setError] = useState(null)
  const [ticketId, setTicketId] = useState('')
  const [symptomText, setSymptomText] = useState('')
  const [fixText, setFixText] = useState('')
  const [severity, setSeverity] = useState('MEDIUM')
  const [ticket, setTicket] = useState(null)
  const [aiResult, setAiResult] = useState(null)
  const [comparison, setComparison] = useState(null)
  const [chatMsg, setChatMsg] = useState('')
  const [chatLog, setChatLog] = useState([])

  async function lookupDevice() {
    setError(null)
    try {
      const data = await api('/devices/lookup', { method: 'POST', body: { identifier, identifier_type: 'device_id' } })
      setDevice(data.device)
      setAnalytics(await api(`/analytics/devices/${data.device.device_id}`))
    } catch (e) { setError(e.message) }
  }

  async function createTicket() {
    setError(null)
    try {
      const newTicketId = ticketId || `TCK-${Date.now()}`
      const data = await api('/service-tickets', { method: 'POST', body: {
        ticket_id: newTicketId, device_id: device.device_id, date: new Date().toISOString(),
        symptom_text: symptomText, fix_text: fixText, severity,
      } })
      setTicket(data); setTicketId(newTicketId)
    } catch (e) { setError(e.message) }
  }

  async function analyzeTicket() {
    setError(null)
    try {
      const data = await api(`/service-tickets/${ticket.ticket_id}/analyze`, { method: 'POST' })
      setAiResult(data)
      setComparison(await api(`/service-tickets/${ticket.ticket_id}/comparison`))
    } catch (e) { setError(e.message) }
  }

  async function sendChat() {
    if (!chatMsg.trim()) return
    const userMsg = chatMsg
    setChatLog(prev => [...prev, { role: 'user', text: userMsg }]); setChatMsg('')
    try {
      const data = await api('/chat/message', { method: 'POST', body: { message: userMsg, device_id: device?.device_id, ticket_id: ticket?.ticket_id } })
      setChatLog(prev => [...prev, { role: 'bot', text: data.reply }])
    } catch (e) { setChatLog(prev => [...prev, { role: 'bot', text: `[${e.code || 'ERROR'}] ${e.message}` }]) }
  }

  return <Layout>
    <h1>Technician Service Console</h1>
    <p className="subtitle">Identify a device, review its history, log a service report, and run AI failure analysis.</p>
    {error && <div className="error-box">{error}</div>}

    <div className="card">
      <h2 style={{ marginTop: 0 }}>1. Device Identification</h2>
      <label>Device identifier (manual entry — simulates barcode scan)</label>
      <input value={identifier} onChange={e => setIdentifier(e.target.value)} />
      <button onClick={lookupDevice}>Look up device</button>
      {device && <div className="grid" style={{ marginTop: 16 }}>
        <div><div className="stat">{device.product_model}</div><div className="stat-label">Product model</div></div>
        <div><div className="stat">{device.serial_range}</div><div className="stat-label">Serial range</div></div>
        <div><div className="stat">{device.status}</div><div className="stat-label">Status</div></div>
      </div>}
    </div>

    {analytics && <div className="card">
      <h2 style={{ marginTop: 0 }}>Device-Specific Analytics</h2>
      <div className="grid">
        <div><div className="stat">{analytics.total_service_tickets}</div><div className="stat-label">Total tickets</div></div>
        {analytics.health && <div><div className="stat">{analytics.health.health_score}</div><div className="stat-label">Current health score</div></div>}
        {analytics.health && <div><div className="stat">{analytics.health.anomaly_score}</div><div className="stat-label">Current anomaly score</div></div>}
      </div>
      <h2>Health Score History</h2>
      <LineChart data={analytics.health_history} valueKey="health_score" labelKey="timestamp" label="Health score" />
      <h2>Ticket Trend</h2>
      <LineChart data={analytics.ticket_trends} valueKey="count" labelKey="period" label="Ticket count" />
      {analytics.anomaly_history?.length > 0 && <><h2>Anomaly Score History</h2><LineChart data={analytics.anomaly_history} valueKey="anomaly_score" labelKey="detected_at" label="Anomaly score" /></>}
      <h2>Recent Tickets</h2>
      <table><thead><tr><th>Ticket</th><th>Date</th><th>Symptom</th><th>Status</th></tr></thead>
        <tbody>{analytics.recent_tickets.map(t => <tr key={t.ticket_id}><td>{t.ticket_id}</td><td>{new Date(t.date).toLocaleDateString()}</td><td>{t.symptom_text}</td><td>{t.status}</td></tr>)}</tbody>
      </table>
    </div>}

    {device && <div className="card">
      <h2 style={{ marginTop: 0 }}>2. Create Service Report</h2>
      <label>Ticket ID (optional, auto-generated if blank)</label><input value={ticketId} onChange={e => setTicketId(e.target.value)} />
      <label>Symptom</label><textarea rows={2} value={symptomText} onChange={e => setSymptomText(e.target.value)} />
      <label>Fix applied (optional)</label><textarea rows={2} value={fixText} onChange={e => setFixText(e.target.value)} />
      <label>Severity</label><select value={severity} onChange={e => setSeverity(e.target.value)}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select>
      <button onClick={createTicket} disabled={!symptomText}>Submit report</button>
    </div>}

    {ticket && <div className="card">
      <h2 style={{ marginTop: 0 }}>3. AI Analysis</h2><button className="amber" onClick={analyzeTicket}>Run AI analysis</button>
      {aiResult && <div style={{ marginTop: 14 }}><div className="grid">
        <div><div className="stat">{aiResult.predicted_failure_mode || '—'}</div><div className="stat-label">Failure mode</div></div>
        <div><div className="stat">{aiResult.predicted_component || '—'}</div><div className="stat-label">Component</div></div>
        <div><div className="stat">{aiResult.predicted_department || '—'}</div><div className="stat-label">Department</div></div>
        <div><div className="stat">{aiResult.confidence != null ? (aiResult.confidence * 100).toFixed(0) + '%' : '—'}</div><div className="stat-label">Confidence</div></div>
      </div>
      {aiResult.low_confidence && <div className="badge warn" style={{ marginTop: 10 }}>LOW CONFIDENCE — verify manually</div>}
      <p style={{ fontSize: 13, marginTop: 12 }}><strong>Suggested action:</strong> {aiResult.suggested_action || 'N/A'}</p>
      {comparison && <p style={{ fontSize: 13 }}><strong>Technician vs AI:</strong> {comparison.overall_match === null ? 'No technician diagnosis entered for comparison.' : comparison.overall_match ? <span className="badge ok">MATCH</span> : <span className="badge danger">MISMATCH</span>}</p>}
      </div>}
    </div>}

    {device && <div className="card">
      <h2 style={{ marginTop: 0 }}>Assistant (Gemini)</h2><div className="chat-window">{chatLog.map((m, i) => <div key={i} className={`chat-msg ${m.role}`}>{m.text}</div>)}</div>
      <div style={{ display: 'flex', gap: 8 }}><input value={chatMsg} onChange={e => setChatMsg(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendChat()} placeholder="Ask about this device or ticket..." style={{ marginBottom: 0 }} /><button onClick={sendChat}>Send</button></div>
    </div>}
  </Layout>
}
