import json

import lib.collabscore.parser as parser_mod

'''
  Edit operations applied to a score. Designed to be combined
  with an optical recognition step
'''

class Edition:
	"""
	  Edit operations
	"""
	
	MERGE_PARTS = "merge_parts"
	DESCRIBE_PART = "describe_part"
	
	EDITION_CODES = [MERGE_PARTS,DESCRIBE_PART]
	
	def __init__(self, name, params={}) :
		if name not in Edition.EDITION_CODES:
			raise parser_mod.CScoreParserError (f"Invalid editing operation  : {name}" )

		self.name  = name 
		self.params = params
		# Target of the operation: a range of pages / systems / measures
		self.target = None 
		
	def apply_to(self, omr_score):
		print (f"Apply edit operation {self.name}")
		if self.name == Edition.MERGE_PARTS:
			# Merge two of more parts
			self.merge_parts(omr_score)
		elif self.name == Edition.DESCRIBE_PART:
			# Provide attributes for a part
			self.describe_part (omr_score)
			
	def merge_parts(self, omr_score):
		# Get the first part: we merge everything there
		target = omr_score.manifest.get_part (self.params["parts"][0])
		for part_id in self.params["parts"]:
			if part_id != target.id:
				source = omr_score.manifest.get_part (part_id)
				for page in omr_score.manifest.pages:
					for system in page.systems:
						for staff in system.staves:
							staff.replace_part (source, target)
						system.create_groups()
					page.create_groups()
				# Remove the part
				del omr_score.manifest.parts[source.id]
			# Re-compute groups
			omr_score.manifest.create_groups()

	def describe_part(self, omr_score):
		# Get the first part: we merge everything there
		part = omr_score.manifest.get_part (self.params["part"])
		if "name" in self.params["values"].keys():
			part.name = self.params["values"]["name"]
		if "abbreviation" in self.params["values"].keys():
			part.abbreviation = self.params["values"]["abbreviation"]
		if "instrument" in self.params["values"].keys():
			part.instrument = self.params["values"]["instrument"]

	def to_json (self):
		return {"name": self.name,
			     "params": self.params
			    }
		
	@staticmethod
	def from_json (json_op):
		return Edition(json_op["name"], json_op["params"])
	