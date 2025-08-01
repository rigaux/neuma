import music21 as m21

import lib.music.events as score_events

import lib.music.Score as score_mod

# for XML editions
from lxml import etree

'''
 Classes representing music notation elements
'''

class Staff:
	'''
		Staff = space where a set of voices from a part (or more?) 
		are displayed. We record in each Staff object the list
		of notational events that occur (clef, signatures, directions, etc.)
	'''
	
	def __init__(self, no_staff) :
		''' 
		   A dictionary, indexed on measures, that records the clefs
		    used in the staff
		    What if a change occurs in the middle of a measure ? Not
		    supported for the time being. We will need a more powerful
		    notion of 'position'
		'''
		self.id = no_staff
		self.current_clef = Clef(Clef.NO_CLEF)
		
		# List of accidentals met so far
		self.accidentals = {"A": None, "B": None, "C": None, 
						  "D": None, "E": None, "F": None, "G": None}
		self.reset_accidentals()

	def reset_accidentals (self):
		# Used to forget that we ever met an accidental on this staff
		for pitch_class in self.accidentals.keys():
			self.accidentals[pitch_class] = score_events.Note.ALTER_NONE		
	def add_accidental (self, pitch_class, acc):
		# Record accidentals met in a measure
		self.accidentals[pitch_class] = acc
		
	def set_current_clef (self, clef):
		if self.current_clef.equals(clef):
			# No need to change the clef ! Probably an initial signature
			score_mod.logger.info (f"Clef {clef} is already the current clef for staff {self.id}")
			return False
		else:
			score_mod.logger.info (f"Clef {clef} becomes the current clef for staff {self.id}")
			self.current_clef = clef

	def get_current_clef (self):
		return self.current_clef
		
class TimeSignature:
	'''
		Represented as a fraction
	'''
	counter = 0
	
	def __init__(self, numer=4, denom=4, id_ts=None) :
		#self.fraction = Fraction (numer, denom)
		if id_ts is None:
			self.id =f"tsign{TimeSignature.counter}" 
			TimeSignature.counter += 1
		else:
			self.id = id_ts

		self.numer = numer
		
		# The denom must be in 1, 2, 4? 8, 16, 32
		if denom not in [1, 2, 4, 8, 16, 32]:
			score_mod.logger.warning (f"Trying to instantiate a time signature with denom {denom}")
			if denom == 3:
				# Bet: confusion with a 8
				denom =8

		self.denom = denom
		self.single_digit = False
		self.is_by_default = False

		# m21 duration is the float obtained from the fraction
		self.m21_time_signature = m21.meter.TimeSignature('{}/{}'.format(self.numer, self.denom))
		self.m21_time_signature.id = self.id

	def set_by_default (self, default_id):
		# Tells that the TS is by default and should be replaced
		self.id = default_id
		self.m21_time_signature.id = default_id
		self.is_by_default = True

	def symbolize(self):
		# Display the TS as a symbole
		if (self.numer==4 and self.denom==4):
			self.m21_time_signature.symbol="common"
		if (self.numer==2 and self.denom==2):
			self.m21_time_signature.symbol="cut"

	def set_single_digit(self):
		# Option to show the numerator only
		self.m21_time_signature.symbol="single-number"
	
	def copy (self):
		# Make a copy of the current object
		return TimeSignature (self.numer, self.denom)
	
	def code(self):
		return f"{self.numer} / {self.denom}"

	def choose_best (self, other):
		
		# Used when some inconsistency is found in a list of signatures
		
		# If 
		return self 

	def barDuration(self):
		# Expected duration of a bar with this TS
		return self.m21_time_signature.barDuration

	def equals(self, other):
		# Check if two time signatures are identical
		# Does not work? if other.m21_time_signature == self.m21_time_signature:
		if other.denom == self.denom and other.numer==self.numer:
			return True
		else:
			return False
	
	def __str__ (self):
		return f"({self.numer} / {self.denom})"
	
class KeySignature:
	'''
		Represented as the number of sharps (same as music21)
	'''
	
	counter = 0

	def __init__(self, nb_sharps=0, nb_flats=0, nb_naturals=0, id_key=None) :
		self.nb_sharps = nb_sharps
		self.nb_flats = nb_flats
		self.nb_naturals = nb_naturals
		self.is_by_default = False
		
		if nb_sharps > 0:
			self.m21_key_signature = m21.key.KeySignature(nb_sharps)
		elif nb_flats > 0:
			self.m21_key_signature = m21.key.KeySignature((-1) * nb_flats)
		else:
			self.m21_key_signature = m21.key.KeySignature(0)
			
		if id_key is None:
			self.id = f"ksign{KeySignature.counter}"
			KeySignature.counter += 1
		else:
			self.id = id_key
		self.m21_key_signature.id = self.id
		

	def set_by_default (self, default_id):
		# Tells that the TS is by default and should be replaced
		self.id = default_id
		self.m21_key_signature.id = default_id
		self.is_by_default = True
		
	# Layer over the music21 functions
	def accidental_by_step(self, pitch):
		if self.m21_key_signature.accidentalByStep(pitch) is not None:
			return self.m21_key_signature.accidentalByStep(pitch).name
		else:
			return score_events.Note.ALTER_NONE

	def nb_alters(self):
		if self.nb_sharps > self.nb_flats:
			return self.nb_sharps 
		else:
			return self.nb_flats 
	def equals(self, other):
		# Check if two key signatures are identical
		if other.m21_key_signature == self.m21_key_signature:
			return True
		else:
			return False
			
	def code(self):
		return f"{self.m21_key_signature.asKey()}"
		
	def alter_type(self):
		if self.nb_sharps > 0:
			return "sharp"
		else:
			return "flat"

	def copy (self):
		# Make a copy of the current object
		return KeySignature (self.nb_sharps, self.nb_flats, self.nb_naturals)

	def choose_best (self, other):
		
		# Used when some inconsistency is found in a list of signatures
		# Choose the other if is has more alterations (?!)
		if other.nb_alters() > self.nb_alters():
			return other
		else:
			return self 
			
	def local_copy (self, other):
		# Make a clone of the current object from the other one
		self.nb_sharps = other.nb_sharps
		self.nb_flats = other.nb_flats
		self.nb_naturals = other.nb_naturals

	def __str__ (self):
		return f"{self.m21_key_signature.asKey()}"

class Clef:
	'''
		Same as m21
	'''
	counter = 0

	# DMOS encoding of clefs
	DMOS_TREBLE_CLEF="G"
	DMOS_BASS_CLEF="F"
	DMOS_UT_CLEF="C"
	DMOS_UT_CLEF_SYN="U"

	TREBLE_CLEF = m21.clef.TrebleClef
	TREBLE_8PLUS_CLEF = m21.clef.Treble8vbClef
	TREBLE_8MIN_CLEF = m21.clef.Treble8vaClef
	SOPRANO_CLEF = m21.clef.SopranoClef
	MEZZO_CLEF = m21.clef.MezzoSopranoClef
	ALTO_CLEF = m21.clef.AltoClef
	TENOR_CLEF = m21.clef.TenorClef
	BARITONE_CLEF = m21.clef.CBaritoneClef
	FBARITONE_CLEF = m21.clef.FBaritoneClef
	BASS_CLEF = m21.clef.BassClef
	NO_CLEF = m21.clef.NoClef
	
	def __init__(self, clef_code, id=None) :
		if id is None:
			self.id = f"clef{Clef.counter}"
		else:
			# Id provided
			self.id = id
			# The following is used to insert a note on a staff with a height that needs to be adjusted
			self.default_height = 5

		if clef_code == self.TREBLE_CLEF:
			self.m21_clef = m21.clef.TrebleClef()
			self.default_height = 5
		elif clef_code == self.TREBLE_8PLUS_CLEF:
			self.m21_clef = m21.clef.Treble8vbClef()
			self.default_height = 5
		elif clef_code == self.TREBLE_8MIN_CLEF:
			self.m21_clef = m21.clef.Treble8vaClef()
			self.default_height = 5
		elif clef_code == self.SOPRANO_CLEF:
			self.m21_clef = m21.clef.SopranoClef()
			self.default_height = 0
		elif clef_code == self.MEZZO_CLEF:
			self.m21_clef = m21.clef.MezzoSopranoClef()
			self.default_height = 2
		elif clef_code == self.ALTO_CLEF:
			self.m21_clef = m21.clef.AltoClef()
			self.default_height = 4
		elif clef_code == self.TENOR_CLEF:
			self.m21_clef = m21.clef.TenorClef()
		elif clef_code == self.BARITONE_CLEF:
			self.default_height = 6
			self.m21_clef = m21.clef.CBaritoneClef()
		elif clef_code == self.FBARITONE_CLEF:
			self.default_height = 3
			self.m21_clef = m21.clef.FBaritoneClef()
		elif clef_code == self.BASS_CLEF:
			self.m21_clef = m21.clef.BassClef()
			self.default_height = 6
		elif clef_code == self.NO_CLEF:
			self.m21_clef = m21.clef.NoClef()
		self.m21_clef.id = self.id
		Clef.counter += 1
	
	def sign(self):
		return self.m21_clef.sign
	def height(self):
		return self.m21_clef.line

	def equals(self, other):
		# Check if two clefs are identical
		if other.m21_clef == self.m21_clef:
			return True
		else:
			return False
		
	@staticmethod 
	def decode_from_dmos (dmos_code, dmos_height, dmos_id=None,
						  dmos_octave_change=0):
		
		# Safety : both "U" and "C" are accepted for C cle.
		# We harmonize to the later
		if dmos_code == Clef.DMOS_UT_CLEF_SYN:
			dmos_code = Clef.DMOS_UT_CLEF
			
		if dmos_code == Clef.DMOS_TREBLE_CLEF:
			if  dmos_octave_change ==0:
				return Clef (Clef.TREBLE_CLEF, dmos_id)
			elif  dmos_octave_change ==1:
				return Clef (Clef.TREBLE_8PLUS_CLEF, dmos_id)
			elif  dmos_octave_change == -1:
				return Clef (Clef.TREBLE_8MIN_CLEF, dmos_id)
		elif dmos_code == Clef.DMOS_BASS_CLEF:
			if dmos_height==3:
				return Clef (Clef.FBARITONE_CLEF, dmos_id)
			else:
				return Clef (Clef.BASS_CLEF, dmos_id)
		elif dmos_code == Clef.DMOS_UT_CLEF and dmos_height==1:
			return Clef (Clef.SOPRANO_CLEF, dmos_id)
		elif dmos_code == Clef.DMOS_UT_CLEF and dmos_height==2:
			return Clef (Clef.MEZZO_CLEF, dmos_id)
		elif dmos_code == Clef.DMOS_UT_CLEF and dmos_height==3:
			return Clef (Clef.ALTO_CLEF, dmos_id)
		elif dmos_code == Clef.DMOS_UT_CLEF and dmos_height==4:
			return Clef (Clef.TENOR_CLEF, dmos_id)
		elif dmos_code == Clef.DMOS_UT_CLEF and dmos_height==5:
			return Clef (Clef.BARITONE_CLEF, dmos_id)
		else:
			# Should not happen
			score_mod.logger.error(f"Unable to decode DMOS code for clef: {dmos_code}/{dmos_height}, id: {dmos_id}. Replaced by treble clef.")
			return Clef (Clef.TREBLE_CLEF)

	def decode_pitch (self, height):
		''' 
			Given the height on a staff, return the pitch class and octave
		'''
		
		#print ("Decode pitch from height " + str(height) + " and clef " + self.m21_clef)
		# The note of the lowest line
		if hasattr(self.m21_clef, 'lowestLine'):
			diatonic_num_base = self.m21_clef.lowestLine
		else:
			# Strange, we got a note but we do not know the key ?!
			score_mod.logger.warning(f"Found a note symbol without having a Clef ?  Assuming G")
			diatonic_num_base = m21.clef.TrebleClef().lowestLine
			
		# We add the line obtained from DMOS
		diatonic_num = diatonic_num_base + height
		pitch = m21.pitch.Pitch() 
		pitch.diatonicNoteNum = diatonic_num
		
		# Check
		if pitch.octave < 0 or pitch.octave > 9:
			score_mod.logger.error(f"Invalid octave found when decoding note with clef {m21.clef.TrebleClef()} and height {height}")
			# Try to fix
			if pitch.octave < 0:
				pitch.octave = 0
			if pitch.octave > 9:
				pitch.octave = 9
			
		return (pitch.step, pitch.octave)

	def __str__ (self):
		return f"({self.m21_clef.sign},{self.m21_clef.line})"

class Beam:
	'''
		Same as Music21
	'''
	START_BEAM="start"
	STOP_BEAM="stop"
	CONTINUE_BEAM="continue"
	
	def __init__(self, beam_type=START_BEAM) :
		# Unclear role of the beam member. Seems to be useful in case of several beams on a same group
		Beam.number = 1
		self.beam_type = beam_type
		self.m21_beam = m21.beam.Beam(type=beam_type, number=Beam.number )
