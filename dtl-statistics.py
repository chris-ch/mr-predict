#
# -*- coding: utf-8 -*-
#
import os
import os.path
import sys
import logging
import cPickle
import csv
import argparse
from collections import defaultdict

from predict.decisiontree.forest import RandomForest

def config_logging(level):
    # create logger
    logger = logging.getLogger('training')
    level_mapping = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warn': logging.WARNING,
    }
    # root logger
    logger.setLevel(level_mapping[level])
    logging.getLogger().setLevel(level_mapping[level])

    # create console handler and set level to debug
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

def main(args):
    config_logging(args.log_level)
    forest_path = args.forest
    forest = RandomForest()
    if os.path.isdir(forest_path):
        only_files = [f for f in os.listdir(forest_path)
            if os.path.isfile(os.path.join(forest_path, f)) ]
            
        for f in only_files:
            with open(os.path.join(forest_path, f), 'r') as forest_file:
                forest_data = cPickle.load(forest_file)
                forest.use_trees(forest_data)
            
    else:
        with open(forest_path, 'r') as forest_file:
            forest_data = cPickle.load(forest_file)
            forest.use_trees(forest_data)
            
    logging.info('loaded a total of %d trees' % len(forest.trees))
    tree_stats = list()
    for count, root in enumerate(forest.trees):
        dimensions = defaultdict(int)
        tree_stats.append(dimensions)
        def print_node(n):
            dimensions[n.split_dimension] += 1
            
        walk(root, print_node)

    for count, ts in enumerate(tree_stats):
        for dim in ts.keys():
            print count, dim, ts[dim]

def walk(node, f_node, f_leaf=None):
    if node.is_leaf():
        if f_leaf: f_leaf(node)
        
    else:
        f_node(node)
        walk(node.left_node, f_node, f_leaf)
        walk(node.right_node, f_node, f_leaf)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Runs statistics on a Random Forest',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-f', '--forest',
        type=str,
        default='forest',
        help='forest data obtained from training phase: can be a directory or a file')

    parser.add_argument('-l', '--log-level',
        type=str,
        default='info',
        choices=['debug', 'info', 'warn'],
        help='sets the level for logging messsages')

    args = parser.parse_args()
    main(args)
