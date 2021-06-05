#
# Access to ElasticSearch
#
ELASTIC_SEARCH = {"host": "localhost", "port": 11420, "index": "scorelib"}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'scorelib',
        'USER': 'user_scorelib',
        'PASSWORD': 'jAcHethu7utE',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

NEUMA_QUALITY_CORPUS_REF = "qualeval"
