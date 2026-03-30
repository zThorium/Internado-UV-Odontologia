# Plataforma de Seguimiento y Bienestar — Internado Odontología UV

## Descripción General

Sistema web para gestionar el internado clínico de estudiantes de 6° año de la carrera de Odontología de la Universidad de Valparaíso (UV). Los estudiantes realizan su internado en campos clínicos externos (CESFAM, hospitales, centros APS) supervisados por tutores externos a la universidad.

El sistema resuelve tres problemas concretos:
1. Los coordinadores UV no tienen visibilidad sobre cómo se evalúa a cada estudiante
2. Los criterios de evaluación son heterogéneos entre tutores
3. Los estudiantes sufren situaciones de maltrato y acoso que no se reportan por falta de un canal seguro

---

## Actores y Roles

### 1. Estudiante
- Alumno de 6° año de Odontología UV realizando internado clínico en campo externo
- Accede únicamente a su propia información
- Puede escribir su bitácora semanal y enviar reportes de incidentes confidenciales

### 2. Tutor Clínico Externo
- Profesional de salud externo a la UV que supervisa al estudiante en terreno
- Su uso de la plataforma NO es obligatorio → la interfaz debe ser extremadamente simple
- Evalúa al estudiante con escala Likert y registra procedimientos realizados
- **NUNCA puede ver la bitácora del estudiante ni los reportes de incidentes**

### 3. Coordinador UV
- Funcionario(s) de la Universidad de Valparaíso (pueden ser varios)
- Tiene acceso completo: bitácoras, evaluaciones, reportes de incidentes, estadísticas
- Gestiona la asignación de estudiantes a campos clínicos y tutores
- Recibe alertas cuando un estudiante envía un reporte de incidente

---

## Reglas Críticas de Privacidad

> Estas restricciones deben aplicarse a nivel de backend (control de acceso por rol), no solo en la interfaz de usuario.

- El **tutor** no puede acceder bajo ninguna circunstancia a:
  - La bitácora del estudiante
  - Los reportes de incidentes
  - Cualquier dato personal del estudiante más allá de lo necesario para evaluar

- Los **reportes de incidentes** son confidenciales:
  - El coordinador puede identificar qué estudiante reportó
  - El tutor no sabe que existe el reporte ni su contenido

- Un **estudiante** no puede ver información de otros estudiantes

---

## Módulos del Sistema

### Módulo 1 — Autenticación y Control de Acceso
- Login con usuario y contraseña
- Roles diferenciados: Estudiante, Tutor, Coordinador
- Sesión con JWT
- Recuperación de contraseña por correo
- Mecanismo de autenticación institucional (correo @uv.cl) pendiente de definición con la UV

### Módulo 2 — Bitácora del Estudiante
- El estudiante crea una entrada por semana
- Cada entrada registra: semana, procedimientos clínicos realizados (nombre, descripción, cantidad)
- El estudiante puede ver su historial completo de entradas
- Puede editar entradas mientras no hayan sido revisadas por el coordinador
- Completamente invisible para el tutor

### Módulo 3 — Reporte de Incidentes
- Canal confidencial para reportar maltrato, acoso, discriminación u otros problemas
- Formulario: tipo de incidente (lista predefinida), descripción libre, fecha del evento
- El coordinador ve quién reporta; el tutor no ve nada
- El coordinador recibe alerta (notificación + correo) al recibir un nuevo reporte
- El estudiante puede ver el estado de sus reportes: Enviado / En revisión / Resuelto

### Módulo 4 — Evaluación del Tutor
- El tutor ve la lista de estudiantes asignados a él
- Evalúa con escala Likert: Logrado / En proceso / No logrado
- Las dimensiones de evaluación (criterios específicos) están pendientes de definición con la Facultad
- Incluye campo de comentario opcional de texto libre
- El flujo de evaluación debe completarse en máximo 3 pantallas/pasos
- El tutor puede registrar los procedimientos clínicos realizados por el estudiante

### Módulo 5 — Dashboard del Coordinador
- Vista de bitácoras de todos los estudiantes bajo su supervisión
- Vista de evaluaciones realizadas por tutores
- Panel de reportes de incidentes con identificación del estudiante
- Estadísticas y resúmenes: procedimientos más realizados, frecuencia, comparativas
- Gestión de asignaciones: qué estudiante va a qué campo clínico con qué tutor
- Gestión de tutores clínicos (alta, edición)
- Cambio de estado de reportes de incidentes

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI (Python) |
| Base de datos | PostgreSQL |
| Autenticación | JWT con roles |
| Hosting objetivo | Railway o Render (por definir) |

---

## Restricciones y Decisiones de Diseño

- Plataforma **solo web** (no app móvil en esta etapa)
- Sin restricciones tecnológicas fijas (stack open source preferido)
- La interfaz del tutor debe ser la más simple posible (máximo 3 pasos para evaluar)
- La plataforma debe soportar múltiples cohortes de estudiantes simultáneamente
- La bitácora se registra con periodicidad **semanal**

---

## Puntos Pendientes (a resolver con profesora guía y Facultad)

- Mecanismo de autenticación institucional (¿correo @uv.cl u otro sistema?)
- Existencia de pauta oficial de evaluación UV (define las dimensiones Likert del tutor)
- Duración exacta del internado y estructura de rotaciones
- Número de estudiantes por cohorte
- Hosting: ¿servidores UV o nube?

---

## Contexto Académico

Este sistema es desarrollado como proyecto de tesis por un estudiante de la Universidad de Valparaíso. El desarrollo se realiza con asistencia de IA (Kiro). El código generado debe ser comprensible y explicable por el tesista para efectos de defensa académica.
