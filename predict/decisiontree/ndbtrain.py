#
# -*- coding: utf-8 -*-
#
import logging
_LOG = logging.getLogger('training.ndb')
import random

from google.appengine.ext import ndb

from predict import models
from predict.decisiontree import tools
from predict.decisiontree.train import BaseTrainingSet

class NDBTrainingSet(BaseTrainingSet):

    """
        Interface to datastore
    """

    def __init__(self, context):
        super(NDBTrainingSet, self).__init__()
        self._context = context
        self._dimensions_by_key = dict()

    def check_column(self, column_name):
        return models.Dimension.query(
            models.Dimension.context == self._context.key,
            models.Dimension.name == column_name
            ).fetch(1) > 0

    def _get_list_not_null(self, dim):
        """
        Sorted list of non null values for a specific dimension.
        """
        if not self._list_not_null.has_key(dim.key):
            not_null_items = [dim.measures[index].value
                for index in self._get_items()
                if dim.measures[index].value is not None]                                    
            self._list_not_null[dim.key] = sorted(not_null_items)
            
        return self._list_not_null[dim.key]

    def _create_child_table(self):
        ts = NDBTrainingSet(self._context)
        # inheriting parent data
        ts._dimensions = self._dimensions
        ts._output_column = self._output_column
        ts._output_sampling = self._output_sampling
        ts._output_min = self._output_min
        ts._output_max = self._output_max
        ts._binary_output = self._binary_output
        return ts

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

    def sample_measures(self, dim_key, sample_size):
        """
        Samples uniformly at random from the set of values of a dimension.

        @param dimension: the dimension
        @param sample_size: number of values to sample

        """
        sample_size = min(sample_size, self.count())
        dimension = self._get_dimension_from_key(dim_key)
        measures = [dimension.measures[index] for index in self._get_items()]
        return random.sample(measures, sample_size)

    def _get_measure(self, item, dim_key):
        dimension = self._get_dimension_from_key(dim_key)
        return dimension.measures[item].value

    def _get_dimension_from_key(self, dim_key):
        if not self._dimensions_by_key.has_key(dim_key):
            self._dimensions_by_key[dim_key] = dim_key.get()
            
        return self._dimensions_by_key[dim_key]
        
