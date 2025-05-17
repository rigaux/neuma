#
# Tests locaux
#

##
#
# Transfert d'un fichier vers la source
#'

curl  -u collabscore:collabscore -X POST http://neuma.huma-num.fr/rest/collections/all:collabscore:saintsaens-ref:C006_0/_sources/iiif/_file/ -F 'dmos.json=@coinsbleus.json'
curl -u collabscore:collabscore -X POST "http://localhost:8000/rest/collections/all:collabscore:saintsaens-ref:C006_0/_sources/iiif/_file/"  -F 'dmos.json=@coinsbleus.json'


####################################
#
# Test sur les annotations
#
####################################

curl -u collabscore:collabscore -X PUT  http://localhost:8000/rest/collections/all:collabscore:saintsaens-ref:C006_0/_annotations/ \
     -H "Content-Type: application/json" \
     -d @annotation.json 

curl -u collabscore:collabscore -X PUT  https://neuma.huma-num.fr/rest/collections/all:collabscore:saintsaens-ref:C006_0/_annotations/ \
     -H "Content-Type: application/json" \
     -d @annotation_list.json 
          
####################################
#
# Test sur les éditions
#
####################################

# Objets musicaux
curl -u collabscore:collabscore -X POST http://localhost:8000/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC006_0/_sources/iiif/_apply_editions/ \
-d @replace_music_el.json  -H "Content-Type: application/json" > t.xml
curl -u collabscore:collabscore -X POST http://neuma.huma-num.fr/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC006_0/_sources/iiif/_apply_editions/ \
-d @replace_music_el.json  -H "Content-Type: application/json" > t.xml

# Deux opérations
curl -u collabscore:collabscore -X POST http://localhost:8000/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC006_0/_sources/iiif/_apply_editions/ \
-d @remove_and_edit.json  -H "Content-Type: application/json" > t.xml

# Suppression d'une tête de note
curl -u collabscore:collabscore -X POST http://localhost:8000/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC006_0/_sources/iiif/_apply_editions/ \
-d @remove_note_head.json  -H "Content-Type: application/json" > t.xml
# Suppression d'une clé dans Fière beauté
curl -u collabscore:collabscore -X POST http://localhost:8000/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC009_0/_sources/iiif/_apply_editions/ \
-d @remove_clef.json  -H "Content-Type: application/json" > t.xml
# Suppression d'une armure dans l'amant malheureux
curl -u collabscore:collabscore -X POST http://localhost:8000/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC046_0/_sources/iiif/_apply_editions/ \
-d @remove_ks.json  -H "Content-Type: application/json" > t.xml


curl -u collabscore:collabscore -X POST http://localhost:8000/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC006_0/_sources/iiif/_apply_editions/ \
-d @switch_note_rest.json  -H "Content-Type: application/json" > t.xml


# Clef
curl -u collabscore:collabscore -X POST http://localhost:8000/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC006_0/_sources/iiif/_apply_editions/ \
-d @eds_replace_clef.json  -H "Content-Type: application/json" > t.xml

# Armure
curl -u collabscore:collabscore -X POST http://localhost:8000/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC006_0/_sources/iiif/_apply_editions/ \
-d @replace_keysign.json  -H "Content-Type: application/json" > t.xml

# Métrique
curl -u collabscore:collabscore -X POST http://localhost:8000/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC006_0/_sources/iiif/_apply_editions/ \
-d @replace_timesign.json  -H "Content-Type: application/json" > t.xml


#
# Tests Neuma
#


# Objets musicaux
curl -u sameh:collabscore -X POST http://neuma.huma-num.fr/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC006_0/_sources/iiif/_apply_editions/ \
-d @replace_music_el.json  -H "Content-Type: application/json" > t.xml


curl -u sameh:collabscore -X POST http://neuma.huma-num.fr/rest/collections/all:collabscore:saintsaens-ref:C006_0/_sources/iiif/_apply_editions/ \
-d @replace_clef.json  -H "Content-Type: application/json"


# Clef
curl -u collabscore:collabscore -X POST http://neuma.huma-num.fr/rest/collections/all:collabscore:saintsaens-ref:C006_0/_sources/iiif/_apply_editions/ \
-d @replace_clef.json  -H "Content-Type: application/json" > t.xml
