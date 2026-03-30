/**
 * Security utilities for the application
 * Implements best practices for authentication and authorization
 */

/**
 * Validates if a token is expired
 * @param {string} token - JWT token
 * @returns {boolean} - True if expired
 */
export function isTokenExpired(token) {
  if (!token) return true
  
  try {
    const payloadPart = token.split('.')[1]
    if (!payloadPart) return true
    
    const normalized = payloadPart.replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(normalized))
    
    if (!payload.exp) return true
    
    // Add 30 second buffer to prevent edge cases
    return payload.exp * 1000 < Date.now() + 30000
  } catch {
    return true
  }
}

/**
 * Sanitizes user input to prevent XSS attacks
 * @param {string} input - User input
 * @returns {string} - Sanitized input
 */
export function sanitizeInput(input) {
  if (typeof input !== 'string') return input
  
  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;')
}

/**
 * Validates email format
 * @param {string} email - Email to validate
 * @returns {boolean} - True if valid
 */
export function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Validates password strength
 * @param {string} password - Password to validate
 * @returns {object} - Validation result with isValid and message
 */
export function validatePasswordStrength(password) {
  if (!password || password.length < 8) {
    return {
      isValid: false,
      message: 'La contraseña debe tener al menos 8 caracteres'
    }
  }
  
  if (!/[a-z]/.test(password)) {
    return {
      isValid: false,
      message: 'La contraseña debe contener al menos una letra minúscula'
    }
  }
  
  if (!/[A-Z]/.test(password)) {
    return {
      isValid: false,
      message: 'La contraseña debe contener al menos una letra mayúscula'
    }
  }
  
  if (!/[0-9]/.test(password)) {
    return {
      isValid: false,
      message: 'La contraseña debe contener al menos un número'
    }
  }
  
  return { isValid: true, message: 'Contraseña válida' }
}

/**
 * Checks if user has required role
 * @param {object} user - User object with role property
 * @param {string|string[]} allowedRoles - Role or array of roles
 * @returns {boolean} - True if user has required role
 */
export function hasRequiredRole(user, allowedRoles) {
  if (!user || !user.role) return false
  
  if (Array.isArray(allowedRoles)) {
    return allowedRoles.includes(user.role)
  }
  
  return user.role === allowedRoles
}

/**
 * Securely clears all authentication data
 */
export function clearAuthData() {
  // Clear localStorage
  localStorage.removeItem('kc_access_token')
  localStorage.removeItem('kc_refresh_token')
  
  // Clear sessionStorage
  sessionStorage.clear()
  
  // Clear cookies (if any)
  document.cookie.split(";").forEach((c) => {
    document.cookie = c
      .replace(/^ +/, "")
      .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/")
  })
}

/**
 * Detects potential security threats in URLs
 * @param {string} url - URL to check
 * @returns {boolean} - True if URL is safe
 */
export function isSafeUrl(url) {
  if (!url) return false
  
  // Block javascript: and data: protocols
  if (url.match(/^(javascript|data|vbscript):/i)) {
    return false
  }
  
  // Only allow relative URLs or same origin
  try {
    const urlObj = new URL(url, window.location.origin)
    return urlObj.origin === window.location.origin
  } catch {
    // If URL parsing fails, assume it's a relative URL (safe)
    return !url.startsWith('http')
  }
}

/**
 * Rate limiting helper for client-side
 * @param {string} key - Unique key for the action
 * @param {number} maxAttempts - Maximum attempts allowed
 * @param {number} windowMs - Time window in milliseconds
 * @returns {boolean} - True if action is allowed
 */
export function checkRateLimit(key, maxAttempts = 5, windowMs = 60000) {
  const now = Date.now()
  const storageKey = `rate_limit_${key}`
  
  try {
    const data = JSON.parse(localStorage.getItem(storageKey) || '{"attempts":[],"blocked":false}')
    
    // Remove old attempts outside the window
    data.attempts = data.attempts.filter(timestamp => now - timestamp < windowMs)
    
    // Check if blocked
    if (data.blocked && data.blockedUntil > now) {
      return false
    }
    
    // Check if exceeded max attempts
    if (data.attempts.length >= maxAttempts) {
      data.blocked = true
      data.blockedUntil = now + windowMs
      localStorage.setItem(storageKey, JSON.stringify(data))
      return false
    }
    
    // Add current attempt
    data.attempts.push(now)
    data.blocked = false
    localStorage.setItem(storageKey, JSON.stringify(data))
    
    return true
  } catch {
    // If localStorage fails, allow the action
    return true
  }
}

/**
 * Logs security events for monitoring
 * @param {string} event - Event type
 * @param {object} details - Event details
 */
export function logSecurityEvent(event, details = {}) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    event,
    details,
    userAgent: navigator.userAgent,
    url: window.location.href,
  }
  
  // In production, send to monitoring service
  if (import.meta.env.PROD) {
    // TODO: Send to monitoring service (e.g., Sentry, LogRocket)
    console.info('[Security Event]', logEntry)
  } else {
    console.warn('[Security Event]', logEntry)
  }
}

/**
 * Detects if user is on a secure connection
 * @returns {boolean} - True if HTTPS or localhost
 */
export function isSecureConnection() {
  return window.location.protocol === 'https:' || 
         window.location.hostname === 'localhost' ||
         window.location.hostname === '127.0.0.1'
}

/**
 * Prevents clickjacking attacks
 */
export function preventClickjacking() {
  if (window.self !== window.top) {
    // Page is in an iframe
    logSecurityEvent('clickjacking_attempt', {
      parentUrl: document.referrer
    })
    
    // Break out of iframe
    window.top.location = window.self.location
  }
}

/**
 * Content Security Policy violation handler
 */
export function setupCSPReporting() {
  document.addEventListener('securitypolicyviolation', (e) => {
    logSecurityEvent('csp_violation', {
      violatedDirective: e.violatedDirective,
      blockedURI: e.blockedURI,
      sourceFile: e.sourceFile,
      lineNumber: e.lineNumber,
    })
  })
}
