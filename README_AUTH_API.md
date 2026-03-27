# API de Autenticación OAuth

Documentación de los endpoints de administración OAuth para configurar la autenticación de YouTube Music desde un panel admin.

## Requisitos

- **ADMIN_SECRET_KEY** configurado en `.env` (obligatorio)
- Todas las requests a `/api/v1/auth/*` requieren el header `X-Admin-Key`
- Redis corriendo (para almacenar credenciales y sesiones)

## Header de Autenticación

Todas las requests requieren:

```http
X-Admin-Key: tu-clave-secreta-configurada-en-env
```

Sin este header, todos los endpoints retornan `403 Forbidden`.

---

## Endpoints

### 1. Guardar Credenciales OAuth

```http
POST /api/v1/auth/credentials
X-Admin-Key: tu-clave-secreta
Content-Type: application/json

{
  "client_id": "188268615112-xxxxx.apps.googleusercontent.com",
  "client_secret": "GOCSPX-xxxxxxxxx"
}
```

**Response 200:**

```json
{
  "has_credentials": true,
  "updated_at": "2026-03-27T16:00:00Z"
}
```

**Error 403:** Admin key inválida o no configurada.

---

### 2. Consultar Estado de Credenciales

```http
GET /api/v1/auth/credentials
X-Admin-Key: tu-clave-secreta
```

**Response 200:**

```json
{
  "has_credentials": true,
  "updated_at": "2026-03-27T16:00:00Z"
}
```

> No expone los valores reales de client_id ni client_secret.

---

### 3. Iniciar Flujo OAuth

```http
POST /api/v1/auth/oauth/start
X-Admin-Key: tu-clave-secreta
```

**Response 200:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "verification_url": "https://www.google.com/device",
  "user_code": "ABCD-EFGH",
  "expires_in": 900,
  "interval": 5
}
```

**Campos:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `session_id` | string | ID único de sesión. Usar para polling. |
| `verification_url` | string | URL que el usuario debe abrir |
| `user_code` | string | Código que el usuario debe ingresar en la URL |
| `expires_in` | int | Segundos hasta que expire la sesión (~15 min) |
| `interval` | int | Segundos recomendados entre cada polling (5s) |

**Error 400:** No hay credenciales guardadas. Llama primero a `POST /credentials`.

---

### 4. Verificar Autorización (Polling)

```http
POST /api/v1/auth/oauth/poll
X-Admin-Key: tu-clave-secreta
Content-Type: application/json

{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response 200 — Pendiente:**

```json
{
  "status": "pending",
  "message": "Waiting for user authorization"
}
```

→ El usuario aún no autorizó. Volver a llamar en 5 segundos.

**Response 200 — Autorizado:**

```json
{
  "status": "authorized",
  "message": "OAuth token saved successfully"
}
```

→ Token guardado en `oauth.json`. El servicio ya puede usar YouTube Music.

**Error 404:** Sesión no encontrada o expirada. Iniciar nuevo flujo.

**Error 410:** Sesión expirada o denegada por el usuario. Iniciar nuevo flujo.

---

### 5. Estado de Autenticación

```http
GET /api/v1/auth/status
X-Admin-Key: tu-clave-secreta
```

**Response 200:**

```json
{
  "authenticated": true,
  "has_credentials": true,
  "has_token": true,
  "method": "oauth"
}
```

**Campos:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `authenticated` | bool | El cliente YTMusic puede hacer requests reales a YouTube |
| `has_credentials` | bool | Hay credenciales OAuth almacenadas |
| `has_token` | bool | El archivo oauth.json existe |
| `method` | string | Método de autenticación (siempre "oauth") |

---

## Schemas

### CredentialsRequest

```json
{
  "client_id": "string (requerido, min 10 chars)",
  "client_secret": "string (requerido, min 10 chars)"
}
```

### CredentialsResponse

```json
{
  "has_credentials": "boolean",
  "updated_at": "string | null (ISO 8601)"
}
```

### OAuthStartResponse

```json
{
  "session_id": "string (UUID)",
  "verification_url": "string (URL)",
  "user_code": "string (XXXX-XXXX)",
  "expires_in": "integer (segundos)",
  "interval": "integer (segundos)"
}
```

### OAuthPollRequest

```json
{
  "session_id": "string (requerido, min 1 char)"
}
```

### OAuthPollPendingResponse

```json
{
  "status": "pending",
  "message": "Waiting for user authorization"
}
```

### OAuthPollAuthorizedResponse

```json
{
  "status": "authorized",
  "message": "OAuth token saved successfully"
}
```

### AuthStatusResponse

```json
{
  "authenticated": "boolean",
  "has_credentials": "boolean",
  "has_token": "boolean",
  "method": "oauth"
}
```

---

## Flujo Completo (Panel Admin)

```
1. GET /auth/status
   ← { authenticated: false, has_credentials: false, has_token: false }
   
2. Admin ingresa Client ID + Client Secret en el panel
   
3. POST /auth/credentials
   Body: { "client_id": "...", "client_secret": "..." }
   ← { has_credentials: true, updated_at: "..." }
   
4. POST /auth/oauth/start
   ← { session_id: "...", verification_url: "...", user_code: "XXXX-XXXX", ... }
   
5. Panel muestra al usuario:
   "Abre https://www.google.com/device e ingresa el código XXXX-XXXX"
   
6. El usuario abre la URL, ingresa el código y autoriza con su cuenta Google
   
7. Panel → POST /auth/oauth/poll (cada 5 segundos)
   ← { status: "pending" }  → seguir polling
   ← { status: "authorized" }  → listo!
   
8. GET /auth/status
   ← { authenticated: true, has_credentials: true, has_token: true }
   
9. El servicio ya puede hacer requests a YouTube Music ✅
```

---

## Códigos de Error

| Status | Código | Descripción |
|--------|--------|-------------|
| 400 | `NO_CREDENTIALS` | No hay credenciales OAuth configuradas |
| 403 | `FORBIDDEN` | Admin key inválida o no configurada |
| 404 | `SESSION_NOT_FOUND` | Sesión de OAuth no encontrada o expirada |
| 410 | `SESSION_GONE` | Sesión expirada o denegada por el usuario |
| 500 | `TOKEN_SAVE_ERROR` | Error escribiendo oauth.json |
| 502 | `GOOGLE_OAUTH_ERROR` | Error comunicándose con Google OAuth |

---

## Swagger y OpenAPI

- **Swagger UI**: `http://localhost:8000/docs` — Interfaz interactiva para probar endpoints
- **ReDoc**: `http://localhost:8000/redoc` — Documentación alternativa
- **OpenAPI JSON**: `http://localhost:8000/openapi.json` — Spec descargable
- **OpenAPI YAML**: `http://localhost:8000/openapi.yaml` — Spec en formato YAML

Para descargar el spec:

```bash
curl http://localhost:8000/openapi.json > openapi.json
curl http://localhost:8000/openapi.yaml > openapi.yaml
```

---

## Notas Técnicas

### Storage en Redis

| Key | Contenido | TTL |
|-----|-----------|-----|
| `music:auth:oauth:credentials` | `{client_id, client_secret, updated_at}` | Sin TTL (persistente) |
| `music:auth:oauth:session:{uuid}` | `{device_code, user_code, ...}` | `expires_in` de Google (~15 min) |

### Workaround Bug ytmusicapi 1.10.3

Google ahora devuelve un campo `refresh_token_expires_in` que causa un `TypeError` en
`RefreshingToken.__init__()`. El endpoint `/auth/oauth/poll` filtra automáticamente
este campo y solo guarda los campos esperados por ytmusicapi en `oauth.json`.

### Renovación Automática

Una vez configurado, `ytmusicapi` renueva el `access_token` automáticamente usando el
`refresh_token`. El archivo `oauth.json` se actualiza en disco en cada renovación.
Por esto, el volume de Docker **no debe ser `:ro`** (read-only).

### Invalidación de Cache

Cuando se actualizan credenciales o se genera un nuevo token, se llama a
`reset_ytmusic_client()` que limpia el cache `@lru_cache()` del cliente YTMusic,
forzando su re-creación con los nuevos datos.
