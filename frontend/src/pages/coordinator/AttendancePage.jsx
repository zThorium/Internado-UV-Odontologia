import { useState, useEffect } from 'react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import { Search, CalendarCheck, Users } from 'lucide-react'

const STATUS_LABELS = { present: 'Presente', absent: 'Ausente', justified: 'Justificado' }
const STATUS_CLS    = { present: 'badge-green', absent: 'badge-red', justified: 'badge-yellow' }

export default function CoordinatorAttendancePage() {
  const [students, setStudents] = useState([])
  const [studentQuery, setStudentQuery] = useState('')
  const [selectedName, setSelectedName] = useState('')
  const [loadingStudents, setLoadingStudents] = useState(false)
  const [showOptions, setShowOptions] = useState(false)
  const [studentId, setStudentId] = useState('')
  const [records, setRecords] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searched, setSearched] = useState(false)

  // Búsqueda con debounce
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

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!studentId) return
    
    setLoading(true)
    setError(null)
    setSearched(true)
    try {
      const [recRes, statsRes] = await Promise.all([
        api.get(`/attendance/students/${studentId}`),
        api.get(`/attendance/students/${studentId}/stats`),
      ])
      setRecords(recRes.data)
      setStats(statsRes.data)
    } catch {
      setError('Error al cargar la asistencia. Por favor, intenta nuevamente.')
    } finally {
      setLoading(false)
    }
  }

  const rateColor = stats
    ? stats.attendance_rate >= 75 ? 'var(--color-ok-text)'
    : stats.attendance_rate >= 50 ? 'var(--color-warn-text)'
    : 'var(--color-err-text)'
    : 'var(--color-ink-500)'

  const rateBarColor = stats
    ? stats.attendance_rate >= 75 ? '#16a34a'
    : stats.attendance_rate >= 50 ? '#d97706'
    : '#dc2626'
    : '#ccc'

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Asistencia</h2>
          <p className="section-subtitle">Consulta el historial y estadísticas de asistencia por estudiante</p>
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
          {studentId ? `Seleccionado: ${selectedName}` : 'Selecciona un estudiante de la lista para consultar asistencia.'}
        </div>
      </div>

      {loading && <Spinner />}
      <AlertError>{error}</AlertError>

      {!loading && searched && !error && stats && (
        <>
          {/* Stats */}
          <div className="stagger stats-grid-4" style={{ marginBottom: '1.25rem' }}>
            {[
              { label: 'Total días',   value: stats.total,     color: 'var(--color-ink-700)' },
              { label: 'Presentes',    value: stats.present,   color: 'var(--color-ok-text)' },
              { label: 'Ausentes',     value: stats.absent,    color: 'var(--color-err-text)' },
              { label: 'Justificados', value: stats.justified, color: 'var(--color-warn-text)' },
            ].map(({ label, value, color }) => (
              <div key={label} className="card-stat" style={{ textAlign: 'center', padding: '1rem' }}>
                <p style={{ fontSize: '0.75rem', color: 'var(--color-ink-500)', margin: '0 0 0.25rem' }}>{label}</p>
                <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 500, color, margin: 0, lineHeight: 1.1 }}>{value}</p>
              </div>
            ))}
          </div>

          {/* Attendance rate bar */}
          <div className="card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.625rem' }}>
              <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-ink-700)' }}>Tasa de asistencia</span>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 500, color: rateColor, lineHeight: 1 }}>
                {stats.attendance_rate}%
              </span>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${stats.attendance_rate}%`, background: rateBarColor }} />
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-ink-500)', marginTop: '0.5rem' }}>
              {stats.attendance_rate >= 75 ? 'Asistencia satisfactoria' : stats.attendance_rate >= 50 ? 'Asistencia en riesgo' : 'Asistencia crítica — requiere atención'}
            </p>
          </div>

          {/* Records */}
          {records.length === 0 ? (
            <div className="card">
              <EmptyState icon={CalendarCheck} title="Sin registros" description="Este estudiante no tiene registros de asistencia." />
            </div>
          ) : (
            <div className="card table-scroll">
              <table className="table">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Estado</th>
                    <th>Observación</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((rec) => (
                    <tr key={rec.id}>
                      <td style={{ fontWeight: 500 }}>{rec.date}</td>
                      <td>
                        <span className={`badge ${STATUS_CLS[rec.status] || 'badge-gray'}`}>
                          {STATUS_LABELS[rec.status] || rec.status}
                        </span>
                      </td>
                      <td style={{ color: 'var(--color-ink-500)' }}>
                        {rec.observation || <span style={{ color: 'var(--color-ink-300)' }}>—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}


    </div>
  )
}
