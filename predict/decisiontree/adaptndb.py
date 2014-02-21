#
# -*- coding: utf-8 -*-
#
import logging
_LOG = logging.getLogger('training-ndb')

from google.appengine.ext import ndb

from predict import models

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
