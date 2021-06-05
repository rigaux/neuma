
def symetrical_chi_square ( obs , exp ):
    l = len ( obs )
    if ( l != len ( exp ) ):
        raise InputLengthMismatchError
    r = [0] * l
    for i in range(1,l):
        if obs[i]+exp[i]:
            r[i] = pow(obs[i]-exp[i],2)/(obs[i]+exp[i])
    return sum(r)/2


