'''

Constants used by the score model

'''

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
IREGION_MEASURE_CONCEPT = "measure-region"
IREGION_NOTE_CONCEPT = "note-region"

# Concepts for the AUDIO_TIME_FRAME annotation
TFRAME_MEASURE_CONCEPT = "measure-tframe"
TFRAME_NOTE_CONCEPT = "note-tframe"

# Concepts for the AM_XML_FRAGMENT annotation
XML_MEASURE_CONCEPT = "measure-xml"
XML_NOTE_CONCEPT = "note-xml"

# Concepts for the AM_OMR_ERROR annotation
OMR_ERROR_UNKNOWN_SYMBOL = "unknown_symbol"
OMR_ERROR_INCONSISTENT_NOTATION = "inconsistent_notation"