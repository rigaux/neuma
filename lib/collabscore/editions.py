import sys 
import lib.collabscore.parser as parser_mod

'''
  Edit operations applied to a score. Designed to be combined
  with an optical recognition step
'''
from numpy import False_, True_

class Edition:
	"""
	  Edit operations
	"""
	
	MERGE_PARTS = "merge_parts"
	DESCRIBE_PART = "describe_part"
	MOVE_PART_TO_STAFF = "move_part_to_staff"
	
	EDITION_CODES = [MERGE_PARTS,DESCRIBE_PART,MOVE_PART_TO_STAFF]
	
	def __init__(self, name, params={}, target=None) :
		if name not in Edition.EDITION_CODES:
			raise parser_mod.CScoreParserError (f"Invalid editing operation  : {name}" )

		self.name  = name 
		self.params = params
		# Target of the operation: a range of pages / systems / measures
		if target == None:
			# Default range: everything is accepted
			self.target =  Range() 
		else:
			self.target = target
		
	def apply_to(self, omr_score):
		parser_mod.logger.info (f"Apply edit operation {self.name}")
		if self.name == Edition.MERGE_PARTS:
			# Merge two of more parts
			self.merge_parts(omr_score)
		elif self.name == Edition.DESCRIBE_PART:
			# Provide attributes for a part
			self.describe_part (omr_score)
		elif self.name == Edition.MOVE_PART_TO_STAFF:
			# Assign a part to a staff
			self.move_part_to_staff (omr_score)
			
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

	def move_part_to_staff(self, omr_score):
		''' The parameters are: the staff id, and the part id
		Everywhere in the range: we assign the part to the staff
		'''
		#
		part = omr_score.manifest.get_part (self.params["part"])
		id_staff =  self.params["staff"]
		# Loop on the staves in the target
		for page in omr_score.manifest.pages:
			for system in page.systems:
				if self.target.in_system_range(page.number,system.number):
					# Ok the system in the range
					
					# First pass: remove the part from its current staff
					for staff in system.staves:
						if staff.contains_part (part.id):
							staff.parts = []

					# Second pass: find the new staff, clear and replace 
					staff_found = False
					for staff in system.staves:
						if staff.id == id_staff:
							staff_found = True
							staff.clear_and_replace_part(part.id)

					if staff_found == False:
						parser_mod.logger.warning(f"Operation assign_staff: " +
												    f"cannot find staff {id_staff} in system {system.number} page {page.number}")
					else:
						parser_mod.logger.warning(f"Part {part.id} assigned to staff {id_staff} in system {system.number} page {page.number}")
						print(f"Part {part.id} assigned to staff {id_staff} in system {system.number} page {page.number}")

	def to_json (self):
		return {"name": self.name,
			     "params": self.params
			    }
		
	@staticmethod
	def from_json (json_op):
		return Edition(json_op["name"], json_op["params"])


class Range():
	'''
	   Defines the range of measures an edition applies to.
	   NB: we use the score layout as a way to refer to a position:
	   a measure nb is in the context of a system nb, itself
	   in the context of a page number. Ex: '3-2-2' refers to
	   measure 2 of system 2 of page 3
	'''
		

	def __init__(self, from_page=0, from_system=0, from_measure=0,
				   to_page=sys.maxsize, to_system=sys.maxsize,to_measure=sys.maxsize) :
		# Range values are INCLUDED
		self.from_page  = from_page 
		self.from_system = from_system
		self.from_measure = from_measure
		self.to_page  = to_page 
		self.to_system = to_system
		self.to_measure = to_measure
	
		
	def in_page_range (self, no_page):
		# Check if a page number is in the range
		if no_page >= self.from_page and no_page <= self.from_page:
			return  True
		else:
			return False

	def in_system_range (self, no_page, no_system):
		# Check if a page number is in the range
		if no_page < self.from_page or (
			no_page == self.from_page and no_system < self.from_system):
			before_range = True
		else:
			before_range = False
		# Same thing from the upper one
		if no_page > self.to_page or (
			no_page == self.to_page and no_system > self.to_system):
			after_range = True
		else:
			after_range = False
			
		return not(after_range or before_range)

	def in_range (self, no_page, no_system, no_measure):
		
		# Check if the measure is before the lower bound
		if no_page < self.from_page or (
			no_page == self.from_page and no_system < self.from_system
			) or (no_measure < self.from_measure):
			before_range = True
		else:
			before_range = False
				
		# Same thing from the upper one
		if no_page > self.to_page or (
			no_page == self.to_page and no_system > self.to_system
			) or (no_measure > self.from_measure):
			after_range = True
		else:
			after_range = False
				
				
		return not(after_range or before_range)
