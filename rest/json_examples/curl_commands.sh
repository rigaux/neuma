curl -u rigaux:Fuf3a3wu! -X POST http://localhost:8000/rest/collections/all:collabscore:saintsaens-ref:C006_0/_sources/iiif/_apply_editions/ \
-d @eds_replace_clef.json  -H "Content-Type: application/json"

curl -u sameh:collabscore -X POST http://neuma.huma-num.fr/rest/collections/all:collabscore:saintsaens-ref:C006_0/_sources/iiif/_apply_editions/ \
-d @replace_clef.json  -H "Content-Type: application/json"

curl -u rigaux:fuf3a3wu -X POST http://neuma.huma-num.fr/rest/collections/all:collabscore:saintsaens-ref:C006_0/_sources/iiif/_apply_editions/ \
-d @replace_clef.json  -H "Content-Type: application/json" > t.xml

Le type frozen est-il obligatoire ?
