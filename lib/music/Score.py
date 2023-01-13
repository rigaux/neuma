# import the logging library
import logging

import music21 as m21

from lib.search.MusicSummary import MusicSummary
import verovio

# Voice is a complex class defined in a separate file
from .Voice import Voice
from . import notation

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# For the console
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.DEBUG)
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

	# For OMR app: we can introduce an intermediate System level
	use_systems = False
	
	def __init__(self, title="", composer="") :
		self.id = ""
		'''
		   'A score is made of components, which can be either voices 
		   (final) or parts. Follows the music21 recommended organization
		'''
		self.parts = []
		
		''' 
            Optionnaly, a score is split in systems: mostly useful
            for OMR applications. In that case the current system
            behaves as a sub-scre, and all call on parts are delegated to it
		'''
		self.systems = []
		self.current_system = None

		'''
			We can store annotations on a score and any of its elemnts
		'''
		self.annotations = []
		
		# For compatibility ...
		self.components = list()
		
		self.m21_score = m21.stream.Score(id='mainScore')
		self.m21_score.metadata = m21.metadata.Metadata()
		
		self.m21_score.metadata.title = title
		self.m21_score.metadata.composer = composer
		
		return
	
	def get_parts(self):
		'''
			Get the list of parts, found either in the score itself or in the current system
		'''
		if Score.use_systems:
			return self.current_system.parts
		else:
			return self.parts

	def add_system (self, system):
		if Score.use_systems:
			self.systems.append (system)
			self.current_system = system
			self.m21_score.append(system.m21_system)
			
	def add_system_break(self):
		system_break = m21.layout.SystemLayout(isNew=True)
		self.m21_score.append (system_break)
			
			
	def add_part (self, part):
		""" Add a part to the main score or to the current system"""
		if Score.use_systems:
			self.current_system.parts.append(part)	
			self.current_system.m21_system.insert(0, part.m21_part)
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

	def get_staff (self, no_staff):
		''' 
		    Find a staff of the score. Staves are embedded in parts
		'''
		for part in self.get_parts():
			if part.staff_exists (no_staff):
				return part.get_staff(no_staff)

		# The staff has not been found: raise an exception
		raise CScoreModelError (f'Unable to find staff {no_staff} in part {part.id}')

	def write_as_musicxml(self, filename):
			''' Produce the MusicXML encoding thanks to Music21'''
			self.m21_score.write ("musicxml", filename)
		
	def write_as_mei(self, filename):
			''' Produce the MEI encoding thanks to Verovio'''
			tk = verovio.toolkit()
			tmp_file = filename + "score.xml"
			self.m21_score.write ("musicxml", tmp_file)
			tk.loadFile(tmp_file)
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
<<<<<<< HEAD
				conv = mei.MeiToM21Converter(meiString)
				self.m21_score = conv.run()
			else:
				#If the score is in XML format
				self.m21_score = m21.converter.parseFile(xml_path,format=format)
		
=======
				conv = m21.mei.MeiToM21Converter(meiString)
				self.m21_score = conv.run()
			else:
				#If the score is in XML format
				self.m21_score = m21.converter.parse(xml_path)
			
			# ignore the following bc it cause errors
>>>>>>> 06c55414e382d98720010d7d39fa88ec015ab7e3
			self.load_component(self.m21_score)

		except Exception as ex:
			self.m21_score = None
			print ("Error while loading from xml:" + str(ex))
			print ("Some error raised while attempting to transform MEI to XML.")


	def load_component(self, m21stream):
		'''Load the components from a M21 stream'''

		default_voice_id = 1
		default_part_id = 1
		
		# Extract the voices
		if m21stream.hasVoices():
			for m21voice in m21stream.voices:
				voice = Voice(self.id + "-" + str(default_voice_id))
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
<<<<<<< HEAD
				
=======

>>>>>>> 06c55414e382d98720010d7d39fa88ec015ab7e3
		# Last case: no voice, no part: the stream itself is a voice
		if not m21stream.hasVoices() and not m21stream.hasPartLikeStreams():
			voice = Voice(self.id + "-" + str(default_voice_id))

			m21voice = m21.stream.Voice(m21stream.flat.notesAndRests.elements)
			# print ("Create voice in component "	self.id	" with id "	voice.id)
			voice.set_from_m21(m21voice)
			voice.convert_to_sequence()

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
		'''Produce a compact representation of a score for search operations'''
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

class System:
	"""
        For OMR only: all the sub-components (parts, etc) are allocated to a single system 
    """

	def __init__(self, no_system) :
		logger.info (f"Adding system {no_system}")
		self.id = no_system

		self.m21_system = m21.stream.System(id=no_system)

		# List of parts in the system
		self.parts = []
		

class Part:
	"""
		Representation of a part as a hierarchy of parts / voices
	"""
	
	def __init__(self, id_part, name="", abbr_name="") :
		self.id = id_part
		
		self.m21_part = m21.stream.Part(id=id_part)
		# Metadata
		self.m21_part.id  = "P" + id_part
		self.m21_part.partName  = name
		self.m21_part.partAbbreviation = abbr_name

		# List of staves the part is displayed on
		self.staves = []
		
		# There should be a add_subpart method for recursive structure. Not
		# used for the moment

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

	def add_clef_to_staff (self, no_staff, no_measure, clef):
		# A new clef at the beginning of measure for this staff
		if self.staff_exists (no_staff):
			staff = self.get_staff (no_staff)
			staff.add_clef (no_measure, clef)
		else:
			# Unknown staff: raise an exception
			print ("Unknown staff : " + no_staff)

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

	@staticmethod
	def create_part_id (id_part):
		# Create a string that identifies the part
		return "Part" + str(id_part)


class Measure:
	"""
		Representation of a measure
	"""
	
	# Sequence for generating measure ids
	sequence_measure = 0
	def __init__(self, no_measure) :
		Measure.sequence_measure += 1
		self.no = no_measure
		self.id = Measure.sequence_measure
		self.m21_measure = m21.stream.Measure(id=f'm{self.id}', number=no_measure)
		self.m21_measure.style.absoluteX = 23
	def add_time_signature(self, time_signature):
		self.m21_measure.insert(0,  time_signature.m21_time_signature)
	def add_clef(self, clef):
		self.m21_measure.insert(0,  clef.m21_clef)
	def add_key_signature(self, key_signature):
		self.m21_measure.insert(0,  key_signature.m21_key_signature)
		
	def add_voice (self, voice):
		self.m21_measure.insert (0, voice.m21_stream)
		

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

