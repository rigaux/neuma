import os
import environ
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# For uploaded files
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'media')
MEDIA_URL = '/media/'
# Allows to include remote JS files
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
# For temp. files
TMP_DIR = os.path.join(os.path.dirname(BASE_DIR), 'media','tmp')
# For script files (bash, XSL, etc.)
SCRIPTS_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'scorelib','scripts')

# Does not work?
os.path.join(BASE_DIR, BASE_DIR + "/lib")

sys.path.append(os.path.join(BASE_DIR, "lib"))


env = environ.Env(
    DEBUG=(bool, True),
    REDIS_HOST=(str, "localhost"),
    REDIS_PORT=(int, 6379),
    INSTANCE_URL=(str, "http://localhost:8000"),
)
environ.Env.read_env()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'nd8p5+*vbbc1-wd1cy5oxj$+@!@5+t6ulhxu(182_4zj@p7i5h'

# 
DEFAULT_FROM_EMAIL="philippe.rigaux@cnam.fr"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['neuma.huma-num.fr', 'localhost', '0.0.0.0']

CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
     'crispy_forms','crispy_bootstrap4',
  'guardian',
    # 'debug_toolbar',
    "home",
    "manager",
    "rest",
    "rest_framework",  
    'rest_framework.authtoken',
    "mptt",
   'drf_spectacular',
   'corsheaders',
    'django_celery_results',
)

SESSION_SERIALIZER='django.contrib.sessions.serializers.JSONSerializer'
SESSION_SAVE_EVERY_REQUEST = True

MIDDLEWARE = (
	'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)


CORS_ALLOW_ALL_ORIGINS = True
SENDFILE_BACKEND='sendfile.backends.simple'

ROOT_URLCONF = 'scorelib.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ["templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'scorelib.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

# DATABASES = {
    # 'default': {
        # 'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    # }
# }
#DATABASES = {
    #'default': {
        #'ENGINE': 'django.db.backends.postgresql_psycopg2',
        #'NAME': 'neuma',
        #'USER': 'neumadmin',
        #'PASSWORD': 'neuma',
        #'HOST': 'localhost',
        #'PORT': '',
    #}
#}


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'neuma',
        'USER': 'neumadmin',
        'PASSWORD': 'neuma',
        'HOST': 'localhost',
        'PORT': '',
     }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LOCALE_PATHS = ('locale',)

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# For django guardian
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # this is default
    'guardian.backends.ObjectPermissionBackend',
)

# Anonymous user (still used?)
ANONYMOUS_USER_ID = -1

# A pseudo user, representing automatic computations for annotations and similar tasks
COMPUTER_USER_NAME = "computer"
#
# Neuma groups
#
EDITOR_GROUP="Editor"  # Can add and edit corpora
VISITOR_GROUP="Visitor" # Can view but not edit
NEUMA_GROUPS = [EDITOR_GROUP,VISITOR_GROUP]
                     
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
#STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Name of the counterpoint tensorflowmodel
COUNTERPOINT_MODEL ="model.h5"

# Directory for JSON encoded ES queries
ES_QUERY_DIR = os.path.join(BASE_DIR, "static/queries")

# Tells whether we use our own ranked search
ES_RANKED_SEARCH = False

#
# Site configuration paramaters
#

# Max nb of items in a collection (can't use sys.maxsize: too large)
#
MAX_ITEMS_IN_CORPUS = 1000000
#
MAX_ITEMS_IN_RESULT = 1000
# Nb of items in a page
ITEMS_PER_PAGE = 20

NEUMA_URL = 'http://neuma.huma-num.fr/rest'
#NEUMA_URL = 'http://neuma-dev.huma-num.fr/rest'
NEUMA_ID_SEPARATOR = ":"
# Convention for the root, external, and transcription corpus
NEUMA_ROOT_CORPUS_REF = "all"
NEUMA_EXTERNAL_CORPUS_REF = "external"
NEUMA_QUALITY_CORPUS_REF = "qualeval"
NEUMA_COLLABSCORE_CORPUS_REF = "all:collabscore"

# Used everywhere, to know which kind of object we are dealing with
CORPUS_TYPE = "corpus"
OPUS_TYPE = "opus"
# Size of ngrams for search
NGRAM_SIZE = 3
# Convention to represent all parts
ALL_PARTS = "all_parts"

# Descriptor types
MELODY_DESCR = "melody"
LYRICS_DESCR = "lyrics"
RHYTHM_DESCR = "rhythm"
NOTES_DESCR = "notes"
DIATONIC_DESCR = "diatonic"

# Neighbors
NB_NEIGHBORS = 10

#
# REST documentation
#
REST_FRAMEWORK = {    
	'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema', 
	'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    # Use Django's standard `django.contrib.auth` permissions,
	# or allow read-only access for unauthenticated users.
	'DEFAULT_PERMISSION_CLASSES': [
		'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
	]
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Neuma REST API',
    'DESCRIPTION': 'API of the Neuma digital library',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # OTHER SETTINGS
}

#
# ElasticSearch
#
ELASTIC_SEARCH = {"host": "cchumweb05.in2p3.fr", "port": 11420, "index": "scorelib"}


# Redis
REDIS_HOST = env("REDIS_HOST")
REDIS_PORT = int(env("REDIS_PORT"))

# Celery
CELERY_BROKER_URL = "redis://%s:%d/0" % (REDIS_HOST, REDIS_PORT)
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP= True


# List of similarity measures
SIMILARITY_MEASURES = ["pitches","intervals","degrees","rhythms"]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


try:
    from scorelib.local_settings import *
    print("local settings .... ok")
except ImportError as error:
    print(error)
