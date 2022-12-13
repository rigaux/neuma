

'''
 A class used to produce JSON-LD encoding of score libray data
'''


class JsonLD:
    '''
        A general utility class to manage JSON LD specifics
    '''
    
    def __init__(self, base) :
        ''' 
           A dictionary, indexed on measures, that records the clefs
            used in the staff
            What if a change occurs in the middle of a measure ? Not
            supported for the time being. We will need a more powerful
            notion of 'position'
        '''
        self.types = {}
        self.base= base

    def add_type (self, name, uri):
        self.types[name] = uri 
        
    
    def get_context(self):
        
        context = {"@base": self.base} | self.types
        
        return  {"@context": context}