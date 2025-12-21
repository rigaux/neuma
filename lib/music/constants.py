'''

Constants used by the score model

'''


"""
Separators
"""
NEUMA_SEPARATOR = ":"
# The following is use to combine several ids in a single xml:id field
# The double dass seems to be the only accepted symbol that survives through successive conversions...
ID_SEPARATOR = "--"

"""
 For annotations
 """
 
# List of annotation models
AM_TEXTUAL = "textual"
AM_QUALITY = "quality"
AM_IMAGE_REGION = "image-region"
AM_AUDIO_TIME_FRAME = "time-frame"
AM_XML_FRAGMENT = "xml-fragment"
AM_OMR_ERROR = "omr-error"

# Concepts for the IMAGE_REGION annotation
IREGION_SYSTEM_CONCEPT = "system-region"
IREGION_MEASURE_CONCEPT = "measure-region"
IREGION_STAFF_CONCEPT = "staff-region"
IREGION_MEASURE_STAFF_CONCEPT = "mstaff-region"
IREGION_NOTE_CONCEPT = "note-region"
IREGION_SYMBOL_CONCEPT = "symbol-region"

# Concepts for the AUDIO_TIME_FRAME annotation
TFRAME_MEASURE_CONCEPT = "measure-tframe"
TFRAME_NOTE_CONCEPT = "note-tframe"

# Concepts for the AM_XML_FRAGMENT annotation
XML_MEASURE_CONCEPT = "measure-xml"
XML_NOTE_CONCEPT = "note-xml"

# Concepts for the AM_OMR_ERROR annotation
OMR_LOW_DURATION = "lowDurErr"
OMR_HIGH_DURATION = "supDurErr"
OMR_VOICE_DURATION = "durationErr"
OMR_LOW_CONFIDENCE = "lowConfidenceErr"
OMR_TSIGN_INCONSISTENCY = "timeInconsistencySystemErr"
OMR_KSIGN_INCONSISTENCY = "keyInconsistencySystemErr"
OMR_ADDED_ELEMENT = "addElmt"
OMR_ADDED_SKIP = "addSkip"
LIST_OMR_ERRORS = {
	OMR_LOW_DURATION: "L'élément de voix reconnu semble trop court", 
	OMR_HIGH_DURATION: "L'élément de voix reconnu semble trop long", 
	OMR_LOW_CONFIDENCE: "Le symbole a été détecté avec un faible score de confiance",
	OMR_TSIGN_INCONSISTENCY: "La signature temporelle est incohérente sur l'ensemble des portées du système",
	OMR_KSIGN_INCONSISTENCY: "L'armure est incohérente sur l'ensemble des portées du système",
	OMR_VOICE_DURATION: "Vérifier la durée de la voix",
	OMR_ADDED_ELEMENT: "Un élément a été ajouté bien que la mesure soit trop longue.",
	OMR_ADDED_SKIP: "Un silence invisible a été ajouté.",
}


# Colors
	

COLOR_VOICE1 = "#13819E"
COLOR_VOICE2  = "#a637b0"
COLOR_VOICE3  = "#5034D4"
COLOR_VOICE4  = "#0a6206"
COLOR_VOICE5 = "black"

# For coloring notes in error
INDEX_ERROR_COLOR= 8

COLORS=[COLOR_VOICE1, COLOR_VOICE2, COLOR_VOICE3, COLOR_VOICE4,  COLOR_VOICE5]

# List of allowed meta keys, 
MK_COLLECTION = "collection"
MK_OFFICE = "office"
MK_FETE = "fete"
MK_MODE = "mode"
MK_GENRE = "genre"
MK_YEAR = "year"
MK_SOLENNITE = "solennite"
MK_TEXTE = "texte"
MK_KEY_TONIC = "key_tonic_name"
MK_KEY_MODE = "key_mode"
MK_METER = "meter"	
MK_NUM_OF_PARTS = "num_of_parts"
MK_NUM_OF_MEASURES = "num_of_measures"
MK_NUM_OF_NOTES = "num_of_notes"
ML_INSTRUMENTS = "instruments"
MK_LOWEST_PITCH_EACH_PART = "lowest_pitch_each_part"
MK_HIGHEST_PITCH_EACH_PART = "highest_pitch_each_part"
MK_MOST_COMMON_PITCHES = "most_common_pitches"
MK_AVE_MELODIC_INTERVAL = "average_melodic_interval"
MK_DIRECTION_OF_MOTION = "direction_of_motion"
MK_MOST_COMMON_NOTE_QUARTER_LENGTH = "most_common_note_quarter_length"
MK_RANGE_NOTE_QUARTER_LENGTH = "range_note_quarter_length"
MK_INIT_TIME_SIG = "initial_time_signature"

# Descriptive infos for meta pairs
META_KEYS = {
		MK_COLLECTION: {"displayed_label": "Collection"},
		MK_OFFICE: {"displayed_label": "Office"},
		MK_FETE: {"displayed_label": "Fête"},
		MK_MODE: {"displayed_label": "Mode"},
		MK_GENRE: {"displayed_label": "Genre"},
		MK_SOLENNITE: {"displayed_label": "Degré de solennité"},
		MK_TEXTE: {"displayed_label": "Texte"},
		MK_KEY_TONIC: {"displayed_label": "Key Tonic Name"},
		MK_KEY_MODE: {"displayed_label":"Key Mode"},
		MK_METER: {"displayed_label":"Meter"},
		MK_YEAR: {"displayed_label":"Year"},
		MK_NUM_OF_PARTS: {"displayed_label": "Number of parts"},
		MK_NUM_OF_MEASURES: {"displayed_label": "Number of measures"},
		MK_NUM_OF_NOTES: {"displayed_label": "Number of notes"},
		ML_INSTRUMENTS: {"displayed_label": "Instruments"},
		MK_LOWEST_PITCH_EACH_PART: {"displayed_label": "Lowest fpitch each part"},
		MK_HIGHEST_PITCH_EACH_PART: {"displayed_label": "Highest pitch each part"},
		MK_MOST_COMMON_PITCHES: {"displayed_label": "Most common pitches"},
		MK_AVE_MELODIC_INTERVAL: {"displayed_label": "Average melodic interval"},
		MK_DIRECTION_OF_MOTION: {"displayed_label": "Direction of motion"},
		MK_MOST_COMMON_NOTE_QUARTER_LENGTH: {"displayed_label": "Most common note quarter length"},
		MK_RANGE_NOTE_QUARTER_LENGTH: {"displayed_label": "Range of note quarter length"},
		MK_INIT_TIME_SIG:{"displayed_label": "Initial time signature"}
	}
