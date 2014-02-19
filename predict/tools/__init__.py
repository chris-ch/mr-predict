import os

def _coord(a, a_max, x_min, x_max):
    """
    Assumes a is a counter from 1 up to a_max
    """
    a0_max = float(a_max - 1)
    a0 = float(a - 1)
    return  ((a0_max - a) * x_min + a0 * x_max) / a0_max
    
def _index(x, a_max, x_min, x_max):
    """
    Reverse from coord function
    """
    a0_max = float(a_max - 1)
    return  int(a0_max * (x - x_min) / (x_max - x_min))
    
class TextGraph(object):
    
    def __init__(self, x1, y1, x2, y2, nb_x, nb_y):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.nb_x = nb_x
        self.nb_y = nb_y
        if x1 > x2: (self.x1, self.x2) = (self.x2, self.x1)
        if y1 > y2: (self.y1, self.y2) = (self.y2, self.y1)
        self.clean()
    
    def clean(self):
        self.values = []
        for y in xrange(self.nb_y):
            row = []
            for x in xrange(self.nb_x):
                row.append(0.0)
                
            self.values.append(row)
        
    def plot(self, x, y, value=1.0):
        index_x = _index(x, self.nb_x, self.x1, self.x2)
        index_y = _index(y, self.nb_y, self.y1, self.y2)
        if index_y >= len(self.values) or index_y < 0:
            #print 'y value out of plotting range', y
            pass
            
        elif index_x >= len(self.values[index_y]) or index_x < 0:
            #print 'x value out of plotting range', x
            pass
        
        else:
            self.values[index_y][index_x] = value
        
    def add_func(self, func):
        for y in xrange(self.nb_y):
            for x in xrange(self.nb_x):
                c_x = _coord(x, self.nb_x, self.x1, self.x2)
                c_y = _coord(y, self.nb_y, self.y1, self.y2)
                value = func(c_x, c_y)
                self.values[y][x] = value

    def output_value(self, value):
        discrete = int(value)
        return ('.', '@', 'o', 'x')[discrete]

    def draw(self):
        out = ''
        for y in xrange(self.nb_y):
            for x in xrange(self.nb_x):
                out += self.output_value(self.values[self.nb_y - y - 1][x])
                
            out += os.linesep
     
        return out
        
    def json(self):
        import json
        return json.dumps(self.values)
        