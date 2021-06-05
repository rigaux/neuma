 
 
 
''' imports '''
from music21 import corpus, converter
import reduction, vectors, dissonance, harmonicWindow
import logging
 
 

if __name__ == '__main__': pass  
 
''' configure logging '''
logging.basicConfig(level=logging.INFO)
 

''' get file '''
#work = converter.parse('/Users/Christophe/Desktop/Emergence_2016/Exemples_musicaux/tests/Corelli_Sonata6.xml') 
#work = corpus.parse('bwv380') 
#work = converter.parse('/Users/Christophe/Desktop/Emergence_2016/Exemples_musicaux/NEUMA_Requiem/Brumel_missa.xml') 
work = converter.parse('/Users/Christophe/Desktop/Emergence_2016/Exemples_musicaux/tests/corelli_3_1/corelli_3_1_2.mei') 
#work = corpus.parse('1grave')



''' create reduction object to remove repetitions ''' 
reductionObject = reduction.Reduction(work)
reductionObject.removeRepetitions()

''' contrapuntal analysis '''
ctpAnalysis = dissonance.ChordAnalysis(reductionObject.getLayer()) 

#harmonicAnalysis = harmonicWindow.ChordAnalysis(ctpAnalysis)



''' @ Philippe: get analyzed pitches : a list of analyzed pitch objects containing id, type, subtype etc. etc.  (returns object AnalyzedPitch)''' 

analyzedPitchList = ctpAnalysis.getAnalyzedPitches()

''' simple statistics '''
ctpAnalysis.showStatistics()

''' get fundamental bass stream'''
#fbStream = ctpAnalysis.getFundamentalBass()

''' simple vector analysis'''
#vectorAnalysis = vectors.VectorAnalysis(fbStream)
#vectorAnalysis.show('simpleGraph')
#vectorAnalysis.show('tonalProfile')

## get analysis for  

''' get annotated stream and insert fundamental bass '''
stream = ctpAnalysis.getAnnotatedStream()
#stream.insert (0, ctpAnalysis.getFundamentalBass()) 

''' display the whole thing'''
stream.show()