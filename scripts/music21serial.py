# Script de sérialisation de Music21

import json
import sys, getopt, os
import music21 as m21
sys.path.append("..")


# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scorelib.settings")
import django
from django.conf import settings
django.setup()

# To communicate with Neuma
from neuma.rest import Client
from manager.models import Corpus, Opus

def main (argv):
    corpus_id = ''
    mode= 'opus'
    tag = ''
    try:
        opts, args = getopt.getopt(argv,"hc:o:",["corpus=","opus="])
    except getopt.GetoptError:
        print('music21serial.py -c <corpus id> -o [opus]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('music21serial.py -c <corpus id> -o [opus]')
            sys.exit()
        elif opt in ("-c", "--corpus"):
            corpus_id = arg
        elif opt in ("-o", "--opus"):
            opus_id = arg

    try:
        opus_ref = corpus_id + settings.NEUMA_ID_SEPARATOR + opus_id
        try:
            opus = Opus.objects.get(ref__exact=opus_ref)
        except Opus.DoesNotExist as e:
            print("does not exist")
            opus = Opus()

        # m21score = opus.get_score().m21_score
        # path = "/home/raph/temp/score"
        # m21.converter.freeze(m21score, fp=path)
        path = opus.freeze(filepath="/home/raph/temp/score")
        print("Opus "+opus_ref+" was serialized at "+path)
    except:
        print("you've lost, try again")
        sys.exit(2)

    newscore = opus.unfreeze(path)
    print("Opus "+opus_ref+" was deserialized into "+str(type(newscore)))
    
if __name__ == '__main__':
    main(sys.argv[1:])
