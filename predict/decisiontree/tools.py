import math

def elog(x):
    """
    Log for entropy calculation returning 0 for 0 * log 0
    """
    if x == 0.0: return 0.0
    return x * math.log(x)

def histogram(x, bins, min_x=None, max_x=None):
    """
    Histogram if the input data in the form of an ordered list of bins.
    """
    if not min_x:
        min_x = min(x)
        
    if not max_x:
        max_x = max(x)
        
    x_range = (min_x, max_x)
    assert x_range[0] != x_range[1], 'cannot create bins when all values are equal'
    h = [0] * bins
    for x_i in x:
        alpha = float(x_i - x_range[0]) / float(x_range[1] - x_range[0])
        index = int(float(bins - 1) * alpha)
        h[index] += 1
        
    return h

def entropy(x, accuracy=20):
    """
    Entropy of a list of float values.
    """
    min_x = min(x)
    max_x = max(x)
    if min_x == max_x:
        return 0.0
        
    bins = histogram(x, accuracy, min_x=min_x, max_x=max_x)
    e = 0.0
    for bin in bins:
        e += elog(float(bin) / len(bins))
    
    return -e

if __name__ == '__main__':
    ones = [1, 0, 1, 1, 1, 1, 1, 0, 1, 1]
    zeros = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
    print 'both', entropy(ones + zeros)
    print 'ones', entropy(ones)
    print 'zeros', entropy(zeros)
    alpha = float(len(ones)) / float(len(ones) + len(zeros))
    print 'total', alpha * entropy(ones) + (1.0 - alpha) * entropy(zeros)
    