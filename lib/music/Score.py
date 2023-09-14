# import the logging library
import logging

import music21 as m21
from numpy.distutils.fcompiler import none
from numpy import True_, False_

#from neumasearch.MusicSummary import MusicSummary
# No longer useful?

'''
the layout stream hierarchy is in perpetual beta, so some things 
won’t work (for instance, reconstruction of standard stream from 
layout stream doesn’t yet exist), but do look at the music21.layout 
module for the docs and proper routines, especially  
layout.divideByPages(normalStream).

'''

import verovio

# Voice is a complex class defined in a separate file
from .Voice import Voice
from . import notation

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


# For the console
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.WARNING)
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
#logger.addHandler(c_handler)

"""
  This module acts as a thin layer over music21, so as to propose
  a somewhat more constrained representation of encoded scores
""" 

class Score:

	"""
        Representation of a score as a hierarchy of sub-scores / voices
    """

	
	def __init__(self, title="", composer="", use_layout=False) :
		self.id = ""
		
		# We can explicitly decompose a Score in pages and systems (OMR)
		self.use_layout = use_layout
		
		'''
		   'A score is made of components, which can be either voices 
		   (final) or parts. Follows the music21 recommended organization
		'''
		self.parts = []
		
		''' 
            Optionally, a score is split in pages and systems: mostly useful
            for OMR applications. In that case the current system
            behaves as a sub-score, and all call on parts are delegated to it
            
            From music21: the proper hierarchy for a stream describing layout is:

				LayoutScore->Page->System->Staff->Measure

			where LayoutScore and Page are subclasses of stream.Opus, 
			System is a subclass of Score, and Staff subclasses Part, so 
			the normal music21 hierarchy of Opus*->Score->Part->Measure is 
			preserved. (Where Opus* indicates  optional and able to 
			embed other Opuses, like Opus->Opus->Opus->Score…)
		'''
		self.pages = []
		self.current_page = None

		'''
			We can store annotations on a score and any of its elemnts
		'''
		self.annotations = []
		
		# For compatibility ...
		self.components = list()
		
		if self.use_layout:
			self.m21_score = m21.layout.LayoutScore(id='mainScore')
		else:
			self.m21_score = m21.stream.Score(id='mainScore')
			
		self.m21_score.metadata = m21.metadata.Metadata()
		
		self.m21_score.metadata.title = title
		self.m21_score.metadata.composer = composer
		
		return
	
	def get_parts(self):
		'''
			Get the list of parts, found either in the score itself or in the current page
		'''
		if self.use_layout:
			return self.current_page.get_parts()
		else:
			return self.parts

	def add_part (self, part):
		""" Add a part to the main score or to the current page"""
		if self.use_layout:
			self.current_page.add_part(part)	
		else:
			self.parts.append(part)	
			self.m21_score.insert(0, part.m21_part)
	
	def part_exists (self, id_part):
		for part in self.get_parts():
				if part.id == id_part:
					return True
		return False

	def get_part (self, id_part):
		for part in self.get_parts():
			if part.id == id_part:
				return part
		
		# Oups, the part has not been found ...
		raise CScoreModelError ("Unable to find this part : " + id_part )

	def add_page (self, page):
		self.pages.append (page)
		self.current_page = page
		self.m21_score.append(page.m21_page)

	def get_staff (self, no_staff):
		''' 
		    Find a staff of the score. Staves are embedded in parts
		'''
		for part in self.get_parts():
			if part.staff_exists (no_staff):
				return part.get_staff(no_staff)

		# The staff has not been found: raise an exception
		raise CScoreModelError (f'Unable to find staff {no_staff} in part {part.id}')

	def reset_accidentals(self):
		# Used when a new measure starts: we forget all accidentals met before
		for part in self.get_parts():
			part.reset_accidentals()

	def write_as_musicxml(self, filename):
			''' Produce the MusicXML encoding thanks to Music21'''
			self.m21_score.write ("musicxml", filename)
		
	def write_as_mei(self, filename):
			''' Produce the MEI encoding thanks to Verovio'''
			tk = verovio.toolkit()
			tmp_file = filename + "score.xml"
			tmp_file = "/tmp/tmp.xml"
			#print (f"Write in {tmp_file}")
			self.m21_score.write ("musicxml", tmp_file)
			#print (f"Load  {tmp_file}")
			tk.loadFile(tmp_file)
			#print (f"Convert to MEI and write")
			with open(filename, "w") as mei_file:
				mei_file.write(tk.getMEI())

	def load_from_xml(self, xml_path, format):
		"""
			Get the score representation from a MEI or MusicXML document
		"""

		try:		
			#If the score is in MEI format, convert it to Music21 stream
			if format == "mei":
				with open (xml_path, "r") as meifile:
					meiString = meifile.read()
				#print ("MEI file: "	meiString[0:40])
				conv = m21.mei.MeiToM21Converter(meiString)
				self.m21_score = conv.run()
			else:
				#If the score is in XML format
				self.m21_score = m21.converter.parse(xml_path)
			
			# ignore the following bc it cause errors

			self.load_component(self.m21_score)

		except Exception as ex:
			self.m21_score = None
			print ("Score::load_from_xml error: " + str(ex))


	def load_component(self, m21stream):
		'''Load the components from a M21 stream'''

		default_voice_id = 1
		default_part_id = 1
		
		# Extract the voices
		if m21stream.hasVoices():
			for m21voice in m21stream.voices:
				# NB: self is assumed to be a part
				voice = Voice(self, self.id + "-" + str(default_voice_id))
				voice.set_from_m21(m21voice)
				#print ("Create voice in component "	self.id	" with id "	voice.id)
				default_voice_id += 1
				self.components.append(voice)

		# Extract the parts as sub-scores
		if m21stream.hasPartLikeStreams():
			partStream = m21stream.parts.stream()
			for p in partStream:
				score = Score()
				score.id = "P" + str(default_part_id)
				#print ("Create component score with id "	score.id)
				default_part_id += 1
				self.components.append(score)
				# Recursive call
				score.load_component(p)

		# Last case: no voice, no part: the stream itself is a voice
		if not m21stream.hasVoices() and not m21stream.hasPartLikeStreams():
			voice = Voice(self, self.id + "-" + str(default_voice_id))

			m21voice = m21.stream.Voice(m21stream.flat.notesAndRests.stream().elements)
			# print ("Create voice in component "	self.id	" with id "	voice.id)
			voice.set_from_m21(m21voice)
			self.components.append(voice)
		
	def get_sub_scores(self):
		'''Return the score components'''
		scores = list()
		for comp in self.components:
			if isinstance(comp, Score):
				scores.append(comp)
		return scores

	def get_voices(self):
		'''Return the local voices components'''
		voices = list()
		for comp in self.components:
			if isinstance(comp, Voice):
				voices.append(comp)
		return voices
	
	def get_all_voices(self):
		'''Recursive search of all the voices in the score'''
		voices = list()
		for comp in self.components:
			if isinstance(comp, Voice):
				# Add the local voices
				voices.append(comp)
			elif isinstance(comp, Score):
				# Add the voices of the sub-components
				voices += comp.get_all_voices()
		return voices
	
	def get_music_summary(self):
		'''Produce a compact representation of a score for search operations
		
		   No longeer used? Seee MusicSummary line 57
		
		music_summary = MusicSummary()
		# Adds a single part, for historical reasons: we do not care about parts
		# for search operations
		part_id = "all_parts"
		music_summary.add_part(part_id)
		# Now add all the voices
		voices = self.get_all_voices()
		for voice in voices:
			music_summary.add_voice_to_part(part_id, voice.id, voice)
			
		return music_summary
		'''
		return
	
	def get_title(self):
		if self.m21_score.metadata:
			return self.m21_score.metadata.title
		else:
			return ""
	def get_composer(self):
		if self.m21_score.metadata:
			return self.m21_score.metadata.composer
		else:
			return ""
	def get_metadata(self):
		return self.m21_score.metadata

	def get_intervals(self):
		return score.chordify()
	
	def add_annotation(self, annotation):
		self.annotations.append(annotation)


class Page:
	"""
        For OMR only: a cpntainer for systems  
         Does not work with music21....
    """

	def __init__(self, no_page) :
		logger.info (f"Adding page {no_page}")
		self.id = no_page

		self.m21_page = m21.layout.Page(id=no_page)

		# List of systems in the page
		self.systems = []
		self.current_system = None 
		
	def add_system (self, system):
		self.systems.append (system)
		self.current_system = system
		self.m21_page.append(system.m21_system)
			

	def add_part (self, part):
		""" Add a part to the current system"""
		self.current_system.add_part(part)	

	def get_parts(self):
		'''
			Get the list of parts in the current system
		'''
		return self.current_system.get_parts()

class System:
	"""
        For OMR only: all the sub-components (parts, etc) are allocated to a single system 
        Does not work with music21....
    """

	def __init__(self, no_system) :
		logger.info (f"Adding system {no_system}")
		self.id = no_system

		self.m21_system = m21.layout.System(id=no_system)

		# List of parts in the system
		self.parts = []
		
	def add_part (self, part):
		self.parts.append(part)	
		self.m21_system.insert(0, part.m21_part)		

	def get_parts(self):
		return self.parts

class Part:
	"""
		Representation of a part as a hierarchy of parts / voices
	"""
	
	def __init__(self, id_part, name="", abbreviation="") :
		self.id = id_part
		
		self.m21_part = m21.stream.Part(id=id_part)
		# Metadata
		self.m21_part.id  = "P" + id_part
		self.m21_part.partName  = name
		self.m21_part.partAbbreviation = abbreviation

		# List of staves the part is displayed on
		self.staves = []
		
		# There should be a add_subpart method for recursive structure. Not
		# used for the moment

	def clear_staves(self):
		# To call when we reinitialize a system or a page
		self.staves = []
		
	def has_staves(self):
		# Check if at least one staff is allocated to the part
		if len(self.staves) > 0:
			return True
		else:
			return False
		
	def add_staff (self, staff):
		self.staves.append(staff)
		
	def staff_exists (self, no_staff):
		for staff in self.staves:
			if staff.id == no_staff:
				return True
		return False
	
	def get_staff (self, no_staff):
		for staff in self.staves:
			if staff.id == no_staff:
				return staff
			
		# The staff has not been found: raise an exception
		raise CScoreModelError (f'Unable to find staff {no_staff} in part {self.id}')

	def add_clef_to_staff (self, no_staff, clef):
		# A new clef at the beginning of measure for this staff
		if self.staff_exists (no_staff):
			staff = self.get_staff (no_staff)
			staff.set_current_clef (clef)
		else:
			# Unknown staff: raise an exception
			raise CScoreModelError (f'Unable to find staff {no_staff} in part {self.id}')

	def add_accidental (self, no_staff, pitch_class, acc):
		staff = self.get_staff(no_staff)
		staff.add_accidental( pitch_class, acc)

	def append_measure (self, measure):
		# Check if we need to insert clef or signature at the beginning
		# of the measure
		
		logger.info (f'Adding measure {measure.no} to part {self.id}')
		self.m21_part.append(measure.m21_measure)

	def add_system_break(self):
		system_break = m21.layout.SystemLayout(isNew=True)
		self.m21_part.append (system_break)

	def reset_accidentals(self):
		# Used when a new measure starts: we fortget all accidentals met before
		for staff in self.staves:
			staff.reset_accidentals()
			
	@staticmethod
	def create_part_id (id_part):
		# Create a string that identifies the part
		return "Part" + str(id_part)


class Measure:
	"""
		Representation of a measure, which belongs to a part
	"""
	
	# Sequence for generating measure ids
	sequence_measure = 0
	
	def __init__(self, part, no_measure) :
		Measure.sequence_measure += 1
		self.part = part
		self.no = no_measure
		self.id = f'm{Measure.sequence_measure}' 
		self.m21_measure = m21.stream.Measure(id=self.id, number=no_measure)
		self.m21_measure.style.absoluteX = 23
		
		# We keep the clef for each staff at the beginning of measure. They
		# are used to determine the pitch from the head's height
		self.initial_clefs = {}
		for staff in part.staves:
			self.initial_clefs[staff.id] = staff.current_clef
			#print (f"Initial clef for measure {self.no} and staff {staff.id}: {staff.current_clef}")
		
	def get_initial_clef_for_staff(self, staff_id):
		if not (staff_id in self.initial_clefs.keys()):
			# Oups, no such staff 
			raise CScoreModelError (f"No staff ‘{staff_id}' for measure {self.no}")
		else:
			return self.initial_clefs[staff_id]
	def set_initial_clef_for_staff(self, staff_id, clef):
		if not (staff_id in self.initial_clefs.keys()):
			# Oups, no such staff 
			raise CScoreModelError (f"No staff ‘{staff_id}' for measure {self.no}")
		else:
			self.initial_clefs[staff_id] = clef
			
		# We add the clef to music 21 measure. Sth strange: no staff specified...
		self.m21_measure.insert(0,  clef.m21_clef)

	def print_initial_clefs(self):
		for staff_id, clef in self.initial_clefs.items():
			print (f"Measure {self.no}, staff {staff_id}: initial clef {clef}")
			
	def add_time_signature(self, time_signature):
		self.m21_measure.insert(0,  time_signature.m21_time_signature)
	def add_key_signature(self, key_signature):
		self.m21_measure.insert(0,  key_signature.m21_key_signature)
		
	def add_voice (self, voice):
		self.m21_measure.insert (0, voice.m21_stream)
	def add_system_break(self):
		system_break = m21.layout.SystemLayout(isNew=True)
		self.m21_measure.insert (system_break)
	def add_page_break(self):
		system_break = m21.layout.PageLayout(isNew=True)
		self.m21_measure.insert (system_break)
		

class CScoreModelError(Exception):
	def __init__(self, *args):
		if args:
			self.message = args[0]
		else:
			self.message = None

	def __str__(self):
		if self.message:
			return 'ScoreModelError, {0} '.format(self.message)
		else:
			return 'ScoreModelError has been raised'

