import AppShell from '../components/AppShell'
import { Users } from 'lucide-react'

const NAV_LINKS = [
  { to: '/tutor', label: 'Mis Estudiantes', icon: Users },
]

export default function TutorDashboard() {
  return <AppShell navLinks={NAV_LINKS} subtitle="Tutor" />
}
