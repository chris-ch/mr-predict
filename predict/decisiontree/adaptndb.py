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

    def __init__(self, context, output_sampling):
        self._context = context
        self._dimensions = None
        self._items = None
        self._list_not_null = dict()
        self._entropy = None
        self._medians = dict()
        self._output_sampling = output_sampling

    def setup_output(self, output_column):
        self._items = (models.Sample.query(
                models.Sample.context == self._context.key
                ).fetch(keys_only=True)
                )
        self._dimensions = models.Dimension.query(
            models.Dimension.context == self._context.key
            ).fetch(keys_only=True)
            
        self._index = dict()
        for dim_key in self._dimensions:
            self._index[dim_key] = dim_key.get().index
        
        self._output_column = models.Dimension.query(models.Dimension.name == output_column).get()
        output_index = self._index[self._output_column.key]
        def items_output():
            for item in self._get_items():
                yield self.fetch_index(item, output_index)
                
        output_categories = set()
        self._output_min = None
        self._output_max = None
        for output in items_output():
            if self._output_min is None or output < self._output_min:
                self._output_min = output
                
            if self._output_max is None or output > self._output_max:
                self._output_max = output
                
            if len(output_categories) < 3:
                output_categories.add(output)
                
        self._binary_output = len(output_categories) == 2
        if self._binary_output:
            _LOG.info('detected binary output')
            
        _LOG.info('output min = %s' % self._output_min)
        _LOG.info('output max = %s' % self._output_max)

    def get_dimensions(self):
        """Gets all defined dimensions"""
        return self._dimensions
        
    def check_column(self, column_name):
        return models.Dimension.query(models.Dimension.name == column_name).fetch(1) > 0
            
    def _get_items(self):
        return self._items
        
    def _get_list_not_null(self, dim_key):
        """
        Sorted list of non null values for a specific dimension.
        """
        if not self._list_not_null.has_key(dim_key):
            not_null_items = [self.fetch_dim_key(item, dim_key)
                for item in self._items
                if self.fetch_dim_key(item, dim_key) is not None]                                    
            self._list_not_null[dim_key] = sorted(not_null_items)
            
        return self._list_not_null[dim_key]

    def count(self):
        """Counts the number of rows in the table."""
        return len(self._get_items())

    def _get_median(self, dim):
        """
        Computes the statistics (median, entropy) for a dimension
        """
        if not self._medians.has_key(dim):
            values = self._get_list_not_null(dim)
            if len(values) == 0:
                median = None

            else:
                median = tools.median(values)
                
            self._medians[dim] = median
            
        return self._medians[dim]
        
    def target_entropy(self):
        """
        Computes the statistics (median, entropy) for a dimension
        """
        if not self._entropy:
            values = self._get_list_not_null(self._output_column.key)
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
        
    def fetch_index(self, item, index):
        return item.get().measures[index].value
        
    def fetch_dim_key(self, item, dim_key):
        index = self._index[dim_key]
        return self.fetch_index(item, index)

    def _create_child_table(self):
        ts = NDBTrainingSet(self._context, self._output_sampling)
        # inheriting parent data
        ts._output_column = self._output_column
        ts._dimensions = self._dimensions
        ts._items = list()
        ts._index = self._index
        ts._output_min = self._output_min
        ts._output_max = self._output_max
        ts._binary_output = self._binary_output
        return ts

    def insert(self, item):
        self._items.append(item)

    def __repr__(self):
        return '[set of %d rows]' % self.count()
     
    def random_split(self, set_left, set_right):
        for item in self._get_items():
            random.choice([set_left, set_right]).insert(item)

    def median(self, dim_name):
        """
        Computes the median for a dimension
        """
        dim = models.Dimension.query(models.name == dim_name).get()
        return self._get_median(dim.key)

    def sample_measures(self, dimension, sample_size):
        """
        Samples uniformly at random from the set of values of a dimension.

        @param dimension: the dimension
        @param sample_size: number of values to sample

        """
        index = self._index[dimension]
        sample_size = min(sample_size, self.count())
        return [self.fetch_index(item, index) for item in random.sample(self._get_items(), sample_size)]

    def split(self, dimension, split_value):
        """Split according to a given dimension and a split value.
        Returns a 3-uple of tables: one for values <= split_value, one for
        values > split_val and one for undef values of the dimension.

        @param dimension: dimension to split on
        @param split_value: split value

        """
        left_table = self._create_child_table()
        right_table = self._create_child_table()
        null_table = self._create_child_table()
        for entry in self._get_items():
            if self.fetch_dim_key(entry, dimension) is None:
                null_table.insert(entry)
                
            elif self.fetch_dim_key(entry, dimension) <= split_value:
                left_table.insert(entry)

            else:
                right_table.insert(entry)

        return left_table, right_table, null_table

