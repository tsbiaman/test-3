const DEFAULT_API_BASE = 'http://localhost:8080/api'
const DEFAULT_WS_URL = 'http://localhost:8080'

const trimTrailingSlash = (value?: string | null) =>
  (value ?? '').replace(/\/$/, '')

const apiBase = trimTrailingSlash(import.meta.env.VITE_API_BASE_URL) || DEFAULT_API_BASE
const wsOverride = trimTrailingSlash(import.meta.env.VITE_WS_URL)
const wsBase = wsOverride || apiBase.replace(/\/api$/, '') || DEFAULT_WS_URL

const withBase = (path: string) => {
  const normalized = path.startsWith('/') ? path : `/${path}`
  return `${apiBase}${normalized}`
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(withBase(path), {
    headers: {
      Accept: 'application/json',
      ...init?.headers,
    },
    ...init,
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(`Request failed (${response.status}): ${message}`)
  }

  return response.json() as Promise<T>
}

export type StatusState = 'ok' | 'error' | 'skipped'

export type DatabaseStatus = {
  status: StatusState
  checked_at?: string
  latency_ms?: number
  error?: string
  [key: string]: unknown
}

export type HealthResponse = {
  service: string
  version: string
  timestamp: string
  counters: Record<string, number>
  databases: Record<string, DatabaseStatus>
}

export type JobRequest = {
  type?: string
  data?: Record<string, unknown>
}

export type JobResponse = {
  id: string
  type: string
  status: string
  created_at: string
  payload: Record<string, unknown>
}

export type EchoResponse = {
  received: Record<string, unknown>
  metadata: Record<string, unknown>
}

export const getApiBaseUrl = () => apiBase

export const getWsUrl = () => wsBase || DEFAULT_WS_URL

export const fetchHealth = () => requestJson<HealthResponse>('/health')

export const fetchConfig = () => requestJson<Record<string, unknown>>('/config')

export const createJob = (job: JobRequest = {}) =>
  requestJson<JobResponse>('/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: job.type ?? 'deploy:smoke-test',
      data: job.data ?? {},
    }),
  })

export const sendEcho = (payload: Record<string, unknown>) =>
  requestJson<EchoResponse>('/echo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
