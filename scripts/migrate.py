#
# Script de migration de Neuma
#

#import psycopg2
# load the psycopg extras module
#import psycopg2.extras

import json
import sys, getopt, os
sys.path.append("..")


# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scorelib.settings")
import django
django.setup()

# To communicate with Neuma
from neuma.rest import Client
from manager.models import Corpus, Opus
from migration.models import CorpusMigration, OpusMigration


def main (argv):
    corpus_id = ''
    mode= 'opus'
    tag = ''
    try:
        opts, args = getopt.getopt(argv,"hc:t:m:",["corpus=","mode=", "tag="])
    except getopt.GetoptError:
        print('migration.py -c <corpus id> -t <tag> -m [opus|descriptor]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('migrate.py -c <corpus_id> -t <tag> -m [opus|descriptor]')
            sys.exit()
        elif opt in ("-c", "--corpus"):
            corpus_id = arg
        elif opt in ("-t", "--tag"):
            tag = arg
        elif opt in ("-m", "--mode"):
            mode = arg

    if tag == "":
        print("You must provide a migration tag with -t" )
        sys.exit(2)

    # Get the corpus migration
    try:
        migration = CorpusMigration.objects.get(corpus__ref=corpus_id)
    except:
        print('Migration for  ' + corpus_id + " does  not exist" )
        sys.exit(2)
    
    print ("Import opera for corpus " + migration.corpus.title + " for tag \"" + tag + "\" in mode " + mode)
    migration.tag = tag
    migration.save()
    migration.migrate_opera(tag, mode)
    
if __name__ == '__main__':
    main(sys.argv[1:])
