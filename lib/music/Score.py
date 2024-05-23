# import the logging library
import logging

import music21 as m21

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

		# During parsing, we maintain the current interpretation context 
		# Useful when a part begins without explicit information
		self.current_key_signature = notation.KeySignature() 
		self.current_time_signature = notation.TimeSignature() 

		'''
			Reset all counters
		'''
		Measure.sequence_measure = 0
		
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
		self.m21_score.metadata.add('software', 'DMOS/Collabscore OMR')
		self.m21_score.metadata.add('copyright', 'CollabScore project')
		return
	
	def duration(self):
		# Music21 conventions
		return self.m21_score.duration
	
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
		
		# The new part receives it initial key / time signature from the score
		part.set_current_key_signature(self.current_key_signature)
		part.set_current_time_signature(self.current_time_signature)
		
		if not part.part_type == Part.STAFF_PART:
			# Just a staff in a multi-staves part: do not put in the score
			self.parts.append(part)	

		# We delay the insertion of the part until a measures comes up
		self.insert_part_at_pos(part, 0)
			
	def insert_part_at_pos (self, part, pos):
		self.m21_score.insert(pos, part.m21_part)
		
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

	def get_part_from_staff(self, no_staff):
		# Given a staff id, we return the part that contains this staff
		for part in self.parts:
			if part.staff_exists(no_staff):
				return part 

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

	def set_current_key_signature (self, key):
		self.current_key_signature = key
	def set_current_time_signature (self, ts):
		self.current_time_signature = ts
	def get_current_time_signature(self):
		return self.current_time_signature
	def get_current_key_signature(self):
		return self.current_key_signature

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
			tmp_file = "/tmp/tmp.xml"
			#print (f"Write in {tmp_file}")
			self.m21_score.write ("musicxml", tmp_file)
			#print (f"Load  {tmp_file}")
			tk.loadFile(tmp_file)
			#print (f"Convert to MEI and write")
			with open(filename, "w") as mei_file:
				mei_file.write(tk.getMEI())

	def write_as_midi(self, filename):
			''' Produce the MIDI encoding thanks to Verovio'''
			tk = verovio.toolkit()
			tmp_file = "/tmp/tmp.xml"
			#print (f"Write in {tmp_file}")
			self.m21_score.write ("musicxml", tmp_file)
			#print (f"Load  {tmp_file}")
			tk.loadFile(tmp_file)
			tk.renderToMIDIFile(filename)

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

	#def get_intervals(self):
	#	return score.chordify()
	
	def add_annotation(self, annotation):
		self.annotations.append(annotation)
		
	def check_time_signatures(self, fix=True):
		"""
		  Check the consistency of the time signatures for all parts
		"""
		for part in self.parts:
			part.check_time_signatures(fix)

	def check_measure_consistency(self):
		for part in self.parts:
			part.check_measure_consistency()	

class Part:
	"""
		Representation of a part as a hierarchy of parts / voices
	"""
	
	SINGLE_PART="standard"
	GROUP_PART="group"
	STAFF_PART="partstaff"
	
	def __init__(self, id_part, name="", abbreviation="", 
				   part_type=SINGLE_PART, group=[], no_staff=1) :
		self.id = id_part
		self.staff_group = [] # For parts with multiple PartStaff

		# List of staves the part is displayed on
		self.staves = {}
		
		if part_type==Part.GROUP_PART:
			#print (f"Creating a part group for part {id_part}")
			m21_group = []
			for part_staff in group:
				m21_group.append(part_staff.m21_part)
			self.m21_part = m21.layout.StaffGroup(m21_group, 
								 name=name, abbreviation=abbreviation,
								 symbol='brace')
			self.staff_group = group
			
			# This part has several staves. They are numbered from 1 to ...
			for i_staff in range(1, len(m21_group)+1):
				self.staves[i_staff] =  notation.Staff(i_staff)
		elif part_type == Part.STAFF_PART:
			print (f"Creating a part Staff for part {id_part} and no staff {no_staff}")
			self.m21_part = m21.stream.PartStaff(id=id_part)
			self.staves[no_staff] =  notation.Staff(no_staff)
		else:
			self.m21_part = m21.stream.Part(id=id_part)
			self.staves[no_staff] =  notation.Staff(no_staff)
	
		# Metadata
		self.m21_part.id  = "P" + id_part
		self.m21_part.partName  = name
		self.m21_part.partAbbreviation = abbreviation
		self.part_type = part_type

		# During parsing, we maintain the current interpretation context 
		self.current_key_signature = notation.KeySignature() 
		self.current_time_signature = notation.TimeSignature() 
	
		# List of measures of this part
		self.measures = []
		self.current_measure = None

	@staticmethod
	def make_part_id (id_part, no_staff=None):
		'''
		  Following the music21 model, a part is on a staff. So the identification
		  is from the part id and the staff number. In case
		  of multi-staves parts, we create one part per staff, and a part group
		  that contain both  
		'''
		if no_staff is None:
			return f"{id_part}"
		else:
			return f"{id_part}-{no_staff}"
	
	def clear_staves(self):
		'''
		   To call when we reinitialize a system or a page
		'''
	
		self.staves = {}
		if self.part_type == Part.GROUP_PART:
			# Add also the staff to one of the sub parts
			# We search the first sub part without staff
			for staff_part in self.staff_group: 
				staff_part.clear_staves()
	
	def has_staves(self):
		# Check if at least one staff is allocated to the part
		if len(self.staves.keys()) > 0:
			return True
		else:
			return False
		
	def add_staff (self, staff):
		self.staves.append(staff)
		
		#
		# PROBABLY USELESS !
		#
		if self.part_type == Part.GROUP_PART:
			# Add also the staff to one of the sub parts
			# We search the first sub part without staff
			for staff_part in self.staff_group: 
				if not staff_part.has_staves():
					logger.info(f"PartGroup: add the staff to sub-part {staff_part.id}")
					staff_part.add_staff(staff)
					return
				else:
					logger.info(f"PartGroup: sub-part {staff_part.id} has already a staff")
			logger.error (f'Cannot add another staff {staff.id} to PartGroup {self.id}. All sub-parts have a staff!')
			
	def staff_exists (self, no_staff):
		return no_staff in self.staves.keys()
	
	def get_staff (self, no_staff):
		if self.staff_exists(no_staff):
			return self.staves[no_staff]
		else:
			# The staff does not exists: raise an exception
			raise CScoreModelError (f'Unable to find staff {no_staff} in part {self.id}')

	def get_duration(self):
		return self.m21_part.duration.quarterLength
	
	def set_current_key_signature (self, key):
		self.current_key_signature = key
		if self.part_type == Part.GROUP_PART:
			for staff_part in self.staff_group: 
				staff_part.set_current_key_signature(key)
				
	def set_current_time_signature (self, ts):
		self.current_time_signature = ts
		if self.part_type == Part.GROUP_PART:
			for staff_part in self.staff_group: 
				staff_part.set_current_time_signature(ts)
				
	def get_current_time_signature(self):
		return self.current_time_signature
	def get_current_key_signature(self):
		return self.current_key_signature
	
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

	def add_measure (self, measure_no):

		if not self.part_type == Part.GROUP_PART:
			measure = Measure(self, measure_no)
			
			""" In case this is the first measure, we insert
			   the current time signature (necessary when 
			    a part begins after the other, and the TS is implicit)
			    Music21 seems clever enough to remove subsequent and equals signatures
			 """
			if len(self.measures) == 0:
				measure.add_time_signature(self.current_time_signature.copy())
				measure.add_key_signature(self.current_key_signature.copy())
			
			self.measures.append(measure)
			self.current_measure = measure
			self.m21_part.append(measure.m21_measure)
		else:
			# We add a measure to each sub-part
			for staff_part in self.staff_group: 
				staff_part.add_measure(measure_no)

	def get_current_measures(self):
		if not self.part_type == Part.GROUP_PART:
			if self.current_measure is None:
				# The part has not yet begun
				return []
			else:
				return [self.current_measure]
		else:
			current_measures = []
			# We add a measure to eah sub-part
			for staff_part in self.staff_group: 
				current_measures.append(staff_part.current_measure)
			return current_measures
		
	def get_measure_from_staff(self, no_staff):
		# Given a staff id, we return the current measure for this staff
		for measure in self.get_current_measures():
			if measure.part.staff_exists(no_staff):
				return measure 
		
		logger.error (f"Unable to find a current measure for part {self.id} and staff {no_staff}")
		raise CScoreModelError (f"Unable to find a current measure for part {self.id} and staff {no_staff}")
			
	def add_voice(self, voice):
		if not self.part_type == Part.GROUP_PART:
			self.current_measure.add_voice(voice)
		else:
			# A part on several staves. We determine the main staff
			main_staff = voice.determine_main_staff()
			# We add the voice to the part measure with this staff
			measure = self.get_measure_from_staff(main_staff)
			measure.add_voice(voice)
			
		
	def add_system_break(self):
		for measure in  self.get_current_measures():
			measure.add_system_break()

	def add_page_break(self):
		for measure in  self.get_current_measures():
			measure.add_page_break()
			
	def append_measure (self, measure):
		logger.info (f'Adding measure {measure.no} to part {self.id}')
		
		if not self.part_type == Part.GROUP_PART:
			self.m21_part.append(measure.m21_measure)
		else:
			# Insert the measure in each part-staff
			for staff_part in self.staff_group: 
				staff_part.m21_part.append(measure.m21_measure)
				break
	
	def insert_measure (self, position, measure):
		logger.info (f'Inserting measure {measure.no} at position {position} in part {self.id}')
		if not self.part_type == Part.GROUP_PART:
			self.m21_part.insert(position, measure.m21_measure)
		else:
			# Insert the measure in each part-staff
			for staff_part in self.staff_group: 
				staff_part.m21_part.insert(position, measure.m21_measure)
				
	def add_system_break_does_not_work(self):
		system_break = m21.layout.SystemLayout(isNew=True)
		self.m21_part.append (system_break)

	def reset_accidentals(self):
		# Used when a new measure starts: we fortget all accidentals met before
		for staff in self.staves.values():
			staff.reset_accidentals()

	def check_time_signatures(self, fix=True):
		"""
		  Check the consistency of the time signatures for the current measure
		"""
		# Checking consistency of time signatures
		count_ts = {}
		# Count the occurrences of each TS
		for measure in self.get_current_measures():
			if measure.initial_ts is not None:
				hash_measure = measure.initial_ts.code()
				if hash_measure in count_ts.keys():
					count_ts[hash_measure] += 1
				else:
					count_ts[hash_measure] = 1
			else:
				count_ts["none"] = 1
		# There should be only one: take the most frequent
		if len (count_ts.keys()) > 1:
			logger.warning (f"Measure {measure.id} in part {self.id} has distinct time signatures. Attempt to fix... !!")

			max_count = 0
			for hm in count_ts.keys():
				if max_count < count_ts[hm]:
					max_count = count_ts[hm]
					main_ts = hm
			
			for measure in self.get_current_measures():
				if measure.initial_ts.code() == main_ts:
					ts_to_use = measure.initial_ts
			logger.warning  (f"The main TS is {ts_to_use}. We use it for all staves")
				
			if fix:
				# Try to fix the issue
				for measure in self.get_current_measures():
					ts = ts_to_use.copy()
					for staff in measure.part.staves.values():
						staff.set_current_time_signature (ts)
					measure.replace_time_signature (ts)

	def check_measure_consistency(self):
		for measure in	self.get_current_measures():
			measure.check_consistency()	
					

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
		self.voices = []
		self.id = f'm{no_measure}-{Measure.sequence_measure}' 
		self.m21_measure = m21.stream.Measure(id=self.id, number=no_measure)
		self.m21_measure.style.absoluteX = 23
		self.initial_clefs = {}
		
		# We keep the clef for each staff at the beginning of measure. They
		# are used to determine the pitch from the head's height
		if len(part.staves.values()) > 0:
			for staff in part.staves.values():
				self.initial_clefs[staff.id] = staff.current_clef
				#print (f"Initial clef for measure {self.no} and staff {staff.id}: {staff.current_clef}")
		
		else:
			# No staves for this measure????
			self.initial_ts = part.get_current_time_signature()
			logger.warning (f"Measure {self.id} has no staves? Assuming a time signature {self.initial_ts}")

		# Same thing for initial time signatures. Used for checking consistency
		# Note: there is only one time signature, common to all staves 
		self.initial_ts = part.current_time_signature
			
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
			# No need to change the clef if it is already there
			if not self.initial_clefs[staff_id].equals(clef):
				self.initial_clefs[staff_id] = clef
				# We add the clef to music 21 measure. Sth strange: no staff specified...
				logger.info (f"Adding Clef {clef.m21_clef} to staff {staff_id}")
				self.m21_measure.insert(0,  clef.m21_clef)
			#else:
			#	print (f"Clef already set for staff {staff_id}")

	def print_initial_clefs(self):
		for staff_id, clef in self.initial_clefs.items():
			print (f"Measure {self.no}, staff {staff_id}: initial clef {clef}")
			
	def add_time_signature(self, time_signature):
		self.initial_ts = time_signature
		self.m21_measure.insert(0,  time_signature.m21_time_signature)

	def replace_time_signature(self, new_time_signature):
		if 	self.initial_ts is not None:
			self.m21_measure.remove(self.initial_ts.m21_time_signature)
			self.add_time_signature(new_time_signature)
		
	def add_key_signature(self, key_signature):
		self.m21_measure.insert(0,  key_signature.m21_key_signature)
		
	def add_voice (self, voice):
		if voice.get_duration() > self.get_expected_duration():
			logger.warning (f"Duration error. In measure {self.no}, voice {voice.id} duration {voice.get_duration()} exceeds the expected duration {self.get_expected_duration()}.")
			# Remove hidden events
			voice.remove_hidden_events()
			if voice.get_duration() > self.get_expected_duration():
				logger.warning (f"After removal of hiden events, voice {voice.id} duration {voice.get_duration()} still exceeds the {self.get_expected_duration()}. Shrinking the voice")
				# Still not enough
				voice.shrink_to_bar_duration(self.get_expected_duration())
		self.voices.append(voice)
		self.m21_measure.insert (0, voice.m21_stream)
		
	def add_system_break(self):
		system_break = m21.layout.SystemLayout(isNew=True)
		self.m21_measure.insert (system_break)
		
		# A new staff begins: trying to control its layout
		#staff_layout = 	m21.layout.StaffLayout(staffNumber=1, staffLines=4)
		#staff_layout = 	m21.layout.StaffLayout(staffNumber=1)
		#self.m21_measure.insert(staff_layout)
		
		# We show the current clef at the beginning of staves
		#self.insert_initial_signatures()

	def add_page_break(self):
		system_break = m21.layout.PageLayout(isNew=True)
		self.m21_measure.insert (system_break)
		#self.insert_initial_signatures()

	def insert_initial_signatures(self):
		# If the measure is the first of score/part/staff, we report
		# the current clef and other initial symbols
		for staff in self.part.staves.values():
			# First of system? We insert the current clef
			self.m21_measure.insert(0,  staff.current_clef.m21_clef)
		
	def check_consistency(self, fix=True):
		"""
		   Check that the events in the measure cover exactly the
		   expected duration
		 """
		
		# First get the time signature in effect
		logger.info (f"Measure {self.id}. Expected duration: {self.initial_ts.barDuration().quarterLength}")
		for voice in self.voices:
			bar_duration = self.get_expected_duration()
			#self.m21_measure.getElementsByClass(m21.stream.Voice):
			if not (voice.m21_stream.duration == self.initial_ts.barDuration()):					
				# Trying to fix this. Easy when we just have to complete the voice
				if fix:
					if voice.m21_stream.duration.quarterLength < bar_duration:
						logger.warning (f"Incomplete duration in measure {self.id}. Expected duration: {bar_duration}. Voice {voice.id} duration is {voice.get_duration()}")
						voice.expand_to_bar_duration(bar_duration)
					else:
						logger.warning (f"Overduration in measure {self.id}. Expected duration: {bar_duration}. Voice {voice.id} duration is {voice.get_duration()}")
						voice.shrink_to_bar_duration(bar_duration)
					logger.warning (f"After fix, measure duration: {bar_duration}. Voice {voice.id} duration {voice.get_duration()}")

		self.m21_measure = m21.stream.Measure(id=self.id, number=self.no)
		for voice in self.voices:
			#print (f"Re-Adding voice with duration {voice.get_duration()}")
			self.m21_measure.insert (0, voice.m21_stream)
		logger.info  (f"Measure duration AFTER FIX: {self.get_duration()}")

	def get_duration(self):
		# Returns the measure duration based on it metric
		return self.m21_measure.duration.quarterLength
			
	def get_expected_duration(self):
		# Returns the measure duration based on it metric
		return self.initial_ts.barDuration().quarterLength
		
	def length(self):
		# Music21 conventions
		return self.m21_measure.duration


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

