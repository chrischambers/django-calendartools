# Minimal settings used for testing.
import os
APPLICATION_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

DEBUG = TEMPLATE_DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'tests.db',
    },
}
MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'threaded_multihost.middleware.ThreadLocalMiddleware',
]

USE_I18N = False
USE_L10N = False
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

TEMPLATE_DIRS = os.path.join(APPLICATION_DIR, 'templates')

ROOT_URLCONF = 'calendartools.urls'
