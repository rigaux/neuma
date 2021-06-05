
# List of analytic models
AMODEL_COUNTERPOINT="counterpoint"
AMODEL_QUALITY="quality"
AMODEL_COMPARISON="comparison"
ANALYTIC_MODELS = [{"code": AMODEL_COUNTERPOINT, "name": "Renaissance counterpoint", 
                       "description": "By Christophe Guillotel-Nothmann"},
                   {"code": AMODEL_QUALITY, "name": "Notation quality", 
                       "description": "GioQoSo project"},
                   ]

# List of Counterpoint analytic concepts
AC_DISSONANCE="dissonance"
AC_SUSPENSION="suspension"
AC_ANTICIPATION="anticipation"
AC_PASSING_NOTE="passingnote"
AC_NEIGHBOR_NOTE="neighbornote"
AC_ESCAPE_NOTE="escapenote"
AC_CONSONANCE="consonance"

# List of quality analytic concepts
AC_QUAL_LYRICS_ISSUES="lyricsissues"
AC_QUAL_METADATA_ISSUES="metadataissues"
AC_QUAL_LAYOUT_ISSUES="layoutissues"
AC_QUAL_MUSIC_ISSUES="musicissues"
AC_QUAL_CORRECTNESS_ISSUES="correctnessissues"

#
# Metadata
#
AC_QUAL_MISSING_TITLE="missingtitle"
AC_QUAL_MISSING_COMPOSER="missingcomposer"
AC_QUAL_MISSING_LYRICIST="missinglyricist"
AC_QUAL_MISSING_OPUS_REF="missingopusref"
AC_QUAL_MISSING_EDITOR="missingeditor"
AC_QUAL_MISSING_COPYRIGHT="missingcopyright"
#
# Lyrics 
#
AC_QUAL_MISSING_LYRICS="missinglyrics"
AC_QUAL_INVALID_LYRICS="invalidlyrics"
AC_QUAL_INVALID_SYLLAB_METADATA="invalidsyllabmd"

#
# Notation correctness
#
AC_QUAL_INCOMPLETE_BARS="incompletebars"
AC_QUAL_PART_MISALIGNMENT="misalignedparts"
AC_QUAL_INCONSISTENT_VOICES="inconsistentvoices"
AC_QUAL_INCONSISTENT_SLURS="inconsistentslurs"
#
# Music issues
#
AC_QUAL_IRREGULAR_TIME_SIGNATURE="irregulartimesign"
AC_QUAL_IRREGULAR_KEY_SIGNATURE="irregularkeysign"
#
# Beaming Error
#
AC_QUAL_INVALID_BEAMING_SUBDIVISION="invalidbeamingsubdivision"
#
# Temporary for testing
# Comparison
#
AC_COMP_INSERTION="insertion"
AC_COMP_DELETION="deletion"
AC_COMP_MODIFICATION="modification"
AC_COMP_COST="comparison_cost"
AC_COMP_ANNOTATIONS = "comparison_annotations"