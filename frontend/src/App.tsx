import { type FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { io, Socket } from 'socket.io-client'
import './App.css'
import {
  createJob,
  fetchHealth,
  getApiBaseUrl,
  getWsUrl,
  sendEcho,
  type HealthResponse,
} from './lib/backend'

type EventEntry = {
  id: string
  label: string
  timestamp: string
  payload: unknown
}

const defaultEcho = () =>
  JSON.stringify(
    {
      message: 'hello from LOCAL_3/frontend',
      branch: 'main',
      at: new Date().toISOString(),
    },
    null,
    2,
  )

const badgeCopy: Record<string, string> = {
  ok: 'Healthy',
  error: 'Failing',
  skipped: 'Idle',
}

const randomId = () => `evt-${Date.now()}-${Math.random().toString(16).slice(2)}`

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthLoading, setHealthLoading] = useState(false)
  const [healthError, setHealthError] = useState<string | null>(null)
  const [jobStage, setJobStage] = useState('deploy')
  const [jobNote, setJobNote] = useState('Smoke test via UI')
  const [jobResult, setJobResult] = useState<string>('')
  const [echoBody, setEchoBody] = useState(() => defaultEcho())
  const [echoResult, setEchoResult] = useState('')
  const [events, setEvents] = useState<EventEntry[]>([])

  const apiBase = useMemo(() => getApiBaseUrl(), [])
  const wsUrl = useMemo(() => getWsUrl(), [])

  const appendEvent = useCallback((label: string, payload: unknown) => {
    setEvents((prev) => {
      const next: EventEntry = {
        id: randomId(),
        label,
        payload,
        timestamp: new Date().toISOString(),
      }
      return [next, ...prev].slice(0, 40)
    })
  }, [])

  const refreshHealth = useCallback(async () => {
    setHealthLoading(true)
    setHealthError(null)
    try {
      const data = await fetchHealth()
      setHealth(data)
      appendEvent('api:health', data)
    } catch (err) {
      setHealthError(err instanceof Error ? err.message : 'Unable to load health')
    } finally {
      setHealthLoading(false)
    }
  }, [appendEvent])

  useEffect(() => {
    refreshHealth()
  }, [refreshHealth])

  useEffect(() => {
    let socket: Socket | undefined

    try {
      socket = io(wsUrl, {
        transports: ['websocket'],
        autoConnect: true,
      })
    } catch (err) {
      appendEvent('socket:error', err instanceof Error ? { message: err.message } : err)
      return
    }

    socket.on('connect', () => appendEvent('socket:connect', { id: socket?.id }))
    socket.on('disconnect', () => appendEvent('socket:disconnect', { id: socket?.id }))
    socket.on('connect_error', (error) => appendEvent('socket:error', { message: error.message }))

    socket.on('health:update', (payload) => {
      appendEvent('health:update', payload)
      setHealth((prev) => {
        const nextTimestamp = payload.timestamp ?? new Date().toISOString()
        const nextDatabases = payload.databases ?? payload
        if (!prev) {
          return {
            service: 'auto-deploy-lab',
            version: 'socket-stream',
            timestamp: nextTimestamp,
            counters: {},
            databases: nextDatabases,
          }
        }
        return {
          ...prev,
          timestamp: nextTimestamp,
          databases: nextDatabases,
        }
      })
    })

    socket.on('jobs:created', (payload) => appendEvent('jobs:created', payload))
    socket.on('jobs:update', (payload) => appendEvent('jobs:update', payload))

    return () => {
      socket?.disconnect()
    }
  }, [appendEvent, wsUrl])

  const handleCreateJob = async (event: FormEvent) => {
    event.preventDefault()
    try {
      const job = await createJob({
        type: `deploy:${jobStage}`,
        data: {
          note: jobNote,
          initiated_by: 'local-3/frontend',
        },
      })
      setJobResult(`Job ${job.id} queued as ${job.status}`)
      appendEvent('jobs:api', job)
    } catch (err) {
      setJobResult(err instanceof Error ? err.message : 'Failed to create job')
    }
  }

  const handleEcho = async () => {
    try {
      const parsed = JSON.parse(echoBody)
      const response = await sendEcho(parsed)
      setEchoResult(JSON.stringify(response, null, 2))
      appendEvent('api:echo', response)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Invalid request payload'
      setEchoResult(message)
    }
  }

  const statusEntries = Object.entries(health?.databases ?? {})

  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">LOCAL_3 · Auto-deploy test bench</p>
          <h1>
            {health?.service ?? 'Auto Deployment Lab'} <span>v{health?.version ?? '—'}</span>
          </h1>
          <p className="subtitle">
            Trigger jobs, inspect database connectors, and monitor real-time events fed by the Flask backend.
          </p>
        </div>
        <div className="connectivity">
          <div>
            <p className="label">API base</p>
            <code>{apiBase}</code>
          </div>
          <div>
            <p className="label">WebSocket</p>
            <code>{wsUrl || 'Disabled'}</code>
          </div>
        </div>
      </header>

      <main className="grid">
        <section className="panel">
          <div className="panel__header">
            <h2>Service health</h2>
            <div className="panel__actions">
              <button onClick={refreshHealth} disabled={healthLoading}>
                {healthLoading ? 'Refreshing…' : 'Refresh'}
              </button>
            </div>
          </div>
          {healthError && <p className="panel__error">{healthError}</p>}
          {health && (
            <>
              <div className="stats">
                <div>
                  <p className="label">Last checked</p>
                  <p className="stat">{new Date(health.timestamp).toLocaleString()}</p>
                </div>
                {Object.entries(health.counters).map(([key, value]) => (
                  <div key={key}>
                    <p className="label">{key}</p>
                    <p className="stat">{value}</p>
                  </div>
                ))}
              </div>
              <div className="db-grid">
                {statusEntries.map(([name, status]) => (
                  <article key={name} className="db-card">
                    <header>
                      <div>
                        <p className="label">connector</p>
                        <h3>{name}</h3>
                      </div>
                      <span className={`badge badge--${status.status}`}>
                        {badgeCopy[status.status] ?? status.status}
                      </span>
                    </header>
                    <dl>
                      {status.latency_ms !== undefined && (
                        <div>
                          <dt>Latency</dt>
                          <dd>{status.latency_ms} ms</dd>
                        </div>
                      )}
                      {status.error && (
                        <div>
                          <dt>Error</dt>
                          <dd>{status.error}</dd>
                        </div>
                      )}
                      <div>
                        <dt>Checked</dt>
                        <dd>{status.checked_at ?? 'n/a'}</dd>
                      </div>
                    </dl>
                  </article>
                ))}
                {!statusEntries.length && <p>No connectors configured. Populate env vars to enable checks.</p>}
              </div>
            </>
          )}
        </section>

        <section className="panel">
          <div className="panel__header">
            <h2>Job simulator</h2>
          </div>
          <form className="job-form" onSubmit={handleCreateJob}>
            <label>
              Stage
              <select value={jobStage} onChange={(event) => setJobStage(event.target.value)}>
                <option value="deploy">deploy</option>
                <option value="migrate">migrate</option>
                <option value="rollback">rollback</option>
                <option value="smoke">smoke</option>
              </select>
            </label>
            <label>
              Note
              <input value={jobNote} onChange={(event) => setJobNote(event.target.value)} />
            </label>
            <button type="submit">Queue job</button>
          </form>
          {jobResult && <p className="panel__success">{jobResult}</p>}
        </section>

        <section className="panel">
          <div className="panel__header">
            <h2>Echo tester</h2>
          </div>
          <textarea value={echoBody} onChange={(event) => setEchoBody(event.target.value)} spellCheck={false} />
          <div className="panel__actions">
            <button type="button" onClick={handleEcho}>
              Send to /api/echo
            </button>
            <button type="button" className="ghost" onClick={() => setEchoBody(defaultEcho())}>
              Reset
            </button>
          </div>
          {echoResult && <pre className="panel__code">{echoResult}</pre>}
        </section>

        <section className="panel panel--wide">
          <div className="panel__header">
            <h2>Live event stream</h2>
            <p className="label">Showing last {events.length} events</p>
          </div>
          <ul className="event-feed">
            {events.map((entry) => (
              <li key={entry.id}>
                <div>
                  <p className="label">{entry.label}</p>
                  <p className="timestamp">{new Date(entry.timestamp).toLocaleTimeString()}</p>
                </div>
                <pre>{JSON.stringify(entry.payload, null, 2)}</pre>
              </li>
            ))}
            {!events.length && <p>No events yet. Kick off a job or wait for health broadcasts.</p>}
          </ul>
        </section>
      </main>
    </div>
  )
}

export default App
