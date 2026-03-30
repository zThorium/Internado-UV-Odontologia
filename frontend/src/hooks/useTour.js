import { useEffect, useRef } from 'react'
import { driver } from 'driver.js'
import 'driver.js/dist/driver.css'

const TOUR_STEPS = {
  student: [
    {
      // Paso 0: bienvenida — sin elemento (centrado)
      popover: {
        title: 'Bienvenido/a a tu espacio de internado',
        description:
          'Aquí podrás registrar tu progreso clínico y estar siempre conectado/a con tu coordinador. Te mostramos las secciones principales en menos de un minuto.',
        side: 'over',
        align: 'center',
      },
    },
    {
      element: '[data-tour="student-logbook"]',
      popover: {
        title: 'Mi Bitácora',
        description:
          'Aquí registras tus procedimientos clínicos cada semana. Tu tutor no puede ver esta sección — es solo entre tú y el coordinador.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="student-attendance"]',
      popover: {
        title: 'Asistencia',
        description:
          'Registra tu asistencia diaria al campo clínico desde aquí. Puedes marcar presente, ausente o justificado.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="student-incidents"]',
      popover: {
        title: 'Reportes confidenciales',
        description:
          'Si vives alguna situación difícil durante tu internado, este es tu canal confidencial. Solo tu coordinador UV tiene acceso a estos reportes.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="sidebar-profile"]',
      popover: {
        title: 'Tu perfil',
        description:
          'Puedes volver a ver este tour cuando quieras desde aquí. También encontrarás la opción para cerrar sesión.',
        side: 'right',
        align: 'end',
      },
    },
  ],

  tutor: [
    {
      popover: {
        title: 'Bienvenido/a al panel de tutor',
        description:
          'Aquí puedes evaluar a los estudiantes que tienes asignados de forma rápida y simple. El proceso toma menos de 2 minutos.',
        side: 'over',
        align: 'center',
      },
    },
    {
      element: '[data-tour="tutor-students"]',
      popover: {
        title: 'Mis Estudiantes',
        description:
          'Encuentra aquí a todos tus estudiantes asignados. Desde cada tarjeta puedes acceder a sus evaluaciones y ver su asistencia.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="sidebar-profile"]',
      popover: {
        title: 'Listo para empezar',
        description:
          'Completar una evaluación toma menos de 2 minutos. Puedes volver a ver este tour desde tu perfil cuando quieras.',
        side: 'right',
        align: 'end',
      },
    },
  ],

  coordinator: [
    {
      popover: {
        title: 'Bienvenido/a al panel de coordinación',
        description:
          'Tienes control completo del internado: monitorea estudiantes, gestiona tutores, revisa bitácoras, evaluaciones y responde a alertas e incidentes.',
        side: 'over',
        align: 'center',
      },
    },
    {
      element: '[data-tour="coordinator-overview"]',
      popover: {
        title: 'Resumen general',
        description:
          'Tu vista principal con métricas clave: estudiantes activos, asistencia, bitácoras pendientes y alertas que requieren atención.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="coordinator-alerts"]',
      popover: {
        title: 'Alertas',
        description:
          'Sistema inteligente que detecta estudiantes en riesgo: baja asistencia, evaluaciones pendientes o problemas de bienestar.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="coordinator-logbooks"]',
      popover: {
        title: 'Bitácoras',
        description:
          'Revisa todas las entradas de bitácora de tus estudiantes. Puedes filtrar por estudiante, fecha o tipo de procedimiento.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="coordinator-evaluations"]',
      popover: {
        title: 'Evaluaciones',
        description:
          'Monitorea el progreso de evaluaciones de tutores. Ve qué estudiantes han sido evaluados y cuáles están pendientes.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="coordinator-attendance"]',
      popover: {
        title: 'Asistencia',
        description:
          'Control completo de asistencia de todos los estudiantes. Identifica patrones y estudiantes con ausentismo.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="coordinator-incidents"]',
      popover: {
        title: 'Incidentes confidenciales',
        description:
          'Reportes confidenciales de estudiantes. Solo tú tienes acceso. Responde y da seguimiento a situaciones sensibles.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="coordinator-wellbeing"]',
      popover: {
        title: 'Bienestar',
        description:
          'Monitorea el estado emocional y bienestar de tus estudiantes. Detecta tempranamente situaciones que requieren apoyo.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="coordinator-assignments"]',
      popover: {
        title: 'Asignaciones',
        description:
          'Asigna estudiantes a tutores y campos clínicos. Gestiona las relaciones tutor-estudiante de forma centralizada.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="coordinator-cohorts"]',
      popover: {
        title: 'Cohortes',
        description:
          'Administra los periodos académicos (cohortes) para mantener ordenadas las asignaciones y reportes.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="coordinator-users"]',
      popover: {
        title: 'Gestión de usuarios',
        description:
          'Crea, edita y elimina usuarios (estudiantes y tutores). Control completo del equipo de internado.',
        side: 'right',
        align: 'start',
      },
    },
    {
      element: '[data-tour="sidebar-profile"]',
      popover: {
        title: 'Todo listo',
        description:
          'Puedes volver a ver este tour cuando quieras desde aquí. También encontrarás opciones de tema y cierre de sesión.',
        side: 'right',
        align: 'end',
      },
    },
  ],
}

export function useTour({ role, active, onComplete }) {
  const driverRef = useRef(null)

  useEffect(() => {
    if (!active || !role) return

    const steps = TOUR_STEPS[role]
    if (!steps) return

    const driverObj = driver({
      animate: true,
      smoothScroll: true,
      allowClose: true,
      overlayOpacity: 0.55,
      stagePadding: 8,
      stageRadius: 10,
      popoverClass: 'uv-tour-popover',
      nextBtnText: 'Siguiente →',
      prevBtnText: '← Anterior',
      doneBtnText: 'Comenzar',
      showProgress: true,
      progressText: '{{current}} de {{total}}',
      onDestroyStarted: () => {
        driverObj.destroy()
        onComplete?.()
      },
      steps,
    })

    driverRef.current = driverObj

    // Pequeño delay para que el DOM esté listo
    const timer = setTimeout(() => {
      driverObj.drive()
    }, 400)

    return () => {
      clearTimeout(timer)
      if (driverRef.current?.isActive?.()) {
        driverRef.current.destroy()
      }
    }
  }, [active, role])
}
