# Authentication Flow - Fixed ✅

## What Was Fixed

### 1. Frontend Navigation (LoginPage.jsx)
**Problem:** After successful login, users stayed on the login page
**Fix:** Added `useNavigate` hook and redirect logic based on user role

```javascript
const role = await login(email, password)
const dashboards = {
  student: '/student',
  tutor: '/tutor',
  coordinator: '/coordinator',
}
navigate(dashboards[role] || '/login')
```

### 2. Keycloak Role Assignment
**Problem:** Users existed in Keycloak but had no realm roles assigned
**Fix:** Ran migration script to assign roles:
```bash
python -m scripts.migrate_to_keycloak
```

### 3. Backend Token Decoding (keycloak_client.py)
**Problem:** JWT decoding used incorrect python-jose syntax
**Fix:** Corrected the `decode_token()` function:

```python
from jose import jwt

# Get Keycloak's public key
public_key_raw = keycloak_openid.public_key()
public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key_raw}\n-----END PUBLIC KEY-----"

# Decode with correct python-jose syntax
decoded = jwt.decode(
    token,
    public_key,
    algorithms=["RS256"],
    audience=None,
    options={"verify_aud": False}
)
```

### 4. Backend Auth Dependency (deps.py)
**Problem:** Was calling `get_user_info()` which doesn't include realm_access.roles
**Fix:** Changed to `decode_token()` to get roles from JWT claims directly

```python
token_claims = decode_token(token, validate=False)
user_id = token_claims.get("sub")
role = get_primary_role(token_claims)  # Extracts role from realm_access.roles
```

## Current Authentication Flow

1. ✅ User enters credentials in React login form
2. ✅ Frontend → `POST /auth/login` → Backend
3. ✅ Backend → Keycloak token endpoint (grant_type=password)
4. ✅ Keycloak → Returns JWT with `realm_access.roles: ["coordinator"]`
5. ✅ Backend → Returns token to frontend
6. ✅ Frontend → Stores token & navigates to role-specific dashboard
7. ✅ Frontend → Sends `Authorization: Bearer <token>` on API requests
8. ✅ Backend → Validates token with Keycloak introspection
9. ✅ Backend → Decodes JWT to extract `sub` and `realm_access.roles`
10. ✅ Backend → Authorizes request based on user role

## Test Credentials

All users have been assigned their proper roles in Keycloak:

- **Coordinator:** `coord@internado-uv.cl` / `coord123`
- **Tutor:** `tutor@internado-uv.cl` / `tutor123`  
- **Student:** `estudiante@internado-uv.cl` / `estudiante123`

## Verification

Login is working:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"coord@internado-uv.cl","password":"coord123"}'
```

Returns:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "expires_in": 300,
  "token_type": "Bearer"
}
```

Protected endpoints work:
```bash
TOKEN="<access_token_from_login>"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/dashboard/overview
```

Returns actual data (not 401 Unauthorized).

## Token Structure

The JWT now correctly includes:
```json
{
  "sub": "d41b3764-1a72-4bf9-87b2-8588a25131f1",
  "email": "coord@internado-uv.cl",
  "realm_access": {
    "roles": ["coordinator", "default-roles-internado-uv", ...]
  }
}
```

The backend extracts the `coordinator` role from `realm_access.roles` and uses it for authorization.

## Files Modified

1. `frontend/src/pages/LoginPage.jsx` - Added navigation after login
2. `backend/app/core/deps.py` - Changed to decode token for roles
3. `backend/app/core/keycloak_client.py` - Fixed JWT decode syntax
4. Keycloak users - Assigned realm roles via migration script

## Status: ✅ WORKING

All authentication and authorization is now functioning correctly.
