import { useEffect, useState } from 'react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import { Search, ClipboardList } from 'lucide-react'

const SCORE_META = {
  achieved:     { label: 'Logrado',      cls: 'badge-green' },
  in_progress:  { label: 'En progreso',  cls: 'badge-yellow' },
  not_achieved: { label: 'No logrado',   cls: 'badge-red' },
}

export default function EvaluationsPage() {
  const [students, setStudents] = useState([])
  const [studentQuery, setStudentQuery] = useState('')
  const [selectedName, setSelectedName] = useState('')
  const [loadingStudents, setLoadingStudents] = useState(false)
  const [showOptions, setShowOptions] = useState(false)
  const [studentId, setStudentId] = useState('')
  const [evaluations, setEvaluations] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searched, setSearched] = useState(false)
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    const timeout = setTimeout(() => {
      setLoadingStudents(true)
      api.get('/dashboard/students', {
        params: { q: studentQuery || undefined, limit: 20 },
      })
        .then(({ data }) => setStudents(data))
        .catch(() => setStudents([]))
        .finally(() => setLoadingStudents(false))
    }, 300)

    return () => clearTimeout(timeout)
  }, [studentQuery])

  const pickStudent = (student) => {
    setStudentId(student.id)
    setSelectedName(student.full_name)
    setStudentQuery(student.full_name)
    setShowOptions(false)
  }

  const handleSearch = (e) => {
    e.preventDefault()
    if (!studentId) return
    setLoading(true)
    setError(null)
    setSearched(true)
    setExpanded(null)
    api.get(`/evaluations/students/${studentId}`)
      .then(({ data }) => setEvaluations(data))
      .catch(() => setError('Error al cargar las evaluaciones'))
      .finally(() => setLoading(false))
  }

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Evaluaciones</h2>
          <p className="section-subtitle">Consulta las evaluaciones clínicas por estudiante</p>
        </div>
      </div>

      <div className="card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.5rem' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.75rem' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <input
              type="text"
              value={studentQuery}
              onChange={(e) => {
                const value = e.target.value
                setStudentQuery(value)
                setShowOptions(true)
                if (value !== selectedName) {
                  setStudentId('')
                }
              }}
              onFocus={() => setShowOptions(true)}
              placeholder="Buscar estudiante por nombre o correo..."
              className="input"
            />
            {showOptions && (
              <div
                className="card"
                style={{
                  position: 'absolute',
                  top: 'calc(100% + 0.35rem)',
                  left: 0,
                  right: 0,
                  zIndex: 30,
                  maxHeight: '15rem',
                  overflowY: 'auto',
                }}
              >
                {loadingStudents && (
                  <div style={{ padding: '0.625rem 0.75rem', fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                    Buscando estudiantes...
                  </div>
                )}
                {!loadingStudents && students.length === 0 && (
                  <div style={{ padding: '0.625rem 0.75rem', fontSize: '0.8125rem', color: 'var(--color-ink-500)' }}>
                    Sin resultados
                  </div>
                )}
                {!loadingStudents && students.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => pickStudent(s)}
                    style={{
                      width: '100%',
                      border: 'none',
                      background: 'transparent',
                      textAlign: 'left',
                      padding: '0.625rem 0.75rem',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <span style={{ color: 'var(--color-ink-700)', fontSize: '0.875rem' }}>{s.full_name}</span>
                    <span style={{ color: 'var(--color-ink-400)', fontSize: '0.75rem' }}>{s.email}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading || !studentId}>
            <Search size={15} /> Buscar
          </button>
        </form>
        <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--color-ink-500)' }}>
          {studentId ? `Seleccionado: ${selectedName}` : 'Selecciona un estudiante de la lista para consultar evaluaciones.'}
        </div>
      </div>

      {loading && <Spinner />}
      <AlertError>{error}</AlertError>

      {!loading && searched && !error && (
        evaluations.length === 0 ? (
          <div className="card">
            <EmptyState
              icon={ClipboardList}
              title="Sin evaluaciones"
              description={`No se encontraron evaluaciones para ${selectedName ?? 'este estudiante'}.`}
            />
          </div>
        ) : (
          <div className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {evaluations.map((ev) => (
              <div key={ev.id} className="card-accent" style={{ overflow: 'hidden' }}>
                <button
                  onClick={() => setExpanded(expanded === ev.id ? null : ev.id)}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '1rem 1.25rem', background: 'none', border: 'none', cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <ClipboardList size={16} style={{ color: 'var(--color-uv-500)', flexShrink: 0 }} />
                    <div>
                      <p style={{ fontWeight: 600, color: 'var(--color-ink-900)', margin: 0 }}>{ev.period}</p>
                      <p style={{ fontSize: '0.8125rem', color: 'var(--color-ink-500)', margin: 0 }}>{ev.evaluation_date}</p>
                    </div>
                  </div>
                  <span className="badge badge-blue">{ev.items?.length ?? 0} criterios</span>
                </button>

                {expanded === ev.id && ev.items?.length > 0 && (
                  <div style={{ borderTop: '1px solid var(--color-ink-100)', padding: '1rem 1.25rem' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {ev.items.map((item, i) => {
                        const meta = SCORE_META[item.score] || { label: item.score, cls: 'badge-gray' }
                        return (
                          <div key={i} style={{
                            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                            padding: '0.5rem 0.75rem',
                            background: 'var(--color-ink-50)',
                            borderRadius: 'var(--radius-md)',
                          }}>
                            <span style={{ fontSize: '0.875rem', color: 'var(--color-ink-700)' }}>{item.dimension}</span>
                            <span className={`badge ${meta.cls}`}>{meta.label}</span>
                          </div>
                        )
                      })}
                    </div>
                    {ev.overall_comment && (
                      <p style={{
                        marginTop: '0.75rem', fontSize: '0.875rem', color: 'var(--color-ink-500)',
                        fontStyle: 'italic', padding: '0.5rem 0.75rem',
                        background: 'var(--color-earth-50)', borderRadius: 'var(--radius-md)',
                        borderLeft: '3px solid var(--color-earth-300)',
                      }}>
                        "{ev.overall_comment}"
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )
      )}
    </div>
  )
}
