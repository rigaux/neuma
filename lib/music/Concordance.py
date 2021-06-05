'''
Created on Jun 14, 2017

@author: libreservice
'''
import numpy as np
from music21 import note, stream, corpus, tree, chord, pitch

score = corpus.parse('bwv66.6')

class ListeAccords:

    '''
    Prend en attribut un objet Stream, les paramètres d'instrument et d'accord:

    instrument = [liste des partiels, liste des amplitudes, liste des largeurs spectrales].
    temperament = [Nom de la note de référence à partir de laquelle va être fait l'accord, liste des déviations en cents des 11 notes
                    restantes par rapport au tempérament tempéré]

    L'attribut 'grandeursHarmoniques' va stoker sous forme de liste les informations de concordance et de cohérence de chaque accord,
    ainsi que son nombre de notes
    L'attribut normalisation va servir à normaliser les concordances des unissons de n notes
    '''
    def __init__(self, stream, partiels, sigma, decroissance):
        self.stream = stream
        self.tree = tree.fromStream.asTimespans(stream, flatten=True,classList=(note.Note, chord.Chord))
        self.instrument = [partiels, sigma, decroissance]
        self.temperament = [0,0,0,0,0,0,0,0,0,0,0,0]
                            #[0,0,0,0,0,0,0,0,0,0,0,0]#Tempéré#
                            #[0,-10,+4,-6,+8,-2,-12,+2,-8,+6,-4,+10]#Pythagore
                            #[0,+17,-7,+10,-14,+3,+20,-3,+14,-10,+7,-17]#Mésotonique 1/4
                            #[]#Mésotonique 1/6
                            #[0,-29,+4,+16,-14,-2,-31,+2,-27,-16,-4,-12]#Juste Majeur
                            #[0,12,+4,+16,-13,-2,+32,+2,+14,-17,+18,-11]#Juste mineur

        self.noteDeReferencePourLeTunning = "C4"
        self.grandeursHarmoniques = []
        self.normalisation = [2,3,4,5,6,7,8]
        self.ConcordanceCoherenceConcordanceOrdre3Liste()

    def spectre(self,f0):
        '''Cette méthode va être appelée dans la classe Accord, mais elle est définie ici car le seul attribut d'objet
         qui en est paramètre est l'instrument'''
        n = np.arange(0,16,0.001)
        S = np.zeros(np.shape(n))
        for i, elt in enumerate([j for j in range(0, self.instrument[0])]):
            S += (1/(i + 1)**self.instrument[2]) * np.exp(-(n - np.log2(elt * f0))**2 / (2 * (self.instrument[1])**2))
        return S

    def Normalisation(self):
        """ Calcule la concordance d'ordre n de l'unisson à n notes, pour n allant de 2 à 8"""

        self.normalisation[0] = np.sum(self.spectre(100)*self.spectre(100))
        self.normalisation[1] = (np.sum(self.spectre(100)*self.spectre(100)*self.spectre(100)))**(2/3)
        self.normalisation[2] = (np.sum(self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)))**(2/4)
        self.normalisation[3] = (np.sum(self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)))**(2/5)
        self.normalisation[4] = (np.sum(self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)))**(2/6)
        self.normalisation[5] = (np.sum(self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)))**(2/7)
        self.normalisation[6] = (np.sum(self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)*self.spectre(100)))**(2/8)

    def frequenceAvecTemperament(self,pitch1):
        """Fonction qui prend en entrée un pitch pour renvoyer une fréquence, en tenant compte du tempérament"""

        pitchRef = pitch.Pitch(self.noteDeReferencePourLeTunning)
        pitch1.microtone = self.temperament[(pitch1.pitchClass - pitchRef.pitchClass)%12]
        return pitch1.frequency

    def ConcordanceCoherenceConcordanceOrdre3Liste (self):
        ''' Transforme chaque verticalité en objet Accord, calcule la concordance, la cohérence et les concordances multiples, et stocke les résultats
        sous forme de liste d'Accords"
        '''
        self.Normalisation()

        for verticality in self.tree.iterateVerticalities():
            v = Accord(verticality, self.instrument, self.normalisation, self.temperament,
                       self.noteDeReferencePourLeTunning)
            v.identifiant = verticality.startTimespans[0].element.id

            v.ListeHauteursAvecMultiplicite()
            v.ListeConcordanceDesIntervallesDansAccord()
            v.NombreDeNotes()
            if v.nombreDeNotes>=2:
                v.Concordance()
                if v.nombreDeNotes>=3:
                    v.Coherence()
                    v.ConcordanceOrdre3()
                    if v.nombreDeNotes>=4:
                        v.ConcordanceTotale()
                    else:
                        v.concordanceTotale = v.concordanceOrdre3
                else:
                    v.concordanceTotale = v.concordance
            self.grandeursHarmoniques.append(v)

    def getAnnotatedStream(self, resultList = ['concordance']):
        for gH in self.grandeursHarmoniques:
            if gH.verticality.bassTimespan is not None :
                element = gH.verticality.bassTimespan.element
                if element.isNote or element.isChord:
                    dataString = ""
                    if 'concordance' in resultList:
                        if dataString != '': dataString + " "
                        dataString += str(round(gH.concordance,2))
                    if 'concordanceOrdre3' in resultList:
                        if dataString != '': dataString + " "
                        dataString += str(round(gH.concordanceOrdre3,2))
                    if 'cohérence' in resultList:
                        if dataString != '': dataString + " "
                        dataString += str (round(gH.coherence,2))
                element.lyric = dataString
        return tree.toStream.partwise(self.tree, self.stream)

    def moyenneConcordance (self):
        l = []
        for accord in self.grandeursHarmoniques:
            l.append(accord.concordance)
        return np.mean(l)

    def moyenneCoherence (self):
        l = []
        for accord in self.grandeursHarmoniques:
            l.append(accord.coherence)
        return np.mean(l)

    def moyenneConcordanceTotale (self):
        l = []
        for accord in self.grandeursHarmoniques:
            l.append(accord.concordanceTotale)
        return np.mean(l)

    def moyenneConcordanceOrdre3 (self):
        l = []
        for accord in self.grandeursHarmoniques:
            l.append(accord.concordanceOrdre3)
        return np.mean(l)


    def offsetList (self):
        '''Donne la liste de tous les offsets des verticalités'''
        l = []
        for verticality in self.tree.iterateVerticalities():
            v = Accord(verticality)
            l.append(v.offset)
        return l

    def idList (self):
        '''Donne la liste des identifiants des verticalités'''
        l = []
        for verticality in self.tree.iterateVerticalities():
            v = Accord(verticality)
            l.append(v.id)
        return l


class Accord(ListeAccords):
    '''
    Classe qui traite les verticalités en héritant de l'instrument et de la méthode spectre de la classe ListeAccords,
    et ayant comme attributs supplémentaires les grandeurs liés à la concordance
    Faiblesse pour l'instant : l'arbre de la classe mère est vide, un attribut 'verticality' vient le remplacer
    '''
    def __init__(self, verticality, instrument, normalisation, temperament, noteDeReferencePourLeTunning):# verticality
        self.instrument = instrument
        self.temperament = temperament
        self.noteDeReferencePourLeTunning = noteDeReferencePourLeTunning
        self.normalisation = normalisation
        self.listeHauteursAvecMultiplicite = []
        self.listeConcordanceDesIntervallesDansAccord = []
        self.verticality = verticality
        self.concordance = 0
        self.coherence = 0
        self.concordanceTotale = 1
        self.concordanceOrdre3 = 0
        self.identifiant = 0
        self.nombreDeNotes = 0

    def __repr__(self):
        """Affichage"""
        return "Concordance: {0} \nCohérence: {1}\nConcordance d'ordre 3:  {2} \nConcordance totale: {3}".format(self.concordance, self.coherence,self.concordanceOrdre3,self.concordanceTotale)

    """
    def tableConcordanceInterv(self):
        intervalle = np.arange(0,8.001,0.001)
        table = np.zeros(np.shape(intervalle))

        for i, inte in enumerate(intervalle):
            S1 = self.spectre(64)
            S2 = self.spectre(64*np.log2(inte))
            table[i] = np.sum(S1*S2)

        return table

    """
    """
    def concIntervVerticality(self): # verticality
        table = self.tableConcordanceInterv()
        accord = np.log2(self.verticality.pitchSet)
        liste_conc = list.new()

        for i, haut1  in enumerate(accord):
            for j, haut2 in enumerate(accord):
                if (i<j):
                liste_conc.append(table[np.trunc(np.abs(haut1-haut2)/0.001)])

        return liste_conc
    """

    def ListeHauteursAvecMultiplicite(self):
        """ Fonction qui donne la liste des pitches, comptés autant de fois qu'ils sont répétés à différentes voix"""
        #self.listeHauteursAvecMultiplicite = list
        for elt in self.verticality.startTimespans:
            if elt.element.isChord:
                for pitch in elt.element.pitches:
                    if elt.element.duration.quarterLength != 0:
                        self.listeHauteursAvecMultiplicite.append(pitch)

            elif elt.element.duration.quarterLength != 0:
                 self.listeHauteursAvecMultiplicite.append(elt.element.pitch)

        for elt in self.verticality.overlapTimespans:
            if elt.element.isChord:
                for pitch in elt.element.pitches:
                    self.listeHauteursAvecMultiplicite.append(pitch)

            else:
                 self.listeHauteursAvecMultiplicite.append(elt.element.pitch)

    def ListeConcordanceDesIntervallesDansAccord(self):
        '''Crée la liste des concordances des intervalles qui constituent l'accord, et le fixe comme paramètre, ceci afin d'éviter
        les redondances dans les calculs de la concordance et de la cohérence '''
        for i, pitch1 in enumerate(self.listeHauteursAvecMultiplicite):
            for j, pitch2 in enumerate(self.listeHauteursAvecMultiplicite):
                if (i<j):
                    self.listeConcordanceDesIntervallesDansAccord.append(np.sum(self.spectre(self.frequenceAvecTemperament(pitch1))*self.spectre(self.frequenceAvecTemperament(pitch2))))

    def NombreDeNotes(self):
        if self.listeHauteursAvecMultiplicite != None:
            self.nombreDeNotes = len(self.listeHauteursAvecMultiplicite)

    def Concordance(self):
        """ Normalisation logarithmique, de manière à rendre égales les concordances des unissons de n notes"""
        self.concordance = np.sum(self.listeConcordanceDesIntervallesDansAccord)
        self.concordance = np.log2(1 + self.concordance / (self.normalisation[0]*self.nombreDeNotes*(self.nombreDeNotes - 1)/2))
        #self.concordance = np.log2(1 + self.concordance)/(np.log(1 + self.normalisation[0]*self.nombreDeNotes*(self.nombreDeNotes - 1)/2) / np.log(1 + self.normalisation[0]))

    def Coherence(self):
        self.coherence = np.std(self.listeConcordanceDesIntervallesDansAccord)/self.normalisation[0]

    def ConcordanceOrdre3(self):
        for i, pitch1 in enumerate(self.listeHauteursAvecMultiplicite):
            for j, pitch2 in enumerate(self.listeHauteursAvecMultiplicite):
                for k, pitch3 in enumerate(self.listeHauteursAvecMultiplicite):
                    if (i<j<k):
                        self.concordanceOrdre3 =  self.concordanceOrdre3 + np.sum(self.spectre(self.frequenceAvecTemperament(pitch1))*self.spectre(self.frequenceAvecTemperament(pitch2))*self.spectre(self.frequenceAvecTemperament(pitch3)))

        self.concordanceOrdre3 = self.concordanceOrdre3**(2/3)
        self.concordanceOrdre3 = np.log2(1 + self.concordanceOrdre3 / (self.normalisation[1]*(self.nombreDeNotes*(self.nombreDeNotes - 1)*(self.nombreDeNotes - 2)/6)**(2/3)))
        #self.concordanceOrdre3 = np.log2(1 + self.concordanceOrdre3)/(np.log(1 + self.normalisation[1] * (self.nombreDeNotes*(self.nombreDeNotes - 1)*(self.nombreDeNotes - 2)/6)**(2/3)) / np.log(1 + self.normalisation[1]))

    def ConcordanceTotale(self):

        S = np.ones(16000)
        for pitch in self.listeHauteursAvecMultiplicite:
                S = S*self.spectre(self.frequenceAvecTemperament(pitch))
                self.concordanceTotale = np.sum(S)

        self.concordanceTotale = self.concordanceTotale**(2/self.nombreDeNotes)

        if self.nombreDeNotes == 4 :
            self.concordanceTotale = np.log2(1 + self.concordanceTotale/self.normalisation[2])
        elif self.nombreDeNotes == 5 :
            self.concordanceTotale = np.log2(1 + self.concordanceTotale/self.normalisation[3])
        elif self.nombreDeNotes == 6 :
            self.concordanceTotale = np.log2(1 + self.concordanceTotale/self.normalisation[4])
        elif self.nombreDeNotes == 7 :
            self.concordanceTotale = np.log2(1 + self.concordanceTotale/self.normalisation[5])
        elif self.nombreDeNotes == 8 :
            self.concordanceTotale = np.log2(1 + self.concordanceTotale/self.normalisation[6])
