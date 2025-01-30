#
# Tests locaux
#

# Objets musicaux
curl -u collabscore:collabscore -X POST http://localhost:8000/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC006_0/_sources/iiif/_apply_editions/ \
-d @replace_music_el.json  -H "Content-Type: application/json" > t.xml


curl -u collabscore:collabscore -X POST http://localhost:8000/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC006_0/_sources/iiif/_apply_editions/ \
-d @switch_note_rest.json  -H "Content-Type: application/json" > t.xml


# Clef
curl -u collabscore:collabscore -X POST http://localhost:8000/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC006_0/_sources/iiif/_editions/ \
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

curl -u sameh:collabscore -X POST http://neuma.huma-num.fr/rest/collections/all:collabscore:saintsaens-ref:C006_0/_sources/iiif/_apply_editions/ \
-d @replace_clef.json  -H "Content-Type: application/json"


# Objets musicaux
curl -u collabscore:collabscore -X POST http://localhost:8000/rest/collections/all%3Acollabscore%3Asaintsaens-ref%3AC006_0/_sources/iiif/_apply_editions/ \
-d @replace_music_el.json  -H "Content-Type: application/json" > t.xml

# Clef
curl -u collabscore:collabscore -X POST http://neuma.huma-num.fr/rest/collections/all:collabscore:saintsaens-ref:C006_0/_sources/iiif/_apply_editions/ \
-d @replace_clef.json  -H "Content-Type: application/json" > t.xml
