# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         pitchCollections.py
# Purpose:      dissonance analysis
# 
#
# Copyright:    Christophe Guillotel-Nothmann Copyright © 2017
#-------------------------------------------------------------------------------


''' imports '''
from music21 import chord, pitch, note
from music21.interval import Interval
import copy, logging

class H_AndNhnCollection():
    ''' class stores and manages information about all pitches collected in a verticality ''' 
    
    def __init__(self, verticality,  analyzedPitchList):
        self.analyzedPitchList = analyzedPitchList
        self.verticality = verticality 
        self.root = None
    
    def addAnalyzedPitch (self, analyzedPitch):
        self.analyzedPitchList.append(analyzedPitch)
    
    def correctIncoherentPitches(self):
        correction = True
        
        while correction == True:
        
            ''' get incoherent pitches (i.e. pitches that are consonant against other pitches labeld as consonances )'''
            incoherentPitchList = self.getIncoherentPitches()
            
            ''' check if pitches in list could be consonances '''
            for incoherentPitch in incoherentPitchList:
                if self.pitchIsConsonantInCollection (incoherentPitch): 
                    ''' change analysis '''
                    incoherentPitch.reinterpretAsConsonance()
                    logging.info ('Test (correctIncoherentPitches): Corrected one pitch:  ' + incoherentPitch.show())
                    correction = True ### change this
                    break
            
            correction = False
                    
                
                
                
    def confirmHypothesis (self, hypothesis, analyzedPitch, concurrentHypotheses = False):
        for pitch in self.analyzedPitchList:
            if hypothesis in pitch.hypothesisList:
                if concurrentHypotheses == True:
                    pitch.confirmHypothesis(hypothesis, analyzedPitch, concurrentHypotheses)
                else:
                    pitch.hypothesisList.remove(hypothesis)
    
    def explainPitches(self):
        explanationString = ""
        for analyzedPitch in self.analyzedPitchList:
            explanationString = explanationString + str(analyzedPitch.pitch) + ": " 
            if analyzedPitch.pitchType != None:
                explanationString = explanationString + str(analyzedPitch.pitchType) + " "
            elif len (analyzedPitch.hypothesisList) > 0:
                for hypothesis in analyzedPitch.hypothesisList :
                    explanationString = explanationString + str(hypothesis.show()) + " ? "
            else : explanationString = explanationString + 'Not explained' + " "
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
    
    def getAnalyzedPitchesBeloningToList (self, analyzedpitchList = []):
        subset = []
        pitchList = []
        
        
        ''' get pitches from analyzed pitch '''
        for analyzedPitch in analyzedpitchList:
            pitchList.append(analyzedPitch.pitch)
            
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch in pitchList:
                subset.append(analyzedPitch)
        
        return subset
    
    def getAnalyzedPitchesCorrespondingToId (self, elementID):
        for analyzedPitch in  self.analyzedPitchList:
            if analyzedPitch.id == elementID:
                return analyzedPitch
        
        return None
            
                
    def getAnalyzedPitchesNotBeloningToList (self, analyzedpitchList = []):
        subset = []
        pitchList = []
        
        ''' get pitches from analyzed pitch '''
        for analyzedPitch in analyzedpitchList:
            pitchList.append(analyzedPitch.pitch)
        
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.pitch not in pitchList:
                subset.append(analyzedPitch)
                
        return subset
    
    def getExplainedPitches (self, pitchTypeList = ['CN']):
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
    
    def getIncoherentPitches (self):
        ''' check if analysis provided is consistent, returns a list of pitches which seem incoherent '''
        ''' if not try to correct '''
        incoherentPitchList = []
        
        ''' make sure that all pitches are explained '''
        if self.isExplained() == False:
            return incoherentPitchList
        
        ''' test 1: if two labeled dissonances are dissonant together, one is necessary wrong '''
        ''' get all analyzed pitches identifies as dissonances '''
        pitchList_I = self.getExplainedPitches(['SU', 'NN', 'PN', 'AN', 'EN'])
        pitchList_II = pitchList_I
       
        
        for dissonantPitch_I in pitchList_I:
            for dissonantPitch_II in pitchList_II:
                if dissonantPitch_I == dissonantPitch_II: continue
                
                dissonantInt =  Interval(dissonantPitch_I.pitch, dissonantPitch_II.pitch)
                if dissonantInt.isConsonant() == False:
                    if dissonantPitch_I not in incoherentPitchList: incoherentPitchList.append(dissonantPitch_I)
                    if dissonantPitch_II not in incoherentPitchList: incoherentPitchList.append(dissonantPitch_II)
                    
        
        ''' TOOO (?) test 2: if two labeled consonances are dissonant together, one is necessary wrong '''
        return incoherentPitchList
    
    def getRootPitch (self, pitchFilter = ['CN', 'PN', 'AN', 'NN']):
        pitchSubset = []
        explainedPitcheList =self.getExplainedPitches(pitchFilter)
   
        ''' handle substitutions for dissonant pitches '''
        for explainedPitch in explainedPitcheList:
            if explainedPitch.pitchType == 'CN':
                pitchSubset.append(explainedPitch.pitch)
            else:
                substitution = self.getSubstitutionForDissonantPitch(explainedPitch)
                if substitution != None: pitchSubset.append(substitution.pitch)
        
        
        if len (pitchSubset) == 0:
            ''' build chord '''
            return None
        else:
            collectionChord = copy.deepcopy(chord.Chord(pitchSubset))
            chordRoot = collectionChord.root()
            ''' as a convention use octave 3 '''
            chordRoot.octave = 3
            
            self.root = chordRoot
            return chordRoot
    
    def getSubstitutionForDissonantPitch (self, pitch):
        if pitch.accentuated:
            if pitch.pitchType in ['PN', 'NN']:
                return pitch.resolutionPitch
            
            else:
                return None
        else:
            if pitch.pitchType in ['PN', 'NN']:
                return pitch.preparationPitch
            elif pitch.pitchType in ['AN']:
                return pitch.preparationPitch
            else:
                return None
            
    def getUnexplainedPitches(self):
        '''' TODO : remove and merge with getExplainedPitches'''
        unexplainedPitchList = []
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.isExplained() == False:  
                unexplainedPitchList.append(analyzedPitch)
        return unexplainedPitchList
    
    
    def isExplained (self):
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.isExplained() == False:
                return False
        
        return True
    
    
    def isNonHarmonicNote (self, pitch):
        pitchExplanation = self.getAnalyzedPitch(pitch)
        
        if not pitchExplanation == None:
            if pitchExplanation.pitchType in ['PN', 'NN', 'AN', 'EN', 'SU']:
                return True
            else: 
                return False
        else: 
            return False
        
    def pitchIsConsonantInCollection (self, incoherentPitch):  
        ''' checks if a pitch labeled as a dissonance could be a consonance i.e - this pitch is consonant against other pitches labeled as consonance '''
        ''' make sure that all pitches are explained '''
        if self.isExplained() == False:
            return False
        
        ''' get consonant pitches '''
        consonantPitches = self.getExplainedPitches(['CN'])
        
        
        ''' TODO Add conditions for fourth against bass '''
        for consonantPitch in consonantPitches:
            intervalPV = Interval(consonantPitch.pitch, incoherentPitch.pitch)
            if intervalPV.generic.simpleUndirected in [2, 4, 7]: 
                return False  
            
        return True
    
    def updateExplanations (self, hypothesis = None):
        ''' infers additional knowledge from analyzed pitches and validated hypothesis '''
        
        
        ''' test 1: if this specific pitch is removed from collection, all other pitches are consonant '''
        if hypothesis != None:
            if self.verticalityWithoutPitchListIsConsonant(hypothesis.pitch):
                for analyzedPitch in self.analyzedPitchList:
                    
                    if analyzedPitch.pitch != hypothesis.pitch and analyzedPitch.pitchType != 'CN':
                        pitchType = analyzedPitch.pitchType
                        analyzedPitch.pitchType = "CN"
                        analyzedPitch.certainty = 1
                        ''' remove concurrent hypotheses '''
                        analyzedPitch.hypothesisList.clear()
                        
                        if pitchType == None:
                            logging.info ('Test 1: Could identify one additional pitch:  ' + analyzedPitch.show())
                        else:
                            logging.info ('Test 1: Corrected one pitch:  ' + analyzedPitch.show())
        
        ''' test 2: if all dissonant notes are removed, verticality is consonant'''
        if self.verticalityWithoutNHNisConsonant():
            for analyzedPitch in self.analyzedPitchList:
                
                
                if analyzedPitch.pitchType == None:
                    analyzedPitch.pitchType = "CN"
                    analyzedPitch.certainty = 1
                    analyzedPitch.hypothesisList.clear()
                    logging.info ('Test 2: Could identify one additional pitch: ' + analyzedPitch.show())
            
                    
                    
        ''' test 3: if verticality with substituted dissonances is consonant '''      
        if self.verticalityWithDissonanceSubstitutionsIsConsonant():
            for analyzedPitch in self.analyzedPitchList:
                if analyzedPitch.pitchType == None:
                    analyzedPitch.pitchType = "CN"
                    analyzedPitch.certainty = 1
                    analyzedPitch.hypothesisList.clear()
                    logging.info ('Test 3: Could identify one additional pitch: ' + analyzedPitch.show()) 
                    
       
                    
    
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
        
    def verticalityWithoutNHNisConsonant (self):
        ''' build chord object which contains only consonant notes '''
        pitchList = []
        
        for pitchInVerticality in self.verticality.pitchSet:
            if self.isNonHarmonicNote(pitchInVerticality) == False:
                pitchList.append(pitchInVerticality)
        
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
            
    


class AnalyzedPitch():
    ''' class stores and manages information about individual pitches'''
    ''' these pitches are grouped in a verticality (class H_AndNhnCollection)'''
    
    def __init__(self, horiozontalities, verticalities, accentuated, pitch, pitchType=None, pitchSubType = None, certainty = 0):
        self.verticalities = None
        self.horizontalities = None
        self.offset = verticalities[1].offset
        self.elementsStartingList = []
        self.accentuated = accentuated
        self.pitchType = None
        self.pitchSubType = None
        self.pitch = pitch
        self.certainty = certainty
        self.harmonicNote = False
        self.isConsonant = False
        self.resolutionOffset = None
        self.preparationPitch = None
        self.resolutionPitch = None# 
        self.hypothesisList = []  
        
        for element in verticalities[1].startTimespans:
            self.elementsStartingList.append (element.element)
        
        
        if certainty == 1:
            self.verticalities = verticalities
            self.horizontalities = horiozontalities
            self.pitchType = pitchType
            self.pitchSubType = pitchSubType
        elif certainty >0 and certainty < 1:
            self.hypothesisList.append(Hypothesis(verticalities, pitch, pitchType, pitchSubType, certainty))
            self.verticalities = [None, verticalities[1], None]
            self.horizontalities = [None, horiozontalities[1], None]
        
        elif certainty == 0:
            self.verticalities = [None, verticalities[1], None]
            self.horizontalities = [None, horiozontalities[1], None]
            
        if pitchType in ['PN', 'NN', 'AN', 'EN', 'SU']:
            self.preparationPitch = horiozontalities[0]
            self.resolutionPitch = horiozontalities[2]
        self.id = self._getId()
        
       
    
    def addHypothesis (self, hypothesis):
        self.hypothesisList.append(hypothesis)         

    def confirmHypothesis (self, hypothesis, analyzedPitch, concurrentHypothesis=True): 
        self.pitchType = analyzedPitch.pitchType
        self.pitchSubType = analyzedPitch.pitchSubType  
        self.certainty = analyzedPitch.certainty
        self.verticalities = analyzedPitch.verticalities
        self.resolutionOffset = analyzedPitch.verticalities[2]
        self.preparationPitch = analyzedPitch.preparationPitch
        self.resolutionPitch = analyzedPitch.resolutionPitch
        
        if concurrentHypothesis == None :
            self.hypothesisList.clear()
        else:
            self.hypothesisList.remove(hypothesis)
            
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
    
    def isExplained(self):
        if self.pitchType != None and self.certainty == 1:
            return True
        
        return False
     
    def reinterpretAsConsonance (self):
        ''' (?) TODO: save olter interpretations ? '''
        
        self.pitchType = 'CN'
        self.pitchSubType = None 
        self.certainty = 1 
        self.isConsonant = True
        self.resolutionOffset = None
        self.preparationPitch = None
        self.resolutionPitch = None# 
        self.hypothesisList = []  
         
    def show(self): 
        pitchString = "Offset: " + str(self.verticalities[1].offset) +  ", pitch: " + str(self.pitch) + ", type: " + str(self.pitchType) + ", subtype: " + str(self.pitchSubType) + ", certainty: " + str(self.certainty) 
        
        return pitchString 
    
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
    
    def _getId (self):
        ''' set id ''' 
        elementsContainingPitch = self._getElementsContainingPitch(self.verticalities[1], self.pitch)
        
        for element in elementsContainingPitch:
            return  element.id
        return None

class Hypothesis ():
    ''' class stores and manages information about hypotheses'''
    
    def __init__(self, verticalities, pitch, pitchType, pitchSubType, certainty):
        self.verticalities = verticalities
        self.pitchType = pitchType
        self.pitchSubType = pitchSubType
        self.pitch = pitch
        self.certainty = certainty    
    
    def show(self):
        ''' displays hypothesis as string'''
        hypothesisString = "Offset: " + str(self.verticalities[1].offset) +  ", pitch: " + str(self.pitch) + ", type: " + str(self.pitchType) + ", subtype: " + str(self.pitchSubType) + ", certainty: " + str(self.certainty) 
        return hypothesisString
