"""Configuración central de Django para `roabackend`.

Este archivo concentra decisiones de infraestructura y compatibilidad del
proyecto: carga de entorno, autenticación de la API, catálogo de apps,
conexión a base de datos y rutas base para contenido estático/media.

"""

from datetime import timedelta
from pathlib import Path
import environ
import os

env = environ.Env()

# `BASE_DIR` se mantiene con `os.path` por compatibilidad con el código legado
# del proyecto, aunque exista `Path` importado en este archivo.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Carga variables de entorno desde el `.env` del proyecto. Esta configuración
# es la fuente principal de secretos y parámetros por ambiente.
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Seguridad base del proyecto.
SECRET_KEY = env('SECRET_KEY')

# Django SecurityMiddleware estaba heredando la politica por defecto
# `same-origin`, lo que bloquea el envio de `Referer` hacia embeds externos
# como YouTube cuando los OAs se sirven desde `/media/`. Se usa una politica
# mas compatible para permitir contexto cross-origin limitado sin exponer la
# URL completa.
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# `DEBUG` puede llegar desde `.env` o desde variables del proceso con formatos
# distintos (`1`, `true`, `release`, etc.). Se normaliza de forma tolerante para
# que valores de entorno no rompan el arranque de Django.
DEBUG_RAW = str(env('DEBUG', default='0')).strip().lower()
DEBUG = DEBUG_RAW in ('1', 'true', 'yes', 'on', 'debug', 'dev', 'development')

if not DEBUG:
    # Se conserva la lista histórica de hosts permitidos por compatibilidad con
    # los despliegues actuales del ROA/EduTech.
    ALLOWED_HOSTS=['repositorio.edutech-project.org']
else:
    # En desarrollo local se permite cualquier host para no bloquear pruebas
    # manuales desde distintos puertos o IPs internas.
    ALLOWED_HOSTS=['*']

# Apps nativas de Django requeridas por el proyecto.
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
]

# Apps propias del dominio de negocio.
LOCAL_APPS = [
    'applications.user',
    'applications.learning_object_file',
    'applications.knowledge_area',
    'applications.education_level',
    'applications.preferences',
    'applications.profession',
    'applications.evaluation_student',
    'applications.evaluation_collaborating_expert',
    'applications.learning_object_metadata',
    'applications.license',
    'applications.recommendation_system',
    'applications.interaction',
    'applications.address',
    'applications.settings',
]

# Dependencias externas que amplían la API REST, CORS y almacenamiento.
THIRD_PARTY_APPS = [
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'django.contrib.postgres',
    'storages',
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS

# La API soporta autenticación JWT y, además, un mecanismo de token expirado
# heredado que varios endpoints todavía consumen.
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        [
            "rest_framework.renderers.BrowsableAPIRenderer",
            "rest_framework.renderers.JSONRenderer",
        ]
        if DEBUG
        else [
            "rest_framework.renderers.JSONRenderer",
        ]
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'applications.user.authentication.ExpiringTokenAuthentication',
        'applications.user.authentication.CookieJWTAuthentication',
    ),
    # El proyecto asume autenticación por defecto y los endpoints públicos
    # abren permisos de forma explícita.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    # 'PAGE_SIZE': 150
}

# Configuracion base de SimpleJWT para preparar la migracion hacia cookies
# HttpOnly manteniendo compatibilidad temporal con `Authorization: Bearer`.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=env.int('JWT_ACCESS_TOKEN_MINUTES', default=5)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=env.int('JWT_REFRESH_TOKEN_DAYS', default=7)
    ),
    'ROTATE_REFRESH_TOKENS': env.bool('JWT_ROTATE_REFRESH_TOKENS', default=True),
    'BLACKLIST_AFTER_ROTATION': env.bool('JWT_BLACKLIST_AFTER_ROTATION', default=True),
    'UPDATE_LAST_LOGIN': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Parametros de cookies JWT. En esta fase todavia no se emiten desde login,
# pero se definen ya para que backend y frontend compartan un contrato estable.
JWT_AUTH_COOKIE_ACCESS = env('JWT_AUTH_COOKIE_ACCESS', default='roa_access')
JWT_AUTH_COOKIE_REFRESH = env('JWT_AUTH_COOKIE_REFRESH', default='roa_refresh')
JWT_AUTH_COOKIE_SECURE = env.bool('JWT_AUTH_COOKIE_SECURE', default=not DEBUG)
JWT_AUTH_COOKIE_HTTP_ONLY = env.bool('JWT_AUTH_COOKIE_HTTP_ONLY', default=True)
JWT_AUTH_COOKIE_SAMESITE = env('JWT_AUTH_COOKIE_SAMESITE', default='Lax')
JWT_AUTH_COOKIE_ACCESS_PATH = env('JWT_AUTH_COOKIE_ACCESS_PATH', default='/')
JWT_AUTH_COOKIE_REFRESH_PATH = env(
    'JWT_AUTH_COOKIE_REFRESH_PATH',
    default='/api/v1/token/refresh/',
)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=JWT_AUTH_COOKIE_SECURE)
CSRF_COOKIE_SAMESITE = env('CSRF_COOKIE_SAMESITE', default=JWT_AUTH_COOKIE_SAMESITE)
# El frontend lee csrftoken para enviar el header X-CSRFToken; no debe ser HttpOnly.
CSRF_COOKIE_HTTPONLY = False

# Configuracion de la documentacion OpenAPI usada por Swagger UI y Redoc.
SPECTACULAR_SETTINGS = {
    'TITLE': 'ROA API-REST Documentation',
    'DESCRIPTION': 'Documentacion tecnica de los endpoints del backend ROA.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
}

# Tiempo maximo del token de autenticacion heredado en segundos.
TOKEN_EXPIRED_AFTER_SECONDS = 1800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

if not DEBUG:
    DOMAIN = env('DOMAIN_HOST')
else:
    # Se mantiene la misma variable en ambos ambientes para no duplicar la
    # fuente de verdad de URLs absolutas usadas en correos y serialización.
    DOMAIN = env('DOMAIN_HOST')

# Puntajes base configurables para las respuestas de la evaluación experta.
YES = env('YES')
NO = env('NO')
PARTIALLY = env('PARTIALLY')
NOT_APPLY = env('NOT_APPLY')

# Mapeo de etiquetas visibles para las opciones de calificación del experto.
CALIFICATION_OPTIONS = {
    'YES': 'Si',
    'NO': 'No',
    'PARTIALLY': 'Parcialmente',
    'NOT_APPLY': 'No aplica',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # CORS debe ejecutarse temprano para adjuntar cabeceras consistentes tanto
    # en respuestas exitosas como en rechazos previos del stack.
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware', 
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'roabackend.urls'

# La configuración de templates se usa principalmente para correos y recursos
# renderizados por Django, no como motor principal de frontend.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'staticfiles': 'django.templatetags.static',
            },
        },
    },
]

WSGI_APPLICATION = 'roabackend.wsgi.application'

# La conexión principal usa Postgres y toma todos los parámetros desde `.env`
# para evitar credenciales hardcodeadas por ambiente.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env('NAME'),
        'USER': env('USERROA'),
        'PASSWORD': env('PASSWORD'),
        'HOST': env('HOST'),
        'PORT': env('PORT'),
    }
}

# Validadores estándar de Django para políticas mínimas de password.
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# El proyecto usa un modelo de usuario custom con roles y perfiles asociados.
AUTH_USER_MODEL = 'user.User'

# En desarrollo local se flexibiliza CORS para permitir pruebas desde el
# frontend sin configuración extra por origen.
CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS', default=False)
CORS_ALLOW_CREDENTIALS = env.bool('CORS_ALLOW_CREDENTIALS', default=True)
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

if DEBUG:
    # Se habilita `ALLOWALL` en desarrollo para simplificar pruebas embebidas
    # o renderizadas en iframes durante soporte y validación manual.
    X_FRAME_OPTIONS = 'ALLOWALL'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Keep legacy integer PKs and remove Django W042 warnings.
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Recursos estáticos y media servidos por Django/WSGI en los entornos
# actuales del proyecto.
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')


#STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
