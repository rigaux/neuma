'''

Constants used by the score model

'''

"""
 For annotations
 """
 
# List of annotation models
AM_TEXTUAL = "textual"
AM_QUALITY = "quality"
AM_COUTERPOINT = "counterpoint"
AM_IMAGE_REGION = "region"
AM_AUDIO_INTERVAL = "interval"
AM_OMR_ERROR = "omr_error"

# Concepts for the IMAGE_REGION annotation
IREGION_MEASURE_CONCEPT = "measure_region"
IREGION_NOTE_CONCEPT = "note_region"

# Concepts for the INTERVAL annotation
INTERVAL_MEASURE_CONCEPT = "measure_interval"
INTERVAL_NOTE_CONCEPT = "note_interval"
INTERVAL_GENERIC_CONCEPT = "generic_interval"

# Concepts for the AM_OMR_ERROR annotation
OMR_ERROR_UNKNOWN_SYMBOL = "unknown_symbol"
OMR_ERROR_INCONSISTENT_NOTATION = "inconsistent_notation"