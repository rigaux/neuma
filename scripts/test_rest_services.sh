#!/bin/bash
JSON_EX=../rest/json_examples/
NEUMA_URL=https://neuma.huma-num.fr
LOCAL_URL=http://localhost:8000

# Change for Neuma testing
SERVER_URL=$LOCAL_URL

LES_COINS_BLEUS=all:collabscore:saintsaens-ref:C006_0

###
###  Services sur les sources
###

# Liste des sources
curl -X GET $SERVER_URL/rest/collections/$LES_COINS_BLEUS/_sources/

# Liste des éditions
echo Appel à $SERVER_URL/rest/collections/$LES_COINS_BLEUS/_sources/iiif/_editions/
curl -X GET $SERVER_URL/rest/collections/$LES_COINS_BLEUS/_sources/iiif/_editions/

# Envoi d'un fichier d'édition à une source
curl -u rigaux:pwd -X POST $SERVER_URL/rest/collections/$LES_COINS_BLEUS/_sources/iiif/_editions/ \
      -d @editions_desc.json  -H "Content-Type: application/json"

# Application d'une liste d'éditions à une source IIIF
echo Appel à $SERVER_URL/rest/collections/$LES_COINS_BLEUS/_sources/iiif/_apply_editions/
curl -X GET $SERVER_URL/rest/collections/$LES_COINS_BLEUS/_sources/iiif/_apply_editions/ \
 -d @editions_desc.json  -H "Content-Type: application/json"

curl -X GET $LOCAL_URL/rest/collections/$LES_COINS_BLEUS/_sources/
