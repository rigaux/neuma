#!/bin/bash
#
# Something specific to Mac OS X. Do not ask why
unset DYLD_LIBRARY_PATH;

echo 
echo ==== XSLT script to convert MusicXML to MEI for Opus {opus_ref}

# Set the claspath
export CLASSPATH=$CLASSPATH:{saxon_path}/saxon9.jar

# Clean 
rm {tmp_dir}/mei.xml {tmp_dir}/tmp-score.xml

# Transform MusicXML to partime 
java net.sf.saxon.Transform -versionmsg:off  -s:{tmp_dir}/score.xml -xsl:{xsl_path}/partime.xsl -o:{tmp_dir}/tmp-score.xml 

# Transform to MEI
java net.sf.saxon.Transform -versionmsg:off  -s:{tmp_dir}/tmp-score.xml -xsl:{xsl_path}/musicxml2mei-3.0.xsl -o:{tmp_dir}/mei.xml