import { CheckCircle2, AlertTriangle, AlertCircle } from 'lucide-react'

/**
 * Indicador de estado compacto para el sistema de alertas.
 * Máximo ~44px de alto. Cambia automáticamente según red/yellow/green.
 *
 * Props:
 *   red    {number}  — estudiantes con alerta roja
 *   yellow {number}  — estudiantes con alerta amarilla
 *   green  {number}  — estudiantes sin alertas
 *   onViewCritical {function} — callback para "Ver críticos"
 */
export default function AlertStatusPill({ red = 0, yellow = 0, green = 0, onViewCritical }) {
  // Determinar nivel dominante
  const level = red > 0 ? 'red' : yellow > 0 ? 'yellow' : 'green'

  const styles = {
    red: {
      bg: '#fff5f5',
      border: '#fecaca',
      iconColor: '#dc2626',
      Icon: AlertCircle,
      text: `${red} estudiante${red !== 1 ? 's' : ''} requiere${red !== 1 ? 'n' : ''} atención inmediata`,
    },
    yellow: {
      bg: '#fffbeb',
      border: '#fde68a',
      iconColor: '#d97706',
      Icon: AlertTriangle,
      text: `${yellow} estudiante${yellow !== 1 ? 's' : ''} requiere${yellow !== 1 ? 'n' : ''} seguimiento`,
    },
    green: {
      bg: '#f0fdf4',
      border: '#bbf7d0',
      iconColor: '#16a34a',
      Icon: CheckCircle2,
      text: 'Todos los estudiantes sin alertas activas',
    },
  }

  const { bg, border, iconColor, Icon, text } = styles[level]

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '0.75rem',
      padding: '0 1rem',
      height: 44,
      background: bg,
      border: `1px solid ${border}`,
      borderRadius: 'var(--radius-lg)',
      marginBottom: '1.25rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Icon size={15} style={{ color: iconColor, flexShrink: 0 }} />
        <span style={{
          fontSize: '0.875rem',
          fontWeight: 500,
          color: 'var(--color-ink-700)',
          lineHeight: 1,
        }}>
          {text}
        </span>
        {level !== 'green' && green > 0 && (
          <span style={{
            fontSize: '0.75rem',
            color: 'var(--color-ink-400)',
            marginLeft: '0.25rem',
          }}>
            · {green} sin novedades
          </span>
        )}
      </div>

      {level !== 'green' && onViewCritical && (
        <button
          onClick={onViewCritical}
          style={{
            fontSize: '0.8125rem',
            fontWeight: 500,
            color: level === 'red' ? '#dc2626' : '#d97706',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '0.25rem 0',
            whiteSpace: 'nowrap',
            flexShrink: 0,
          }}
        >
          Ver críticos →
        </button>
      )}
    </div>
  )
}
