# 🎵 YouTube Music API Service

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

**Servicio de alto rendimiento para la extracción de música, metadatos y streaming directo.**
*Construido con FastAPI, ytmusicapi y yt-dlp.*

[Reportar Bug](https://github.com/lucadevv/music_services/issues) · [Solicitar Feature](https://github.com/lucadevv/music_services/issues)

</div>

---

## 🚀 ¿Qué hace este servicio?

Este no es solo un wrapper de la API de YouTube Music. Es un ecosistema completo diseñado para ser el motor musical de aplicaciones modernas. Provee una interfaz estandarizada para buscar, navegar y, lo más importante, obtener **flujos de audio directo (streams)** de alta calidad sin las complicaciones de las cuotas de API oficiales.

### ✨ Características Principales

- 🔍 **Búsqueda Avanzada**: Resultados precisos para canciones, álbumes, artistas y playlists.
- 🎧 **Streaming Inteligente**: URLs directas (best audio) con sistema de enriquecimiento en runtime para evitar expiración de enlaces.
- 🌍 **Soporte Multi-plataforma**: Nuevo endpoint genérico `yt-dlp` para extraer audio/video de prácticamente cualquier red social (TikTok, IG, Twitter, etc.).
- 🛡️ **Arquitectura Resiliente**: Circuit Breaker para protección contra bloqueos y Rate Limiting integrado.
- ⚡ **Caché de Dos Niveles**: Metadata cacheada por 24h y Stream URLs por 1h usando Redis.
- 🔐 **Seguridad Dual**: Separación clara entre acceso de usuario (`Bearer Token`) y gestión administrativa (`X-Admin-Key`).

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Rol |
| :--- | :--- | :--- |
| **Framework** | FastAPI | Core API & OpenAPI Spec |
| **Runtime** | Python 3.11+ | Motor de ejecución |
| **Streaming** | yt-dlp | Extracción de streams de alta calidad |
| **Metadata** | ytmusicapi | Interfaz con YouTube Music |
| **Caché** | Redis 7 | Almacenamiento persistente y temporal |
| **Despliegue** | Docker | Containerización completa |

---

## 🔐 Seguridad y Autenticación

El servicio implementa una separación de responsabilidades estricta:

### 🎵 Music Endpoints (`/api/v1/music/*`)
Requieren una **API Key** de usuario.
```bash
Authorization: Bearer <tu_api_key>
```

### 🔐 Admin Endpoints (`/api/v1/admin/*`)
Requieren la **Master Admin Key** configurada en el servidor.
```bash
X-Admin-Key: <admin_secret_key>
```

---

## 📦 Instalación y Uso (Docker)

La forma recomendada de correr este servicio es usando Docker para asegurar que todas las dependencias (Redis, Postgres) estén listas.

1. **Clonar el repo**
   ```bash
   git clone https://github.com/lucadevv/music_services.git
   cd music_services
   ```

2. **Configurar entorno**
   ```bash
   cp .env.example .env
   # Edita .env con tus credenciales
   ```

3. **Levantar con Docker Compose**
   ```bash
   docker compose up -d --build
   ```

4. **Acceder a la documentación**
   - **Swagger UI**: `http://localhost:8000/docs`
   - **ReDoc**: `http://localhost:8000/redoc`

---

## 🗺️ Estructura de Endpoints (Estandarizada)

### 🎵 Música (`/api/v1/music`)
- `GET /search` - Búsqueda global y sugerencias.
- `GET /browse` - Artistas, álbumes, letras y navegación por casa.
- `GET /explore` - Charts mundiales, moods y géneros.
- `GET /stream` - Obtención de URLs directas y proxy de audio.
- `GET /ytdlp` - **(Nuevo)** Extracción genérica de cualquier red social.

### 🔐 Administración (`/api/v1/admin`)
- `GET /api-keys` - Gestión de llaves de acceso de usuarios.
- `GET /stats` - Métricas de rendimiento, caché y uso.
- `GET /cache` - Gestión manual del almacenamiento en Redis.
- `GET /auth` - Configuración de cuentas de navegador.

---

<div align="center">
Desarrollado con ❤️ para la comunidad musical.
</div>
