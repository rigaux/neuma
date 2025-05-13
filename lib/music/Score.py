# import the logging library
import logging

import music21 as m21

import verovio


# Voice is a complex class defined in a separate file
from .Voice import Voice
from . import notation
from . import events
from .constants import ID_SEPARATOR

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

		# We need to know the initial signatures in case they are missing
		self.initial_key_signature = notation.KeySignature() 
		self.initial_time_signature = notation.TimeSignature() 

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
			
		instr =  m21.instrument.Alto()
		instr.partId = "cocu"
		self.m21_score.insert(0, instr)

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
		part.set_current_time_signature(self.current_time_signature)
		part.current_time_signature.set_by_default(f"default_ts")

		part.set_current_key_signature(self.current_key_signature)
		part.current_key_signature.set_by_default(f"default_ks")
		
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

	def add_page (self, page):
		self.pages.append (page)
		self.current_page = page
		self.m21_score.append(page.m21_page)
		
	def set_initial_key_signature (self, key):
		key.set_by_default("default_score_key")
		self.current_key_signature = key
	def set_initial_time_signature (self, ts):
		ts.set_by_default("default_score_time")
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
	
	def write_as_mei(self, mxml_file, mei_name):
			''' Produce the MEI encoding from MusicXML thanks to Verovio'''
			tk = verovio.toolkit()
			print (f"Load MusicXML {mxml_file}")
			tk.loadFile(mxml_file)
			print (f"Convert {mxml_file} to MEI and write in {mei_name}")
			with open(mei_name, "w") as mei_file:
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
				default_voice_id += 1
				self.components.append(voice)

		# Extract the parts as sub-scores
		if m21stream.hasPartLikeStreams():
			partStream = m21stream.parts.stream()
			for p in partStream:
				score = Score()
				score.id = "P" + str(default_part_id)
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
		if annotation is not None:
			self.annotations.append(annotation)
		
	def check_time_signatures(self, fix=True):
		"""
		  Check the consistency of the time signatures for all parts
		"""
		for part in self.parts:
			part.check_time_signatures(fix)

	def check_measure_consistency(self):
		list_removals = []
		for part in self.parts:
			list_removals += part.check_measure_consistency()	
		return list_removals

	def aggregate_voices_from_measures(self):
		for part in self.parts:
			part.aggregate_voices_from_measures()
			
	def clean_voices(self):
		for part in self.parts:
			part.clean_voices()
			
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
		self.parent_part = None # For staff parts
		
		
		if part_type==Part.GROUP_PART:
			#print (f"Creating a part group for part {id_part}")
			m21_group = []
			for part_staff in group:
				m21_group.append(part_staff.m21_part)
				# Set the parent
				part_staff.parent_part = self
			self.m21_part = m21.layout.StaffGroup(m21_group, 
								 name=name, abbreviation=abbreviation,
								 symbol='brace',id=id_part)
			self.staff_group = group
			
		elif part_type == Part.STAFF_PART:
			#print (f"Creating a part Staff for part {id_part} and no staff {no_staff}")
			self.m21_part = m21.stream.PartStaff(id=id_part)
			#self.staves[no_staff] =  notation.Staff(no_staff)
		else:
			self.m21_part = m21.stream.Part(id=id_part)
			#self.staves[no_staff] =  notation.Staff(no_staff)
	
		# Metadata
		self.m21_part.id  = "P" + id_part
		self.m21_part.partName  = name
		self.m21_part.partAbbreviation = abbreviation
		self.part_type = part_type

		"""
		   During parsing, we maintain the current interpretation 
		   context. It consists in the current key, current time 
		   signature, current alterations met so far, and current clef.
		   
		   This is based on the fact that a part = a staff in the
		   music21 model (for parts with part_type = STAFF_PART)
		"""
		self.current_key_signature = notation.KeySignature() 
		self.current_time_signature = notation.TimeSignature() 
		
		# Sequence of clefs found in the part, at a given position
		self.current_clefs = [
			{"pos": -1, "clef": notation.Clef(notation.Clef.NO_CLEF)}
			]
		
		# List of accidentals met so far
		self.accidentals = {"A": None, "B": None, "C": None, 
						  "D": None, "E": None, "F": None, "G": None}
		self.reset_accidentals()
	
		# List of measures of this part
		self.measures = []
		self.current_measure = None

		# List of voices, and local counter for the voice 
		self.reset_voice_counter()
		self.voices = []
		
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

	def reset_voice_counter(self):
		self.voice_counter = 0
	def new_voice_counter(self):
		self.voice_counter += 1
		return self.voice_counter
		
	def set_instrument(self, instr_name, instr_abbrev):
		# The instrument gives informations about the part, 
		# and in particular its id (which must be the 'partId' attribute) 
		instr =  m21.instrument.Piano()
		instr.partId = self.id
		instr.instrumentName = instr_name
		instr.instrumentAbbreviation = instr_abbrev
		
		if self.part_type==Part.GROUP_PART:
			self.staff_group[0].m21_part.insert(0, instr)
		else: 
			self.m21_part.insert(0, instr)
			
	def reset_accidentals (self):
		# Used to forget that we ever met an accidental on this staff
		if self.part_type==Part.GROUP_PART:
			for part_staff in self.staff_group:
				part_staff.reset_accidentals()
		else:
			for pitch_class in self.accidentals.keys():
				self.accidentals[pitch_class] = events.Note.ALTER_NONE		
				
	def add_accidental (self, pitch_class, acc):
		# Record accidentals met in a measure
		self.accidentals[pitch_class] = acc
				
	def get_part_staff (self, no_staff):
		# Given the number of the staff, returns the 
		# corresponding part staff
		if self.part_type == Part.GROUP_PART:
			if len(self.staff_group) >= no_staff:
				return self.staff_group[no_staff-1]
			else:
				logger.error (f"Unable to find a current measure for part {self.id} and staff {no_staff}")
				raise CScoreModelError (f"Unable to find a current measure for part {self.id} and staff {no_staff}")
		else:
			# Too easy...
			return self
		
	def get_duration(self):
		if self.part_type == Part.GROUP_PART:
			#WARNING: hope that both sub-part are at the same position
			return self.staff_group[0].get_duration()
		else:
			return self.m21_part.duration.quarterLength
	
	def set_current_key_signature (self, key,no_staff=1):
		if self.part_type == Part.GROUP_PART:
			subpart = self.get_part_staff (no_staff)
			#print (f"Setting time signature with id {ts.id} to staff {no_staff}")
			changed_key = subpart.set_current_key_signature(key)

			# Keep the current at the global part level: it
			# is used to determine default alterations
			if changed_key:
				self.current_key_signature = key
				if self.current_measure is not None:
					self.current_measure.replace_key_signature(key)
			
				## TRICK ! In MusicXML there is only one  signature for both staves.
				## The id of the second one is lost, and we cannot therefore find
				## the related annotation. Hence the trick: we concatenate
				## in the first KS the ids of all the symbol found on the score
				if no_staff == 2:
					first_staff_part = self.get_part_staff (1)
					first_staff_ks = first_staff_part.current_measure.initial_ks 
					first_staff_ks.id = f"{first_staff_ks.id}{ID_SEPARATOR}{key.id}"
					first_staff_ks.m21_key_signature.id = first_staff_ks.id

			return changed_key
		else:
			# Returns True is a change of key has been found
			#if self.current_key_signature is not None:
			if self.current_key_signature.equals(key) and not self.current_key_signature.is_by_default:
				return False 
			else:
				self.current_key_signature = key
				if self.current_measure is not None:
						# Might be done during part initialization
						self.current_measure.replace_key_signature(key)
				return True
			#else:		
			#	self.current_key_signature = key
			#	return True
		
	def set_current_time_signature (self, ts, no_staff=1):
		if self.part_type == Part.GROUP_PART:
			# Propagate it to the subpart
			subpart = self.get_part_staff (no_staff)
			changed_ts = subpart.set_current_time_signature(ts)			

			# Keep the current at the global part level: it
			# is used to check the length of voices
			if changed_ts:
				self.current_time_signature = ts
				if self.current_measure is not None:
					self.current_measure.replace_time_signature(ts)
				
				## TRICK ! See the comment in set_key_signature
				if no_staff == 2:
					first_staff_part = self.get_part_staff (1)
					first_staff_ts = first_staff_part.current_measure.initial_ts 
					first_staff_ts.id = f"{first_staff_ts.id}{ID_SEPARATOR}{ts.id}"
					first_staff_ts.m21_time_signature.id = first_staff_ts.id
			return changed_ts
		else:
			if self.current_time_signature.equals(ts) and not self.current_time_signature.is_by_default:
				return False
			else:
				self.current_time_signature = ts
				if self.current_measure is not None:
					# Might be done during part initialization
					self.current_measure.replace_time_signature(ts)
				return True
		
	def get_clef_at_pos (self, position=0):
		# Find, in the stream of clef, the clef valid at the given pos
		clef = self.current_clefs[0]['clef']
		for cur_clef in self.current_clefs:
			if cur_clef['pos'] <= position:
				clef = cur_clef['clef'] 
		return clef

	def set_current_clef (self, clef, no_staff, abs_position=0):
		# Get the part, given the staff
		part = self.get_part_staff(no_staff)
		current_clef = part.get_clef_at_pos(abs_position)
		
		if current_clef.equals(clef):
			# No need to change the clef ! Probably an initial signature
			logger.info (f"Clef {clef} is already the current clef for part {part.id} at position {abs_position}")
			return False
		else:
			logger.info (f"Setting the current clef to {clef} for part {part.id} at position {abs_position}")
			print (f"Setting the current clef to {clef} with id {clef.id} for part {part.id} at position {abs_position}")
			part.current_clefs.append({"pos": abs_position, "clef": clef})
			# Insert the clef in the music flow
			part.current_measure.set_initial_clef(clef, abs_position)
			return True
				
	def get_current_time_signature(self):
		return self.current_time_signature
	def get_current_key_signature(self):
		return self.current_key_signature

	def add_measure (self, measure_no):

		if self.part_type == Part.GROUP_PART:
			# This is the measure of the group. It is not exported but we give an id anyway
			id_measure = Measure.make_measure_id(self.id + "-group", measure_no)
		else:
			if self.parent_part is None:
				# A single part, no pb
				id_measure = Measure.make_measure_id(self.id, measure_no)
			else:
				# A part staff in a group: the measure is identified wrt the parent part
				id_measure = Measure.make_measure_id(self.parent_part.id, measure_no)
				

		measure = Measure(self, measure_no, id_measure)
		
		""" In case this is the first measure, we insert
		   the current time signature (necessary when 
		    a part begins after the other, and the TS is implicit)
		    Music21 seems clever enough to remove subsequent and equals signatures
		"""
		if len(self.measures) == 0:
			default_ts = self.current_time_signature.copy()
			default_ts.set_by_default(f"default_ts_{self.id}")
			measure.add_time_signature(default_ts)
			default_ks = self.current_key_signature.copy()
			default_ks.set_by_default(f"default_ks_{self.id}")
			measure.add_key_signature(default_ks)
			
			
		self.measures.append(measure)
		self.current_measure = measure
			
		if not self.part_type == Part.GROUP_PART:
			self.m21_part.append(measure.m21_measure)
		else:
			# We keep a global measure at the part level, to record
			# the voices and other informations global to the part.
			# However this global measure is NOT added to the music21 part
			pass
			
		if self.part_type == Part.GROUP_PART:			
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
		part = self.get_part_staff(no_staff)
		return part.current_measure
			
	def add_measure_voice(self, voice):
		"""
		  Add a voice internal to the current measure.
			NB: in case of a GROUP_PART, the current measure is not
			inserted in the music21 part. We only use it to keep
			global information on the part (particularly voices, that may span
			the sub parts)
		"""
		
		self.current_measure.add_voice(voice)
		
		# In case of a GROUP_PART (several staves), we add the voice to one of the sub parts
		if self.part_type == Part.GROUP_PART:
			#  We determine the main staff
			main_staff = voice.determine_main_staff()
			# We add the voice to the part measure with this staff			
			measure = self.get_measure_from_staff(main_staff)
			measure.add_voice(voice)
			
	def add_slur(self, events):
		m21_group = []
		for e in events:
			m21_group.append(e.m21_event)
			if self.part_type == Part.GROUP_PART:
				# Shoudl we insert in one of the sub parts ??
				self.current_measure.m21_measure.insert(0, m21.spanner.Slur(m21_group))
			else:
				self.m21_part.insert(0, m21.spanner.Slur(m21_group))

	def add_system_break(self):
		for measure in  self.get_current_measures():
			measure.add_system_break()

	def add_page_break(self):
		for measure in  self.get_current_measures():
			measure.add_page_break()
	
	def insert_measure (self, position, measure):
		logger.info (f'Inserting measure {measure.no} at position {position} in part {self.id}')
		if not self.part_type == Part.GROUP_PART:
			self.m21_part.insert(position, measure.m21_measure)
		else:
			# Insert the measure in each part-staff
			for staff_part in self.staff_group: 
				staff_part.m21_part.insert(position, measure.m21_measure)
				
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
					measure.part.set_current_time_signature (ts)
					measure.replace_time_signature (ts)

	def check_measure_consistency(self):
		list_removals = []
		if self.part_type==Part.GROUP_PART:
			for part_staff in self.staff_group:
				list_removals += part_staff.check_measure_consistency()
		else:
			for measure in	self.measures:
				if  measure.no == 1 and measure.initial_clef is None:
					logger.warning (f"Measure 1 in part {self.id} has no initial clef. Adding treble")
					# Add a treble clef for safety
					default_clef = notation.Clef(notation.Clef.TREBLE_CLEF)
					measure.m21_measure.insert(0,  default_clef.m21_clef)
				list_removals += measure.check_consistency(fix=True)	
		
		return list_removals
		
	def aggregate_voices_from_measures(self):
		"""
			 This function attempts to connect the voices internal to the measures
			 in a set of voices global to the part
		"""
		logger.info (f"\nAggregate measure voices for part {self.id}") 
		self.voices = []
		current_voice_id = 0
		# We maintain an array of current voices
		current_voices = []
		for m in self.measures:
			#print (f"Processing voice from measure {m.id}. Nb voices = {m.nb_voices()} Current nb of voices: {len(current_voices)}")
			if self.voices == []:
				# Copy the voices of the first measure
				for v in m.voices:
					current_voice_id += 1
					part_voice = Voice(self, f"{current_voice_id}")
					part_voice.copy_from(v)
					self.voices.append(part_voice)	
					current_voices.append (part_voice)
			else:
				if len(m.voices) >= len(current_voices):
					# We copy the first voices of the measure if the opened voices. 
					# We can probably do better in terms of matching
					i_voice = 0
					for part_voice in current_voices:
						measure_voice = m.voices[i_voice]
						part_voice.copy_from(measure_voice)
						i_voice += 1
					# Now what happens if there is a new voice ?
					if len(m.voices) > len(current_voices):
						for i_voice in range (len(current_voices), len(m.voices)):
							current_voice_id += 1
							#print (f"Adding a new voice {current_voice_id} at this measure.")
							part_voice = Voice(self, f"{current_voice_id}")
							part_voice.copy_from(m.voices[i_voice])
							self.voices.append(part_voice)
							current_voices.append (part_voice)				
				else:
					for i_voice in range (len(m.voices)):
						part_voice = current_voices[i_voice]
						part_voice.copy_from(m.voices[i_voice])
					# This closes the last additional voice met
					#print (f"Warning: the number of voices is lesser for this measure.")
					for i_voice in range (len(m.voices), len(current_voices)):
						current_voices.pop()
						
			#for voice in current_voices:
			#	print (f"Current voice voice {voice.id}")

		#for v in self.voices:
		#	v.display()
				
	def clean_voices(self):
		# Clean the voice of possible inconsistencies. For
		# instance ties that to not make sense
		for voice in self.voices:
			#print (f"Cleaning voice {voice.id} in part {self.id}")
			voice.clean()
							

class Measure:
	"""
		Representation of a measure, which belongs to a part
	"""

	@staticmethod
	def make_measure_id (id_part, no):
		'''
		  A measure (in the model) is identified by the measure number
		  and the part it belongs to
		'''
		return f'm{no}-{id_part}' 

	def __init__(self, part, no_measure, id) :
		self.part = part
		self.no = no_measure
		self.voices = []
		self.id = id
		self.m21_measure = m21.stream.Measure(id=self.id, number=no_measure)
		self.m21_measure.style.absoluteX = 23

		# Absolute position of the measure. Initialized with the current part position
		#
		# BEWARE: if we have voices too long, then the part duration is not reliable.
		self.absolute_position = part.get_duration()
		
		# Used for checking consistency
		# Note: there is only one time signature, common to all staves 
		self.initial_ts = part.current_time_signature
			
		# Same thing for the key signature
		self.initial_ks = part.current_key_signature
		
		# A measure may have an initial clef. The first measure MUST have an initial clef
		# This is tested in check_measure_consistency()
		self.initial_clef = None 
	def set_initial_clef (self, clef, abs_position=0):
		# We add the clef to music 21 measure. 
		relative_position = abs_position - self.absolute_position 
		logger.info (f"Adding Clef {clef.m21_clef} at relative position {relative_position} to the current measure of part {self.part.id}")
		print (f"Adding Clef {clef.m21_clef} with id {clef.m21_clef.id} at relative position {relative_position} to the current measure of part {self.part.id}")
		self.m21_measure.insert(relative_position,  clef.m21_clef)
		if relative_position == 0:
			self.initial_clef = clef
		
	def add_time_signature(self, time_signature):
		self.initial_ts = time_signature
		self.m21_measure.insert(0,  time_signature.m21_time_signature)

	def replace_time_signature(self, new_time_signature):
		if 	self.initial_ts is not None:
			self.m21_measure.remove(self.initial_ts.m21_time_signature)
			self.add_time_signature(new_time_signature)
			
	def add_key_signature(self, key_signature):
		self.initial_ks = key_signature
		self.m21_measure.insert(0,  key_signature.m21_key_signature)
	def replace_key_signature(self, new_key_signature):
		if 	self.initial_ks is not None:
			self.m21_measure.remove(self.initial_ks.m21_key_signature)
		self.add_key_signature(new_key_signature)
		
	def add_voice (self, voice):
		self.voices.append(voice)
		self.m21_measure.insert (0, voice.m21_stream)
		# The absolute position of the voice is that of the measure
		#voice.absolute_position = self.absolute_position
		
	def add_system_break(self):
		system_break = m21.layout.SystemLayout(isNew=True)
		self.m21_measure.insert (system_break)

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
		
		# List of events removed 
		list_removals = []
		
		# First get the time signature in effect
		for voice in self.voices:
			bar_duration = self.get_expected_duration()
			if voice.get_duration() > bar_duration:					
				# Trying to fix this. Easy when we just have to complete the voice
				if fix:
					logging.info (f"Overduration in measure {self.id}. Expected duration: {bar_duration}. Voice {voice.id} duration is {voice.get_duration()}")
					removed_events = voice.shrink_to_bar_duration(bar_duration)
					if removed_events is not None:
						list_removals.append(removed_events)
					#logging.warning (f"After fix, measure duration: {bar_duration}. Voice {voice.id} duration {voice.get_duration()} / {voice.m21_stream.duration}")

				# We do nothing is the voice is included in the measure
				# incomplete voices are accepted

		return list_removals

	def get_duration(self):
		# Returns the measure duration based on it metric
		return self.m21_measure.duration.quarterLength
			
	def get_expected_duration(self):
		# Returns the measure duration based on it metric
		return self.initial_ts.barDuration().quarterLength
		
	def length(self):
		# Music21 conventions
		return self.m21_measure.duration
	def nb_voices(self):
		return len(self.voices)


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

