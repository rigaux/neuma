#
# Access to ElasticSearch
#
ELASTIC_SEARCH = {"host": "localhost", "port": 9200, "index": "scorelib"}

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

NEUMA_URL = 'http://localhost:8000/rest'

ALLOWED_HOSTS = ['neuma.huma-num.fr', 'localhost', '0.0.0.0', "127.0.0.1"]
NEUMA_QUALITY_CORPUS_REF = "neumasuite:qualeval"


GRAMMAR_INPUT_PATH = '/mnt/c/Users/fosca/Desktop/CNAM/scorelib/app/scorelib/transcription/grammars/grammar.txt'
SCHEMAS_PATH = '/mnt/c/Users/fosca/Desktop/CNAM/qparselib/build/schemas'
QPARSELIB_CONFIG_PATH= '/mnt/c/Users/fosca/Desktop/CNAM/qparselib/params.ini'
NEUMA_QUALITY_CORPUS_REF = "qualeval"
NEUMA_COMPARISON_TEST = "all:comparison"


NEUMA_COMPARISON_TEST = "all:comparison"
