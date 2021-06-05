
import numpy as np

def map_opera ( ax ):
    ''' Creates mapping between an opus_id and arbitrary id
        (starting from 0) that will be used as matrix coord '''
    t, l = 0, {}
    for i in ax:
        if not i in l:
            l[int(i)] = t
            t+=1
    return l

def matrix_transform ( triplet_list ):
    ''' This function transform a list of triplets (opus,opus,value)
        into a distance matrix with opera on axis and values as data.

        This function returns both matrix and inversed mapping to 
        retrieve opus_id from matrix coordinates '''

    triplets = np.array(triplet_list)

    map_ids = map_opera(list(set(triplets[:,0]).union(set(triplets[:,1]))))

    mapped_triplets = []
    for i in triplet_list:
        # here we need to find the matrix coord from the opera ids
        mapped_triplets += [(map_ids[int(i[0])],map_ids[int(i[1])],i[2])]

    # Numpy transformation
    mapped_triplets = np.array(mapped_triplets)

    ymax = mapped_triplets[:, 0].max()
    xmax = mapped_triplets[:, 1].max()

    # Target array initialized with zeros
    target = np.zeros((int(ymax+1), int(xmax+1)), float)#triplets.dtype)

    target[mapped_triplets[:, 0].astype(int), 
           mapped_triplets[:, 1].astype(int)] = mapped_triplets[:, 2]

    # Returns matrix and (arbitrary id -> opus id) map
    return target,{v:k for k,v in map_ids.items()}

