#
# -*- coding: utf-8 -*-
#
import os
import sys
import logging
import argparse

from predict.decisiontree.forest import RandomForest
from predict.decisiontree.training import TrainingSetFactory

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
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

def main(args):
    config_logging(args.log_level)
    factory = TrainingSetFactory()
    input_file = args.csv_input_file
    target_column = args.target_column
    data = factory.train_csv(input_file, target_name=target_column)
    input_file.close()
    forest = RandomForest()
    forest.set_training_data(data, target_column)
    forest.grow_trees(args.number_trees)
    with open(args.output, 'wb') as output_file:
        forest.serialize(output_file)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Generates a Random Forest',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('csv_input_file',
        type=argparse.FileType('r'),
        help='CSV file (including header) with list of training samples. First column serves as id for the sample')

    parser.add_argument('-o', '--output',
        type=str,
        default='forest',
        help='resulting forest to be used as input for regression')

    parser.add_argument('-t', '--target-column',
        type=str,
        default='target',
        help='name indicating the ouput column')

    parser.add_argument('-n', '--number-trees',
        type=int,
        default=30,
        help='number of trees to grow')

    parser.add_argument('-l', '--log-level',
        type=str,
        default='info',
        choices=['debug', 'info', 'warn'],
        help='sets the level for logging messsages')

    args = parser.parse_args()
    main(args)

