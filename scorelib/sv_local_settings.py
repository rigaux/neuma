#
# Access to ElasticSearch
#
ELASTIC_SEARCH = {"host": "localhost", "port": 9200, "index": "scorelib"}

#
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


NEUMA_QUALITY_CORPUS_REF = "neumasuite:qualeval"

#Paths about the schemas script of qparselib
GRAMMAR_INPUT_PATH = '/mnt/c/Users/fosca/Desktop/CNAM/scorelib/app/scorelib/transcription/grammars/grammar.txt'
SCHEMAS_PATH = '/mnt/c/Users/fosca/Desktop/CNAM/qparselib/build/schemas'
QPARSELIB_CONFIG_PATH= '/mnt/c/Users/fosca/Desktop/CNAM/qparselib/params.ini'