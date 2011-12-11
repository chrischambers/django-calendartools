# Minimal settings used for testing.
from os import path
CURRENT_DIR = path.abspath(path.dirname(__file__))
APPLICATION_DIR = path.abspath(path.dirname(path.dirname(__file__)))

APPEND_SLASH = True
DEBUG = TEMPLATE_DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'tests.db',
    },
}
MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'threaded_multihost.middleware.ThreadLocalMiddleware',
]
STATIC_DOC_ROOT = path.join(path.split(APPLICATION_DIR)[0], 'static')
MEDIA_ROOT = STATIC_DOC_ROOT
MEDIA_URL = '/media/'

USE_I18N = True
USE_L10N = True
LANGUAGE_CODE = 'en-gb'
FORMAT_MODULE_PATH = 'calendartools.formats'
SITE_ID = 1

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django_extensions',
    'calendartools',
    'event',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_DIRS = [path.join(APPLICATION_DIR, 'templates'),
                 path.join(CURRENT_DIR, 'templates')]
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'calendartools.context_processors.current_datetime',
    'calendartools.context_processors.current_site',
)

ROOT_URLCONF = 'calendartools.urls'
