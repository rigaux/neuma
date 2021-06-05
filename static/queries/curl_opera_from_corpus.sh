#!/bin/bash

#
# Send a query stored in  a file to ElasticSearch
#
# Param 1: corpus id
# Param 2: ElasticSearch host (including port) 
#

corpusId=$1
host=http://${2:-localhost:9200}/_search

# Create the query from the template
sed "s/{corpus_id}/$1/" opera_from_corpus_search.json > curl_query.json

echo Send the query in $file to $host
curl $host -d @curl_query.json
