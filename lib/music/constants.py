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
OMR_ERROR_UNKNOWN_SYMBOL = "unknown-symbol"
OMR_ERROR_INCONSISTENT_NOTATION = "inconsistent-notation"