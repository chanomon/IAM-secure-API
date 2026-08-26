
# IAM-Secure API

Microservicio de gestión de identidades y accesos (IAM) desarrollado con FastAPI. Implementa registro y autenticación de usuarios, emisión de tokens JWT y autorización basada en roles y permisos (RBAC).

> **Estado actual:** prototipo funcional en desarrollo. La estructura principal está definida, pero existen algunos problemas que deben corregirse antes de utilizarlo en producción.

## Características

- Registro de usuarios.
- Contraseñas protegidas con bcrypt.
- Inicio de sesión mediante correo y contraseña.
- Tokens JWT de acceso y renovación.
- Access tokens con vigencia de 15 minutos.
- Refresh tokens con vigencia de 7 días.
- Autorización RBAC mediante roles y permisos.
- Persistencia en PostgreSQL mediante SQLAlchemy.
- Infraestructura local con Docker Compose.
- Documentación OpenAPI automática con Swagger UI.
- Modelo preparado para almacenar metadatos de auditoría del usuario.

## Stack tecnológico

| Componente | Tecnología |
| --- | --- |
| API | FastAPI 0.115 |
| Servidor ASGI | Uvicorn |
| Base de datos | PostgreSQL 15 |
| ORM | SQLAlchemy 2 |
| Validación | Pydantic 2 |
| Autenticación | JWT con python-jose |
| Hash de contraseñas | Passlib + bcrypt |
| Caché prevista | Redis 7 |
| Contenedores | Docker y Docker Compose |
| Python | 3.11 |

## Arquitectura

```text
iam-service/
├── app/
│   ├── main.py                      # Aplicación y endpoints de usuarios
│   ├── api/
│   │   ├── deps.py                  # Sesiones, autenticación y permisos
│   │   └── v1/endpoints/
│   │       └── auth.py              # Login y renovación de tokens
│   ├── core/
│   │   ├── config.py                # Configuración de la aplicación
│   │   ├── database.py              # Engine y sesiones SQLAlchemy
│   │   ├── security.py              # Hashing y operaciones JWT
│   │   └── seed.py                  # Permisos y rol Admin iniciales
│   └── models/
│       ├── db_models.py             # Modelos SQLAlchemy
│       └── schemas.py               # Esquemas Pydantic
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

El flujo principal de seguridad es:

```text
Credenciales
    ↓
POST /api/v1/auth/login
    ↓
Access token + Refresh token
    ↓
Authorization: Bearer <access_token>
    ↓
Validación del usuario
    ↓
Verificación del permiso RBAC
    ↓
Acceso al recurso
```

## Modelo de datos

### User

Representa una identidad del sistema.

- `id`
- `email`
- `hashed_password`
- `is_active`
- `metadata_json`
- Relación muchos-a-muchos con roles

### Role

Agrupa permisos y puede asignarse a varios usuarios.

- `id`
- `name`
- `description`
- Relación muchos-a-muchos con usuarios
- Relación muchos-a-muchos con permisos

### Permission

Representa una acción sobre un recurso.

- `id`
- `name`, por ejemplo `users:read`
- `resource`, por ejemplo `users`
- `action`, por ejemplo `read`

Las relaciones se almacenan en las tablas asociativas `user_roles` y `role_permissions`.

## Endpoints

| Método | Ruta | Descripción | Protección |
| --- | --- | --- | --- |
| POST | `/api/v1/users` | Registra un usuario | Pública |
| GET | `/api/v1/users` | Lista los usuarios | Permiso `users:read` |
| POST | `/api/v1/auth/login` | Autentica y entrega tokens | Pública |
| POST | `/api/v1/auth/refresh` | Renueva ambos tokens | Refresh token |

### Registrar un usuario

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "password": "una-clave-segura"
  }'
```

La contraseña debe contener al menos ocho caracteres.

### Iniciar sesión

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "password": "una-clave-segura"
  }'
```

Respuesta esperada:

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer"
}
```

### Consultar usuarios

```bash
curl http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer <access_token>"
```

El usuario correspondiente al token debe tener un rol que contenga el permiso `users:read`.

### Renovar los tokens

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token>"
  }'
```

## Ejecución con Docker

El método previsto para ejecutar el proyecto es Docker Compose:

```bash
docker compose up --build
```

Esto levanta:

- API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

Documentación interactiva:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI: `http://localhost:8000/openapi.json`

Para detener los servicios:

```bash
docker compose down
```

Para eliminar también el volumen persistente de PostgreSQL:

```bash
docker compose down --volumes
```

## Configuración

La aplicación reconoce las siguientes variables:

| Variable | Valor predeterminado | Descripción |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL local o servicio `postgres` | Conexión a la base |
| `REDIS_URL` | `redis://redis:6379/0` | Conexión prevista a Redis |
| `SECRET_KEY` | Clave insegura de desarrollo | Firma de tokens JWT |

Para un entorno real se debe proporcionar obligatoriamente una clave secreta robusta:

```env
SECRET_KEY=<clave-aleatoria-larga>
DATABASE_URL=postgresql://user:pass@postgres:5432/iam_db
REDIS_URL=redis://redis:6379/0
```

## Datos iniciales

El módulo `core/seed.py` define estos permisos:

- `users:read`
- `users:write`
- `users:delete`
- `roles:read`

También crea un rol `Admin` y le asigna los permisos disponibles.

Actualmente el procedimiento no se ejecuta automáticamente. Una vez corregida la inicialización de la base de datos, podría invocarse dentro del contenedor con:

```bash
docker compose exec app python -c \
  "from core.seed import init_permissions; init_permissions()"
```

El seed crea el rol, pero no crea un usuario administrador ni asigna automáticamente dicho rol a un usuario.

## Consideraciones de seguridad

El proyecto ya contempla varios controles importantes:

- Las contraseñas no se almacenan en texto plano.
- Los tokens contienen fecha de expiración y tipo.
- Un refresh token no puede utilizarse como access token.
- Los usuarios inactivos no pueden iniciar sesión ni acceder a rutas protegidas.
- El acceso a la lista de usuarios requiere un permiso explícito.

Antes de producción aún sería recomendable incorporar:

- Rotación o revocación de refresh tokens.
- Rate limiting para login y refresh.
- Política más fuerte de contraseñas.
- Gestión segura de secretos.
- Registro de intentos de autenticación.
- Protección contra enumeración de usuarios.
- HTTPS obligatorio.
- CORS explícito.
- Migraciones de base de datos con Alembic.
- Pruebas automatizadas.
- Índices y restricciones adicionales en las tablas asociativas.

## Problemas detectados con chatGPT

Hay dos bloqueos importantes en el estado actual:

1. **Se utilizan dos objetos `Base` distintos.**

   `core/database.py` declara un `Base`, mientras que `models/db_models.py` declara otro. `main.py` ejecuta `create_all()` sobre el primero, que no contiene los modelos, por lo que las tablas probablemente no se crearán. Los modelos deben importar el `Base` de `core.database`.

2. **Existe un `import jwt` no utilizado e incompatible con las dependencias declaradas.**

   `api/deps.py` contiene `import jwt`, pero `requirements.txt` instala `python-jose`, cuyo uso correcto ya ocurre mediante `from jose import jwt` en `core/security.py`. En una imagen limpia, ese import puede impedir que la aplicación arranque.

También se observó lo siguiente:

- Redis está configurado, pero todavía no se utiliza.
- No existen endpoints para administrar roles, permisos o asignaciones.
- No hay migraciones ni suite de pruebas.
- `docker-compose.yml` utiliza la propiedad obsoleta `version`.
- `depends_on` no espera a que PostgreSQL esté listo para aceptar conexiones.
- La creación de tablas ocurre al importar `main.py`, en lugar de usar migraciones o un ciclo de arranque controlado.
- La solicitud de refresh usa un `dict` genérico en vez de un esquema Pydantic.
- Hay imports sin utilizar en algunos módulos.
- El directorio no está inicializado actualmente como repositorio Git.

## Estado de validación

- La sintaxis de todos los archivos Python es válida.
- La configuración de Docker Compose se puede resolver correctamente.
- Docker Compose reporta únicamente la advertencia sobre la propiedad obsoleta `version`.
- No fue posible considerar el servicio ejecutable de extremo a extremo sin corregir los dos bloqueos de inicialización señalados.
