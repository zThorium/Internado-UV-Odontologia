import { useState, useEffect } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { LogOut, MapPin, Moon, Sun, Menu, X } from 'lucide-react'
import { useTour } from '../hooks/useTour'

const TOUR_KEY_MAP = {
  '/student/logbook':         'student-logbook',
  '/student/attendance':      'student-attendance',
  '/student/incidents':       'student-incidents',
  '/tutor':                   'tutor-students',
  '/coordinator/overview':    'coordinator-overview',
  '/coordinator/alerts':      'coordinator-alerts',
  '/coordinator/logbooks':    'coordinator-logbooks',
  '/coordinator/evaluations': 'coordinator-evaluations',
  '/coordinator/attendance':  'coordinator-attendance',
  '/coordinator/incidents':   'coordinator-incidents',
  '/coordinator/wellbeing':   'coordinator-wellbeing',
  '/coordinator/assignments': 'coordinator-assignments',
  '/coordinator/users':       'coordinator-users',
}

export default function AppShell({ navLinks, subtitle }) {
  const { user, logout, showTour, completeTour, triggerTour } = useAuth()
  const { isDark, toggleTheme } = useTheme()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useTour({ role: user?.role, active: showTour, onComplete: completeTour })

  // Cerrar sidebar al navegar
  useEffect(() => { setSidebarOpen(false) }, [location.pathname])

  // Bloquear scroll del body cuando sidebar está abierto en móvil
  useEffect(() => {
    document.body.style.overflow = sidebarOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [sidebarOpen])

  const sidebarContent = (
    <>
      {/* Brand */}
      <div style={{ padding: '1.5rem 1.25rem 1.25rem', borderBottom: '1px solid rgb(255 255 255 / 0.06)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: 36, height: 36, borderRadius: '10px',
            background: 'var(--color-earth-300)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-earth-900)' }}>UV</span>
          </div>
          <div>
            <p style={{ fontFamily: 'var(--font-display)', fontSize: '0.9375rem', fontWeight: 500, color: 'var(--color-sidebar-text)', lineHeight: 1.2, margin: 0 }}>
              Internado
            </p>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-sidebar-muted)', margin: 0, lineHeight: 1.3 }}>
              Odontología UV
            </p>
          </div>
        </div>
      </div>

      {/* Role label */}
      {subtitle && (
        <div style={{ padding: '1rem 1.25rem 0.375rem' }}>
          <p style={{ fontSize: '0.6875rem', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--color-sidebar-muted)', margin: 0 }}>
            {subtitle}
          </p>
        </div>
      )}

      {/* Nav links */}
      <nav style={{ flex: 1, padding: '0.375rem 0.625rem', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {navLinks.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            data-tour={TOUR_KEY_MAP[to]}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            {Icon && <Icon size={15} strokeWidth={1.75} />}
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Perfil + tour + logout */}
      <div
        data-tour="sidebar-profile"
        style={{ padding: '0.625rem', borderTop: '1px solid rgb(255 255 255 / 0.06)', display: 'flex', flexDirection: 'column', gap: 2 }}
      >
        <button onClick={toggleTheme} className="nav-link" style={{ color: 'var(--color-sidebar-text)' }}>
          {isDark ? <Moon size={14} strokeWidth={1.75} /> : <Sun size={14} strokeWidth={1.75} />}
          {isDark ? 'Modo oscuro' : 'Modo claro'}
        </button>
        <button onClick={triggerTour} className="nav-link" style={{ color: 'var(--color-sidebar-muted)', fontSize: '0.8125rem' }}>
          <MapPin size={14} strokeWidth={1.75} />
          Ver tour de bienvenida
        </button>
        <button onClick={logout} className="nav-link" style={{ color: 'var(--color-sidebar-muted)' }}>
          <LogOut size={15} strokeWidth={1.75} />
          Cerrar sesión
        </button>
      </div>
    </>
  )

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--color-bg-base)' }}>

      {/* ── Sidebar desktop (≥768px) ─────────────────────────────────── */}
      <aside className="sidebar-desktop" style={{
        width: 240, flexShrink: 0,
        background: 'var(--color-bg-sidebar)',
        display: 'flex', flexDirection: 'column',
        position: 'sticky', top: 0, height: '100vh', overflowY: 'auto',
      }}>
        {sidebarContent}
      </aside>

      {/* ── Overlay móvil ────────────────────────────────────────────── */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          style={{
            position: 'fixed', inset: 0, zIndex: 40,
            background: 'rgb(0 0 0 / 0.45)',
            backdropFilter: 'blur(2px)',
          }}
        />
      )}

      {/* ── Sidebar móvil (drawer) ───────────────────────────────────── */}
      <aside className="sidebar-mobile" style={{
        position: 'fixed', top: 0, left: 0, bottom: 0,
        width: 260, zIndex: 50,
        background: 'var(--color-bg-sidebar)',
        display: 'flex', flexDirection: 'column',
        transform: sidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
        transition: 'transform 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
        overflowY: 'auto',
      }}>
        {/* Botón cerrar */}
        <button
          onClick={() => setSidebarOpen(false)}
          style={{
            position: 'absolute', top: '1rem', right: '1rem',
            background: 'rgb(255 255 255 / 0.1)', border: 'none',
            borderRadius: '8px', padding: '0.375rem',
            color: 'var(--color-sidebar-text)', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >
          <X size={18} />
        </button>
        {sidebarContent}
      </aside>

      {/* ── Main content ─────────────────────────────────────────────── */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>

        {/* Topbar móvil */}
        <header className="mobile-topbar" style={{
          display: 'none',
          alignItems: 'center',
          gap: '0.75rem',
          padding: '0.875rem 1.25rem',
          background: 'var(--color-bg-sidebar)',
          position: 'sticky', top: 0, zIndex: 30,
        }}>
          <button
            onClick={() => setSidebarOpen(true)}
            style={{
              background: 'rgb(255 255 255 / 0.1)', border: 'none',
              borderRadius: '8px', padding: '0.4375rem',
              color: 'var(--color-sidebar-text)', cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <Menu size={20} />
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{
              width: 28, height: 28, borderRadius: '7px',
              background: 'var(--color-earth-300)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-earth-900)' }}>UV</span>
            </div>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '0.9375rem', fontWeight: 500, color: 'var(--color-sidebar-text)' }}>
              Internado
            </span>
          </div>
        </header>

        <main style={{ flex: 1, padding: '2.5rem 3rem', maxWidth: 1100 }} className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
