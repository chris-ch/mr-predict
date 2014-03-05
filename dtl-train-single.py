#
# -*- coding: utf-8 -*-
#
import os
import sys
import logging
import argparse
import cPickle

from predict.decisiontree.forest import RandomForest
from predict.decisiontree.forest import serialize_forests
from predict.decisiontree.train import TrainingSetFactory

def config_logging(level):
    # create logger
    logger = logging.getLogger('training')
    level_mapping = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warn': logging.WARNING,
    }
    logger.setLevel(level_mapping[level])

    # create console handler and set level to debug
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s %(asctime)s [%(name)s] %(message)s')
    ch.setFormatter(formatter)

    logging.getLogger('tools').setLevel(level_mapping[level])
    
    # add ch to logger
    logger.addHandler(ch)
    logging.getLogger('tools').addHandler(ch)

def main(args):
    config_logging(args.log_level)
    
    options = ['--%s %s' % (option, vars(args)[option]) for option in vars(args).keys()]
    logging.getLogger('training').info('running with options: %s' % ' '.join(options))
    
    ignored = list()
    if args.ignore_columns:
        with open(args.ignore_columns, 'r') as file_ignore:
            ignored = [line.rstrip() for line in file_ignore]
            
    # Single processor
    factory = TrainingSetFactory()
    forests = None
    input_file = args.csv_input_file
    data = factory.train_csv(input_file, target_name=args.target_column, 
        output_sampling=args.output_sampling, ignore_columns=ignored)
    forest = RandomForest()
    forest.set_training_data(data, args.target_column, 
        min_count=args.min_leaf_size, split_sampling=args.split_sampling)
    forest.grow_trees(1)
    forests = [forest]
    serialize_forests(forests, args.output)
        
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Generates a Random Forest',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('csv_input_file',
        type=argparse.FileType('r'),
        nargs='?',
        default=sys.stdin,
        help='CSV file (including header) with list of training samples. First column serves as id for the samples')

    parser.add_argument('-o', '--output',
        type=argparse.FileType('wb'),
        nargs='?',
        default='forest',
        help='resulting forest to be used as input for regression')

    parser.add_argument('-t', '--target-column',
        type=str,
        default='target',
        help='name indicating the ouput column')

    parser.add_argument('-x', '--min-leaf-size',
        type=int,
        default=5,
        help='number of samples below which the tree stops growing')

    parser.add_argument('-y', '--split-sampling',
        type=int,
        default=100,
        help='number of samples used when selecting a split')

    parser.add_argument('-s', '--output-sampling',
        type=int,
        default=5,
        help='number of categories for output sampling')

    parser.add_argument('-i', '--ignore-columns',
        type=str,
        help='file containing a list of columns to be ignored')

    parser.add_argument('-l', '--log-level',
        type=str,
        default='info',
        choices=['debug', 'info', 'warn'],
        help='sets the level for logging messsages')

    args = parser.parse_args()
    main(args)

