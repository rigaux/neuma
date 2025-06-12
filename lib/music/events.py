
import music21 as m21

from fractions import Fraction
import lib.music.notation as score_notation
import lib.music.constants as score_constants
import lib.music.Score as score_mod

# for XML editions
from lxml import etree

'''
 Classes representing musical event (e.g., pairs (duratioin, value)
'''

class Duration:
	'''
		A duration is a fraction of a quarter note
	'''
	
	def __init__(self, numer, denom, whole=False) :
		self.fraction = Fraction (numer, denom)
		
		# m21 duration is the float obtained from the fraction
		if not whole:
			self.m21_duration = m21.duration.Duration(self.fraction)
		else:
			dur = m21.duration.convertTypeToQuarterLength("whole", dots=1)
			self.m21_duration = m21.duration.Duration(dur)

	def get_value(self):
		return self.m21_duration.quarterLength
	
	def __repr__(self):
		return f'Duration({self.m21_duration.quarterLength})'

class Event:
	'''
		Super-class for anything (note, rest, chord, clef) that occurs 
		at a given position in a voice
	'''
	
	TYPE_CHORD = "chord"
	TYPE_CLEF = "clef"
	TYPE_NOTE = "note"
	TYPE_REST = "rest"
	
	# A counter for all events. It consists of i) a global part representing the context
	# (ie, a measure in a part), and ii) a local counter for events met in this context
	counter_context = ""
	counter_event = 0

	@staticmethod 
	def reset_counter(new_context):
		# Initializes the local counter for a new context
		Event.counter_context = new_context
		Event.counter_event = 0
		
	def __init__(self, duration, tied=False, id=None, voice=None) :
		if id is None:
			Event.counter_event += 1
			self.id = f'{Event.counter_context}E{Event.counter_event}'
		else:
			self.id = id
			
		self.duration = duration
		self.m21_event = None 
		self.type = Event.TYPE_NOTE
		self.beam = None  
		# Mostly used for hidden rests 
		self.visible = True
		self.no_staff = None

		# Tie information, applies to notes and chords
		self.tied = tied
		self.tie_type = None
		self.id_tie = None
		
		# A "decoration" is any object that can be inserted 
		# in the music flow, at a position relative to the event
		self.decorations = []
		
		# An event belongs to a voice
		self.voice = voice
		
	def is_note(self):
		return False
	def is_rest(self):
		return False
	def is_chord(self):
		return False
	
	def get_duration(self):
		return self.duration.get_value()
	
	@staticmethod
	def get_musicxml_duration(quarter_length, divisions):
		# Concert a Music21 quarter length value to a music XML duration
		return int(quarter_length * divisions)
	
	def set_visibility(self, visibility):
		self.visible = visibility
		if visibility == False:
			self.m21_event.style.hideObjectOnPrint = True 
		else:
			self.m21_event.style.hideObjectOnPrint = False 
			
	def add_articulation (self, art):
		self.m21_event.articulations.append(art.m21_articulation)

	def add_expression (self, expr):
		self.m21_event.expressions.append(expr.m21_expression)

	def start_beam(self, beam_id=1):
		if not self.is_rest():
			#score_mod.logger.info (f"Start a beam : {beam_id}" )
			self.beam = score_notation.Beam()
			self.m21_event.beams.append(self.beam.m21_beam)
		else:
			score_mod.logger.warning (f"Trying to start a beam ({beam_id}) on a rest for event {self.id}")
	def continue_beam(self, beam_id=1):
		if not self.is_rest():
			#score_mod.logger.info (f"Continue a beam : {beam_id}" )
			self.beam = score_notation.Beam("continue")
			#self.m21_event.beams.append("continue")
			self.m21_event.beams.append(self.beam.m21_beam)
		else:
			score_mod.logger.warning (f"Trying to continue a beam ({beam_id}) on a rest for event {self.id}")
	def stop_beam(self, beam_id=1):
		if not self.is_rest():
			#score_mod.logger.info (f"Stop a beam : {beam_id}" )
			self.beam = score_notation.Beam("stop")
			#self.m21_event.beams.append("stop")
			self.m21_event.beams.append(self.beam.m21_beam)
		else:
			score_mod.logger.warning (f"Trying to stop a beam ({beam_id}) on a rest")

	def id(self):
		return self.m21_event.id
	
	def add_decoration(self, decoration):
		self.decorations.append(decoration)

	def set_color(self, i_color):
		# Find the color in the palette
		if i_color < 0 or i_color >= len(score_constants.COLORS):
			score_mod.logger.warning (f"Color index {i_color} is  beyond range. Ignored.")
			return 
		else:
			
			#print (f"Using color {i_color}")
			self.m21_event.style.color = score_constants.COLORS[i_color]
		
	def to_musicxml(self, divisions):
		el = etree.Element('void')
		return [el]

	def __str__(self):
		return f"Event {self.id}. Duration {self.duration}"
	
class Articulation ():
	"""
		Articulation = some performance indication attached to a note
	"""
	
	STACCATO = "staccato"
	ACCENT = "accent"
	TENUTO="tenuto"
	STRONG_ACCENT="strong-accent"
	CODA="coda"
	SEGNO="segno"
	MARCATO = "marcato"
	
	def __init__(self, placement, art_type) :
		if art_type == Articulation.STACCATO:
			self.m21_articulation = m21.articulations.Staccato()
		elif art_type == Articulation.ACCENT:
			self.m21_articulation = m21.articulations.Accent()
		elif art_type == Articulation.TENUTO:
			self.m21_articulation = m21.articulations.Tenuto()
		elif art_type == Articulation.STRONG_ACCENT:
			self.m21_articulation = m21.articulations.StrongAccent()
		elif art_type == Articulation.MARCATO:
			# Does seem to exist as such in Music21... Using 'accent' instead
			self.m21_articulation = m21.articulations.Accent()
		else:
			raise score_mod.CScoreModelError (f"Unknown articulation type: '{art_type}'")

		self.m21_articulation.placement = placement
		return

class Expression ():
	"""
		Expression = a directive attached to a note
	"""
	
	FERMATA="fermata"
	TRILL="trill"
	ARPEGGIO="arpeggio"
	
	def __init__(self, placement, expr_type) :
		if  expr_type == Expression.FERMATA:
			self.m21_expression = m21.expressions.Fermata()
		elif  expr_type == Expression.TRILL:
			self.m21_expression = m21.expressions.Trill()
		elif  expr_type == Expression.ARPEGGIO:
			self.m21_expression = m21.expressions.ArpeggioMark('normal')
			#self.m21_expression = m21.expressions.Trill()
		else:
			raise score_mod.CScoreModelError (f"Unknown expression type: '{expr_type}'")

		self.m21_expression.placement = placement
		return

class Note (Event):
	"""
		Representation of a note
	"""
	UNDEFINED_STAFF = 0
	
	ALTER_FLAT = "-"
	ALTER_DOUBLE_FLAT = "--"
	ALTER_SHARP = "#"
	ALTER_DOUBLE_SHARP = "##"	
	ALTER_NATURAL = "n"
	ALTER_NONE = ""
		
	# Stem directions (uses music21 codes)
	SD_UNSPECIFIED = "unspecified"
	SD_UP = "up"
	SD_DOWN = "down"
	
	def __init__(self, pitch_class, octave, duration,  alter=ALTER_NONE,
				no_staff=UNDEFINED_STAFF, tied=False, 
				stem_direction=None,
				note_type=None, 
				id=None,
				voice=None):
		super ().__init__(duration, tied, id, voice)
		
		self.type = Event.TYPE_NOTE
		self.alter = alter
		self.pitch_class = pitch_class
		self.octave = octave
		self.pitch_name = pitch_class + alter + str(octave)
		self.alter = alter
		self.m21_event = m21.note.Note(self.pitch_name)
		self.m21_event.duration = duration.m21_duration
		self.m21_event.id = self.id
		self.no_staff = no_staff
		self.stem_direction = stem_direction
		if note_type=="quaver":
			# Caution
			note_type="eighth"
		self.note_type=note_type
		
		self.syllable = None 
		
		if stem_direction != None:
			self.m21_event.stemDirection = stem_direction
			
		return
	
	def get_code(self):
		return self.pitch_class + self.alter + str(self.octave) 
	def is_note(self):
		return True
	def get_no_staff(self):
		return self.no_staff
	def get_alter(self):
		return self.alter
	def get_pitch_class(self):
		return self.pitch_class
		
	def same_pitch(self, note):
		
		if not (note.is_note()):
			# Cannot compare
			return False
		if self.pitch_class==note.pitch_class and self.octave==note.octave and self.alter==note.alter:
			return True
		else:
			return False
		
	def start_tie(self, id_tie):
		self.tied = True
		self.tie_type = "start"
		self.id_tie = id_tie
		self.m21_event.tie = m21.tie.Tie('start')
	def stop_tie(self, id_tie):
		self.tied = True
		self.tie_type = "stop"
		self.id_tie = id_tie
		self.m21_event.tie = m21.tie.Tie('stop')
	
	def add_syllable(self, txt, nb=1, dashed=False):
		if dashed:
			txt = txt + "-"
		lyric = m21.note.Lyric(text=txt,number=nb)
		self.m21_event.lyrics.append(lyric)
		
	def to_musicxml(self,divisions=10080):
		el = etree.Element('note')
		el.set("id", self.id)
		pitch = etree.SubElement(el, 'pitch')
		step = etree.SubElement(pitch, 'step')
		step.text = str(self.pitch_class)
		octave = etree.SubElement(pitch, 'octave')
		octave.text = str(self.octave)
		if self.voice is not None:
			voice = etree.SubElement(el, 'voice')
			voice.text = str(self.voice.id)
			if int(self.voice.id) < len(score_constants.COLORS):
				el.set("color", score_constants.COLORS[int(self.voice.id)])
			else:
				score_mod.logger.warning (f"Voice id {self.voice.id} is beyond the maximal color index. Unable to color." )
			#el.set("color", score_constants.COLORS[score_constants.INDEX_ERROR_COLOR])
		duration = etree.SubElement(el, 'duration')
		duration.text= str(Event.get_musicxml_duration(self.duration.get_value(), divisions))
		staff = etree.SubElement(el, 'staff')
		staff.text = str(self.no_staff)
		stem = etree.SubElement(el, 'stem')
		stem.text = str(self.stem_direction)
		note_type = etree.SubElement(el, 'type')
		note_type.text = str(self.note_type)
		if self.tied:
			tie = etree.SubElement(el, 'tie')
			tie.set("type", str(self.tie_type))
		if self.beam:
			beam = etree.SubElement(el, 'beam')
			beam.set("number", str(self.beam.number))
			if self.beam.beam_type == score_notation.Beam.START_BEAM:
				beam.text = "begin"
			elif self.beam.beam_type == score_notation.Beam.CONTINUE_BEAM:
				beam.text = "continue"
			elif self.beam.beam_type == score_notation.Beam.STOP_BEAM:
				beam.text = "end"
			
		return [el]
		
	def __str__(self):
		return f"Note {self.id}. {self.pitch_class}{self.octave}{self.alter}-{self.duration}"

class Chord (Event):
	"""
		Representation of a chord = a list of notes
	"""
	
	def __init__(self,  duration, no_staff, notes, id=None, voice=None) :
		super ().__init__(duration, tied=False, id=id,voice=voice)
		self.type = Event.TYPE_CHORD
		self.notes = notes
		# Create the m21 representation: encode 
		m21_notes = []
		for note in notes:
			if isinstance(note, Note):
				m21_notes.append (note.m21_event)
				
				# If at least one note is tied, the chord is candidate for being tied
				if note.tied:
					self.tied = True
					self.tie_type = note.tie_type
					
		self.m21_event = m21.chord.Chord(m21_notes)
		
		if self.tied:
			if self.tie_type == "start":
				self.m21_event.tie = m21.tie.Tie('start')
			else:
				self.m21_event.tie = m21.tie.Tie('stop')

		self.m21_event.duration = duration.m21_duration
		self.m21_event.id = self.id

		Event.counter_event += 1
		self.no_staff = no_staff
		return
	
	def is_note(self):
		return False
	def is_chord(self):
		return True
	def get_no_staff(self):
		return self.no_staff
	def set_color(self, i_color):
		for note in self.notes:
			note.set_color(i_color)
	def contains_pitch (self, pitch):
		# Param pitch is a note instance: we test if the pitch is in the chord
		for n in self.notes:
			if n.same_pitch(pitch):
				return True
		return False
		
	def same_pitch(self, chord):
		if not (chord.is_chord()):
			# Cannot compare
			return False

		# Check if two chords contain exactly the same pitches
		if len(self.notes) != len(chord.notes):
			return False
		for n in self.notes: 
			if not (chord.contains_pitch(n)):
				return False 
		return True
				
	def to_musicxml(self,divisions):
		i_note = 1
		els = []
		for note in self.notes:
			el = note.to_musicxml()[0]
			if i_note > 1:
				etree.SubElement(el, 'chord')
			i_note += 1
			els.append(el)
		return els

	def __str__(self):
		note_list = ""
		for note in self.notes:
			note_list += f"{note.pitch_class}{note.octave}{note.alter} "
		return f"Chord {self.id}. [{note_list}]-{self.duration}"

class Rest (Event):
	"""
		Representation of a rest
	"""
	
	def __init__(self,  duration, no_staff, id=None, voice=None) :
		super ().__init__(duration, tied=False, id=None, voice=voice)
		self.type = Event.TYPE_REST

		self.m21_event = m21.note.Rest()
		self.m21_event.duration = duration.m21_duration
		self.m21_event.id = self.id
		Event.counter_event += 1
		self.no_staff = no_staff
		return
	
	def is_note(self):
		return False
	def is_rest(self):
		return True
	def get_no_staff(self):
		return self.no_staff
	def get_code(self):
		return f"Rest {self.m21_event.duration.quarterLength}" 
	
	def to_musicxml(self,divisions):
		el = etree.Element('note')
		el.set("id", self.id)
		etree.SubElement(el, 'rest')
		duration = etree.SubElement(el, 'duration')
		duration.text= str(Event.get_musicxml_duration(self.duration.get_value(), divisions))
		staff = etree.SubElement(el, 'staff')
		staff.text = str(self.no_staff)
		if self.voice is not None:
			voice = etree.SubElement(el, 'voice')
			voice.text = str(self.voice.id)
			if int(self.voice.id) < len(score_constants.COLORS):
				el.set("color", score_constants.COLORS[int(self.voice.id)])
			else:
				score_mod.logger.warning (f"Voice id {self.voice.id} is beyond the maximal color index. Unable to color." )

			#el.set("color", score_constants.COLORS[score_constants.INDEX_ERROR_COLOR])

		return [el]

	def __str__(self):
		return f"Rest {self.id}-{self.duration}"


class Decoration():
	""" 
		A "decoration" is any object that can be inserted 
		in the music flow, at a position relative to the event
	"""
	def __init__(self, relative_pos=0) :
		self.m21_object = None
		self.relative_position = relative_pos


class Dynamics (Decoration):
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
		super ().__init__(0)

		if dyn_type == Dynamics.PIANO:
			self.m21_object = m21.dynamics.Dynamic('p')
		elif dyn_type == Dynamics.PIANISSIMO:
			self.m21_object = m21.dynamics.Dynamic('pp')
		elif dyn_type == Dynamics.FORTE:
			self.m21_object = m21.dynamics.Dynamic('f')
		elif dyn_type == Dynamics.FORTISSIMO:
			self.m21_object = m21.dynamics.Dynamic('ff')
		elif dyn_type == Dynamics.MEZZOPIANO:
			self.m21_object = m21.dynamics.Dynamic('mp')
		elif dyn_type == Dynamics.MEZZOFORTE:
			self.m21_object = m21.dynamics.Dynamic('mf')
		else:
			raise score_mod.CScoreModelError (f"Unknown dynamics type: '{dyn_type}'")

		self.m21_object.placement = placement
		
		return
