# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         chordAnalysis.py
# Purpose:      dissonance analysis
# 
#
# Copyright:    Christophe Guillotel-Nothmann Copyright © 2017
#-------------------------------------------------------------------------------
from music21.tree.spans import PitchedTimespan


''' imports '''
from music21 import tree, note, chord, stream, interval, clef, key
from .pitchCollections import H_AndNhnCollection, AnalyzedPitch
import lib.music.counterpoint.reduction
import copy, logging   

class ChordAnalysis(object):
    
    '''  identifies non harmonic and harmonic notes '''
    def __init__(self, work):
        ''' create stream and AVL tree '''
        from music21.tree.verticality import VerticalitySequence
        self.stream = work
        self.scoreTree = tree.fromStream.asTimespans(self.stream, flatten=True, classList=(note.Note, chord.Chord))
        self.explainedPitchCollectionList = []
        
        i = 0
        ''' loop through verticalities '''
        for verticality in self.scoreTree.iterateVerticalities():
    
            ''' explain verticality n '''
            i = i+1
            print ("Analyzing verticality " + str(verticality))
            logging.info ('Analyzing verticality at offset: ' + str(verticality.offset)) 
            explainedPitchCollection = self.explainVerticalitySequence(VerticalitySequence([verticality.previousVerticality, verticality, verticality.nextVerticality]))
            
            if explainedPitchCollection != None:
                logging.info ('...' + explainedPitchCollection.explainPitches()) 
                self.explainedPitchCollectionList.append(explainedPitchCollection)
                
                ''' infer knowledge from explained pitches '''
                self.inferKnowledgeFromExplainedPitches(explainedPitchCollection)
                
 
            ''' test hypotheses in hypothesis list '''
            hypothesisList = self.getHypotheses()
            
            for hypothesis in hypothesisList:  
                
                ''' slice to three verticalities and create sequence ''' 
                verticality2 = verticality
                verticality1 = hypothesis.verticalities[1]
                
                ''' TODO (?) loop backwards if irregular preparation (?) '''
                
                verticality0 = hypothesis.verticalities[0]
                verticalities = VerticalitySequence([verticality0, verticality1, verticality2])
                
                ''' check if timespan between verticality 0 and verticality 1 ; 
                   verticality 1 and verticality 2 can still be a prolongation '''
                if self.couldBeProlongation(verticalities):
                    explainedPitchCollection = self.explainVerticalitySequence(verticalities)
                    
                    if explainedPitchCollection != None:
                    
                        analyzedPitch = explainedPitchCollection.getAnalyzedPitch(hypothesis.pitch)
                        if analyzedPitch.pitchType == hypothesis.pitchType and analyzedPitch.certainty == 1:            
                            self.confirmHypothesis(hypothesis, analyzedPitch, True) 
                            logging.info ('... hypothesis confirmed: ' +  hypothesis.show())
                            
                            ''' test if additional knowledge can be inferred from hypothesis'''
                            self.inferKnowledgeFromHypothesis(hypothesis)
                #else:
                #    ''' validate implicit alternatives if any (resolutions before actual resolution)'''
                #    self.rejectHypothesis(hypothesis)           
         
                ''' check if analysis is consistent and if not correct incoherent labels '''
            
            
            #pitchCollection = self.getExplainedPitchCollectionAtOffset(verticality.offset)
            #pitchCollection.correctIncoherentPitches()
            		
            if i > 15: break
      
        hypothesisList = self.getHypotheses()
        for hypo in hypothesisList:
            logging.info (hypo)                     
        
    
    def confirmHypothesis (self, hypothesis, analyzedPitch, concurrentHypothesis = False):
        
        ''' get explainedPitchCollection '''
        explainedPitchCollection = self.getExplainedPitchCollectionAtOffset(hypothesis.verticalities[1].offset)
        
        ''' remove hypothesis '''
        explainedPitchCollection.confirmHypothesis(hypothesis, analyzedPitch, concurrentHypothesis)
    
    def couldBeProlongation(self, verticalities):
        
        '''TODO deduce harmonic rhyhtm from time signature and harmonic rhyhtm '''
        harmonicRhythm = 1 
        
        ''' distance between v2 and v1 '''
        probableHarmonicRhythm = False         
        if (verticalities[2].offset - verticalities[1].offset)  <= harmonicRhythm *4:
            probableHarmonicRhythm = True
            
        ''' TODO take into account metrical positions of prolongation '''
        
        if probableHarmonicRhythm == True:
            return True
        
        else:
            return False
    
    def explainVerticalitySequence(self, verticalities):         
        if verticalities[1].offset == 56:
            print ('')
        
        pitchAnalysisList = []
      
        isAccentuated = self._isAccentuated(verticalities, 1) 
        
        
        ''' durations '''
        if verticalities[0] != None and verticalities [1] != None: 
            v0v1Duration = verticalities[1].offset-verticalities[0].offset
        else:
            v0v1Duration = 0
        if verticalities[1] != None and verticalities [2] != None: 
            v1v2Duration = verticalities[2].offset-verticalities[1].offset
        else:
            v1v2Duration = 0
            
        if verticalities [2] != None and verticalities [2].nextVerticality != None:
            v2v3Duration = verticalities[2].nextVerticality.offset-verticalities[2].offset
        else:
            v2v3Duration = 0
        
        ''' loop over pitches '''
        for pitchV in verticalities[1].pitchSet:      
            pitchIsDissonant = self._pitchIsDissonantAgainstAtLeastOnePitch(verticalities[1], pitchV)
            
            if pitchIsDissonant == False:
                pitchAnalysisList.append(AnalyzedPitch(None, verticalities, isAccentuated, pitch = pitchV, pitchType='CN', certainty=1))
                
            else:  
                ''' analyze pitch, identify dissonance type or make hypothesis about what it could be ''' 
                melodicStream = self._getMelStreams(verticalities, pitchV)
                melodicMovementsList = self._getMelMovementsList(melodicStream)
                horizontalityList = self._getHorizontalityList(melodicStream)
                
                ''' TODO: if melodicMovementsList and horizontalityList have more than one entry, loop over all entries '''
                onePitchClassRemainsV0V1 = self._atLeastOnePitchClassIsCommon(verticalities[0], verticalities[1]) # no filter pitch needed here
                onePitchClassRemainsV1V2 = self._atLeastOnePitchClassIsCommon(verticalities[1], verticalities[2], [pitchV])
                
                onePitchNotParsimoniousV0V1 = self._atLeastOnePitchisNotParsimonious(verticalities[0], verticalities[1], [pitchV]) 
                
                pitchType, pitchSubType, certainty = self._pitchAnalysis(pitchV, isAccentuated, melodicMovementsList, onePitchClassRemainsV0V1, onePitchClassRemainsV1V2, onePitchNotParsimoniousV0V1, v0v1Duration, v1v2Duration, v2v3Duration)    
                pitchAnalysisList.append(AnalyzedPitch(horizontalityList[0], verticalities, isAccentuated, pitchV, pitchType, pitchSubType, certainty)) 
                
        analyzedVerticality = H_AndNhnCollection(verticalities[1], pitchAnalysisList)

        return analyzedVerticality       
    
    def getAnalysis(self, verticality):
        for analyzedVerticality in self.analyzedVerticalitiesList:
            if analyzedVerticality.verticality == verticality:
                return analyzedVerticality
        
        return None   
    
    
    def getAnnotatedStream(self):
        ''' remove all lyrics '''
        for verticality in  self.scoreTree.iterateVerticalities():
            for element in verticality.startTimespans:
                if isinstance(element.element, note.Note) or isinstance(element.element, chord.Chord):
                    element.element.lyric = None
        
        
        ''' loop through nhn collection list '''
        for explainedPitchCollection in self.explainedPitchCollectionList: 
            verticality = explainedPitchCollection.verticality
            
            
            for analyzedPitch in explainedPitchCollection.analyzedPitchList:
                elementList = self._getElementsContainingPitch(verticality, analyzedPitch.pitch)
                
                for element in elementList:
           
                    
                    if analyzedPitch.pitchType == None:
                        pitchType =  "*"
                    else:
                        pitchType = str(analyzedPitch.pitchType)
                        
                        
                        
                
                    if element.lyric == None:
                            element.lyric =  pitchType
                    elif pitchType in element.lyric:
                        pass
                    
                    else:   
                        element.lyric = str (element.lyric) + pitchType
                
    
        return tree.toStream.partwise(self.scoreTree, templateStream=self.stream)
    
    def getDissonancesAtOffset (self, offset):
        ''' returns identified dissonances starting before current offset and resolving after this offset '''
        analyzedDissonancesList = []
        
        for pitchCollection in self.explainedPitchCollectionList:
            
            ''' break if collection offset > as current offset ''' 
            if pitchCollection.verticality.offset > offset:
                break
            
            ''' check if collection has dissonances resolving after current offset '''
            if pitchCollection.getHighestResolutionOffest() > offset:
                
                for analyzedPitch in pitchCollection.getExplainedPitches(['PN', 'NN', 'AN', 'EN', 'SU']):
                    if analyzedPitch.resolutionOffset != None:
                        analyzedDissonancesList.append(analyzedPitch)
        return analyzedDissonancesList 
    
    
    def getExplainedPitchCollectionAtOffset (self, offset):
        for explainedPitchCollection in self.explainedPitchCollectionList:
            if explainedPitchCollection.verticality.offset == offset:
                return explainedPitchCollection 
            
        return None
    
    def getExplainedPitchesAtOffset (self, offset):
        ''' get pitch collection '''
        pitchCollection = self.getExplainedPitchCollectionAtOffset(offset)
                
        ''' get explained pitches '''   
        pitchList = pitchCollection.analyzedPitchList
        return pitchList
    
    
    def getAnalyzedPitches(self, elementID = None, offset = None):
        if elementID != None:
            return self.getAnalzedPitchCorrespondingToId(elementID)
        elif offset != None:
            return self.getExplainedPitchesAtOffset(offset)
            
        else:
            analyzedPitchList = []
            
            for analyzedPitchCollection in self.explainedPitchCollectionList:
                analyzedPitchList = analyzedPitchList + analyzedPitchCollection.analyzedPitchList
        
        return analyzedPitchList
            
    
    def getAnalzedPitchCorrespondingToId (self, elementID):
        for analyzedPitchCollection in self.explainedPitchCollectionList:
            if analyzedPitchCollection.getAnalyzedPitchesCorrespondingToId(elementID) != None:
                return analyzedPitchCollection
        return analyzedPitchCollection
    
    
    def getExplainedPitchCollectionBeforeOffset (self, offset):
        ''' get index number of explained collection'''
        
        for x in range (0, len (self.explainedPitchCollectionList)):
            if self.explainedPitchCollectionList[x].verticality.offset == offset:
                if x > 0: return self.explainedPitchCollectionList[x-1]
        
        return None
    
    def getFundamentalBass (self):
        ''' create stream  with part for FB'''     
        chordifiedStream =  self.stream.chordify() 
      
        fbStream = stream.Part()
        
        ''' put everything but notes and chords in stream'''
        chordifiedFlat = chordifiedStream.flat
        
        for el in chordifiedFlat.iter.getElementsNotOfClass([chord.Chord, note.Note]):
            fbStream.insert(el.offset, el)
 
        ''' loop over PitchCollections and get root pitches '''
        for pitchCollection in self.explainedPitchCollectionList:
            rootPitch = pitchCollection.getRootPitch()
            #logging.info (rootPitch)
            
            ''' create note according to duration of verticality '''
            currentOffset = pitchCollection.verticality.offset
            if pitchCollection.verticality.nextVerticality == None:
                nextOffset = pitchCollection.verticality.timespanTree.element.duration.quarterLength
            else:
                nextOffset = pitchCollection.verticality.nextVerticality.offset
            durationQuartLength = nextOffset-currentOffset
            
            if rootPitch == None:
                rootNote = note.Rest()  
            else:  
                rootNote = note.Note(rootPitch)
            rootNote.duration.quarterLength = durationQuartLength
            
            fbStream.insert(currentOffset, rootNote)
         
         
        fbStream.id = "Fundamental Bass"
        fbStream.partName = 'Fundamental Bass'
        fbStream.partAbbreviation = 'FB'
        
        
        ''' change key(s) ''' 
        for clefElement in fbStream.recurse().getElementsByClass(clef.Clef):
            fbStream.recurse().replace(clefElement, fbStream.bestClef(recurse=True))
        
        #for keyElement in fbStream.recurse().getElementsByClass(key.Key):
            #logging.info (keyElement.alteredPitches)
        
        stream1 = stream.Stream() 
        stream1.append(fbStream)
        
            
        ''' remove repetitions in stream '''
        reductionStream = reduction.Reduction (stream1)
        reductionStream.removeRepetitions()
        
        return reductionStream.getLayer() 
    
    
    def getHypotheses (self):
        hypothesisList = []
        for explainedPitchCollection in self.explainedPitchCollectionList:
            for hypothesis in explainedPitchCollection.getHypotheses():
                hypothesisList.append(hypothesis)
        
        return hypothesisList
    
    def getPitchExplanation (self, pitch):
        for H_AndNhnCollection in self.analyzedVerticalitiesList: 
            if H_AndNhnCollection.getPitchExplanation(pitch) != None:
                return H_AndNhnCollection.getPitchExplanation(pitch)
             
        return None 

    def getUnexplainedPitches (self):
        pitchList = []
        for explainedPitchCollection in self.explainedPitchCollectionList:
            for unexplainedPitch in explainedPitchCollection.getUnexplainedPitches():
                pitchList.append(unexplainedPitch)
        
        return pitchList   
     
    def isProlongationOfOngoingDissonance (self, unexplainedPitch):
        
        ''' get current unresolved dissonances '''
        unresolvedDissonanceList = self.getDissonancesAtOffset (unexplainedPitch.verticalities[1].offset)
        
        ''' check if unexplainedPitch corresponds to one of them '''
        for unresolvedDissonance in unresolvedDissonanceList:
            if unresolvedDissonance.pitch == unexplainedPitch.pitch: 
                ''' if so update knowledge and clear hypotheses'''
                self._mergePitchInformation(unresolvedDissonance, unexplainedPitch)
                unexplainedPitch.hypothesisList.clear()
                return True
        return False 
        
        
    def rejectHypothesis(self, hypothesis):
        ''' rejects hypothesis and accepts implicit alternatives (for example actual resolution if hypothesis "resolution before actual resolution' is wrong etc.)'''
        if hypothesis.pitchSubType=='resolution before actual resolution':
            pitchCollection = self.getExplainedPitchCollectionAtOffset(hypothesis.verticalities[1].offset)
            explainedPitch = pitchCollection.getAnalyzedPitch(hypothesis.pitch)
            explainedPitch.pitchType = hypothesis.pitchType
            pitchCollection.updateExplanations()   
            
    def unexplainedPitches (self):
        ''' TODO merge with getUnexplainedPitches '''
        unexplainedPitchList = []
        for pitchCollection in self.explainedPitchCollectionList:
            unexplainedPitchList = unexplainedPitchList + pitchCollection.unexplainedPitches()
        return unexplainedPitchList           
    
    def inferKnowledgeFromExplainedPitches (self, pitchCollection):
        ''' Non contextual tests '''
        pitchCollection.updateExplanations()
        
        ''' Contextual tests '''
        pitchCollectionV0 =  self.getExplainedPitchCollectionBeforeOffset(pitchCollection.verticality.offset)
        pitchCollectionV1 = pitchCollection
        if pitchCollectionV1.isExplained(): return
        
        
        ''' test 1: inertia --- if all pitches are explained in previous verticality and if changing pitches are all explained in current verticalty, then stationary pitches have same explanation in this verticality '''
        ''' everything is explained in previous verticalty '''
        if  pitchCollectionV0.isExplained():
            ''' test if all changing pitches are explained (each pitch which is not in previous verticality is explained)'''
            ''' get changing pitches '''
            changedPitches = pitchCollectionV1.getAnalyzedPitchesNotBeloningToList(pitchCollectionV0.analyzedPitchList)
            unchangedPitches = pitchCollectionV1.getAnalyzedPitchesNotBeloningToList(changedPitches)
            ''' test if everything is explained '''
            if all(analyzedPitch.isExplained() == True for analyzedPitch in changedPitches):
                
                ''' merge explanation of unchangedPitches '''
                for unchangedPitch in unchangedPitches:
                    self._mergePitchInformation(pitchCollectionV0.getAnalyzedPitch(unchangedPitch.pitch), unchangedPitch) 
    
    
    
    def inferKnowledgeFromHypothesis(self, hypothesis):
        ''' Non contextual tests '''
        pitchCollectionAtOffset = self.getExplainedPitchCollectionAtOffset(hypothesis.verticalities[1].offset)
        pitchCollectionAtOffset.updateExplanations(hypothesis)
        
        ''' Contextual tests '''    
        updateInformation = True
        while updateInformation:
            updateInformation = False
            unexplainedPitchList = self.getUnexplainedPitches()
            
            for unexplainedPitch in unexplainedPitchList:                    
                ''' test if unexplained pitch is prolonged dissonance, if so, add information to analyzed pitch '''
                if self.isProlongationOfOngoingDissonance (unexplainedPitch):
                    explainedCollection = self.getExplainedPitchCollectionAtOffset(unexplainedPitch.verticalities[1].offset)
                    explainedCollection.updateExplanations()
                    updateInformation = True 
                    break
    
    def showStatistics (self):
        ''' get analyzed pitches '''
        analyzedPitchList = self.getAnalyzedPitches()
        
        explainedPitches = 0
        unexplainedPitches = 0
        remainingHypotheses = 0
        
        for analyzedPitch in analyzedPitchList:
            
            if analyzedPitch.isExplained():
                explainedPitches = explainedPitches + 1
            
            else:
                unexplainedPitches = unexplainedPitches + 1
                remainingHypotheses = remainingHypotheses + len (analyzedPitch.hypothesisList)
                
                
        logging.info ('Explained pitches: ' + str( round (explainedPitches/len (analyzedPitchList)*100,2)) + '% (' + str (explainedPitches) + ')'  + ', unexplained pitches: '  + str(round (unexplainedPitches/len (analyzedPitchList)*100,2)) + '%(' + str (unexplainedPitches) + ')'  + " unresolved hypotheses :" + str(remainingHypotheses)  )
 
    def _atLeastOnePitchClassIsCommon (self, verticality1, verticality2, excludePitches = []):
        for pitchV1 in verticality1.pitchSet:
            if pitchV1 not in excludePitches: 
                for pitchV2 in verticality2.pitchSet:
                    if pitchV1.pitchClass == pitchV2.pitchClass:
                        return True
         
        return False
    
    def _atLeastOnePitchisNotParsimonious (self, verticality1, verticality2, excludePitchesV2 = []):
        
        ''' remove excluded pitches from v1 v2 ''' 
        V1num = []
        filteredV2num = []
        
        for pitch in  verticality1.pitchSet:
            V1num.append(pitch.diatonicNoteNum)
            
        for pitch in verticality2.pitchSet:
            if pitch not in excludePitchesV2: filteredV2num.append(pitch.diatonicNoteNum)

        
        ''' test that the pitches of v1 either remain in v2 or progress by step upwards or downwards ''' 
        for diatonicNoteNum in filteredV2num:
            pitchNumStepUp = diatonicNoteNum + 1
            pitchNumStepDown = diatonicNoteNum -1 
            if diatonicNoteNum not in V1num and pitchNumStepUp not in V1num and pitchNumStepDown not in V1num:
                return True  
        return False 
    
    def _getHorizontalityContainingPitch(self, pitchS, horizontalities):
        for unused_part, timespanList in horizontalities.items():
            for elementTimespansCounter in range (0, len(timespanList.timespans)):
                element = timespanList.timespans[elementTimespansCounter].element
                if element.isNote:
                    if  element.pitch == pitchS:
                        return timespanList
                elif element.isChord:
                    if pitchS in element.pitches:
                        return timespanList
        
    def _mergePitchInformation (self, sourceAnalyzedPitch, targetAnalyzedPitch): 
        
            from music21.tree.verticality import VerticalitySequence 
            targetAnalyzedPitch.pitchType = sourceAnalyzedPitch.pitchType
            targetAnalyzedPitch.pitchSubType = sourceAnalyzedPitch.pitchSubType
            targetAnalyzedPitch.certainty = sourceAnalyzedPitch.certainty
            ''' rebuild verticality sequence '''
            verticalities = VerticalitySequence([sourceAnalyzedPitch.verticalities[0], targetAnalyzedPitch.verticalities[1], sourceAnalyzedPitch.verticalities[2] ])
            targetAnalyzedPitch.verticalities = verticalities 
            logging.info ('Could infer additional information: pitch ' + str (targetAnalyzedPitch.pitch) + ' at offset ' + str(targetAnalyzedPitch.verticalities[1].offset) +  ': ' + str(targetAnalyzedPitch.pitchType))    
    
    def _getElementsContainingPitch (self, nhVerticality, pitch): 
        elementList = []
        allElements = []
        
        for element in nhVerticality.startTimespans:
            allElements.append(element.element)
            
        for element in nhVerticality.overlapTimespans:
            allElements.append(element.element)
    
        
        for element in allElements:
            if isinstance(element, note.Note):
                if element.pitch == pitch:
                    elementList.append(element)
            if isinstance(element, chord.Chord):
                if pitch in element.pitches:
                    elementList.append(element)
        return elementList
    
    def _getHorizontalityList (self, scoreStream):
        ''' returns trigram'''
        horizontalityList = []
        for part in scoreStream.parts:
            ''' loop through parts '''
            pitchList = []
            for element in part.elements:
                 
                if element.isNote:  
                    pitchList.append (element) 
                else:
                    pitchList.append(None)
            horizontalityList.append(pitchList)    
        return horizontalityList
    
    def _getMelMovementsList (self, scoreStream):
        ''' returns melodic movements of trigram '''
        
        movementList = []   
        ''' loop through scoreStream '''
        for part in scoreStream.parts:
            ''' loop through parts '''
            movement = []
            for elementCounter in range (0, len (part)-1):
                element1 = part[elementCounter]
                element2 = part[elementCounter +1]
                if element1.isNote and element2.isNote:
                    movement.append (interval.Interval (element1.pitch, element2.pitch).generic.directed) 
                else:
                    movement.append(0)
            movementList.append(movement)   
            
        return movementList 
    
    def _getMelStreams(self, verticalities, containsPitch):
        ''' returns a stream with one or many melodic lines corresponding to parts'''
        ''' each line has three notes '''
        ''' get offsetList '''
        
        
        ''' create offset list '''
        offsetList = []
        for element in verticalities._verticalities:
            offsetList.append(element.offset)
        
        ''' get horizontalities and loop over parts'''
        horizontalities = self.scoreTree.unwrapVerticalities(verticalities)
        scoreStream = stream.Score()
        for unused_part, timespanList in horizontalities.items():
            
            ''' check if pitch in timespanList and if so get pitchedTimeSpan '''
            pitchedTimeSpan = self._getPitchedTimeSpanConainingPitchAtOrBeforeInHorizontality(timespanList, offsetList[1], containsPitch)
            if pitchedTimeSpan == None : continue
           
            ''' check number of elements at v0, v1, v2, if vo or v2 have no elements add rest'''
            elementListV0 = self._getElementAtOrBeforeInHorizontality(timespanList, offsetList[0], pitchedTimeSpan.part)
            elementListV1 = self._getElementAtOrBeforeInHorizontality(timespanList, offsetList[1], pitchedTimeSpan.part)
            elementListV2 = self._getElementAtOrBeforeInHorizontality(timespanList, offsetList[2], pitchedTimeSpan.part)
            
            if len (elementListV0) == 0: elementListV0.append(note.Rest())
            if len (elementListV2) == 0: elementListV2.append(note.Rest())
            
            
            ''' create streams according to the number of elements '''        
            for elementV0 in elementListV0:
                for elementV1 in elementListV1:
                    for elementV2 in elementListV2:
                        partStream = stream.Part()
                        ''' deep copy '''
                        elementV0dC = copy.deepcopy(elementV0)
                        elementV1dC = copy.deepcopy(elementV1)
                        elementV2dC = copy.deepcopy(elementV2)
                        
                        ''' same durations '''
                        elementV0dC.duration.quarterLength = 1
                        elementV1dC.duration.quarterLength = 1
                        elementV2dC.duration.quarterLength = 1
                        
                        ''' append '''
                        partStream.append(elementV0dC)
                        partStream.append(elementV1dC)
                        partStream.append(elementV2dC) 
                        
                        ''' insert stream '''
                        scoreStream.insert(0, partStream) 
        if len (scoreStream.elements) > 0:
            return scoreStream
        else: 
            return None 
        
    
    def _getElementAtOrBeforeInHorizontality (self, horizontality, offset, part = None):
        ''' returns a list of elements at or before offset in horizontality '''
        elementList = []
        timespans = horizontality.timespans
        
        for pitchedTimeSpan in timespans:
            if part != None : 
                if pitchedTimeSpan.part != part: continue
            
            if pitchedTimeSpan.offset == offset:
                elementList.append(pitchedTimeSpan.element)
            elif pitchedTimeSpan.offset < offset and pitchedTimeSpan.endTime > offset:
                elementList.append (pitchedTimeSpan.element)
                
        return elementList
    
    def _getPitchedTimeSpanConainingPitchAtOrBeforeInHorizontality (self, horizontality, offset, pitch):
        ''' returns either pitchedTimeSpan in which the pitch appears or none '''
        timespans = horizontality.timespans
        for pitchedTimeSpan in timespans:
            if pitchedTimeSpan.offset == offset:
                if pitchedTimeSpan.element.pitch.nameWithOctave == pitch.nameWithOctave:
                    return pitchedTimeSpan
            elif pitchedTimeSpan.offset < offset and pitchedTimeSpan.endTime > offset:
                if pitchedTimeSpan.element.pitch.nameWithOctave == pitch.nameWithOctave:
                    return pitchedTimeSpan
                
        return None
        
    
                
 
        
    
    def _elementListContainsPitch (self, elementList, pitch):
        for element in elementList :
            if not isinstance(element, note.Note): continue
            if element.pitch.nameWithOctave == pitch.nameWithOctave:  
                return True
        return False
    
    def _getVerticalityVector(self, verticality1, verticality2):
        rootV1 = verticality1.toChord().root()
        rootV2 = verticality2.toChord().root()
        
        rootInterval = interval.Interval(rootV1, rootV2)
        
        if rootInterval.generic.simpleUndirected > 4:
            rootInterval = rootInterval.complement
            return rootInterval.generic.directed
        else:
            return rootInterval.generic.directed
    
    def _isAccentuated (self, verticalities, chordNb): 
        accentuated = False
        
        if verticalities[1] == None or verticalities[2] == None:
            return None
        
        if verticalities[chordNb].beatStrength > verticalities[chordNb+1].beatStrength:
            accentuated = True
        return accentuated  
    
    def _pitchAnalysis(self, pitch, isAccentuated, horiozontalityList, onePitchClassRemainsV0V1, onePitchClassRemainsV1V2, onePitchNotParsimoniousV0V1, v0v1Duration, v1v2Duration, v2v3Duration):
        #mainBeat = 1
        
        # TODO retrun analyzedPitch //  hypothesis list 
        
        
        if horiozontalityList == None:
            return None, None
        
        ''' reorganize hList '''
        reorganizedList1 = []
        reorganizedList2 = []
        reorganizedList3 = []
        for horizontality in horiozontalityList:  
            
            reorganizedList1.append([horizontality[0], horizontality[1] > 2 or horizontality[1] < -2]) # melodic movement or h0 and h1 has leap
            reorganizedList2.append([horizontality[0] == 1, horizontality[1]]) # h0 remains in place, h1 melodic movement
            reorganizedList3.append ([horizontality[0] > 2 or horizontality[0] < 2, horizontality[1]])  # h0 makes leap, h1 melodic movement

        ''' canonic dissonances '''
        # non accentuated passing notes
        if isAccentuated == False and  any(x in [[2, 2], [-2, -2]] for x in horiozontalityList) and onePitchClassRemainsV0V1 == True:
            return 'PN', '', 1
        # non accentuated neighbor notes 
        elif isAccentuated == False and any(x in [[2, -2], [-2, 2]] for x in horiozontalityList) and onePitchClassRemainsV0V1 == True:
            return 'NN', '', 1
        # accentuated passing notes     
        elif isAccentuated == True and  any(x in [[2, 2], [-2, -2]] for x in horiozontalityList) and onePitchClassRemainsV1V2 == True:
            return 'PN', 'AC', 1
        # accentuated neighbor notes    
        elif isAccentuated == True and any(x in [[2, -2], [-2, 2]] for x in horiozontalityList) and onePitchClassRemainsV1V2 == True and v1v2Duration <= v2v3Duration:
            return 'NN', 'AC', 1 
        # suspensions    
        elif isAccentuated == True and any(x in [[1, -2]] for x in horiozontalityList)and onePitchClassRemainsV0V1 == True: # and v1v2Duration >= mainBeat:
            return 'SU', '', 1
        # non accentuated suspension
        elif isAccentuated == False and any(x in [[1, -2]] for x in horiozontalityList)and onePitchClassRemainsV0V1 == True and onePitchNotParsimoniousV0V1 == True: # last criterium used to avoid confusion with passing note 
            return 'SU', 'suspension on weak beat', 1
        
        # escape notes 
        elif isAccentuated == False and any(x in [[2, True], [-2, True]] for x in reorganizedList1) and onePitchClassRemainsV0V1 == True:
            return 'EN', '', 1
        
        # anticipations
        elif isAccentuated == False and any(x in [[False, 1]] for x in reorganizedList2) and onePitchClassRemainsV0V1 == True:
            return 'AN', '', 1
        
            
        #### irregular dissonances ####
        
        # suspensions 
        # suspensions with resolution before actual resolution 
        elif isAccentuated == True and any(x in [[1, -2]] for x in horiozontalityList)and onePitchClassRemainsV0V1 == True: #and v1v2Duration < mainBeat:
            return 'SU', 'resolution before actual resolution', 0.75
        
        # suspensions with interpolation (anything but resolution) before resolution ?
        elif isAccentuated == True and any(x in [[1, True]] for x in reorganizedList1)and onePitchClassRemainsV0V1 == True:
            return 'SU', 'with interpolation before resolution', 0.5
        
        elif isAccentuated == False and any(x in [[1, True]] for x in reorganizedList1)and onePitchClassRemainsV0V1 == True and onePitchNotParsimoniousV0V1 == True:
            return 'SU', 'suspension on weak beat with interpolation before resolution', 0.5
        
        # suspensions with delayed regular resolution 
        elif isAccentuated == True and any(x in [[1, 1]] for x in horiozontalityList)and onePitchClassRemainsV0V1 == True: 
            return 'SU', 'suspensions with delayed regular resolution', 0.5
        
        elif isAccentuated == False and any(x in [[1, 1]] for x in horiozontalityList)and onePitchClassRemainsV0V1 == True and onePitchNotParsimoniousV0V1 == True:
            ''' if regular resolution afterwards and other voice's pitch classes don't change ''' 
            return 'SU', 'suspensions on weak beat with delayed regular resolution', 0.5
        
        
        # passing notes  
        # passing notes of higher level (diminutions at other voices)
        elif isAccentuated == True and any(x in [[2, 1], [-2, 1]] for x in horiozontalityList) and onePitchClassRemainsV0V1 == True and onePitchClassRemainsV1V2 == True:
            return 'PN', 'DR', 0.5
        
        
        
        
        
        else: return None, None, 0 
    
    def _pitchesAtOffsetinHorizontality(self, horizontality, offset):
        for pitchedTimeSpan in horizontality.timespans:
          
            if offset == pitchedTimeSpan.offset and offset < pitchedTimeSpan.endTime: # starts at the beginning of span and before endtime
                return pitchedTimeSpan.pitches
            elif offset > pitchedTimeSpan.offset and offset < pitchedTimeSpan.endTime: # starts after beginning of span
                return pitchedTimeSpan.pitches
        return None
        
    
    def _pitchIsDissonantAgainstAtLeastOnePitch (self, verticality, pitch):
        
        bassPitch = verticality.toChord().bass()
        fourthToBass = self._verticalityHasIntervalToBass(verticality, ['P4', ['A4']])
        pitchBassInterval = interval.Interval (bassPitch, pitch)
        
        
        if fourthToBass:
            if pitch.name == bassPitch.name or pitchBassInterval.generic.simpleUndirected in [4]: return True 
        
        
        for pitchV in verticality.pitchSet:
            intervalPV = interval.Interval(pitchV, pitch)
            if intervalPV.generic.simpleUndirected in [2, 7]: return True  
            
        return False
    
    def _verticalityHasIntervalToBass (self, verticality, intervalSimpleNameList):
        realBassPitch = verticality.toChord().bass()
        
        for pitchV in verticality.pitchSet:
            if interval.Interval(realBassPitch, pitchV).simpleName in intervalSimpleNameList:
                return True
        return False  
    
   
        