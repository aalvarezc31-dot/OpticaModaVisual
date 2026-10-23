"""
Servidor web (nivel 1 de la arquitectura N-tier): capa de presentación.

NO tiene base de datos ni driver de SQL Server. Todo lo que muestra o guarda
lo pide al servidor de aplicación por HTTP (presentacion/cliente_api.py).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'OPTICA_WEB_SECRET_KEY',
    'django-insecure-web-7q$x!h3k2v9m1p8r6t4w0z5y&c^n-presentacion',
)

DEBUG = os.environ.get('OPTICA_DEBUG', '1') == '1'

ALLOWED_HOSTS = os.environ.get('OPTICA_WEB_HOSTS', 'localhost,127.0.0.1').split(',')

# Dirección del servidor de aplicación (nivel 2).
URL_API = os.environ.get('OPTICA_API_URL', 'http://127.0.0.1:8010')
API_TIMEOUT = 15  # segundos

INSTALLED_APPS = [
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'presentacion',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'presentacion.middleware.SesionAPIMiddleware',
    'presentacion.middleware.ErroresAPIMiddleware',
    'presentacion.middleware.PermisosPorRolMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'presentacion.context_processors.seccion_actual',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Sin base de datos: este nivel nunca toca SQL Server.
DATABASES = {}

# La sesión (token de la API, rol y secciones) vive en una cookie firmada.
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 12 * 60 * 60
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

LANGUAGE_CODE = 'es'
FORMAT_MODULE_PATH = ['config.formatos']
TIME_ZONE = 'America/Guatemala'
USE_I18N = True
USE_TZ = False

STATIC_URL = 'static/'

LOGIN_URL = '/login/'
