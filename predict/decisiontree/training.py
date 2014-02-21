#
# -*- coding: utf-8 -*-
#
import logging
_LOG = logging.getLogger('training')

import random
from collections import defaultdict

from google.appengine.ext import ndb

from predict import models

class TrainingSetFactory(object):
    
    def train_x_y(self, func, count, range_x, range_y,
            target_name='target', missing_rate=0.0):
        """
        For double entry functions.
        
        @param func: function used a reference for training
        @param count: number of runs
        @param range_x: range for dimension x as a tuple (min, max)
        @param range_y: range for dimension y as a tuple (min, max)
        @param target_name: output dimension
        @param missing_rate: rate  which one of the inputs may be missing
        """
        loc_table = TrainingSet()
        keys = ['x', 'y']
        for index in xrange(count):
            log_data = {}
            dimension_to_skip = None
            missing_input = random.uniform(0.0, 1.0) <= missing_rate
            if missing_input:
                dimension_to_skip = random.choice(keys)
            
            x = random.uniform(*range_x)
            if dimension_to_skip != 'x':
                log_data['x'] = x
            
            y = random.uniform(*range_y)
            if dimension_to_skip != 'y':
                log_data['y'] = y
            
            log_data['target'] = func(x, y)
            loc_table.insert(log_data)
        
        return loc_table


class NDBTrainingSet(object):
    
    """
        Interfacing NDB
    """
    def __init__(self, context):
        self._context = context
        self._dimensions = None
        self._samples = list()
        
    def start(self):
        """
        Starts with full samples set.
        """
        self._samples = (models.Sample.query(
                models.Sample.context == self._context.key
                ).fetch(keys_only=True)
                )
        
    def insert(self, sample):
        self._samples.append(sample)
            
    def get_dimensions(self):
        """
        Gets all dimensions.
        """
        if not self._dimensions:
            self._dimensions = models.Dimension.query(
                models.Dimension.context == self._context.key
                ).fetch(keys_only=True)
            
        return self._dimensions
    
    @property
    def samples(self):
        return self._samples
    
    def count(self):
        """
        Total number of samples
        """
        return len(self.samples)

    def count_not_null(self, dimension):
        """
        Number of samples having a specific attribute filled in
        """
        if len(self.samples) == 0:
            return 0
            
        count = models.Sample.query(
            ndb.AND(
                models.Sample.measures.dimension == dimension,
                models.Sample.key.IN(self.samples)
                )
            ).count()
        return count

    def mean(self, dimension):
        """
        Mean value across a specific dimension.
        """
        assert len(self.samples) > 0, 'Trying to compute mean of an empty set'
        total = 0
        for sample_key in self.samples:
            sample = sample_key.get()
            _LOG.info('test %s' % str(sample.measures[dimension]))
            for measure in sample.measures:
                if measure.dimension == dimension:
                    total += measure.value
                    
        return total / len(self.samples)
    
    def variance(self, dimension):
        """Compute the variance of the set of values of an attribute."""
        assert len(self.samples) > 0, 'Trying to compute variance of an empty set'
        totsq = sum([row[dimension]**2 for row in self.samples.itervalues()])
        return float(totsq) / len(self.samples) - self.mean(dimension)**2

    def sample_rows(self, sample_size):
        """Sample table rows uniformly at random."""
        assert len(self.items) > 0, 'Trying to sample an empty table'
        return [self.items[random.randint(0, len(self.items) - 1)]
                for i in range(sample_size)]
    
    def sample_measures(self, dimension, sample_size):
        """
        Samples uniformly at random from the set of values of a dimension.

        @param dimension: the dimension
        @param sample_size: number of values to sample

        """
        return [row[dimension] for row in self.sample_rows(sample_size)]

    def split(self, dimension, split_val):
        """Split according to a given dimension and a split value.
        Returns a 3-uple of tables: one for values <= split_val, one for
        values > split_val and one for undef values of the dimension.

        dimension -- dimension to split on
        split_val -- split value

        """
        left_table = TrainingSet()
        right_table = TrainingSet()
        null_table = TrainingSet()
        for entry in self.items.itervalues():
            if not dimension in entry.keys():
                null_table.insert(entry)
                
            elif entry[dimension] <= split_val:
                left_table.insert(entry)
                
            else:
                right_table.insert(entry)
                
        return left_table, right_table, null_table

class TrainingSet(object):
    
    """
        Interface to datastore
    """
    
    def __init__(self):
        self._dimensions = list()
        self.items = dict()
 
    def insert(self, entry):
        row_id = len(self.items)
        self.items[row_id] = defaultdict(lambda: None)
        for key in entry.keys():
            if not key in self._dimensions:
                self._dimensions.append(key)
                
            self.items[row_id][key] = entry[key]

    def get_dimensions(self):
        """Get all table attributes."""
        return self._dimensions
    
    def count(self):
        """Count the number of rows in the table."""
        return len(self.items)

    def count_not_null(self, attr):
        """Count the number of rows in the table."""
        return len([item for item in self.items.itervalues() if item[attr] is not None])

    def mean(self, attr):
        """Compute the mean of all (real) values of an attribute."""
        assert len(self.items) > 0, 'Trying to compute mean of an empty set'
        total = float(sum([row[attr] for row in self.items.itervalues()]))
        return total / len(self.items)
    
    def variance(self, attr):
        """Compute the variance of the set of values of an attribute."""
        assert len(self.items) > 0, 'Trying to compute variance of an empty set'
        totsq = float(sum([row[attr]**2 for row in self.items.itervalues()]))
        return totsq / len(self.items) - self.mean(attr)**2

    def sample_rows(self, sample_size):
        """Sample table rows uniformly at random."""
        assert len(self.items) > 0, 'Trying to sample an empty table'
        return [self.items[random.randint(0, len(self.items) - 1)]
                for i in range(sample_size)]
    
    def sample_measures(self, dimension, sample_size):
        """
        Samples uniformly at random from the set of values of a dimension.

        @param dimension: the dimension
        @param sample_size: number of values to sample

        """
        return [row[dimension] for row in self.sample_rows(sample_size)]

    def split(self, dimension, split_val):
        """Split according to a given dimension and a split value.
        Returns a 3-uple of tables: one for values <= split_val, one for
        values > split_val and one for undef values of the dimension.

        dimension -- dimension to split on
        split_val -- split value

        """
        left_table = TrainingSet()
        right_table = TrainingSet()
        null_table = TrainingSet()
        for entry in self.items.itervalues():
            if not dimension in entry.keys():
                null_table.insert(entry)
                
            elif entry[dimension] <= split_val:
                left_table.insert(entry)
                
            else:
                right_table.insert(entry)
                
        return left_table, right_table, null_table

    def to_csv(self, csv_file=None):
        """
        Careful, that can be huge...
        If provided, fills in the file with the training data in csv format, 
        otherwise returns the csv as a string
        """
        as_string = False
        if csv_file is None:
            as_string = True
            from StringIO import StringIO
            csv_file = StringIO()
            
        import csv
        field_names = ['id'] + self.get_dimensions()
        csv_writer = csv.DictWriter(csv_file, fieldnames=field_names, dialect='excel')
        csv_writer.writeheader()
        for item_id in self.items:
            row_data = dict()
            row_data['id'] = item_id
            for dim in self.get_dimensions():
                row_data[dim] = self.items[item_id][dim]
                
            csv_writer.writerow(row_data)
        
        value = None
        if as_string:
            value = csv_file.getvalue()
            
        csv_file.close()        
        return value

    def __str__(self):
        return self.to_csv()

