import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import EmptyState from '../../components/ui/EmptyState'
import { AlertError, AlertSuccess } from '../../components/ui/Alert'
import { ArrowLeft, CheckCircle2, ClipboardCheck } from 'lucide-react'

function periodLabelByWeek(weekNumber) {
  if (weekNumber >= 1 && weekNumber <= 13) return 'Semestre 1'
  if (weekNumber >= 14 && weekNumber <= 26) return 'Semestre 2'
  return 'Fuera de rango semestral'
}

export default function LogbookValidationPage() {
  const { student_id } = useParams()
  const [searchParams] = useSearchParams()
  const studentName = searchParams.get('name') || 'Estudiante'
  const navigate = useNavigate()

  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [validatingId, setValidatingId] = useState(null)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const loadEntries = () => {
    setLoading(true)
    setError(null)
    api.get(`/logbook/tutor/students/${student_id}/entries`)
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
          <p className="section-subtitle">{studentName} · Confirmación semanal de registros clínicos</p>
        </div>
      </div>

      <div className="stagger" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginBottom: '1rem' }}>
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
        <div className="card" style={{ overflow: 'hidden' }}>
          <table className="table">
            <thead>
              <tr>
                <th>Semana</th>
                <th>Periodo</th>
                <th>Fecha inicio</th>
                <th>Procedimientos</th>
                <th>Validación tutor</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id}>
                  <td style={{ fontWeight: 600 }}>Semana {entry.week_number}</td>
                  <td>{periodLabelByWeek(entry.week_number)}</td>
                  <td>{entry.week_start_date}</td>
                  <td>{(entry.procedures || []).reduce((sum, proc) => sum + (proc.quantity || 0), 0)}</td>
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
                      className="btn btn-primary btn-sm"
                      onClick={() => handleValidate(entry.id)}
                      disabled={Boolean(entry.tutor_validation) || validatingId === entry.id}
                    >
                      {validatingId === entry.id ? 'Validando...' : 'Validar'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
