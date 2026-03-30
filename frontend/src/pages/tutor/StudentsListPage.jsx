import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { AlertError } from '../../components/ui/Alert'
import EmptyState from '../../components/ui/EmptyState'
import { Users, ClipboardList, CalendarCheck, MapPin } from 'lucide-react'

export default function StudentsListPage() {
  const [students, setStudents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/evaluations/my-students')
      .then(({ data }) => setStudents(data))
      .catch(() => setError('No se pudo cargar la lista de estudiantes.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Mis estudiantes</h2>
          <p className="section-subtitle">Estudiantes asignados para evaluación y seguimiento</p>
        </div>
        {students.length > 0 && (
          <span className="badge badge-blue" style={{ fontSize: '0.875rem', padding: '0.375rem 0.875rem' }}>
            {students.length} asignado{students.length !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      <AlertError>{error}</AlertError>

      {students.length === 0 ? (
        <div className="card">
          <EmptyState icon={Users} title="Sin estudiantes" description="No tienes estudiantes asignados." />
        </div>
      ) : (
        <div className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {students.map((s) => (
            <div key={s.assignment_id} className="card" style={{ padding: '1.25rem 1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
                {/* Avatar + info */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem', minWidth: 0 }}>
                  <div style={{
                    width: 44, height: 44, borderRadius: '50%', flexShrink: 0,
                    background: 'var(--color-uv-100)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 600, color: 'var(--color-uv-700)' }}>
                      {s.full_name?.charAt(0)?.toUpperCase() || '?'}
                    </span>
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <p style={{ fontWeight: 600, color: 'var(--color-ink-900)', margin: 0 }}>{s.full_name}</p>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--color-ink-500)', margin: 0 }}>{s.email}</p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginTop: '0.25rem' }}>
                      <MapPin size={11} style={{ color: 'var(--color-earth-500)' }} />
                      <span style={{ fontSize: '0.75rem', color: 'var(--color-earth-600)' }}>{s.clinical_site}</span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
                  <button
                    onClick={() => navigate(`/tutor/evaluate/${s.assignment_id}?student_id=${s.id}`)}
                    className="btn btn-primary btn-sm"
                  >
                    <ClipboardList size={13} /> Evaluar
                  </button>
                  <button
                    onClick={() => navigate(`/tutor/attendance/${s.id}?name=${encodeURIComponent(s.full_name)}`)}
                    className="btn btn-secondary btn-sm"
                  >
                    <CalendarCheck size={13} /> Asistencia
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
