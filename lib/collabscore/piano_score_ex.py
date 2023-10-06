import music21 as m21
sc1 = m21.stream.Score()
right_hand = m21.stream.PartStaff()
left_hand = m21.stream.PartStaff()
right_hand.append(m21.key.Key('Ab', 'major'))
right_hand.append(m21.note.Note('D-4'))
right_hand.append(m21.note.Note('F-4'))
right_hand.append(m21.note.Note('A-4'))
right_hand.append(m21.note.Note('B--4'))
left_hand.append(m21.chord.Chord(
    [m21.note.Note('D-3'), m21.note.Note('A-3')],
    duration=m21.duration.Duration(4)))
sc1.insert(0, right_hand)
sc1.insert(0, left_hand)
sc1.insert(0, m21.layout.StaffGroup([right_hand, left_hand], 
								 name='Marimba', abbreviation='Mba.',
								 symbol='brace'))
  
sc1.show()