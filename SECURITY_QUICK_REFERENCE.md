# Security Quick Reference Guide

## Common Security Tasks

### Protecting a New Route

```javascript
// In App.jsx
<Route
  path="/new-feature"
  element={
    <ProtectedRoute allowedRoles={['coordinator', 'tutor']}>
      <NewFeaturePage />
    </ProtectedRoute>
  }
/>
```

### Checking User Permissions in Component

```javascript
import { useAuth } from '../context/AuthContext'
import { hasRequiredRole } from '../utils/security'

function MyComponent() {
  const { user } = useAuth()
  
  if (!hasRequiredRole(user, 'coordinator')) {
    return <div>No tienes permisos para ver esto</div>
  }
  
  return <div>Contenido protegido</div>
}
```

### Validating User Input

```javascript
import { sanitizeInput, isValidEmail } from '../utils/security'

function handleSubmit(formData) {
  // Sanitize input
  const cleanName = sanitizeInput(formData.name)
  
  // Validate email
  if (!isValidEmail(formData.email)) {
    setError('Email inválido')
    return
  }
  
  // Proceed with clean data
  submitData({ name: cleanName, email: formData.email })
}
```

### Logging Security Events

```javascript
import { logSecurityEvent } from '../utils/security'

// Log suspicious activity
logSecurityEvent('suspicious_activity', {
  action: 'multiple_failed_attempts',
  userId: user.id,
  count: attemptCount,
})
```

### Rate Limiting User Actions

```javascript
import { checkRateLimit } from '../utils/security'

function handleAction() {
  // Check if user can perform action (max 5 times per minute)
  if (!checkRateLimit('action_key', 5, 60000)) {
    setError('Demasiados intentos. Espera un momento.')
    return
  }
  
  // Proceed with action
  performAction()
}
```

## Security Patterns

### Pattern 1: Protected API Call

```javascript
async function fetchSensitiveData() {
  try {
    const response = await api.get('/sensitive-endpoint')
    return response.data
  } catch (error) {
    if (error.response?.status === 401) {
      // Token expired, user will be redirected to login
      logSecurityEvent('unauthorized_api_access', {
        endpoint: '/sensitive-endpoint'
      })
    }
    throw error
  }
}
```

### Pattern 2: Conditional Rendering Based on Role

```javascript
function Dashboard() {
  const { user } = useAuth()
  
  return (
    <div>
      <h1>Dashboard</h1>
      
      {hasRequiredRole(user, 'coordinator') && (
        <AdminPanel />
      )}
      
      {hasRequiredRole(user, ['tutor', 'coordinator']) && (
        <TutorTools />
      )}
      
      <UserContent />
    </div>
  )
}
```

### Pattern 3: Secure Form Submission

```javascript
function SecureForm() {
  const [formData, setFormData] = useState({})
  const [error, setError] = useState(null)
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Rate limit submissions
    if (!checkRateLimit('form_submit', 3, 60000)) {
      setError('Demasiados envíos. Espera un momento.')
      return
    }
    
    // Validate input
    if (!isValidEmail(formData.email)) {
      setError('Email inválido')
      return
    }
    
    // Sanitize input
    const cleanData = {
      name: sanitizeInput(formData.name),
      email: formData.email,
    }
    
    try {
      await api.post('/endpoint', cleanData)
      logSecurityEvent('form_submitted', { form: 'contact' })
    } catch (error) {
      logSecurityEvent('form_submission_failed', {
        form: 'contact',
        error: error.message
      })
      setError('Error al enviar formulario')
    }
  }
  
  return <form onSubmit={handleSubmit}>...</form>
}
```

## Common Security Mistakes to Avoid

### ❌ DON'T: Store sensitive data in state without protection
```javascript
// Bad
const [password, setPassword] = useState('')
console.log('Password:', password) // Logged to console!
```

### ✅ DO: Handle sensitive data carefully
```javascript
// Good
const [password, setPassword] = useState('')
// Never log sensitive data
// Clear after use
useEffect(() => {
  return () => setPassword('')
}, [])
```

### ❌ DON'T: Trust user input
```javascript
// Bad
<div dangerouslySetInnerHTML={{ __html: userInput }} />
```

### ✅ DO: Sanitize user input
```javascript
// Good
<div>{sanitizeInput(userInput)}</div>
```

### ❌ DON'T: Expose error details to users
```javascript
// Bad
catch (error) {
  setError(error.stack) // Exposes internal details!
}
```

### ✅ DO: Show user-friendly messages
```javascript
// Good
catch (error) {
  logSecurityEvent('error', { error: error.message })
  setError('Algo salió mal. Por favor, intenta nuevamente.')
}
```

### ❌ DON'T: Skip authentication checks
```javascript
// Bad
function AdminPanel() {
  return <div>Admin content</div> // No protection!
}
```

### ✅ DO: Always protect sensitive components
```javascript
// Good
function AdminPanel() {
  const { user } = useAuth()
  
  if (!hasRequiredRole(user, 'coordinator')) {
    return <Navigate to="/login" />
  }
  
  return <div>Admin content</div>
}
```

## Emergency Procedures

### If You Suspect a Security Breach

1. **Immediate**: Contact the security team
2. **Document**: Take screenshots, save logs
3. **Isolate**: Disable affected features if possible
4. **Don't**: Delete evidence or logs
5. **Communicate**: Inform stakeholders

### If You Find a Vulnerability

1. **Don't**: Exploit it or share publicly
2. **Do**: Report to security team immediately
3. **Document**: Steps to reproduce
4. **Suggest**: Potential fixes if you have ideas
5. **Follow up**: Verify fix is implemented

## Security Contacts

- **Security Team**: security@internado-uv.cl
- **Emergency**: +56 9 XXXX XXXX
- **Bug Reports**: bugs@internado-uv.cl

## Regular Security Tasks

### Daily
- [ ] Monitor security logs
- [ ] Check for failed login attempts
- [ ] Review error rates

### Weekly
- [ ] Review access logs
- [ ] Check for dependency updates
- [ ] Test authentication flows

### Monthly
- [ ] Security audit
- [ ] Update dependencies
- [ ] Review and update security policies
- [ ] Test disaster recovery procedures

## Quick Commands

```bash
# Check for vulnerabilities
npm audit
npm audit fix

# Update dependencies
npm update

# Run security tests
npm run test:security

# Check code quality
npm run lint
```
