import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { createPortal } from 'react-dom'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import EmptyState from '../../components/ui/EmptyState'
import { AlertError, AlertSuccess } from '../../components/ui/Alert'
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  ClipboardCheck,
  Eye,
  Minus,
  TrendingDown,
  TrendingUp,
  X,
} from 'lucide-react'

function periodLabelByWeek(weekNumber) {
  if (weekNumber >= 1 && weekNumber <= 13) return 'Semestre 1'
  if (weekNumber >= 14 && weekNumber <= 26) return 'Semestre 2'
  return 'Fuera de rango semestral'
}

const STATUS_META = {
  draft: { label: 'Borrador', cls: 'badge-gray' },
  submitted: { label: 'Enviada', cls: 'badge-blue' },
  reviewed: { label: 'Revisada', cls: 'badge-green' },
}

const WELLBEING_META = {
  good: { label: 'Bien', cls: 'badge-green', Icon: TrendingUp },
  regular: { label: 'Regular', cls: 'badge-yellow', Icon: Minus },
  difficult: { label: 'Difícil', cls: 'badge-red', Icon: TrendingDown },
}

function canTutorValidate(entry) {
  if (!entry || entry.tutor_validation) return false
  return entry.status === 'submitted' || entry.status === 'reviewed'
}

function LogbookEntryDetailModal({ entry, studentName, onClose, onValidate, validating }) {
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    const onEscape = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onEscape)
    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', onEscape)
    }
  }, [onClose])

  if (!entry) return null

  const statusMeta = STATUS_META[entry.status] || { label: entry.status, cls: 'badge-gray' }
  const wellbeingMeta = entry.wellbeing_status ? WELLBEING_META[entry.wellbeing_status] : null
  const totalQty = (entry.procedures || []).reduce((sum, p) => sum + (p.quantity || 0), 0)
  const showValidate = canTutorValidate(entry)

  return createPortal(
    <div
      className="modal-backdrop"
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(15, 31, 46, 0.6)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '1rem',
      }}
    >
      <div
        className="modal-content card"
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: 640,
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          margin: 'auto',
          padding: 0,
        }}
      >
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--color-ink-100)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '1rem',
          }}
        >
          <div>
            <h3 className="section-title" style={{ marginBottom: '0.25rem', fontSize: '1.25rem' }}>
              Semana {entry.week_number} · {periodLabelByWeek(entry.week_number)}
            </h3>
            <p className="section-subtitle" style={{ margin: 0 }}>
              {studentName} · Inicio {entry.week_start_date}
            </p>
          </div>
          <button type="button" className="btn btn-ghost btn-sm" onClick={onClose} aria-label="Cerrar">
            <X size={18} />
          </button>
        </div>

        <div style={{ padding: '1.25rem 1.5rem' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: '0.75rem',
              marginBottom: '1.25rem',
            }}
          >
            <div className="card" style={{ padding: '1rem' }}>
              <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-ink-400)' }}>Estado bitácora</p>
              <span className={`badge ${statusMeta.cls}`} style={{ marginTop: '0.5rem' }}>
                {statusMeta.label}
              </span>
            </div>
            <div className="card" style={{ padding: '1rem' }}>
              <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-ink-400)' }}>Bienestar reportado</p>
              {wellbeingMeta ? (
                <span
                  className={`badge ${wellbeingMeta.cls}`}
                  style={{ marginTop: '0.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                >
                  <wellbeingMeta.Icon size={11} />
                  {wellbeingMeta.label}
                </span>
              ) : (
                <p style={{ margin: '0.5rem 0 0', fontSize: '0.875rem', color: 'var(--color-ink-400)' }}>No registrado</p>
              )}
            </div>
            <div className="card" style={{ padding: '1rem' }}>
              <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-ink-400)' }}>Total procedimientos</p>
              <p style={{ margin: '0.35rem 0 0', fontFamily: 'var(--font-display)', fontSize: '1.35rem' }}>{totalQty}</p>
            </div>
          </div>

          <div className="card table-scroll" style={{ marginBottom: '1rem' }}>
            <div
              style={{
                padding: '0.75rem 1rem',
                borderBottom: '1px solid var(--color-ink-100)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <BookOpen size={14} style={{ color: 'var(--color-uv-500)' }} />
              <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>Procedimientos de la semana</span>
            </div>
            {(entry.procedures || []).length === 0 ? (
              <p style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--color-ink-400)', margin: 0 }}>
                Sin procedimientos registrados
              </p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Procedimiento</th>
                    <th>Descripción</th>
                    <th style={{ textAlign: 'right' }}>Cant.</th>
                  </tr>
                </thead>
                <tbody>
                  {entry.procedures.map((proc) => (
                    <tr key={proc.id}>
                      <td style={{ fontWeight: 500 }}>{proc.name}</td>
                      <td style={{ color: 'var(--color-ink-500)', fontSize: '0.875rem' }}>
                        {proc.description || '—'}
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

          {entry.tutor_validation && (
            <p style={{ fontSize: '0.875rem', color: 'var(--color-ok-text)', margin: '0 0 1rem' }}>
              <CheckCircle2 size={14} style={{ verticalAlign: 'middle', marginRight: '0.35rem' }} />
              Validada el{' '}
              {new Date(entry.tutor_validation.validated_at).toLocaleDateString('es-CL', {
                day: '2-digit',
                month: 'long',
                year: 'numeric',
              })}
            </p>
          )}

          {!showValidate && !entry.tutor_validation && entry.status === 'draft' && (
            <p style={{ fontSize: '0.875rem', color: 'var(--color-warn-text)', margin: 0 }}>
              Esta semana aún está en borrador. El estudiante debe enviarla antes de que puedas validarla.
            </p>
          )}
        </div>

        <div
          style={{
            padding: '1rem 1.5rem 1.25rem',
            borderTop: '1px solid var(--color-ink-100)',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '0.75rem',
            flexWrap: 'wrap',
          }}
        >
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Cerrar
          </button>
          {showValidate && (
            <button
              type="button"
              className="btn btn-primary"
              disabled={validating}
              onClick={() => onValidate(entry.id)}
            >
              <CheckCircle2 size={15} />
              {validating ? 'Validando...' : 'Confirmar validación'}
            </button>
          )}
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default function LogbookValidationPage() {
  const { student_id } = useParams()
  const [searchParams] = useSearchParams()
  const studentName = searchParams.get('name') || 'Estudiante'
  const navigate = useNavigate()

  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [validatingId, setValidatingId] = useState(null)
  const [selectedEntry, setSelectedEntry] = useState(null)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const loadEntries = () => {
    setLoading(true)
    setError(null)
    api
      .get(`/logbook/tutor/students/${student_id}/entries`)
      .then(({ data }) => setEntries(data))
      .catch(() => setError('No fue posible cargar la bitácora de este estudiante.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadEntries()
  }, [student_id])

  const handleValidate = async (entryId) => {
    setValidatingId(entryId)
    setError(null)
    setSuccess(null)
    try {
      await api.post(`/logbook/entries/${entryId}/validate`)
      setSuccess('Entrada validada correctamente.')
      setSelectedEntry(null)
      loadEntries()
    } catch (validationError) {
      setError(validationError.response?.data?.detail || 'No fue posible validar la entrada.')
    } finally {
      setValidatingId(null)
    }
  }

  const summary = useMemo(() => {
    const total = entries.length
    const validated = entries.filter((entry) => entry.tutor_validation).length
    return {
      total,
      validated,
      pending: Math.max(0, total - validated),
    }
  }, [entries])

  if (loading) return <Spinner />

  return (
    <div className="page-enter">
      <button
        type="button"
        className="btn btn-ghost btn-sm"
        onClick={() => navigate('/tutor')}
        style={{ marginBottom: '1rem', marginLeft: '-0.5rem' }}
      >
        <ArrowLeft size={15} /> Volver
      </button>

      <div className="section-header">
        <div>
          <h2 className="section-title">Validación de bitácora</h2>
          <p className="section-subtitle">
            {studentName} · Revisa el detalle semanal antes de confirmar la validación
          </p>
        </div>
      </div>

      <div className="stagger stats-grid-3" style={{ marginBottom: '1rem' }}>
        <div className="card-stat" style={{ textAlign: 'center', padding: '0.9rem' }}>
          <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-ink-500)' }}>Total semanas</p>
          <p style={{ margin: '0.25rem 0 0', fontSize: '1.5rem', fontFamily: 'var(--font-display)', color: 'var(--color-ink-800)' }}>{summary.total}</p>
        </div>
        <div className="card-stat" style={{ textAlign: 'center', padding: '0.9rem' }}>
          <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-ink-500)' }}>Validadas</p>
          <p style={{ margin: '0.25rem 0 0', fontSize: '1.5rem', fontFamily: 'var(--font-display)', color: 'var(--color-ok-text)' }}>{summary.validated}</p>
        </div>
        <div className="card-stat" style={{ textAlign: 'center', padding: '0.9rem' }}>
          <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-ink-500)' }}>Pendientes</p>
          <p style={{ margin: '0.25rem 0 0', fontSize: '1.5rem', fontFamily: 'var(--font-display)', color: 'var(--color-warn-text)' }}>{summary.pending}</p>
        </div>
      </div>

      <AlertError>{error}</AlertError>
      <AlertSuccess>{success}</AlertSuccess>

      {entries.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={ClipboardCheck}
            title="Sin entradas semanales"
            description="Este estudiante no tiene registros de bitácora para validar."
          />
        </div>
      ) : (
        <div className="card table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th>Semana</th>
                <th>Periodo</th>
                <th>Fecha inicio</th>
                <th>Procedimientos</th>
                <th>Estado</th>
                <th>Validación tutor</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => {
                const statusMeta = STATUS_META[entry.status] || { label: entry.status, cls: 'badge-gray' }
                const procCount = (entry.procedures || []).length
                const procQty = (entry.procedures || []).reduce((sum, proc) => sum + (proc.quantity || 0), 0)

                return (
                  <tr key={entry.id}>
                    <td style={{ fontWeight: 600 }}>Semana {entry.week_number}</td>
                    <td>{periodLabelByWeek(entry.week_number)}</td>
                    <td>{entry.week_start_date}</td>
                    <td>
                      <span title={`${procCount} tipo(s) de procedimiento`}>
                        {procQty} <span style={{ color: 'var(--color-ink-400)', fontSize: '0.8rem' }}>({procCount})</span>
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${statusMeta.cls}`}>{statusMeta.label}</span>
                    </td>
                    <td>
                      {entry.tutor_validation ? (
                        <span className="badge badge-green" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                          <CheckCircle2 size={12} />
                          {new Date(entry.tutor_validation.validated_at).toLocaleDateString('es-CL')}
                        </span>
                      ) : (
                        <span className="badge badge-yellow">Pendiente</span>
                      )}
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => setSelectedEntry(entry)}
                      >
                        <Eye size={14} />
                        Ver detalle
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <LogbookEntryDetailModal
        entry={selectedEntry}
        studentName={studentName}
        onClose={() => setSelectedEntry(null)}
        onValidate={handleValidate}
        validating={validatingId === selectedEntry?.id}
      />
    </div>
  )
}
