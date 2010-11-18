# Minimal settings used for testing.
import os
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
APPLICATION_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

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

USE_I18N = True
USE_L10N = True
FIRST_DAY_OF_WEEK = 1 # Monday
LANGUAGE_CODE = 'en_GB'
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
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_DIRS = [os.path.join(APPLICATION_DIR, 'templates'),
                 os.path.join(CURRENT_DIR, 'templates')]
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'calendartools.context_processors.current_datetime',
    'calendartools.context_processors.current_site',
)

ROOT_URLCONF = 'calendartools.urls'
