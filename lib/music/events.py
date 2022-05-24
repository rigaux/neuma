
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

class Event:
	'''
		Super-class for anything (note, rest, chord) that occurs for a given duration
	'''
	
	# A counter for all events
	counter_event = 1

	def __init__(self, duration) :
		self.m21_event = None 

	def is_note(self):
		return False

class Note (Event):
	"""
		Representation of a note
	"""

	DMOS_FLAT_SYMBOL="bemol"
	DMOS_SHARP_SYMBOL="diese"
	
	UNDEFINED_STAFF = 0
	
	ALTER_FLAT = "-"
	ALTER_SHARP = "#"
	ALTER_NATURAL = "n"
	ALTER_NONE = ""
		
	def __init__(self, pitch_class, octave, duration,  alter=ALTER_NONE,
				no_staff=UNDEFINED_STAFF, tied=False) :
		
		self.alter = alter
		self.pitch_class = pitch_class

		pitch_name = pitch_class + alter + str(octave)
		self.alter = alter
		self.m21_event = m21.note.Note(pitch_name)
		self.m21_event.duration = duration.m21_duration
		self.m21_event.id = f'n{Event.counter_event}'
		Event.counter_event += 1
		self.no_staff = no_staff
		self.tied = tied
		return
	
	def is_note(self):
		return True
	def get_no_staff(self):
		return self.no_staff
	def get_alter(self):
		return self.alter
	def get_pitch_class(self):
		return self.pitch_class


class Rest (Event):
	"""
		Representation of a rest
	"""
	
	def __init__(self,  duration, no_staff) :
		
		self.m21_event = m21.note.Rest()
		self.m21_event.duration = duration.m21_duration
		self.m21_event.id = f'r{Event.counter_event}'
		Event.counter_event += 1
		self.no_staff = no_staff
		return
	
	def is_note(self):
		return False
	def get_no_staff(self):
		return self.no_staff
