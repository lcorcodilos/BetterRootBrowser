import math
def entropies(l):
    '''For len(l) unique items, return the entropies of each splitting
    where l gives the distribution of splittings. For example, 
    [1,2,3] denotes three splittings with 1, 2, and 3 items per splitting.

    Args:
        l ([type]): [description]

    Returns:
        [type]: [description]
    '''
    tot = sum(l)
    p = 1./tot
    return [-1*n/tot*p*math.log(p, len(l)) for n in l]

if __name__ == '__main__':
    my = sum(entropies([1,4]))
    my_cat_given_my = sum(entropies([1,3]))
    my_cat = sum(entropies([1,1,3]))
    
    print(f'''
    my = {my}
    my_cat = {my_cat}
    my_cat_given_my = {my_cat_given_my}
    ''')

    print(f'''
    {sum(entropies([2,2]))}
    {sum(entropies([1,1,2]))}
    {sum(entropies([1,1,1,1]))}
    ''')