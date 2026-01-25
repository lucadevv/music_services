# 🐳 Docker Setup para YouTube Music API Service

## 📋 Requisitos Previos

- Docker >= 20.10
- Docker Compose >= 2.0

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

Copia el archivo de ejemplo y ajusta según necesites:

```bash
cp .env.example .env
```

Edita `.env` y configura:
- `REDIS_HOST=redis` (cuando uses Docker Compose)
- `REDIS_HOST=localhost` (cuando uses Redis externo)
- `REDIS_PASSWORD` (si tu Redis tiene contraseña)

### 2. Asegúrate de tener browser.json

El archivo `browser.json` debe estar en la raíz del proyecto para autenticación con YouTube Music.

### 3. Levantar los Servicios

```bash
# Producción
docker-compose up -d

# Desarrollo (con hot reload si lo configuras)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 4. Verificar que está funcionando

```bash
# Ver logs
docker-compose logs -f api

# Verificar salud
curl http://localhost:8000/health

# Ver estadísticas
curl http://localhost:8000/api/v1/stats/stats
```

## 📦 Servicios Incluidos

### API Service
- **Puerto**: 8000
- **Health Check**: `/health`
- **Documentación**: `/docs`

### Redis (Opcional)
- **Puerto**: 6379
- **Volumen**: `redis_data` (persistente)
- **Health Check**: Automático

## 🔧 Comandos Útiles

### Construir la imagen
```bash
docker-compose build
```

### Ver logs
```bash
# Todos los servicios
docker-compose logs -f

# Solo API
docker-compose logs -f api

# Solo Redis
docker-compose logs -f redis
```

### Detener servicios
```bash
docker-compose down
```

### Detener y eliminar volúmenes
```bash
docker-compose down -v
```

### Reconstruir sin caché
```bash
docker-compose build --no-cache
```

### Ejecutar comandos dentro del contenedor
```bash
docker-compose exec api bash
```

## 🔄 Usar Redis Externo

El `docker-compose.yml` está configurado para usar Redis externo por defecto.

### Configuración Actual
- **Redis externo**: Usa `host.docker.internal` para acceder al Redis del host
- **Cache por defecto**: Usa `memory` (no requiere Redis)
- **Servicio Redis**: Comentado para evitar conflictos

### Opciones de Configuración

1. **Usar Cache en Memoria (Recomendado - Sin Redis)**
   ```env
   CACHE_BACKEND=memory
   ```
   No requiere Redis, funciona perfectamente para desarrollo.

2. **Usar tu Redis Existente**
   ```env
   CACHE_BACKEND=redis
   REDIS_HOST=host.docker.internal  # Para acceder al Redis del host
   REDIS_PORT=6379
   REDIS_DB=0  # Usa una DB diferente si quieres aislar
   REDIS_PASSWORD=  # Si tu Redis tiene contraseña
   ```

3. **Usar Redis de otro Contenedor Docker**
   Si tu Redis está en otro contenedor, puedes:
   - Conectar ambos contenedores a la misma red Docker
   - O usar la IP del contenedor: `REDIS_HOST=172.17.0.1` (ajusta según tu setup)

## 🛠️ Desarrollo

### Hot Reload (Opcional)

Para desarrollo con hot reload, modifica `docker-compose.dev.yml`:

```yaml
services:
  api:
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
```

Luego ejecuta:
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## 🔒 Seguridad

- El contenedor corre como usuario no-root (`appuser`)
- Health checks configurados
- Resource limits establecidos
- Secrets via environment variables

## 📊 Monitoreo

### Ver estadísticas del servicio
```bash
curl http://localhost:8000/api/v1/stats/stats
```

### Ver uso de recursos
```bash
docker stats music_app_api music_app_redis
```

## 🐛 Troubleshooting

### El contenedor no inicia
```bash
# Ver logs detallados
docker-compose logs api

# Verificar configuración
docker-compose config
```

### Error de conexión a Redis
- Verifica que `REDIS_HOST` sea `redis` cuando uses Docker Compose
- Verifica que el servicio Redis esté saludable: `docker-compose ps`

### Error con browser.json
- Asegúrate de que el archivo existe en la raíz
- Verifica permisos: `chmod 644 browser.json`

### Puerto ya en uso
- Cambia el puerto en `.env`: `PORT=8001`
- O detén el servicio que usa el puerto 8000

## 🚀 Producción

Para producción, considera:

1. **Usar secrets de Docker** para contraseñas
2. **Configurar reverse proxy** (Nginx/Traefik)
3. **Habilitar SSL/TLS**
4. **Configurar backups** de Redis
5. **Monitoreo** con Prometheus/Grafana
6. **Logging** centralizado

## 📝 Notas

- El Dockerfile usa multi-stage build para optimizar tamaño
- La imagen final es ~200-300MB (con dependencias)
- Redis es opcional si usas cache en memoria
- El health check verifica `/health` cada 30 segundos
