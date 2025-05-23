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
