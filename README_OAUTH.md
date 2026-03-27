# Configuración de YTMusicAPI con OAuth

Este documento explica cómo configurar la autenticación OAuth para usar ytmusicapi con YouTube Music.

## Requisitos Previos

- Python 3.9 o superior
- Una cuenta de Google
- Acceso a la consola de Google Cloud Platform

## Configuración Rápida

### 1. Crear un entorno virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # En macOS/Linux
# o
venv\Scripts\activate  # En Windows
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar credenciales en Google Cloud Console

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un nuevo proyecto o seleccionar uno existente
3. Ir a **APIs & Services** > **Library**
4. Buscar y habilitar **YouTube Data API v3**
5. Ir a **APIs & Services** > **Credentials**
6. Crear **OAuth 2.0 Client ID**:
   - Application type: **TVs and Limited Input Devices** (Device Flow)
   - Nombre: el que quieras (ej. `music-services`)
7. Copiar el **Client ID** y **Client Secret**

### 4. Configurar variables de entorno

Editar el archivo `.env` con las credenciales obtenidas:

```env
OAUTH_JSON_PATH=./oauth.json
YTMUSIC_CLIENT_ID=tu_client_id_aqui.apps.googleusercontent.com
YTMUSIC_CLIENT_SECRET=tu_client_secret_aqui
```

### 5. Generar el archivo oauth.json

> **Nota:** Existe un bug conocido en ytmusicapi 1.10.3 donde Google devuelve un campo `refresh_token_expires_in` que causa un error `TypeError`. Se recomienda usar el script de generación manual incluido en el proyecto.

```bash
python scripts/generate_oauth.py
```

El script te pedirá:
1. **Client ID** (pegar el de `.env`)
2. **Client Secret** (pegar el de `.env`)
3. Abre una URL en el browser para autorizar la app
4. Espera a que completes la autorización
5. Genera `oauth.json` automáticamente

### 6. Verificar que funciona

```bash
python -c "from app.core.ytmusic_client import get_ytmusic_client; client = get_ytmusic_client(); print(client.search('rick astley', filter='songs', limit=1)[0]['title'])"
```

Si todo está bien, deberías ver el título de una canción.

## Flujo de Autenticación

```
1. Tu app solicita acceso con Client ID + Client Secret
                    ↓
2. Google devuelve: verification_url + user_code
                    ↓
3. El usuario abre la URL e ingresa el código
                    ↓
4. El usuario autoriza la app con su cuenta de Google
                    ↓
5. Google devuelve un refresh_token
                    ↓
6. Se guarda en oauth.json
                    ↓
7. ytmusicapi usa el refresh_token para obtener access_tokens automáticamente
```

## Estructura del archivo oauth.json

```json
{
  "access_token": "ya29.a0AfH6SMB...",
  "expires_in": 3600,
  "scope": "https://www.googleapis.com/auth/youtube",
  "token_type": "Bearer",
  "refresh_token": "1//0dx7...",
  "expires_at": 1711596000
}
```

## Renovación Automática

- El `access_token` expira cada ~1 hora
- `ytmusicapi` lo renueva automáticamente usando el `refresh_token` (que no expira)
- Cada vez que se renueva, se actualiza `oauth.json` en disco
- **Importante:** En Docker, el volume de `oauth.json` debe ser **writable** (no `:ro`)

## Solución de Problemas

### Error: `Token refresh error. Most likely client/token mismatch`

El `oauth.json` fue generado con credenciales diferentes a las del `.env`.

**Solución:** Regenerar `oauth.json` con el mismo Client ID y Client Secret que están en `.env`.

### Error: `TypeError: __init__() got an unexpected keyword argument 'refresh_token_expires_in'`

Bug de ytmusicapi 1.10.3. Google agregó un campo nuevo que la librería no maneja.

**Solución:** Usar el script `scripts/generate_oauth.py` en vez del CLI `ytmusicapi oauth`.

### Error: `FileNotFoundError: No se encontró archivo de autenticación`

No existe `oauth.json` en la ruta configurada.

**Solución:** Ejecutar el paso 5 de la configuración.
