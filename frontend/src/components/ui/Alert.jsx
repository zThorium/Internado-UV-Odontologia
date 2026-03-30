import { AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react'

export function AlertError({ children }) {
  if (!children) return null
  // Normalizar errores de Pydantic (array de objetos {msg, loc, ...})
  const message = Array.isArray(children)
    ? children.map(e => e?.msg || String(e)).join(', ')
    : typeof children === 'object'
      ? (children.msg || JSON.stringify(children))
      : children
  return (
    <div className="alert alert-error">
      <AlertCircle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
      <span>{message}</span>
    </div>
  )
}

export function AlertSuccess({ children }) {
  if (!children) return null
  return (
    <div className="alert alert-success">
      <CheckCircle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
      <span>{children}</span>
    </div>
  )
}

export function AlertWarn({ children }) {
  if (!children) return null
  return (
    <div className="alert alert-warn">
      <AlertTriangle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
      <span>{children}</span>
    </div>
  )
}
