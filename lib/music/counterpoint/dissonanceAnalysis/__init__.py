
import numpy as np
import tensorflow as tf

from django.conf import settings

class DissonanceAnalysis ():

    def __init__(self, pitchCollectionSequences):
        self.pitchCollectionSequenceList = pitchCollectionSequences
        #self.featuresPath = 'dissonanceNeuralNetwork/observations.npy'
        #self.labelsPath = 'dissonanceNeuralNetwork/labels.npy'
        self.modelPath = settings.BASE_DIR + '/static/dissonanceNeuralNetwork/model.h5'

        ''' run model '''
        #self.features = np.load(self.featuresPath)
        #self.labels = np.load(self.labelsPath)
        self.new_model = keras.models.load_model(self.modelPath)
        self.new_model.compile(optimizer=tf.optimizers.Adam(), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        self.new_model.summary()

        #unused_loss, acc = self.new_model.evaluate(self.features, self.labels)
        #print("Restored model, accuracy: {:5.2f}%".format(100 * acc))

        self.analyzeWithModel()

    def analyzeWithModel (self):

        ''' loop over all analyzed pitches '''
        pitchCollectionSequence = self.pitchCollectionSequenceList.pitchCollSequence

        for pitchCollection in pitchCollectionSequence.explainedPitchCollectionList:
            ''' loop over all analyzed pitches '''
            for analyzedPitch in pitchCollection.analyzedPitchList:

                ''' get observation list and put it in array '''

                observationArray = np.array(pitchCollectionSequence.getObservationsForPitchId(analyzedPitch.id,
                5, pitchCollection.verticality.offset))
                feature = np.array([observationArray])

                ''' make prediction from observation list '''
                predictions = self.new_model.predict(feature)

                ''' get highest score identifiy index '''
                highestScore = max(predictions[0])
                for index in range (0, len(predictions[0])):
                    if predictions[0][index] == highestScore:
                        break

                labelDict = {0:"CN", 1:"PN", 2:"NN", 3:"AN", 4:"SU", 5:"AP", 6:"PE", 7:"EN"}
                #print ("prediction: " + labelDict[index] + " score: " + str(highestScore))

                analyzedPitch.pitchType = labelDict[index]
                analyzedPitch.probability = highestScore
