#
# -*- coding: utf-8 -*-
#
import os
import os.path
import math
import sys
import logging
import csv
import argparse
from collections import defaultdict

def as_number(s):
    try:
        v = float(s)
        return v
    except ValueError:
        return None
        
def as_int(s):
    try:
        v = int(s)
        return v
    except ValueError:
        return None
        
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
    input_rows = csv.reader(args.csv_input_file)
    header = next(input_rows)
    categories = defaultdict(lambda: set())
    count_rows = 0
    stats_count_na = defaultdict(int)
    stats_average = defaultdict(float)
    stats_min = defaultdict(float)
    stats_max = defaultdict(float)
    stats_stdev_m = dict()
    stats_stdev_s = dict()
    stats_stdev = defaultdict(float)
    
    for columns in input_rows:
        count_rows += 1
        for count, cell in enumerate(columns):
            column_category = categories[header[count]]
            if len(column_category) < args.max_count:
                column_category.add(cell)
            
            value = as_number(cell)
            if not value:
                stats_count_na[header[count]] += 1
                
            else:
                if not stats_stdev_m.has_key(header[count]):
                    """
                    Iterative method for computing stdev:
                    M(1) = x(1)
                    M(k) = M(k-1) + (x(k) - M(k-1)) / k
                    
                    S(1) = 0
                    S(k) = S(k-1) + (x(k) - M(k-1)) * (x(k) - M(k))
                    
                    for 2 <= k <= n, then sigma = sqrt(S(n) / (n - 1))
                    """
                    stats_stdev_m[header[count]] = value
                    stats_stdev_s[header[count]] = 0.0
                    
                else:
                    m_prev = stats_stdev_m[header[count]]
                    s_prev = stats_stdev_s[header[count]]
                    stats_stdev_m[header[count]] = m_prev + (value - m_prev) / count_rows
                    stats_stdev_s[header[count]] = s_prev + (value - m_prev) * (value - stats_stdev_m[header[count]])
                    
                stats_average[header[count]] += value
                if value < stats_min[header[count]]:
                    stats_min[header[count]] = value
                    
                if value > stats_min[header[count]]:
                    stats_max[header[count]] = value
     
    for column in header:
        if count_rows == stats_count_na[column]:
            stats_average[column] = None
            
        else:
            stats_average[column] /= (count_rows - stats_count_na[column])
            if count_rows != stats_count_na[column] + 1:
                stats_stdev[column] = math.sqrt(stats_stdev_s[column] / (count_rows - stats_count_na[column] - 1))
                
            else:
                stats_stdev[column] = None
        
    for column in header:
        print column, stats_average[column], stats_stdev[column], stats_min[column], stats_max[column], stats_count_na[column], len(categories[column])

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Runs statistics on a Random Forest',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-l', '--log-level',
        type=str,
        default='info',
        choices=['debug', 'info', 'warn'],
        help='sets the level for logging messsages')

    parser.add_argument('-m', '--max-count',
        type=int,
        default=20,
        help='max size for categories')

    parser.add_argument('csv_input_file',
        type=argparse.FileType('r'),
        nargs='?',
        default=sys.stdin,
        help='CSV file (including header) with list of training samples. First column serves as id for the samples')

    args = parser.parse_args()
    main(args)
