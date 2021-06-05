#!/bin/bash
#
# Something specific to Mac OS X. Do not ask why
unset DYLD_LIBRARY_PATH;

echo ==== Execute score compilation for Opus {opus_ref}

#
# Run Lilypond for the preview (no title, no header)
#
{lilydir}/lilypond -dpreview -o {tmpdir}/score {lilypreview_file} 

#
# Run Lilypond without the preview
#
# Note: the EPS backend ensures a one page with the whole score
#
{lilydir}/lilypond -dbackend=eps --formats=pdf,png -o {tmpdir}/score {lilypond_file}
