import os
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

DEBUG = TEMPLATE_DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'dev.db',
    }
}

TIME_ZONE = 'Europe/London'
LANGUAGE_CODE = 'en-GB'

SITE_ID = 1
SECRET_KEY = '5^m%rm8(t4&cew1v-hkaq1)$4r603yu6d-#sv0k=!1)_@n473i'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'threaded_multihost.middleware.ThreadLocalMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'basic.urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
)

ADMIN_MEDIA_PREFIX = '/media/admin/'
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')
MEDIA_URL = '/media/'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',

    'calendartools',
)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Django Debug Toolbar:
# ---------------------
# Consider ourselves an internal IP
from socket import gethostname, gethostbyname
INTERNAL_IPS = ( '127.0.0.1',
                 gethostbyname(gethostname()),)

MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)
INSTALLED_APPS += (
    'debug_toolbar',
)

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}
