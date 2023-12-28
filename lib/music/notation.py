import copy
import music21 as m21


import lib.music.events as score_events

import lib.music.Score as score_mod
from numpy import True_, False_

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
		self.current_key_signature = KeySignature() 
		self.current_time_signature = TimeSignature() 

		# Probably not useful at the end, since these notations are
		# directly injected in the music21 measure.
		self.clef_events = {}
		self.time_signature_events = {}
		self.key_signature_events = {}
		#####
		
		# List of accidentals met so far
		self.accidentals = {"A": "", "B": "", "C": "", "D": "", "E":"", "F": "", "G": ""}
		self.reset_accidentals()

	def reset_accidentals (self):
		# Used to forget that we ever met an accidental on this staff
		for pitch_class in self.accidentals.keys():
			self.accidentals[pitch_class] = score_events.Note.ALTER_NONE		
	def add_accidental (self, pitch_class, acc):
		# Record accidentals met in a measure
		self.accidentals[pitch_class] = acc
		
	def get_accidental (self, pitch_class):
				
		if self.accidentals[pitch_class] != "":
			return self.accidentals[pitch_class]
		else:
			# The key signature holds
			return self.current_key_signature.accidentalByStep(pitch_class)

	def set_current_clef (self, clef):
		self.current_clef = clef
	def set_current_key_signature (self, key):
		self.current_key_signature = key
	def set_current_time_signature (self, ts):
		self.current_time_signature = ts

	'''
	    All these functions are now useless. To be removed
	
		
	def add_clef (self, no_measure, clef):
		self.clef_events[no_measure] = clef
		self.current_clef = clef
	def add_time_signature (self, no_measure, ts):
		self.time_signature_events[no_measure] = ts
		
	def clef_found_at_measure (self, no_measure):
		return (no_measure in self.clef_events.keys())
	def get_clef (self, no_measure):
		return self.clef_events[no_measure]

	def ts_found_at_measure (self, no_measure):
		return (no_measure in self.time_signature_events.keys())
	def get_time_signature (self, no_measure):
		return self.time_signature_events[no_measure]
	'''
		
class TimeSignature:
	'''
		Represented as a fraction
	'''
	counter = 0
	
	def __init__(self, numer=4, denom=4) :
		#self.fraction = Fraction (numer, denom)
		self.numer = numer
		self.denom = denom
		# m21 duration is the float obtained from the fraction
		self.m21_time_signature = m21.meter.TimeSignature('{}/{}'.format(self.numer, self.denom))
		self.m21_time_signature.id = f"tsign{TimeSignature.counter}" 
		TimeSignature.counter += 1

	def copy (self):
		# Make a copy of the current object
		return TimeSignature (self.numer, self.denom)
	
	def __str__ (self):
		return f"({self.numer} / {self.denom})"
	
class KeySignature:
	'''
		Represented as the number of sharps (same as music21)
	'''
	
	counter = 0

	def __init__(self, nb_sharps=0, nb_flats=0, nb_naturals=0) :
		if nb_sharps > 0:
			self.m21_key_signature = m21.key.KeySignature(nb_sharps)
		elif nb_flats > 0:
			self.m21_key_signature = m21.key.KeySignature((-1) * nb_flats)
		else:
			self.m21_key_signature = m21.key.KeySignature(0)
		self.m21_key_signature.id = f"ksign{KeySignature.counter}"
		KeySignature.counter += 1

	# Layer over the music21 functions
	def accidentalByStep(self, pitch):
		if self.m21_key_signature.accidentalByStep(pitch) is not None:
			return self.m21_key_signature.accidentalByStep(pitch).name
		else:
			return score_events.Note.ALTER_NONE

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
	
	def __init__(self, clef_code) :
		self.id = f"clef{Clef.counter}"

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
		Clef.counter += 1
		
	def equals(self, other):
		# Check if two clefs are identical
		if other.m21_clef == self.m21_clef:
			return True
		else:
			return False
		
	@staticmethod 
	def decode_from_dmos (dmos_code, dmos_height):
		#print ("Decode " + dmos_code)
		if dmos_code == Clef.DMOS_TREBLE_CLEF:
			return Clef (Clef.TREBLE_CLEF)
		elif dmos_code == Clef.DMOS_BASS_CLEF:
			return Clef (Clef.BASS_CLEF)
		elif dmos_code == Clef.DMOS_UT_CLEF and dmos_height==3:
			return Clef (Clef.ALTO_CLEF)
		elif dmos_code == Clef.DMOS_UT_CLEF and dmos_height==4:
			return Clef (Clef.TENOR_CLEF)
		else:
			# Should not happen
			score_mod.logger.error('Unable to decode DMOS code for clef: ' + dmos_code 
						+ " " + str(dmos_height))
			return Clef (TREBLE_CLEF)


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
		return (pitch.step, pitch.octave)

	def __str__ (self):
		return f"({self.m21_clef.sign},{self.m21_clef.line})"

class Dynamics ():
	"""
		Dynamics = directions
	"""
	
	PIANO="p"
	PIANISSIMO="pp"
	FORTE="f"
	FORTISSIMO="ff"
	MEZZOPIANO="mp"
	MEZZOFORTE="mf"
	
	def __init__(self, placement, dyn_type) :
		if dyn_type == Dynamics.PIANO:
			self.m21_dynamic = m21.dynamics.Dynamic('p')
		elif dyn_type == Dynamics.FORTE:
			self.m21_dynamic = m21.dynamics.Dynamic('f')
		else:
			raise score_mod.CScoreModelError (f"Unknown dynaics type: '{dyn_type}'")

		self.m21_dynamic.placement = placement
		
		return

class Beam:
	'''
		Same as Music21
	'''
	number= 0
	
	def __init__(self) :
		# Unclear role of the beam member. Seems to be useful in case of several beams on a same group
		Beam.number = Beam.number + 1
		self.m21_beam = m21.beam.Beam(type='start', number=1)
