.. _chap-search:
   

###########################
Searching Neuma collections
###########################


The chapter describes the search operations in Neuma.


*************
ElasticSearch
*************

*********
Searching
*********

Exact search
============

A descriptor is produced that combines melodic and rythmic information. It is stored in ElasticSearch.


Melodic search
==============

A descriptor is produced with melodic information. Ranking is done a rythmic similarity
of the best occurrence.

Rythmic search
==============

A descriptor is produced with rythmic information. Ranking is done a rythmic similarity.



*******
Ranking
*******

.. code-block:: json

    {
    "query": {
        "function_score": {
         "query": {
            "match": {
            "body": "foo"
            }
        },
        "functions": [
            {
            "script_score": {
                "script": {
                "source": "scorelib",
                "lang" : "ScoreSim",
                "params": {
                    "query": [{"index":5, "duration":3}, {"index":6, "duration":2}],
                    "type": 1
                }
                }
              }
            }
          ]
        }
      }   
    }

