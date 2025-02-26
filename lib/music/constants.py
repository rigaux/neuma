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
LIST_OMR_ERRORS = {
	OMR_LOW_DURATION: "L'élément de voix reconnu semble trop court", 
	OMR_HIGH_DURATION: "L'élément de voix reconnu semble trop long", 
	OMR_LOW_CONFIDENCE: "Le symbole a été détecté avec un faible score de confiance",
	OMR_TSIGN_INCONSISTENCY: "La signature temporelle est incohérente sur l'ensemble des portées du système",
	OMR_KSIGN_INCONSISTENCY: "L'armure est incohérente sur l'ensemble des portées du système",
	OMR_VOICE_DURATION: "Vérifier la durée de la voix"
}


# Colors

COLOR_BLUE = "#1f77b4"
COLOR_RED = "#FF0000"
COLOR_MAROON = "#800000"
COLOR_GREEN  = "#008000"
COLOR_PURPLE  = "#800080"
COLOR_ORANGE="#FF7F50"
COLOR_DARKRED="#7b241c"
COLOR_GOLD="#FFD700"
COLOR_PINK= "#FF1493"

# For coloring notes in error
INDEX_ERROR_COLOR= 8

COLORS=[COLOR_DARKRED, COLOR_BLUE, COLOR_GREEN, COLOR_MAROON, COLOR_ORANGE, COLOR_PURPLE, COLOR_DARKRED, COLOR_GOLD, COLOR_PINK]
