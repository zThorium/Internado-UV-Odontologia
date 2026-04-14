import AppShell from '../components/AppShell'
import { Users, AlertTriangle } from 'lucide-react'

const NAV_LINKS = [
  { to: '/tutor', label: 'Mis Estudiantes', icon: Users },
  { to: '/tutor/incidents', label: 'Incidentes', icon: AlertTriangle },
]

export default function TutorDashboard() {
  return <AppShell navLinks={NAV_LINKS} subtitle="Tutor" />
}
