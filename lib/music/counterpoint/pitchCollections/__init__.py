# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# 
#
# Copyright:    Christophe Guillotel-Nothmann Copyright © 2017
#-------------------------------------------------------------------------------

from music21 import tree, note, chord, stream, pitch, interval
from music21.tree.spans import PitchedTimespan
from music21.tree.verticality import VerticalitySequence, Verticality
from _operator import and_
#from tkinter.constants import VERTICAL, END
from copy import deepcopy
from music21.pitch import Pitch
import numpy, logging, copy
from setuptools.dist import sequence 
from music21.stream import Score
from python_log_indenter import IndentedLoggerAdapter
from music21.chord import Chord
from music21.tree.timespanTree import TimespanTree
from music21.languageExcerpts.instrumentLookup import transposition
 

class PitchCollectionSequences(object):

    def __init__(self, work, adaptableFrame=False, exploreHypothesis=False):
        ''' create stream and AVL tree, get chord Templates '''
        
        self.stream = work
        # self.scoreTree=self.stream.asTimespans(classList=(note.Note, chord.Chord))
        self.scoreTree = tree.fromStream.asTimespans(self.stream, flatten=True, classList=(note.Note, chord.Chord))
        
        self.pitchCollectionSequenceList = []
        self.adaptableFrame = adaptableFrame
        self.exploreHypothesis = exploreHypothesis
        
        ''' 1.Create AnalyzedPitchCollectionSequence  '''
        explainedPitchCollectionList = []
        logging.info ('Creating pitch collections...') 
        for verticality in self.scoreTree.iterateVerticalities():
            ''' create pitch collection '''
            pitchCollection = self.createPitchCollection (verticality)
            explainedPitchCollectionList.append(pitchCollection)
        
        self.pitchCollSequence = PitchCollectionSequence(self.scoreTree, explainedPitchCollectionList)
        # logging.info ('Number of pitch collections: ' + str(len(explainedPitchCollectionList)) + ' current explanation ratio: ' + str(self.pitchCollSequence.explanationRatioList[-1]) +  ' current incoherence ratio: ' + str(self.pitchCollSequence.incoherenceRatioList[-1])) 
        
        self.pitchCollectionSequenceList.append(self.pitchCollSequence)
        
    def createPitchCollection (self, verticality):
        
        analyzedPitchList = []
        verticalities = VerticalitySequence([None, verticality, None])
        
        ''' check if verticality is consonant '''
        #=======================================================================
        # element = verticality.makeElement()
        # 
        # if isinstance(element, chord.Chord) :
        #     if element.isConsonant(): isConsonant = True
        #     
        # if isinstance (element, note.Note): isConsonant = True
        #=======================================================================
        
        ''' extract all pitches (not only pitch sets but also every instance of same pitch) '''
        ''' 1. get everything in start and overlap timespans '''
        elementList = []
        for element in verticality.startTimespans:
            elementList.append(element)
        
        for element in verticality.overlapTimespans:
            
            if round (element.endTime, 6) == round (verticality.offset, 6):continue
            elementList.append(element)
        
        ''' 2. loop over these elements  '''
        for element in elementList:
            ''' 2.1. extract part '''
            elementPart = element.getParentageByClass(classList=(stream.Part,))
            
            ''' 2.2. extract voice '''
            elementVoice = element.getParentageByClass(classList=(stream.Voice,))
            
            ''' 2.3a if element is note '''
            if isinstance(element.element, note.Note):
                ''' get id for this specific note '''
                elementId = element.element.id 
                ''' create analyzed pitch, add information append to pitchList'''
                analyzedPitch = Pitch(element.element.pitch, verticalities)
                analyzedPitch.id = elementId
                analyzedPitch.part = elementPart
                analyzedPitch.voice = elementVoice
                analyzedPitch.attack = True if element in verticality.startTimespans else False
                analyzedPitchList.append(analyzedPitch)
                
                if verticality.nextVerticality != None:
                    analyzedPitch.segmentQuarterLength = verticality.nextVerticality.offset - verticality.offset
                else:
                    analyzedPitch.segmentQuarterLength = verticality.startTimespans[0].quarterLength
                
            if isinstance(element.element, chord.Chord):
                
                ''' loop over every note in chord and create analyzed pitch '''
                for chordNote in element.element._notes:
                    analyzedPitch = Pitch(chordNote.pitch, verticalities)
                    analyzedPitch.id = chordNote.id
                    analyzedPitch.part = elementPart
                    analyzedPitch.voice = elementVoice
                    analyzedPitch.attack = True if element in verticality.startTimespans else False
                    analyzedPitchList.append(analyzedPitch)
            
        return PitchCollection(verticality, analyzedPitchList)
    
    def getAnalyzedPitches (self, sequence=0):
        
        ''' get all analyzed pitches in pitchCollSequence '''
        return self.pitchCollectionSequenceList[sequence].getAnalyzedPitches()
    
    def getElementsContainingPitch (self, nhVerticality, pitch): 
        elementList = []
        allElements = []
        
        for element in nhVerticality.startTimespans:
            allElements.append(element.element)
            
        for element in nhVerticality.overlapTimespans:
            allElements.append(element.element)
        
        for element in allElements:
            if isinstance(element, note.Note):
                if element.pitch.nameWithOctave == pitch.nameWithOctave:
                    elementList.append(element)
            if isinstance(element, chord.Chord):
                if pitch in element.pitches:
                    elementList.append(element)
        return elementList
    
    def getPitchIdOfReferenceElement (self, verticality, pitch):
        elementList = self.getElementsContainingPitch (verticality, pitch)
        elementReferenceIdList = []
        
        for element in elementList:
            if isinstance(element, note.Note):
                elementReferenceIdList.append(element.pitch.id)
        
        return elementReferenceIdList
    
    def getPitchCollectionSequence(self, xmlString=False):
    
        if len (self.pitchCollectionSequenceList) == 0: 
            if xmlString == False:
                return self.pitchCollSequence
            else:
                return self.pitchCollSequence.getXML()
        else : 
            # logging.INFO('MORE THAN ONE POSSIBLE SCORE... Retrieving only first possibility')
            if xmlString == False:
            
                return self.pitchCollectionSequenceList[0] 
            else: return self.pitchCollectionSequenceList[0].setXML()
    
    def getXMLRepresentation (self):
        xmlRepresentation = self.pitchCollectionSequenceList[0].getXMLRepresentation()
        
        return xmlRepresentation
    
    def getAnnotatedStream(self):
        scoreList = []
        
        ''' remove all lyrics '''
        for verticality in  self.scoreTree.iterateVerticalities():
            for element in verticality.startTimespans:
                if isinstance(element.element, note.Note) or isinstance(element.element, chord.Chord):
                    element.element.lyric = None
        
        ''' loop through nhn collection list '''
        
        possibleScores = []
        if len (self.pitchCollectionSequenceList) == 0 :
            possibleScores = [self.pitchCollSequence]
        
        else: possibleScores = self.pitchCollectionSequenceList
        
        for possibleScore in possibleScores:
            
            ''' remove all lyrics '''
            for verticality in  self.scoreTree.iterateVerticalities():
                for element in verticality.startTimespans:
                    if isinstance(element.element, note.Note) or isinstance(element.element, chord.Chord):
                        element.element.lyric = None
        
            for explainedPitchCollection in possibleScore.explainedPitchCollectionList: 
                verticality = explainedPitchCollection.verticality
                
                for analyzedPitch in explainedPitchCollection.analyzedPitchList:
                    elementList = possibleScore.getElementsContainingPitch(verticality, analyzedPitch.pitch)
                    
                    for element in elementList:
                        pitchType = str(analyzedPitch.pitchType)
                        if analyzedPitch.probability < 1: pitchType = pitchType + " (?)" 
                    
                        if element.lyric == None:
                                element.lyric = pitchType
                        elif pitchType in element.lyric:
                            pass
                        
                        else:   
                            element.lyric = str (element.lyric) + pitchType
        
            scoreList.append (tree.toStream.partwise(self.scoreTree, templateStream=self.stream))
            
        # if len (scoreList)> 1: logging.info(str (len(scoreList)) + ' POSSIBLE SCORES... Retrieving only first item')
        
        return scoreList
    
    def setPitchCollectionSequence(self, xmlString):
        ''' loads xmlData into pitch coll sequence '''
        
        self.pitchCollectionSequenceList[0].loadXMLAnalysis(xmlString)
         
    
class PitchCollectionSequence (object):
    
    def __init__(self, scoreTree, pitchCollectionList):
        self.scoreTree = scoreTree
        self.explainedPitchCollectionList = pitchCollectionList
        self.explanationRatioList = []
        self.incoherenceRatioList = []
        self.probabilityRatioList = []
        self.totalPitches = 0
        self.idDictionary = {}  # ## maps note or chord id to analyzedPitches (one note or chord can have several analytical interpretations according to offset) 
        self.callId = None
        self.rootMap = []  # stores data about roots from a start offset to an end offset
        self.name = None 
        self.exploredHypothesisList = []  # a list of pitch hypotheses already explored
    
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
    
    def getAnalyzedCollections (self, startOffset=None, stopOffset=None, templateRepresentation=None, probabilityThreshold=None):
        pitchCollList = []
        
        for pitchCollection in self.explainedPitchCollectionList:
            
            if startOffset != None:
                if pitchCollection.verticality.offset < startOffset: continue
                
            if stopOffset != None:
                if pitchCollection.verticality.offset > stopOffset: break
            
            if probabilityThreshold != None:
                if pitchCollection.probability < probabilityThreshold: continue
            
            if templateRepresentation != None:
                if len (pitchCollection.template.representation) != len (templateRepresentation) : continue  # check if same size
                comparison = True
                for pitchSetCounter in range (0, len(pitchCollection.template.representation)):  # check if match
                    if pitchCollection.template.representation[pitchSetCounter] != templateRepresentation[pitchSetCounter] :
                        comparison = False
                        break
                if comparison == False: continue 
                
            pitchCollList.append(pitchCollection)
        return pitchCollList
    
    def getAnalyzedPitches(self, elementID=None, offset=None):
        if elementID != None:
            return self.getAnalyzedPitchCorrespondingToId(elementID)
        elif offset != None:
            return self.getExplainedPitchesAtOffset(offset)
            
        else:
            analyzedPitchList = []
            
            for analyzedPitchCollection in self.explainedPitchCollectionList:
                analyzedPitchList = analyzedPitchList + analyzedPitchCollection.analyzedPitchList
        
        return analyzedPitchList
    
    def getAnalyzedPitchCorrespondingToId (self, elementID, offset=None):
        analyzedPitchList = []
        for analyzedPitchCollection in self.explainedPitchCollectionList:
            analyzedPitchesCorrespondingToId = analyzedPitchCollection.getAnalyzedPitchesCorrespondingToId(elementID)
            if  analyzedPitchesCorrespondingToId != None:
                if offset != None:
                    if offset == analyzedPitchesCorrespondingToId.offset:
                        return [analyzedPitchesCorrespondingToId]
                else:
                    analyzedPitchList.append (analyzedPitchesCorrespondingToId)
        return analyzedPitchList
    
    def getAnalyzedPitchCollectionAtOffset (self, offset):
        for explainedPitchCollection in self.explainedPitchCollectionList:
            if explainedPitchCollection.verticality.offset == offset:
                return explainedPitchCollection 
            
        return None
    
    def getElementsContainingPitch (self, nhVerticality, pitch): 
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
    
    def getExplainedPitchesAtOffset (self, offset):
        ''' get pitch collection '''
        pitchCollection = self.getAnalyzedPitchCollectionAtOffset(offset)
                
        ''' get explained pitches '''   
        pitchList = pitchCollection.analyzedPitchList
        return pitchList
    
    def getExplainedPitchAtOffset (self, offset, pitch):
        ''' returns a list of explained pitch instances which correspond to the pitch at specified offset ''' 
        
        ''' get all pitches at offset '''
        explainedPitchList = self.getExplainedPitchesAtOffset(offset)
        explainedPitchSubList = []
        
        for analyzedPitch in explainedPitchList:
            if analyzedPitch.pitch == pitch:
                explainedPitchSubList.append(analyzedPitch)
        
        return explainedPitchSubList
    
    def getExplainedPitchesFromTo (self, startOffset, stopOffset, filterPitch=None):
        pitchList = []
        
        for explainedPitchCollection in self.explainedPitchCollectionList:
            if explainedPitchCollection.verticality.offset < startOffset: continue 
            if explainedPitchCollection.verticality.offset >= stopOffset: continue
            
            if filterPitch == None:
                pitchList = pitchList + explainedPitchCollection.analyzedPitchList
            else :
                pitchList = pitchList + self.getExplainedPitchAtOffset(explainedPitchCollection.verticality.offset, filterPitch)
            
        return pitchList
    
    def getExplainedPitchCollectionBeforeOffset (self, offset):
        ''' get index number of explained collection'''
        
        for x in range (0, len (self.explainedPitchCollectionList)):
            if self.explainedPitchCollectionList[x].verticality.offset == offset:
                if x > 0: return self.explainedPitchCollectionList[x - 1]
        
        return None
    
    def getChordifiedStream (self, unused_filter=['CN', 'SU']):
    
        ''' build root stream and chordify it '''
        rootStream = self.getFundamentalBass()
        chordifiedStream = rootStream.chordify()
        
        ''' loop over chords in stream '''
        for chordElement in chordifiedStream.flat.getElementsByClass(chord.Chord):
            offset = chordElement.offset
            duration = chordElement.duration.quarterLength
            if len (chordElement.pitches) > 0:
                chordElement.root = chordElement.pitches[0]
            else: chordElement.root = None
            
            ''' get all pitches between offset and next offset '''
            analyzedPitchList = self.getExplainedPitchesFromTo(offset, offset + duration, None)
            
            subList = []
            for analyzedPitch in analyzedPitchList:
                
                ''' filter pitches and add them '''
                if analyzedPitch.pitchType in unused_filter: 
                    subList.append(analyzedPitch.pitch)
            chordElement.pitches = subList
        
        return chordifiedStream            
    
    def getPitchCollectionSubset (self, startOffset, endOffset):
        subList = []
        
        for pitchColl in self.explainedPitchCollectionList:
            if pitchColl.verticality.offset >= startOffset and pitchColl.verticality.offset <= endOffset: 
                subList.append(pitchColl)
                
            elif pitchColl.verticality.offset > endOffset : return subList
        
        return subList
    
    def getPitchCollectionContext (self, offset, context):
        contextList = []
        
        ''' get pitch coll index of offset'''
        v0Index = None
        for  explainedPitchCollectionCounter in range (0, len(self.explainedPitchCollectionList)):
            if self.explainedPitchCollectionList[explainedPitchCollectionCounter].verticality.offset == offset:
                v0Index = explainedPitchCollectionCounter
                break
        
        ''' loop over pitch colls from lowest index to highest index'''
        lowestIndex = v0Index - context
        highestIndex = v0Index + context
        
        for index in range (lowestIndex, highestIndex + 1):
            if index < 0: contextList.append(None)  # index out of range 
            elif index > len(self.explainedPitchCollectionList) - 1: contextList.append(None)
            else:
                contextList.append(self.explainedPitchCollectionList[index])
                
        return contextList
        
    def getUnexplainedPitches (self, startOffset=None, stopOffset=None):
        pitchList = []
        for explainedPitchCollection in self.explainedPitchCollectionList:
            for unexplainedPitch in explainedPitchCollection.getUnexplainedPitches():
                    
                if startOffset != None and stopOffset != None:
                    if unexplainedPitch.offset >= startOffset and unexplainedPitch.offset < stopOffset:
                        pitchList.append(unexplainedPitch)
                 
                else: pitchList.append(unexplainedPitch) 
                
                ''' TODO: additionnal conditions startOffset != None, stopOffset == None etc. if needed ? '''  
        
        return pitchList   
    
    def getObservations(self):
        import numpy as np
        import os
        
        ''' get highest fileIndex in folder '''
 
        filenameList = []
        for filename in os.listdir('/Users/Christophe/Desktop/dataset/observations/'):
            if filename[-3:] != 'npy':continue
            filenameList.append(filename)

        fileIndex = len(filenameList)
        
        ''' loop over all pitch collections '''
        for pitchCollection in self.explainedPitchCollectionList:
            ''' loop over all analyzed pitches '''
            for analyzedPitch in pitchCollection.analyzedPitchList:
                
                ''' get observation list '''
                observationList = self.getObservationsForPitchId(analyzedPitch.id, 5, pitchCollection.verticality.offset)
                # fileObservations.write(observationString)
        
                ''' store label in file_2'''
                labelString = analyzedPitch.pitchType  # + '\t' + analyzedPitch.pitchSubType
                if labelString not in ["CN", "PN", "NN", "AN", "SU", "AP", "PE", "EN"]:
                    print ("Wrong label...skip: " + str(labelString))
                    continue
                
                # fileLabel.write(labelString)
        
                ''' store id in file_3 ''' 
                if analyzedPitch.id == None or pitchCollection.verticality.offset == None:
                    print ("ID or Offset not identified... skip")
                    continue 
                idString = analyzedPitch.id + '; ' + str(pitchCollection.verticality.offset)
                # fileId.write(idString)
                
                ''' put everything in numpy array'''
                thisdict = {"CN": 0, "PN": 1, "NN": 2, "AN": 3, "SU": 4, "AP": 5, "PE": 6, "EN":7}
            
                np.save('/Users/Christophe/Desktop/dataset/observations/' + str(fileIndex).zfill(7), np.array(observationList), True, False)
                np.save('/Users/Christophe/Desktop/dataset/labels/' + str(fileIndex).zfill(7), np.array(thisdict[labelString]), True, False)
                np.save('/Users/Christophe/Desktop/dataset/ids/' + str(fileIndex).zfill(7), np.array(idString), True, False)
                
                print ("Observation %s set" % (fileIndex))
                
                # fileObservations.close()
                # fileLabel.close()
                # fileId.close()
                
                fileIndex = fileIndex + 1
    
    def getObservationsForPitchId(self, analyzedPitchId, context=5, offset=0):
        
        ''' build list of list and fill everything with 0'''
        pitchList = []
        contextList = []
        
        observationList = [0, 0, 0, 0, 0, 0, 0, 0]
        
        for unused_counter in range (0, 7):
            pitchList.append(deepcopy(observationList))     
        
        for unused_counter in range (0, context * 2 + 1):
            contextList.append(deepcopy(pitchList)) 
        
        ''' get transposition interval '''
        observedPitch = self.getAnalyzedPitchCorrespondingToId(analyzedPitchId, offset)
        transpositionInterval = interval.Interval(noteStart=observedPitch[0].pitch, noteEnd=pitch.Pitch('C4'))  # # reference is arbitrarily set to 'C4' could be any pitch 
        
        # print ('Reference pitch: ' + observedPitch[0].pitch.step + ", diatonic number: " + str(pitchDiatonicNumber) + ", diatonic vector: " + str (diatonicVector))
        
        ''' create pitchCollList i.e. context before and after reference offset'''
        pitchCollectionList = self.getPitchCollectionContext(offset, context)
        
        ''' loop over pitch colls '''
        for index in range (0, len(pitchCollectionList)):
            pitchCollection = pitchCollectionList[index]
            
            if pitchCollection == None: continue  # in that case all values remain zero
            deepestPitchClass = pitchCollection.getBassPitch().step  # get deepest pitch class
            
            ''' loop over every analyzed pitch '''
            for analyzedPitch in pitchCollection.analyzedPitchList:
                
                ''' transpose pitch '''
                transpositionInterval.noteStart = note.Note(analyzedPitch.pitch.nameWithOctave)
                transposedPitch = transpositionInterval.noteEnd.pitch
                
                ''' get diatonic step'''
                diatonicStep = (transposedPitch.diatonicNoteNum - 1) % 7
                
                # print ("Observed pitch (0): %s, transposition interval: %s, current pitch: %s, transposition: %s, diatonic step: %s, alteration: %s " %(observedPitch[0].pitch, transpositionInterval, analyzedPitch.pitch.nameWithOctave, transposedPitch.nameWithOctave, diatonicStep, transposedPitch.alter))
                
                ''' fill list with dimension at corresponding position '''
                    
                ''' 1. vectorized diatonic steps '''
                contextList[index][diatonicStep][0] = 1 
                
                ''' 2. alteration '''
                contextList[index][diatonicStep][1] = transposedPitch.alter
                
                ''' 3. deepest pitch class '''   
                contextList[index][diatonicStep][2] = 1 if deepestPitchClass == analyzedPitch.pitch.step else 0
                
                ''' 4. duration '''
                contextList[index][diatonicStep][3] = pitchCollection.duration
                
                ''' 5. beat strength '''
                contextList[index][diatonicStep][4] = pitchCollection.verticality.beatStrength 
                
                ''' 6. attack '''
                contextList[index][diatonicStep][5] = 1 if analyzedPitch.attack == True else 0
                
                ''' 7. occurrence '''
                contextList[index][diatonicStep][6] = contextList[index][diatonicStep][6] + 1 
                
                ''' 8. same voice - part as reference pitch ''' 
                if contextList[index][diatonicStep][7] == 0:  # the diatonic step may be instantiated by another pitch. If result is positive, leave it like this
                    if analyzedPitch.part == observedPitch[0].part and analyzedPitch.voice == observedPitch[0].voice:
                        contextList[index][diatonicStep][7] = 1 
                    else: 0 
            
        return contextList 
    
    def loadXMLAnalysis (self, xmlString):
        
        'extracts information about pitch colls and analysed pitches from XML'
        import xml.etree.ElementTree as ET
        tree = ET.fromstring(xmlString)
        
        ''' pitch colls '''
         
        ''' 1. loop over pitch colls '''
        for pitchCollection in self.explainedPitchCollectionList:
            
            ''' get node corresponding to pitch coll '''
            nodeList = tree.findall(".//pitchColl[@offset='%s']" % (pitchCollection.verticality.offset))
            if len(nodeList) == 0: continue
            
            print (nodeList[0].attrib["root"])
            
            if nodeList[0].attrib["root"] in ['*', '', 'None', ' ']:
                pitchCollection.rootPitch = None
            else:
                pitchCollection.rootPitch = pitch.Pitch(nodeList[0].attrib["root"])
        
        ''' 2. analyzed pitches '''
        
        analyzedPitchList = self.getAnalyzedPitches()
        
        ''' loop over analyzed pitches '''
        for analyzedPitch in analyzedPitchList:
            
            ''' get node corresponding to analyzed pitch ''' 
            nodeList = tree.findall(".//*[@id='%s']" % (analyzedPitch.id))
            node = None
            for element in nodeList:
                if element.attrib["offset"] == str(analyzedPitch.offset): 
                    node = element
                    break
            
            ''' update analyzedPitch information '''
            if node == None: continue
            
            ''' check if anything has changed '''
            changed = False
            
            if str (analyzedPitch.pitchType) != node.attrib["pitchType"] or \
            str (analyzedPitch.pitchSubType) != node.attrib["pitchSubType"] or \
            str (analyzedPitch.explained) != node.attrib["explained"]  or \
            str (analyzedPitch.hypothesesChecked) != node.attrib["hypothesesChecked"] or \
            str (analyzedPitch.probability) != float (node.attrib["probability"]) or \
            str(analyzedPitch.preparationPitchID) != node.attrib["preparationPitchID"] or \
            str(analyzedPitch.resolutionPitchID) != node.attrib["resolutionPitchID"] or \
            str(analyzedPitch.preparationOffset) != node.attrib["preparationOffset"] or \
            str(analyzedPitch.resolutionOffset) != node.attrib["resolutionOffset"] :
                analyzedPitch.preparationPitchID = node.attrib["preparationPitchID"]
                analyzedPitch.resolutionPitchID = node.attrib["resolutionPitchID"]
                # analyzedPitch.preparationOffset = float (node.attrib["preparationOffset"]) if node.attrib["preparationOffset"] != 'None' else None
                # analyzedPitch.resolutionOffset = float (node.attrib["resolutionOffset"]) if node.attrib["resolutionOffset"] != 'None' else None
                changed = True
                
            analyzedPitch.pitchType = node.attrib["pitchType"]
            analyzedPitch.pitchSubType = node.attrib["pitchSubType"]
            analyzedPitch.explained = False if node.attrib["explained"] == 'False' else True
            analyzedPitch.hypothesesChecked = False if node.attrib["hypothesesChecked"] == 'False' else True 
            analyzedPitch.probability = float (node.attrib["probability"])
            
            ''' if changes find preparation and resolution pitches'''  
            if changed == False: continue        
            
            ''' recreate horizontalities and verticalities if dissonance, else None values '''
            
            if analyzedPitch.pitchType != 'CN':
                pass
                # analyzedPitch.preparationPitch = self.getAnalyzedPitchCorrespondingToId (analyzedPitch.preparationPitchID, analyzedPitch.preparationOffset)[0]
                # analyzedPitch.resolutionPitch = self.getAnalyzedPitchCorrespondingToId (analyzedPitch.preparationPitchID, analyzedPitch.resolutionOffset)[0]  
                
                # analyzedPitch.verticalities = VerticalitySequence([analyzedPitch.preparationPitch.verticalities[0], analyzedPitch.verticalities[0], analyzedPitch.resolutionPitch.verticalities[0] ])
                # horizontalities = self.scoreTree.unwrapVerticalities(analyzedPitch.verticalities)
                # analyzedPitch.horizontalities = self._getHorizontalityContainingPitch (self, analyzedPitch.pitch, horizontalities)
                
            else:
                analyzedPitch.verticalities = VerticalitySequence([None, analyzedPitch.verticalities[1], None ])
                analyzedPitch.horizontalities = None
                analyzedPitch.preparationOffset = None
                analyzedPitch.preparationPitchID = None
                analyzedPitch.resolutionOffset = None
                analyzedPitch.resolutionPitchID = None 
                analyzedPitch.probability = 1.0
    
    def setIdDictionary (self):
        'sets number of analytical subdivisions of the element (chord or note) the analytical pitch belongs to'
        
        ''' loop over all pitches '''
        analyzedPitchList = self.getAnalyzedPitches()
        for analyzedPitch in analyzedPitchList:
            ''' test if entry exists in idDictionary if so '''
            if not analyzedPitch.id in self.idDictionary:  
                ''' get sublist of analyzed pitches which share the same id (i.e. which are part of the same note / chord )'''
                subList = self.getAnalyzedPitches(analyzedPitch.id)        
                self.idDictionary.update({analyzedPitch.id: subList})
            
    def getXMLRepresentation(self):
        ''' creates an xml representation of analytical information of pitch colls and analysed pitches ''' 
        
        ''' populate id dictionary '''
        self.setIdDictionary()
        
        xmlSequence = "<root>"
        
        for pitchCollection in self.explainedPitchCollectionList:
            xmlSequence = xmlSequence + '<pitchColl offset="%s" root="%s">' % (pitchCollection.verticality.offset, pitchCollection.rootPitch)
            
            for analyzedPitch in pitchCollection.analyzedPitchList:
                
                xmlSequence = xmlSequence + '<analyzedPitch accentuated="%s" pitchType="%s" pitchSubType="%s" offset="%s" pitch="%s" probability="%s" preparationPitchID="%s" preparationOffset="%s" resolutionPitchID="%s" resolutionOffset="%s" explained="%s" hypothesesChecked="%s" id="%s" analyticalDivisions="%s"/>' % (analyzedPitch.accentuated, analyzedPitch.pitchType, "", analyzedPitch.offset, analyzedPitch.pitch, analyzedPitch.probability, analyzedPitch.preparationPitchID, analyzedPitch.preparationOffset, analyzedPitch.resolutionPitchID, analyzedPitch.resolutionOffset, analyzedPitch.explained, analyzedPitch.hypothesesChecked, analyzedPitch.id, len (self.idDictionary[analyzedPitch.id]))
            
            xmlSequence = xmlSequence + '</pitchColl>'
            
        xmlSequence = xmlSequence + "</root>"
            
        return xmlSequence    
    
    def showStatistics (self, timeElapsed):
        ''' get analyzed pitches '''
        analyzedPitchList = self.getAnalyzedPitches()
        
        explainedPitches = 0
        #=======================================================================
        unexplainedPitches = 0
        remainingHypotheses = 0
        # 
        for analyzedPitch in analyzedPitchList:
        #     
            if analyzedPitch.explained: 
                explainedPitches = explainedPitches + 1 
        #         
        #     
            else:
                unexplainedPitches = unexplainedPitches + 1
                analyzedPitch.setBestHypothesis()
                remainingHypotheses = remainingHypotheses + len (analyzedPitch.hypothesisList) 
        #=======================================================================
                
        # logging.info ('Explained pitches: ' + str( round (explainedPitches/len (analyzedPitchList)*100,2)) + '% (' + str (explainedPitches) + ')'  + ', unexplained pitches: '  + str(round (unexplainedPitches/len (analyzedPitchList)*100,2)) + '%(' + str (unexplainedPitches) + ')'  + " unresolved hypotheses :" + str(remainingHypotheses)  )
 
        self.setExplanationRatio()
        self.setIncoherenceRatio() 
        
        logging.info ('Explanation ratio: ' + str(round(self.explanationRatioList[-1], 2)) + ', incoherence ratio: ' + str(round(self.incoherenceRatioList[-1], 2)) + ", probability: " + str(round(self.probabilityRatioList[-1], 2)) + ", unresolved hypotheses :" + str(remainingHypotheses) + " Call id: " + str(self.callId) + " Time elapsed: " + str(timeElapsed))
    
    def unexplainedPitches (self):
        ''' TODO merge with getUnexplainedPitches '''
        unexplainedPitchList = []
        for pitchCollection in self.explainedPitchCollectionList:
            unexplainedPitchList = unexplainedPitchList + pitchCollection.unexplainedPitches()
        return unexplainedPitchList           
    
    def _atLeastOnePitchClassIsCommon (self, verticality1, verticality2, excludePitches=[]):
        for pitchV1 in verticality1.pitchSet:
            if pitchV1 not in excludePitches: 
                for pitchV2 in verticality2.pitchSet:
                    if pitchV1.pitchClass == pitchV2.pitchClass:
                        return True
         
        return False
    
    def _atLeastOnePitchisNotParsimonious (self, verticality1, verticality2, excludePitchesV2=[]):
        ''' build full verticality sequence '''
 
        verticalityList = []
        verticality = verticality1
        
        while verticality.offset <= verticality2.offset :
            verticalityList.append(verticality)
            verticality = verticality.nextVerticality
 
        ''' iterate pairwise over verticalities '''
        
        for verticality1, verticality2 in self._pairwise (verticalityList):
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
                pitchNumStepDown = diatonicNoteNum - 1 
                if diatonicNoteNum not in V1num and pitchNumStepUp not in V1num and pitchNumStepDown not in V1num:
                    return True  
        return False 
    
    def _elementListContainsPitch (self, elementList, pitch):
        for element in elementList :
            if not isinstance(element, note.Note): continue
            if element.pitch.nameWithOctave == pitch.nameWithOctave:  
                return True
        return False
    
    def _getAnalyzedContext (self, pitchList, verticalityList):
            analyzedContext = []
            
            for x in range (len (pitchList)):
                element = pitchList[x]
                if isinstance(element, pitch.Pitch):
                    verticality = verticalityList[x] 
                    if verticality != None:
                        offset = verticality.offset
                    else: offset = None
                    elementList = self.getAnalyzedPitchCorrespondingToId(element.id, offset)
                    if len (elementList) > 0:
                        analyzedContext.append(elementList[0])
                    else: analyzedContext.append(None)
                    
                else: analyzedContext.append(None)
            return analyzedContext
    
    def _getCompletePitchList(self, horizontality, verticalities):
        ''' returns pitchList organized as follows: [[v0 and elaborations][v1][elaborations v2] '''
        
        V0AndElaborations = []
        V1 = []
        ElaborationsAndV2 = []
        
        ''' V0AndElaborations '''
        verticality = verticalities[0] 
        while verticality.offset < verticalities[1].offset:
            V0AndElaborations.append(self._getPitchAtOffSetFromHorizontality(horizontality, verticality.offset))
            verticality = verticality.nextVerticality
            if verticality == None : break
            
        ''' V1 '''
        verticality = verticalities[1] 
        V1.append(self._getPitchAtOffSetFromHorizontality(horizontality, verticality.offset))
        
        ''' ElaborationsAndV2 '''
        verticality = verticalities[1].nextVerticality
        
        while verticality.offset <= verticalities[2].offset:
            ElaborationsAndV2.append(self._getPitchAtOffSetFromHorizontality(horizontality, verticality.offset))
            verticality = verticality.nextVerticality
            if verticality == None : 
                break
       
        return [V0AndElaborations, V1, ElaborationsAndV2]
            
    def _getElementAtOrBeforeInHorizontality (self, horizontality, offset, part=None):
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
    
    def _getMelodicMovementsFromPitchList (self, pitchList):
        ''' returns melodic movements, expressed as integers ''' 
        movementList = []   
        
        ''' reorganize list: if silences keep previous pitch '''
        formerPitch = pitchList [0]
        for x in range (1, len (pitchList)):
            if pitchList[x] == None: pitchList[x] = formerPitch
            formerPitch = pitchList [x]
        
        ''' iterate pairwise over pitchList '''
        for element1, element2 in self._pairwise (pitchList):
            if isinstance(element1, pitch.Pitch) and isinstance(element2, pitch.Pitch):
                movementList.append (interval.Interval (element1, element2).generic.directed) 
            else:
                movementList.append(0)
        return movementList
    
    def _getMelMovementsFromTimeSpanList(self, timeSpanList):
        movementList = []   
        
        ''' iterate pairwise over timeSpanList '''
        for element1, element2 in self._pairwise (timeSpanList):
            if element1.element.isNote and element2.element.isNote:
                movementList.append (interval.Interval (element1.element.pitch, element2.element.pitch).generic.directed) 
            else:
                movementList.append(0)
        return movementList
    
    def _getMelMovementsList (self, scoreStream):
        ''' returns melodic movements of trigram '''
        if scoreStream == None:
            print ('')
        
        movementList = []   
        ''' loop through scoreStream '''
        for part in scoreStream.parts:
            ''' loop through parts '''
            movement = []
            for elementCounter in range (0, len (part) - 1):
                element1 = part[elementCounter]
                element2 = part[elementCounter + 1]
                if element1.isNote and element2.isNote:
                    movement.append (interval.Interval (element1.pitch, element2.pitch).generic.directed) 
                else:
                    movement.append(0)
            movementList.append(movement)   
            
        return movementList 
    
    def _getNbOfMelMovements (self, movementList):
        nbOfMovements = 0
        
        for movement in movementList:
            if movement not in [0, 1]:
                nbOfMovements = nbOfMovements + 1
        return nbOfMovements
    
    def _getNormalizedMelStreams(self, verticalities, containsPitch):
        ''' returns a stream with one or many melodic lines corresponding to parts'''
        ''' each line has three notes '''
        ''' get offsetList '''
        
        ''' create offset list '''
        offsetList = []
        for element in verticalities._verticalities:
            offsetList.append(element.offset if element != None else None)
        
        ''' get horizontalities and loop over parts'''
        horizontalities = self.scoreTree.unwrapVerticalities(verticalities)
        scoreStream = stream.Score()
        for unused_part, timespanList in horizontalities.items():
            
            ''' check if pitch in timespanList and if so get pitchedTimeSpan '''
            pitchedTimeSpan = self._getPitchedTimeSpanContainingPitchAtOrBeforeInHorizontality(timespanList, offsetList[1], containsPitch)
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

    def _getPitchAtOffSetFromHorizontality(self, horizontality, offset):
        
        for timespan in horizontality.timespans:
            if timespan.offset <= offset and timespan.endTime > offset:
                return timespan.pitches[0]
            
        return None
    
    def _getPitchesFromTimespans (self, timeSpanList):
        pitchList = []
        for timespan in timeSpanList: 
            pitchList.append(timespan.pitch)
            break
    
    def _getPitchedTimeSpanContainingPitchAtOrBeforeInHorizontality (self, horizontality, offset, pitch):
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
    
    def _getTimeSpanContainingPitch (self, horizontality, pitch):
        ''' returns either pitchedTimeSpan in which the pitch appears or none '''
        
        timespans = horizontality.timespans
        for pitchedTimeSpan in timespans: 
            if pitchedTimeSpan.element.pitch.id in pitch.referenceIDs:
                return pitchedTimeSpan
        
        return None
    
    def _getTimespanListContainingPitch (self, containsPitch, offsetStart, offsetEnd, withStartOffset, withEndOffset):
        ''' returns the portion of the part between offsetStart and offsetEnd '''
        # from music21.tree.verticality import VerticalitySequence
        
        verticalityList = []
        
        ''' build verticality sequence'''
        verticality = self.scoreTree.getVerticalityAt(offsetStart)
        if withStartOffset == False: verticality = verticality.nextVerticality
        
        while verticality is not None :
            verticalityList.append(verticality)
            verticality = verticality.nextVerticality
            if verticality == None: break
            if withEndOffset:
                if verticality.offset > offsetEnd: break
            else:
                if verticality.offset >= offsetEnd: break
        verticalities = VerticalitySequence(verticalityList)
        
        ''' get horizontalities '''
        horizontalities = self.scoreTree.unwrapVerticalities(verticalities)
        
        for unused_part, timespanList in horizontalities.items():
            ''' check if pitch in timespanList and if so get pitchedTimeSpan '''
            pitchedTimeSpan = self._getTimeSpanContainingPitch(timespanList, containsPitch)
            if pitchedTimeSpan == None : continue
            return timespanList

        return None
    
    def _getVerticalityVector(self, verticality1, verticality2):
        rootV1 = verticality1.toChord().root()
        rootV2 = verticality2.toChord().root()
        
        rootInterval = interval.Interval(rootV1, rootV2)
        
        if rootInterval.generic.simpleUndirected > 4:
            rootInterval = rootInterval.complement
            return rootInterval.generic.directed
        else:
            return rootInterval.generic.directed
    
    def _pitchRemainsDuringTimeSpan (self, pitch, timeSpanList):
        ''' checks if pitch remains at same voice between both verticalities'''
        if timeSpanList == None: return False
        
        for timeSpan in timeSpanList:
            for tsPitch in timeSpan.pitches:
                if tsPitch.name != pitch.name:
                    return False
            
        return True
    
    def _isAccentuated (self, verticalities, chordNb): 
        accentuated = False
        
        if verticalities[1] == None or verticalities[2] == None:
            return None
        
        if verticalities[chordNb].beatStrength > verticalities[chordNb + 1].beatStrength:
            accentuated = True
        return accentuated  
    
    def _pairwise(self, iterable):
        from itertools import tee
    
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)
    
    def _pitchesAtOffsetinHorizontality(self, horizontality, offset):
        for pitchedTimeSpan in horizontality.timespans:
          
            if offset == pitchedTimeSpan.offset and offset < pitchedTimeSpan.endTime:  # starts at the beginning of span and before endtime
                return pitchedTimeSpan.pitches
            elif offset > pitchedTimeSpan.offset and offset < pitchedTimeSpan.endTime:  # starts after beginning of span
                return pitchedTimeSpan.pitches
        return None
    
    def _pitchIsDissonantAgainstAtLeastOnePitch (self, element, pitch):
        
        if isinstance(element, Verticality):
            chord = element.toChord()
            
        elif isinstance(element, PitchCollection):
            chord = element.toChord
        elif isinstance(element, Chord):
            chord = element
        else: return False
        
        bassPitch = chord.bass()
 
        fourthToBass = self._chordHasIntervalToBass(chord, ['P4', ['A4']])
        pitchBassInterval = interval.Interval (bassPitch, pitch)
        
        if fourthToBass:
            if pitch.name == bassPitch.name or pitchBassInterval.generic.simpleUndirected in [4]: return True 
        
        for pitchV in chord.pitches:
            intervalPV = interval.Interval(pitchV, pitch)
            if intervalPV.generic.simpleUndirected in [2, 7]: return True  
            
        return False
    
    def _pitchIsExplainedAfterOffset(self, analyzedPitch, offset):
        ''' get all analyzed pitches corresponding to id '''
        analyzedPitchList = self.getAnalyzedPitchCorrespondingToId (analyzedPitch.id)
        
        ''' check if analyzed pitch former to offset is explained '''
        for analyzedPitch in analyzedPitchList:
            if analyzedPitch.offset > offset and analyzedPitch.probability == 1:
                return True
        
        return False
    

class PitchCollection():
    ''' class stores and manages information about all pitches collected in a verticality ''' 
    
    def __init__(self, verticality, analyzedPitchList, chordTemplates=None):
        self.analyzedPitchList = analyzedPitchList
        self.verticality = verticality
        
        ''' harmonic information '''
        self.chord = verticality.toChord() 
        self.chordHypothesisList = []
        self.probability = 0
        self.template = None
        self.rootPitch = None 
        self.rep2PitchDictionary = None
               
        if verticality != None and verticality.nextVerticality != None:
            self.duration = verticality.nextVerticality.offset - verticality.offset
        else: self.duration = 0
    
    def addAnalyzedPitch (self, analyzedPitch):
        self.analyzedPitchList.append(analyzedPitch)
        self.setBestHypotheses()
    
    def clone(self):
        
        clonedPitchList = []
        for analyzedPitch in self.analyzedPitchList:
            clonedPitchList.append(analyzedPitch.clone())
        return PitchCollection(self.verticality, clonedPitchList, self.chordTemplates)
    
    def explainPitches(self):
        explanationString = ""
        for analyzedPitch in self.analyzedPitchList:
            explanationString = explanationString + '%s : %s ' % (str(analyzedPitch.pitch), str (analyzedPitch.pitchType) if analyzedPitch.pitchType != None else 'None')
            if analyzedPitch.probability < 1: explanationString = explanationString + "(" + str(analyzedPitch.probability) + ") "
                
        return explanationString    
    
    def getAnalyzedPitch (self, pitch):
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.pitch == pitch:
                return analyzedPitch
        return None
    
    def getAnalyzedPiches (self):
        return self.analyzedPitchList
    
    def getAnalyzedPitchFromClass (self, pitch):
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.pitch.name == pitch.name:
                return analyzedPitch
        return False
    
    def getAnalyzedPitchesBeloningToList (self, analyzedpitchList=[]):
        subset = []
        pitchList = []
        
        ''' get pitches from analyzed pitch '''
        for analyzedPitch in analyzedpitchList:
            pitchList.append(analyzedPitch.pitch)
            
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch in pitchList:
                subset.append(analyzedPitch)
        
        return subset
    
    def getAnalyzedPitchesCorrespondingToLabels (self, labelList):
        subList = []
        
        for analyzedPitch in self.analyzedPitchList: 
            if analyzedPitch.pitchType in labelList:
                subList.append (analyzedPitch)
                
        return subList
    
    def getAnalyzedPitchesCorrespondingToId (self, elementID):
        for analyzedPitch in  self.analyzedPitchList:
            if analyzedPitch.id == elementID:
                return analyzedPitch
        
        return None
                
    def getAnalyzedPitchesNotBeloningToList (self, analyzedpitchList=[]):
        subset = []
        pitchList = []
        
        ''' get pitches from analyzed pitch '''
        for analyzedPitch in analyzedpitchList:
            pitchList.append(analyzedPitch.pitch)
        
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.pitch not in pitchList:
                subset.append(analyzedPitch)
                
        return subset
    
    def getBassPitch (self):
        return self.verticality.toChord().bass()
    
    def getExplainedPitches (self, pitchTypeList=['CN']):
        pitchList = []
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.pitchType in pitchTypeList:
                pitchList.append(analyzedPitch)
        return pitchList
    
    def getHighestResolutionOffest (self):
        dissonantPitchList = self.getExplainedPitches(['PN', 'NN', 'AN', 'EN', 'SU'])
        highestOffset = 0
        for dissonantPitch in dissonantPitchList:
            if highestOffset < dissonantPitch.verticalities[2].offset:
                highestOffset = dissonantPitch.verticalities[2].offset
        
        return highestOffset
    
    def getHypotheses(self): 
        hypothesisList = []
        for analyzedPitch in self.analyzedPitchList:
            if len (analyzedPitch.hypothesisList) > 0:
                for hypothesis in analyzedPitch.hypothesisList:
                    hypothesisList.append(hypothesis)
        
        return hypothesisList
    
    def isExplained (self):
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.explained == False:
                return False
        
        return True
    
    def isNonHarmonicNote (self, pitch):
        pitchExplanation = self.getAnalyzedPitch(pitch)
         
        if not pitchExplanation == None:
            if pitchExplanation.pitchType in ['PN', 'NN', 'AN', 'EN', 'SU'] and pitchExplanation.probability == 1:
                return True
            else: 
                return False
        else: 
            return False
        
    def toChord (self):
        pitchList = []
        for analyzedPitch in self.analyzedPitchList:
            pitchList.append(analyzedPitch.pitch)
            
        return chord.Chord(pitchList)
       
    def getNumberOfConsonantAndDissonantIntervalsImpliedByPitch (self, pitch):
        consonantIntervals = 0
        dissonantIntervals = 0 
        
        bassPitch = self.verticality.toChord().bass()
        
        for analyzedPitch in self.analyzedPitchList:
            
            intervalPV = interval.Interval(analyzedPitch.pitch, pitch)
            genericUndirected = intervalPV.generic.simpleUndirected
            
            if genericUndirected in [2, 7]: 
                dissonantIntervals = dissonantIntervals + 1
                
            elif genericUndirected in [1, 3, 5, 6, 8]:
                consonantIntervals = consonantIntervals + 1
        
            elif genericUndirected in [4]: 
                if bassPitch.name in [pitch.name, bassPitch] and not intervalPV.simpleName == 'A4':
                    dissonantIntervals = dissonantIntervals + 1
                else: consonantIntervals = consonantIntervals + 1
        
        return [consonantIntervals, dissonantIntervals]
        
    def pitchIsConsonantInCollection (self, incoherentPitch):  
        ''' checks if a pitch labeled as a dissonance could be a consonance i.e - this pitch is consonant against other pitches labeled as consonance '''
        ''' make sure that all pitches are explained '''
        if self.isExplained() == False:
            return False
        
        ''' get consonant pitches '''
        consonantPitches = self.getExplainedPitches(['CN'])
        
        ''' TODO Add conditions for fourth against bass '''
        for consonantPitch in consonantPitches:
            intervalPV = interval.Interval(consonantPitch.pitch, incoherentPitch.pitch)
            if intervalPV.generic.simpleUndirected in [2, 4, 7]: 
                return False  
            
        return True
    
    def verticalityWithDissonanceSubstitutionsIsConsonant (self):
        ''' build chord object which contains substitutions for dissonant notes '''
        pitchList = []
        
        for pitchInVerticality in self.verticality.pitchSet:
            
            if self.isNonHarmonicNote(pitchInVerticality) == False:
                ''' if consonant append '''
                pitchList.append(pitchInVerticality) 
            else:
                ''' if dissonant get substitution '''
                substitutionPitch = self.getSubstitutionForDissonantPitch(self.getAnalyzedPitch(pitchInVerticality))
                if substitutionPitch != None: 
                    pitchList.append(substitutionPitch)
                else:
                    pitchList.append(pitchInVerticality)
                 
        chordWithoutSubstitutions = chord.Chord(pitchList)
        
        if self._chordIsConsonant(chordWithoutSubstitutions):
            return True
        else:
            return False
        
    def verticalityWithoutIdentifiedDissonancesisConsonant (self):
        ''' build chord object which contains only consonant notes '''
        pitchList = []
        
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.explained == True and analyzedPitch.pitchType in ['SU', 'PN', 'EN', 'NN', 'AN']:
                pass
            else: pitchList.append(analyzedPitch.pitch)
        
        chordWithoutNHN = chord.Chord(pitchList)
        
        if self._chordIsConsonant(chordWithoutNHN):
            return True
        else:
            return False
        
    def verticalityWithoutPitchListIsConsonant (self, pitch):
        ''' build chord object which contains all pitches except those in list '''
        remainingPitchList = []
        
        for pitchInVerticality in self.verticality.pitchSet:
            if pitchInVerticality != pitch:
                remainingPitchList.append(pitchInVerticality)
        
        chordWithoutNHN = chord.Chord(remainingPitchList)
         
        if chordWithoutNHN.isConsonant():
            return True
        else:
            return False    
        
    def _chordIsConsonant(self, chord):
        if chord.isConsonant():
            return True
        
        elif chord.isDiminishedTriad():
            return True
        
        elif chord.isAugmentedTriad():
            return True
        
        return False 


class Pitch():
    ''' class stores and manages information about individual pitches'''
    ''' these pitches are grouped in a verticality (class AnalyzedPitchCollection)'''
    
    def __init__(self, pitch, verticalities, hypothesisList=[]):
        self.horizontalities = None
        self.elementsStartingList = []
        self.accentuated = None
        self.pitchType = None
        self.pitchSubType = None
        self.verticalities = verticalities
        self.offset = verticalities[1].offset
        self.pitch = pitch
        self.harmonicNote = False
        self.probability = -1
        self.segmentQuarterLength = 0
        # self.isConsonant = False
        self.resolutionOffset = None
        self.preparationOffset = None
        self.preparationPitch = None
        self.resolutionPitch = None 
        self.preparationPitchID = None
        self.resolutionPitchID = None
        self.hypothesisList = hypothesisList
        self.explained = False
        self.hypothesesChecked = False
        if len (hypothesisList) > 0:  self.setBestHypothesis()
        self.id = None
        self.part = None
        self.voice = None
        self.work = None
        self.attack = False
        
    def clone (self): 
        analzedPitch = Pitch(self.pitch, self.verticalities, self.hypothesisList)
        analzedPitch.horizontalities = self.horizontalities
        analzedPitch.elementsStartingList = self.elementsStartingList
        analzedPitch.accentuated = self.accentuated
        analzedPitch.pitchType = self.pitchType
        analzedPitch.pitchSubType = self.pitchSubType
        analzedPitch.verticalities = self.verticalities
        analzedPitch.offset = self.offset
        analzedPitch.pitch = self.pitch
        analzedPitch.harmonicNote = self.harmonicNote
        analzedPitch.probability = self.probability
        # analzedPitch.isConsonant = self.isConsonant
        analzedPitch.resolutionOffset = self.resolutionOffset
        analzedPitch.preparationOffset = self.preparationOffset
        analzedPitch.preparationPitch = self.preparationPitch
        analzedPitch.resolutionPitch = self.resolutionPitch 
        analzedPitch.hypothesisList = list (self.hypothesisList)
        analzedPitch.explained = self.explained
        analzedPitch.id = self.id
        analzedPitch.resolutionPitchID = self.resolutionPitchID
        analzedPitch.preparationPitchID = self.preparationPitchID
        return analzedPitch
    
    def getBestHypotheses (self):
        ''' returns list with best hypotheses '''
        bestHypothesisList = []
        
        if len (self.hypothesisList) == 0: return bestHypothesisList
        self.hypothesisList.sort(key=lambda x: x.probability, reverse=True)    
        bestProbability = self.hypothesisList[0].probability
        
        for hypothesis in self.hypothesisList:
            if hypothesis.probability == bestProbability:
                bestHypothesisList.append(hypothesis)
        
        if len (bestHypothesisList) <= 1: return bestHypothesisList 
        
        ''' for every dissonance type get longest distance between v0 and v1 ''' 
        typeHypothesisList = []
        for pitchType in ['PN', 'NN', 'AN', 'EN', 'SU']:
            distanceV0V1 = 0
            typeHypothesis = None
            for hypothesis in bestHypothesisList:
                if hypothesis.pitchType == pitchType:
                    if hypothesis.verticalities[1].offset - hypothesis.verticalities [0].offset >= distanceV0V1: typeHypothesis = hypothesis
            
            if typeHypothesis != None: typeHypothesisList.append(typeHypothesis)
            
        return typeHypothesisList       
            
    def getAnalyzedPitchTimeSpan(self):
        horizontality = self.getHorizontality()
        return horizontality.timespans[1] 
    
    def getConstitutivePitch(self):
        ''' either the resolution pitch either the preparation pitch '''        
        
        if self.pitchType in ['SU']:
            return self.resolutionPitch
        elif self.pitchType in ['PN', 'NN', 'AN', 'EN'] and self.accentuated == True:
            return self.resolutionPitch
        else:
            return self.preparationPitch
    
    def getType (self): 
        return self.nhnType
    
    def isIdenticalWithThisAnalyzedPitch (self, analyzedPitch):  
        ''' test on id and basic analytical information '''
       
        if analyzedPitch.id != self.id: return False
        if analyzedPitch.pitchType != self.pitchType: return False
        if analyzedPitch.pitchSubType != self.pitchSubType: return False   
        if analyzedPitch.probability != self.probability: return False 
         
        return True
 
    def show(self): 
        pitchString = "Offset: " + str(self.verticalities[1].offset) + ", pitch: " + str(self.pitch) + ", type: " + str(self.pitchType) + ", subtype: " + str(self.pitchSubType) + ", probability: " + str(self.probability) 
        
        return pitchString 
    
    def _getPart(self, nhVerticality, pitch):
        allElements = []
        elementContainingPitch = None
         
        for element in nhVerticality.startTimespans:
            allElements.append(element)
            
        for element in nhVerticality.overlapTimespans:
            allElements.append(element)
        
        for element in allElements:
            if element.element.id == self.id: 
                elementContainingPitch = element
                break
        
        ''' get Part '''
        if elementContainingPitch != None: 
            return elementContainingPitch.part
        else:
            return None  
        
    def _getVoice (self, nhVerticality):
        allElements = []
        elementContainingPitch = None
         
        for element in nhVerticality.startTimespans:
            allElements.append(element)
            
        for element in nhVerticality.overlapTimespans:
            allElements.append(element)
        
        for element in allElements:
            if element.element.id == self.id: 
                elementContainingPitch = element
                break
        
        ''' get all parents  '''
        if elementContainingPitch == None: return None
        parents = elementContainingPitch.parentage 
        
        ''' loop over parentage, check if included in voice '''
        for parent in parents:
            if isinstance(parent, stream.Voice):
                return parent
        
        return None
    
    def _getElementsContainingPitch (self, nhVerticality, pitch): 
        elementList = []
        allElements = []
        
        for element in nhVerticality.startTimespans:
            allElements.append(element.element)
            
        for element in nhVerticality.overlapTimespans:
            allElements.append(element.element)
        
        for element in allElements:
            if isinstance(element, note.Note):
                if element.pitch.nameWithOctave == pitch.nameWithOctave:
                    elementList.append(element)
            if isinstance(element, chord.Chord):
                if pitch in element.pitches:
                    elementList.append(element)
        return elementList
    
    def _getId (self):
        
        ''' TODO: best solution: when creating tree, create id which allows to map id '''
        ''' set id ''' 
        if self.verticalities == None:
            return None
        
        elementsContainingPitch = self._getElementsContainingPitch(self.verticalities[1], self.pitch)
        
        for element in elementsContainingPitch:
            if isinstance(element, chord.Chord):continue
            return  element.pitch.id  # change to take chords into account
        return None
    
    def _getVerticalities (self):
        if self.verticalities != None:
            return self.verticalities
        else: 
            bestHyp = self.getBestHypotheses()
            return bestHyp[0].verticalities if bestHyp != None else None
        
