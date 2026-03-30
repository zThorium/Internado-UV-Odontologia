import AppShell from '../components/AppShell'
import {
  LayoutDashboard, BookOpen, ClipboardList,
  AlertTriangle, Users, CalendarCheck, Heart, Bell, Layers3
} from 'lucide-react'

const NAV_LINKS = [
  { to: '/coordinator/overview',    label: 'Resumen',       icon: LayoutDashboard },
  { to: '/coordinator/alerts',      label: 'Alertas',       icon: Bell },
  { to: '/coordinator/logbooks',    label: 'Bitácoras',     icon: BookOpen },
  { to: '/coordinator/evaluations', label: 'Evaluaciones',  icon: ClipboardList },
  { to: '/coordinator/attendance',  label: 'Asistencia',    icon: CalendarCheck },
  { to: '/coordinator/incidents',   label: 'Incidentes',    icon: AlertTriangle },
  { to: '/coordinator/wellbeing',   label: 'Bienestar',     icon: Heart },
  { to: '/coordinator/assignments', label: 'Asignaciones',  icon: Users },
  { to: '/coordinator/cohorts',     label: 'Cohortes',      icon: Layers3 },
  { to: '/coordinator/users',       label: 'Usuarios',      icon: Users },
]

export default function CoordinatorDashboard() {
  return <AppShell navLinks={NAV_LINKS} subtitle="Coordinador" />
}
