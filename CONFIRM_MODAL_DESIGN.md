# ConfirmModal - Especificación de Diseño

## Vista General
Modal de confirmación moderno que se integra perfectamente con el design system del sistema de gestión de internado odontológico UV.

## Estructura Visual

```
┌─────────────────────────────────────────────────────────────┐
│                    [Backdrop oscurecido]                     │
│                                                              │
│     ┌───────────────────────────────────────────┐          │
│     │  ╔═══════════════════════════════════╗  [X]│          │
│     │  ║                                   ║     │          │
│     │  ║    ⚠️  [Icono de advertencia]    ║     │          │
│     │  ║       en círculo coloreado        ║     │          │
│     │  ║                                   ║     │          │
│     │  ╚═══════════════════════════════════╝     │          │
│     │                                            │          │
│     │  ¿Eliminar usuario?                        │          │
│     │  [Título en Fraunces, grande]              │          │
│     │                                            │          │
│     │  Estás a punto de eliminar                 │          │
│     │  permanentemente a Juan Pérez.             │          │
│     │  Esta acción no se puede deshacer.         │          │
│     │  [Mensaje en Plus Jakarta Sans]            │          │
│     │                                            │          │
│     │                    [Cancelar] [Eliminar]   │          │
│     │                     ghost      red         │          │
│     └───────────────────────────────────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Especificaciones Técnicas

### Backdrop (Full-Page Overlay)
- **Posición**: `fixed` con `top: 0, left: 0, right: 0, bottom: 0`
- **Dimensiones**: `100vw × 100vh` - Cubre toda la ventana del navegador
- **Color**: `rgba(15, 31, 46, 0.6)` - Azul oscuro semi-transparente (60% opacidad)
- **Blur**: `4px` - Desenfoque aplicado a todo el contenido detrás
- **WebKit Blur**: `4px` - Soporte para Safari
- **Z-index**: `9999` - Asegura que esté sobre todo el contenido
- **Display**: `flex` con `align-items: center` y `justify-content: center`
- **Animación**: Fade in 150ms con easing `cubic-bezier(0.16, 1, 0.3, 1)`
- **Portal**: Renderizado usando `createPortal` directamente en `document.body`

### Contenedor del Modal
- **Fondo**: `var(--color-bg-surface)` - Blanco puro (#ffffff)
- **Border radius**: `var(--radius-xl)` - 1.375rem (22px)
- **Sombra**: 
  - Principal: `0 20px 60px rgba(0, 0, 0, 0.25)`
  - Secundaria: `0 4px 12px rgba(0, 0, 0, 0.15)`
- **Max width**: `420px`
- **Filter**: `none` - Asegura que el modal NO se vea borroso
- **Backdrop filter**: `none` - Sin blur en el modal mismo
- **Isolation**: `isolate` - Crea un nuevo contexto de apilamiento
- **Will-change**: `transform` - Optimización de rendimiento
- **Animación**: Slide up + scale 200ms

### Icono de Advertencia
- **Tamaño contenedor**: `48px × 48px`
- **Border radius**: `50%` (círculo perfecto)
- **Fondo destructivo**: `var(--color-err-bg)` - #fce4ec
- **Fondo normal**: `var(--color-warn-bg)` - #fff8e1
- **Color icono destructivo**: `var(--color-err-text)` - #c62828
- **Color icono normal**: `var(--color-warn-text)` - #e65100
- **Icono**: AlertTriangle de lucide-react (24px)

### Tipografía

#### Título
- **Font**: `var(--font-display)` - Fraunces
- **Size**: `1.375rem` (22px)
- **Weight**: `500`
- **Color**: `var(--color-ink-900)` - #0f1f2e
- **Letter spacing**: `-0.02em`
- **Line height**: `1.2`
- **Margin bottom**: `0.75rem`

#### Mensaje
- **Font**: `var(--font-body)` - Plus Jakarta Sans
- **Size**: `0.9375rem` (15px)
- **Color**: `var(--color-ink-500)` - #3d6480
- **Line height**: `1.6`

### Botones

#### Botón Cancelar (Ghost)
- **Background**: `transparent`
- **Color**: `var(--color-ink-500)`
- **Padding**: `0.5625rem 1.125rem`
- **Border radius**: `var(--radius-md)` - 0.625rem
- **Font size**: `0.875rem`
- **Font weight**: `600`
- **Hover**: Background `var(--color-ink-50)`

#### Botón Confirmar Destructivo
- **Background**: `#dc2626` (rojo)
- **Color**: `#fff`
- **Padding**: `0.5625rem 1.125rem`
- **Border radius**: `var(--radius-md)`
- **Font size**: `0.875rem`
- **Font weight**: `600`
- **Sombra**: `0 1px 3px rgba(220, 38, 38, 0.3)`
- **Hover**: 
  - Background: `#b91c1c`
  - Sombra: `0 2px 8px rgba(220, 38, 38, 0.35)`

#### Botón Confirmar Normal
- **Background**: `var(--color-uv-600)` - #1e4d8c
- **Color**: `#fff`
- **Sombra**: `0 1px 3px rgba(30, 77, 140, 0.25)`
- **Hover**:
  - Background: `var(--color-uv-700)` - #1a3a6b
  - Sombra: `0 2px 8px rgba(30, 77, 140, 0.30)`

### Botón Cerrar (X)
- **Posición**: Absolute, top right
- **Top**: `1rem`
- **Right**: `1rem`
- **Padding**: `0.375rem`
- **Color**: `var(--color-ink-300)` - #8aafc8
- **Hover**: `var(--color-ink-500)` - #3d6480
- **Icono**: X de lucide-react (18px)

### Espaciado
- **Padding contenido**: `2rem 2rem 1.5rem` (top/sides, bottom)
- **Padding acciones**: `1rem 2rem 2rem`
- **Gap entre botones**: `0.75rem`
- **Margin bottom icono**: `1.25rem`

### Animaciones

#### Backdrop Fade In
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

#### Modal Slide Up
```css
@keyframes modalSlideUp {
  from {
    opacity: 0;
    transform: translateY(16px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
```

### Interacciones
- **Cerrar con Escape**: Listener en window
- **Cerrar con click fuera**: Click en backdrop
- **Cerrar con X**: Botón en esquina superior derecha
- **Bloqueo de scroll**: `body { overflow: hidden }` cuando está abierto
- **Estado de carga**: Botón muestra "Procesando..." y se deshabilita

## Responsive
- **Mobile**: Padding reducido, modal ocupa más ancho
- **Tablet**: Mantiene diseño completo
- **Desktop**: Max width 420px centrado

## Accesibilidad
- Focus trap dentro del modal
- Escape para cerrar
- Aria labels apropiados
- Contraste WCAG AA compliant

## Casos de Uso

### Acción Destructiva (Eliminar)
```jsx
<ConfirmModal
  isDestructive={true}
  title="¿Eliminar usuario?"
  message="Estás a punto de eliminar permanentemente a Juan Pérez..."
/>
```
- Icono rojo
- Botón rojo
- Énfasis en irreversibilidad

### Acción Normal (Confirmar)
```jsx
<ConfirmModal
  isDestructive={false}
  title="¿Confirmar cambios?"
  message="Los cambios se aplicarán inmediatamente..."
/>
```
- Icono amarillo
- Botón azul UV
- Tono más neutral
