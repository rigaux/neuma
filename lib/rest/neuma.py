
#import json
import requests

from django.conf import settings

import  sys

# import the logging library
import logging

# services codes
CORPORA_SERV = "_corpora"
OPERA_SERV = "_opera"
FILES_SERV ="_files"
LILYPOND_SERV ="_lilypond"
DESCRIPTORS_SERV ="_descriptors"
COUNT_OPERA_SERV = "_count_opera"
REF_SEPARATOR = ":" 
REQUEST_OK = 200

# Get an instance of a logger
logger = logging.getLogger(__name__)

class Client:
    """A class to communicate with Neuma REST API"""

    
    def __init__(self) :
        self.neumaUrl = settings.NEUMA_URL
        
    def checkService (self):
        r = requests.get(settings.NEUMA_URL)
        logger.error ("Calling checkService")
        logger.error(mess)
        
        return ''
    
    def get_top_level_corpora (self):
        r = requests.get(settings.NEUMA_URL + "/" + CORPORA_SERV)
        response = r.json()
        return response["corpora"];
    
    def get_corpus_by_id (self, corpus_id):
        r = requests.get(settings.NEUMA_URL + "/" + corpus_id)
        # Load from JSON
        return r.json()
    
    def get_count_opera_from_corpus (self, corpus_id):
        r = requests.get(settings.NEUMA_URL + "/" + corpus_id + "/" + COUNT_OPERA_SERV)
        # Load from JSON
        return r.json()

    def get_opera_from_corpus (self, corpus_id, start_pos=0, size=settings.MAX_ITEMS_IN_CORPUS):
        params = {'from': start_pos, 'size': size}
        r = requests.get(settings.NEUMA_URL + "/" + 
                         corpus_id.replace(REF_SEPARATOR,"/") + "/" + OPERA_SERV,
                         params)
        # Load from JSON
        return r.json()
    
    def get_opus_by_id (self, opus_id):
        """Loads an Opus from the Neuma REST API."""
        r = requests.get(settings.NEUMA_URL + "/" + opus_id)
        return r.json()

    def get_opus_url (self, opus_id):
        return settings.NEUMA_URL + "/" + opus_id.replace(REF_SEPARATOR,"/") + "/"

    def get_files_from_opus (self, opus_id):
        """Get the list of existing files for an Opus"""
        r = requests.get(settings.NEUMA_URL + "/" + 
                         opus_id.replace(REF_SEPARATOR,"/") +"/"+FILES_SERV)
        try:
            opus_with_files = r.json()
            if ('files' in opus_with_files):
                return opus_with_files["files"]
            else:
                print ("Cannot get files for Opus "  + opus_id)
                return {}        
        except:
            print ("Unable to decode the following JSON file for " + opus_id)
            print (str(r))
            return {}


    def get_descriptors_from_opus (self, opus_id):
        """Get the list of descriptors for an Opus"""
        r = requests.get(settings.NEUMA_URL + "/" + 
                         opus_id.replace(REF_SEPARATOR,"/") +"/"+DESCRIPTORS_SERV)
        opus_with_descriptors = r.json()
        if ('descriptors' in opus_with_descriptors):
            return opus_with_descriptors["descriptors"]
        else:
            print ("Cannot get descriptors for Opus "  + opus_id)
            return []
        
    def get_children_from_corpus (self, corpus_id):
        
        r = requests.get(settings.NEUMA_URL + "/" + 
                         corpus_id.replace(REF_SEPARATOR,"/") + "/" + CORPORA_SERV)
        # Load from JSON
        return r.json()
    
       
    def lilypond (self, corpus_id, musicxml_content, preview=False):
        url = settings.NEUMA_URL + "/" +   corpus_id.replace(REF_SEPARATOR,"/") + "/" + LILYPOND_SERV
        params = {}
        if preview == True:
            params = {"preview": preview}
            
        print ("Call URL " + url + " with params " + str(params))
        r = requests.put(url, params=params, data=musicxml_content.encode('utf-8'))
        if r.status_code == REQUEST_OK:
            # Enforce the encoding before decoding r.content into r.text
            # Can we/should we do better?
            r.encoding = 'utf-8'
            return r.text
        else:
            response = r.json()
            raise LookupError(response["message"])
