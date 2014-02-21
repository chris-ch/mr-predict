#
# -*- coding: utf-8 -*-
#
import os
import sys
import logging
import math

from predict.decisiontree.forest import RandomForest
from predict.decisiontree.training import TrainingSetFactory
from predict.tools import TextGraph

def config_logging():   
    # create logger
    logger = logging.getLogger('regression')
    logger.setLevel(logging.DEBUG)
    
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    
    # add ch to logger
    logger.addHandler(ch)

if __name__ == '__main__':
    config_logging()
    factory = TrainingSetFactory()
    
    def in_diskus(x0, y0, r):
        return (x0 * x0 + y0 * y0) < (r * r)
        
    def diskus_func(x0, y0):
        return (0.0, 1.0)[in_diskus(x0, y0, 0.7)]

    def in_oblique_rectangle(x0, y0, x1, y1, width, height, rotation=math.pi/3.0):
        # expressing x0, y0 in the coordinates of the rectangle
        # Step 1 - translation
        x0_t = x0 - x1
        y0_t = y0 - y1
        # Step 2 - rotation
        x0_tr = x0_t * math.cos(rotation) - y0_t * math.sin(rotation)
        y0_tr = x0_t * math.sin(rotation) + y0_t * math.cos(rotation)
        return x0_tr <= width and x0_tr >= 0 and y0_tr >= 0 and y0_tr <= height
        
    def in_rectangle(x0, y0, x1, x2, y1, y2):
        if x1 > x2: (x1, x2) = (x2, x1)
        if y1 > y2: (y1, y2) = (y2, y1)
        return x0 <= x2 and x0 >= x1 and y0 >= y1 and y0 <= y2
        
    def oblique_rectangle_func(x0, y0):
        return (0.0, 1.0)[in_oblique_rectangle(x0, y0, -0.9, 0.1, 1.0, 1.0)]

    def rectangle_func(x0, y0):
        return (0.0, 1.0)[in_rectangle(x0, y0, -1.0, 1.0, -0.5, 0.5)]

    def empty_rectangle_func(x0, y0):
        return (0.0, 1.0)[in_rectangle(x0, y0, -1.0, 1.0, -0.5, 0.5)
            and not in_rectangle(x0, y0, -0.7, 0.7, -0.2, 0.2)]

    range_x = (-2.0, 2.0)
    range_y = (-2.0, 2.0)
    data = factory.train_x_y(oblique_rectangle_func, 1000, 
            range_x, range_y, target_name='target', missing_rate=0.1)
    forest = RandomForest(data, 'target')
    forest.grow_trees(30)
    print forest.persist()
    
    
