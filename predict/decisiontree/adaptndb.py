#
# -*- coding: utf-8 -*-
#
import logging
_LOG = logging.getLogger('training-ndb')
import random

from google.appengine.ext import ndb

from predict import models
from predict.decisiontree import tools

class NDBTrainingSet(object):

    """
        Interface to datastore
    """

    def __init__(self, context):
        self._context = context
        self._dimensions = None
        self._items = None
        self._list_not_null = dict()
        self._entropy = None
        self._median = None

    def set_binary_output(self, is_binary_output):
        if is_binary_output:
            _LOG.info('detected binary output')
            
        self._binary_output = is_binary_output
    
    def setup_output(self, output_column_name, output_sampling):
        self._output_sampling = output_sampling
        self._output_column = models.Dimension.query(
            models.Dimension.context == self._context.key,
            models.Dimension.name == output_column_name
            ).get()
                     
        self._items = xrange(len(self._output_column.measures))
        self._dimensions = models.Dimension.query(
            models.Dimension.context == self._context.key
            ).fetch(keys_only=True)
                           
        output_categories = set()
        self._output_min = None
        self._output_max = None
        for output in self._output_column.measures:
            if self._output_min is None or output.value < self._output_min:
                self._output_min = output.value
                
            if self._output_max is None or output.value > self._output_max:
                self._output_max = output.value
                
            if len(output_categories) < 3:
                output_categories.add(output.value)
                
        self.set_binary_output(len(output_categories) == 2)
        
        _LOG.info('output min = %s' % self._output_min)
        _LOG.info('output max = %s' % self._output_max)

    def get_dimensions(self):
        """Gets all defined dimensions"""
        return self._dimensions
        
    def check_column(self, column_name):
        return models.Dimension.query(
            models.Dimension.context == self._context.key,
            models.Dimension.name == column_name
            ).fetch(1) > 0
            
    def _get_items(self):
        return self._items
        
    def _get_list_not_null(self, dimension):
        """
        Sorted list of non null values for a specific dimension.
        """
        if not self._list_not_null.has_key(dimension.key):
            not_null_items = [dimension.measures[index].value
                for index in self._get_items()
                if dimension.measures[index].value is not None]                                    
            self._list_not_null[dimension.key] = sorted(not_null_items)
            
        return self._list_not_null[dimension.key]

    def count(self):
        """Counts the number of rows in the table."""
        return len(self._get_items())

    def target_median(self):
        """
        Computes the median of the output
        """
        if self._median is None:
            values = self._get_list_not_null(self._output_column)
            if len(values) == 0:
                median = None

            else:
                median = tools.median(values)
                
            self._median = median
            
        return self._median
        
    def target_entropy(self):
        """
        Computes the statistics (median, entropy) for a dimension
        """
        if not self._entropy:
            values = self._get_list_not_null(self._output_column)
            if len(values) == 0:
                entropy = None

            else:
                if self._binary_output:
                    entropy = tools.binary_entropy(values)
                    
                else:
                    entropy = tools.entropy(values,
                            self._output_min,
                            self._output_max,
                            accuracy=self._output_sampling)
                
            self._entropy = entropy
            
        return self._entropy
        
    def _create_child_table(self):
        ts = NDBTrainingSet(self._context)
        ts._output_sampling = self._output_sampling
        ts._output_column = self._output_column
        # inheriting parent data
        ts._dimensions = self._dimensions
        ts._items = list()
        ts._output_min = self._output_min
        ts._output_max = self._output_max
        ts._binary_output = self._binary_output
        return ts

    def insert(self, item):
        self._items.append(item)

    def random_split(self, set_left, set_right):
        for item in self._get_items():
            random.choice([set_left, set_right]).insert(item)

    def sample_measures(self, dim_key, sample_size):
        """
        Samples uniformly at random from the set of values of a dimension.

        @param dimension: the dimension
        @param sample_size: number of values to sample

        """
        sample_size = min(sample_size, self.count())
        dimension = dim_key.get()
        samples = [dimension.measures[index] for index in self._get_items()]
        return random.sample(samples, sample_size)

    def split(self, dim_key, split_value):
        """Split according to a given dimension and a split value.
        Returns a 3-uple of tables: one for values <= split_value, one for
        values > split_val and one for undef values of the dimension.

        @param dimension: dimension to split on
        @param split_value: split value

        """
        left_table = self._create_child_table()
        right_table = self._create_child_table()
        null_table = self._create_child_table()
        dimension = dim_key.get()
        for item in self._get_items():
            if dimension.measures[item].value is None:
                null_table.insert(item)
                
            elif dimension.measures[item].value <= split_value:
                left_table.insert(item)

            else:
                right_table.insert(item)

        return left_table, right_table, null_table

    def __repr__(self):
        return '[set of %d rows]' % self.count()
     
