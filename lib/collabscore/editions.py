import sys 
import lib.collabscore.parser as parser_mod
PSEUDO_BEAM_ID = 99999

# for XML editions
from lxml import etree
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
	ASSIGN_PART_TO_STAFF = "assign_staff_to_part"
	MOVE_OBJECT_TO_STAFF = "move_object_to_staff"
	REPLACE_CLEF = "replace_clef"
	REPLACE_TIMESIGN = "replace_timesign"
	REPLACE_KEYSIGN = "replace_keysign"
	REPLACE_MUSIC_ELEMENT="replace_music_element"
	REMOVE_OBJECT = "remove_object"
	APPEND_OBJECTS="append_objects"
	CLEAN_BEAM = "clean_beam"
	
	# All edition codes
	EDITION_CODES = [MERGE_PARTS,DESCRIBE_PART,ASSIGN_PART_TO_STAFF,
					REPLACE_CLEF, REPLACE_TIMESIGN,REPLACE_KEYSIGN,REMOVE_OBJECT,
					MOVE_OBJECT_TO_STAFF,CLEAN_BEAM,APPEND_OBJECTS,REPLACE_MUSIC_ELEMENT]
	
	# List of editions that apply at parser initialization
	PRE_EDITION_CODES = [MERGE_PARTS,DESCRIBE_PART,ASSIGN_PART_TO_STAFF]
	# List of editions that apply at parsing time
	PARSE_TIME_EDITION_CODES = [REPLACE_CLEF,REPLACE_KEYSIGN,REPLACE_TIMESIGN,REPLACE_MUSIC_ELEMENT,REMOVE_OBJECT]
	# List of editions that apply to the XML output
	POST_EDITION_CODES = [MOVE_OBJECT_TO_STAFF,APPEND_OBJECTS]
	
	def __init__(self, name, target, params={}, edition_range=None) :
		if name not in Edition.EDITION_CODES:
			raise parser_mod.CScoreParserError (f"Invalid editing operation name : {name}" )

		self.name  = name 
		self.target = target
		self.params = params
		# Range of the operation: pages / systems / measures
		if edition_range == None:
			# Default range: everything is accepted
			self.range =  Range() 
		else:
			self.range = edition_range
		
	def apply_to(self, omr_score, mxml_file=None):
		parser_mod.logger.info (f"Apply edit operation {self.name}")
		if self.name == Edition.MERGE_PARTS:
			# Merge two of more parts
			self.merge_parts(omr_score)
		elif self.name == Edition.DESCRIBE_PART:
			# Provide attributes for a part
			self.describe_part (omr_score)
		elif self.name == Edition.ASSIGN_PART_TO_STAFF:
			# Assign a part to a staff
			self.assign_staff_to_part (omr_score)
		elif self.name == Edition.MOVE_OBJECT_TO_STAFF:
			# Assign an object to a staff. Done in the MusicXML file
			self.move_object_to_staff (mxml_file)
		elif self.name == Edition.CLEAN_BEAM:
			# Assign an object to a staff. Done in the MusicXML file
			self.clean_beam (mxml_file)
			
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
		part = omr_score.manifest.get_part (self.target)
		if "name" in self.params.keys():
			part.name = self.params["name"]
		if "abbreviation" in self.params.keys():
			part.abbreviation = self.params["abbreviation"]
		if "instrument" in self.params.keys():
			part.instrument = self.params["instrument"]

	def assign_staff_to_part(self, omr_score):
		''' The parameters are: 
		       the staff id (Staff1, Staff2, etc)
		       the part id
			Everywhere in the range: we assign the staff to the part
		'''
		#
		part = omr_score.manifest.get_part (self.target)
		staff_id =  self.params["staff_id"]
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
						if staff.id == staff_id:
							staff_found = True
							staff.clear_and_replace_part(part.id)

					if staff_found == False:
						parser_mod.logger.warning(f"Operation assign_staff: " +
												    f"cannot find staff {staff_id} in system {system.number} page {page.number}")
					else:
						parser_mod.logger.warning(f"Part {part.id} assigned to staff {staff_id} in system {system.number} page {page.number}")

	def move_object_to_staff(self, mxml_doc):
		''' The parameters are: the staff id, and the object id (a note, a rest, a clef...)
			This is a post-xml correction...
		'''

		object_id = self.target
		staff_no = self.params["staff_no"]
		direction = self.params["direction"]
		
		object = mxml_doc.find(f".//*[@id = '{object_id}']")
		if object is not None:
			# Note: staves in MusicXML are numbered internally
			# to a part. So, if we move a note, it is either
			# to staff 2 of direction is down, or staff 1 if direction is up
			
			staff = object.find("staff")
			# An heuristic to infer the numbering of staves in MusicXML
			if direction == "up":
				#staff_no = int(staff.text) - 1
				staff_no = 1
			else:
				# staff_no = int(staff.text) + 1
				staff_no = 2
			parser_mod.logger.info(f"Moving {direction} object {object_id} to staff {staff_no}")
			staff.text = f"{staff_no}"
		else:
			parser_mod.logger.warning(f"Unable to find object {object_id} that should be moved to staff {staff_no}")
		
		return 

	def append_objects(self, mxml_doc, divisions):
		''' 
		    Objects have been removed from a voice
		    after conversion. We reinsert them directly in the file
		'''
		object_id = self.target
		list_events = self.params["events"]		

		target = mxml_doc.find(f".//*[@id = '{object_id}']")
		if target is not None:
			voice_el = target.find("./voice")
			if voice_el is not None:
				voice = voice_el.text
				print (f"APPEND AFTER id {object_id}. Voice={voice} Divisions={divisions}")
				parent = target.getparent()
				#print(f"Object found " + str(etree.tostring(target)))
				for removed in list_events:
					print (f"\t\tAppend object {removed.id} after {target.get('id')}")
					musicxml_elements = removed.to_musicxml(divisions)
					for el in musicxml_elements:
						v = etree.SubElement(el, 'voice')
						v.text = str(voice)
						self.insert_after(parent, target, el)
						target = el
			else:
				parser_mod.logger.warning(f"Unable to find the voice in element {object_id}. Ignored...")			
		else:
			print (f"Event {object_id} not found in the file")

		
	def insert_after(self, parent, element, new_element):
		parent.insert(parent.index(element)+1, new_element)

	@staticmethod
	def apply_editions_to_file(post_editions, xml_file):
		# All post editions apply to the MusicXML file
		mxml_doc = etree.parse(xml_file)
		
		# Find the value of "divisions": used to determine XML duration
		for division_node in mxml_doc.findall(f".//divisions"):
			divisions = int(division_node.text)
			
		for ed in post_editions:
			if ed.name == Edition.MOVE_OBJECT_TO_STAFF:
				# Assign an object to a staff. Done in the MusicXML file
				ed.move_object_to_staff (mxml_doc)
			elif ed.name == Edition.CLEAN_BEAM:
				# Assign an object to a staff. Done in the MusicXML file
				ed.clean_beam (mxml_doc)
			elif ed.name == Edition.APPEND_OBJECTS:
				ed.append_objects (mxml_doc, divisions)
	
		# Write it back
		mxml_doc.write (xml_file)

	@staticmethod
	def add_edition_to_list(editions, edition):
		""" 
		  Add an edition to a list, or replace in case of redundancy
		"""
		
		already_exists =False
		for ed in editions:
			if edition.name == ed.name and edition.target==ed.target:
				already_exists = True
				# Maybe we can UPDATE the current edition. TO DO

		if not(already_exists):
			editions.append(edition)
		else:
			print (f"Edition {edition.name} already exists for target {edition.target}")
		
		return editions

	def clean_beam (self, mxml_doc):
		parser_mod.logger.info(f"Cleaning pseudo-beams")
		
		notes = mxml_doc.findall(f".//note")
		for note in notes:
			beams = note.findall("beam")
			for beam in beams:
				if int(beam.get("number")) == PSEUDO_BEAM_ID:
					#print (f"Removing pseudo Beam {beam}")
					note.remove(beam)
	
	def to_json (self):
		return {"name": self.name,
			    "target": self.target,
			     "params": self.params
			    }
		
	@staticmethod
	def from_json (json_op):
		return Edition(json_op["name"], json_op["target"], json_op["params"])
				 
	
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
