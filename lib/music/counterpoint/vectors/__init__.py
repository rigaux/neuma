# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         vectrors.py
# Purpose:      implement theory of harmonic vectors
# 
#
# Copyright:    Christophe Guillotel-Nothmann Copyright © 2017
#-------------------------------------------------------------------------------
''' imports ''' 
from music21 import  stream, graph, note, chord, clef, interval, key
from music21.interval import Direction
from collections import OrderedDict
from _operator import and_
#from graphs import progressionScatterPlot
#import graphs
import copy, logging 

class FundamentalBass (object):
    def __init__ (self, stream):
        self.fundamentalBass = copy.deepcopy(stream) 
        self.fundamentalBass = self.fundamentalBass.chordify()
        
        ''' create new layer with fundamental bass '''
        for element in self.fundamentalBass.recurse():
            if chord.Chord in element.classSet:
                rootPitch = element.sortAscending(inPlace=False).findRoot() 
           
                if rootPitch.accidental != None:
                    rootPitch.accidental.displayStatus = None 
                   
                ''' ref octave = oct3 '''
                rootPitch.octave = 3     
                    
                rootNote = note.Note(rootPitch)
                rootNote.duration.quarterLength = element.duration.quarterLength
                self.fundamentalBass.recurse().replace(element, rootNote, recurse = True)             
       
        ''' change key(s) ''' 
        for clefElement in self.fundamentalBass.recurse().getElementsByClass(clef.Clef):
            self.fundamentalBass.recurse().replace(clefElement, self.fundamentalBass.bestClef(recurse=True))
        
        #for keyElement in self.fundamentalBass.recurse().getElementsByClass(key.Key):
        #    logging.info (keyElement.alteredPitches)
            
        self.fundamentalBass.id = "Fundamental bass"
        self.fundamentalBass.partName = "Fundamental bass"
        self.fundamentalBass.partAbbreviation = "F.B." 
        
    def getFundamentalBass(self):
        stream1 = stream.Part() 
        stream1.append(self.fundamentalBass)
        
        return stream1
 

class VectorAnalysis(object):    
    
    def __init__(self, stream):
        ''' store stream '''
        self.stream = stream
        
        ''' get stream with only notes and rests'''
        #self.fundamentalBassStream = FundamentalBass(stream).getFundamentalBass()
        self.notesAndRestsStream = stream.flat.notesAndRests
        
        ''' get intervals '''
        self.vectorList = self._computeVectors() 
        
        
        ''' set vector categories '''
        self.vectorPopulation = self._setVectorCategories()
        

        
        
    def show(self, representationType = "text", percents = False):
        population = self.vectorPopulation
        ratio = len(self.vectorList)
        
        if representationType == "text":
            logging.info (population.name + ': ' + str (population.occurrence))
            
            if percents == True:
                ratio = self.vectorPopulation.occurrence
            
            for vectorCategory in population.subCategories:
                logging.info ('\t' + str (vectorCategory.name) + ': ' + str(vectorCategory.occurrence/ratio))
                for interval in vectorCategory.subCategories:
                    logging.info  ('\t\t' + str(interval.name) + ': ' + str(interval.occurrence/ratio))
                    for intervalType in interval.subCategories:
                        logging.info  ('\t\t\t' + str (intervalType.name) + ': ' + str(intervalType.occurrence/ratio))
                        
        elif representationType == 'simpleGraph':
            
            DV4 = round (len(self.getSubSet(generic = 4))/ratio, 2)
            DV3 = round (len(self.getSubSet(generic = -3))/ratio, 2)
            DV2 = round (len(self.getSubSet(generic = 2))/ratio, 2)
                      
            SV4 = round (len(self.getSubSet(generic = -4))/ratio, 2)
            SV3 = round (len(self.getSubSet(generic = 3))/ratio, 2)
            SV2 = round (len(self.getSubSet(generic = -2))/ratio, 2)
                      
            #graphs.SimpleVectorGraph((DV4, SV4), (DV3, SV3), (DV2, SV2)) 
            
        elif representationType == 'tonalProfile':
            self.getProgressionScatter()
            
            
        
    def getSubSet (self, generic=None, bassProgression =None):
        vectorList = []
        
        
        for vector in self.vectorList:
            if generic != None:
                if vector.vector.generic.directed == generic:
                    vectorList.append(vector) 
            if bassProgression != None:
                if bassProgression[0].name == vector.noteStart.name and \
                bassProgression[1].name == vector.noteEnd.name:
                    vectorList.append(vector)
                           
                    
        return vectorList
    
    
        
    def getDistance (self):
        cycle5Dictionary = {'C-':-7, 'G-':-6, 'D-':-5, 'A-':-4, 'E-':-3, 'B-':-2, 'F':-1,'C':0 ,'G':1,'D':2, 'A':3, 'E':4, 'B':5, 'F#':6, 'C#':7, 'G#':8, 'D#':9, 'A#':10, 'E#':11}
        minDegreeStart = 11
        maxDegreeStart = -7
        
        for vector in self.vectorList:
            degreeStart = cycle5Dictionary[vector.noteStart.name]
            logging.info (degreeStart)
            if degreeStart < minDegreeStart:
                minDegreeStart = degreeStart
            if degreeStart > maxDegreeStart:
                maxDegreeStart = degreeStart
                
            
                
        
        
        return maxDegreeStart-minDegreeStart  
        
        
        
    def getProgressionScatter(self):
        
        cycle5Dictionary = {-7:'c-', -6:'g-', -5:'d-', -4:'a-', -3:'e-', -2:'b-', -1:'f', 0:'c' , 1:'g', 2:'d', 3:'a', 4:'e', 5:'b', 6:'f#', 7:'c#', 8:'g#', 9:'d#', 10:'a#', 11:'e#'}
        yCoordinates = []
        xCoordinates = []
        tickLabels = tuple(cycle5Dictionary.values())
        values = [] 
        vectors = []
        
        ''' create x- y-coordinates and get values '''      
        for key1 in cycle5Dictionary.keys():
            for key2 in cycle5Dictionary.keys(): 
                yCoordinates.append(key1) 
                xCoordinates.append(key2) 
                
                note1 = note.Note(cycle5Dictionary[key1])
                note2 = note.Note(cycle5Dictionary[key2])
                subset = self.getSubSet(bassProgression= [note1, note2])
                
                if len(subset) == 0:
                    vectors.append(None)
                else: 
                    vectors.append(subset[0])
                        
                values.append(len (subset)) 
                
                
        ''' create plot '''
                
        #progressionScatterPlot(yCoordinates, xCoordinates, values, tickLabels, vectors)
        
            
            
                    
            
            
             
    

        
        
    
    
    def _computeVectors (self):
    
        vectorList = []    
        ''' get melodic intervals '''
        for noteRestListCounter in range(len(self.notesAndRestsStream)-1):
            self.notesAndRestsStream[noteRestListCounter]
            
            NoteOrRest1 = self.notesAndRestsStream[noteRestListCounter]
            NoteOrRest2 = self.notesAndRestsStream[noteRestListCounter+1]
            
            if NoteOrRest1.isNote and NoteOrRest2.isNote:
                fbInterval = interval.Interval(NoteOrRest1, NoteOrRest2) 
                
                vector = HarmonicVector(fbInterval)
                vectorList.append(vector) 
                
                logging.info (vector.vector)
        return vectorList
    
    
    def _setVectorCategories (self):
      
        vectorPopulation = VectorCategory ("population")
       
        
        ''' VD / VS '''
        for vector in self.vectorList:
            vectorPopulation.addToSubCategory(vector, vector.category)
            vectorPopulation.vectorList.append(vector)
            vectorPopulation.setOccurence()
            
        
        ''' intervals '''
        vectorTypeCategories = vectorPopulation.subCategories
        for vectorTypeCategory in vectorTypeCategories:
            for vector in vectorTypeCategory.vectorList:
                vectorTypeCategory.addToSubCategory (vector, vector.vector.generic.directed)  
                
                
        
        ''' interval's nature '''
        vectorTypeCategories = vectorPopulation.subCategories
        for vectorTypeCategory in vectorTypeCategories:
            for vectorIntervalCategroy in vectorTypeCategory.subCategories:
                for vector in vectorIntervalCategroy.vectorList:
                    vectorIntervalCategroy.addToSubCategory(vector, vector.vector.specificName) 
                    
        return vectorPopulation
                
        
    
    #def getVectorCategory (self, vectorCategory):
    #    vectorList =[] #

    #    if isinstance(vectorCategory, interval.Interval):
    #        for vector in self.vectorList: 
    #            if vector.vector == vectorCategory.generic.directed:
    #                vectorList.append(vector)
    #    
    #    return vectorList 
    
    
    def getAnnotatedFundamentalBass (self):
        for vector in self.vectorList:
            vector.getNote1().lyric = str(vector.getDirectionArrow()) + str(vector.getInterval())
        return self.stream
    
    
            
    
class VectorCategory ():
    def __init__ (self, categoryName):
        self.name  = categoryName
        self.vectorList = []
        self.occurrence = None 
        self.subCategories = [] 
        
    def addToSubCategory(self, vector, subCategoryName):
        subCategory = self.getSubCategory (subCategoryName)
        if subCategory == None:
            subCategory = VectorCategory(subCategoryName)
            self.subCategories.append(subCategory)
        
        subCategory.vectorList.append(vector)
        subCategory.setOccurence()
        
        
    def setOccurence (self):
        self.occurrence = len (self.vectorList)
    
    
    def getSubCategory (self, subCategoryName):
        for category in self.subCategories:
            if category.name == subCategoryName:
                return category
        
        return None
             
        
                 
            
class HarmonicVector (object):
    def __init__(self, interval):
      
        self.noteStart = interval.noteStart
        self.noteEnd = interval.noteEnd
        self.vector = self._setVector(interval) ## 
        self.category = self._setCategory()
        self.isSubstitution =  self._setIsPrincipal()
        self.direction = self.vector.diatonic.direction
        
    
    def _setVector (self, fbProgression):        
        ''' if interval > fourth then complementary '''
        if fbProgression.generic.directed > 4:
            ''' create complement interval '''
            intervalS = interval.Interval ("-"+fbProgression.complement.simpleName)
            
            return intervalS
        elif fbProgression.generic.directed < -4:
            return fbProgression.complement
            
            
        else:
            return fbProgression
    
    def _setCategory (self):
        if self.vector.generic.directed in [4, 2, -3]:
            return "dominant"
        elif self.vector.generic.directed in [-4, -2, 3]:
            return "subdominant"
    
    def _setIsPrincipal (self):
        if self.vector.generic.directed in [4, -4]:
            return True
        else: 
            return False
    
    def getNote1 (self):
        return self.noteStart
    
    def getNote2 (self):
        return self.noteEnd
    
    def getInterval (self):
        vector = self.vector.diatonic.directedSimpleName
        
        return vector
        
    def getDirectionArrow (self):
        arrow = ""
        if self.category == "dominant":
            arrow = "=>" 
        elif self.category == "subdominant":
            arrow = "<="
        
        return arrow
        
    
        
        
         
        
        
        
              
        
        
     
        
    ''' identify aba patterns '''
    
    ''' identify cadence formulas '''
    ''' +2 +4 '''
        
        
 
        
        
    ''' identify specifc subdominant patterns  ''' 