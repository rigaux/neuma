

'''
 A class used to produce JSON-LD encoding of score library data
'''


class JsonLD:
	'''
		A general utility class to manage JSON LD specifics
	'''
	
	def __init__(self, ontos) :
		''' 
		   ontos is an array of prefix-iri pairs, from which types are taken
		'''
		self.ontologies = ontos

		self.types = {}

	def add_type (self, prefix, nom_type):
		'''
		  Add a type and specifies the prefix of its ontology
		'''
		self.types[nom_type] = prefix
		
	
	def get_context(self):
		
		# First create a dict with the ontologies
		context = self.ontologies
		# Add the types
		for nom_type, prefix  in self.types.items():
			context[nom_type] = prefix + ":" + nom_type
		return  {"@context": context}