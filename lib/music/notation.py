import music21 as m21

import lib.music.events as score_events

import lib.music.Score as score_mod

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
		self.denom = denom
		self.single_digit = False
		# m21 duration is the float obtained from the fraction
		self.m21_time_signature = m21.meter.TimeSignature('{}/{}'.format(self.numer, self.denom))
		self.m21_time_signature.id = self.id
		
		

	def symbolize(self):
		# Display the TS as a symbole
		if (self.numer==4 and self.denom==4):
			self.m21_time_signature.symbol="common"
		if (self.numer==2 and self.denom==4):
			self.m21_time_signature.symbol="cut"

	def set_single_digit(self):
		# Option to show the numerator only
		self.m21_time_signature.symbol="single-number"
	
	def copy (self):
		# Make a copy of the current object
		return TimeSignature (self.numer, self.denom)
	
	def code(self):
		return f"{self.numer} / {self.denom}"
	
	def barDuration(self):
		# Expected duration of a bar with this TS
		return self.m21_time_signature.barDuration
	
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
		

	# Layer over the music21 functions
	def accidental_by_step(self, pitch):
		if self.m21_key_signature.accidentalByStep(pitch) is not None:
			return self.m21_key_signature.accidentalByStep(pitch).name
		else:
			return score_events.Note.ALTER_NONE

	def copy (self):
		# Make a copy of the current object
		return KeySignature (self.nb_sharps, self.nb_flats, self.nb_naturals)

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
	DMOS_UT_CLEF="U"

	TREBLE_CLEF = m21.clef.TrebleClef
	ALTO_CLEF = m21.clef.AltoClef
	TENOR_CLEF = m21.clef.AltoClef
	BASS_CLEF = m21.clef.BassClef
	NO_CLEF = m21.clef.NoClef
	
	def __init__(self, clef_code, id=None) :
		if id is None:
			self.id = f"clef{Clef.counter}"
		else:
			# Id provided
			self.id = id

		if clef_code == self.TREBLE_CLEF:
			self.m21_clef = m21.clef.TrebleClef()
		elif clef_code == self.ALTO_CLEF:
			self.m21_clef = m21.clef.AltoClef()
		elif clef_code == self.TENOR_CLEF:
			self.m21_clef = m21.clef.TenorClef()
		elif clef_code == self.BASS_CLEF:
			self.m21_clef = m21.clef.BassClef()
		elif clef_code == self.NO_CLEF:
			self.m21_clef = m21.clef.NoClef()
		self.m21_clef.id = self.id
		self.m21_clef.style = self.id
		Clef.counter += 1
		
	def equals(self, other):
		# Check if two clefs are identical
		if other.m21_clef == self.m21_clef:
			return True
		else:
			return False
		
	@staticmethod 
	def decode_from_dmos (dmos_code, dmos_height, dmos_id=None):
		if dmos_id == "clef_1223_1710":
			print ("Decode " + dmos_code)
		if dmos_code == Clef.DMOS_TREBLE_CLEF:
			return Clef (Clef.TREBLE_CLEF, dmos_id)
		elif dmos_code == Clef.DMOS_BASS_CLEF:
			return Clef (Clef.BASS_CLEF, dmos_id)
		elif dmos_code == Clef.DMOS_UT_CLEF and dmos_height==3:
			return Clef (Clef.ALTO_CLEF, dmos_id)
		elif dmos_code == Clef.DMOS_UT_CLEF and dmos_height==4:
			return Clef (Clef.TENOR_CLEF, dmos_id)
		else:
			# Should not happen
			score_mod.logger.error('Unable to decode DMOS code for clef: ' + dmos_code 
						+ " " + str(dmos_height))
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
	number= 0
	START_BEAM="start"
	STOP_BEAM="stop"
	CONTINUE_BEAM="continue"
	
	def __init__(self, beam_type=START_BEAM) :
		# Unclear role of the beam member. Seems to be useful in case of several beams on a same group
		Beam.number = Beam.number + 1
		self.beam_type = beam_type
		self.m21_beam = m21.beam.Beam(type=beam_type, number=1)
