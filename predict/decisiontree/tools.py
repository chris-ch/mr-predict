import math
import logging
_LOG = logging.getLogger('tools')

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

def binary_entropy(x):
    x0 = x[0]
    count = 0
    for x_i in x:
        if x_i == x0:
            count += 1
    
    p = float(count) / len(x)
    return -elog(p) - elog(1.0 - p)
        

def entropy(x, min_x=None, max_x=None, accuracy=20):
    """
    Entropy of a list of float values.
    """
    if not min_x:
        min_x = min(x)
        
    if not max_x:
        max_x = max(x)
        
    if min_x == max_x:
        return 0.0
    
    bins = histogram(x, accuracy, min_x=min_x, max_x=max_x)
    e = 0.0
    for bin in bins:
        probability = float(bin) / len(x)
        e += elog(probability)
    
    return -e

def median(values):
    median = None
    if len(values) & 1:
        # odd number of items
        median = values[len(values) / 2]
        
    else:
        # even number of items
        median = 0.5 * (values[len(values) / 2 - 1] + values[len(values) / 2])
    
    return median
    
if __name__ == '__main__':
    import random
    import sys
    ones = [1, 0, 1, 1, 1, 1, 1, 0, 1, 1]
    zeros = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
    print entropy(ones, accuracy=2)
    print binary_entropy(ones)
    print
    print entropy(zeros, accuracy=2)
    print binary_entropy(zeros)
    print
    print 'both', entropy(ones + zeros, 0, 100)
    print 'ones', entropy(ones, 0, 1)
    print 'zeros', entropy(zeros, 0, 1)
    alpha = float(len(ones)) / float(len(ones) + len(zeros))
    print 'total', alpha * entropy(ones, 0, 1) + (1.0 - alpha) * entropy(zeros, 0, 1)
    print entropy([0, 0, 1, 0, 0, 0, 0, 0, 0, 0], 0, 1)
    print entropy([0, 0, 100, 0, 0, 0, 0, 0, 0, 0], 0, 100)
    print entropy([0, 0, 1, 0, 0, 0, 0, 0, 0, 0], 0, 100)
    print entropy([random.randint(1, 11) for x in range(11)] + zeros + ones , 0, 11, accuracy=11)
    