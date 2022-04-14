# import the logging library
import logging

import music21 as m21

import verovio

# Voice is a complex class defined in a separate file
from .Voice import Voice
from . import notation

# Get an instance of a logger
logger = logging.getLogger(__name__)


"""
  This module acts as a thin layer over music21, so as to propose
  a somewhat more constrained representation of encoded scores
""" 

class Score:
	"""
		Representation of a score as a hierarchy of sub-scores / voices
	"""
	
	def __init__(self, title="", composer="") :
		self.id = ""
		'''
		   'A score is made of components, which can be either voices 
		   (final) or parts. Follows the music21 recomended organization
		'''
		self.parts = []
		
		# For compatibility ...
		self.components = list()
		
		self.m21_score = m21.stream.Score(id='mainScore')
		self.m21_score.metadata = m21.metadata.Metadata()
		
		self.m21_score.metadata.title = title
		self.m21_score.metadata.composer = composer
		
		return
	
	def add_part (self, part):
		""" Add a part to the main score """
		self.parts.append(part)	
		self.m21_score.insert(0, part.m21_part)
	
	def part_exists (self, id_part):
		for part in self.parts:
			if part.id == id_part:
				return True
		return False

	def get_part (self, id_part):
		for part in self.parts:
			if part.id == id_part:
				return part
		
		# Oups, the part has not been found ...
		logger.log ("Unable to find this part : " + id_part )

	def get_staff (self, no_staff):
		''' 
		    Find a staff of the score. Staves are embedded in parts
		'''
		for part in self.parts:
			if part.staff_exists (no_staff):
				return part.get_staff(no_staff)

		# The staff has not been found: raise an exception
		print ("Unknown staff : " + str(no_staff))
		return None

	def write_as_musicxml(self, filename):
			''' Produce the MusicXML encoding thanks to Music21'''
			self.m21_score.write ("musicxml", filename)
		
	def write_as_mei(self, filename):
			''' Produce the MEI encoding thanks to Verovio'''
			tk = verovio.toolkit()
			print ("Version : " + tk.getVersion())
			tmp_file = filename + "score.xml"
			self.m21_score.write ("musicxml", tmp_file)
			with open("/tmp/score.xml") as f:
				score_xml = f.read()
			tk.loadData(score_xml)
			
			#with open(filename, "w") as mei_file:
			#	mei_file.write(tk.getMEI())

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
				conv = mei.MeiToM21Converter(meiString)
				self.m21_score = conv.run()
			else:
				#If the score is in XML format
				self.m21_score = m21.converter.parseFile(xml_path,format=format)
		
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


class Part:
	"""
		Representation of a part as a hierarchy of parts / voices
	"""
	
	def __init__(self, id_part, name="", abbr_name="") :
		self.id = id_part
		
		self.m21_part = m21.stream.Part(id=id_part)
		# Metadata
		self.m21_part.partName  = name
		self.m21_part.partAbbreviation = abbr_name
		
		# List of staves the part is displayed on
		self.staves = []
		
		# There should be a add_subpart method for recursive structure. Not
		# used for the moment

	def add_staff (self, staff):
		self.staves.append(staff)
	def staff_exists (self, id_staff):
		for staff in self.staves:
			if staff.id == id_staff:
				return True
		return False
	def get_staff (self, id_staff):
		for staff in self.staves:
			if staff.id == id_staff:
				return staff

	def add_clef_to_staff (self, id_staff, no_measure, clef):
		# A new clef at the beginning of measure for this staff
		if self.staff_exists (id_staff):
			staff = self.get_staff (id_staff)
			staff.add_clef (no_measure, clef)
		else:
			# Unknown staff: raise an exception
			print ("Unknown staff : " + id_staff)
		
	def append_measure (self, measure):
		# Check if we need to insert clef or signature at the beginning
		# of the measure
		
		# NB: needs to be improved if a part extends over several staves
		for staff in self.staves:
			if staff.clef_found_at_measure(measure.no):
				measure.add_clef (staff.get_clef(measure.no))
		self.m21_part.append(measure.m21_measure)

	@staticmethod
	def create_part_id (id_part):
		# Create a string that identifies the part
		return "Part" + str(id_part)

class Measure:
	"""
		Representation of a measure
	"""
	
	def __init__(self, no_measure) :
		self.no = no_measure
		self.m21_measure = m21.stream.Measure(number=no_measure)
		
	def add_time_signature(self, time_signature):
		self.m21_measure.insert(0,  time_signature.m21_time_signature)
	def add_clef(self, clef):
		self.m21_measure.insert(0,  clef.m21_clef)
	def add_key_signature(self, key_signature):
		self.m21_measure.insert(0,  key_signature.m21_key_signature)
		
	def add_voice (self, voice):
		self.m21_measure.insert (0, voice.m21_stream)
		