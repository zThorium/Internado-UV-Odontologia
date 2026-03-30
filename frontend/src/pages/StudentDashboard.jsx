import AppShell from '../components/AppShell'
import { BookOpen, AlertTriangle, CalendarCheck } from 'lucide-react'

const NAV_LINKS = [
  { to: '/student/logbook',    label: 'Mi Bitácora', icon: BookOpen },
  { to: '/student/attendance', label: 'Asistencia',  icon: CalendarCheck },
  { to: '/student/incidents',  label: 'Incidentes',  icon: AlertTriangle },
]

export default function StudentDashboard() {
  return <AppShell navLinks={NAV_LINKS} subtitle="Estudiante" />
}
