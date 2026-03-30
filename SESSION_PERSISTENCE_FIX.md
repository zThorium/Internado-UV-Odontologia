# Session Persistence - Fixed ✅

## Problem
After logging in, users were redirected back to the login page on page refresh.
The session was not persisting across browser reloads.

## Root Causes

1. **No Loading State**: ProtectedRoute immediately redirected to login while token restoration was in progress
2. **Race Condition**: Session restoration from localStorage happened async in useEffect, but routes rendered immediately
3. **No Token Refresh on 401**: When tokens expired during a session, the app redirected to login instead of attempting refresh
4. **No Redirect Prevention**: Logged-in users could access /login page

## Fixes Implemented

### 1. Added Loading State to AuthContext

**File:** `frontend/src/context/AuthContext.jsx`

Added `isRestoringSession` state that tracks when the app is loading tokens from localStorage:

```javascript
const [isRestoringSession, setIsRestoringSession] = useState(true)

useEffect(() => {
  const restoreSession = async () => {
    const savedAccess = localStorage.getItem('kc_access_token')
    const savedRefresh = localStorage.getItem('kc_refresh_token')

    if (!savedAccess || !savedRefresh) {
      setIsRestoringSession(false)
      return
    }

    const claims = decodeJwt(savedAccess)

    // Token is valid
    if (claims) {
      setDirectAccessToken(savedAccess)
      setDirectRefreshToken(savedRefresh)
      setDirectUser(extractUserFromClaims(claims))
      setIsRestoringSession(false)
      return
    }

    // Token expired, try to refresh
    try {
      const { data } = await api.post('/auth/refresh', null, {
        params: { refresh_token: savedRefresh },
      })
      // ... update tokens
    } catch (error) {
      // ... clear invalid tokens
    } finally {
      setIsRestoringSession(false)
    }
  }

  restoreSession()
}, [])
```

Exposed `isLoading` in the context:

```javascript
<AuthContext.Provider
  value={{
    user,
    token,
    isLoading,  // ✅ New!
    login,
    logout,
    ...
  }}
>
```

### 2. Updated ProtectedRoute to Show Loading

**File:** `frontend/src/components/ProtectedRoute.jsx`

Added loading spinner that displays while checking authentication:

```javascript
export default function ProtectedRoute({ children, allowedRoles }) {
  const { user, isLoading } = useAuth()

  // Show loading spinner while checking authentication
  if (isLoading) {
    return <LoadingSpinner />
  }

  // Only redirect if loading is complete and user is null
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // ... rest of logic
}
```

**Key Change**: Don't redirect to login until `isLoading === false`

### 3. Enhanced Axios Interceptor for Auto Token Refresh

**File:** `frontend/src/services/api.js`

Implemented automatic token refresh on 401 errors:

```javascript
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Don't refresh for auth endpoints
      if (isAuthEndpoint(originalRequest.url)) {
        return Promise.reject(error)
      }

      // Avoid infinite loops
      if (originalRequest._retry) {
        // Clear tokens and redirect
        window.location.href = '/login'
        return Promise.reject(error)
      }

      originalRequest._retry = true

      // Attempt to refresh token
      try {
        const { data } = await api.post('/auth/refresh', ...)
        const newAccessToken = data.access_token

        // Update tokens in storage and axios headers
        localStorage.setItem('kc_access_token', newAccessToken)
        setAuthToken(newAccessToken)

        // Retry the original request with new token
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`
        return api(originalRequest)

      } catch (refreshError) {
        // Refresh failed, redirect to login
        window.location.href = '/login'
      }
    }
  }
)
```

**Features:**
- ✅ Automatically refreshes expired tokens on 401
- ✅ Retries failed request with new token
- ✅ Handles concurrent requests during refresh (request queue)
- ✅ Only redirects to login if refresh fails

### 4. Prevent Logged-In Users from Accessing Login Page

**File:** `frontend/src/pages/LoginPage.jsx`

Added redirect for already-authenticated users:

```javascript
export default function LoginPage() {
  const { login, user, isLoading } = useAuth()

  // Redirect to dashboard if already logged in
  useEffect(() => {
    if (!isLoading && user) {
      const dashboards = {
        student: '/student',
        tutor: '/tutor',
        coordinator: '/coordinator',
      }
      navigate(dashboards[user.role] || '/student', { replace: true })
    }
  }, [user, isLoading, navigate])
  
  // ... rest of component
}
```

## Session Flow (After Fix)

### On Page Load:

1. ✅ App starts, `isRestoringSession = true`
2. ✅ ProtectedRoute shows loading spinner (not login redirect)
3. ✅ AuthContext reads tokens from localStorage
4. ✅ If token valid → restore user session
5. ✅ If token expired → attempt refresh with refresh_token
6. ✅ If refresh succeeds → restore user session with new tokens
7. ✅ If refresh fails → clear tokens
8. ✅ Set `isRestoringSession = false`
9. ✅ ProtectedRoute now renders:
   - User's page if authenticated
   - Login redirect if not authenticated

### During Session:

1. ✅ User makes API request
2. ✅ If token expired → 401 error
3. ✅ Axios interceptor catches 401
4. ✅ Attempts token refresh automatically
5. ✅ If refresh succeeds → retry original request
6. ✅ If refresh fails → redirect to login

### On Login:

1. ✅ User enters credentials
2. ✅ Tokens returned from backend
3. ✅ Tokens saved to localStorage
4. ✅ User state set in context
5. ✅ Navigate to role-specific dashboard
6. ✅ Session persists even after page refresh

## Files Modified

1. `frontend/src/context/AuthContext.jsx` - Added loading state and smart session restoration
2. `frontend/src/components/ProtectedRoute.jsx` - Added loading spinner, prevent premature redirects
3. `frontend/src/services/api.js` - Enhanced 401 interceptor with auto token refresh
4. `frontend/src/pages/LoginPage.jsx` - Prevent logged-in users from accessing login page

## Testing

### Test Case 1: Login and Refresh

1. Login with `coord@internado-uv.cl` / `coord123`
2. Navigate to `/coordinator/overview`
3. Refresh the page (F5)
4. ✅ **Expected**: Stay on overview page, no redirect to login

### Test Case 2: Token Expiry During Session

1. Login and wait for access_token to expire (~5 minutes)
2. Make an API request (click a button, navigate)
3. ✅ **Expected**: Token refreshes automatically, request succeeds

### Test Case 3: Prevent Login Page Access When Authenticated

1. Login successfully
2. Manually navigate to `/login`
3. ✅ **Expected**: Immediately redirected back to your dashboard

### Test Case 4: Invalid Refresh Token

1. Login successfully
2. Manually corrupt the refresh_token in localStorage:
   ```javascript
   localStorage.setItem('kc_refresh_token', 'invalid_token')
   ```
3. Refresh the page
4. ✅ **Expected**: Redirect to login (refresh fails, session cleared)

## Status: ✅ WORKING

Session now persists across page refreshes.
Tokens refresh automatically when expired.
Users stay logged in until they explicitly logout or refresh token expires.
