#
# -*- coding: utf-8 -*-
#
import os
import sys
import logging
import cPickle
import csv
import argparse

from predict.decisiontree.forest import RandomForest

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
    forest_file = args.forest
    forest_data = cPickle.load(forest_file)
    forest_file.close()
    forest = RandomForest()
    forest.use_trees(forest_data)
    samples = csv.reader(args.csv_input_file, delimiter=',')
    first_line = next(samples)
    header = first_line[1:]
    out = csv.writer(args.output)
    out.writerow([first_line[0], args.target_column])
    for sample_data in samples:
        sample_id = sample_data[0]
        sample = dict()
        for index, column in enumerate(sample_data[1:]):
            try:
                sample[header[index]] = float(column)
                
            except ValueError:
                pass
        
        value = forest.predict(sample)
        out.writerow([sample_id, value])
        
        
    
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Runs a Random Forest on a set',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('csv_input_file',
        type=argparse.FileType('r'),
        help='CSV file (including header) with list of samples. First column serves as sample identifier.')
    
    parser.add_argument('-o', '--output',
        type=argparse.FileType('w'),
        default='results.csv',
        help='output of the regression for each sample')
    
    parser.add_argument('-f', '--forest',
        type=argparse.FileType('r'),
        default='forest',
        help='forest data obtained from training phase')
    
    parser.add_argument('-t', '--target-column',
        type=str,
        default='target',
        help='name of the ouput column')
    
    parser.add_argument('-l', '--log-level',
        type=str,
        default='info',
        choices=['debug', 'info', 'warn'],
        help='sets the level for logging messsages')
    
    args = parser.parse_args()
    main(args)