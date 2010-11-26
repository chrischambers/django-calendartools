from os import path
PROJECT_ROOT = path.abspath(path.dirname(__file__))

DEBUG = TEMPLATE_DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME':   'basic.db',
    }
}

TIME_ZONE = 'Europe/London'
LANGUAGE_CODE = 'en_GB'

SITE_ID = 1
SECRET_KEY = '5^m%rm8(t4&cew1v-hkaq1)$4r603yu6d-#sv0k=!1)_@n473i'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
USE_L10N = True
USE_I18N = True
# FIRST_DAY_OF_WEEK = 1 # Monday
FORMAT_MODULE_PATH = 'calendartools.formats'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'threaded_multihost.middleware.ThreadLocalMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'basic.urls'

STATIC_DOC_ROOT = path.join(PROJECT_ROOT, 'static')
MEDIA_ROOT = STATIC_DOC_ROOT
MEDIA_URL = '/media/'
TEMPLATE_DIRS = (
    path.join(PROJECT_ROOT, 'templates'),
)
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'calendartools.context_processors.current_datetime',
    'calendartools.context_processors.current_site',
)

ADMIN_MEDIA_PREFIX = '/media/admin/'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',

    'django_extensions',
    'event',
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


# Calendar Stuff:
# ---------------
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S'
)
log = logging.getLogger('calendartools.forms')
log.setLevel(logging.DEBUG)
