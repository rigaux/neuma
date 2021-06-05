echo
echo ==== XSLT script to convert MusicXML to MEI for Opus {opus_ref}
set CLASSPATH={saxon_path}\saxon9.jar
rm {tmp_dir}\mei.xml {tmp_dir}\tmp-score.xml
java net.sf.saxon.Transform -versionmsg:off  -s:{tmp_dir}\score.xml -xsl:{xsl_path}\partime.xsl -o:{tmp_dir}\tmp-score.xml
java net.sf.saxon.Transform -versionmsg:off  -s:{tmp_dir}\tmp-score.xml -xsl:{xsl_path}\musicxml2mei-3.0.xsl -o:{tmp_dir}\mei.xml