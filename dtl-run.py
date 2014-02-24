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
        
    print 'number of trees:', len(forest.trees)
    samples = csv.reader(args.csv_input_file, delimiter=',')
    first_line = next(samples)
    header = first_line[1:]
    with open(args.output, 'wb') as output_file:
        out = csv.writer(output_file)
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

    if args.check:
        from itertools import izip
        with open(args.output, 'rb') as res_file:
            ref_rows = csv.reader(args.check)
            res_rows = csv.reader(res_file)
            next(ref_rows)
            next(res_rows)
            errors_count = 0
            samples_count = 0
            for ref_row, res_row in izip(ref_rows, res_rows):
                ref_value = float(ref_row[1])
                samples_count += 1
                if res_row[1] not in ('None', '', 'NA'):                    
                    res_value = round(float(res_row[1]))
                    errors_count += (0, 1)[abs(ref_value - res_value) != 0.0]

                else:
                    errors_count += 1

            print 'cheking results: %d errors detected from a total of %d samples' % (errors_count, samples_count)



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Runs a Random Forest on a set',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('csv_input_file',
        type=argparse.FileType('r'),
        help='CSV file (including header) with list of samples. First column serves as sample identifier.')

    parser.add_argument('-o', '--output',
        type=str,
        default='results.csv',
        help='output of the regression for each sample')

    parser.add_argument('-f', '--forest',
        type=str,
        default='forest',
        help='forest data obtained from training phase: can be a directory or a file')

    parser.add_argument('-c', '--check',
        type=argparse.FileType('r'),
        help='file used for cross-checking the results')

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
