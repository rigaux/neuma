#!/bin/bash

#
# Send a query stored in  a file to ElasticSearch
#
# Param 1: opus id
# Param 2: ElasticSearch host (including port) 
#

opusId=$1
host=http://${2:-localhost:9200}/_search

# Create the query from the template
sed "s/{opus_id}/$1/" opus_by_id.json > curl_query.json

echo Send the query in $file to $host
curl $host -d @curl_query.json
