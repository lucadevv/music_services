# Plan de Seguridad - Music Services

**Fecha**: 2026-03-29
**Estado**: Pendiente de implementación
**Prioridad**: Alta

---

## 1. Autenticación Admin Actual

### Estado Actual
- **Método**: `ADMIN_SECRET_KEY` via header `X-Admin-Key`
- **Ubicación**: `.env` (no commitear)
- **Alcance**: Solo endpoints `/api/v1/auth/*`

### Fortalezas
✅ Simple de implementar
✅ No expone tokens en URLs
✅ Fácil de rotar
✅ Funciona con Docker secrets

### Debilidades
⚠️ Sin expiración automática
⚠️ Sin rate limiting específico
⚠️ Sin audit logging
⚠️ Vulnerable a brute force si no hay rate limiting

---

## 2. Recomendaciones de Seguridad

### Corto Plazoo (Implementar Ahora)

#### 2.1 Rate Limiting en Endpoints Admin
```python
# Agregar a app/api/v1/endpoints/auth.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/browser/from-url")
@limiter.limit("5/minute")  # 5 requests por minuto
async def add_browser_account_from_url(...):
    pass
```

#### 2.2 Audit Logging
```python
# Agregar a cada endpoint admin
import logging

logger = logging.getLogger(__name__)

async def add_browser_account_from_url(...):
    logger.info(f"Admin action: Adding browser account from URL by admin")
    # ... resto del código
```

#### 2.3 Validación de Input
```python
# Agregar validación a URLs
from pydantic import HttpUrl

class BrowserAddFromUrlRequest(BaseModel):
    url: HttpUrl  # Validar que sea URL válida
    name: Optional[str] = None
```

### Mediano Plazo (Considerar para Producción)

#### 2.4 JWT Tokens para Admin
```python
# En lugar de ADMIN_SECRET_KEY simple
from datetime import datetime, timedelta
import jwt

def create_admin_token(admin_key: str) -> str:
    """Create JWT token for admin session."""
    if admin_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(403, "Invalid admin key")
    
    token = jwt.encode({
        "sub": "admin",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=8)
    }, settings.JWT_SECRET_KEY)
    
    return token

def verify_admin_token(token: str) -> bool:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY)
        return payload.get("sub") == "admin"
    except:
        return False
```

#### 2.5 API Keys (Alternativa a JWT)
```python
# O usar API keys estáticas en lugar de tokens
from hashlib import sha256

def validate_api_key(api_key: str) -> bool:
    """Validate API key."""
    expected = sha256.hash(settings.ADMIN_API_KEY.encode()).hexdigest()
    provided = sha256.hash(api_key.encode()).hexdigest()
    return expected == provided
```

---

## 3. Docker Security

### Producción
```yaml
# docker-compose.yml
services:
  api:
    environment:
      - ADMIN_SECRET_KEY=${ADMIN_SECRET_KEY}  # From .env
    secrets:
      - admin_secret_key  # Docker secret
```

### Secrets Management
```bash
# Crear secret
echo "your-super-secret-key-here" | docker secret create admin_secret_key -

# Usar en compose
docker-compose up -d
```

---

## 4. Checklist de Seguridad

- [x] Variables sensibles en `.env` (no commitear)
- [x] `.env` en `.gitignore`
- [x] Rate limiting habilitado
- [x] CORS configurado correctamente
- [ ] Audit logging implementado
- [ ] HTTPS en producción
- [ ] API keys rotadas regularmente
- [ ] Tests de seguridad
- [ ] Documentación de seguridad

---

## 5. Próximos Pasos
1. **Implementar rate limiting** (1-2 horas)
2. **Agregar audit logging** (1 hora)
3. **Crear tests de seguridad** (2-3 horas)
4. **Documentar procedimientos** (1 hora)
5. **Configurar HTTPS** (30 min)
6. **Establecer rotación de keys** (30 min)

---

## 6. Referencias
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)
