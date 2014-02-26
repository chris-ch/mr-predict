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
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s %(asctime)s [%(name)s] %(message)s')
    ch.setFormatter(formatter)

    logging.getLogger('tools').setLevel(level_mapping[level])
    
    # add ch to logger
    logger.addHandler(ch)
    logging.getLogger('tools').addHandler(ch)

def main(args):
    config_logging(args.log_level)
    workers_count = args.multiprocessing
    
    ignored = list()
    if args.ignore_columns:
        with open(args.ignore_columns, 'r') as file_ignore:
            ignored = [line.rstrip() for line in file_ignore]
            
    if workers_count:
        import multiprocessing as mp
        mp.log_to_stderr(logging.INFO)
        logger = mp.get_logger()
        pool = mp.Pool(processes=workers_count)
        forests = list()
        def gather_trees(tree_serial, f=forests):
            tree = cPickle.loads(tree_serial)
            forest = RandomForest()
            forest.trees = [tree]
            forests.append(forest)
        
        pool_status = list()
        for index in range(args.number_trees):
            status = pool.apply_async(create_tree,
                    (args.log_level, args.csv_input_file, args.target_column, 
                        args.min_leaf_size, args.split_sampling, args.output_sampling, ignored),
                    callback=gather_trees)
            pool_status.append(status)
            
        for s in pool_status:
            # This is only for forcing the display of some error ...
            # It would go unnoticed otherwise!
            # Also note that side-effect of setting a timeout is that
            # it works around python's bug when processes are interrupted
            # (they would hang otherwise forcing to kill -9...)
            s.get(args.timeout_min * 60)
        
        pool.close()
        pool.join()
        
    else:
        # Single processor
        factory = TrainingSetFactory()
        forests = None
        with open(args.csv_input_file, 'r') as input_file:
            data = factory.train_csv(input_file, target_name=args.target_column, 
                output_sampling=args.output_sampling, ignore_columns=ignored)
            forest = RandomForest()
            forest.set_training_data(data, args.target_column, 
                min_count=args.min_leaf_size, split_sampling=args.split_sampling)
            forest.grow_trees(args.number_trees)
            forests = [forest]
    
    with open(args.output, 'wb') as output_file:
        serialize_forests(forests, output_file)
        
def create_tree(log_level, csv_input_file, target_column, min_leaf_size, 
    split_sampling, output_sampling, ignored):
    """
    Grows a single-tree forest
    """
    import multiprocessing as mp
    logger = mp.get_logger()
    logger.setLevel(logging.INFO)
    factory = TrainingSetFactory()
    tree = None
    with open(csv_input_file, 'r') as input_file:
        data = factory.train_csv(input_file, target_name=target_column, output_sampling=output_sampling, ignore_columns=ignored)
        forest = RandomForest()
        forest.set_training_data(data, target_column, min_count=min_leaf_size, split_sampling=split_sampling)
        tree = forest.grow_tree()
    
    import cPickle
    from StringIO import StringIO
    output = StringIO()
    cPickle.dump(tree, output)
    return output.getvalue()
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Generates a Random Forest',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('csv_input_file',
        type=str,
        help='CSV file (including header) with list of training samples. First column serves as id for the samples')

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
        default=32,
        help='number of trees to grow')

    parser.add_argument('-m', '--multiprocessing',
        type=int,
        help='splits the work using local processors')

    parser.add_argument('-f', '--timeout-min',
        type=int,
        default=600,
        help='forces processors to stop after tiemout in minutes')

    parser.add_argument('-x', '--min-leaf-size',
        type=int,
        default=5,
        help='number of samples below which the tree stops growing')

    parser.add_argument('-y', '--split-sampling',
        type=int,
        default=20,
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

