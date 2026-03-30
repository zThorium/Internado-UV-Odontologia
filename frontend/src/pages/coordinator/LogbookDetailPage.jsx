import { useEffect, useState } from 'react'
import { useNavigate, useParams, useLocation } from 'react-router-dom'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import { ArrowLeft, BookOpen, CheckCircle, Stethoscope, Heart, TrendingUp, Minus, TrendingDown } from 'lucide-react'

const STATUS_META = {
  draft:     { label: 'Borrador',  cls: 'badge-gray' },
  submitted: { label: 'Enviada',   cls: 'badge-blue' },
  reviewed:  { label: 'Revisada',  cls: 'badge-green' },
}

const WELLBEING_META = {
  good:      { label: 'Bien',     cls: 'badge-green',  Icon: TrendingUp },
  regular:   { label: 'Regular',  cls: 'badge-yellow', Icon: Minus },
  difficult: { label: 'Difícil',  cls: 'badge-red',    Icon: TrendingDown },
}

export default function LogbookDetailPage() {
  const { entryId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [entry, setEntry] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [marking, setMarking] = useState(false)
  const [markError, setMarkError] = useState(null)

  // El nombre del estudiante puede venir por state de navegación (evita un fetch extra)
  const studentName = location.state?.studentName

  useEffect(() => {
    api.get(`/logbook/entries/${entryId}`)
      .then(({ data }) => setEntry(data))
      .catch(() => setError('No se pudo cargar la entrada'))
      .finally(() => setLoading(false))
  }, [entryId])

  const handleMarkReviewed = async () => {
    setMarkError(null)
    setMarking(true)
    try {
      const { data } = await api.patch(`/logbook/entries/${entryId}/status`, { status: 'reviewed' })
      setEntry(data)
    } catch (err) {
      setMarkError(err.response?.data?.detail || 'Error al actualizar el estado')
    } finally {
      setMarking(false)
    }
  }

  if (loading) return <Spinner />

  if (error) {
    return (
      <div className="page-enter">
        <AlertError>{error}</AlertError>
        <button onClick={() => navigate(-1)} className="btn btn-secondary">
          <ArrowLeft size={15} /> Volver
        </button>
      </div>
    )
  }

  const statusMeta = STATUS_META[entry.status] || { label: entry.status, cls: 'badge-gray' }
  const wellbeingMeta = entry.wellbeing_status ? WELLBEING_META[entry.wellbeing_status] : null
  const totalProcedures = entry.procedures?.reduce((sum, p) => sum + p.quantity, 0) ?? 0

  return (
    <div className="page-enter" style={{ maxWidth: 720 }}>
      {/* Volver */}
      <button
        onClick={() => navigate(-1)}
        className="btn btn-ghost btn-sm"
        style={{ marginBottom: '1.25rem', marginLeft: '-0.5rem' }}
      >
        <ArrowLeft size={15} /> Volver a bitácoras
      </button>

      {/* Encabezado */}
      <div style={{ marginBottom: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
          <div>
            <h2 className="section-title" style={{ marginBottom: '0.25rem' }}>
              Semana {entry.week_number}
            </h2>
            <p className="section-subtitle" style={{ margin: 0 }}>
              {studentName ? `${studentName} · ` : ''}{entry.week_start_date}
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', flexShrink: 0 }}>
            <span className={`badge ${statusMeta.cls}`}>{statusMeta.label}</span>
            {entry.status === 'submitted' && (
              <button
                onClick={handleMarkReviewed}
                disabled={marking}
                className="btn btn-primary btn-sm"
              >
                <CheckCircle size={14} />
                {marking ? 'Guardando...' : 'Marcar como revisada'}
              </button>
            )}
          </div>
        </div>
        <AlertError>{markError}</AlertError>
      </div>

      {/* Tarjeta de resumen */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
        {/* Bienestar */}
        <div className="card" style={{ padding: '1.25rem 1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: 40, height: 40, borderRadius: '50%',
            background: 'var(--color-earth-100)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <Heart size={18} style={{ color: 'var(--color-earth-600)' }} />
          </div>
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-ink-400)', margin: '0 0 0.25rem' }}>Estado de bienestar</p>
            {wellbeingMeta ? (
              <span className={`badge ${wellbeingMeta.cls}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                <wellbeingMeta.Icon size={11} strokeWidth={2.5} />
                {wellbeingMeta.label}
              </span>
            ) : (
              <span style={{ fontSize: '0.875rem', color: 'var(--color-ink-400)' }}>No registrado</span>
            )}
          </div>
        </div>

        {/* Procedimientos */}
        <div className="card" style={{ padding: '1.25rem 1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: 40, height: 40, borderRadius: '50%',
            background: 'var(--color-uv-50)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <Stethoscope size={18} style={{ color: 'var(--color-uv-600)' }} />
          </div>
          <div>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-ink-400)', margin: '0 0 0.25rem' }}>Procedimientos</p>
            <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', fontWeight: 500, color: 'var(--color-uv-700)', margin: 0, lineHeight: 1 }}>
              {totalProcedures}
              <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.8125rem', fontWeight: 400, color: 'var(--color-ink-400)', marginLeft: '0.375rem' }}>
                en {entry.procedures?.length ?? 0} tipo{(entry.procedures?.length ?? 0) !== 1 ? 's' : ''}
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* Lista de procedimientos */}
      <div className="card" style={{ overflow: 'hidden' }}>
        <div style={{
          padding: '0.875rem 1.5rem',
          borderBottom: '1px solid var(--color-ink-100)',
          display: 'flex', alignItems: 'center', gap: '0.5rem',
        }}>
          <BookOpen size={14} style={{ color: 'var(--color-uv-500)' }} />
          <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-ink-600)' }}>
            Procedimientos registrados
          </span>
        </div>

        {entry.procedures?.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-ink-400)', fontSize: '0.875rem' }}>
            Sin procedimientos registrados
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Procedimiento</th>
                <th>Descripción</th>
                <th style={{ textAlign: 'right' }}>Cantidad</th>
              </tr>
            </thead>
            <tbody className="stagger">
              {entry.procedures.map((proc) => (
                <tr key={proc.id}>
                  <td style={{ fontWeight: 500 }}>{proc.name}</td>
                  <td style={{ color: 'var(--color-ink-500)', fontSize: '0.875rem' }}>
                    {proc.description || <span style={{ color: 'var(--color-ink-300)', fontStyle: 'italic' }}>Sin descripción</span>}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <span className="badge badge-blue">{proc.quantity}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
