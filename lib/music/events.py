
import music21 as m21

from fractions import Fraction


'''
 Classes representing musical event (e.g., pairs (duratioin, value)
'''

class Duration:
	'''
		A duration is a fraction of a quarter note
	'''
	
	def __init__(self, numer, denom) :
		self.fraction = Fraction (numer, denom)
		
		# m21 duration is the float obtained from the fraction
		self.m21_duration = m21.duration.Duration(self.fraction)

class Note:
	"""
		Representation of a note
	"""

	DMOS_FLAT_SYMBOL="bémol"
	DMOS_SHARP_SYMBOL="dièse"
	
	UNDEFINED_STAFF = 0
	
	ALTER_FLAT = "-"
	ALTER_SHARP = "#"
	
	def __init__(self, pitch_class, octave, duration,  alter="",
				no_staff=UNDEFINED_STAFF, tied=False) :
		
		pitch_name = pitch_class + alter + str(octave)
		self.m21_note = m21.note.Note(pitch_name)
		self.m21_note.duration = duration.m21_duration
		
		self.no_staff = no_staff
		self.tied = tied
		return
